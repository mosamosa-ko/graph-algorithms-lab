"""Reduction-based recognition and decomposition of undirected TTSP networks."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum

from .decomposition import DecompositionNode, edge, parallel, series
from .graph import UndirectedMultiGraph, Vertex


class ReductionKind(StrEnum):
    PARALLEL = "parallel"
    SERIES = "series"


@dataclass(frozen=True, slots=True)
class ReductionStep:
    index: int
    kind: ReductionKind
    removed_edge_ids: tuple[int, ...]
    eliminated_vertex: Vertex | None
    remaining_edges: int


@dataclass(frozen=True, slots=True)
class RecognitionResult:
    is_ttsp: bool
    decomposition: DecompositionNode | None
    reductions: tuple[ReductionStep, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class _VirtualEdge:
    id: int
    u: Vertex
    v: Vertex
    tree: DecompositionNode

    def oriented(self, source: Vertex, sink: Vertex) -> DecompositionNode:
        if (self.u, self.v) == (source, sink):
            return self.tree
        if (self.u, self.v) == (sink, source):
            return self.tree.reversed()
        raise ValueError("requested endpoints do not match virtual edge")

    def other(self, vertex: Vertex) -> Vertex:
        if vertex == self.u:
            return self.v
        if vertex == self.v:
            return self.u
        raise ValueError("vertex is not incident")


def recognize_ttsp(
    graph: UndirectedMultiGraph, source: Vertex, sink: Vertex
) -> RecognitionResult:
    """Recognize a TTSP network and construct one S/P decomposition tree.

    The implementation repeatedly contracts parallel edges and nonterminal
    degree-two vertices. It intentionally rebuilds candidate tables after each
    reduction, favoring an inspectable trace over the optimal linear-time data
    structures in the literature. Worst-case running time is O((|V|+|E|)^2).
    """
    if source == sink:
        return RecognitionResult(False, None, (), "terminals must be distinct")
    if source not in graph.vertices or sink not in graph.vertices:
        return RecognitionResult(False, None, (), "both terminals must be vertices")
    if graph.size == 0 or not graph.is_connected():
        return RecognitionResult(False, None, (), "the graph must be connected")

    active = {
        item.id: _VirtualEdge(item.id, item.u, item.v, edge(item.id))
        for item in graph.edges
    }
    next_identifier = -1
    steps: list[ReductionStep] = []

    def replace(
        removed: tuple[int, ...], u: Vertex, v: Vertex, tree: DecompositionNode
    ) -> None:
        nonlocal next_identifier
        for identifier in removed:
            del active[identifier]
        active[next_identifier] = _VirtualEdge(next_identifier, u, v, tree)
        next_identifier -= 1

    while len(active) > 1:
        by_endpoints: dict[frozenset[Vertex], list[_VirtualEdge]] = defaultdict(list)
        for item in active.values():
            by_endpoints[frozenset((item.u, item.v))].append(item)

        parallel_group = next(
            (
                sorted(group, key=lambda item: item.id)
                for group in by_endpoints.values()
                if len(group) > 1
            ),
            None,
        )
        if parallel_group is not None:
            u, v = parallel_group[0].u, parallel_group[0].v
            removed = tuple(item.id for item in parallel_group)
            tree = parallel(*(item.oriented(u, v) for item in parallel_group))
            replace(removed, u, v, tree)
            steps.append(
                ReductionStep(
                    len(steps), ReductionKind.PARALLEL, removed, None, len(active)
                )
            )
            continue

        incidence: dict[Vertex, list[_VirtualEdge]] = defaultdict(list)
        for item in active.values():
            incidence[item.u].append(item)
            incidence[item.v].append(item)
        candidate = next(
            (
                vertex
                for vertex in sorted(incidence, key=repr)
                if vertex not in {source, sink}
                and len(incidence[vertex]) == 2
                and incidence[vertex][0].other(vertex)
                != incidence[vertex][1].other(vertex)
            ),
            None,
        )
        if candidate is None:
            break
        first, second = sorted(incidence[candidate], key=lambda item: item.id)
        u, v = first.other(candidate), second.other(candidate)
        removed = (first.id, second.id)
        tree = series(first.oriented(u, candidate), second.oriented(candidate, v))
        replace(removed, u, v, tree)
        steps.append(
            ReductionStep(
                len(steps), ReductionKind.SERIES, removed, candidate, len(active)
            )
        )

    if len(active) != 1:
        return RecognitionResult(
            False,
            None,
            tuple(steps),
            "no valid series or parallel reduction remains",
        )
    final = next(iter(active.values()))
    if {final.u, final.v} != {source, sink}:
        return RecognitionResult(
            False, None, tuple(steps), "reduction did not end at the terminals"
        )
    return RecognitionResult(
        True,
        final.oriented(source, sink),
        tuple(steps),
        "reduced to one terminal edge",
    )
