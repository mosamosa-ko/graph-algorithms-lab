"""Reproducible benchmark harness for TTSP recognition."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from .decomposition import generate_ttsp
from .recognition import recognize_ttsp


@dataclass(frozen=True, slots=True)
class BenchmarkRow:
    edges: int
    vertices: int
    repetitions: int
    median_ms: float
    minimum_ms: float
    maximum_ms: float


def run_benchmark(
    sizes: list[int], *, repetitions: int, warmups: int, seed: int
) -> list[BenchmarkRow]:
    rows: list[BenchmarkRow] = []
    for size in sizes:
        network = generate_ttsp(size, seed=seed + size)
        for _ in range(warmups):
            recognize_ttsp(network.graph, network.source, network.sink)
        samples = []
        for _ in range(repetitions):
            started = time.perf_counter_ns()
            result = recognize_ttsp(network.graph, network.source, network.sink)
            elapsed = time.perf_counter_ns() - started
            if not result.is_ttsp:
                raise RuntimeError(f"generated size-{size} network was rejected")
            samples.append(elapsed / 1_000_000)
        rows.append(
            BenchmarkRow(
                edges=size,
                vertices=network.graph.order,
                repetitions=repetitions,
                median_ms=statistics.median(samples),
                minimum_ms=min(samples),
                maximum_ms=max(samples),
            )
        )
    return rows


def write_results(
    rows: list[BenchmarkRow], output: Path, *, warmups: int, seed: int
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    with (output / "recognition.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(asdict(rows[0])))
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
    metadata = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor() or "not reported",
        "timer": "time.perf_counter_ns",
        "warmups": warmups,
        "seed": seed,
        "note": "Wall-clock timings are environment-dependent; rerun before comparison.",
    }
    (output / "environment.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    (output / "recognition.svg").write_text(_benchmark_svg(rows), encoding="utf-8")


def _benchmark_svg(rows: list[BenchmarkRow]) -> str:
    width, height = 760, 430
    left, right, top, bottom = 78, 28, 32, 64
    plot_width, plot_height = width - left - right, height - top - bottom
    max_x = max(row.edges for row in rows)
    max_y = max(row.median_ms for row in rows) * 1.12 or 1.0

    def x(value: float) -> float:
        return left + value / max_x * plot_width

    def y(value: float) -> float:
        return top + plot_height - value / max_y * plot_height

    points = " ".join(f"{x(row.edges):.1f},{y(row.median_ms):.1f}" for row in rows)
    circles = "\n".join(
        f'<circle cx="{x(row.edges):.1f}" cy="{y(row.median_ms):.1f}" r="4"/>'
        for row in rows
    )
    x_ticks = "\n".join(
        f'<text x="{x(row.edges):.1f}" y="{height - 35}" text-anchor="middle">{row.edges}</text>'
        for row in rows
    )
    y_ticks = "\n".join(
        (
            f'<line x1="{left - 5}" y1="{y(max_y * ratio):.1f}" '
            f'x2="{width - right}" y2="{y(max_y * ratio):.1f}" class="grid"/>'
            f'<text x="{left - 10}" y="{y(max_y * ratio) + 4:.1f}" '
            f'text-anchor="end">{max_y * ratio:.1f}</text>'
        )
        for ratio in (0.0, 0.25, 0.5, 0.75, 1.0)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="TTSP recognition benchmark">
<style>
  text {{ fill:#334155; font:12px ui-sans-serif,sans-serif }}
  .axis {{ stroke:#64748b; stroke-width:1.5 }}
  .grid {{ stroke:#cbd5e1; stroke-width:1; opacity:0.55 }}
  .series {{ fill:none; stroke:#0f766e; stroke-width:3 }}
  circle {{ fill:#14b8a6; stroke:#134e4a }}
</style>
{y_ticks}
<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" class="axis"/>
<line x1="{left}" y1="{top + plot_height}" x2="{width - right}" y2="{top + plot_height}" class="axis"/>
<polyline points="{points}" class="series"/>
{circles}
{x_ticks}
<text x="{width / 2}" y="{height - 8}" text-anchor="middle">number of edges</text>
<text x="18" y="{height / 2}" transform="rotate(-90 18 {height / 2})" text-anchor="middle">median time (ms)</text>
<text x="{left}" y="20" style="font-weight:700">Reduction recognizer — local wall-clock benchmark</text>
</svg>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", nargs="+", type=int, default=[8, 16, 32, 64, 128])
    parser.add_argument("--repetitions", type=int, default=20)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--output", type=Path, default=Path("benchmarks/results"))
    arguments = parser.parse_args()
    rows = run_benchmark(
        arguments.sizes,
        repetitions=arguments.repetitions,
        warmups=arguments.warmups,
        seed=arguments.seed,
    )
    write_results(
        rows, arguments.output, warmups=arguments.warmups, seed=arguments.seed
    )
    for row in rows:
        print(f"{row.edges:>4} edges  {row.median_ms:>10.4f} ms median")


if __name__ == "__main__":
    main()
