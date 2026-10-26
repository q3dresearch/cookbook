#!/usr/bin/env python3
"""Which driver moves the bill? Reliable work and judgment work disagree.

    python chart-tornado.py

Each bar swings one driver from its P10 to its P90 and re-prices the task,
holding the others at their base. For agentic code the biggest lever is token
volume ($6.18). For a knowledge deliverable it is remediation ($12.27), which
is the cost of being wrong — not the cost of a token.

Two panels share one dollar scale, so the comparison is between the panels and
not only within them.
"""
from __future__ import annotations

from pathlib import Path

import svgkit as k
from scenarios import tornado_rows

OUT = Path(__file__).resolve().parents[1] / "charts" / "tornado.svg"

ALL = tornado_rows()
TASKS = (("agentic code task", "agentic code", 260, 570),
         ("knowledge deliverable", "knowledge deliverable", 650, 960))
ORDER = ("remediation $", "token volume", "p(success)", "cache hit")
W, H = 1040, 540
T, ROW_H = 200, 64
X_MAX = 18


def sx(value, x0, x1):
    return k.scale_linear(value, (0, X_MAX), (x0, x1))


def driver_label(name, low, high):
    if name == "token volume":
        return f"{low:.2f}x to {high:.2f}x"
    if name == "remediation $":
        return f"${low:.2f} to ${high:.2f}"
    return f"{low:.0%} to {high:.0%}"


def main() -> None:
    body = k.header(
        "Optimize tokens for reliable work; reliability for judgment work",
        "One-at-a-time P10 to P90 swing in cost per solved task. Blue is the cheap "
        "end, red the expensive end. Both panels share a dollar scale.",
        "Model: llm_econ.py Monte Carlo, Claude Sonnet 4.6 · 4,000 runs per driver · "
        "base cost in each panel title",
    )
    body += k.legend([("cost below base", k.BLUE), ("cost above base", k.RED)], 116)

    for task_name, title, x0, x1 in TASKS:
        rows = [row for row in ALL if row["task"] == task_name]
        by_driver = {row["driver"]: row for row in rows}
        base = rows[0]["base"]
        body.append(k.text(x0, T - 50, title, size=13.5, fill=k.INK, weight="600"))
        body.append(k.text(x0, T - 30, f"base {k.usd(base, 2)}", size=11.5,
                           fill=k.INK2))

        base_x = sx(base, x0, x1)
        body.append(k.line(base_x, T - 18, base_x, T + ROW_H * len(ORDER) - 22,
                          stroke=k.BASELINE, width=1))
        for value in (0, 5, 10, 15):
            x = sx(value, x0, x1)
            body.append(k.line(x, T + ROW_H * len(ORDER) - 18, x,
                               T + ROW_H * len(ORDER) - 14, stroke=k.BASELINE))
            body.append(k.text(x, T + ROW_H * len(ORDER) + 4, f"${value}",
                               size=10.5, fill=k.MUTED, anchor="middle",
                               tabular=True))

        for index, driver in enumerate(ORDER):
            row = by_driver[driver]
            y = T + index * ROW_H
            low = min(row["cost_low"], row["cost_high"])
            high = max(row["cost_low"], row["cost_high"])
            low_x, high_x = sx(low, x0, x1), sx(high, x0, x1)
            left_w, right_w = base_x - low_x, high_x - base_x
            bar_h = 18
            if left_w > 0:
                body.append(k.bar_h_left(base_x - 1, y - bar_h / 2, left_w - 1,
                                         bar_h, k.BLUE))
            if right_w > 0:
                body.append(k.bar_h(base_x + 1, y - bar_h / 2, right_w - 1,
                                    bar_h, k.RED))

            if right_w >= left_w:
                label_x, anchor = high_x + 8, "start"
            else:
                label_x, anchor = low_x - 8, "end"
            body.append(k.text(label_x, y + 4, k.usd(row["swing"], 2), size=11,
                               fill=k.INK2, anchor=anchor, tabular=True,
                               weight="600"))

    # Driver names once, shared by both panels. The P10-P90 range differs by
    # task, so it is not printed here; printing one task's range for both panels
    # would be a quiet lie.
    for index, driver in enumerate(ORDER):
        y = T + index * ROW_H
        body.append(k.text(36, y + 4, driver, size=12.5, fill=k.INK,
                           weight="500"))

    body.append(k.footer(
        "The two panels answer different questions. Token price is the lever when the "
        "task usually succeeds; remediation is the lever when it does not.", 516))

    OUT.write_text(k.doc(
        W, H,
        "Optimize tokens for reliable work; reliability for judgment work",
        "Two tornado panels comparing one-at-a-time P10 to P90 cost swings for agentic "
        "code and a knowledge deliverable. Code is driven by token volume ($6.18), "
        "knowledge work by remediation ($12.27).",
        body))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
