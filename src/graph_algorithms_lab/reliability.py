"""A small dynamic-programming example on S/P decomposition trees."""

from __future__ import annotations

from itertools import product

from .decomposition import DecompositionNode, NodeKind, TTSPNetwork


def terminal_reliability(
    root: DecompositionNode, edge_survival: dict[int, float]
) -> float:
    """Compute two-terminal reliability by a postorder S/P-tree DP.

    Edge states are independent. The recurrence is ``prod(p_i)`` for series
    composition and ``1 - prod(1 - p_i)`` for parallel composition.
    """
    if root.kind is NodeKind.EDGE:
        if root.edge_id is None:
            raise ValueError("decomposition leaves must refer to concrete edges")
        probability = edge_survival[root.edge_id]
        if not 0.0 <= probability <= 1.0:
            raise ValueError("edge probabilities must be in [0, 1]")
        return probability
    values = [terminal_reliability(child, edge_survival) for child in root.children]
    if root.kind is NodeKind.SERIES:
        result = 1.0
        for value in values:
            result *= value
        return result
    failure = 1.0
    for value in values:
        failure *= 1.0 - value
    return 1.0 - failure


def brute_force_terminal_reliability(
    network: TTSPNetwork, edge_survival: dict[int, float]
) -> float:
    """Reference implementation enumerating all 2^|E| edge states."""
    edges = network.graph.edges
    total = 0.0
    for states in product((False, True), repeat=len(edges)):
        state_probability = 1.0
        adjacency: dict[object, set[object]] = {
            vertex: set() for vertex in network.graph.vertices
        }
        for item, survives in zip(edges, states, strict=True):
            probability = edge_survival[item.id]
            if not 0.0 <= probability <= 1.0:
                raise ValueError("edge probabilities must be in [0, 1]")
            state_probability *= probability if survives else 1.0 - probability
            if survives:
                adjacency[item.u].add(item.v)
                adjacency[item.v].add(item.u)
        reachable = {network.source}
        stack = [network.source]
        while stack:
            vertex = stack.pop()
            for neighbor in adjacency[vertex] - reachable:
                reachable.add(neighbor)
                stack.append(neighbor)
        if network.sink in reachable:
            total += state_probability
    return total
