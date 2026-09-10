#!/usr/bin/env python3
"""Which applications sit on the table forever, and where.

    python chart-where-it-stalls.py <applications.csv>

The national median hides two different failures. Plotting the typical wait
against the unlucky one, by production area, separates them:

  * UNIFORMLY SLOW — Vestfjorden og Vesterålen decides in a median 754 days and
    a 90th-percentile 1,049. Nearly every application is slow. Tail ratio 1.4.
  * A LOTTERY — Nordhordland til Stadt decides in a median 160 days but its 90th
    percentile is 917. Most applicants are fine; one in ten waits two and a half
    years. Tail ratio 5.7.

Same application type throughout (change of, or new, sea site for salmon and
trout), so this is not a mix of easy and hard paperwork.

WHY THIS CHART USES PRODUCTION AREAS, NOT COUNTIES. The obvious version of this
finding is "Nordland is slow" — it holds up against every control: within a
single application type Nordland's median is 368 days against Vestland's 161, and
it survives splitting by outcome (granted 316 vs 229, denied 789 vs 353), by
applicant (24 slow decisions across 14 companies) and by submission year. It is
still a merge. Nordland contains BOTH extremes: Vestfjorden og Vesterålen at 754
days and Helgeland til Bodø at 212, a 3.6x spread inside one county and one
application type. The county average is a number describing nowhere.

What the register cannot say is WHY. Vestfjorden og Vesterålen is production area
8, which the traffic-light system has repeatedly coloured red, and a red area
restricts growth — but that is an outside fact, not something in this data, and
this recipe has not tested it.
"""
from __future__ import annotations

import collections
import csv
import statistics
import sys
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "where-it-stalls.svg"

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE, GRID, LINK = "#e3e2db", "#efeee8", "#c9c6bc"
# Sequential, one hue light to dark: share of the area's applications still pending.
RAMP = ["#f6dfc6", "#eab97e", "#d99244", "#b5651d", "#7d4413"]
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'

SEA = {"Endring av lokalitet for laks, ørret og regnbueørret i sjø.",
       "Ny lokalitet for laks, ørret og regnbueørret i sjø."}
