#!/usr/bin/env python3
"""A 30-turn agent loop: what caching the whole history is worth.

    python chart-caching-modes.py

The first simulator cached a fixed prefix (the system prompt) and concluded
caching was nearly worthless. It was right about that policy and wrong about
the realistic one. An agent loop is append-only: last turn's entire context is
this turn's prefix, so the cacheable set grows with the session.

No cache and fixed prefix sit almost on top of each other. Appending the whole
history cuts the bill 82%. The gap between those two dots is the finding.
"""
from __future__ import annotations

from pathlib import Path

import svgkit as k
from scenarios import caching_rows

OUT = Path(__file__).resolve().parents[1] / "charts" / "caching-modes.svg"

ROWS = sorted(caching_rows(), key=lambda row: row[4])
W, H = 980, 620
L, R = 250, 720
T, ROW_H = 150, 60


def sx(value):
    return k.scale_log(value, (0.1, 60), (L, R))


def main() -> None:
    body = k.header(
        "Cache the whole history, not a prefix",
        "30-turn agent loop, 10K to 372K context. Appending the history cuts the "
        "bill 82%; caching a fixed 8K prefix cuts it 4%.",
        "Model: llm_econ.py · Claude Sonnet 4.6 list prices, early 2026 · $ per 30-turn session",
    )
    body += k.legend([
        ("no cache", k.RED, "dot"),
        ("fixed prefix", k.MUTED, "dot"),
        ("append history", k.BLUE, "dot"),
    ], 112)

    # x grid: one decade either side of the interesting range.
    for value, label in ((0.1, "$0.10"), (1, "$1"), (10, "$10"), (60, "$60")):
        x = sx(value)
        body.append(k.line(x, T - 10, x, T - 10 + ROW_H * len(ROWS), stroke=k.GRID))
        body.append(k.text(x, T - 20 + ROW_H * len(ROWS) + 8, label, size=11,
                           fill=k.MUTED, anchor="middle", tabular=True))
    body.append(k.text((L + R) / 2, T + ROW_H * len(ROWS) + 36,
                       "$ per 30-turn session (log scale)", size=11.5,
                       fill=k.MUTED, anchor="middle"))

    for index, (key, name, none, fixed, append) in enumerate(ROWS):
        y = T + index * ROW_H
        # Row label and the policy it describes, not a colour key.
        body.append(k.text(36, y + 5, name, size=12.5, fill=k.INK, weight="500"))
        body.append(k.text(36, y + 23, f"{k.usd(none)} uncached", size=11, fill=k.MUTED))

        # The distance the reader is being asked to see.
        body.append(k.line(sx(none), y, sx(append), y, stroke=k.GRID, width=1))
        # No-cache and fixed-prefix land almost on top of each other; a small
        # vertical offset keeps both visible without implying a different value.
        body.append(k.dot(sx(none), y + 5, 4.5, k.RED))
        body.append(k.dot(sx(fixed), y - 5, 4.5, k.MUTED))
        body.append(k.dot(sx(append), y, 6, k.BLUE))

        saved = 1 - append / none
        body.append(k.text(R + 16, y + 4, k.usd(append), size=12, fill=k.INK,
                           weight="600", tabular=True))
        body.append(k.text(R + 78, y + 4, f"{saved * 100:.1f}% saved", size=11,
                           fill=k.INK2, tabular=True))

    body.append(k.footer(
        "Fixed-prefix caching is not a cheap version of append caching; for this "
        "workload it is a rounding error. The lever is the grown history.", 588))

    OUT.write_text(k.doc(
        W, H,
        "Cache the whole history, not a prefix",
        "Session cost of a 30-turn agent loop for five models under three caching "
        "policies. No cache and fixed-prefix caching are almost identical; appending "
        "the whole history cuts the Claude Sonnet bill from $17.44 to $3.23, 82%.",
        body))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
