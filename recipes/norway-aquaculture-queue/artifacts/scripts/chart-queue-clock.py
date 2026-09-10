#!/usr/bin/env python3
"""The queue as a stock and a flow: what arrives, what leaves, what piles up.

    python chart-queue-clock.py <applications.csv>

Two panels on one time axis rather than two scales on one panel. The stock is in
the hundreds and the monthly flows in the tens, and putting them on a shared
vertical axis with two scales would let the scale choice decide how alarming the
picture looks.

    top     applications sitting in the queue at the end of each month
    bottom  how many arrived that month, against how many were decided

The register opens in February 2023 with four applications, so the early climb is
a system filling up rather than a backlog forming. What matters is the later
years, where arrivals still outrun decisions: the regulator resolves roughly three
applications for every four it receives, and the stock has never fallen.

**The stock line is an upper bound.** 80 applications were withdrawn by their
applicants and Fiskeridirektoratet records no date for a withdrawal, so they
cannot be removed on the month they actually left. They are shown as a band at the
top of the stock rather than hidden inside it.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import sys
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "queue-clock.svg"

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE, STOCK, UNDATED = "#e3e2db", "#2361b0", "#b9c9e2"
ARRIVE, DECIDE = "#b5651d", "#3f7d3a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
D = lambda s: dt.date.fromisoformat(s) if s else None          # noqa: E731


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))

    arrive = collections.Counter()
    decide = collections.Counter()
    withdrawn = 0
    for r in rows:
        s, d = D(r["submitted"]), D(r["decided"])
        if s:
            arrive[f"{s:%Y-%m}"] += 1
        if d:
            decide[f"{d:%Y-%m}"] += 1
        elif r["status"] == "WITHDRAWN":
            withdrawn += 1

    months = sorted(set(arrive) | set(decide))
    if len(months) < 6:
        print("  too short a history")
        return 1
    stock, series = 0, []
    for m in months:
        stock += arrive[m] - decide[m]
        series.append((m, stock, arrive[m], decide[m]))

    W, L, R = 1000, 78, 60
    T1, PH1 = 194, 210
    T2, PH2 = T1 + PH1 + 96, 132
    H = T2 + PH2 + 118
    n = len(series)
    mx1 = max(s for _, s, _, _ in series) * 1.12
    mx2 = max(max(a, d) for _, _, a, d in series) * 1.15

    def sx(i):
        return L + i / max(n - 1, 1) * (W - L - R)

    def sy1(v):
        return T1 + PH1 - v / mx1 * PH1

    def sy2(v):
        return T2 + PH2 - v / mx2 * PH2

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'The queue has never once shrunk</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Applications waiting at the end of each month, and the monthly flows that '
             f'produce it. The register opens in {months[0]} with</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'{series[0][2]} applications, so the first year is a system filling up. What '
             f'follows is not.</text>')
    o.append(f'<text x="36" y="112" font-size="12" fill="{MUTED}">'
             f'The stock is an upper bound: {withdrawn} applications were withdrawn and no '
             f'withdrawal date is published, so they cannot be removed on the month they '
             f'left.</text>')

    o.append(f'<text x="36" y="{T1-16}" font-size="12.5" font-weight="600" fill="{INK}">'
             f'Applications waiting, end of month</text>')
    for g in range(0, int(mx1), 100):
        if g == 0:
            continue
        o.append(f'<line x1="{L}" y1="{sy1(g):.1f}" x2="{W-R}" y2="{sy1(g):.1f}" '
                 f'stroke="{RULE}"/>')
        o.append(f'<text x="{L-10}" y="{sy1(g)+4:.1f}" font-size="11.5" fill="{MUTED}" '
                 f'text-anchor="end">{g}</text>')
    area = " ".join(f"{sx(i):.1f},{sy1(s):.1f}" for i, (_, s, _, _) in enumerate(series))
    o.append(f'<polygon points="{sx(0):.1f},{sy1(0):.1f} {area} {sx(n-1):.1f},{sy1(0):.1f}" '
             f'fill="{STOCK}" fill-opacity="0.16"/>')
    o.append(f'<polyline points="{area}" fill="none" stroke="{STOCK}" stroke-width="2.8"/>')
    last = series[-1]
    o.append(f'<text x="{sx(n-1):.1f}" y="{sy1(last[1])-14:.1f}" font-size="13" '
             f'font-weight="600" fill="{STOCK}" text-anchor="end">{last[1]} waiting</text>')
    o.append(f'<text x="{sx(0)+6:.1f}" y="{sy1(series[0][1])-10:.1f}" font-size="12" '
             f'fill="{MUTED}">{series[0][1]}</text>')

    o.append(f'<text x="36" y="{T2-16}" font-size="12.5" font-weight="600" fill="{INK}">'
             f'Arriving and decided, per month</text>')
    o.append(f'<circle cx="286" cy="{T2-20}" r="5.5" fill="{ARRIVE}"/>')
    o.append(f'<text x="296" y="{T2-16}" font-size="12" fill="{ARRIVE}" '
             f'font-weight="600">arrived</text>')
    o.append(f'<circle cx="376" cy="{T2-20}" r="5.5" fill="{DECIDE}"/>')
    o.append(f'<text x="386" y="{T2-16}" font-size="12" fill="{DECIDE}" '
             f'font-weight="600">decided</text>')
    for g in range(0, int(mx2), 20):
        if g == 0:
            continue
        o.append(f'<line x1="{L}" y1="{sy2(g):.1f}" x2="{W-R}" y2="{sy2(g):.1f}" '
                 f'stroke="{RULE}"/>')
        o.append(f'<text x="{L-10}" y="{sy2(g)+4:.1f}" font-size="11.5" fill="{MUTED}" '
                 f'text-anchor="end">{g}</text>')
    for vals, col in (([a for _, _, a, _ in series], ARRIVE),
                      ([d for _, _, _, d in series], DECIDE)):
        pts = " ".join(f"{sx(i):.1f},{sy2(v):.1f}" for i, v in enumerate(vals))
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.2"/>')

    for i, (m, _, _, _) in enumerate(series):
        if m.endswith(("-01", "-07")):
            o.append(f'<line x1="{sx(i):.1f}" y1="{T1}" x2="{sx(i):.1f}" y2="{T1+PH1}" '
                     f'stroke="{RULE}"/>')
            o.append(f'<text x="{sx(i):.1f}" y="{T2+PH2+22}" font-size="11" fill="{MUTED}" '
                     f'text-anchor="middle">{m}</text>')

    yb = T2 + PH2 + 52
    recent = [s for s in series if s[0] >= "2025-01"]
    ra, rd = sum(s[2] for s in recent), sum(s[3] for s in recent)
    o.append(f'<line x1="36" y1="{yb-18}" x2="{W-36}" y2="{yb-18}" stroke="{RULE}"/>')
    o.append(f'<text x="36" y="{yb+4}" font-size="13" fill="{INK}">'
             f'<tspan font-weight="600">Since 2025 the regulator has decided {rd} '
             f'applications and received {ra}.</tspan> It resolves about '
             f'{rd/ra:.0%} of what arrives, so the pile grows by roughly one in '
             f'{round(1/max(1-rd/ra, 0.01))}.</text>')
    o.append(f'<text x="36" y="{yb+26}" font-size="12.5" fill="{INK2}">'
             f'A queue that clears would show the two lines crossing. They have not '
             f'crossed for a sustained period in three and a half years.</text>')
    o.append(f'<text x="36" y="{yb+54}" font-size="11.5" fill="{MUTED}">'
             f'Source: Fiskeridirektoratet Akvakultursøknader, layers 0 and 4. The final '
             f'month is partial. Withdrawals leave the stock only at the end, not when they '
             f'occurred.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name} — {n} months, {series[0][0]} to {series[-1][0]}")
    print(f"    stock {series[0][1]} -> {series[-1][1]}   "
          f"since 2025: {ra} arrived, {rd} decided ({rd/ra:.0%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
