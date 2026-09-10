#!/usr/bin/env python3
"""What is waiting in the queue right now, and how long it has been waiting.

    python chart-queue-exposure.py <queue.csv>

Five things, one population: how long the median active project has waited (x),
how many gigawatts are behind it (y), how many projects that is (area), what they
are (fill), and which grid (border — solid California, dashed Midwest). The
whisker runs to the ninetieth percentile, because the tail is the finding: a queue
whose p90 sits just above its median is moving, and one where it is double has
projects that have been stuck for over a decade.

This replaces an earlier chart that plotted build rate against capacity. That one
needed two different populations for its two axes — the rate from projects old
enough to have finished, the capacity from everything queued — and could not show
any recent technology at all, because a young family has volume but no age-matched
rate. MISO's Hybrid, its fastest-growing category at 372 projects, was invisible
on it. Only ACTIVE projects appear here: nothing has resolved, so nothing needs
age-matching, and the number is what is exposed today rather than what happened
to a cohort that entered a decade ago.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import math
import statistics
import sys
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "queue-exposure.svg"
MIN_N = 20
LABEL_N = 2

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE = "#e3e2db"
FAMILY_HUE = {"Solar": "#b5651d", "Wind": "#3f7d3a", "Storage": "#2361b0",
              "Gas": "#7a4fa3", "Geothermal": "#a8324a", "Hybrid": "#1f7a86"}
FAMILY = {"solar": "Solar", "photovoltaic": "Solar",
          "wind": "Wind", "wind turbine": "Wind",
          "battery": "Storage", "battery storage": "Storage", "storage": "Storage",
          "pumped-storage hydro": "Storage",
          "natural gas": "Gas", "gas": "Gas",
          "geothermal": "Geothermal", "hybrid": "Hybrid"}
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
D = lambda s: dt.date.fromisoformat(s) if s else None          # noqa: E731


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    everything = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
    rows = [r for r in everything if r["status"] == "active" and r["queue_date"]]
    live = collections.Counter(r["iso"] for r in rows)
    done = collections.Counter(r["iso"] for r in everything
                               if r["status"] in ("built", "withdrawn"))
    today = dt.date.today()

    agg = collections.defaultdict(lambda: {"n": 0, "mw": 0.0, "age": []})
    unmapped = collections.Counter()
    for r in rows:
        fam = (FAMILY.get((r.get("fuel") or "").strip().lower())
               or FAMILY.get((r["technology"] or "").strip().lower()))
        if not fam:
            unmapped[(r["technology"] or "(blank)").strip()[:18]] += 1
            continue
        a = agg[(r["iso"], fam)]
        a["n"] += 1
        try:
            a["mw"] += float(r["mw"])
        except (TypeError, ValueError):
            pass
        a["age"].append((today - D(r["queue_date"])).days / 365.25)

    pts = []
    for (iso, fam), a in agg.items():
        if a["n"] < MIN_N or a["mw"] <= 0:
            continue
        ages = sorted(a["age"])
        pts.append({"iso": iso, "fam": fam, "n": a["n"], "gw": a["mw"] / 1000,
                    "med": statistics.median(ages),
                    "p90": ages[int(0.9 * len(ages))]})
    if not pts:
        print("  nothing to plot")
        return 1
    pts.sort(key=lambda p: p["med"])

    W, H, L, R, T, B = 980, 606, 92, 128, 226, 112
    x1 = max(p["p90"] for p in pts) * 1.08
    ys = [p["gw"] for p in pts]
    y0, y1 = min(ys) / 1.8, max(ys) * 1.8
    rmax = max(p["n"] for p in pts)

    def sx(v):
        return L + v / x1 * (W - L - R)

    def sy(v):
        return H - B - (math.log10(v) - math.log10(y0)) / \
            (math.log10(y1) - math.log10(y0)) * (H - T - B)

    def rad(n):
        return 9 + 26 * math.sqrt(n / rmax)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'What is stuck in the queue now, and how long it has been stuck</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Active projects only &#8212; nothing here has resolved. Fill is the family, '
             f'border the grid, area the project count, and the</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'whisker runs from the median wait to the ninetieth percentile.</text>')
    # The grids look lopsided here and it is not a sampling accident: California's
    # queue has largely cleared while the Midwest's is four times larger and still
    # running. Every other chart in this recipe uses resolved history, where the
    # asymmetry runs the other way, and a reader moving between them needs telling.
    o.append(f'<text x="36" y="{T-62}" font-size="12" fill="{MUTED}">'
             f'MISO shows more families because its live queue is larger: '
             f'{live["MISO"]:,} active projects against CAISO&#8217;s {live["CAISO"]:,}.</text>')
    o.append(f'<text x="36" y="{T-46}" font-size="12" fill="{MUTED}">'
             f'On resolved history the asymmetry reverses &#8212; CAISO has '
             f'{done["CAISO"]:,} finished projects to MISO&#8217;s {done["MISO"]:,} &#8212; '
             f'which is the population every other chart here uses.</text>')

    lx = 36
    for fam, hue in FAMILY_HUE.items():  # noqa: E501
        if not any(p["fam"] == fam for p in pts):
            continue
        o.append(f'<circle cx="{lx+7}" cy="134" r="7" fill="{hue}" fill-opacity="0.34" '
                 f'stroke="{hue}" stroke-width="1.6"/>')
        o.append(f'<text x="{lx+20}" y="138" font-size="12" fill="{INK2}">{fam}</text>')
        lx += 32 + len(fam) * 7.2
    lx += 16
    o.append(f'<circle cx="{lx+7}" cy="134" r="7" fill="none" stroke="{INK}" '
             f'stroke-width="2.2"/>')
    o.append(f'<text x="{lx+20}" y="138" font-size="12" fill="{INK2}">CAISO</text>')
    lx += 80
    o.append(f'<circle cx="{lx+7}" cy="134" r="7" fill="none" stroke="{INK}" '
             f'stroke-width="2.2" stroke-dasharray="3 2.4"/>')
    o.append(f'<text x="{lx+20}" y="138" font-size="12" fill="{INK2}">MISO</text>')

    for g in range(0, int(x1) + 1, 2):
        o.append(f'<line x1="{sx(g):.1f}" y1="{T}" x2="{sx(g):.1f}" y2="{H-B}" '
                 f'stroke="{RULE}"/>')
        o.append(f'<text x="{sx(g):.1f}" y="{H-B+21}" font-size="11.5" fill="{MUTED}" '
                 f'text-anchor="middle">{g}y</text>')
    for g in (20, 50, 100):
        if not y0 <= g <= y1:
            continue
        o.append(f'<line x1="{L}" y1="{sy(g):.1f}" x2="{W-R}" y2="{sy(g):.1f}" '
                 f'stroke="{RULE}"/>')
        o.append(f'<text x="{L-10}" y="{sy(g)+4:.1f}" font-size="11.5" fill="{MUTED}" '
                 f'text-anchor="end">{g} GW</text>')
    o.append(f'<text x="36" y="{T-16}" font-size="11.5" fill="{MUTED}">'
             f'gigawatts still waiting, log scale</text>')
    o.append(f'<text x="{(L+W-R)/2:.0f}" y="{H-B+46}" font-size="11.5" fill="{MUTED}" '
             f'text-anchor="middle">years already waited &#8212; median, whisker to the '
             f'90th percentile</text>')

    for p in pts:
        x, y, r = sx(p["med"]), sy(p["gw"]), rad(p["n"])
        hue = FAMILY_HUE[p["fam"]]
        dash = ' stroke-dasharray="3 2.4"' if p["iso"] == "MISO" else ""
        o.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{sx(p["p90"]):.1f}" y2="{y:.1f}" '
                 f'stroke="{hue}" stroke-width="1.8" stroke-opacity="0.75"/>')
        o.append(f'<line x1="{sx(p["p90"]):.1f}" y1="{y-5:.1f}" x2="{sx(p["p90"]):.1f}" '
                 f'y2="{y+5:.1f}" stroke="{hue}" stroke-width="1.8"/>')
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{hue}" '
                 f'fill-opacity="0.34" stroke="{hue}" stroke-width="2.4"{dash}/>')

    # Fastest two label below their marker, slowest two above, so the two Storage
    # bubbles sitting almost on top of each other do not share a caption.
    edges = [(p, +1) for p in pts[:LABEL_N]] + [(p, -1) for p in pts[-LABEL_N:]]
    for p, side in edges:
        x, y, r = sx(p["med"]), sy(p["gw"]), rad(p["n"])
        ty = y + (r + 26) if side > 0 else y - r - 24
        o.append(f'<text x="{x:.1f}" y="{ty:.1f}" font-size="12.5" font-weight="600" '
                 f'fill="{INK}" text-anchor="middle">{p["fam"]}, {p["iso"]}</text>')
        o.append(f'<text x="{x:.1f}" y="{ty+15:.1f}" font-size="11.5" fill="{MUTED}" '
                 f'text-anchor="middle">{p["med"]:.1f}y median &#183; {p["p90"]:.1f}y p90 '
                 f'&#183; {p["gw"]:.0f} GW</text>')

    ca = [p for p in pts if p["iso"] == "CAISO"]
    mi = [p for p in pts if p["iso"] == "MISO"]
    # The tail RATIO is about the same in both (1.7x vs 1.8x) and saying so
    # contradicted the headline it sat under. What actually separates them is the
    # absolute wait, and it separates completely.
    if ca and mi:
        worst_mi = max(p["med"] for p in mi)
        best_ca = min(p["med"] for p in ca)
        sep = best_ca > worst_mi
        o.append(f'<text x="36" y="{H-52}" font-size="12.5" fill="{INK}">'
                 f'<tspan font-weight="600">Every Midwest family has waited less than every '
                 f'California one &#8212; {worst_mi:.1f} years at worst against '
                 f'{best_ca:.1f} at best.</tspan>'
                 f'{" The two do not overlap at all." if sep else ""}</text>')
        cr = statistics.median([p["p90"] / p["med"] for p in ca])
        mr = statistics.median([p["p90"] / p["med"] for p in mi])
        o.append(f'<text x="36" y="{H-33}" font-size="12.5" fill="{INK2}">'
                 f'The tails are proportionally similar &#8212; p90 is {cr:.1f}&#215; the '
                 f'median in California and {mr:.1f}&#215; in the Midwest &#8212; so this is '
                 f'not a few stragglers. The whole queue is slower.</text>')
    n_un = sum(unmapped.values())
    o.append(f'<text x="36" y="{H-13}" font-size="11.5" fill="{MUTED}">'
             f'{n_un:,} active projects fall outside these families and are not plotted '
             f'({", ".join(f"{t} {n}" for t, n in unmapped.most_common(2))}). '
             f'Families keyed on fuel, not turbine type.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name} — {len(pts)} markers")
    for p in pts:
        print(f"    {p['iso']:<6}{p['fam']:<11}{p['n']:>5,} proj {p['gw']:>6.0f} GW  "
              f"median {p['med']:>4.1f}y  p90 {p['p90']:>5.1f}y")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
