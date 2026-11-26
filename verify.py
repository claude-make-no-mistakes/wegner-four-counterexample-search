"""Validate archived sphere embeddings, square colorings, and short separators."""

import argparse
from collections import Counter
from itertools import combinations
import gzip
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from geometry import check, faces, record, square, verify_color, verify_separator


def rows(directory, info, plantri):
    with gzip.open(directory / info["certificate"], "rb") as data:
        if not info.get("detached"):
            yield from data
            return
        check(plantri is not None and info["quartic_only"],
              "Detached quartic certificates require --plantri")
        with subprocess.Popen([plantri, "-q", "-d", "-a", str(info["order"]+2)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE) as generator:
            for embedding, color in zip(generator.stdout, data, strict=True):
                yield b" ".join(embedding.split() + color.split()) + b"\n"
            report = generator.stderr.read()
            check(generator.wait() == 0, report.decode())


def verify(directory, plantri):
    result = Counter()
    orders = set()
    for path in sorted(directory.glob("order-*.json")):
        info = json.loads(path.read_text(encoding="utf-8"))
        claimed_edges = {int(m): count for m, count in info["edge_counts"].items()}
        read_counts = dict.fromkeys(claimed_edges, 0)
        order = info["order"]
        check(order not in orders, "Duplicate order")
        orders.add(order)
        counts = Counter()
        digest = sha256()
        for line in rows(directory, info, plantri):
            digest.update(line)
            graph, witness = record(line.decode("ascii"))
            check(len(graph) == order, "Graph order differs from summary")
            edges = sum(map(len, graph)) // 2
            read_counts[edges] += 1
            if info["quartic_only"]:
                check(edges == 2*order and not witness.startswith("S"),
                      "Quartic cases must have direct colorings")
            boundaries, index = faces(graph)
            if witness.startswith("S"):
                length = verify_separator(graph, witness, boundaries, index)
                counts[f"separator_{length}"] += 1
            else:
                colors = verify_color(graph, witness)
                counts[f"colors_{colors}"] += 1
        check(digest.hexdigest() == info["stream_sha256"], "Stream hash mismatch")
        check(counts == info["witness_types"] and read_counts == claimed_edges,
              "Ledger counts differ")
        result.update(counts)
    check(orders and orders == set(range(min(orders), max(orders)+1)), "Missing order")
    print(f"{directory}: orders {min(orders)} to {max(orders)}, {sum(result.values())} "
          f"certificates, {dict(sorted(result.items()))}")


def verify_example(path):
    graph, witness = record(path.read_text(encoding="ascii"))
    faces(graph)
    check(len(graph) == 17 and all(len(row) == 4 for row in graph), "Wrong example")
    check(verify_color(graph, witness) == 9, "Missing nine-color upper bound")
    adj = square(graph)
    check(all(any(v in adj[u] for u, v in combinations(triple, 2))
              for triple in combinations(range(len(graph)), 3)), "Found independent triple")
    check(all(not all(v in adj[u] for u, v in combinations(vertices, 2))
              for vertices in combinations(range(len(graph)), 7)), "Found seven-clique")
    check(all(v in adj[u] for u, v in combinations((0, 1, 2, 3, 4, 6), 2)), "Six-clique missing")
    print("Example: chromatic number 9, clique number 6, independence number 2.")


def verify_growth(path):
    summary = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    by_order = {row["order"]: row for row in summary["orders"]}
    expected = {n: Counter(row["witness_types"]) for n, row in by_order.items()}
    counts = {n: Counter() for n in by_order}
    minima = {n: None for n in by_order}
    seen = set()
    digest = sha256()
    with gzip.open(path, "rb") as data:
        for line in data:
            digest.update(line)
            graph, witness = record(line.decode("ascii"))
            faces(graph)
            key = tuple(tuple(sorted(row)) for row in graph)
            check(key not in seen, "Duplicate growth candidate")
            seen.add(key)
            n = len(graph)
            counts[n][f"colors_{verify_color(graph, witness)}"] += 1
            adj = square(graph)
            triples = sum(v not in adj[u] and w not in adj[u] and w not in adj[v]
                          for u, v, w in combinations(range(n), 3))
            minima[n] = triples if minima[n] is None else min(minima[n], triples)
    check(digest.hexdigest() == summary["stream_sha256"] and counts == expected,
          "Growth ledger hash or count mismatch")
    check(all(minima[n] == row["min_distant_triples"] and sum(counts[n].values()) == row["graphs"]
              for n, row in by_order.items()), "Growth summary differs")
    print(f"{path}: {len(seen)} checked colorings, minimum distant triples {minima}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", type=Path, nargs="+")
    parser.add_argument("--example", type=Path)
    parser.add_argument("--growth", type=Path)
    parser.add_argument("--plantri", type=Path)
    args = parser.parse_args()
    plantri = str(args.plantri.resolve(strict=True)) if args.plantri else None
    for directory in args.directories:
        verify(directory, plantri)
    if args.example:
        verify_example(args.example)
    if args.growth:
        verify_growth(args.growth)
