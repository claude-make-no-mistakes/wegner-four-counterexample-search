"""Draw the verified example using a convex-face barycentric embedding."""

import argparse
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from geometry import faces, record, verify_color


def layout(graph, boundaries):
    n = len(graph)
    candidates = []
    for boundary in boundaries:
        matrix = np.eye(n)
        targets = np.zeros((n, 2))
        rim = [u for u, _ in boundary]
        for i, u in enumerate(rim):
            angle = 2*np.pi*i/len(rim) + np.pi/2
            targets[u] = np.cos(angle), np.sin(angle)
        for u, row in enumerate(graph):
            if u not in rim:
                matrix[u, list(row)] = -1/len(row)
        position = np.linalg.solve(matrix, targets)
        separation = min(np.linalg.norm(position[u]-position[v])
                         for u, v in combinations(range(n), 2))
        candidates.append((separation, position))
    return max(candidates, key=lambda candidate: candidate[0])[1]


def draw(source, output):
    graph, coloring = record(source.read_text(encoding="ascii"))
    verify_color(graph, coloring)
    position = layout(graph, faces(graph)[0])
    palette = ("#1959a7", "#d48a09", "#287e52", "#c1484b", "#a258ac",
               "#168e99", "#ad602d", "#6770ce", "#c45e92")
    fig, ax = plt.subplots(figsize=(7, 7.4), layout="constrained")
    ax.set_aspect("equal")
    ax.set_axis_off()
    for u, row in enumerate(graph):
        for v in row:
            if u < v:
                ax.plot(*position[[u, v]].T, color="#586373", lw=1.8)
    for u, (x, y) in enumerate(position):
        ax.scatter(x, y, s=360, color=palette[int(coloring[u])], edgecolor="#172536",
                   linewidth=1, zorder=2)
        ax.text(x, y, chr(ord("a")+u), color="white", va="center", ha="center",
                fontsize=11, fontweight="bold", zorder=3)
    ax.margins(0.1)
    ax.set_title("A 17-vertex planar graph requiring nine distance-two colors",
                 fontsize=14, fontweight="bold", color="#172536", pad=15)
    fig.savefig(output, dpi=200, facecolor="white")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source", type=Path, default=Path("example-17.txt"))
    args = parser.parse_args()
    draw(args.source, args.output)
