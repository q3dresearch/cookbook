#!/usr/bin/env python3
"""Which applications sit on the table forever, and where.

    python chart-where-it-stalls.py <applications.csv>

One application type throughout (change of, or new, sea site for salmon and
trout), so this is not a mix of easy and hard paperwork. Across: the typical
wait. Up: the unlucky one. Both axes carry the same scale, so the dashed 45
degree line is where a queue with no tail would sit and the crosshair at the
all-area median cuts four quadrants:

    fast, a lottery   |  slow for everyone     <- Vestfjorden og Vesteralen
    ------------------+-------------------        754d median, 1049d p90
    fast, predictable |  slow, predictable
        ^ Nordhordland til Stadt, 160d median but 917d p90

Colour is the county. Nordland appears at BOTH ends of the chart — Vestfjorden
og Vesteralen at 754 days and Helgeland til Bodo at 212 — which is the point:
"Nordland is slow" survives controls for application type, outcome, applicant
and submission year, and is still a merge of two places 3.6x apart.

Marks are NOT joined. An earlier version drew a line between areas in the same
county; a connector asserts a sequence between two independent measurements and
there is none. Shared colour carries the same information without the claim.
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
RULE, GRID = "#e3e2db", "#eceae3"
# Worst pair separates at OKLab dE 12.7 under deuteranope/protanope simulation,
# 17.4 at normal vision. Seven counties could not be made to pass; the three with
# a single production area share a neutral, since a spread needs two points.
OTHER = "one area only"
COUNTY = {"Nordland": "#b5651d", "Troms": "#1d7f88", "Trøndelag": "#f0b44a",
          "Vestland": "#0d3b66", OTHER: "#9aa0a6"}
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'

SEA = {"Endring av lokalitet for laks, ørret og regnbueørret i sjø.",
       "Ny lokalitet for laks, ørret og regnbueørret i sjø."}
MIN_N = 10
# Equal SPANS, not equal ranges. Both axes cover 800 days, so the diagonal is a
# true 45 degrees, but the window is cropped to where the data actually is —
# no median exceeds 760d and no 90th percentile falls below 370d.
X0, X1 = 100.0, 900.0
Y0, Y1 = 300.0, 1100.0
XT = (200, 400, 600, 800)
YT = (400, 600, 800, 1000)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))

    days = collections.defaultdict(list)
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

    pts = []
    for pa, v in days.items():
        if len(v) < MIN_N:
            continue
        v = sorted(v)
        pts.append({"pa": pa, "n": len(v), "med": statistics.median(v),
                    "p90": v[int(0.9 * len(v))],
                    "county": county[pa].most_common(1)[0][0]})
    if len(pts) < 6:
        print("  too few production areas above the minimum")
        return 1

    seen = collections.Counter(p["county"] for p in pts)
    for p in pts:
        p["key"] = p["county"] if seen[p["county"]] > 1 else OTHER
    nmax = max(p["n"] for p in pts)
    xm = statistics.median([p["med"] for p in pts])
    ym = statistics.median([p["p90"] for p in pts])

    W, L, T, S = 1040, 92, 188, 596
    H = T + S + 168

    def sx(v):
        return L + (v - X0) / (X1 - X0) * S

    def sy(v):
        return T + S - (v - Y0) / (Y1 - Y0) * S

    def sr(n):
        return 5.0 + (n / nmax) ** 0.5 * 13.0

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'Two different ways to wait for the same permit</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Sea-site applications by production area. Nordland holds both extremes, '
             f'which is why a county average describes neither place.</text>')

    for v in YT:
        o.append(f'<line x1="{L}" y1="{sy(v):.1f}" x2="{L+S}" y2="{sy(v):.1f}" '
                 f'stroke="{GRID}"/>')
        o.append(f'<text x="{L-11}" y="{sy(v)+4:.1f}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="end">{v:,}d</text>')
    for v in XT:
        o.append(f'<line x1="{sx(v):.1f}" y1="{T}" x2="{sx(v):.1f}" y2="{T+S}" '
                 f'stroke="{GRID}"/>')
        o.append(f'<text x="{sx(v):.1f}" y="{T+S+22:.0f}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="middle">{v:,}d</text>')
    o.append(f'<text x="{L-11}" y="{T-10}" font-size="12" font-weight="600" '
             f'fill="{INK2}" text-anchor="end">unlucky wait</text>')
    o.append(f'<text x="{L-11}" y="{T+6}" font-size="10.5" fill="{MUTED}" '
             f'text-anchor="end">90th percentile</text>')
    o.append(f'<text x="{L+S}" y="{T+S+44:.0f}" font-size="12" font-weight="600" '
             f'fill="{INK2}" text-anchor="end">typical wait &#183; median days</text>')

    # The quadrant. Dividers are the median across areas, not a chosen threshold.
    o.append(f'<line x1="{sx(xm):.1f}" y1="{T}" x2="{sx(xm):.1f}" y2="{T+S}" '
             f'stroke="{RULE}" stroke-width="1.2"/>')
    o.append(f'<line x1="{L}" y1="{sy(ym):.1f}" x2="{L+S}" y2="{sy(ym):.1f}" '
             f'stroke="{RULE}" stroke-width="1.2"/>')
    # p90 can never fall below the median, so nothing can sit below this line.
    d0, d1 = max(X0, Y0), min(X1, Y1)
    o.append(f'<line x1="{sx(d0):.1f}" y1="{sy(d0):.1f}" x2="{sx(d1):.1f}" '
             f'y2="{sy(d1):.1f}" stroke="{RULE}" stroke-width="1" '
             f'stroke-dasharray="5 5"/>')
    o.append(f'<text x="{sx(d1)-8:.1f}" y="{sy(d1)-9:.1f}" font-size="10.5" '
             f'fill="{MUTED}" text-anchor="end">p90 = median &#183; no tail</text>')
    for tx, ty, anc, txt in ((L + 8, T + 18, "start", "fast, but a lottery"),
                             (L + S - 8, T + 18, "end", "slow for everyone"),
                             (L + 8, T + S - 10, "start", "fast and predictable"),
                             (L + S - 8, T + S - 10, "end", "slow but predictable")):
        o.append(f'<text x="{tx:.0f}" y="{ty:.0f}" font-size="11.5" fill="{MUTED}" '
                 f'text-anchor="{anc}" font-style="italic">{txt}</text>')

    for p in sorted(pts, key=lambda p: -p["n"]):
        o.append(f'<circle cx="{sx(p["med"]):.1f}" cy="{sy(p["p90"]):.1f}" '
                 f'r="{sr(p["n"]):.1f}" fill="{COUNTY[p["key"]]}" fill-opacity="0.85" '
                 f'stroke="{SURFACE}" stroke-width="2"/>')

    # Labels: try each side, then nudge, avoiding marks and labels already placed.
    marks = [(sx(q["med"]), sy(q["p90"]), sr(q["n"])) for q in pts]
    taken: list[tuple[float, float, float, float]] = []

    def blocked(b):
        return (any(b[0] < t[2] and t[0] < b[2] and b[1] < t[3] and t[1] < b[3]
                    for t in taken)
                or any(b[0] < cx + r and cx - r < b[2] and b[1] < cy + r and cy - r < b[3]
                       for cx, cy, r in marks))

    for p in sorted(pts, key=lambda p: -p["n"]):
        x, y, r = sx(p["med"]), sy(p["p90"]), sr(p["n"])
        w = len(p["pa"]) * 6.4 + 10
        for dy in (0, -15, 15, -30, 30, -45, 45):
            for anc in ("start", "end"):
                x0 = x + r + 7 if anc == "start" else x - r - 7 - w
                b = (x0, y + dy - 8, x0 + w, y + dy + 6)
                if b[0] < 36 or b[2] > W - 30 or blocked(b):
                    continue
                taken.append(b)
                o.append(f'<text x="{x + (r+7 if anc == "start" else -r-7):.1f}" '
                         f'y="{y+dy+4:.1f}" font-size="11.5" fill="{INK2}" '
                         f'text-anchor="{anc}">{p["pa"]}</text>')
                break
            else:
                continue
            break

    lx, ly = L + S + 78, T + 30
    o.append(f'<text x="{lx}" y="{ly-18}" font-size="11.5" font-weight="600" '
             f'fill="{INK2}">County</text>')
    for i, (name, c) in enumerate(COUNTY.items()):
        if name != OTHER and not seen.get(name):
            continue
        o.append(f'<circle cx="{lx+8}" cy="{ly+i*24-4}" r="7" fill="{c}" '
                 f'fill-opacity="0.85"/>')
        o.append(f'<text x="{lx+24}" y="{ly+i*24}" font-size="12" fill="{INK2}">'
                 f'{name}</text>')
    sy0 = ly + len(COUNTY) * 24 + 26
    o.append(f'<text x="{lx}" y="{sy0}" font-size="11.5" font-weight="600" '
             f'fill="{INK2}">Decisions</text>')
    for i, n in enumerate((10, 30)):
        cy = sy0 + 30 + i * 40
        o.append(f'<circle cx="{lx+16}" cy="{cy}" r="{sr(n):.1f}" fill="none" '
                 f'stroke="{MUTED}" stroke-width="1.2"/>')
        o.append(f'<text x="{lx+44}" y="{cy+4}" font-size="11" fill="{MUTED}">{n}</text>')

    yb = T + S + 84
    o.append(f'<line x1="36" y1="{yb-24}" x2="{W-36}" y2="{yb-24}" stroke="{RULE}"/>')
    o.append(f'<text x="36" y="{yb}" font-size="13" fill="{INK}">'
             f'<tspan font-weight="600">Where you apply moves the wait more than what you '
             f'apply for.</tspan> Vestfjorden og Vester&#229;len is slow for everyone; '
             f'Nordhordland til Stadt</text>')
    o.append(f'<text x="36" y="{yb+21}" font-size="13" fill="{INK}">'
             f'is fast for most and catastrophic for a tenth. Those need opposite '
             f'responses, and one national median hides both.</text>')
    o.append(f'<text x="36" y="{yb+46}" font-size="11.5" fill="{MUTED}">'
             f'Dividers are the median across areas, not a chosen threshold. '
             f'{MIN_N}&#8211;29 decisions per area, so read the two extremes, not the '
             f'middle. {blank_p} pending applications carry no production area.</text>')
    o.append(f'<text x="36" y="{yb+66}" font-size="11.5" fill="{MUTED}">'
             f'Source: Fiskeridirektoratet Akvakults&#248;knader, layers 0 and 4. '
             f'Why area 8 runs at 754 days is not in this register &#8212; see the '
             f'recipe.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name} — {len(pts)} areas, quadrant at {xm:.0f}d / {ym:.0f}d")
    for p in sorted(pts, key=lambda p: -p["med"]):
        print(f"    {p['pa'][:30]:30s} n={p['n']:3d} med {p['med']:4.0f}d "
              f"p90 {p['p90']:4.0f}d  {p['key']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
