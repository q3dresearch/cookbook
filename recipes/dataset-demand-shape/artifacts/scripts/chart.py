#!/usr/bin/env python3
"""What happens to a dataset published on Kaggle?

    python chart.py

Two sources, deliberately not joined. Kaggle's own Meta Kaggle index gives the
POPULATION — every dataset ever published, with downloads, votes and notebook
counts — and is the only way to get a denominator, because the public list API
caps at 8,000 rows per ordering. The list-API sample gives SIZE, which Meta
Kaggle does not record at all.

They are kept apart because Meta Kaggle keys on a surrogate `Id` while the list
API keys on the business key `ref`. Surrogate ids get re-based; joining on one
is how a refresh invents change that never happened.

The 100 MB index is fetched, not committed. It is reconstructible from a URL
that needs no credentials, so shipping the fetch is more honest than freezing a
copy — and it keeps the repo clonable.
"""
from __future__ import annotations

import csv
import collections
import re
import sys
import urllib.request
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
INDEX = RECIPE / "artifacts" / "data" / "Datasets.csv"
URL = ("https://www.kaggle.com/api/v1/datasets/download/kaggle/meta-kaggle"
       "?file_name=Datasets.csv")
OUT = RECIPE / "artifacts" / "charts" / "what-happens-to-a-dataset.svg"

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, HILITE, DIM = "#e1e0d9", "#c3c2b7", "#2361b0", "#c9c8c1"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
BANDS = [(0, 0, "0"), (1, 10, "1–10"), (11, 100, "11–100"),
         (101, 1000, "101–1,000"), (1001, 10000, "1,000–10,000"), (10001, 10**9, "over 10,000")]


def fetch() -> None:
    """One fetcher, in fetch.py. Two would drift apart."""
    if INDEX.exists():
        return
    raise SystemExit("  data/Datasets.csv missing — run `python fetch.py` first")


def read():
    counts, cohort, dl, never = collections.Counter(), collections.defaultdict(lambda: [0, 0]), [], 0
    with INDEX.open(newline="") as fh:
        for r in csv.DictReader(fh):
            try:
                d, k = int(r["TotalDownloads"] or 0), int(r["TotalKernels"] or 0)
            except ValueError:
                continue
            dl.append(d)
            never += (k == 0)
            for lo, hi, lab in BANDS:
                if lo <= d <= hi:
                    counts[lab] += 1
                    break
            m = re.search(r"(20\d\d)", r.get("CreationDate") or "")
            if m:
                cohort[m.group(1)][0] += 1
                cohort[m.group(1)][1] += (k == 0)
    dl.sort()
    return counts, {y: v for y, v in sorted(cohort.items()) if v[0] > 500}, dl, never


