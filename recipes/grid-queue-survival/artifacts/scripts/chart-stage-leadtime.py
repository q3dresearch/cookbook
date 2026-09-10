#!/usr/bin/env python3
"""Where the time goes, and therefore where the bottleneck is.

    python chart-stage-leadtime.py <queue.csv>

`death-stage` says how many projects stop at each point. It cannot say whether
stopping there was quick or slow, and those imply opposite remedies: a stage that
kills half the queue inside a year is a volume filter, while one that holds
projects for four years is a capacity constraint.

So: the distribution of time-in-queue, split by the furthest study a project
reached. Two dimensions plus a spread, because a median alone would hide that the
late stages are not merely slower but far more variable — the tenth of projects
that die holding a signed agreement have been waiting nearly eleven years.

CAISO publishes study STATUSES, not study DATES, so this is time from queue entry
to outcome for projects that stopped at a given stage. It is not the duration of
that stage. The jump between two adjacent rows is the closest thing to a per-stage
cost this data supports, and it is an upper bound on it.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import statistics
import sys
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "stage-leadtime.svg"
MIN_N = 20

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE, DEAD, BUILT = "#e3e2db", "#2361b0", "#3f7d3a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
STAGES = ["never studied", "in feasibility", "through system impact",
          "through facilities study", "signed an agreement"]
D = lambda s: dt.date.fromisoformat(s) if s else None          # noqa: E731


def stage_of(r) -> int:
    started = (r["feasibility"] or "").strip().lower() in (
        "complete", "executed", "waived", "in progress", "re-study")
    if (r["ia_status"] or "").strip():
        return 4
    if (r["facilities"] or "").strip().lower() == "complete":
        return 3
    if (r["sys_impact"] or "").strip().lower() == "complete":
        return 2
    return 1 if started else 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rows = [r for r in csv.DictReader(open(sys.argv[1], encoding="utf-8"))
            if r["iso"] == "CAISO"]

    dead = collections.defaultdict(list)
    built = collections.defaultdict(list)
    for r in rows:
        q = D(r["queue_date"])
        if not q:
            continue
        if r["status"] == "withdrawn" and r["withdrawn_date"]:
            dead[stage_of(r)].append((D(r["withdrawn_date"]) - q).days / 365.25)
        elif r["status"] == "built" and r["online_date"]:
            built[stage_of(r)].append((D(r["online_date"]) - q).days / 365.25)

    def band(v):
        v = sorted(v)
        return (v[len(v) // 4], statistics.median(v), v[3 * len(v) // 4],
                v[int(0.9 * len(v))], len(v))

    W, L, R, T, RH = 1000, 240, 236, 200, 62
    H = T + len(STAGES) * RH + 172
    mx = max(band(v)[3] for v in dead.values() if len(v) >= MIN_N) * 1.06

    def sx(y):
        return L + y / mx * (W - L - R)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'Everything before the facilities study resolves in a year. After it, years.</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Time from joining the queue to the outcome, by the furthest study a project '
             f'reached. Bar spans the middle half,</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'the line runs to the 90th percentile, the dot is the median.</text>')
    o.append(f'<circle cx="42" cy="118" r="6" fill="{DEAD}"/>')
    o.append(f'<text x="54" y="122" font-size="12.5" font-weight="600" fill="{DEAD}">'
             f'withdrawn</text>')
    o.append(f'<circle cx="164" cy="118" r="6" fill="{BUILT}"/>')
    o.append(f'<text x="176" y="122" font-size="12.5" font-weight="600" fill="{BUILT}">'
             f'built and energised</text>')

    for g in range(0, int(mx) + 1, 2):
        o.append(f'<line x1="{sx(g):.1f}" y1="{T-28}" x2="{sx(g):.1f}" '
                 f'y2="{T+len(STAGES)*RH-34}" stroke="{RULE}"/>')
        o.append(f'<text x="{sx(g):.1f}" y="{T+len(STAGES)*RH-14}" font-size="11.5" '
                 f'fill="{MUTED}" text-anchor="middle">{g}y</text>')

    prev_med = None
    for i, name in enumerate(STAGES):
        y = T + i * RH
        o.append(f'<text x="{L-18}" y="{y+5}" font-size="13" fill="{INK}" '
                 f'text-anchor="end">{name}</text>')
        for vals, colour, dy in ((dead.get(i, []), DEAD, -8), (built.get(i, []), BUILT, 10)):
            if len(vals) < MIN_N:
                continue
            q1, med, q3, p90, n = band(vals)
            yy = y + (dy if built.get(i) and len(built[i]) >= MIN_N else 0)
            o.append(f'<line x1="{sx(q1):.1f}" y1="{yy}" x2="{sx(p90):.1f}" y2="{yy}" '
                     f'stroke="{colour}" stroke-width="1.4" stroke-opacity="0.55"/>')
            o.append(f'<rect x="{sx(q1):.1f}" y="{yy-6}" width="{sx(q3)-sx(q1):.1f}" '
                     f'height="12" rx="2" fill="{colour}" fill-opacity="0.35"/>')
            o.append(f'<circle cx="{sx(med):.1f}" cy="{yy}" r="5.5" fill="{colour}" '
                     f'stroke="{SURFACE}" stroke-width="1.6"/>')
            o.append(f'<text x="{W-R+14}" y="{yy+4}" font-size="12" fill="{colour}">'
                     f'{med:.1f}y median &#183; n={n:,}</text>')
        if i == 3 and prev_med:
            o.append(f'<text x="{L-18}" y="{y+21}" font-size="11" fill="{MUTED}" '
                     f'text-anchor="end">{band(dead[3])[1]/prev_med:.1f}&#215; the row '
                     f'above</text>')
        if dead.get(i) and len(dead[i]) >= MIN_N:
            prev_med = band(dead[i])[1]

    yb = T + len(STAGES) * RH + 24
    o.append(f'<line x1="36" y1="{yb-18}" x2="{W-36}" y2="{yb-18}" stroke="{RULE}"/>')
    d4, b4 = band(dead[4]), band(built[4])
    o.append(f'<text x="36" y="{yb+4}" font-size="13" fill="{INK}">'
             f'<tspan font-weight="600">A project that dies holding a signed agreement has '
             f'waited {d4[1]:.1f} years. One that gets built waited {b4[1]:.1f}.</tspan> '
             f'Almost the same investment, no asset.</text>')
    o.append(f'<text x="36" y="{yb+26}" font-size="12.5" fill="{INK2}">'
             f'Two different bottlenecks. Intake is high-volume and fast: half the queue leaves '
             f'inside a year having consumed no study at all.</text>')
    o.append(f'<text x="36" y="{yb+45}" font-size="12.5" fill="{INK2}">'
             f'The facilities stage is low-volume and slow. Study capacity does not fix the '
             f'first; entry deposits do not fix the second.</text>')
    o.append(f'<text x="36" y="{yb+74}" font-size="11.5" fill="{MUTED}">'
             f'CAISO publishes study statuses, not study dates, so this is time to OUTCOME for '
             f'projects that stopped at each stage, not the duration of that stage.</text>')
    o.append(f'<text x="36" y="{yb+92}" font-size="11.5" fill="{MUTED}">'
             f'The jump between adjacent rows is an upper bound on that stage&#8217;s cost. '
             f'Rows under {MIN_N} projects are not drawn; only the last stage has enough '
             f'built projects to compare.</text>')
    o.append(f'<text x="36" y="{yb+116}" font-size="11.5" fill="{MUTED}">'
             f'Source: CAISO PublicQueueReport.xlsx. MISO publishes no study milestones for any of its 3,833 projects, so this cannot be split by grid.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name}")
    for i, name in enumerate(STAGES):
        if len(dead.get(i, [])) >= MIN_N:
            q1, med, q3, p90, n = band(dead[i])
            print(f"    {name:<26} dead  p25 {q1:>4.1f}  med {med:>4.1f}  "
                  f"p75 {q3:>4.1f}  p90 {p90:>5.1f}  n={n:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
