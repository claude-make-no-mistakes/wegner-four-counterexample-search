"""Stream plantri embeddings into the search and archive color certificates."""

import argparse
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess


def commands(n, quartic):
    for edges in range(2*n if quartic else (3*n+1)//2, 2*n+1):
        dual = edges - n + 2
        if dual < 4 or 3*dual > 2*edges or edges > 3*dual-6:
            continue
        if edges == 2*n:
            yield edges, ["-q", "-d", "-a", str(dual)]
        elif 2*edges == 3*n:
            yield edges, ["-d", "-a", str(dual)]
        else:
            yield edges, ["-p", "-c3", "-m3", "-f4", "-d", "-a", f"-e{edges}", str(dual)]


def sweep(n, quartic, target, plantri, search, detached):
    digest = sha256()
    counts = Counter()
    edge_counts = {}
    extension = "colors" if detached else "txt"
    final = target / f"order-{n}.{extension}.gz"
    with final.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", compresslevel=6, fileobj=raw, mtime=0) as archive:
            for edges, args in commands(n, quartic):
                with subprocess.Popen([plantri, *args], stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE) as generator:
                    check_command = [search, "--all"] if quartic else [search]
                    with subprocess.Popen(check_command, stdin=generator.stdout, stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE) as worker:
                        generator.stdout.close()
                        size = 0
                        for line in worker.stdout:
                            text = b" ".join(line.split()) + b"\n"
                            labels = text.split()
                            if len(labels) != 3 or int(labels[0]) != n:
                                raise ValueError(f"Unexpected search output: {text!r}")
                            witness = labels[2]
                            if witness == b"FAIL":
                                print(f"Counterexample candidate: {text.decode().strip()}", flush=True)
                                counts["failure"] += 1
                            elif witness.startswith(b"S"):
                                counts[f"separator_{len(witness)-1}"] += 1
                            else:
                                counts[f"colors_{len(set(witness))}"] += 1
                            archive.write(witness + b"\n" if detached else text)
                            digest.update(text)
                            size += 1
                        diagnostic = worker.stderr.read().decode()
                        if worker.wait():
                            raise RuntimeError(diagnostic)
                    report = generator.stderr.read()
                    match = re.search(rb"(\d+) [a-z ]+ written to stdout", report)
                    if generator.wait() or match is None or int(match[1]) != size:
                        raise RuntimeError(report.decode())
                edge_counts[edges] = size
    summary = {"order": n, "quartic_only": quartic, "edge_counts": edge_counts,
               "witness_types": counts, "stream_sha256": digest.hexdigest(),
               "certificate": final.name}
    if detached:
        summary["detached"] = True
    directory = target / f"order-{n}.json"
    directory.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True), flush=True)
    return not counts["failure"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--plantri", type=Path, required=True)
    parser.add_argument("--search", type=Path, required=True)
    parser.add_argument("--from", dest="first", type=int, default=4)
    parser.add_argument("--through", dest="last", type=int, required=True)
    parser.add_argument("--quartic-only", action="store_true")
    parser.add_argument("--detached", action="store_true",
                        help="archive only colors, and regenerate quartic embeddings during replay")
    args = parser.parse_args()
    if not 4 <= args.first <= args.last <= 26:
        parser.error("expected 4 <= from <= through <= 26")
    if args.detached and not args.quartic_only:
        parser.error("detached archives are available for quartic enumeration")
    plantri, search = (str(path.resolve(strict=True)) for path in (args.plantri, args.search))
    args.target.mkdir(parents=True, exist_ok=True)
    for n in range(args.first, args.last + 1):
        if not sweep(n, args.quartic_only, args.target, plantri, search, args.detached):
            raise SystemExit(2)


if __name__ == "__main__":
    main()
