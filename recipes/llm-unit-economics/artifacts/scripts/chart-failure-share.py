#!/usr/bin/env python3
"""What "cost per task" is made of: the attempt, or the cleanup.

    python chart-failure-share.py

Expected cost per solved task is attempt / p(success) + (1 − p) · remediation.
For a reliable task the first term is the whole bill. For a task that succeeds
60% of the time and costs $15 to clean up when it fails, 77% of the bill is the
second term — and the model's token price barely moves it.

The bars are sorted by total cost, not by failure share, because the reader's
question is "which task is expensive", and the failure share is the answer to
"why".
"""
from __future__ import annotations

from pathlib import Path

import svgkit as k
from scenarios import failure_rows

OUT = Path(__file__).resolve().parents[1] / "charts" / "failure-share.svg"

ROWS = sorted(failure_rows(), key=lambda row: -row["solved_usd"])
W, H = 980, 600
L, R = 230, 720
T, ROW_H = 164, 60
X_MAX = 8.6


def sx(value):
    return k.scale_linear(value, (0, X_MAX), (L, R))


def main() -> None:
    body = k.header(
        "For hard work, most of the bill is failure cleanup",
        "Expected cost per solved task, Claude Sonnet 4.6. Orange is "
        "(1 - p) times remediation, blue is attempts divided by p. The total is the bar.",
        "Model: llm_econ.py task profiles · p(success) and remediation are assumptions, "
        "not invoices",
    )
    body += k.legend([("attempt cost", k.BLUE), ("failure cleanup", k.ORANGE)], 116)

    for value in (0, 2, 4, 6, 8):
        x = sx(value)
        body.append(k.line(x, T - 16, x, T + ROW_H * len(ROWS) - 20, stroke=k.GRID))
        body.append(k.text(x, T + ROW_H * len(ROWS) - 2, f"${value}",
                           size=11, fill=k.MUTED, anchor="middle", tabular=True))
    body.append(k.text((L + R) / 2, T + ROW_H * len(ROWS) + 22,
                       "$ per solved task", size=11.5, fill=k.MUTED,
                       anchor="middle"))

    for index, row in enumerate(ROWS):
        y = T + index * ROW_H
        body.append(k.text(36, y + 3, row["task"], size=12.5, fill=k.INK,
                           weight="500"))
        body.append(k.text(36, y + 21, f"p(success) {row['p_success']:.0%}",
                           size=11, fill=k.MUTED))

        attempt_w = sx(row["attempt_usd"]) - L
        total_w = sx(row["solved_usd"]) - L
        failure_w = total_w - attempt_w
        bar_h = 22
        body.append(k.bar_h(L, y - bar_h / 2, attempt_w, bar_h, k.BLUE))
        # The 2px surface gap is the separator; no stroke around the segment.
        body.append(k.bar_h(L + attempt_w + 2, y - bar_h / 2,
                            max(failure_w - 2, 0), bar_h, k.ORANGE))

        label = f"{k.usd(row['solved_usd'])} · {row['failure_share']:.0%} cleanup"
        body.append(k.text(L + total_w + 12, y + 4, label,
                           size=11.5, fill=k.INK2, tabular=True))

    body.append(k.footer(
        "Moving this task from DeepSeek to Sonnet changes the solved cost only ~1.3x, "
        "despite a ~30x token-price gap: remediation dominates.", 586))

    OUT.write_text(k.doc(
        W, H,
        "For hard work, most of the bill is failure cleanup",
        "Stacked horizontal bars of expected cost per solved task for six task types, "
        "split into attempt cost and failure cleanup. Knowledge work is 77% cleanup, "
        "CAD 83%, agentic code 20% and chat 8%.",
        body))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
