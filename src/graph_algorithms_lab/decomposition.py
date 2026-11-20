"""S/P decomposition-tree data structures and TTSP construction."""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from enum import StrEnum

from .graph import UndirectedMultiGraph, Vertex


class NodeKind(StrEnum):
    EDGE = "edge"
    SERIES = "series"
    PARALLEL = "parallel"


@dataclass(frozen=True, slots=True)
class DecompositionNode:
    """A node in an S/P decomposition tree.

    Leaves refer to concrete graph edge identifiers after materialization. Internal
    nodes record series or parallel composition. An S/P tree is a certificate of
    construction; it need not be unique.
    """

    kind: NodeKind
    children: tuple[DecompositionNode, ...] = ()
    edge_id: int | None = None

    def __post_init__(self) -> None:
        if self.kind is NodeKind.EDGE:
            if self.children:
                raise ValueError("an edge leaf cannot have children")
        elif len(self.children) < 2:
            raise ValueError("composition nodes need at least two children")

    @property
    def leaf_count(self) -> int:
        if self.kind is NodeKind.EDGE:
            return 1
        return sum(child.leaf_count for child in self.children)

    def reversed(self) -> DecompositionNode:
        """Reverse the terminal orientation represented by this tree."""
        if self.kind is NodeKind.EDGE:
            return self
        children = tuple(child.reversed() for child in self.children)
        if self.kind is NodeKind.SERIES:
            children = tuple(reversed(children))
        return replace(self, children=children)


def edge(edge_id: int | None = None) -> DecompositionNode:
    return DecompositionNode(NodeKind.EDGE, edge_id=edge_id)


def _compose(
    kind: NodeKind, children: tuple[DecompositionNode, ...]
) -> DecompositionNode:
    if len(children) < 2:
        raise ValueError("at least two components are required")
    flattened: list[DecompositionNode] = []
    for child in children:
        if child.kind is kind:
            flattened.extend(child.children)
        else:
            flattened.append(child)
    return DecompositionNode(kind, tuple(flattened))


def series(*children: DecompositionNode) -> DecompositionNode:
    return _compose(NodeKind.SERIES, children)


def parallel(*children: DecompositionNode) -> DecompositionNode:
    return _compose(NodeKind.PARALLEL, children)


@dataclass(frozen=True, slots=True)
class TTSPNetwork:
    graph: UndirectedMultiGraph
    source: Vertex
    sink: Vertex
    decomposition: DecompositionNode


def materialize(
    root: DecompositionNode,
    *,
    source: Vertex = "s",
    sink: Vertex = "t",
) -> TTSPNetwork:
    """Build the concrete multigraph represented by ``root``."""
    if source == sink:
        raise ValueError("terminals must be distinct")
    graph = UndirectedMultiGraph()
    next_vertex = 0

    def fresh_vertex() -> str:
        nonlocal next_vertex
        while True:
            candidate = f"v{next_vertex}"
            next_vertex += 1
            if candidate not in {source, sink}:
                return candidate

    def build(
        node: DecompositionNode, left: Vertex, right: Vertex
    ) -> DecompositionNode:
        if node.kind is NodeKind.EDGE:
            identifier = graph.add_edge(left, right)
            return edge(identifier)
        if node.kind is NodeKind.PARALLEL:
            return parallel(*(build(child, left, right) for child in node.children))

        boundaries: list[Vertex] = [left]
        boundaries.extend(fresh_vertex() for _ in range(len(node.children) - 1))
        boundaries.append(right)
        return series(
            *(
                build(child, boundaries[index], boundaries[index + 1])
                for index, child in enumerate(node.children)
            )
        )

    concrete_root = build(root, source, sink)
    return TTSPNetwork(graph, source, sink, concrete_root)


def generate_ttsp(
    edge_count: int,
    *,
    seed: int = 0,
    parallel_probability: float = 0.5,
) -> TTSPNetwork:
    """Generate a reproducible TTSP network with exactly ``edge_count`` edges."""
    if edge_count < 1:
        raise ValueError("edge_count must be positive")
    if not 0.0 <= parallel_probability <= 1.0:
        raise ValueError("parallel_probability must be in [0, 1]")
    rng = random.Random(seed)

    def generate(leaves: int) -> DecompositionNode:
        if leaves == 1:
            return edge()
        left_size = rng.randint(1, leaves - 1)
        children = (generate(left_size), generate(leaves - left_size))
        if rng.random() < parallel_probability:
            return parallel(*children)
        return series(*children)

    return materialize(generate(edge_count))
