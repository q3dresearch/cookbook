#!/usr/bin/env python3
"""When a platform writes your metric for you.

    python artefact.py

Kaggle auto-created a notebook for every dataset until some point in 2020,
which makes `TotalKernels` incomparable across years — and the test that
reveals it is simple enough to reuse anywhere.

Look only at datasets nobody obtained: one download or fewer. Those cannot have
a user-written notebook. Any notebook attached to them was created by the
platform. The share carrying one runs near 100% through 2019 and collapses to
8% by 2021, which dates the feature and disqualifies the earlier years.

This figure exists because the finding was originally written as a caption. A
correction usually needs its own chart: the old figure was built to argue the
old point.
"""
from __future__ import annotations

import collections
import csv
import re
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
DATA = RECIPE / "artifacts" / "data"
OUT = RECIPE / "artifacts" / "charts" / "a-platform-wrote-the-metric.svg"

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, HILITE, DIM = "#e1e0d9", "#c3c2b7", "#2361b0", "#b9c9e2"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def main() -> int:
    csv.field_size_limit(10 ** 7)
    quiet = collections.defaultdict(lambda: [0, 0])   # datasets with <=1 download
    allk = collections.defaultdict(lambda: [0, 0])    # every dataset
    for r in csv.DictReader((DATA / "Datasets.csv").open(newline="")):
        m = re.search(r"(20\d\d)", r.get("CreationDate") or "")
        if not m:
            continue
        try:
            d, k = int(r["TotalDownloads"] or 0), int(r["TotalKernels"] or 0)
        except ValueError:
            continue
        y = m.group(1)
        allk[y][0] += 1
        allk[y][1] += (k >= 1)
        if d <= 1:
            quiet[y][0] += 1
            quiet[y][1] += (k >= 1)
    yrs = [y for y in sorted(quiet) if quiet[y][0] >= 5 and y >= "2016"]

    W, H, L, R, T = 940, 520, 92, 42, 132
    ph = 200
    px = lambda i: L + i * (W - L - R) / (len(yrs) - 1)
    py = lambda v: T + ph - v / 100 * ph
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'>", f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="{L}" y="40" font-size="19" font-weight="600" fill="{INK}">'
             f'Kaggle wrote the notebooks itself, until it stopped</text>')
    o.append(f'<text x="{L}" y="64" font-size="13.5" fill="{INK2}">'
             f'A dataset nobody downloaded cannot have a notebook somebody wrote. Yet nearly all of them carried '
             f'one until 2020 &#8212;</text>')
    o.append(f'<text x="{L}" y="82" font-size="13.5" fill="{INK2}">'
             f'so &#8220;never opened in a notebook&#8221; measures a platform feature before 2021, not interest. '
             f'Any trend crossing that line is broken.</text>')

    for v in (0, 50, 100):
        o.append(f'<line x1="{L}" y1="{py(v):.1f}" x2="{W-R}" y2="{py(v):.1f}" stroke="{GRID}"/>')
        o.append(f'<text x="{L-10}" y="{py(v)+4:.1f}" font-size="11" fill="{MUTED}" text-anchor="end">{v}%</text>')

    for lab, src, col, wdt in (("all datasets", allk, DIM, 2), ("datasets with ≤1 download", quiet, HILITE, 2.5)):
        pts = " ".join(f"{px(i):.1f},{py(src[y][1]/src[y][0]*100):.1f}" for i, y in enumerate(yrs))
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{wdt}"/>')
        for i, y in enumerate(yrs):
            o.append(f'<circle cx="{px(i):.1f}" cy="{py(src[y][1]/src[y][0]*100):.1f}" r="3.5" fill="{col}"/>')
    o.append(f'<text x="{px(0)+8:.0f}" y="{py(quiet[yrs[0]][1]/quiet[yrs[0]][0]*100)-12:.0f}" '
             f'font-size="12" fill="{INK}">datasets with one download or fewer</text>')
    o.append(f'<text x="{px(0)+8:.0f}" y="{py(allk[yrs[0]][1]/allk[yrs[0]][0]*100)+22:.0f}" '
             f'font-size="12" fill="{INK2}">all datasets</text>')
    for i, y in enumerate(yrs):
        o.append(f'<text x="{px(i):.1f}" y="{T+ph+20:.0f}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="middle">{y}</text>')

    cut = [i for i, y in enumerate(yrs) if y == "2021"]
    if cut:
        x = px(cut[0])
        o.append(f'<line x1="{x:.1f}" y1="{T-8}" x2="{x:.1f}" y2="{T+ph}" stroke="{BASELINE}" stroke-dasharray="3 3"/>')
        o.append(f'<text x="{x+8:.0f}" y="{T-12}" font-size="11.5" fill="{INK2}">comparable from here</text>')

    yb = T + ph + 56
    o.append(f'<text x="{L}" y="{yb:.0f}" font-size="12.5" fill="{INK2}">'
             f'The 2019 &#8220;dip&#8221; an earlier version of this recipe could not explain was this feature at its '
             f'peak: 48.8% of 2019</text>')
    o.append(f'<text x="{L}" y="{yb+20:.0f}" font-size="12.5" fill="{INK2}">'
             f'datasets sit at <tspan font-weight="600">exactly one</tspan> notebook, against ~36% either side. '
             f'The cohort figure in this recipe now starts at 2021.</text>')
    o.append(f'<text x="{L}" y="{H-30}" font-size="11.5" fill="{MUTED}">'
             f'Source: Kaggle Meta Kaggle, Datasets.csv, retrieved 2026-09-09. Every dataset ever published.</text>')
    o.append(f'<text x="{L}" y="{H-14}" font-size="11.5" fill="{MUTED}">'
             f'Method and code: github.com/q3dresearch/cookbook &#183; recipes/dataset-demand-shape</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
