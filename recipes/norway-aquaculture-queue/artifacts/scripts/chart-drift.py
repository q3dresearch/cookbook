#!/usr/bin/env python3
"""Whether the regulator is getting stricter, slower, or both.

    python chart-drift.py <applications.csv>

Every rate elsewhere in this recipe is pooled across three and a half years. If
the regulator's behaviour is changing, a pooled figure describes nobody: it is an
average over a moving target, and an applicant today faces the latest value rather
than the mean.

Two panels on a shared year axis rather than two scales on one, because a share
and a duration have no common unit and putting them together would let the scale
choice decide how the trend reads.

Both move the same way. Approval falls from 94% to 83% while the median decision
stretches from 71 days to 200 — stricter and slower at once, which is what a
queue under load looks like rather than a policy change in either direction alone.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import statistics
import sys
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "drift.svg"
MIN_N = 20

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE, RATE, TIME = "#e3e2db", "#2361b0", "#b5651d"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
D = lambda s: dt.date.fromisoformat(s) if s else None          # noqa: E731


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))

    res = collections.defaultdict(collections.Counter)
    days = collections.defaultdict(list)
    for r in rows:
        d = D(r["decided"])
        if not d or not r["result"]:
            continue
        res[d.year][r["result"].lower()] += 1
        if str(r["days_to_decide"]).strip().isdigit():
            days[d.year].append(int(r["days_to_decide"]))

    years = [y for y in sorted(res)
             if res[y]["granted"] + res[y]["denied"] >= MIN_N and len(days[y]) >= MIN_N]
    if len(years) < 3:
        print("  too few complete years")
        return 1
    rate = [res[y]["granted"] / (res[y]["granted"] + res[y]["denied"]) for y in years]
    med = [statistics.median(days[y]) for y in years]
    this = dt.date.today().year

    W, L, R = 940, 92, 112
    T1, PH1 = 190, 156
    T2, PH2 = T1 + PH1 + 92, 156
    H = T2 + PH2 + 150
    n = len(years)
    # The rate axis does not start at zero. It never goes below 80%, and a 0-100
    # axis spent four fifths of the panel on empty space while flattening the very
    # change the chart is about. The floor is stated on the axis.
    r0 = min(rate) - 0.10
    r1 = max(rate) * 1.03
    m1 = max(med) * 1.16

    def sx(i):
        return L + (i + 0.5) / n * (W - L - R)

    def sy1(v):
        return T1 + PH1 - (v - r0) / (r1 - r0) * PH1

    def sy2(v):
        return T2 + PH2 - v / m1 * PH2

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'Stricter and slower at the same time</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Every other rate in this recipe is pooled across all years. These are the '
             f'years separately, and they are not the same:</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'an applicant today faces {rate[-1]:.0%}, not the pooled '
             f'{sum(res[y]["granted"] for y in years)/sum(res[y]["granted"]+res[y]["denied"] for y in years):.0%}.</text>')

    for panel, (vals, col, lab, sy, top, fmt) in enumerate((
            (rate, RATE, "share of decisions granted", sy1, r1, lambda v: f"{v:.0%}"),
            (med, TIME, "median days to a decision", sy2, m1, lambda v: f"{v:.0f}d"))):
        base = T1 if panel == 0 else T2
        ph = PH1 if panel == 0 else PH2
        o.append(f'<text x="36" y="{base-16}" font-size="12.5" font-weight="600" '
                 f'fill="{col}">{lab}</text>')
        step = 0.05 if panel == 0 else 50
        g = (round(r0 / step) + 1) * step if panel == 0 else step
        while g < (r1 if panel == 0 else top):
            yy = sy(g)
            o.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{W-R}" y2="{yy:.1f}" stroke="{RULE}"/>')
            o.append(f'<text x="{L-10}" y="{yy+4:.1f}" font-size="11.5" fill="{MUTED}" '
                     f'text-anchor="end">{fmt(g)}</text>')
            g += step
        pts = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(vals))
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="3"/>')
        for i, v in enumerate(vals):
            o.append(f'<circle cx="{sx(i):.1f}" cy="{sy(v):.1f}" r="5.5" fill="{col}" '
                     f'stroke="{SURFACE}" stroke-width="2"/>')
            o.append(f'<text x="{sx(i):.1f}" y="{sy(v)-13:.1f}" font-size="12.5" '
                     f'font-weight="600" fill="{INK}" text-anchor="middle">{fmt(v)}</text>')
        if panel == 1:
            for i, y in enumerate(years):
                lbl = f"{y} (partial)" if y >= this else str(y)
                o.append(f'<text x="{sx(i):.1f}" y="{base+ph+24:.1f}" font-size="12" '
                         f'fill="{MUTED if y >= this else INK2}" text-anchor="middle">'
                         f'{lbl}</text>')
                o.append(f'<text x="{sx(i):.1f}" y="{base+ph+40:.1f}" font-size="10.5" '
                         f'fill="{MUTED}" text-anchor="middle">'
                         f'n={res[y]["granted"]+res[y]["denied"]}</text>')

    yb = H - 74
    o.append(f'<line x1="36" y1="{yb-16}" x2="{W-36}" y2="{yb-16}" stroke="{RULE}"/>')
    o.append(f'<text x="36" y="{yb+4}" font-size="13" fill="{INK}">'
             f'<tspan font-weight="600">Approval falls {rate[0]:.0%} to {rate[-1]:.0%} while '
             f'the median decision stretches {med[0]:.0f} to {med[-1]:.0f} days.</tspan> '
             f'Both worsen together.</text>')
    o.append(f'<text x="36" y="{yb+26}" font-size="12.5" fill="{INK2}">'
             f'That is the signature of a queue under load rather than a decision to refuse '
             f'more: the regulator is not saying no faster, it is saying anything slower.</text>')
    o.append(f'<text x="36" y="{H-14}" font-size="11.5" fill="{MUTED}">'
             f'Years with fewer than {MIN_N} decisions omitted; the current year is partial and '
             f'holds only what has been decided so far. Withdrawn applications carry no date '
             f'and are excluded here.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name}")
    for i, y in enumerate(years):
        print(f"    {y}  {rate[i]:>5.0%} granted  {med[i]:>4.0f}d median  "
              f"n={res[y]['granted']+res[y]['denied']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
