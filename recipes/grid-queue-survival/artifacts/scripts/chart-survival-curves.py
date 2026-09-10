#!/usr/bin/env python3
"""How long a project survives the queue, and how long the survivors take.

    python chart-survival-curves.py <queue.csv>

Kaplan-Meier curves: for each technology, the share of projects not yet withdrawn
after N years in the queue. Three dimensions — time, surviving share, technology —
where a bar chart of "average time to withdrawal" would spend one and hide the
shape, which is the whole point. Most of the dying happens early.

Censoring is done properly, because it changes the answer at exactly the durations
worth reading. A project that was BUILT left the queue alive at its actual on-line
date; a project still ACTIVE has simply not finished yet. Both are censored at
those times rather than counted as survivors forever, which would flatten every
curve upward at the right-hand end where the samples are thinnest.

CAISO only, and not by choice. MISO publishes an application status but no
withdrawal date for any of its 3,833 projects, so it can say how many died and
never when. There is no version of this chart with a Midwest line on it; drawing
one from queue dates alone would invent the result.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from families import HUE, family_of                            # noqa: E402
from xml.sax.saxutils import escape

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "survival-curves.svg"
MIN_N, YEARS = 60, 12
# A curve stops where its own cohort thins, not at a shared horizon. Storage is a
# recent technology: 35 of its projects are twelve years old against 594
# photovoltaic ones, so its tail was a handful of unusual early entrants drawn
# level with everyone else's mature sample. A floor of 5 let that through.
MIN_AT_RISK = 25

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE = "#e3e2db"
# Colour comes from families.py so a family is the same colour on every chart.
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
D = lambda s: dt.date.fromisoformat(s) if s else None          # noqa: E731


def km(records, horizon):
    """Kaplan-Meier survival at yearly steps. records = [(years, died_bool)]."""
    out, surv = [(0.0, 1.0)], 1.0
    for t in range(1, horizon + 1):
        at_risk = sum(1 for y, _ in records if y >= t - 1)
        died = sum(1 for y, d in records if d and t - 1 <= y < t)
        if at_risk >= MIN_AT_RISK:
            surv *= (1 - died / at_risk)
            out.append((float(t), surv))
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rows = [r for r in csv.DictReader(open(sys.argv[1], encoding="utf-8"))
            if r["iso"] == "CAISO" and r["queue_date"]]
    today = dt.date.today()

    per = collections.defaultdict(list)
    build_years = collections.defaultdict(list)
    for r in rows:
        q = D(r["queue_date"])
        tech = family_of(r)
        if not q or not tech:
            continue
        if r["status"] == "withdrawn" and r["withdrawn_date"]:
            per[tech].append(((D(r["withdrawn_date"]) - q).days / 365.25, True))
        elif r["status"] == "built" and r["online_date"]:
            y = (D(r["online_date"]) - q).days / 365.25
            per[tech].append((y, False))
            build_years[tech].append(y)
        elif r["status"] == "active":
            per[tech].append(((today - q).days / 365.25, False))

    series = [(t, v) for t, v in per.items() if len(v) >= MIN_N]
    series.sort(key=lambda kv: -len(kv[1]))
    series = series[:6]
    if not series:
        print("  not enough dated projects")
        return 1

    W, H, L, R, T, B = 1000, 618, 84, 268, 178, 122
    def sx(y): return L + y / YEARS * (W - L - R)
    def sy(s): return H - B - s * (H - T - B)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'The queue kills fast and builds slow</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Share of California projects not yet withdrawn, by years since they '
             f'joined the queue. Projects that were built are censored at</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'the date they came online, and active ones at today &#8212; they left '
             f'alive or have not finished, and neither is a death.</text>')

    for g in range(0, YEARS + 1, 2):
        o.append(f'<line x1="{sx(g):.1f}" y1="{T}" x2="{sx(g):.1f}" y2="{H-B}" '
                 f'stroke="{RULE}"/>')
        o.append(f'<text x="{sx(g):.1f}" y="{H-B+21}" font-size="11.5" fill="{MUTED}" '
                 f'text-anchor="middle">{g}y</text>')
    for g in (0, 0.25, 0.5, 0.75, 1.0):
        o.append(f'<line x1="{L}" y1="{sy(g):.1f}" x2="{W-R}" y2="{sy(g):.1f}" '
                 f'stroke="{RULE}"/>')
        o.append(f'<text x="{L-10}" y="{sy(g)+4:.1f}" font-size="11.5" fill="{MUTED}" '
                 f'text-anchor="end">{g:.0%}</text>')
    o.append(f'<text x="36" y="{T-14}" font-size="11.5" fill="{MUTED}">'
             f'share still in the queue, not withdrawn</text>')
    o.append(f'<text x="{(L+W-R)/2:.0f}" y="{H-B+44}" font-size="11.5" fill="{MUTED}" '
             f'text-anchor="middle">years since joining the queue</text>')

    ends = []
    for i, (tech, recs) in enumerate(series):
        c = HUE.get(tech, "#52514e")
        pts = km(recs, YEARS)
        d = " ".join(f"{'M' if k == 0 else 'L'}{sx(x):.1f},{sy(s):.1f}"
                     for k, (x, s) in enumerate(pts))
        o.append(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="2.6" '
                 f'stroke-linejoin="round"/>')
        ends.append((pts[-1][1], tech, c, len(recs), pts[-1][0]))

    ends.sort(reverse=True)
    for i, (s_, tech, c, n, x_) in enumerate(ends):
        y = T + 10 + i * 40
        o.append(f'<line x1="{sx(x_):.1f}" y1="{sy(s_):.1f}" x2="{W-R+10}" y2="{y-4:.1f}" '
                 f'stroke="{c}" stroke-width="0.8" stroke-dasharray="2 2"/>')
        o.append(f'<text x="{W-R+16}" y="{y}" font-size="12.5" font-weight="600" fill="{c}">'
                 f'{escape(tech)[:20]}</text>')
        bl = build_years.get(tech, [])
        extra = (f" &#183; built in {statistics.median(bl):.1f}y" if len(bl) >= 8 else "")
        o.append(f'<text x="{W-R+16}" y="{y+16}" font-size="11" fill="{MUTED}">'
                 f'{s_:.0%} alive at {x_:.0f}y &#183; n={n:,}{extra}</text>')

    allb = [y for v in build_years.values() for y in v]
    alld = [y for v in per.values() for y, d in v if d]
    if allb and alld:
        o.append(f'<text x="36" y="{H-46}" font-size="13" fill="{INK}">'
                 f'<tspan font-weight="600">Median {statistics.median(alld):.1f} year to a '
                 f'withdrawal, {statistics.median(allb):.1f} years to an energisation.</tspan> '
                 f'Survive the first two years and the odds change entirely.</text>')
    o.append(f'<text x="36" y="{H-26}" font-size="11.5" fill="{MUTED}">'
             f'CAISO only: MISO publishes an application status but no withdrawal date, so '
             f'it can say how many died and not when. Technologies with fewer than '
             f'{MIN_N} dated projects are omitted.</text>')
    o.append(f'<text x="36" y="{H-10}" font-size="11.5" fill="{MUTED}">'
             f'Source: CAISO PublicQueueReport.xlsx, fetched {today}. Curve stops where '
             f'fewer than {MIN_AT_RISK} projects of that technology remain at '
             f'risk, so a line ending early means its cohort is young, not that it '
             f'stopped dying.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name} — {len(series)} technologies")
    for s_, tech, c, n, x_ in ends:
        print(f"    {tech[:22]:<24} {s_:>6.0%} alive at {x_:.0f}y   n={n:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
