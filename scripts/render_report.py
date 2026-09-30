#!/usr/bin/env python3
"""Render the static order-variant figure from saved Phase 2 evidence."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results" / "invariance" / "variants.json"
OUTPUT = ROOT / "reports" / "study.svg"
EXPECTED = ["original", "reverse", "lexicographic_xyz"] + [f"permutation_{n:02d}" for n in range(20)]


def render(rows: list[dict]) -> str:
    names = [row["name"] for row in rows]
    if names != EXPECTED:
        raise ValueError("saved order variants do not match the frozen protocol order")
    counts = [int(row["false_alarms"]) for row in rows]
    width, height = 1180, 500
    left, top, plot_width, plot_height = 72, 78, 1068, 310
    baseline = top + plot_height
    maximum = 70
    step = plot_width / len(rows)
    bar_width = max(6, step - 8)
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="500" viewBox="0 0 1180 500" role="img" aria-labelledby="title desc">',
        '<title id="title">False alarms across SwitchBench alarm-order variants</title>',
        '<desc id="desc">Twenty-three order variants in frozen protocol order, shown on a zero-based false-alarm axis. Original is marked in blue. Roundtrip and duplicate controls each scored 70 false alarms.</desc>',
        '<rect width="1180" height="500" fill="white"/>',
        '<style>text{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;fill:#20242a}.title{font-size:22px;font-weight:700}.sub{font-size:13px;fill:#58616c}.axis{font-size:12px;fill:#58616c}.label{font-size:10px;fill:#58616c}.note{font-size:12px;fill:#424b55}</style>',
        '<text id="title-text" x="72" y="34" class="title">False alarms across equivalent alarm orders</text>',
        '<text x="72" y="56" class="sub">Fixed detector export and scorer settings · 23 variants in protocol order · zero-based axis</text>',
    ]
    for tick in range(0, 71, 10):
        y = baseline - (tick / maximum) * plot_height
        color = "#9aa5b1" if tick == 0 else "#dfe5ea"
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}" stroke="{color}" stroke-width="1"/>')
        parts.append(f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" class="axis">{tick}</text>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{baseline}" stroke="#7b8794"/>')
    for index, (name, count) in enumerate(zip(names, counts)):
        x = left + index * step + (step - bar_width) / 2
        h = count / maximum * plot_height
        y = baseline - h
        fill = "#1769aa" if name == "original" else "#d86c5b"
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{h:.1f}" fill="{fill}"/>')
        label = "O" if name == "original" else "R" if name == "reverse" else "L" if name == "lexicographic_xyz" else f"P{int(name[-2:])}"
        parts.append(f'<text x="{x + bar_width / 2:.1f}" y="{baseline + 17}" text-anchor="middle" class="label">{escape(label)}</text>')
    parts.extend([
        f'<text x="{left}" y="{baseline + 40}" class="note"><tspan fill="#1769aa">O</tspan> original  ·  R reverse  ·  L lexicographic xyz  ·  P0–P19 independent per-patch permutations</text>',
        '<text x="72" y="458" class="note">Representation controls outside the order series: lossless JSON roundtrip = 70  ·  exact duplicate insertion = 70</text>',
        '<text x="72" y="480" class="sub">Bar position indicates the frozen protocol order and does not imply a time trend or statistical significance</text>',
        '</svg>',
    ])
    return "\n".join(parts) + "\n"


def main() -> None:
    evidence = json.loads(INPUT.read_text(encoding="utf-8"))
    rows = evidence["variants"][:23]
    OUTPUT.write_text(render(rows), encoding="utf-8")


if __name__ == "__main__":
    main()
