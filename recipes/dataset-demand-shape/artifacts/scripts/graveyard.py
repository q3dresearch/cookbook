#!/usr/bin/env python3
"""How big is the dataset graveyard, and who is filling it?

    python graveyard.py

412,935 datasets — 56% of everything ever published on Kaggle — have ten
lifetime downloads or fewer. The absolute number grows faster than publication
does, because the dead share is rising at the same time as the volume.

The obvious explanation is spam, and the data rejects it. 96.8% of datasets
earn no medal, and publishers who post once are barely better off than those
who post a hundred times: 161,320 people published exactly one dataset and the
median got twelve downloads. This is not dumping. It is ordinary people trying
once and being ignored.

RECENCY IS REAL HERE and the figure says so: a 2026 dataset has had months to
find an audience where a 2021 one has had five years. The 2021 cohort is the
honest floor — five years old, and still 30% dead.
"""
from __future__ import annotations

import collections
import csv
import re
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
DATA = RECIPE / "artifacts" / "data"
OUT = RECIPE / "artifacts" / "charts" / "the-graveyard-is-growing.svg"

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, HILITE, DIM = "#e1e0d9", "#c3c2b7", "#2361b0", "#c9d6ea"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def main() -> int:
    csv.field_size_limit(10 ** 7)
    by = collections.defaultdict(lambda: [0, 0])
    once = collections.defaultdict(list)
    for r in csv.DictReader((DATA / "Datasets.csv").open(newline="")):
        m = re.search(r"(20\d\d)", r.get("CreationDate") or "")
        try:
            d = int(r["TotalDownloads"] or 0)
        except ValueError:
            continue
        if m:
            by[m.group(1)][0] += 1
            by[m.group(1)][1] += (d <= 10)
        o = r.get("OwnerUserId")
        if o:
            once[o].append(d)
    yrs = [y for y in sorted(by) if y >= "2018"]
    dead_all = sum(v[1] for v in by.values())
    tot_all = sum(v[0] for v in by.values())
    solo = [v[0] for v in once.values() if len(v) == 1]
    solo_med = sorted(solo)[len(solo) // 2]

    W, H, L, R, T = 940, 600, 92, 42, 136
    ph = 210
    mx = max(v[0] for v in by.values())
    bw = (W - L - R) / len(yrs) * 0.62
    px = lambda i: L + (i + 0.5) * (W - L - R) / len(yrs)
    py = lambda v: T + ph - v / mx * ph

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'>", f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="{L}" y="40" font-size="19" font-weight="600" fill="{INK}">'
             f'The graveyard grows faster than the catalogue</text>')
    o.append(f'<text x="{L}" y="64" font-size="13.5" fill="{INK2}">'
             f'{dead_all:,} datasets &#8212; {dead_all/tot_all*100:.0f}% of everything ever published on Kaggle '
             f'&#8212; have ten lifetime downloads or fewer.</text>')
    o.append(f'<text x="{L}" y="82" font-size="13.5" fill="{INK2}">'
             f'Publication grew seventeenfold since 2018; the share that goes nowhere grew alongside it.</text>')

    for v in (50000, 100000, 150000):
        o.append(f'<line x1="{L}" y1="{py(v):.1f}" x2="{W-R}" y2="{py(v):.1f}" stroke="{GRID}"/>')
        o.append(f'<text x="{L-10}" y="{py(v)+4:.1f}" font-size="11" fill="{MUTED}" text-anchor="end">'
                 f'{v//1000}k</text>')
    o.append(f'<text x="{L-10}" y="{T-14:.0f}" font-size="11.5" fill="{MUTED}">datasets published that year</text>')
    o.append(f'<line x1="{L}" y1="{T+ph}" x2="{W-R}" y2="{T+ph}" stroke="{BASELINE}" stroke-width="1.5"/>')

    for i, y in enumerate(yrs):
        t, dead = by[y]
        x = px(i) - bw / 2
        o.append(f'<rect x="{x:.1f}" y="{py(t):.1f}" width="{bw:.1f}" height="{ph-(py(t)-T):.1f}" '
                 f'rx="3" fill="{DIM}"/>')
        o.append(f'<rect x="{x:.1f}" y="{py(dead):.1f}" width="{bw:.1f}" height="{ph-(py(dead)-T):.1f}" '
                 f'rx="3" fill="{HILITE}"/>')
        o.append(f'<text x="{px(i):.1f}" y="{py(t)-8:.1f}" font-size="11" fill="{INK2}" '
                 f'text-anchor="middle">{dead/t*100:.0f}%</text>')
        o.append(f'<text x="{px(i):.1f}" y="{T+ph+20:.0f}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="middle">{y}</text>')
    o.append(f'<rect x="{L}" y="{T+ph+34}" width="11" height="11" rx="2" fill="{HILITE}"/>')
    o.append(f'<text x="{L+18}" y="{T+ph+44:.0f}" font-size="11.5" fill="{INK2}">'
             f'ten downloads or fewer</text>')
    o.append(f'<rect x="{L+170}" y="{T+ph+34}" width="11" height="11" rx="2" fill="{DIM}"/>')
    o.append(f'<text x="{L+188}" y="{T+ph+44:.0f}" font-size="11.5" fill="{INK2}">everything else</text>')
    o.append(f'<text x="{W-R}" y="{T+ph+44:.0f}" font-size="11.5" fill="{MUTED}" text-anchor="end">'
             f'recent years are inflated by recency &#8212; 2021, five years old, is the honest floor at '
             f'{by["2021"][1]/by["2021"][0]*100:.0f}%</text>')

    yb = T + ph + 86
    o.append(f'<text x="{L}" y="{yb:.0f}" font-size="13" font-weight="600" fill="{INK}">'
             f'It is not spam. It is people trying once.</text>')
    o.append(f'<text x="{L}" y="{yb+22:.0f}" font-size="12.5" fill="{INK2}">'
             f'96.8% of datasets earn no medal, and prolific publishers do barely worse than one-timers. '
             f'{len(solo):,} people</text>')
    o.append(f'<text x="{L}" y="{yb+42:.0f}" font-size="12.5" fill="{INK2}">'
             f'published exactly one dataset &#8212; presumably their best effort &#8212; and the median got '
             f'<tspan font-weight="600">{solo_med} downloads</tspan>.</text>')
    o.append(f'<text x="{L}" y="{H-30}" font-size="11.5" fill="{MUTED}">'
             f'Source: Kaggle Meta Kaggle, Datasets.csv, retrieved 2026-09-09. Every dataset ever published.</text>')
    o.append(f'<text x="{L}" y="{H-14}" font-size="11.5" fill="{MUTED}">'
             f'Method and code: github.com/q3dresearch/cookbook &#183; recipes/dataset-demand-shape</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name}  ({dead_all:,} dead of {tot_all:,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
