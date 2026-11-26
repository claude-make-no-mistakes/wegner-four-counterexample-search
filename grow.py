"""Grow the 17-vertex nine-color example while minimizing distant triples."""

import argparse
from collections import Counter
from itertools import combinations
import gzip
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from geometry import ascii_graph, faces, record, square


def split_vertices(graph):
    for u, row in enumerate(graph):
        if len(row) != 4:
            continue
        w = len(graph)
        for start in range(2):
            a, b, c, d = row[start:] + row[:start]
            grown = list(graph)
            grown[u] = (a, b, w)
            grown.append((c, d, u))
            for v in (c, d):
                grown[v] = tuple(w if x == u else x for x in graph[v])
            yield tuple(grown)


def bridge_subdivisions(graph):
    boundaries, _ = faces(graph)
    x = len(graph)
    y = x + 1
    for boundary in boundaries:
        for (a, b), (c, d) in combinations(boundary, 2):
            grown = list(graph)
            for u, v, w in ((a, b, x), (b, a, x), (c, d, y), (d, c, y)):
                grown[u] = tuple(w if z == v else z for z in grown[u])
            yield (*grown, (a, y, b), (c, x, d))


def add_chords(graph):
    boundaries, _ = faces(graph)
    for boundary in boundaries:
        for (a, u), (b, v) in combinations(boundary, 2):
            if u == v or v in graph[u] or len(graph[u]) == 4 or len(graph[v]) == 4:
                continue
            grown = list(graph)
            left = graph[u].index(a) + 1
            right = graph[v].index(b) + 1
            grown[u] = graph[u][:left] + (v,) + graph[u][left:]
            grown[v] = graph[v][:right] + (u,) + graph[v][right:]
            yield tuple(grown)


def score(graph):
    adj = square(graph)
    full = (1 << len(graph)) - 1
    remote = [(full ^ sum(1 << v for v in row)) & ~(1 << u) for u, row in enumerate(adj)]
    triples = 0
    pairs = 0
    for u, row in enumerate(remote):
        later = row >> (u + 1) << (u + 1)
        pairs += later.bit_count()
        while later:
            bit = later & -later
            later ^= bit
            v = bit.bit_length() - 1
            triples += (later & remote[v]).bit_count()
    return triples, pairs


def run(seed, output, through, width, search):
    initial, _ = record(seed.read_text(encoding="ascii"))
    beam = {17: [initial]}
    digest = sha256()
    totals = []
    with output.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            for n in range(18, through + 1):
                cases = {}

                def keep(graph):
                    key = tuple(tuple(sorted(row)) for row in graph)
                    cases.setdefault(key, graph)

                for graph in beam[n-1]:
                    for child in split_vertices(graph):
                        keep(child)
                        for denser in add_chords(child):
                            keep(denser)
                for graph in beam.get(n-2, []):
                    for child in bridge_subdivisions(graph):
                        keep(child)
                        for denser in add_chords(child):
                            keep(denser)
                ranked = sorted((score(graph), key, graph) for key, graph in cases.items())
                beam[n] = [graph for _, _, graph in ranked[:width]]
                order_input = "".join(ascii_graph(graph) + "\n" for _, _, graph in ranked)
                result = subprocess.run([search, "--all"], input=order_input.encode(),
                                        capture_output=True, check=True)
                outcomes = Counter()
                for line in result.stdout.splitlines():
                    canonical = b" ".join(line.split()) + b"\n"
                    digest.update(canonical)
                    compressed.write(canonical)
                    witness = canonical.split()[-1]
                    if witness == b"FAIL":
                        outcomes["failure"] += 1
                        print(f"Counterexample candidate: {canonical.decode().strip()}", flush=True)
                    else:
                        outcomes[f"colors_{len(set(witness))}"] += 1
                if sum(outcomes.values()) != len(cases):
                    raise ValueError("Worker returned an incomplete graph batch")
                summary = {"order": n, "graphs": len(cases), "min_distant_triples": ranked[0][0][0],
                           "witness_types": outcomes}
                totals.append(summary)
                print(json.dumps(summary, sort_keys=True), flush=True)
                if outcomes["failure"]:
                    break
    return {"orders": totals, "stream_sha256": digest.hexdigest(), "width": width}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--search", type=Path, required=True)
    parser.add_argument("--seed", type=Path, default=Path("example-17.txt"))
    parser.add_argument("--through", type=int, default=22)
    parser.add_argument("--width", type=int, default=22)
    args = parser.parse_args()
    if not 18 <= args.through <= 26 or args.width < 1:
        parser.error("expected 18 <= through <= 26 and positive width")
    final = run(args.seed, args.output, args.through, args.width, str(args.search.resolve(strict=True)))
    args.output.with_suffix(".json").write_text(
        json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
