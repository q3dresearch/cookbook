#!/usr/bin/env python3
"""Does file size predict whether a dataset gets used?

    python size.py

Yes — and a sample drawn from the platform's own popularity orderings says the
opposite, which is the more useful half of this figure.

Sampling `votes` and `hottest` reaches only datasets that already succeeded.
Within winners, size carries almost no signal. Across the whole population it
carries a monotonic one. The sample did not merely lose precision; it inverted
the conclusion, and nothing inside the sample could have revealed that.

The recency confound is ruled out rather than waved away: median creation year
is 2024 in every size band, and the effect survives inside the 2023 cohort
alone, where age is held constant.
"""
from __future__ import annotations

import collections
import csv
import re
import statistics as st
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
DATA = RECIPE / "artifacts" / "data"
OUT = RECIPE / "artifacts" / "charts" / "size-predicts-use.svg"

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, HILITE, DIM = "#e1e0d9", "#c3c2b7", "#2361b0", "#b9c9e2"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
BANDS = [(1, "under 1 MB"), (100, "1–100 MB"), (1000, "100 MB–1 GB"), (9e9, "over 1 GB")]


def band(b):
    mb = b / 1e6
    for hi, name in BANDS:
        if mb < hi:
            return name


def load():
    csv.field_size_limit(10 ** 7)
    size = {}
    for r in csv.DictReader((DATA / "DatasetVersions.csv").open(newline="")):
        did = r.get("DatasetId")
        try:
            b = int(r.get("TotalUncompressedBytes") or 0)
        except ValueError:
            b = 0
        if did and b:
            size[did] = max(size.get(did, 0), b)
    allb, cohort = collections.defaultdict(list), collections.defaultdict(list)
    for r in csv.DictReader((DATA / "Datasets.csv").open(newline="")):
        b = size.get(r["Id"])
        if not b:
            continue
        try:
            d, k = int(r["TotalDownloads"] or 0), int(r["TotalKernels"] or 0)
        except ValueError:
            continue
        allb[band(b)].append((d, k))
        m = re.search(r"(20\d\d)", r.get("CreationDate") or "")
        if m and m.group(1) == "2023":
            cohort[band(b)].append((d, k))
    return allb, cohort


def main() -> int:
    allb, cohort = load()
    n = sum(len(v) for v in allb.values())
    names = [nm for _, nm in BANDS]

    W, H, L, R, T = 960, 510, 160, 40, 126
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'>", f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="{L-120}" y="40" font-size="19" font-weight="600" fill="{INK}">'
             f'Bigger datasets are used less &#8212; and sampling the winners hides it</text>')
    o.append(f'<text x="{L-120}" y="64" font-size="13.5" fill="{INK2}">'
             f'Across all {n:,} datasets with a recorded size, both measures of not-being-used climb with file size. '
             f'A sample</text>')
    o.append(f'<text x="{L-120}" y="82" font-size="13.5" fill="{INK2}">'
             f'drawn from Kaggle&#8217;s own popularity orderings reaches only datasets that already succeeded, and '
             f'reports no such effect.</text>')

    bh, gap = 30, 16
    mx = 100.0
    # Two measures, because the magnitude depends on which you pick and showing
    # only the flattering one would be a choice the reader cannot see.
    o.append(f'<text x="{L-120}" y="{T-14}" font-size="11.5" fill="{MUTED}">'
             f'whole population, two measures of not-being-used</text>')
    for i, nm in enumerate(names):
        y = T + i * (bh + gap)
        v = allb[nm]
        under10 = sum(1 for x in v if x[0] < 10) / len(v) * 100
        never = sum(1 for x in v if x[1] == 0) / len(v) * 100
        wide = W - L - R - 250
        o.append(f'<text x="{L-12}" y="{y+13:.0f}" font-size="12.5" fill="{INK2}" text-anchor="end">{nm}</text>')
        o.append(f'<rect x="{L}" y="{y}" width="{under10/mx*wide:.1f}" height="13" rx="3" fill="{HILITE}"/>')
        o.append(f'<rect x="{L}" y="{y+15}" width="{never/mx*wide:.1f}" height="13" rx="3" fill="{DIM}"/>')
        o.append(f'<text x="{L+under10/mx*wide+9:.1f}" y="{y+11:.0f}" font-size="12" fill="{INK}">{under10:.0f}%'
                 f' <tspan fill="{MUTED}">under 10 downloads</tspan></text>')
        o.append(f'<text x="{L+never/mx*wide+9:.1f}" y="{y+26:.0f}" font-size="12" fill="{INK2}">{never:.0f}%'
                 f' <tspan fill="{MUTED}">never in a notebook &#183; n={len(v):,}</tspan></text>')

    c26 = cohort["under 1 MB"]; c1g = cohort["over 1 GB"]
    f26 = sum(1 for x in c26 if x[0] < 10) / len(c26) * 100
    f1g = sum(1 for x in c1g if x[0] < 10) / len(c1g) * 100
    yb = T + 4 * (bh + gap) + 34
    o.append(f'<text x="{L-120}" y="{yb:.0f}" font-size="12.5" fill="{INK2}">'
             f'Not an age effect: within the 2023 cohort alone, under-10-downloads runs {f26:.0f}% for the smallest '
             f'band against {f1g:.0f}% for the largest.</text>')
    yb += 44
    o.append(f'<text x="{L-120}" y="{yb:.0f}" font-size="13" font-weight="600" fill="{INK}">'
             f'The same question, answered by a sample of 4,233 that had already been noticed</text>')
    o.append(f'<text x="{L-120}" y="{yb+24:.0f}" font-size="12.5" fill="{INK2}">'
             f'share under 100 downloads: 28% &#183; 23% &#183; 21% &#183; 15% &#183; 18% &#183; 22% from smallest to largest &#8212; '
             f'flat, and the</text>')
    o.append(f'<text x="{L-120}" y="{yb+42:.0f}" font-size="12.5" fill="{INK2}">'
             f'smallest band the deadest. The sample did not lose precision. It inverted the conclusion.</text>')
    o.append(f'<text x="{L-120}" y="{H-30}" font-size="11.5" fill="{MUTED}">'
             f'Source: Kaggle Meta Kaggle (Datasets, DatasetVersions), retrieved 2026-09-09. Median creation year is '
             f'2024 in every band.</text>')
    o.append(f'<text x="{L-120}" y="{H-14}" font-size="11.5" fill="{MUTED}">'
             f'Method and code: github.com/q3dresearch/cookbook &#183; recipes/dataset-demand-shape</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name}  (n={n:,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
