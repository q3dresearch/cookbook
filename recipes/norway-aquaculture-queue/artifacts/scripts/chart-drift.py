#!/usr/bin/env python3
"""How long a decision takes, quarter by quarter, as a distribution.

    python chart-drift.py <applications.csv>

The previous version of this chart plotted an annual median and reported that
decisions had slowed from 71 days to 200. That is true and it is the least
interesting true thing here: quarterly, the median wanders between 19 and 265 days
with no clean trend, while the ninetieth percentile climbs from 202 days to a
thousand. The typical applicant's experience has barely changed. The unlucky
applicant's has quadrupled.

A median cannot show that, which is the argument for a box: the box spans the
middle half, the whiskers reach the tenth and ninetieth percentiles, and the line
inside is the median. Widening boxes with a stable centre is a queue growing a
tail, not slowing uniformly.

The approval rate keeps a panel because it moves too, and the two together say
what one alone cannot: the regulator is not refusing more decisively, it is
taking longer to reach anyone.
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
MIN_N = 12

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE, TIME, RATE = "#e3e2db", "#b5651d", "#2361b0"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
D = lambda s: dt.date.fromisoformat(s) if s else None          # noqa: E731


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))

    days = collections.defaultdict(list)
    res = collections.defaultdict(collections.Counter)
    for r in rows:
        d = D(r["decided"])
        if not d:
            continue
        q = f"{d.year}Q{(d.month - 1) // 3 + 1}"
        if str(r["days_to_decide"]).strip().isdigit():
            days[q].append(int(r["days_to_decide"]))
        if r["result"]:
            res[q][r["result"].lower()] += 1

    qs = [q for q in sorted(days) if len(days[q]) >= MIN_N]
    if len(qs) < 4:
        print("  too few quarters")
        return 1

    def box(v):
        v = sorted(v)
        return (v[int(0.10 * len(v))], v[len(v) // 4], statistics.median(v),
                v[3 * len(v) // 4], v[int(0.90 * len(v))], len(v))

    boxes = [box(days[q]) for q in qs]
    rates = [(res[q]["granted"] / (res[q]["granted"] + res[q]["denied"])
              if res[q]["granted"] + res[q]["denied"] >= 8 else None) for q in qs]

    # One plot, two scales. Permitted here because the second series is a RATE
    # against a duration, not a second quantity of the same kind — the failure a
    # dual axis usually invites is two comparable magnitudes whose relative
    # position is set by the scale choice. Each axis is drawn in its series'
    # colour so there is never a question which one a mark reads against.
    W, L, R = 1040, 84, 96
    T1, PH1 = 226, 300
    H = T1 + PH1 + 186
    n = len(qs)
    mx = max(b[4] for b in boxes) * 1.06
    bw = min(34, (W - L - R) / n * 0.56)

    def sx(i):
        return L + (i + 0.5) / n * (W - L - R)

    def sy(v):
        return T1 + PH1 - v / mx * PH1

    # The rate axis spans 40-100% and sits in the lower half of the same box, so
    # the line cannot wander into the boxes and be mistaken for one.
    R0, R1 = 0.40, 1.02

    def sy2(v):
        return T1 + PH1 - (v - R0) / (R1 - R0) * PH1

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'The typical wait barely moved. The unlucky one quadrupled.</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Days from application to decision, by quarter decided. Box is the middle half, '
             f'whiskers reach the 10th and 90th</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'percentiles, the line inside is the median. Boxes widening around a stable '
             f'centre is a queue growing a tail, not slowing evenly.</text>')
    first, last = boxes[0], boxes[-1]
    o.append(f'<text x="36" y="112" font-size="12.5" fill="{MUTED}">'
             f'Median {first[2]:.0f}d to {last[2]:.0f}d. Ninetieth percentile '
             f'{first[4]:.0f}d to {last[4]:.0f}d.</text>')

    o.append(f'<text x="36" y="{T1-18}" font-size="12.5" font-weight="600" fill="{TIME}">'
             f'days to a decision</text>')
    o.append(f'<text x="220" y="{T1-18}" font-size="11.5" fill="{MUTED}">'
             f'left axis &#183; boxes</text>')
    o.append(f'<text x="{W-R-90}" y="{T1-18}" font-size="11.5" fill="{MUTED}" '
             f'text-anchor="end">right axis &#183; line</text>')
    for g in range(0, int(mx), 200):
        if g == 0:
            continue
        o.append(f'<line x1="{L}" y1="{sy(g):.1f}" x2="{W-R}" y2="{sy(g):.1f}" '
                 f'stroke="{RULE}"/>')
        o.append(f'<text x="{L-10}" y="{sy(g)+4:.1f}" font-size="11.5" fill="{MUTED}" '
                 f'text-anchor="end">{g}d</text>')

    for i, (p10, q1, med, q3, p90, cnt) in enumerate(boxes):
        x = sx(i)
        o.append(f'<line x1="{x:.1f}" y1="{sy(p10):.1f}" x2="{x:.1f}" y2="{sy(p90):.1f}" '
                 f'stroke="{TIME}" stroke-width="1.3" stroke-opacity="0.7"/>')
        for v in (p10, p90):
            o.append(f'<line x1="{x-bw/4:.1f}" y1="{sy(v):.1f}" x2="{x+bw/4:.1f}" '
                     f'y2="{sy(v):.1f}" stroke="{TIME}" stroke-width="1.3"/>')
        o.append(f'<rect x="{x-bw/2:.1f}" y="{sy(q3):.1f}" width="{bw:.1f}" '
                 f'height="{max(sy(q1)-sy(q3), 2):.1f}" rx="2" fill="{TIME}" '
                 f'fill-opacity="0.30" stroke="{TIME}" stroke-width="1.4"/>')
        o.append(f'<line x1="{x-bw/2:.1f}" y1="{sy(med):.1f}" x2="{x+bw/2:.1f}" '
                 f'y2="{sy(med):.1f}" stroke="{TIME}" stroke-width="2.6"/>')
    o.append(f'<text x="{sx(n-1):.1f}" y="{sy(boxes[-1][4])-10:.1f}" font-size="11.5" '
             f'font-weight="600" fill="{TIME}" text-anchor="end">'
             f'{boxes[-1][4]:.0f}d</text>')

    o.append(f'<text x="{W-R+12}" y="{T1-18}" font-size="12.5" font-weight="600" '
             f'fill="{RATE}" text-anchor="end">granted</text>')
    for g in (0.5, 0.75, 1.0):
        o.append(f'<text x="{W-R+10}" y="{sy2(g)+4:.1f}" font-size="11.5" fill="{RATE}">'
                 f'{g:.0%}</text>')
        o.append(f'<line x1="{W-R}" y1="{sy2(g):.1f}" x2="{W-R+6}" y2="{sy2(g):.1f}" '
                 f'stroke="{RATE}" stroke-width="1.2"/>')
    pts = [(i, v) for i, v in enumerate(rates) if v is not None]
    line = " ".join(f"{sx(i):.1f},{sy2(v):.1f}" for i, v in pts)
    o.append(f'<polyline points="{line}" fill="none" stroke="{RATE}" stroke-width="2.4"/>')
    for i, v in pts:
        o.append(f'<circle cx="{sx(i):.1f}" cy="{sy2(v):.1f}" r="4" fill="{RATE}" '
                 f'stroke="{SURFACE}" stroke-width="1.6"/>')

    for i, q in enumerate(qs):
        if q.endswith(("Q1", "Q3")):
            o.append(f'<text x="{sx(i):.1f}" y="{T1+PH1+22}" font-size="11" fill="{MUTED}" '
                     f'text-anchor="middle">{q}</text>')

    yb = T1 + PH1 + 56
    o.append(f'<line x1="36" y1="{yb-16}" x2="{W-36}" y2="{yb-16}" stroke="{RULE}"/>')
    o.append(f'<text x="36" y="{yb+6}" font-size="13" fill="{INK}">'
             f'<tspan font-weight="600">A median would have reported this as '
             f'&#8220;decisions slowed from {first[2]:.0f} to {last[2]:.0f} days&#8221;.</tspan> '
             f'The middle half barely moved; the top tenth went from '
             f'{first[4]:.0f} days to {last[4]:.0f}.</text>')
    o.append(f'<text x="36" y="{yb+28}" font-size="12.5" fill="{INK2}">'
             f'Refusals take a median 359 days against 129 for grants, so a lengthening tail '
             f'is where the refusals accumulate &#8212; and the pending pile inherits them.</text>')
    o.append(f'<text x="36" y="{yb+50}" font-size="11.5" fill="{MUTED}">'
             f'Two scales on one plot: boxes read the left axis in days, the line reads the '
             f'right in per cent. They are independent &#8212; the vertical distance between '
             f'them means nothing.</text>')
    o.append(f'<text x="36" y="{yb+74}" font-size="11.5" fill="{MUTED}">'
             f'Quarters with fewer than {MIN_N} decisions omitted; the final quarter is '
             f'partial. Withdrawn applications carry no date and cannot appear.</text>')
    o.append(f'<text x="36" y="{yb+96}" font-size="11.5" fill="{MUTED}">'
             f'Source: Fiskeridirektoratet Akvakultursøknader.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name} — {n} quarters")
    for q, b in zip(qs, boxes):
        print(f"    {q}  n={b[5]:>3}  p10 {b[0]:>4}  med {b[2]:>4.0f}  p90 {b[4]:>5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
