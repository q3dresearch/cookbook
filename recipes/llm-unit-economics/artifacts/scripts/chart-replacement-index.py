#!/usr/bin/env python3
"""The replacement index: what an hour of replaced human work costs.

    python chart-replacement-index.py

AI dollars per solved task divided by the human hours that task takes. Against
a $70 loaded hourly rate, the modelled answer is $0.74–$1.45 per human-hour
equivalent — 48x to 95x cheaper. That is not a claim that the work is
equivalent: it excludes human-in-the-loop review, verification, integration and
the cost of the failures the p(success) term already prices.

The reference line is the whole point. Without it the dots are just small
numbers; with it, the distance is the claim.
"""
from __future__ import annotations

from pathlib import Path

import svgkit as k
from scenarios import replacement_rows

OUT = Path(__file__).resolve().parents[1] / "charts" / "replacement-index.svg"

ROWS = sorted(replacement_rows(), key=lambda row: -row["human_x"])
W, H = 980, 580
L, R = 230, 720
T, ROW_H = 172, 54
HUMAN_RATE = 70.0


def sx(value):
    return k.scale_log(value, (0.5, 120), (L, R))


def main() -> None:
    body = k.header(
        "A replaced human-hour costs $0.74 to $1.45, not $70",
        "AI dollars per human-hour equivalent, Claude Sonnet 4.6. Before review, "
        "verification, integration and the failures the model already prices.",
        "Model: llm_econ.py task profiles · loaded human rate $70/hr · ratios are "
        "human cost divided by AI cost",
    )

    for value, label in ((1, "$1"), (10, "$10"), (100, "$100")):
        x = sx(value)
        body.append(k.line(x, T - 18, x, T + ROW_H * len(ROWS) - 18, stroke=k.GRID))
        body.append(k.text(x, T + ROW_H * len(ROWS) + 2, label, size=11,
                           fill=k.MUTED, anchor="middle", tabular=True))
    body.append(k.text((L + R) / 2, T + ROW_H * len(ROWS) + 26,
                       "$ per human-hour equivalent (log)", size=11.5,
                       fill=k.MUTED, anchor="middle"))

    human_x = sx(HUMAN_RATE)
    body.append(k.line(human_x, T - 26, human_x, T + ROW_H * len(ROWS) - 18,
                       stroke=k.INK2, width=1, dash="5 4"))
    body.append(k.text(human_x - 8, T - 32, "$70 human loaded rate", size=11.5,
                       fill=k.INK2, anchor="end", weight="600"))

    for index, row in enumerate(ROWS):
        y = T + index * ROW_H
        body.append(k.text(36, y + 4, row["task"], size=12.5, fill=k.INK,
                           weight="500"))
        body.append(k.text(36, y + 22, f"{row['human_hours']:g} human hr",
                           size=11, fill=k.MUTED))
        body.append(k.dot(sx(row["ai_usd_per_hour"]), y, 6, k.BLUE))
        body.append(k.text(R + 16, y + 4, f"{row['human_x']:.0f}x cheaper",
                           size=12, fill=k.INK, weight="600", tabular=True))
        body.append(k.text(R + 16, y + 22, k.usd(row["ai_usd_per_hour"], 2),
                           size=11, fill=k.INK2, tabular=True))

    note = ("The weakest case is the highest-value one: knowledge deliverables carry "
            "a 60% success rate, so failure cleanup eats the margin. Treat this as the "
            "ceiling of the saving, not the saving.")
    for line_no, part in enumerate(k.wrap(note, 900, 11)):
        body.append(k.text(36, 542 + line_no * 16, part, size=11, fill=k.MUTED))

    OUT.write_text(k.doc(
        W, H,
        "A replaced human-hour costs $0.74 to $1.45, not $70",
        "Dot plot on a log scale of AI dollars per human-hour equivalent for six task "
        "types against a $70 loaded human hourly rate. Agentic code is $0.74 (95x "
        "cheaper), CAD $1.45 (48x cheaper).",
        body))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
