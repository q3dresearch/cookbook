#!/usr/bin/env python3
"""How much production capacity is waiting on a decision, against how much exists.

    python chart-biomass-at-risk.py <applications.csv>

Applications state a desired maximum allowed biomass — standing capacity, not
annual production. Comparing what is pending against what has ever been granted
turns a queue length into a capacity figure: new sea sites have 152,957 tonnes
waiting against 41,939 ever approved, more than three times as much held as
released.

Bars are stacked because the three states are exclusive parts of one total: every
tonne applied for is granted, refused, or still waiting. The interesting quantity
is the share of each family's total that has never been decided.

**Every figure is a floor.** Biomass is stated on a minority of applications — 49
of 71 denied and 71 of 446 granted — so the totals count only the applications
that filled the field in. They are not a sample of the rest; an applicant who
omits a biomass figure may be systematically different, and nothing here tests
that.
"""
from __future__ import annotations

import collections
import csv
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from families import adds_capacity, family_of                  # noqa: E402

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "biomass-at-risk.svg"
MIN_T = 20000

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE, PEND, GRANT, DENY = "#e3e2db", "#b5651d", "#3f7d3a", "#a8324a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))

    agg = collections.defaultdict(lambda: collections.Counter())
    stated = collections.Counter()
    total = collections.Counter()
    for r in rows:
        fam = family_of(r["application_type"])
        if not fam:
            continue
        total[fam] += 1
        try:
            b = float(r["biomass_tonnes"])
        except (TypeError, ValueError):
            continue
        if b <= 0:
            continue
        stated[fam] += 1
        if r["layer"] == "pending":
            agg[fam]["pending"] += b
        elif r["result"] == "GRANTED":
            agg[fam]["granted"] += b
        elif r["result"] == "DENIED":
            agg[fam]["denied"] += b

    fams = [(f, c) for f, c in agg.items() if sum(c.values()) >= MIN_T]
    if not fams:
        print("  nothing to plot")
        return 1
    fams.sort(key=lambda kv: -kv[1]["pending"] / max(sum(kv[1].values()), 1))

    W, L, R, T, RH = 1030, 250, 226, 208, 62
    H = T + len(fams) * RH + 178
    mx = max(sum(c.values()) for _, c in fams)

    def sw(v):
        return v / mx * (W - L - R)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'More new capacity is waiting than has ever been approved</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Maximum allowed biomass applied for, by what happened to the application. '
             f'Standing capacity, not annual production.</text>')
    for i, (lab, col) in enumerate((("still waiting", PEND), ("granted", GRANT),
                                    ("refused", DENY))):
        x = 36 + i * 168
        o.append(f'<rect x="{x}" y="{88}" width="12" height="12" rx="2.5" fill="{col}"/>')
        o.append(f'<text x="{x+18}" y="{98}" font-size="12" fill="{INK2}">{lab}</text>')

    for i, (fam, c) in enumerate(fams):
        y = T + i * RH
        tot = sum(c.values())
        o.append(f'<text x="{L-16}" y="{y+4}" font-size="13" fill="{INK}" '
                 f'text-anchor="end">{escape(fam)}</text>')
        o.append(f'<text x="{L-16}" y="{y+20}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="end">{"new capacity" if adds_capacity(fam) else "modification"}'
                 f' &#183; {stated[fam]} of {total[fam]} state a figure</text>')
        x = float(L)
        for key, col in (("pending", PEND), ("granted", GRANT), ("denied", DENY)):
            w = sw(c[key])
            if w <= 0:
                continue
            o.append(f'<rect x="{x:.1f}" y="{y-11}" width="{max(w-1.5, 1):.1f}" height="24" '
                     f'fill="{col}"/>')
            if w > 54:
                o.append(f'<text x="{x+w/2:.1f}" y="{y+5}" font-size="11.5" fill="#ffffff" '
                         f'text-anchor="middle">{c[key]/1000:,.0f}k</text>')
            x += w
        o.append(f'<text x="{W-R+14}" y="{y+4}" font-size="12" fill="{PEND}" '
                 f'font-weight="600">{c["pending"]/max(tot,1):.0%} undecided</text>')
        if c["granted"] > 0:
            o.append(f'<text x="{W-R+14}" y="{y+20}" font-size="11" fill="{MUTED}">'
                     f'{c["pending"]/c["granted"]:.1f}&#215; what was granted</text>')

    yb = T + len(fams) * RH + 26
    newp = sum(c["pending"] for f, c in fams if adds_capacity(f))
    allp = sum(c["pending"] for _, c in fams)
    o.append(f'<line x1="36" y1="{yb-18}" x2="{W-36}" y2="{yb-18}" stroke="{RULE}"/>')
    o.append(f'<text x="36" y="{yb+4}" font-size="13" fill="{INK}">'
             f'<tspan font-weight="600">{newp:,.0f} of the {allp:,.0f} tonnes awaiting a '
             f'decision would be new capacity &#8212; {newp/allp:.0%} of the '
             f'pile.</tspan></text>')
    o.append(f'<text x="36" y="{yb+26}" font-size="12.5" fill="{INK2}">'
             f'Norway caps salmon output by licensed biomass, so a queue holding more new '
             f'capacity than it has released is the binding constraint on growth.</text>')
    o.append(f'<text x="36" y="{yb+54}" font-size="11.5" fill="{MUTED}">'
             f'Every figure is a floor: biomass is stated on a minority of applications and '
             f'the totals count only those. Whether applicants who omit it differ '
             f'systematically is untested.</text>')
    o.append(f'<text x="36" y="{yb+72}" font-size="11.5" fill="{MUTED}">'
             f'Source: Fiskeridirektoratet Akvakultursøknader, layers 0 and 4. Families under '
             f'{MIN_T:,} tonnes omitted.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name} — {len(fams)} families")
    for fam, c in fams:
        t = sum(c.values())
        print(f"    {fam:<22}{c['pending']/1000:>8,.0f}k pending  {c['granted']/1000:>8,.0f}k "
              f"granted  {c['pending']/max(t,1):>5.0%} undecided")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
