#!/usr/bin/env python3
"""Two ways a warm cache stops paying: idle time, and partial invalidation.

    python chart-cache-fragility.py

The left panel is a cliff. Below the provider's TTL the prefix stays resident
and the session costs $3.23; one second past it the cache is cold on every turn
and the bill is the cold-cache $21.74. There is no slope between them.

The right panel is the same loss arriving gradually. At a 70% hit rate — well
inside the range production agents report — the bill is $8.78 against $3.23 at
100%, 2.7x the fully-warm cost. An estimate that assumes 100% is not a small
optimism.
"""
from __future__ import annotations

from pathlib import Path

import svgkit as k
from scenarios import TIER_MODELS, PRICING, hit_rows, ttl_rows

OUT = Path(__file__).resolve().parents[1] / "charts" / "cache-fragility.svg"

COLOURS = {"sonnet-4.6": k.BLUE, "gemini-3.1": k.ORANGE, "ds-v4-flash": k.AQUA}
GAPS, TTL = ttl_rows()
RATES, HITS = hit_rows()

W, H = 980, 540
TOP, BOTTOM = 190, 440
PANELS = ((96, 456), (560, 920))
Y_LO, Y_HI = 0.1, 50


def sy(value):
    return k.scale_log(value, (Y_LO, Y_HI), (BOTTOM, TOP))


def panel_frame(x0, x1, title, subtitle):
    out = [k.text(x0, TOP - 42, title, size=13.5, fill=k.INK, weight="600"),
           k.text(x0, TOP - 22, subtitle, size=11.5, fill=k.INK2)]
    out += k.grid_y(None, sy, x0, x1, [0.1, 1, 10, 50],
                    lambda v: f"${v:g}" if v >= 1 else "$0.10")
    out.append(k.line(x0, BOTTOM, x1, BOTTOM, stroke=k.BASELINE))
    return out


def line_series(xs, ys, xscale, colour):
    parts = []
    for (x0, y0), (x1, y1) in zip(zip(xs, ys), list(zip(xs, ys))[1:]):
        parts.append(f"M{xscale(x0):.1f},{sy(y0):.1f} L{xscale(x1):.1f},{sy(y1):.1f}")
    return (f'<path d="{" ".join(parts)}" fill="none" stroke="{colour}" '
            f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')


def main() -> None:
    body = k.header(
        "The cache is either warm or it is not",
        "Left: idle time between turns against session cost. Right: the fraction "
        "of the prefix that hits. One is a cliff; the other is a slow leak.",
        "Model: llm_econ.py · 30-turn agent loop, append caching · Claude Sonnet 4.6, "
        "Gemini 3.1 Pro, DeepSeek V4 Flash",
    )
    body += k.legend([(PRICING[key].name, COLOURS[key], "line") for key in TIER_MODELS], 116)

    # ── left: TTL ──────────────────────────────────────────────────────────
    x0, x1 = PANELS[0]
    body += panel_frame(x0, x1, "Idle time between turns", "5-minute TTL, marked")

    def sx_gap(value):
        return k.scale_log(value, (10, 900), (x0, x1))

    threshold = sx_gap(300)
    body.append(k.line(threshold, TOP, threshold, BOTTOM, stroke=k.BASELINE,
                       width=1, dash="4 4"))
    body.append(k.text(threshold - 8, TOP + 12, "TTL expires", size=11,
                       fill=k.INK2, anchor="end"))
    body.append(k.text(threshold - 8, TOP + 28, "every turn is cold", size=11,
                       fill=k.MUTED, anchor="end"))
    for value, label in ((10, "10s"), (60, "1m"), (300, "5m"), (900, "15m")):
        x = sx_gap(value)
        body.append(k.text(x, BOTTOM + 20, label, size=11, fill=k.MUTED,
                           anchor="middle", tabular=True))
    body.append(k.text((x0 + x1) / 2, BOTTOM + 42, "seconds between turns (log)",
                       size=11, fill=k.MUTED, anchor="middle"))

    for key in TIER_MODELS:
        index = 1 + list(PRICING).index(key)
        ys = [row[index] for row in TTL]
        body.append(line_series(GAPS, ys, sx_gap, COLOURS[key]))
    body.append(k.text(x0 + 8, TOP - 6, "$/session", size=11, fill=k.MUTED))

    # Sonnet's cliff, labelled where it happens.
    sonnet_y = sy(21.7406)
    body.append(k.dot(threshold, sonnet_y, 4.5, k.BLUE))
    body.append(k.text(threshold + 12, sonnet_y - 10, "6.7x", size=12,
                       fill=k.BLUE, weight="600"))

    # ── right: hit rate ────────────────────────────────────────────────────
    x0, x1 = PANELS[1]
    body += panel_frame(x0, x1, "Share of the prefix that hits", "100% is the assumption, not the telemetry")

    def sx_hit(value):
        return k.scale_linear(value, (0, 1), (x0, x1))

    for value, label in ((0, "0%"), (0.25, "25%"), (0.5, "50%"), (0.75, "75%"), (1, "100%")):
        body.append(k.text(sx_hit(value), BOTTOM + 20, label, size=11, fill=k.MUTED,
                           anchor="middle", tabular=True))
    body.append(k.text((x0 + x1) / 2, BOTTOM + 42, "cache hit rate",
                       size=11, fill=k.MUTED, anchor="middle"))

    for key in TIER_MODELS:
        index = 1 + list(PRICING).index(key)
        ys = [row[index] for row in HITS]
        body.append(line_series(RATES, ys, sx_hit, COLOURS[key]))

    # The 70% mark: the loss is already most of the prize.
    at_70 = next(row[1] for row in HITS if round(row[0], 2) == 0.7)
    x70 = sx_hit(0.7)
    body.append(k.line(x70, TOP, x70, BOTTOM, stroke=k.BASELINE, width=1, dash="4 4"))
    body.append(k.dot(x70, sy(at_70), 4.5, k.BLUE))
    body.append(k.text(x70 - 10, sy(at_70) + 20, f"70% hit: ${at_70:.2f}", size=11.5,
                       fill=k.BLUE, weight="600", anchor="end"))
    body.append(k.text(x70 - 10, sy(at_70) + 36, "100% hit: $3.23", size=11,
                       fill=k.INK2, anchor="end"))

    body.append(k.footer(
        "Production cache-hit rates run from 8% to 92% (Requesty, GitHub Copilot); "
        "the dotted line at 100% is nobody's measurement.", 506))

    OUT.write_text(k.doc(
        W, H,
        "The cache is either warm or it is not",
        "Two panels. Left: session cost against seconds between turns for three models, "
        "with a cliff at the 300-second TTL. Right: session cost against cache hit rate, "
        "showing that a 70% hit rate costs 2.7x the fully-warm bill.",
        body))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
