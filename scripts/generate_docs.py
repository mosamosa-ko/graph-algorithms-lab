"""Regenerate the checked-in SVG examples from library code."""

from pathlib import Path

from graph_algorithms_lab import edge, materialize, parallel, recognize_ttsp, series
from graph_algorithms_lab.visualization import (
    decomposition_svg,
    graph_svg,
    reduction_trace_svg,
)


def main() -> None:
    root = series(parallel(edge(), series(edge(), edge())), parallel(edge(), edge()))
    network = materialize(root)
    result = recognize_ttsp(network.graph, network.source, network.sink)
    if not result.is_ttsp or result.decomposition is None:
        raise RuntimeError("example network should be recognized")
    output = Path("docs/images")
    output.mkdir(parents=True, exist_ok=True)
    (output / "ttsp-network.svg").write_text(graph_svg(network), encoding="utf-8")
    (output / "decomposition-tree.svg").write_text(
        decomposition_svg(result.decomposition), encoding="utf-8"
    )
    (output / "reduction-trace.svg").write_text(
        reduction_trace_svg(result.reductions), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
