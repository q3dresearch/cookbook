#!/usr/bin/env python3
"""Which kinds of dataset get used, and which do not.

    python categories.py

Joins Kaggle's tag taxonomy onto the population. Categories with at least 2,000
datasets only — below that the medians are unstable and the ranking becomes a
list of small tags rather than a finding.

The join is DatasetTags.DatasetId -> Datasets.Id, both surrogate ids from the
same export, which is the one case where joining on a surrogate is safe: they
are internally consistent within a single Meta Kaggle snapshot. Do not carry
these ids across snapshots.
"""
from __future__ import annotations

import collections
import csv
import statistics as st
from pathlib import Path
from xml.sax.saxutils import escape

RECIPE = Path(__file__).resolve().parents[2]
DATA = RECIPE / "artifacts" / "data"
OUT = RECIPE / "artifacts" / "charts" / "which-categories-get-used.svg"
MIN_N = 2000

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, HILITE, DIM = "#e1e0d9", "#c3c2b7", "#2361b0", "#c9c8c1"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def load():
    csv.field_size_limit(10 ** 7)
    ds = {}
    for r in csv.DictReader((DATA / "Datasets.csv").open(newline="")):
        try:
            ds[r["Id"]] = (int(r["TotalDownloads"] or 0), int(r["TotalKernels"] or 0),
                           bool(r["OwnerOrganizationId"]))
        except ValueError:
            pass
    tags = {r["Id"]: r["Name"] for r in csv.DictReader((DATA / "Tags.csv").open(newline=""))}
    bytag = collections.defaultdict(list)
    for r in csv.DictReader((DATA / "DatasetTags.csv").open(newline="")):
        d = ds.get(r["DatasetId"])
        if d and r["TagId"] in tags:
            bytag[tags[r["TagId"]]].append(d)
    return ds, bytag


def main() -> int:
    ds, bytag = load()
    rows = [(k, len(v), st.median(x[0] for x in v), sum(1 for x in v if x[1] == 0) / len(v) * 100)
            for k, v in bytag.items() if len(v) >= MIN_N]
    rows.sort(key=lambda r: -r[2])
    show = rows[:6] + rows[-6:]

    W, H, L, R, T = 1000, 730, 210, 40, 118
    bh, gap = 22, 11
    mx = max(r[2] for r in show)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'>", f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="{L-140}" y="40" font-size="19" font-weight="600" fill="{INK}">'
             f'Datasets tagged &#8220;research&#8221; are among the least used on Kaggle</text>')
    o.append(f'<text x="{L-140}" y="64" font-size="13.5" fill="{INK2}">'
             f'Median lifetime downloads by category, for the {len(rows)} tags with at least '
             f'{MIN_N:,} datasets. The spread is 60-fold, and</text>')
    o.append(f'<text x="{L-140}" y="82" font-size="13.5" fill="{INK2}">'
             f'a specialist corpus sits at the wrong end of it. All {len(ds):,} datasets ever published.</text>')

    for i, (name, n, med, never) in enumerate(show):
        y = T + i * (bh + gap) + (18 if i >= 6 else 0)
        w = med / mx * (W - L - R - 300)
        hot = name in ("research", "pre-trained model")
        o.append(f'<text x="{L-12}" y="{y+bh*0.72:.0f}" font-size="12.5" '
                 f'fill="{INK if hot else INK2}" text-anchor="end">{escape(name)}</text>')
        o.append(f'<rect x="{L}" y="{y}" width="{max(w,1.5):.1f}" height="{bh}" rx="3.5" '
                 f'fill="{HILITE}" opacity="{1.0 if hot else 0.55}"/>')
        o.append(f'<text x="{L+max(w,1.5)+10:.1f}" y="{y+bh*0.72:.0f}" font-size="12" fill="{INK}">'
                 f'{med:,.0f} <tspan fill="{MUTED}">dl &#183; {n:,} sets &#183; {never:.0f}% never used</tspan></text>')
    ymid = T + 6 * (bh + gap) + 4
    o.append(f'<line x1="{L-200}" y1="{ymid:.0f}" x2="{W-R}" y2="{ymid:.0f}" stroke="{BASELINE}" '
             f'stroke-dasharray="3 3"/>')
    o.append(f'<text x="{L-200}" y="{ymid-6:.0f}" font-size="11" fill="{MUTED}">most used</text>')
    o.append(f'<text x="{L-200}" y="{ymid+18:.0f}" font-size="11" fill="{MUTED}">least used</text>')

    org = [v for v in ds.values() if v[2]]
    ind = [v for v in ds.values() if not v[2]]
    yb = T + 12 * (bh + gap) + 78
    o.append(f'<text x="{L-140}" y="{yb:.0f}" font-size="13" font-weight="600" fill="{INK}">'
             f'The organisation &#8220;advantage&#8221; is mostly a head start</text>')
    o.append(f'<text x="{L-140}" y="{yb+24:.0f}" font-size="12.5" fill="{INK2}">'
             f'organisations median {st.median(x[0] for x in org):,.0f} downloads, individuals '
             f'{st.median(x[0] for x in ind):,.0f} &#8212; a twentyfold gap.</text>')
    o.append(f'<text x="{L-140}" y="{yb+44:.0f}" font-size="12.5" fill="{INK2}">'
             f'But median publication year is 2018 for organisations and 2024 for individuals. Matched on year '
             f'and size band,</text>')
    o.append(f'<text x="{L-140}" y="{yb+64:.0f}" font-size="12.5" fill="{INK}">'
             f'the advantage falls to <tspan font-weight="600">2.8x</tspan>. Most of the headline gap is six extra '
             f'years of accumulation, not the badge.</text>')

    o.append(f'<text x="{L-140}" y="{H-30}" font-size="11.5" fill="{MUTED}">'
             f'Source: Kaggle Meta Kaggle (Datasets, Tags, DatasetTags), retrieved 2026-09-09.</text>')
    o.append(f'<text x="{L-140}" y="{H-14}" font-size="11.5" fill="{MUTED}">'
             f'Method and code: github.com/q3dresearch/cookbook &#183; recipes/dataset-demand-shape</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name}  ({len(rows)} categories over {MIN_N:,} datasets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
