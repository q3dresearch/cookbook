#!/usr/bin/env python3
"""The same project, in two grids, under the same federal rule.

    python chart-jurisdiction.py <queue.csv>

FERC requires every US transmission provider to run an interconnection queue, so
CAISO and MISO are doing the same job under the same law. They do not get the same
result. Holding the technology AND the entry era fixed — the two confounds that
made every earlier comparison in this recipe wrong — California clears solar at
12.5% where the Midwest clears it at 42.6%, and wind at 6.5% against 18.0%.

That gap is larger than any difference between technologies. After age-matching,
the spread from the worst technology to the best is roughly two-fold. The spread
between the two grids, for one technology, is three-fold. Which grid you are in
matters more than what you are building, and this is the chart that says so.

Read the sample sizes before the gap. MISO's queue is overwhelmingly recent: only
253 of its 2,700 resolved projects entered by 2017, against CAISO's 1,446. The
direction is not in doubt, the magnitude is.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "jurisdiction.svg"
ERA = (2011, 2017)
MIN_N = 25
# The same thing under each operator's own vocabulary.
FAMILIES = [("Solar", "Photovoltaic", "Solar"),
            ("Wind", "Wind Turbine", "Wind"),
            ("Storage", "Storage", "Battery Storage"),
            ("Gas, combined cycle", "Combined Cycle", "Gas")]

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE, CAISO_C, MISO_C = "#e3e2db", "#2361b0", "#b5651d"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))

    def rate(iso, tech):
        b = w = 0
        for r in rows:
            if r["iso"] != iso or (r["technology"] or "").strip() != tech:
                continue
            y = (r["queue_date"] or "")[:4]
            if not y.isdigit() or not ERA[0] <= int(y) <= ERA[1]:
                continue
            if r["status"] == "built":
                b += 1
            elif r["status"] == "withdrawn":
                w += 1
        return (b / (b + w), b + w) if b + w else (None, 0)

    pairs = []
    for label, ct, mt in FAMILIES:
        c, cn = rate("CAISO", ct)
        m, mn = rate("MISO", mt)
        pairs.append((label, c, cn, m, mn))

    usable = [p for p in pairs if p[1] is not None and p[3] is not None
              and p[2] >= MIN_N and p[4] >= MIN_N]
    W, L, R, T, RH = 980, 210, 300, 200, 64
    H = T + len(pairs) * RH + 150
    mx = max([v for p in pairs for v in (p[1], p[3]) if v is not None] + [0.45])

    def sx(v):
        return L + v / (mx * 1.08) * (W - L - R)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'Which grid you queue in matters more than what you are building</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Share of projects built, for the same technology entering the queue in the same '
             f'years ({ERA[0]}&#8211;{ERA[1]}), in two systems</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'running the same FERC-mandated process. Age and technology are held fixed, so the '
             f'gap is the operator.</text>')
    o.append(f'<circle cx="42" cy="118" r="6" fill="{CAISO_C}"/>')
    o.append(f'<text x="54" y="122" font-size="12.5" font-weight="600" fill="{CAISO_C}">'
             f'CAISO &#8212; California</text>')
    o.append(f'<circle cx="222" cy="118" r="6" fill="{MISO_C}"/>')
    o.append(f'<text x="234" y="122" font-size="12.5" font-weight="600" fill="{MISO_C}">'
             f'MISO &#8212; Midwest</text>')

    for g in (0, 0.1, 0.2, 0.3, 0.4):
        if g > mx * 1.08:
            continue
        o.append(f'<line x1="{sx(g):.1f}" y1="{T-24}" x2="{sx(g):.1f}" '
                 f'y2="{T+len(pairs)*RH-30}" stroke="{RULE}"/>')
        o.append(f'<text x="{sx(g):.1f}" y="{T+len(pairs)*RH-10}" font-size="11.5" '
                 f'fill="{MUTED}" text-anchor="middle">{g:.0%}</text>')

    for i, (label, c, cn, m, mn) in enumerate(pairs):
        y = T + i * RH
        # A row where only one operator has enough projects still carries a real
        # number for that operator. Blanking it threw away CAISO's 137 storage
        # projects because MISO had four.
        c_ok = c is not None and cn >= MIN_N
        m_ok = m is not None and mn >= MIN_N
        both = c_ok and m_ok
        o.append(f'<text x="{L-18}" y="{y+5}" font-size="13.5" font-weight="600" '
                 f'fill="{INK if both else INK2}" text-anchor="end">{label}</text>')
        if not both:
            if not c_ok and not m_ok:
                o.append(f'<text x="{L+8}" y="{y+5}" font-size="12" fill="{MUTED}">'
                         f'too few in both to report '
                         f'(CAISO n={cn}, MISO n={mn})</text>')
                continue
            v, col, n, who = ((c, CAISO_C, cn, "CAISO") if c_ok
                              else (m, MISO_C, mn, "MISO"))
            other, on = ("MISO", mn) if c_ok else ("CAISO", cn)
            o.append(f'<circle cx="{sx(v):.1f}" cy="{y}" r="7" fill="{col}" '
                     f'stroke="{SURFACE}" stroke-width="2"/>')
            o.append(f'<text x="{sx(v)+13:.1f}" y="{y+5}" font-size="12.5" '
                     f'font-weight="600" fill="{col}">{v:.0%}</text>')
            o.append(f'<text x="{W-R+14}" y="{y+1}" font-size="12" fill="{MUTED}">'
                     f'{who} only &#183; n={n}</text>')
            o.append(f'<text x="{W-R+14}" y="{y+17}" font-size="11" fill="{MUTED}">'
                     f'{other} had {on} in this era</text>')
            continue
        o.append(f'<line x1="{sx(c):.1f}" y1="{y}" x2="{sx(m):.1f}" y2="{y}" '
                 f'stroke="{MUTED}" stroke-width="2"/>')
        for v, col, n in ((c, CAISO_C, cn), (m, MISO_C, mn)):
            o.append(f'<circle cx="{sx(v):.1f}" cy="{y}" r="7" fill="{col}" '
                     f'stroke="{SURFACE}" stroke-width="2"/>')
        left, right = (c, CAISO_C, cn), (m, MISO_C, mn)
        if c > m:
            left, right = right, left
        o.append(f'<text x="{sx(left[0])-13:.1f}" y="{y+5}" font-size="12.5" '
                 f'font-weight="600" fill="{left[1]}" text-anchor="end">{left[0]:.0%}</text>')
        o.append(f'<text x="{sx(right[0])+13:.1f}" y="{y+5}" font-size="12.5" '
                 f'font-weight="600" fill="{right[1]}">{right[0]:.0%}</text>')
        o.append(f'<text x="{W-R+14}" y="{y+1}" font-size="12" fill="{INK}">'
                 f'{max(c, m)/min(c, m):.1f}&#215; better in '
                 f'{"MISO" if m > c else "CAISO"}</text>')
        o.append(f'<text x="{W-R+14}" y="{y+17}" font-size="11" fill="{MUTED}">'
                 f'n={cn} CAISO, {mn} MISO</text>')

    yb = T + len(pairs) * RH + 24
    o.append(f'<line x1="36" y1="{yb-16}" x2="{W-36}" y2="{yb-16}" stroke="{RULE}"/>')
    o.append(f'<text x="36" y="{yb+6}" font-size="13" fill="{INK}">'
             f'<tspan font-weight="600">Age-matched, the spread between technologies is about '
             f'two-fold. Between these two grids, for one technology, it is three.</tspan></text>')
    o.append(f'<text x="36" y="{yb+28}" font-size="12.5" fill="{INK2}">'
             f'Both operate under the same federal interconnection rule, which makes the gap a '
             f'question about process rather than about resources or geography.</text>')
    o.append(f'<text x="36" y="{yb+56}" font-size="11.5" fill="{MUTED}">'
             f'Read the sample sizes before the ratio. MISO&#8217;s queue is overwhelmingly '
             f'recent: 253 of its 2,700 resolved projects entered by 2017, against '
             f'CAISO&#8217;s 1,446, so its rate rests on a small</text>')
    o.append(f'<text x="36" y="{yb+74}" font-size="11.5" fill="{MUTED}">'
             f'early cohort. The direction is not in doubt; the magnitude is. Rows with '
             f'only one operator show that operator&#8217;s rate and are not a comparison.'
             f'</text>')
    o.append(f'<text x="36" y="{yb+98}" font-size="11.5" fill="{MUTED}">'
             f'Sources: CAISO PublicQueueReport.xlsx, MISO api/giqueue/getprojects. '
             f'Built and withdrawn only; still-active projects excluded.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name}")
    for label, c, cn, m, mn in pairs:
        cs = f"{c:.1%}({cn})" if c is not None else "-"
        ms = f"{m:.1%}({mn})" if m is not None else "-"
        print(f"    {label:<22} CAISO {cs:<14} MISO {ms}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
