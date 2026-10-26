#!/usr/bin/env python3
"""Where the GPU floor crosses the list price.

    python chart-server-floor.py

The user's bill is drawn as the list-price line. The provider's floor is the
roofline cost of GPU-seconds for the same request: prefill (compute-bound, and
quadratic in context) plus decode (KV-read bound). At short context the gap is
wide. At 1M the 70B GQA floor is $3.92 against a $3.02 list price — the provider
loses on every request. Hybrid attention moves the floor to $1.16, which is why
the architecture matters more than the price sheet.

This is a floor, not a P&L: no power, idle capacity, networking or margin. The
direction is the finding, not the third decimal.
"""
from __future__ import annotations

from pathlib import Path

import svgkit as k
from scenarios import server_rows

OUT = Path(__file__).resolve().parents[1] / "charts" / "server-floor.svg"

ROWS = server_rows()
ARCHES = (
    ("gqa-70b", "70B GQA", k.BLUE),
    ("gqa-70b-h", "70B GQA, hybrid attention", k.ORANGE),
    ("mla-600b", "671B MLA (40B active)", k.AQUA),
)
W, H = 980, 600
L, R, T, B = 96, 700, 180, 446


def sx(value):
    return k.scale_log(value, (10_000, 1_000_000), (L, R))


def sy(value):
    return k.scale_log(value, (0.003, 8), (B, T))


def main() -> None:
    body = k.header(
        "At 1M context the GPU floor crosses the list price",
        "One request, 1,000 output tokens, batch 64 (compute only). Long-context "
        "serving is compute-bound, so the floor rises faster than a per-token quote.",
        "Model: llm_econ.py · H100 at $2.50/hr, 8x H100 at $20/hr · MFU 0.50, MBU 0.75 · floor only",
    )
    body += k.legend(
        [(label, colour, "line") for _, label, colour in ARCHES]
        + [("Claude Sonnet 4.6 list price", k.INK2, "line")], 148)

    # Axes.
    body += k.grid_y(None, sy, L, R, [0.01, 0.1, 1, 10],
                     lambda v: f"${v:g}" if v >= 0.01 else f"${v:g}")
    body.append(k.line(L, B, R, B, stroke=k.BASELINE))
    for value, label in ((10_000, "10K"), (30_000, "30K"), (100_000, "100K"),
                         (300_000, "300K"), (1_000_000, "1M")):
        x = sx(value)
        body.append(k.line(x, B, x, B + 4, stroke=k.BASELINE))
        body.append(k.text(x, B + 22, label, size=11, fill=k.MUTED,
                           anchor="middle", tabular=True))
    body.append(k.text((L + R) / 2, B + 48, "context tokens (log)", size=11.5,
                       fill=k.MUTED, anchor="middle"))


    # Architecture floors.
    by_arch = {}
    for key, _, _ in ARCHES:
        by_arch[key] = sorted([row for row in ROWS if row["arch"] == key],
                              key=lambda row: row["context"])

    for key, label, colour in ARCHES:
        rows = by_arch[key]
        d = []
        for left, right in zip(rows, rows[1:]):
            d.append(f"M{sx(left['context']):.1f},{sy(left['server_usd']):.1f} "
                     f"L{sx(right['context']):.1f},{sy(right['server_usd']):.1f}")
        body.append(f'<path d="{" ".join(d)}" fill="none" stroke="{colour}" '
                    f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')

    # The list price for the same request, as a reference line.
    list_rows = by_arch["gqa-70b"]
    d = []
    for left, right in zip(list_rows, list_rows[1:]):
        d.append(f"M{sx(left['context']):.1f},{sy(left['user_usd']):.1f} "
                 f"L{sx(right['context']):.1f},{sy(right['user_usd']):.1f}")
    body.append(f'<path d="{" ".join(d)}" fill="none" stroke="{k.INK2}" '
                f'stroke-width="2" stroke-dasharray="5 4" stroke-linecap="round"/>')

    # End labels, one line each, staggered where the lines converge.
    ends = [
        ("mla-600b", 5.743, k.AQUA, "$5.74  671B MLA", -10),
        ("gqa-70b", 3.920, k.BLUE, "$3.92  70B GQA", 4),
        ("price", 3.015, k.INK2, "$3.02  list price", 22),
        ("gqa-70b-h", 1.161, k.ORANGE, "$1.16  hybrid", 2),
    ]
    for key, value, colour, label, offset in ends:
        body.append(k.dot(R, sy(value), 4.5, colour))
        body.append(k.text(R + 16, sy(value) + offset, label, size=11.5,
                           fill=k.INK))
        body.append(k.line(R + 4, sy(value), R + 12, sy(value), stroke=colour, width=1))

    # The inversion, said once.
    body.append(k.line(sx(1_000_000), T, sx(1_000_000), B, stroke=k.BASELINE,
                       width=1, dash="4 4"))
    body.append(k.text(sx(120_000), T + 34,
                       "At 1M the 70B floor is $3.92", size=11.5, fill=k.INK2,
                       weight="600"))
    body.append(k.text(sx(120_000), T + 51,
                       "against a $3.02 list price. Hybrid:", size=11, fill=k.MUTED))
    body.append(k.text(sx(120_000), T + 67,
                       "$1.16, still above water.", size=11, fill=k.MUTED))

    body.append(k.footer(
        "Hybrid attention (one full layer in four) cuts the 1M floor 3.4x. A cache "
        "hit removes prefill but not the KV reads during decode.", 548))
    body.append(k.text(
        36, 566, "Compute floor only: at 1M the 70B GQA KV is 164 GB per sequence, "
        "beyond one 80 GB H100. Not a deployable configuration.", size=11,
        fill=k.MUTED))

    OUT.write_text(k.doc(
        W, H,
        "At 1M context the GPU floor crosses the list price",
        "Log-log chart of server GPU cost per request against context length for "
        "70B GQA, hybrid-attention 70B and 671B MLA, against a flat $3 per million "
        "list price. At 1M the GQA floor is $3.92 against $3.02 list, while hybrid is $1.16.",
        body))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
