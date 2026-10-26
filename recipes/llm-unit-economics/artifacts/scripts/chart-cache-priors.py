#!/usr/bin/env python3
"""The cache-hit assumption, against production telemetry.

    python chart-cache-priors.py

The first version of this model assumed a 100% cache-hit rate. Real coding
agents report 8% to 92%, depending on the agent and on whether the cache
survives a turn boundary or a model switch. The 100% line is drawn because it
is the number the model used to assume, not because anyone measures it.

One series, so no legend: the title says what is plotted. The model-switch bar
is the accent because it is the case that breaks the caching story outright.
"""
from __future__ import annotations

from pathlib import Path

import svgkit as k
from llm_econ import CACHE_PRIORS

OUT = Path(__file__).resolve().parents[1] / "charts" / "cache-priors.svg"

ROWS = sorted(CACHE_PRIORS.items(), key=lambda item: -item[1])
W, H = 980, 610
L, R = 220, 720
T, ROW_H = 178, 38


def sx(value):
    return k.scale_linear(value, (0, 1.05), (L, R))


def main() -> None:
    body = k.header(
        "Real cache-hit rates are 8% to 92%, not 100%",
        "Session-level cache hit rate by coding agent, production telemetry. "
        "The 100% line is the assumption this model started with.",
        "Sources: Requesty coding-agent telemetry, GitHub Copilot production study · "
        "Apr 2026 · shares are fractions of the cacheable prefix",
    )

    for value in (0, 0.25, 0.5, 0.75, 1.0):
        x = sx(value)
        body.append(k.line(x, T - 20, x, T + ROW_H * len(ROWS) - 16, stroke=k.GRID))
        body.append(k.text(x, T + ROW_H * len(ROWS) + 4, f"{value:.0%}",
                           size=11, fill=k.MUTED, anchor="middle", tabular=True))
    for index, (agent, rate) in enumerate(ROWS):
        y = T + index * ROW_H
        colour = k.RED if agent == "Copilot (model switch)" else k.BLUE
        body.append(k.text(36, y + 4, agent, size=12.5, fill=k.INK, weight="500"))
        body.append(k.bar_h(L, y - 9, sx(rate) - L, 18, colour))
        body.append(k.text(sx(rate) + 10, y + 4, f"{rate:.1%}", size=11.5,
                           fill=k.INK2, tabular=True))

    # The old assumption, as a reference rather than a series.
    x100 = sx(1.0)
    body.append(k.line(x100, T - 34, x100, T + ROW_H * len(ROWS) - 16,
                       stroke=k.INK2, width=1, dash="5 4"))
    body.append(k.text(x100 - 8, T - 40, "100%: the old assumption", size=11.5,
                       fill=k.INK2, anchor="end", weight="600"))

    body.append(k.footer(
        "A model switch drops the hit rate to 8%: the prefix is still there, but it "
        "belongs to a different model. The cheap-token plan has to survive that.", 578))

    OUT.write_text(k.doc(
        W, H,
        "Real cache-hit rates are 8% to 92%, not 100%",
        "Horizontal bars of session-level cache hit rate for ten coding agents and "
        "conditions, from Claude Code at 91.9% to Copilot on a model switch at 8%, "
        "against a 100% reference line.",
        body))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
