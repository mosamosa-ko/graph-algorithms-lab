"""Dependency-free SVG renderers for graphs, decomposition trees, and traces."""

from __future__ import annotations

import math
from html import escape

from .decomposition import DecompositionNode, NodeKind, TTSPNetwork
from .recognition import ReductionStep


def graph_svg(network: TTSPNetwork, *, width: int = 760, height: int = 420) -> str:
    """Render a network with a deterministic circular layout."""
    vertices = network.graph.vertices
    center_x, center_y = width / 2, height / 2 + 12
    radius = min(width, height) * 0.34
    positions: dict[object, tuple[float, float]] = {}
    for index, vertex in enumerate(vertices):
        angle = math.pi + 2 * math.pi * index / len(vertices)
        positions[vertex] = (
            center_x + radius * math.cos(angle),
            center_y + radius * math.sin(angle),
        )

    lines = [_svg_header(width, height, "TTSP network")]
    edge_offsets: dict[frozenset[object], int] = {}
    for item in network.graph.edges:
        key = frozenset((item.u, item.v))
        offset_index = edge_offsets.get(key, 0)
        edge_offsets[key] = offset_index + 1
        x1, y1 = positions[item.u]
        x2, y2 = positions[item.v]
        if offset_index == 0:
            lines.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" '
                'y2="{y2:.1f}" class="edge"/>'.format(y2=y2)
            )
        else:
            midpoint_x = (x1 + x2) / 2 + 18 * offset_index
            midpoint_y = (y1 + y2) / 2 - 18 * offset_index
            lines.append(
                f'<path d="M{x1:.1f},{y1:.1f} Q{midpoint_x:.1f},{midpoint_y:.1f} '
                f'{x2:.1f},{y2:.1f}" class="edge" fill="none"/>'
            )

    for vertex in vertices:
        x, y = positions[vertex]
        terminal = vertex in {network.source, network.sink}
        css_class = "terminal" if terminal else "vertex"
        lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" class="{css_class}"/>')
        lines.append(
            f'<text x="{x:.1f}" y="{y + 5:.1f}" class="label" text-anchor="middle">'
            f"{escape(str(vertex))}</text>"
        )
    lines.append("</svg>")
    return "\n".join(lines)


def decomposition_svg(
    root: DecompositionNode, *, width: int = 760, level_height: int = 92
) -> str:
    """Render an S/P decomposition tree in leaf order."""
    positions: dict[int, tuple[float, float]] = {}
    edges: list[tuple[int, int]] = []
    labels: dict[int, str] = {}
    leaf_index = 0
    max_depth = 0

    def visit(node: DecompositionNode, depth: int) -> float:
        nonlocal leaf_index, max_depth
        max_depth = max(max_depth, depth)
        identifier = id(node)
        if node.kind is NodeKind.EDGE:
            x = leaf_index + 0.5
            leaf_index += 1
            labels[identifier] = f"e{node.edge_id}"
        else:
            child_x = []
            for child in node.children:
                child_x.append(visit(child, depth + 1))
                edges.append((identifier, id(child)))
            x = sum(child_x) / len(child_x)
            labels[identifier] = "S" if node.kind is NodeKind.SERIES else "P"
        positions[identifier] = (x, depth)
        return x

    visit(root, 0)
    height = (max_depth + 1) * level_height + 54
    x_scale = (width - 80) / max(1, leaf_index)
    lines = [_svg_header(width, height, "S/P decomposition tree")]
    for parent, child in edges:
        px, py = positions[parent]
        cx, cy = positions[child]
        lines.append(
            f'<line x1="{40 + px * x_scale:.1f}" y1="{38 + py * level_height:.1f}" '
            f'x2="{40 + cx * x_scale:.1f}" y2="{38 + cy * level_height:.1f}" '
            'class="edge"/>'
        )
    for identifier, (x_position, depth) in positions.items():
        x = 40 + x_position * x_scale
        y = 38 + depth * level_height
        is_leaf = labels[identifier].startswith("e")
        css_class = "leaf" if is_leaf else "operator"
        lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="17" class="{css_class}"/>')
        lines.append(
            f'<text x="{x:.1f}" y="{y + 5:.1f}" class="label" text-anchor="middle">'
            f"{labels[identifier]}</text>"
        )
    lines.append("</svg>")
    return "\n".join(lines)


def reduction_trace_svg(steps: tuple[ReductionStep, ...], *, width: int = 900) -> str:
    """Render the reduction sequence as a compact process diagram."""
    box_width, box_height, gap = 130, 74, 24
    required_width = 40 + len(steps) * (box_width + gap)
    width = max(width, required_width)
    height = 150
    lines = [_svg_header(width, height, "TTSP reduction trace")]
    for index, step in enumerate(steps):
        x = 24 + index * (box_width + gap)
        if index:
            lines.append(
                f'<path d="M{x - gap + 3},65 L{x - 5},65" class="edge" '
                'marker-end="url(#arrow)"/>'
            )
        lines.append(
            f'<rect x="{x}" y="28" width="{box_width}" height="{box_height}" '
            'rx="10" class="step"/>'
        )
        label = "PARALLEL" if step.kind.value == "parallel" else "SERIES"
        detail = (
            f"remove {len(step.removed_edge_ids)} edges"
            if step.eliminated_vertex is None
            else f"eliminate {step.eliminated_vertex}"
        )
        lines.append(f'<text x="{x + 12}" y="52" class="step-title">{label}</text>')
        lines.append(f'<text x="{x + 12}" y="75" class="small">{escape(detail)}</text>')
        lines.append(
            f'<text x="{x + 12}" y="93" class="small">{step.remaining_edges} edge(s) left</text>'
        )
    lines.append("</svg>")
    return "\n".join(lines)


def _svg_header(width: int, height: int, title: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b"/></marker>
  <style>
    .edge {{ stroke: #64748b; stroke-width: 2; }}
    .vertex {{ fill: #e2e8f0; stroke: #334155; stroke-width: 2; }}
    .terminal {{ fill: #67e8f9; stroke: #0e7490; stroke-width: 3; }}
    .operator {{ fill: #0f766e; stroke: #134e4a; stroke-width: 2; }}
    .leaf {{ fill: #dbeafe; stroke: #1d4ed8; stroke-width: 2; }}
    .label {{ fill: #0f172a; font: 600 13px ui-monospace, monospace; }}
    .operator + .label {{ fill: #ffffff; }}
    .step {{ fill: #f8fafc; stroke: #475569; stroke-width: 1.5; }}
    .step-title {{ fill: #0f766e; font: 700 13px ui-sans-serif, sans-serif; }}
    .small {{ fill: #334155; font: 12px ui-sans-serif, sans-serif; }}
  </style>
</defs>"""