MIN_N = 10
X0, X1 = 100.0, 820.0
Y0, Y1 = 300.0, 1120.0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))

    days = collections.defaultdict(list)
    pend = collections.Counter()
    county = collections.defaultdict(collections.Counter)
    blank_p = blank_d = 0
    for r in rows:
        if r["application_type"] not in SEA:
            continue
        pa = r["production_area"] or ""
        if not pa:
            blank_p += r["layer"] == "pending"
            blank_d += r["layer"] == "decided"
            continue
        county[pa][r["county"] or "?"] += 1
        if r["layer"] == "decided" and r["days_to_decide"]:
            days[pa].append(int(r["days_to_decide"]))
        elif r["layer"] == "pending":
            pend[pa] += 1

    pts = []
    for pa, v in days.items():
        if len(v) < MIN_N:
            continue
        v = sorted(v)
        med, p90 = statistics.median(v), v[int(0.9 * len(v))]
        share = pend[pa] / (len(v) + pend[pa])
        pts.append({"pa": pa, "n": len(v), "med": med, "p90": p90, "share": share,
                    "county": county[pa].most_common(1)[0][0]})
    if len(pts) < 6:
        print("  too few production areas above the minimum")
        return 1
    nmax = max(p["n"] for p in pts)

    W, L, R, T, PH = 1040, 84, 250, 206, 430
    H = T + PH + 208

    def sx(v):
        return L + (v - X0) / (X1 - X0) * (W - L - R)

    def sy(v):
        return T + PH - (v - Y0) / (Y1 - Y0) * PH

    def sr(n):
        return 6.0 + (n / nmax) ** 0.5 * 14.0

    def col(share):
        return RAMP[min(int(share / 0.12), len(RAMP) - 1)]

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'Two different ways to wait, and the county average describes neither'
             f'</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Sea-site applications by production area. Across is the typical wait, up is '
             f'the unlucky one. Far right means slow for everyone;</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'high but left means a lottery &#8212; most applicants fine, one in ten '
             f'stranded. Grey lines join areas in the same county.</text>')
    o.append(f'<text x="36" y="112" font-size="12" fill="{MUTED}">'
             f'Nordland holds both extremes: 754 days in Vestfjorden og Vester&#229;len, 212 '
             f'in Helgeland til Bod&#248;. One application type throughout.</text>')

    for v in range(400, int(Y1) + 1, 200):
        y = sy(v)
        o.append(f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" stroke="{GRID}"/>')
        o.append(f'<text x="{L-12}" y="{y+4:.1f}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="end">{v:,}d</text>')
    for v in range(200, int(X1) + 1, 200):
        o.append(f'<text x="{sx(v):.1f}" y="{T+PH+24:.0f}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="middle">{v:,}d</text>')
    o.append(f'<text x="{L-12}" y="{T-14}" font-size="11.5" font-weight="600" '
             f'fill="{INK2}" text-anchor="end">unlucky</text>')
    o.append(f'<text x="{L-12}" y="{T+2}" font-size="11.5" fill="{MUTED}" '
             f'text-anchor="end">90th pct</text>')
    axc = (L + W - R) / 2
    o.append(f'<text x="{axc-6:.0f}" y="{T+PH+48:.0f}" font-size="11.5" '
             f'font-weight="600" fill="{INK2}" text-anchor="end">typical</text>')
    o.append(f'<text x="{axc:.0f}" y="{T+PH+48:.0f}" font-size="11.5" fill="{MUTED}" '
             f'text-anchor="start">&#183; median days to a decision</text>')

    # p90 can never fall below the median; the diagonal is the floor, and distance
    # above it is exactly how uneven the queue is.
    o.append(f'<line x1="{sx(max(X0, Y0)):.1f}" y1="{sy(max(X0, Y0)):.1f}" '
             f'x2="{sx(min(X1, Y1)):.1f}" y2="{sy(min(X1, Y1)):.1f}" '
             f'stroke="{LINK}" stroke-width="1" stroke-dasharray="4 4"/>')
    o.append(f'<text x="{sx(790):.1f}" y="{sy(790)+18:.1f}" font-size="10.5" '
             f'fill="{MUTED}" text-anchor="end">p90 = median &#183; no tail at all</text>')

    county_labels: list[tuple[float, float, str]] = []
    by_c = collections.defaultdict(list)
    for p in pts:
        by_c[p["county"]].append(p)
    for c, g in by_c.items():
        if len(g) < 2:
            continue
        g = sorted(g, key=lambda p: p["med"])
        o.append('<polyline points="' +
                 " ".join(f'{sx(p["med"]):.1f},{sy(p["p90"]):.1f}' for p in g) +
                 f'" fill="none" stroke="{LINK}" stroke-width="1.6"/>')
        a, b = g[0], g[-1]
        mx = (sx(a["med"]) + sx(b["med"])) / 2
        my = (sy(a["p90"]) + sy(b["p90"])) / 2 - 10
        county_labels.append((mx, my, c))

    for p in sorted(pts, key=lambda p: -p["n"]):
        c = col(p["share"])
        o.append(f'<circle cx="{sx(p["med"]):.1f}" cy="{sy(p["p90"]):.1f}" '
                 f'r="{sr(p["n"]):.1f}" fill="{c}" stroke="{INK2}" stroke-width="1" '
                 f'stroke-opacity="0.45"/>')

    for mx, my, c in county_labels:
        o.append(f'<text x="{mx:.1f}" y="{my:.1f}" font-size="10.5" fill="{MUTED}" '
                 f'text-anchor="middle" font-style="italic">{c}</text>')

    # Label placement. The middle of this chart is crowded, so try each side and
    # then a vertical nudge, keeping a list of boxes already taken. Eyeballing the
    # render was how the previous version's overlaps were found.
    taken = [(mx - len(c) * 3.6 - 6, my - 10, mx + len(c) * 3.6 + 6, my + 5)
             for mx, my, c in county_labels]

    marks = [(sx(q["med"]), sy(q["p90"]), sr(q["n"])) for q in pts]

    def hits_mark(box):
        x0, y0, x1, y1 = box
        return any(x0 < cx + rr and cx - rr < x1 and y0 < cy + rr and cy - rr < y1
                   for cx, cy, rr in marks)

    def free(box):
        ax0, ay0, ax1, ay1 = box
        return not any(ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1
                       for bx0, by0, bx1, by1 in taken)

    for p in sorted(pts, key=lambda p: -p["n"]):
        x, y, r = sx(p["med"]), sy(p["p90"]), sr(p["n"])
        w = len(p["pa"]) * 6.4 + 10
        placed = False
        for dy in (0, -16, 16, -32, 32, -48, 48):
            for anc in ("start", "end"):
                lx0 = x + r + 7 if anc == "start" else x - r - 7 - w
                box = (lx0, y + dy - 8, lx0 + w, y + dy + 6)
                if (box[0] < L - 40 or box[2] > W - R - 4
                        or not free(box) or hits_mark(box)):
                    continue
                taken.append(box)
                o.append(f'<text x="{x + (r+7 if anc == "start" else -r-7):.1f}" '
                         f'y="{y+dy+4:.1f}" font-size="11" fill="{INK2}" '
                         f'text-anchor="{anc}">{p["pa"]}</text>')
                placed = True
                break
            if placed:
                break
        if not placed:
            o.append(f'<text x="{x:.1f}" y="{y-r-8:.1f}" font-size="11" fill="{INK2}" '
                     f'text-anchor="middle">{p["pa"]}</text>')

    lx, ly = W - R + 26, T + 6
    o.append(f'<text x="{lx}" y="{ly}" font-size="11.5" font-weight="600" fill="{INK2}">'
             f'Still pending</text>')
    o.append(f'<text x="{lx}" y="{ly+16}" font-size="10.5" fill="{MUTED}">'
             f'share of the area&#8217;s</text>')
    o.append(f'<text x="{lx}" y="{ly+30}" font-size="10.5" fill="{MUTED}">'
             f'applications undecided</text>')
    for i, c in enumerate(RAMP):
        o.append(f'<rect x="{lx+i*24}" y="{ly+44}" width="22" height="14" fill="{c}"/>')
    o.append(f'<text x="{lx}" y="{ly+74}" font-size="10.5" fill="{MUTED}">10%</text>')
    o.append(f'<text x="{lx+5*24-2}" y="{ly+74}" font-size="10.5" fill="{MUTED}" '
             f'text-anchor="end">60%</text>')
    o.append(f'<text x="{lx}" y="{ly+112}" font-size="11.5" font-weight="600" '
             f'fill="{INK2}">Area = decisions</text>')
    for i, n in enumerate((10, 30)):
        cy = ly + 146 + i * 46
        o.append(f'<circle cx="{lx+22}" cy="{cy}" r="{sr(n):.1f}" fill="none" '
                 f'stroke="{MUTED}" stroke-width="1.2"/>')
        o.append(f'<text x="{lx+52}" y="{cy+4}" font-size="10.5" fill="{MUTED}">{n}</text>')

    yb = T + PH + 76
    o.append(f'<line x1="36" y1="{yb-22}" x2="{W-36}" y2="{yb-22}" stroke="{RULE}"/>')
    o.append(f'<text x="36" y="{yb}" font-size="13" fill="{INK}">'
             f'<tspan font-weight="600">Where you apply changes the wait more than what you '
             f'apply for</tspan> &#8212; and the county is the wrong unit to ask it in.</text>')
    o.append(f'<text x="36" y="{yb+22}" font-size="13" fill="{INK}">'
             f'Nordland&#8217;s two production areas sit at opposite ends of this chart, 3.6x '
             f'apart, inside one county and one application type.</text>')
    o.append(f'<text x="36" y="{yb+48}" font-size="11.5" fill="{MUTED}">'
             f'Read with drift.svg, which shows the same thing in time: the national median '
             f'barely moved while the 90th percentile went 202 to 1,000 days. This chart says '
             f'where that tail lives.</text>')
    o.append(f'<text x="36" y="{yb+70}" font-size="11.5" fill="{MUTED}">'
             f'The register does not say why. Vestfjorden og Vester&#229;len is production '
             f'area 8, repeatedly red under the traffic-light system, but that is an outside '
             f'fact this recipe has not tested.</text>')
    o.append(f'<text x="36" y="{yb+92}" font-size="11.5" fill="{MUTED}">'
             f'{blank_p} pending and {blank_d} decided sea-site applications carry no '
             f'production area and cannot appear here &#8212; the largest single pending '
             f'group in the register.</text>')
    o.append(f'<text x="36" y="{yb+114}" font-size="11.5" fill="{MUTED}">'
             f'Areas under {MIN_N} decisions are omitted. Source: Fiskeridirektoratet '
             f'Akvakults&#248;knader, layers 0 and 4.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name} — {len(pts)} production areas")
    for p in sorted(pts, key=lambda p: -p["med"]):
        print(f"    {p['pa'][:30]:30s} n={p['n']:3d} med {p['med']:4.0f}d "
              f"p90 {p['p90']:4.0f}d  tail x{p['p90']/p['med']:.1f}  "
              f"pending {p['share']:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
