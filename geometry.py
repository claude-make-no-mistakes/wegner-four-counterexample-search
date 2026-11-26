"""Read plane graphs and walk the faces of their rotation systems."""


def check(condition, message):
    if not condition:
        raise ValueError(message)


def record(line):
    order, rotation, witness = line.split()
    graph = tuple(tuple(ord(v) - ord("a") for v in row) for row in rotation.split(","))
    check(len(graph) == int(order), "Wrong order")
    return graph, witness


def ascii_graph(graph):
    rotation = ",".join("".join(chr(v + ord("a")) for v in row) for row in graph)
    return f"{len(graph)} {rotation}"


def faces(graph):
    n = len(graph)
    for u, row in enumerate(graph):
        check(3 <= len(row) <= 4 and len(set(row)) == len(row), "Wrong degree or repeat")
        check(all(0 <= v < n and v != u and u in graph[v] for v in row),
              "Invalid undirected edge")
    position = [{v: i for i, v in enumerate(row)} for row in graph]
    connected = {0}
    todo = [0]
    while todo:
        for v in graph[todo.pop()]:
            if v not in connected:
                connected.add(v)
                todo.append(v)
    check(len(connected) == n, "Disconnected rotation system")
    index = {}
    boundaries = []
    for u, row in enumerate(graph):
        for v in row:
            if (u, v) in index:
                continue
            start, dart = (u, v), (u, v)
            boundary = []
            while dart not in index:
                index[dart] = len(boundaries)
                boundary.append(dart)
                a, b = dart
                dart = (b, graph[b][(position[b][a]+1) % len(graph[b])])
            check(dart == start, "Face does not close")
            boundaries.append(tuple(boundary))
    check(n - len(index)//2 + len(boundaries) == 2, "Rotation is not on the sphere")
    return boundaries, index


def square(graph):
    return [set(row).union(*(graph[v] for v in row)) - {u} for u, row in enumerate(graph)]


def verify_color(graph, witness):
    check(len(witness) == len(graph) and all(c in "012345678" for c in witness),
          "Invalid color string")
    check(all(witness[u] != witness[v] for u, row in enumerate(square(graph)) for v in row),
          "Distance-two coloring conflict")
    return len(set(witness))


def verify_separator(graph, witness, boundaries, index):
    cycle = tuple(ord(c) - ord("a") for c in witness[1:])
    check(len(cycle) in (3, 4) and len(set(cycle)) == len(cycle), "Invalid cycle")
    cut = set()
    for u, v in zip(cycle, cycle[1:] + cycle[:1], strict=True):
        check((u, v) in index, "Separator contains a nonedge")
        cut.add(frozenset((u, v)))
    opposite = [set() for _ in boundaries]
    for (u, v), f in index.items():
        if frozenset((u, v)) not in cut:
            opposite[f].add(index[v, u])
    first = index[cycle[0], cycle[1]]
    left, todo = {first}, [first]
    while todo:
        for f in opposite[todo.pop()] - left:
            left.add(f)
            todo.append(f)
    occupied = {index[u, row[0]] in left for u, row in enumerate(graph) if u not in cycle}
    check(occupied == {False, True}, "Cycle does not have vertices on both sides")
    return len(cycle)
