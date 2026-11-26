# Degree-four Wegner counterexample search

Every planar graph on at most **13 vertices** with maximum degree at most four has a nine-colorable square. A smallest counterexample to the full conjecture must be 3-connected and have no separating triangle or 4-cycle. [Research note and proof](note.pdf) · [LaTeX](note.tex)

The [general enumeration](certificates/) accounted for 112,671 3-connected plane graphs whose vertices have degree three or four. Every graph has a separating-cycle certificate or a valid square coloring. The small-separator proof makes those reductions valid with a nine-color palette. Bousquet et al. used related arguments for twelve colors. [Prior separator argument](https://arxiv.org/html/2204.05791#S5.SS2)

The separate [4-regular enumeration](quartic/) checked every 3-connected 4-regular plane graph through **22 vertices**. All 840,245 graphs have direct color certificates. Exactly two need nine colors.

- At order nine, the square is a nine-clique. [Published sharp example](https://theory.stanford.edu/~tomas/d2cols.pdf#page=14)
- At order seventeen, the square has independence number two and clique number six. The independence bound forces nine colors, and its recorded coloring attains nine. [Rotation system and coloring](example-17.txt) · [Drawing](example-17.png)

The [growth search](growth.txt.json) began with the 17-vertex graph and explored 23,173 labeled graphs at orders 18–22 using vertex splits and cofacial edge insertions. All had square colorings with at most eight colors. The unrestricted conjecture remains open.

## Verify and regenerate

Use Python 3.10 or later and plantri 5.8. The checker reconstructs sphere embeddings, verifies square colorings, and verifies separator certificates by cutting the dual. For the compact archives at orders 21 and 22 it regenerates the planar rotations and aligns them with the recorded colors. The checked hash binds each rotation to its color assignment.

    python verify.py certificates quartic --plantri /path/to/plantri --example example-17.txt --growth growth.txt.gz

To regenerate the searches, compile the standalone C++17 evaluator. On Windows use the executable extension and a matching compiler, such as 64-bit MinGW-w64. Plantri's Windows build can set `CPUTIME` to zero in `plantri.c` to disable the POSIX timing dependency. [Plantri source and manual](https://users.cecs.anu.edu.au/~bdm/plantri/)

    g++ -std=c++17 -O3 -Wall -Wextra -Werror search.cpp -o search
    python enumerate.py replay-general --plantri /path/to/plantri --search ./search --through 13
    python enumerate.py replay-quartic --plantri /path/to/plantri --search ./search --quartic-only --from 6 --through 20
    python enumerate.py replay-quartic --plantri /path/to/plantri --search ./search --quartic-only --detached --from 21 --through 22
    python grow.py replay-growth.txt.gz --search ./search --through 22 --width 22

The solver tries eight colors before nine. Ledger counts through eight refer to the size of the returned colorings. The archived example drawing can be regenerated with `python draw.py example-17.png` using NumPy and Matplotlib.
