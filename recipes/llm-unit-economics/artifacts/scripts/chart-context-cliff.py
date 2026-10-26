#!/usr/bin/env python3
"""One request, five thousand output tokens: what a bigger prompt costs.

    python chart-context-cliff.py

Flat-priced models scale linearly with prompt length. Tiered models do not:
above a threshold the WHOLE request re-prices, so the line steps rather than
bends. Comparing 200K to 1M, the flat model rises 4.6x and the tiered one 8.9x.
That gap is the reason "the biggest window is free" is only true for some
price sheets, and it is invisible in a per-token quote.

Output is held fixed at 5,000 tokens so the only moving part is input.
"""
from __future__ import annotations

from pathlib import Path

import svgkit as k
from scenarios import context_cliff_rows

OUT = Path(__file__).resolve().parents[1] / "charts" / "context-cliff.svg"

MODELS = (
    ("sonnet-4.6", "Claude Sonnet 4.6 (flat)", k.BLUE),
    ("gemini-3.1", "Gemini 3.1 Pro (tiered at 200K)", k.ORANGE),
    ("ds-v4-flash", "DeepSeek V4 Flash (flat)", k.AQUA),
)
PROMPTS, SERIES = context_cliff_rows()

W, H = 980, 560
L, R, T, B = 96, 700, 136, 430
Y_MAX = 4.6


def sx(value):
    return k.scale_log(value, (10_000, 1_000_000), (L, R))


def sy(value):
    return k.scale_linear(value, (0, Y_MAX), (B, T))


def main() -> None:
    body = k.header(
        "The 200K cliff is a step, not a slope",
        "One request with 5,000 output tokens. The tiered prompt is re-priced "
        "in full above the line, so 200K to 1M costs 8.9x against 4.6x flat.",
        "Model: llm_econ.py · list prices, early 2026 · tier multiplier applies to the whole request",
    )

    body += k.legend([(label, colour, "line") for _, label, colour in MODELS], 112)

    # Horizontal grid and y-axis ticks.
    body += k.grid_y(None, sy, L, R, [0, 1, 2, 3, 4], lambda v: f"${v:,.0f}")
    body.append(k.line(L, B, R, B, stroke=k.BASELINE))

    # The tier boundary.
    x200 = sx(200_000)
    body.append(k.line(x200, T, x200, B, stroke=k.BASELINE, width=1, dash="4 4"))
    body.append(k.text(x200 - 8, T + 14, "200K tier boundary", size=11, fill=k.INK2,
                       anchor="end"))
    body.append(k.text(x200 - 8, T + 30, "above it the whole prompt re-prices",
                       size=11, fill=k.MUTED, anchor="end"))

    # x-axis ticks.
    for value, label in ((10_000, "10K"), (50_000, "50K"), (100_000, "100K"),
                         (250_000, "250K"), (500_000, "500K"), (1_000_000, "1M")):
        x = sx(value)
        body.append(k.line(x, B, x, B + 4, stroke=k.BASELINE))
        body.append(k.text(x, B + 22, label, size=11, fill=k.MUTED,
                           anchor="middle", tabular=True))
    body.append(k.text((L + R) / 2, B + 48, "prompt tokens", size=11.5,
                       fill=k.MUTED, anchor="middle"))

    # Lines. Marker on the points that matter, not every sample.
    for key, label, colour in MODELS:
        points = SERIES[key]
        segments = []
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            segments.append(f"M{sx(x0):.1f},{sy(y0):.1f} L{sx(x1):.1f},{sy(y1):.1f}")
        body.append(f'<path d="{" ".join(segments)}" fill="none" stroke="{colour}" '
                    f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
        for ctx, value in points:
            if ctx in (200_000, 1_000_000):
                body.append(k.dot(sx(ctx), sy(value), 4.5, colour))
        end_value = points[-1][1]
        body.append(k.text(R + 16, sy(end_value) + 4, label, size=11.5, fill=k.INK))
        body.append(k.text(R + 16, sy(end_value) + 20, k.usd(end_value), size=11.5,
                           fill=k.INK2, tabular=True))

    # The two ratios, drawn where the reader is already looking.
    body.append(k.text(L + 14, T + 52, "200K to 1M", size=11, fill=k.MUTED))
    body.append(k.text(L + 14, T + 70, "4.6x flat", size=13, fill=k.BLUE, weight="600"))
    body.append(k.text(L + 120, T + 70, "8.9x tiered", size=13, fill=k.ORANGE,
                       weight="600"))

    body.append(k.footer(
        "A flat quote hides this. Tiered billing is not a surcharge on the excess: "
        "crossing the line reprices every token already sent.", 520))

    OUT.write_text(k.doc(
        W, H,
        "The 200K cliff is a step, not a slope",
        "Cost of one request with a 5,000-token output against prompt length for "
        "Claude Sonnet 4.6, Gemini 3.1 Pro and DeepSeek V4 Flash. The tiered Gemini "
        "line steps at 200K and rises 8.9x to 1M, against 4.6x for the flat model.",
        body))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
