import pytest

from graph_algorithms_lab import edge, generate_ttsp, materialize, parallel, series


def test_series_and_parallel_materialization() -> None:
    root = series(parallel(edge(), edge()), edge())
    network = materialize(root)

    assert network.graph.size == 3
    assert network.graph.order == 3
    assert network.graph.degree(network.source) == 2
    assert network.graph.degree(network.sink) == 1
    assert network.decomposition.leaf_count == 3


def test_generator_is_reproducible_and_has_exact_size() -> None:
    first = generate_ttsp(25, seed=42)
    second = generate_ttsp(25, seed=42)

    assert first.graph.edges == second.graph.edges
    assert first.decomposition == second.decomposition
    assert first.graph.size == 25


@pytest.mark.parametrize("edge_count", [0, -1])
def test_generator_rejects_nonpositive_sizes(edge_count: int) -> None:
    with pytest.raises(ValueError):
        generate_ttsp(edge_count)
