#!/usr/bin/env python3
"""Whether the licence queue is actually the constraint on growth.

    python chart-constraint.py <applications.csv> <sites.csv>

A queue holding 430,838 tonnes of applications reads as a bottleneck until you
ask what is already licensed. Norway has 3.86 million tonnes of licensed capacity
and 1.44 million of it — 37%, across 464 sites — has no fish in it. Idle licensed
capacity is more than three times the entire pending queue.

That does not make the queue harmless, and it does not make the idle capacity
available: salmon sites are deliberately fallowed between production cycles, so
some share of that 37% is a working farm between crops rather than dormant
capacity. What it does rule out is the claim this recipe previously made — that
licence availability is what binds Norwegian salmon growth. Whatever the
constraint is, there is more capacity sitting empty than waiting to be granted.

Capacity is counted only where the licence states tonnes. The field also carries
STK, a count of individual fish, and DA, an area in dekar; summing those as mass
produced 87 million tonnes against a national output near 1.5 million.
"""
from __future__ import annotations

import collections
import csv
import sys
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "constraint.svg"

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE, STOCKED, IDLE, QUEUE = "#e3e2db", "#3f7d3a", "#b5651d", "#2361b0"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    apps = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
    sites = list(csv.DictReader(open(sys.argv[2], encoding="utf-8")))

    def t(r):
        try:
            return float(r["capacity_tonnes"])
        except (TypeError, ValueError, KeyError):
            return 0.0

    stocked = sum(t(r) for r in sites if r["has_fish"] == "Ja")
    idle = sum(t(r) for r in sites if r["has_fish"] == "Nei")
    n_idle = sum(1 for r in sites if r["has_fish"] == "Nei")
    pending = 0.0
    for r in apps:
        if r["layer"] != "pending":
            continue
        try:
            pending += float(r["biomass_tonnes"])
        except (TypeError, ValueError):
            pass

    bars = [("Licensed, fish in the water", stocked, STOCKED,
             f"{sum(1 for r in sites if r['has_fish'] == 'Ja')} sites"),
            ("Licensed, no fish in it", idle, IDLE, f"{n_idle} sites"),
            ("Applied for, awaiting a decision", pending, QUEUE,
             f"{sum(1 for r in apps if r['layer'] == 'pending')} applications")]

    W, L, R, T, RH = 1000, 300, 190, 214, 78
    H = T + len(bars) * RH + 196
    mx = max(v for _, v, _, _ in bars) * 1.04

    def sw(v):
        return v / mx * (W - L - R)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'The queue is not what limits Norwegian salmon</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Maximum allowed biomass in tonnes. More licensed capacity is sitting with no '
             f'fish in it than the entire pending queue</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'is asking for &#8212; by a factor of {idle/pending:.1f}.</text>')
    o.append(f'<text x="36" y="112" font-size="12" fill="{MUTED}">'
             f'This recipe previously said licensed biomass caps output, so the queue binds '
             f'growth. The first half is true and the second does not follow.</text>')

    for i, (label, v, col, sub) in enumerate(bars):
        y = T + i * RH
        o.append(f'<text x="{L-18}" y="{y+4}" font-size="13.5" fill="{INK}" '
                 f'text-anchor="end">{label}</text>')
        o.append(f'<text x="{L-18}" y="{y+21}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="end">{sub}</text>')
        o.append(f'<rect x="{L}" y="{y-15}" width="{max(sw(v), 2):.1f}" height="32" rx="3" '
                 f'fill="{col}" fill-opacity="0.85"/>')
        o.append(f'<text x="{L+sw(v)+12:.1f}" y="{y+6}" font-size="13.5" '
                 f'font-weight="600" fill="{INK}">{v/1e6:,.2f}m t</text>')

    yb = T + len(bars) * RH + 26
    o.append(f'<line x1="36" y1="{yb-20}" x2="{W-36}" y2="{yb-20}" stroke="{RULE}"/>')
    o.append(f'<text x="36" y="{yb+2}" font-size="13" fill="{INK}">'
             f'<tspan font-weight="600">{idle/1e6:,.2f} million tonnes of licensed capacity '
             f'has no fish in it, against {pending/1e3:,.0f} thousand tonnes waiting to be '
             f'licensed.</tspan></text>')
    o.append(f'<text x="36" y="{yb+26}" font-size="12.5" fill="{INK2}">'
             f'The queue is real, slow and getting slower &#8212; but licence availability is '
             f'not what caps production, because most of what is already licensed is not in '
             f'use.</text>')
    o.append(f'<text x="36" y="{yb+56}" font-size="11.5" fill="{MUTED}">'
             f'Idle does not mean available. Salmon sites are deliberately fallowed between '
             f'production cycles, so an unknown share of these {n_idle} sites is a working '
             f'farm between crops rather than dormant</text>')
    o.append(f'<text x="36" y="{yb+74}" font-size="11.5" fill="{MUTED}">'
             f'capacity. This chart rules out one explanation; it does not establish the '
             f'replacement.</text>')
    o.append(f'<text x="36" y="{yb+100}" font-size="11.5" fill="{MUTED}">'
             f'Counted only where the licence states tonnes. The field also carries STK, a '
             f'count of individual fish, and DA, an area &#8212; summing those as mass gave '
             f'87 million tonnes against a national output near 1.5 million.</text>')
    o.append(f'<text x="36" y="{yb+124}" font-size="11.5" fill="{MUTED}">'
             f'Sources: Fiskeridirektoratet Akvakultursøknader and Biomasse layers.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name}")
    print(f"    stocked {stocked:,.0f} t | idle {idle:,.0f} t | queued {pending:,.0f} t")
    print(f"    idle is {idle/pending:.1f}x the queue")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
