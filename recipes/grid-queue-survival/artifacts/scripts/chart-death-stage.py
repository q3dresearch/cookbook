#!/usr/bin/env python3
"""How far projects get before giving up, and how little that depends on what they are.

    python chart-death-stage.py <queue.csv>

CAISO fills its study-milestone fields in order, so the last one completed is
where a withdrawn project stopped. Two dimensions: the stage reached, and the
technology — because the interesting result is that the second one barely
matters. Between 43% and 55% of every technology dies before any study is done.

That flatness is the policy content. A bottleneck that falls equally on solar,
storage, wind and gas is not about any of them; it is about how many applications
the process accepts before it filters. Charting stage alone would have shown the
same 52% and left the reader to assume it was a story about one technology.

Capacity is deliberately NOT plotted beside project count: the two shares track
within three points at every stage (49% vs 52% at intake) and average project
size is flat across stages, so a second series would be two near-identical bars
dressed as a comparison. That equality is stated once, in the footnote, which is
all it is worth.
"""
from __future__ import annotations

import collections
import csv
import sys
from pathlib import Path
from xml.sax.saxutils import escape

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "death-stage.svg"
MIN_N = 60

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE = "#e3e2db"
# Sequential: one hue, light to dark, because stage is ordered.
RAMP = ["#cfd9e6", "#9cb2cd", "#6a8ab4", "#3c6699", "#1d4373"]
STAGES = ["died before any study", "in feasibility", "after system impact",
          "after facilities study", "after signing an agreement"]
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


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
            if r["iso"] == "CAISO" and r["status"] == "withdrawn"]

    def mw(r):
        try:
            return float(r["mw"])
        except (TypeError, ValueError):
            return 0.0

    per = collections.defaultdict(collections.Counter)
    overall = collections.Counter()
    gw = collections.Counter()
    for r in rows:
        s = stage_of(r)
        overall[s] += 1
        gw[s] += mw(r)
        t = (r["technology"] or "").strip()
        if t:
            per[t][s] += 1
    techs = [t for t, c in sorted(per.items(), key=lambda kv: -sum(kv[1].values()))
             if sum(c.values()) >= MIN_N]
    series = [("All withdrawn projects", overall)] + [(t, per[t]) for t in techs]

    W, L, R, T, RH = 1000, 250, 56, 208, 46
    H = T + len(series) * RH + 196
    BW = W - L - R

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'Half the queue dies before anyone studies it, whatever it is</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Where {len(rows):,} withdrawn California projects stopped, as a share of each '
             f'technology&#8217;s own withdrawals. The rows barely differ:</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'the filter falls at intake, and it falls on everything equally.</text>')

    lx = 36
    for i, name in enumerate(STAGES):
        o.append(f'<rect x="{lx}" y="{T-46}" width="12" height="12" rx="2.5" fill="{RAMP[i]}"/>')
        o.append(f'<text x="{lx+18}" y="{T-36}" font-size="11.5" fill="{INK2}">{name}</text>')
        lx += 30 + len(name) * 6.5

    for i, (label, counts) in enumerate(series):
        y = T + i * RH
        n = sum(counts.values())
        head = i == 0
        o.append(f'<text x="{L-16}" y="{y+15}" font-size="13" '
                 f'font-weight="{"600" if head else "400"}" fill="{INK if head else INK2}" '
                 f'text-anchor="end">{escape(label)[:26]}</text>')
        o.append(f'<text x="{L-16}" y="{y+30}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="end">{n:,} withdrawn</text>')
        x = float(L)
        for s in range(5):
            w = counts[s] / n * BW
            if w <= 0:
                continue
            o.append(f'<rect x="{x:.1f}" y="{y}" width="{max(w-2, 1):.1f}" height="24" '
                     f'fill="{RAMP[s]}"/>')
            if w > 42:
                o.append(f'<text x="{x+w/2-1:.1f}" y="{y+16}" font-size="11.5" '
                         f'fill="{"#ffffff" if s >= 3 else INK}" text-anchor="middle">'
                         f'{counts[s]/n:.0%}</text>')
            x += w
        if head:
            o.append(f'<line x1="{L}" y1="{y+34}" x2="{W-R}" y2="{y+34}" stroke="{RULE}"/>')

    yb = T + len(series) * RH + 22
    tot = sum(overall.values())
    tgw = sum(gw.values()) / 1000
    o.append(f'<text x="36" y="{yb}" font-size="13" fill="{INK}">'
             f'<tspan font-weight="600">{overall[0]/tot:.0%} never reached a study at all, and '
             f'{overall[4]/tot:.0%} died holding a signed interconnection agreement.</tspan></text>')
    o.append(f'<text x="36" y="{yb+22}" font-size="12.5" fill="{INK2}">'
             f'Those are different problems. The first is an intake that accepts more than it '
             f'can filter; the second is a project that cleared every study and still could '
             f'not proceed.</text>')
    o.append(f'<text x="36" y="{yb+52}" font-size="11.5" fill="{MUTED}">'
             f'Capacity follows count almost exactly &#8212; {gw[0]/1000/tgw:.0%} of the '
             f'{tgw:,.0f} GW abandoned is at intake against {overall[0]/tot:.0%} of projects, '
             f'and average size is flat across stages.</text>')
    o.append(f'<text x="36" y="{yb+70}" font-size="11.5" fill="{MUTED}">'
             f'Big projects do not die later than small ones, so screening by size would not '
             f'work. Stage is inferred from CAISO&#8217;s study-completion fields, which it '
             f'fills in order;</text>')
    o.append(f'<text x="36" y="{yb+88}" font-size="11.5" fill="{MUTED}">'
             f'a project with no milestone recorded is counted as never studied.</text>')
    o.append(f'<text x="36" y="{yb+112}" font-size="11.5" fill="{MUTED}">'
             f'CAISO only &#8212; MISO publishes no study milestones for any of its 3,833 projects, so this cannot be split by grid. Technologies with fewer '
             f'than {MIN_N} withdrawals are omitted. Source: PublicQueueReport.xlsx.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name} — {len(series)} rows")
    for label, c in series:
        n = sum(c.values())
        print(f"    {label[:24]:<26}" + "".join(f"{c[s]/n:>7.0%}" for s in range(5)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
