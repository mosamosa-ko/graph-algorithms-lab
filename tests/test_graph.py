import pytest

from graph_algorithms_lab import UndirectedMultiGraph


def test_traversals_and_connectivity_are_deterministic() -> None:
    graph = UndirectedMultiGraph()
    graph.add_edge("a", "c")
    graph.add_edge("a", "b")
    graph.add_edge("c", "d")

    assert graph.bfs("a") == ("a", "b", "c", "d")
    assert graph.dfs("a") == ("a", "b", "c", "d")
    assert graph.is_connected()
    assert graph.connected_components() == (frozenset({"a", "b", "c", "d"}),)


def test_parallel_edges_have_distinct_ids_and_contribute_to_degree() -> None:
    graph = UndirectedMultiGraph()
    first = graph.add_edge(0, 1)
    second = graph.add_edge(0, 1)

    assert first != second
    assert graph.degree(0) == 2
    assert graph.neighbors(0) == (1,)


def test_invalid_operations_fail_loudly() -> None:
    graph = UndirectedMultiGraph()
    with pytest.raises(ValueError, match="self-loops"):
        graph.add_edge("x", "x")
    with pytest.raises(KeyError):
        graph.bfs("missing")
