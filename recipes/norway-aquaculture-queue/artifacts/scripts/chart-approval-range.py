#!/usr/bin/env python3
"""What share of applications are granted — as a range, because a point is wrong.

    python chart-approval-range.py <applications.csv>

Three numbers per family, and the distance between them is the finding:

  reported   granted / (granted + denied). This is what a decided-only reading
             gives, and what the previous version of this recipe published.
  + withdrawn  counts an application the applicant pulled before any decision as
             not granted. 80 of 599 concluded applications were withdrawn and
             were being dropped entirely.
  floor      if every still-pending application were refused.

The truth is not the midpoint. Refusals take a median of 359 days against 129 for
grants, so the pending pile is disproportionately made of cases heading for
refusal — which means the real figure sits nearer the floor than the reported
number, and the reported number is a ceiling rather than an estimate.

Bar length is the total asked for, so a wide range on a short bar is a small
category and not a scandal.
"""
from __future__ import annotations

import collections
import csv
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from families import family_of                                 # noqa: E402

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "approval-range.svg"
MIN_N = 25

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE, HI, MID, LO = "#e3e2db", "#b9c9e2", "#2361b0", "#a8324a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))

    agg = collections.defaultdict(collections.Counter)
    for r in rows:
        fam = family_of(r["application_type"])
        if not fam:
            continue
        if r["layer"] == "pending":
            agg[fam]["pending"] += 1
        elif r["status"] == "WITHDRAWN":
            agg[fam]["withdrawn"] += 1
        elif r["result"]:
            agg[fam][r["result"].lower()] += 1

    fams = []
    for fam, c in agg.items():
        g, d, w, p = c["granted"], c["denied"], c["withdrawn"], c["pending"]
        n = g + d + w + p
        if n < MIN_N or g + d == 0:
            continue
        fams.append({"fam": fam, "n": n, "g": g, "d": d, "w": w, "p": p,
                     "rep": g / (g + d), "inc": g / (g + d + w), "floor": g / n})
    if not fams:
        print("  nothing to plot")
        return 1
    fams.sort(key=lambda f: f["rep"])

    W, L, R, T, RH = 1000, 226, 220, 208, 54
    H = T + len(fams) * RH + 172

    def sx(v):
        return L + v * (W - L - R)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'The approval rate is a range, and the published number is its ceiling</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Each bar runs from the floor &#8212; every pending application refused &#8212; '
             f'to the figure a decided-only reading gives.</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'Refusals take a median of 359 days against 129 for grants, so the pending pile '
             f'skews toward refusal and the truth sits low in each bar.</text>')

    o.append(f'<circle cx="42" cy="118" r="6" fill="{LO}"/>')
    o.append(f'<text x="54" y="122" font-size="12" fill="{INK2}">floor: pending all refused</text>')
    o.append(f'<circle cx="266" cy="118" r="6" fill="{MID}"/>')
    o.append(f'<text x="278" y="122" font-size="12" fill="{INK2}">counting withdrawals as '
             f'not granted</text>')
    o.append(f'<circle cx="596" cy="118" r="6" fill="{HI}" stroke="{MUTED}" stroke-width="1.2"/>')
    o.append(f'<text x="608" y="122" font-size="12" fill="{INK2}">as previously published</text>')

    for g in (0, 0.25, 0.5, 0.75, 1.0):
        o.append(f'<line x1="{sx(g):.1f}" y1="{T-26}" x2="{sx(g):.1f}" '
                 f'y2="{T+len(fams)*RH-28}" stroke="{RULE}"/>')
        o.append(f'<text x="{sx(g):.1f}" y="{T+len(fams)*RH-8}" font-size="11.5" '
                 f'fill="{MUTED}" text-anchor="middle">{g:.0%}</text>')

    for i, f in enumerate(fams):
        y = T + i * RH
        o.append(f'<text x="{L-16}" y="{y+2}" font-size="13" fill="{INK}" '
                 f'text-anchor="end">{escape(f["fam"])}</text>')
        o.append(f'<text x="{L-16}" y="{y+18}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="end">{f["n"]} asked &#183; {f["p"]} still pending</text>')
        o.append(f'<line x1="{sx(f["floor"]):.1f}" y1="{y}" x2="{sx(f["rep"]):.1f}" y2="{y}" '
                 f'stroke="{MUTED}" stroke-width="2" stroke-opacity="0.5"/>')
        o.append(f'<circle cx="{sx(f["rep"]):.1f}" cy="{y}" r="6.5" fill="{HI}" '
                 f'stroke="{MUTED}" stroke-width="1.4"/>')
        o.append(f'<circle cx="{sx(f["inc"]):.1f}" cy="{y}" r="6.5" fill="{MID}"/>')
        o.append(f'<circle cx="{sx(f["floor"]):.1f}" cy="{y}" r="6.5" fill="{LO}"/>')
        o.append(f'<text x="{W-R+14}" y="{y+2}" font-size="12" fill="{INK}">'
                 f'{f["floor"]:.0%} &#8211; {f["rep"]:.0%}</text>')
        o.append(f'<text x="{W-R+14}" y="{y+18}" font-size="11" fill="{MUTED}">'
                 f'{f["g"]} granted, {f["d"]} denied, {f["w"]} withdrawn</text>')

    yb = T + len(fams) * RH + 22
    ns = next((f for f in fams if f["fam"] == "New sea site"), None)
    lb = next((f for f in fams if f["fam"] == "Land-based"), None)
    o.append(f'<line x1="36" y1="{yb-16}" x2="{W-36}" y2="{yb-16}" stroke="{RULE}"/>')
    if ns and lb:
        o.append(f'<text x="36" y="{yb+6}" font-size="13" fill="{INK}">'
                 f'<tspan font-weight="600">New sea space is {ns["floor"]:.0%}&#8211;'
                 f'{ns["rep"]:.0%}; going onto land is {lb["floor"]:.0%}&#8211;'
                 f'{lb["rep"]:.0%}.</tspan> The gap holds at every reading, but neither is '
                 f'the single number it was reported as.</text>')
    o.append(f'<text x="36" y="{yb+28}" font-size="12.5" fill="{INK2}">'
             f'Land-based was previously called &#8220;close to automatic&#8221; at 94%. '
             f'Counting the applicants who withdrew, it is 70%.</text>')
    o.append(f'<text x="36" y="{yb+56}" font-size="11.5" fill="{MUTED}">'
             f'Families with fewer than {MIN_N} applications are omitted. Source: '
             f'Fiskeridirektoratet Akvakultursøknader, layers 0 and 4, fetched '
             f'{__import__("datetime").date.today()}.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name} — {len(fams)} families")
    for f in fams:
        print(f"    {f['fam']:<26}{f['floor']:>6.0%} - {f['rep']:>4.0%}   "
              f"(+wd {f['inc']:.0%})  n={f['n']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
