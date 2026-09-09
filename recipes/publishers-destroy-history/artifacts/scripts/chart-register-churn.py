#!/usr/bin/env python3
"""Two different things happen to records in this register, and they look alike.

    python chart-register-churn.py

Sweden's harvest-notification register holds ~128,000 records and the total
barely moves between captures. Underneath it, 380 notifications vanished in two
days — and splitting them by case year separates two phenomena completely:

    318 returned the next day    every one a 2025 case    service instability
     62 never returned           61 of them 2021 cases    expiry

The separation is exact; there is no overlap. The permanent departures are the
earliest-filed cases of 2021, aging out five years on, which is the retention
behaviour this archive was built to catch. The returners are a service that
answers differently depending on the day.

A WRONG TURN WORTH RECORDING. The permanent departures cluster at the front of
their partitions — a 3x excess in the first decile — and that was read as a
boundary bug in our own query, a `>=` versus `>` error. It is not. Partitions
are county x case-year x date-range with correct half-open intervals, they are
ordered by case number, and the front of a partition is simply the oldest case
in that year. The anomaly was the finding.
"""
from __future__ import annotations

import collections
import csv
import glob
import gzip
import json
import os
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
FLEET = RECIPE / "artifacts" / "data" / "wss-forest-harvest"
ARCHIVE = "https://github.com/q3dresearch/wss-forest-harvest.git"
OUT = RECIPE / "artifacts" / "charts" / "register-churn.svg"
SRC = "skogsstyrelsen.harvest.notified"

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, HILITE, DIM = "#e1e0d9", "#c3c2b7", "#2361b0", "#b9c9e2"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def load(p):
    with open(p, "rb") as fh:
        head = fh.read(2)
    op = gzip.open if head == b"\x1f\x8b" else open
    with op(p, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def fetch() -> None:
    """The evidence lives in the archive, so fetch the archive.

    This recipe reads captured bytes rather than a published API, which means
    reproducing it needs the archive that holds them. It is public and small,
    so a shallow clone is the whole dependency — and the clone is itself the
    demonstration: a finding here resolves to specific commits there.
    """
    if FLEET.exists():
        return
    FLEET.parent.mkdir(parents=True, exist_ok=True)
    print(f"  cloning {ARCHIVE} (shallow) …")
    import subprocess
    subprocess.run(["git", "clone", "--depth", "50", "--quiet", ARCHIVE, str(FLEET)], check=True)


def read():
    fetch()
    rows = []
    for f in glob.glob(str(FLEET / "manifest" / SRC / "*.csv")):
        rows += list(csv.DictReader(open(f, newline="")))
    day = collections.defaultdict(dict)
    for r in rows:
        ref = r.get("raw_ref") or ""
        if not ref.startswith("raw/"):
            continue          # quarantined captures are fetch anomalies, not behaviour
        p = FLEET / ref
        if not p.exists():
            continue
        try:
            for f_ in load(p)["features"]:
                a = f_["attributes"]
                day[r["fetched_at"][:10]][a["Beteckn"]] = a.get("ArendeAr")
        except Exception:
            continue
    return day


def main() -> int:
    day = read()
    ds = sorted(day)
    d4, d6, d7 = (set(day[d]) for d in ds[:3])
    gone = d4 - d6
    back = sorted(gone & d7)
    perm = sorted(gone - d7)
    yb = collections.Counter(day[ds[0]][k] for k in back)
    yp = collections.Counter(day[ds[0]][k] for k in perm)

    W, H, L, R, T = 940, 460, 130, 42, 132
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'>", f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="{L-70}" y="40" font-size="19" font-weight="600" fill="{INK}">'
             f'A register that both forgets and flickers, and the two look identical</text>')
    o.append(f'<text x="{L-70}" y="64" font-size="13.5" fill="{INK2}">'
             f'{len(gone)} notifications vanished from Sweden&#8217;s harvest register in two days. Splitting them by '
             f'case year separates</text>')
    o.append(f'<text x="{L-70}" y="82" font-size="13.5" fill="{INK2}">'
             f'two phenomena exactly, with no overlap &#8212; and only one of them is the record being destroyed.</text>')

    tot = len(gone)
    bw = W - L - R
    y0 = T
    o.append(f'<text x="{L-70}" y="{y0-14}" font-size="11.5" fill="{MUTED}">'
             f'the {tot} that disappeared between 04 and 06 September</text>')
    wb = len(back) / tot * bw
    o.append(f'<rect x="{L-70}" y="{y0}" width="{wb:.1f}" height="34" rx="4" fill="{DIM}"/>')
    o.append(f'<rect x="{L-70+wb:.1f}" y="{y0}" width="{bw-wb:.1f}" height="34" rx="4" fill="{HILITE}"/>')
    o.append(f'<text x="{L-70+wb/2:.0f}" y="{y0+22:.0f}" font-size="13" fill="{INK}" text-anchor="middle">'
             f'{len(back)} returned the next day</text>')
    o.append(f'<text x="{L-70+wb+(bw-wb)/2:.0f}" y="{y0+22:.0f}" font-size="13" fill="{SURFACE}" '
             f'text-anchor="middle">{len(perm)} did not</text>')

    for j, (lab, cnt, col, note) in enumerate((
            ("returned", yb, DIM, "the service answering differently, not the record changing"),
            ("permanently gone", yp, HILITE, "the earliest-filed cases of their year, five years on"))):
        yy = y0 + 74 + j * 92
        o.append(f'<text x="{L-70}" y="{yy:.0f}" font-size="13" font-weight="600" fill="{INK}">'
                 f'{sum(cnt.values())} {lab}</text>')
        o.append(f'<text x="{L-70}" y="{yy+20:.0f}" font-size="12.5" fill="{INK2}">{note}</text>')
        x = L - 70
        for y, n in sorted(cnt.items(), key=str):
            w = n / sum(cnt.values()) * (bw * 0.72)
            o.append(f'<rect x="{x:.1f}" y="{yy+32}" width="{max(w-2,1):.1f}" height="20" rx="3" fill="{col}"/>')
            if w > 60:
                o.append(f'<text x="{x+w/2:.1f}" y="{yy+46:.0f}" font-size="11.5" '
                         f'fill="{SURFACE if col==HILITE else INK2}" text-anchor="middle">'
                         f'{y} &#183; {n}</text>')
            else:
                o.append(f'<text x="{x+w+6:.1f}" y="{yy+46:.0f}" font-size="11.5" fill="{INK2}">{y} &#183; {n}</text>')
            x += w
    o.append(f'<text x="{L-70}" y="{H-46}" font-size="11.5" fill="{MUTED}">'
             f'Every returner is a 2025 case; every permanent departure but one is 2021. The split is exact.</text>')
    o.append(f'<text x="{L-70}" y="{H-28}" font-size="11.5" fill="{MUTED}">'
             f'Source: wss-forest-harvest, skogsstyrelsen.harvest.notified, 226 partitions, captured '
             f'{ds[0]} to {ds[2]}. Diffed by case number.</text>')
    o.append(f'<text x="{L-70}" y="{H-12}" font-size="11.5" fill="{MUTED}">'
             f'Method and code: q3dresearch &#183; recipes/publishers-destroy-history</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name}  ({len(back)} returned, {len(perm)} permanent)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