def main() -> int:
    fetch()
    counts, cohort, dl, nk = read()
    n = len(dl)
    med = dl[n // 2]

    W, H, L, R = 940, 668, 150, 40
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'>", f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="{L}" y="40" font-size="19" font-weight="600" fill="{INK}">'
             f'The median dataset published on Kaggle is downloaded eight times</text>')
    o.append(f'<text x="{L}" y="64" font-size="13.5" fill="{INK2}">'
             f'Publishing a specialist corpus here is publishing into a population where 56% never pass ten '
             f'downloads and 69.5%</text>')
    o.append(f'<text x="{L}" y="82" font-size="13.5" fill="{INK2}">'
             f'are never opened in a notebook. Every dataset ever published, n = {n:,}.</text>')

    # Panel A — the distribution
    top, bh, gap = 118, 26, 12
    mx = max(counts.values())
    o.append(f'<text x="{L}" y="{top-12}" font-size="11.5" fill="{MUTED}">lifetime downloads</text>')
    for i, (_, _, lab) in enumerate(BANDS):
        y = top + i * (bh + gap)
        c = counts[lab]
        w = c / mx * (W - L - R - 130)
        o.append(f'<text x="{L-12}" y="{y+bh*0.7:.0f}" font-size="12" fill="{INK2}" text-anchor="end">{lab}</text>')
        o.append(f'<rect x="{L}" y="{y}" width="{w:.1f}" height="{bh}" rx="4" fill="{HILITE}"'
                 f'{" opacity=\"0.45\"" if c/n < 0.05 else ""}/>')
        o.append(f'<text x="{L+w+10:.1f}" y="{y+bh*0.7:.0f}" font-size="12" fill="{INK}">'
                 f'{c/n*100:.1f}%  <tspan fill="{MUTED}">({c:,})</tspan></text>')
    # No median annotation here: the title already states it, and placed on the
    # 1-10 row it collided with that bar's own value label.

    # Panel B — the cohort trend
    by = top + len(BANDS) * (bh + gap) + 54
    bhgt = 132
    # Pre-2021 is NOT comparable: Kaggle auto-created a notebook per dataset
    # until some point in 2020. Among datasets with <=1 download — which cannot
    # have a user-written notebook — 100% of 2017, 87% of 2018 and 89% of 2019
    # still carry one, against 8% of 2021. Plotting those years would show a
    # platform feature ending, not interest declining.
    yrs = [y for y in sorted(cohort) if y >= "2021"]
    px = lambda i: L + i * (W - L - R) / (len(yrs) - 1)
    py = lambda v: by + bhgt - v / 100 * bhgt
    o.append(f'<text x="{L}" y="{by-14}" font-size="11.5" fill="{MUTED}">'
             f'share of each year&#8217;s datasets never opened in a notebook &#183; 2021 onward only</text>')
    for v in (0, 50, 100):
        o.append(f'<line x1="{L}" y1="{py(v):.1f}" x2="{W-R}" y2="{py(v):.1f}" stroke="{GRID}"/>')
        o.append(f'<text x="{L-10}" y="{py(v)+4:.1f}" font-size="11" fill="{MUTED}" text-anchor="end">{v}%</text>')
    pts = " ".join(f"{px(i):.1f},{py(cohort[y][1]/cohort[y][0]*100):.1f}" for i, y in enumerate(yrs))
    o.append(f'<polyline points="{pts}" fill="none" stroke="{HILITE}" stroke-width="2"/>')
    for i, y in enumerate(yrs):
        t, yr_never = cohort[y]        # NOT nk — that is the population counter
        o.append(f'<circle cx="{px(i):.1f}" cy="{py(yr_never/t*100):.1f}" r="3.5" fill="{HILITE}"/>')
        if i % 2 == 0 or i == len(yrs) - 1:
            o.append(f'<text x="{px(i):.1f}" y="{by+bhgt+18:.0f}" font-size="11" fill="{MUTED}" '
                     f'text-anchor="middle">{y}</text>')
    o.append(f'<text x="{L}" y="{by+bhgt+40:.0f}" font-size="11.5" fill="{MUTED}">'
             f'Earlier years are excluded because Kaggle auto-created a notebook per dataset until 2020: among '
             f'datasets with one download or</text>')
    o.append(f'<text x="{L}" y="{by+bhgt+56:.0f}" font-size="11.5" fill="{MUTED}">'
             f'fewer, 100% of 2017 and 89% of 2019 still carry one, against 8% of 2021. Part of what remains is '
             f'recency.</text>')

    o.append(f'<text x="{L}" y="{H-30}" font-size="11.5" fill="{MUTED}">'
             f'Source: Kaggle Meta Kaggle, Datasets.csv, retrieved 2026-09-09. Every dataset ever published.</text>')
    o.append(f'<text x="{L}" y="{H-14}" font-size="11.5" fill="{MUTED}">'
             f'Method and code: github.com/q3dresearch/cookbook &#183; recipes/dataset-demand-shape</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))

    # Record this run. The series accumulates by running, not by remembering to
    # write it down — and Meta Kaggle publishes only current totals, so these
    # rows are the only longitudinal record of them that will exist.
    import csv as _csv, datetime, json as _json
    prov = _json.loads((RECIPE / "provenance.json").read_text())
    row = {
        "run_date": datetime.date.today().isoformat(),
        "method_version": prov["method_version"],
        "population": n,
        "median_downloads": med,
        "share_under_10_downloads": round(sum(1 for x in dl if x <= 10) / n, 4),
        "share_never_in_notebook": round(nk / n, 4),
        "never_revised": None,
    }
    # 2.0.0 changed what is measured, so the old columns do not apply. Old rows
    # stay: a break in the series is a fact about the series, not an error to
    # delete. See VERSIONING.md.
    hist = RECIPE / "history.csv"
    # Key on (date, method_version), not date alone: a method change on the same
    # day is a new observation, not a duplicate. Deduplicating on date silently
    # dropped the 2.0.0 row when this was first used.
    seen = ({(r["run_date"], r["method_version"])
             for r in _csv.DictReader(hist.open(newline=""))} if hist.exists() else set())
    if (row["run_date"], row["method_version"]) not in seen:
        with hist.open("a", newline="") as fh:
            _csv.DictWriter(fh, fieldnames=list(row)).writerow(row)
        print(f"  history.csv += {row['run_date']}")
    else:
        print(f"  history.csv already has {row['run_date']} at method {row['method_version']}")

    print(f"  {OUT.name}  (n={n:,}, median={med})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
