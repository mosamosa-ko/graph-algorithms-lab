from functools import cache
from itertools import combinations

import pytest

from graph_algorithms_lab import (
    DecompositionNode,
    UndirectedMultiGraph,
    edge,
    generate_ttsp,
    materialize,
    parallel,
    recognize_ttsp,
    series,
)


@pytest.mark.parametrize("size", [1, 2, 3, 8, 32, 100])
def test_generated_networks_are_recognized(size: int) -> None:
    network = generate_ttsp(size, seed=size)
    result = recognize_ttsp(network.graph, network.source, network.sink)

    assert result.is_ttsp, result.reason
    assert result.decomposition is not None
    assert result.decomposition.leaf_count == size


def test_wheatstone_bridge_is_not_ttsp_for_given_terminals() -> None:
    graph = UndirectedMultiGraph()
    for u, v in [("s", "a"), ("a", "t"), ("s", "b"), ("b", "t"), ("a", "b")]:
        graph.add_edge(u, v)

    result = recognize_ttsp(graph, "s", "t")

    assert not result.is_ttsp
    assert result.decomposition is None


def test_disconnected_graph_is_rejected() -> None:
    graph = UndirectedMultiGraph()
    graph.add_edge("s", "t")
    graph.add_edge("x", "y")
    assert not recognize_ttsp(graph, "s", "t").is_ttsp


@cache
def all_binary_sp_trees(leaves: int) -> tuple[DecompositionNode, ...]:
    """Enumerate ordered binary S/P expressions with exactly ``leaves`` leaves."""
    if leaves == 1:
        return (edge(),)
    result = []
    for left_size in range(1, leaves):
        for left in all_binary_sp_trees(left_size):
            for right in all_binary_sp_trees(leaves - left_size):
                result.extend((series(left, right), parallel(left, right)))
    return tuple(result)


@pytest.mark.parametrize("leaves", range(1, 7))
def test_exhaustive_small_sp_expressions_are_recognized(leaves: int) -> None:
    """Exhaust all ordered binary construction trees through six edges."""
    for root in all_binary_sp_trees(leaves):
        network = materialize(root)
        result = recognize_ttsp(network.graph, network.source, network.sink)
        assert result.is_ttsp, (root, result.reason)
        assert result.decomposition is not None
        assert result.decomposition.leaf_count == leaves


def _reference_reduces_to_edge(
    edges: tuple[tuple[int, int], ...], source: int, sink: int
) -> bool:
    """Branch over every valid reduction order; independent test-only oracle."""

    @cache
    def search(state: tuple[tuple[int, int], ...]) -> bool:
        if len(state) == 1:
            return state[0] == (source, sink)

        endpoint_groups: dict[tuple[int, int], list[int]] = {}
        for index, pair in enumerate(state):
            endpoint_groups.setdefault(pair, []).append(index)
        for pair, indices in endpoint_groups.items():
            if len(indices) > 1:
                removed = set(indices)
                reduced = [
                    item for index, item in enumerate(state) if index not in removed
                ]
                reduced.append(pair)
                if search(tuple(sorted(reduced))):
                    return True

        incidence: dict[int, list[int]] = {}
        for index, (u, v) in enumerate(state):
            incidence.setdefault(u, []).append(index)
            incidence.setdefault(v, []).append(index)
        for vertex, indices in incidence.items():
            if vertex in {source, sink} or len(indices) != 2:
                continue
            first, second = (state[index] for index in indices)
            left = first[1] if first[0] == vertex else first[0]
            right = second[1] if second[0] == vertex else second[0]
            if left == right:
                continue
            removed = set(indices)
            reduced = [item for index, item in enumerate(state) if index not in removed]
            reduced.append(tuple(sorted((left, right))))
            if search(tuple(sorted(reduced))):
                return True
        return False

    return search(tuple(sorted(edges)))


@pytest.mark.parametrize("order", range(2, 6))
def test_all_small_simple_graphs_match_branching_reduction_oracle(order: int) -> None:
    """Exhaust every labeled simple graph on at most five vertices."""
    possible_edges = tuple(combinations(range(order), 2))
    source, sink = 0, order - 1
    for mask in range(1 << len(possible_edges)):
        selected = tuple(
            item for index, item in enumerate(possible_edges) if mask & (1 << index)
        )
        graph = UndirectedMultiGraph()
        for vertex in range(order):
            graph.add_vertex(vertex)
        for u, v in selected:
            graph.add_edge(u, v)

        actual = recognize_ttsp(graph, source, sink).is_ttsp
        expected = graph.is_connected() and _reference_reduces_to_edge(
            selected, source, sink
        )
        assert actual == expected, (order, selected)
