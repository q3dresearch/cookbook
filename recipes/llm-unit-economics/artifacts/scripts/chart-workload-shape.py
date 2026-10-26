#!/usr/bin/env python3
"""The shape of a workload is its input:output ratio, not its size.

    python chart-workload-shape.py

Every task is one request-shaped unit with two token counts. Drawn as a
dumbbell, the distance between the dots is the ratio, and the ratio is what
decides which lever exists: an input-heavy task can be cached, an output-heavy
one cannot. Code is 55:1 and RAG 83:1; SVG is 1:6 the other way.

Totals are drawn on a log scale because they span four orders of magnitude.
Read the ratio off the annotation, not the distance on screen.
"""
from __future__ import annotations

from pathlib import Path

import svgkit as k
from scenarios import workload_rows

OUT = Path(__file__).resolve().parents[1] / "charts" / "workload-shape.svg"

ROWS = sorted(workload_rows(), key=lambda row: -row["ratio"])
W, H = 980, 590
L, R = 250, 730
T, ROW_H = 168, 52


def sx(value):
    return k.scale_log(value, (500, 3_000_000), (L, R))


def ratio_label(ratio):
    if ratio >= 10:
        return f"{ratio:,.0f}:1"
    if ratio >= 1:
        return f"{ratio:,.1f}:1"
    inverse = 1 / ratio
    return f"1:{inverse:,.0f}" if inverse >= 10 else f"1:{inverse:,.1f}"


def main() -> None:
    body = k.header(
        "Code and RAG are input-heavy; SVG is output-heavy",
        "Tokens per task on a log scale. The ratio decides which lever exists: "
        "a cache can only help the side that is re-sent.",
        "Model: llm_econ.py task profiles, seeded from Vantage, GDPval and Playcode · 2026",
    )
    body += k.legend([("input tokens", k.BLUE), ("output tokens", k.ORANGE)], 112)

    for value, label in ((1_000, "1K"), (10_000, "10K"), (100_000, "100K"),
                         (1_000_000, "1M")):
        x = sx(value)
        body.append(k.line(x, T - 18, x, T + ROW_H * len(ROWS) - 18, stroke=k.GRID))
        body.append(k.text(x, T + ROW_H * len(ROWS) + 4, label, size=11,
                           fill=k.MUTED, anchor="middle", tabular=True))
    body.append(k.text((L + R) / 2, T + ROW_H * len(ROWS) + 28,
                       "tokens per task (log)", size=11.5, fill=k.MUTED,
                       anchor="middle"))

    for index, row in enumerate(ROWS):
        y = T + index * ROW_H
        body.append(k.text(36, y + 4, row["task"], size=12.5, fill=k.INK,
                           weight="500"))
        body.append(k.text(36, y + 22, row["category"], size=11, fill=k.MUTED))

        x_in, x_out = sx(row["tokens_in"]), sx(row["tokens_out"])
        body.append(k.line(min(x_in, x_out), y, max(x_in, x_out), y,
                           stroke=k.GRID, width=1))
        body.append(k.dot(x_in, y, 5.5, k.BLUE))
        body.append(k.dot(x_out, y, 5.5, k.ORANGE))

        body.append(k.text(R + 16, y + 4, ratio_label(row["ratio"]), size=12,
                           fill=k.INK, weight="600", tabular=True))

        # Label the two extremes on the chart itself; the axis carries the rest.
        if row["task"] in ("RAG / doc summarization", "SVG / vector art"):
            body.append(k.text(x_in, y - 14, k.tokens(row["tokens_in"]), size=11,
                               fill=k.BLUE, anchor="middle", tabular=True))
            body.append(k.text(x_out, y - 14, k.tokens(row["tokens_out"]), size=11,
                               fill=k.ORANGE, anchor="middle", tabular=True))

    body.append(k.footer(
        "A cache is a prefix lever, so it helps the left-hand workloads. For SVG the "
        "bill is generation, and no amount of prefix reuse changes it.", 552))

    OUT.write_text(k.doc(
        W, H,
        "Code and RAG are input-heavy; SVG is output-heavy",
        "Dumbbell chart of input and output tokens per task on a log scale. RAG is "
        "83:1 input-heavy, agentic code 55:1, knowledge work 23:1, chat 7.5:1, CAD 3:1 "
        "and SVG 1:6 output-heavy.",
        body))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
