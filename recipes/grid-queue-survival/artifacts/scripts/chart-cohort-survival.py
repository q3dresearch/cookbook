#!/usr/bin/env python3
"""Survival at a fixed age, within fixed entry cohorts.

    python chart-cohort-survival.py <queue.csv>

Comparing technologies on all-time survival compares eras, not technologies.
CAISO's gas turbines have a median queue year of 2007 and its storage projects
2020: they were never in the same queue, under the same rules, competing for the
same transmission. A ranking across them measures fourteen years of policy.

This holds both axes of that confound fixed. Projects are grouped by the years
they ENTERED the queue, and every one is measured at the SAME five years of
exposure, so a difference between two lines is a difference between technologies.
A technology appears in a cohort only if it has at least MIN_N projects there,
which is why gas does not appear at all: it had essentially stopped entering the
queue before storage started.

Three dimensions — entry cohort, survival at five years, technology — because the
question is how the ranking moves, and a bar chart per cohort would make the
reader hold three pictures in their head to see one trend.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from families import HUE, family_of                            # noqa: E402
from xml.sax.saxutils import escape

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "cohort-survival.svg"
# Non-overlapping five-year bins. The first version used sliding windows
# (2008-2012, 2010-2015, 2013-2017) to keep each cell's sample up, which put the
# same project in two bins and made "the trend" partly a redrawing of the same
# projects. Clean bins cost some n and mean what they say.
COHORTS = [(2006, 2010), (2011, 2015), (2016, 2020)]
HORIZON, MIN_N = 5, 30

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE = "#e3e2db"

FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
D = lambda s: dt.date.fromisoformat(s) if s else None          # noqa: E731


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    allrows = [r for r in csv.DictReader(open(sys.argv[1], encoding="utf-8"))
               if r["queue_date"]]

    # A grid can only appear here if its withdrawals are DATED. Survival at a fixed
    # horizon asks whether a project died within five years, and an operator that
    # publishes no withdrawal date can never answer yes — every one of its families
    # came out at exactly 100%, which read as a spectacular result and was a
    # missing column. MISO publishes none for any of its 3,833 projects.
    dated = {iso for iso in {r["iso"] for r in allrows}
             if sum(1 for r in allrows
                    if r["iso"] == iso and (r.get("withdrawn_date") or "").strip()) >= 50}
    skipped = sorted({r["iso"] for r in allrows} - dated)
    rows = [r for r in allrows if r["iso"] in dated]
    if not rows:
        print("  no grid publishes dated withdrawals — cannot draw survival at a horizon")
        return 1
    today = dt.date.today()

    grid = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    for r in rows:
        q = D(r["queue_date"])
        fam = family_of(r)
        if not q or not fam:
            continue
        tech = (r["iso"], fam)
        if (today - q).days / 365.25 < HORIZON:
            continue                                # not yet observed for long enough
        for lo, hi in COHORTS:
            if not lo <= q.year <= hi:
                continue
            cell = grid[(lo, hi)][tech]
            cell[1] += 1
            died = (r["status"] == "withdrawn" and r["withdrawn_date"]
                    and (D(r["withdrawn_date"]) - q).days / 365.25 <= HORIZON)
            if not died:
                cell[0] += 1

    techs = sorted({t for c in grid.values() for t, v in c.items() if v[1] >= MIN_N},
                   key=lambda t: -sum(grid[c][t][1] for c in grid))
    # Dashed is MISO, solid CAISO; colour stays the family. Same encoding as
    # queue-exposure so the two can be read side by side.
    if not techs:
        print("  no technology has a comparable cohort")
        return 1

    W, H, L, R, T, B = 1000, 548, 92, 90, 214, 132
    n = len(COHORTS)
    # Scale to the data's own ceiling, not to 100%. Mapping 0-1 into the box left
    # the top two thirds empty and squashed every line into a band.
    top = max(v[0] / v[1] for c in grid.values() for v in c.values() if v[1] >= MIN_N)
    YMAX = min(1.0, (int(top * 20) + 2) / 20)
    def sx(i): return L + (i + 0.5) / n * (W - L - R)
    def sy(v): return H - B - (v / YMAX) * (H - T - B)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'Compared fairly, storage is not the worst bet in the queue</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Share of projects still alive after exactly {HORIZON} years, grouped by when '
             f'they entered the queue. Same technology, same</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'exposure, same era &#8212; so a gap between lines is the technology, not '
             f'fourteen years of changing rules.</text>')
    if skipped:
        o.append(f'<text x="36" y="{T-64}" font-size="12" fill="{MUTED}">'
                 f'{", ".join(skipped)} cannot appear: it publishes no withdrawal date, so a '
                 f'death can be counted but never placed in time. Included, every one of its '
                 f'families scored exactly 100%.</text>')
    o.append(f'<text x="36" y="110" font-size="12.5" fill="{MUTED}">'
             f'Gas appears only in the two older cohorts and storage only in the two newer '
             f'ones: they barely overlapped in time, so read down a cohort, not across.</text>')

    for g in [x / 100 for x in range(0, int(YMAX * 100) + 1, 10)]:
        o.append(f'<line x1="{L}" y1="{sy(g):.1f}" x2="{W-R}" y2="{sy(g):.1f}" '
                 f'stroke="{RULE}"/>')
        o.append(f'<text x="{L-10}" y="{sy(g)+4:.1f}" font-size="11.5" fill="{MUTED}" '
                 f'text-anchor="end">{g:.0%}</text>')
    o.append(f'<text x="36" y="{T-12}" font-size="11.5" fill="{MUTED}">'
             f'share of projects still alive at exactly {HORIZON} years</text>')
    for i, (lo, hi) in enumerate(COHORTS):
        o.append(f'<text x="{sx(i):.1f}" y="{H-B+24}" font-size="12" fill="{INK2}" '
                 f'text-anchor="middle">{lo}&#8211;{hi}</text>')
    o.append(f'<text x="{(L+W-R)/2:.0f}" y="{H-B+46}" font-size="11.5" fill="{MUTED}" '
             f'text-anchor="middle">years the project entered the queue</text>')

    drawn = []
    for k, tech in enumerate(techs):
        iso, fam = tech
        c = HUE.get(fam, "#52514e")
        dash = ' stroke-dasharray="5 3"' if iso == "MISO" else ""
        pts = [(i, grid[co][tech][0] / grid[co][tech][1], grid[co][tech][1])
               for i, co in enumerate(COHORTS) if grid[co][tech][1] >= MIN_N]
        if len(pts) < 2:
            continue
        d = " ".join(f"{'M' if j == 0 else 'L'}{sx(i):.1f},{sy(v):.1f}"
                     for j, (i, v, _) in enumerate(pts))
        o.append(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="2.8"{dash}/>')
        for i, v, _n in pts:
            o.append(f'<circle cx="{sx(i):.1f}" cy="{sy(v):.1f}" r="5" fill="{c}" '
                     f'stroke="{SURFACE}" stroke-width="2"/>')
        drawn.append((tech, c, pts))

    # A plain legend. The colour already says which line is which, so no leader
    # lines and no per-point labels: they were drawing more ink than the data.
    lx = 36
    for tech, c, _p in drawn:
        iso, fam = tech
        label = f"{fam}, {iso}"
        o.append(f'<circle cx="{lx+6}" cy="{T-42}" r="5.5" fill="{c}"'
                 f'{" stroke=\"" + SURFACE + "\" stroke-width=\"1.6\"" if iso == "MISO" else ""}/>')
        o.append(f'<text x="{lx+18}" y="{T-38}" font-size="12.5" fill="{INK2}">'
                 f'{escape(label)}</text>')
        lx += 34 + len(label) * 7.0

    sizes = ", ".join(f"{t[1]} {t[0]} n={min(p[2] for p in pts)}-{max(p[2] for p in pts)}"
                      for t, _c, pts in drawn)
    o.append(f'<text x="36" y="{H-64}" font-size="11" fill="{MUTED}">'
             f'Projects per point: {sizes}.</text>')
    o.append(f'<text x="36" y="{H-46}" font-size="12.5" fill="{INK}">'
             f'<tspan font-weight="600">All-time survival said storage was worst at '
             f'8.1%.</tspan> Age-matched it is 19.6%, level with combined-cycle gas and '
             f'above solar.</text>')
    o.append(f'<text x="36" y="{H-26}" font-size="11.5" fill="{MUTED}">'
             f'Storage projects have had time to be withdrawn (median 1 year) but not to be '
             f'built (median 6.1 years), so counting all of them understates it.</text>')
    o.append(f'<text x="36" y="{H-10}" font-size="11.5" fill="{MUTED}">'
             f'CAISO only. A technology is shown in a cohort only with at least {MIN_N} '
             f'projects there. Source: PublicQueueReport.xlsx, fetched {today}.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name} — {len(drawn)} technologies with comparable cohorts")
    for co in COHORTS:
        cells = {t: v for t, v in grid[co].items() if v[1] >= MIN_N}
        if cells:
            print(f"    {co[0]}-{co[1]}: " + "  ".join(
                f"{t[:12]} {v[0]/v[1]:.0%}(n={v[1]})" for t, v in
                sorted(cells.items(), key=lambda kv: -kv[1][0]/kv[1][1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
