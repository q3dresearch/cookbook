#!/usr/bin/env python3
"""Does an organisation badge earn downloads, or did organisations just arrive first?

    python matched.py

The raw gap is twentyfold — organisations median 158 downloads, individuals 8.
But organisations published in 2018 and individuals in 2024, and six years of
accumulation is worth a great deal on a cumulative counter.

Comparing within publication year removes that. What is left is a real but far
smaller advantage, and this figure shows both the gap and the reason it is
mostly not what it looks like.
"""
from __future__ import annotations

import collections
import csv
import re
import statistics as st
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
DATA = RECIPE / "artifacts" / "data"
OUT = RECIPE / "artifacts" / "charts" / "the-badge-or-the-head-start.svg"

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, HILITE, DIM = "#e1e0d9", "#c3c2b7", "#2361b0", "#b9c9e2"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def main() -> int:
    csv.field_size_limit(10 ** 7)
    org = collections.defaultdict(list)
    ind = collections.defaultdict(list)
    for r in csv.DictReader((DATA / "Datasets.csv").open(newline="")):
        m = re.search(r"(20\d\d)", r.get("CreationDate") or "")
        if not m:
            continue
        try:
            d = int(r["TotalDownloads"] or 0)
        except ValueError:
            continue
        (org if r["OwnerOrganizationId"] else ind)[m.group(1)].append(d)
    # Every year on the axis, evenly spaced. Filtering to years with enough
    # organisation datasets and then joining the survivors would draw a line
    # from 2020 straight to 2024 and imply a step that does not exist.
    yrs = [y for y in sorted(set(org) | set(ind)) if y >= "2016"]
    THIN = 20   # below this, the organisation median is not worth plotting
    no, ni = sum(len(v) for v in org.values()), sum(len(v) for v in ind.values())

    W, H, L, R, T = 940, 600, 92, 42, 132
    ph = 190
    px = lambda i: L + i * (W - L - R) / (len(yrs) - 1)
    lo, hi = 0.0, 3.9        # log10 downloads
    py = lambda v: T + ph - (max(v, 1) and (__import__("math").log10(max(v, 1)) - lo) / (hi - lo)) * ph

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'>", f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="{L}" y="40" font-size="19" font-weight="600" fill="{INK}">'
             f'The organisation advantage is mostly six years of head start</text>')
    o.append(f'<text x="{L}" y="64" font-size="13.5" fill="{INK2}">'
             f'Organisations median 158 lifetime downloads against 8 for individuals &#8212; twentyfold. But they '
             f'published in 2018 and</text>')
    o.append(f'<text x="{L}" y="82" font-size="13.5" fill="{INK2}">'
             f'individuals in 2024. Compared within the same year, the gap is a fraction of that.</text>')

    for e in range(0, 4):
        yy = py(10 ** e)
        o.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{W-R}" y2="{yy:.1f}" stroke="{GRID}"/>')
        o.append(f'<text x="{L-10}" y="{yy+4:.1f}" font-size="11" fill="{MUTED}" text-anchor="end">'
                 f'{10**e:,}</text>')
    o.append(f'<text x="{L-10}" y="{T-32:.0f}" font-size="11.5" fill="{MUTED}">'
             f'median lifetime downloads (log) &#183; hollow marks are years with under {THIN} organisation datasets</text>')

    for lab, src, col, thin in (("organisation", org, HILITE, THIN), ("individual", ind, DIM, 1)):
        run = []
        for i, y in enumerate(yrs):
            if len(src[y]) >= thin:
                run.append(f"{px(i):.1f},{py(st.median(src[y])):.1f}")
            else:                       # break the line rather than bridge it
                if len(run) > 1:
                    o.append(f'<polyline points="{" ".join(run)}" fill="none" stroke="{col}" stroke-width="2.5"/>')
                run = []
        if len(run) > 1:
            o.append(f'<polyline points="{" ".join(run)}" fill="none" stroke="{col}" stroke-width="2.5"/>')
        for i, y in enumerate(yrs):
            n = len(src[y])
            if n >= thin:
                o.append(f'<circle cx="{px(i):.1f}" cy="{py(st.median(src[y])):.1f}" r="4" fill="{col}"/>')
            elif n:
                o.append(f'<circle cx="{px(i):.1f}" cy="{py(st.median(src[y])):.1f}" r="3" fill="{SURFACE}" '
                         f'stroke="{col}" stroke-width="1.5" stroke-dasharray="1.5 1.5"/>')
    o.append(f'<text x="{px(0)+8:.0f}" y="{py(st.median(org[yrs[0]]))-12:.0f}" font-size="12" fill="{INK}">'
             f'published by an organisation</text>')
    o.append(f'<text x="{px(0)+8:.0f}" y="{py(st.median(ind[yrs[0]]))+22:.0f}" font-size="12" fill="{INK2}">'
             f'published by an individual</text>')
    for i, y in enumerate(yrs):
        o.append(f'<text x="{px(i):.1f}" y="{T+ph+20:.0f}" font-size="11" fill="{MUTED}" text-anchor="middle">{y}</text>')

    yb = T + ph + 54
    o.append(f'<text x="{L}" y="{yb:.0f}" font-size="11.5" fill="{MUTED}">'
             f'where each group actually published &#8212; share of its own datasets</text>')
    bh = 15
    for j, (lab, src, tot, col) in enumerate((("organisations", org, no, HILITE), ("individuals", ind, ni, DIM))):
        yy = yb + 14 + j * (bh + 8)
        x = L
        for i, y in enumerate(yrs):
            w = len(src[y]) / tot * (W - L - R)
            o.append(f'<rect x="{x:.1f}" y="{yy}" width="{max(w-1,0.5):.1f}" height="{bh}" fill="{col}" '
                     f'opacity="{0.45 + 0.55*(i/len(yrs))}"/>')
            if w > 44:
                o.append(f'<text x="{x+w/2:.1f}" y="{yy+11:.0f}" font-size="10" fill="{SURFACE}" '
                         f'text-anchor="middle">{y}</text>')
            x += w
        o.append(f'<text x="{L-10}" y="{yy+11:.0f}" font-size="11.5" fill="{INK2}" text-anchor="end">{lab}</text>')

    o.append(f'<text x="{L}" y="{yb+80:.0f}" font-size="12.5" fill="{INK}">'
             f'Matched on publication year and size band across 18 strata, the advantage falls from '
             f'<tspan font-weight="600">20x to 2.8x</tspan>.</text>')
    o.append(f'<text x="{L}" y="{yb+100:.0f}" font-size="12.5" fill="{INK2}">'
             f'That residual is real and unexplained &#8212; matching removes year and size, not promotion, '
             f'audience or subject.</text>')
    o.append(f'<text x="{L}" y="{H-30}" font-size="11.5" fill="{MUTED}">'
             f'Source: Kaggle Meta Kaggle, Datasets.csv, retrieved 2026-09-09. Years with at least 20 organisation '
             f'datasets.</text>')
    o.append(f'<text x="{L}" y="{H-14}" font-size="11.5" fill="{MUTED}">'
             f'Method and code: github.com/q3dresearch/cookbook &#183; recipes/dataset-demand-shape</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
