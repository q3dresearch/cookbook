#!/usr/bin/env python3
"""The point estimate is not the budget.

    python chart-uncertainty.py

Six tasks, 2,000 simulated runs each. The bar is P10–P90 and the dot is P50.
The small tick is what the deterministic model says. Every task's P90 lands
2.4x to 2.9x above that tick, which is why the planning number is P90 and the
point estimate is only a median-shaped guess.

The simulation samples four things at once: p(success) (Beta), cache-hit rate
(Beta), run-to-run token volume (lognormal, sigma 0.85) and remediation
(lognormal). It is still a model; the dispersion is an assumption, not a
measured variance.
"""
from __future__ import annotations

from pathlib import Path

import svgkit as k
from scenarios import mc_rows

OUT = Path(__file__).resolve().parents[1] / "charts" / "uncertainty.svg"

ROWS = sorted(mc_rows(), key=lambda row: -row["p90"])
W, H = 980, 590
L, R = 250, 730
T, ROW_H = 172, 54


def sx(value):
    return k.scale_log(value, (0.03, 30), (L, R))


def main() -> None:
    body = k.header(
        "Budget at P90, not the point estimate",
        "2,000 runs per task. Bars span P10 to P90, the dot is P50, the tick is the "
        "deterministic model. P90 is 2.4x to 2.9x the point estimate.",
        "Model: llm_econ.py Monte Carlo, Claude Sonnet 4.6 · token variance lognormal "
        "sigma 0.85 · 2,000 runs, seed 7",
    )
    body += k.legend([
        ("P10 to P90", k.BLUE_RAMP[3], "line"),
        ("P50", k.BLUE, "dot"),
        ("deterministic", k.INK2, "line"),
    ], 116)

    for value, label in ((0.1, "$0.10"), (1, "$1"), (10, "$10")):
        x = sx(value)
        body.append(k.line(x, T - 16, x, T + ROW_H * len(ROWS) - 18, stroke=k.GRID))
        body.append(k.text(x, T + ROW_H * len(ROWS) + 2, label, size=11,
                           fill=k.MUTED, anchor="middle", tabular=True))
    body.append(k.text((L + R) / 2, T + ROW_H * len(ROWS) + 26,
                       "$ per solved task (log)", size=11.5, fill=k.MUTED,
                       anchor="middle"))

    for index, row in enumerate(ROWS):
        y = T + index * ROW_H
        body.append(k.text(36, y + 4, row["task"], size=12.5, fill=k.INK,
                           weight="500"))
        multiple = row["p90"] / row["point"] if row["point"] else 0
        body.append(k.text(36, y + 22, f"P90 {multiple:.1f}x point", size=11,
                           fill=k.MUTED))

        # The interval is the mark; the median is the dot on it.
        body.append(k.line(sx(row["p10"]), y, sx(row["p90"]), y,
                           stroke=k.BLUE, width=2))
        body.append(k.line(sx(row["p10"]), y - 4, sx(row["p10"]), y + 4,
                           stroke=k.BLUE, width=2))
        body.append(k.line(sx(row["p90"]), y - 4, sx(row["p90"]), y + 4,
                           stroke=k.BLUE, width=2))
        body.append(k.dot(sx(row["p50"]), y, 5, k.BLUE))
        body.append(k.line(sx(row["point"]), y - 7, sx(row["point"]), y + 7,
                           stroke=k.INK2, width=2))

        body.append(k.text(R + 16, y + 4, k.usd(row["p90"], 2), size=12,
                           fill=k.INK, weight="600", tabular=True))
        body.append(k.text(R + 16, y + 22, "P90", size=10.5, fill=k.MUTED))

    body.append(k.footer(
        "The deterministic figures elsewhere in this recipe are the tick, not the dot. "
        "For budgeting, use the right-hand number.", 560))

    OUT.write_text(k.doc(
        W, H,
        "Budget at P90, not the point estimate",
        "Horizontal interval chart of P10 to P90 cost per solved task for six tasks, "
        "with P50 dots and deterministic ticks. Knowledge work has a P90 of $19.45 "
        "against a $7.79 point estimate.",
        body))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
