import random

import pytest

from graph_algorithms_lab import (
    brute_force_terminal_reliability,
    edge,
    generate_ttsp,
    materialize,
    parallel,
    series,
    terminal_reliability,
)


def test_closed_form_example() -> None:
    network = materialize(series(parallel(edge(), edge()), edge()))
    probabilities = {
        item.id: value
        for item, value in zip(network.graph.edges, [0.5, 0.5, 0.8], strict=True)
    }

    assert terminal_reliability(network.decomposition, probabilities) == pytest.approx(
        0.6
    )


@pytest.mark.parametrize("size", range(1, 9))
def test_tree_dp_matches_exhaustive_edge_state_enumeration(size: int) -> None:
    network = generate_ttsp(size, seed=100 + size)
    rng = random.Random(size)
    probabilities = {item.id: rng.uniform(0.1, 0.9) for item in network.graph.edges}

    dynamic_program = terminal_reliability(network.decomposition, probabilities)
    brute_force = brute_force_terminal_reliability(network, probabilities)

    assert dynamic_program == pytest.approx(brute_force, abs=1e-12)


def test_probability_validation() -> None:
    network = materialize(edge())
    with pytest.raises(ValueError, match="probabilities"):
        terminal_reliability(network.decomposition, {0: 1.1})
