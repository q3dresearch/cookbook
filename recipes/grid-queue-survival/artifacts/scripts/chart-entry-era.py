#!/usr/bin/env python3
"""When each technology was in the queue, and why comparing them is not obvious.

    python chart-entry-era.py <queue.csv>

This is the caveat chart. Every technology comparison in this recipe depends on
the claim that these families occupied the queue at different times, and until
now that claim lived only in a terminal. Here it is: each bar spans the middle
half of a family's entry years, with the median marked.

California's gas sits in 2007-2008 and its storage in 2018-2021. The two do not
touch. A ranking of gas against storage on all-time survival is therefore a
comparison of the 2007 interconnection process against the 2020 one, wearing the
labels of two technologies — which is exactly what the first version of this
recipe published.

Both grids, because the shapes differ and that difference is itself the finding:
CAISO's families are strung across two decades, MISO's are stacked in the last
six years. The two queues are not at the same point in their lives.
"""
from __future__ import annotations

import collections
import csv
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from families import HUE, family_of                            # noqa: E402

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "entry-era.svg"
MIN_N = 40

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE = "#e3e2db"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))

    per = collections.defaultdict(list)
    for r in rows:
        y = (r["queue_date"] or "")[:4]
        fam = family_of(r)
        if fam and y.isdigit() and 1995 < int(y) < 2030:
            per[(r["iso"], fam)].append(int(y))

    bars = []
    for (iso, fam), ys in per.items():
        if len(ys) < MIN_N:
            continue
        ys.sort()
        bars.append({"iso": iso, "fam": fam, "n": len(ys),
                     "q1": ys[len(ys) // 4], "med": statistics.median(ys),
                     "q3": ys[3 * len(ys) // 4], "lo": ys[0], "hi": ys[-1]})
    if not bars:
        print("  nothing to plot")
        return 1
    bars.sort(key=lambda b: (b["iso"], b["med"]))

    W, L, R, T, RH = 1000, 230, 168, 214, 40
    H = T + len(bars) * RH + 194
    lo = min(b["lo"] for b in bars)
    hi = max(b["hi"] for b in bars)

    def sx(y):
        return L + (y - lo) / max(hi - lo, 1) * (W - L - R)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'These technologies were never in the queue at the same time</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'When each family entered. The bar is the middle half of its entry years, the '
             f'line its full range, the notch its median.</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'This is why every comparison in this recipe is made within a cohort: rank two '
             f'families whose bars do not overlap and you have</text>')
    o.append(f'<text x="36" y="106" font-size="13.5" fill="{INK2}">'
             f'compared two decades of interconnection policy, not two technologies.</text>')

    for y in range(((lo + 4) // 5) * 5, hi + 1, 5):
        o.append(f'<line x1="{sx(y):.1f}" y1="{T-24}" x2="{sx(y):.1f}" '
                 f'y2="{T+len(bars)*RH-16}" stroke="{RULE}"/>')
        o.append(f'<text x="{sx(y):.1f}" y="{T+len(bars)*RH+4}" font-size="11.5" '
                 f'fill="{MUTED}" text-anchor="middle">{y}</text>')

    last_iso = None
    for i, b in enumerate(bars):
        y = T + i * RH
        if b["iso"] != last_iso:
            o.append(f'<text x="36" y="{y+5}" font-size="13" font-weight="600" fill="{INK}">'
                     f'{b["iso"]}</text>')
            last_iso = b["iso"]
        c = HUE.get(b["fam"], "#52514e")
        o.append(f'<text x="{L-16}" y="{y+5}" font-size="12.5" fill="{INK2}" '
                 f'text-anchor="end">{b["fam"]}</text>')
        o.append(f'<line x1="{sx(b["lo"]):.1f}" y1="{y}" x2="{sx(b["hi"]):.1f}" y2="{y}" '
                 f'stroke="{c}" stroke-width="1.3" stroke-opacity="0.5"/>')
        o.append(f'<rect x="{sx(b["q1"]):.1f}" y="{y-9}" '
                 f'width="{max(sx(b["q3"])-sx(b["q1"]), 3):.1f}" height="18" rx="3" '
                 f'fill="{c}" fill-opacity="0.42" stroke="{c}" stroke-width="1.6"/>')
        o.append(f'<line x1="{sx(b["med"]):.1f}" y1="{y-9}" x2="{sx(b["med"]):.1f}" '
                 f'y2="{y+9}" stroke="{c}" stroke-width="2.6"/>')
        o.append(f'<text x="{W-R+12}" y="{y+4}" font-size="11.5" fill="{MUTED}">'
                 f'{b["q1"]}&#8211;{b["q3"]} &#183; n={b["n"]:,}</text>')

    yb = T + len(bars) * RH + 34
    ca = {b["fam"]: b for b in bars if b["iso"] == "CAISO"}
    o.append(f'<line x1="36" y1="{yb-18}" x2="{W-36}" y2="{yb-18}" stroke="{RULE}"/>')
    if "Gas" in ca and "Storage" in ca:
        g, st = ca["Gas"], ca["Storage"]
        o.append(f'<text x="36" y="{yb+4}" font-size="13" fill="{INK}">'
                 f'<tspan font-weight="600">California&#8217;s gas sits in '
                 f'{g["q1"]}&#8211;{g["q3"]} and its storage in {st["q1"]}&#8211;{st["q3"]}. '
                 f'The two never overlap.</tspan> The first version of this recipe '
                 f'ranked them against each other.</text>')
    o.append(f'<text x="36" y="{yb+28}" font-size="12.5" fill="{INK2}">'
             f'The two queues are at different points in their own lives: California&#8217;s '
             f'families are strung across two decades, the Midwest&#8217;s are stacked in the '
             f'last six.</text>')
    mi = {b["fam"]: b for b in bars if b["iso"] == "MISO"}
    if "Gas" in ca and "Gas" in mi:
        o.append(f'<text x="36" y="{yb+47}" font-size="12.5" fill="{INK2}">'
                 f'And gas runs opposite ways: it is California&#8217;s oldest family '
                 f'(median {ca["Gas"]["med"]:.0f}) and the Midwest&#8217;s newest '
                 f'(median {mi["Gas"]["med"]:.0f}).</text>')
    o.append(f'<text x="36" y="{yb+78}" font-size="11.5" fill="{MUTED}">'
             f'Families with fewer than {MIN_N} projects in a grid are omitted. Families keyed '
             f'on fuel, not turbine type. Entry year is the queue date.</text>')
    o.append(f'<text x="36" y="{yb+96}" font-size="11.5" fill="{MUTED}">'
             f'Sources: CAISO PublicQueueReport.xlsx, MISO api/giqueue/getprojects.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name} — {len(bars)} family/grid bars")
    for b in bars:
        print(f"    {b['iso']:<6}{b['fam']:<11}{b['q1']}-{b['q3']}  median {b['med']:.0f}  "
              f"range {b['lo']}-{b['hi']}  n={b['n']:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
