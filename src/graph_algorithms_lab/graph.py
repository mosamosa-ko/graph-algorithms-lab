"""A small undirected multigraph with deterministic traversal algorithms."""

from __future__ import annotations

from collections import deque
from collections.abc import Hashable, Iterator
from dataclasses import dataclass

Vertex = Hashable


@dataclass(frozen=True, slots=True)
class Edge:
    """An undirected edge identified independently from its endpoints."""

    id: int
    u: Vertex
    v: Vertex
    label: str | None = None

    def other(self, vertex: Vertex) -> Vertex:
        """Return the endpoint opposite ``vertex``."""
        if vertex == self.u:
            return self.v
        if vertex == self.v:
            return self.u
        raise ValueError(f"{vertex!r} is not incident to edge {self.id}")


class UndirectedMultiGraph:
    """An undirected loop-free multigraph.

    Parallel edges are distinct because every edge has a stable integer identifier.
    Self-loops are intentionally excluded: they are not needed by the TTSP model in
    this repository and complicate degree conventions.
    """

    def __init__(self) -> None:
        self._vertices: set[Vertex] = set()
        self._edges: dict[int, Edge] = {}
        self._incidence: dict[Vertex, set[int]] = {}
        self._next_edge_id = 0

    @property
    def vertices(self) -> tuple[Vertex, ...]:
        return tuple(sorted(self._vertices, key=repr))

    @property
    def edges(self) -> tuple[Edge, ...]:
        return tuple(self._edges[key] for key in sorted(self._edges))

    def __len__(self) -> int:
        return len(self._vertices)

    @property
    def order(self) -> int:
        return len(self._vertices)

    @property
    def size(self) -> int:
        return len(self._edges)

    def add_vertex(self, vertex: Vertex) -> None:
        self._vertices.add(vertex)
        self._incidence.setdefault(vertex, set())

    def add_edge(
        self,
        u: Vertex,
        v: Vertex,
        *,
        label: str | None = None,
        edge_id: int | None = None,
    ) -> int:
        if u == v:
            raise ValueError("self-loops are not supported")
        self.add_vertex(u)
        self.add_vertex(v)
        identifier = self._next_edge_id if edge_id is None else edge_id
        if identifier in self._edges:
            raise ValueError(f"edge id {identifier} already exists")
        self._next_edge_id = max(self._next_edge_id, identifier + 1)
        self._edges[identifier] = Edge(identifier, u, v, label)
        self._incidence[u].add(identifier)
        self._incidence[v].add(identifier)
        return identifier

    def edge(self, edge_id: int) -> Edge:
        return self._edges[edge_id]

    def incident_edges(self, vertex: Vertex) -> tuple[Edge, ...]:
        if vertex not in self._vertices:
            raise KeyError(vertex)
        return tuple(self._edges[key] for key in sorted(self._incidence[vertex]))

    def degree(self, vertex: Vertex) -> int:
        """Return multigraph degree (parallel edges count separately)."""
        return len(self.incident_edges(vertex))

    def neighbors(self, vertex: Vertex) -> tuple[Vertex, ...]:
        adjacent = {edge.other(vertex) for edge in self.incident_edges(vertex)}
        return tuple(sorted(adjacent, key=repr))

    def bfs(self, start: Vertex) -> tuple[Vertex, ...]:
        """Return deterministic breadth-first discovery order in O(|V| + |E|)."""
        if start not in self._vertices:
            raise KeyError(start)
        discovered = {start}
        queue = deque([start])
        order: list[Vertex] = []
        while queue:
            vertex = queue.popleft()
            order.append(vertex)
            for neighbor in self.neighbors(vertex):
                if neighbor not in discovered:
                    discovered.add(neighbor)
                    queue.append(neighbor)
        return tuple(order)

    def dfs(self, start: Vertex) -> tuple[Vertex, ...]:
        """Return deterministic iterative depth-first discovery order."""
        if start not in self._vertices:
            raise KeyError(start)
        discovered: set[Vertex] = set()
        stack = [start]
        order: list[Vertex] = []
        while stack:
            vertex = stack.pop()
            if vertex in discovered:
                continue
            discovered.add(vertex)
            order.append(vertex)
            stack.extend(reversed(self.neighbors(vertex)))
        return tuple(order)

    def connected_components(self) -> tuple[frozenset[Vertex], ...]:
        remaining = set(self._vertices)
        components: list[frozenset[Vertex]] = []
        while remaining:
            start = min(remaining, key=repr)
            component = frozenset(self.bfs(start))
            components.append(component)
            remaining -= component
        return tuple(components)

    def is_connected(self) -> bool:
        """Return whether every vertex is reachable (the null graph is false)."""
        return bool(self._vertices) and len(self.bfs(self.vertices[0])) == self.order

    def iter_edge_pairs(self) -> Iterator[tuple[Vertex, Vertex, int]]:
        for edge in self.edges:
            yield edge.u, edge.v, edge.id

    def copy(self) -> UndirectedMultiGraph:
        result = UndirectedMultiGraph()
        for vertex in self.vertices:
            result.add_vertex(vertex)
        for edge in self.edges:
            result.add_edge(edge.u, edge.v, label=edge.label, edge_id=edge.id)
        return result
