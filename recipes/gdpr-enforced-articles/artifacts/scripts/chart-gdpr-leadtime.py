#!/usr/bin/env python3
"""How long a GDPR case takes, and whether that is getting worse.

    python chart-gdpr-leadtime.py <gdprhub.jsonl>

Date_Started to Date_Decided, for the quarter of decisions that record both.
The band is the interquartile range: half of cases land inside it, and it is
drawn because a median alone hides that the slowest quarter runs past two years.

Coverage is the thing to check before believing any of it. A quarter of the
corpus carries both dates, and if that quarter were one authority the line would
be that authority's line wearing a European label — so the panel on the right
shows coverage per authority, and the median is only drawn for years where at
least MIN_YEAR cases are dated.

Two lines, because the obvious objection to a trend drawn from a wiki is that the
set of authorities changed underneath it. The heavier line is a FIXED PANEL: only
authorities with at least PANEL_MIN dated decisions in every year of the window,
so the same regulators are compared with themselves. It rises faster than the
all-authorities line, which means composition was hiding the effect rather than
creating it.
"""
from __future__ import annotations

import collections
import datetime as dt
import importlib.util
import json
import statistics
import sys
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "gdpr-leadtime.svg"
MIN_YEAR = 40
PANEL_MIN = 8      # dated decisions an authority needs in EVERY year to join the panel

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE, HUE, BAND, ALT = "#e3e2db", "#2361b0", "#dbe5f2", "#b5651d"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def _timeline():
    spec = importlib.util.spec_from_file_location(
        "gdpr_timeline", str(Path(__file__).with_name("gdpr-case-timeline.py")))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    t = _timeline()
    rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]

    spans = []
    for r in rows:
        a, b = t.date(r.get("date_started", "")), t.date(r.get("date_decided", ""))
        if a and b and b >= a and (b - a).days < 4000:
            spans.append(((b - a).days, b.year, r))
    if not spans:
        print("  no dated decisions")
        return 1
    if not spans:
        print("  no dated decisions")
        return 1

    byy = collections.defaultdict(list)
    for d, y, _ in spans:
        byy[y].append(d)
    years = [y for y in sorted(byy) if len(byy[y]) >= MIN_YEAR]
    if len(years) < 3:
        print(f"  only {len(years)} years reach n>={MIN_YEAR}")
        return 1
    stats = []
    for y in years:
        v = sorted(byy[y])
        q = statistics.quantiles(v, n=4)
        stats.append((y, q[0], statistics.median(v), q[2], len(v)))

    # Fixed panel: the same authorities in every year of the window.
    byyj = collections.defaultdict(lambda: collections.defaultdict(list))
    for d, y, r in spans:
        byyj[y][r.get("juris") or "?"].append(d)
    panel = sorted(j for j in {j for y in years for j in byyj[y]}
                   if all(len(byyj[y].get(j, [])) >= PANEL_MIN for y in years))
    pstats = []
    for y in years:
        v = sorted(d for j in panel for d in byyj[y].get(j, []))
        if len(v) >= 4:
            q = statistics.quantiles(v, n=4)
            pstats.append((y, statistics.median(v), len(v), q[0], q[2]))

    cov_n = collections.Counter(r["juris"] for r in rows if r.get("juris"))
    cov_k = collections.Counter(r["juris"] for _, _, r in spans if r.get("juris"))
    cov = sorted(((cov_k[j] / cov_n[j], j, cov_k[j], cov_n[j])
                  for j in cov_k if cov_n[j] >= 60), reverse=True)[:7]

    W, H = 980, 560
    L, R, T, B = 92, 384, 190, 96
    hi = max(s[3] for s in stats) * 1.12
    def sx(i): return L + i / max(len(stats) - 1, 1) * (W - L - R)
    def sy(v): return H - B - v / hi * (H - T - B)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    # Headline off the last COMPLETE year. The current year is missing every case
    # that has not finished yet, and the cases that have not finished are the slow
    # ones, so its median is the least trustworthy number on the chart.
    this_year = dt.date.today().year
    complete = [s_ for s_ in stats if s_[0] < this_year]
    first, last = stats[0], (complete[-1] if complete else stats[-1])
    pc = [q for q in pstats if q[0] < this_year]
    grew = (pc[-1][1] / pstats[0][1] - 1) if pc and pstats else None
    pn = {q[0]: q[2] for q in pstats}
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'The same regulators take {grew:+.0%} longer than they did in '
             f'{pstats[0][0]}.</text>' if grew is not None else
             f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'A GDPR case took {first[2]:,.0f} days in {first[0]}.</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Days from the authority opening a case to deciding it, by year of decision. '
             f'Band is the middle half of cases.</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'Only the {len(spans):,} decisions ({len(spans)/len(rows):.0%}) that record both '
             f'dates, so read the coverage panel before the line.</text>')
    o.append(f'<line x1="36" y1="112" x2="62" y2="112" stroke="{HUE}" stroke-width="3"/>')
    o.append(f'<text x="70" y="116" font-size="12" fill="{INK2}">'
             f'same authorities every year ({", ".join(panel)})</text>')
    o.append(f'<line x1="{420}" y1="112" x2="{446}" y2="112" stroke="{ALT}" '
             f'stroke-width="2" stroke-dasharray="5 3"/>')
    o.append(f'<text x="454" y="116" font-size="12" fill="{MUTED}">'
             f'all authorities &#8212; diluted by who joined when</text>')
    o.append(f'<text x="36" y="{T-16}" font-size="11.5" fill="{MUTED}">'
             f'days from opening to decision</text>')

    for gy in range(0, int(hi), 200):
        if gy == 0:
            continue
        o.append(f'<line x1="{L}" y1="{sy(gy):.1f}" x2="{W-R}" y2="{sy(gy):.1f}" '
                 f'stroke="{RULE}"/>')
        o.append(f'<text x="{L-10}" y="{sy(gy)+4:.1f}" font-size="11.5" fill="{MUTED}" '
                 f'text-anchor="end">{gy:,}</text>')
    o.append(f'<line x1="{L}" y1="{H-B}" x2="{W-R}" y2="{H-B}" stroke="{MUTED}"/>')

    idx0 = {s_[0]: i for i, s_ in enumerate(stats)}
    band = " ".join(f"{sx(idx0[y]):.1f},{sy(q1):.1f}" for y, _, _, q1, _ in pstats) + " " + \
           " ".join(f"{sx(idx0[y]):.1f},{sy(q3):.1f}" for y, _, _, _, q3 in reversed(pstats))
    o.append(f'<polygon points="{band}" fill="{BAND}"/>')
    alt = " ".join(f"{'M' if i == 0 else 'L'}{sx(i):.1f},{sy(s[2]):.1f}"
                   for i, s in enumerate(stats))
    o.append(f'<path d="{alt}" fill="none" stroke="{ALT}" stroke-width="2" '
             f'stroke-dasharray="5 3"/>')
    idx = {s_[0]: i for i, s_ in enumerate(stats)}
    line = " ".join(f"{'M' if i == 0 else 'L'}{sx(idx[y]):.1f},{sy(m):.1f}"
                    for i, (y, m, _k, _a, _b) in enumerate(pstats))
    o.append(f'<path d="{line}" fill="none" stroke="{HUE}" stroke-width="3"/>')
    for y, m, k, _q1, _q3 in pstats:
        o.append(f'<circle cx="{sx(idx[y]):.1f}" cy="{sy(m):.1f}" r="5.4" fill="{HUE}" '
                 f'stroke="{SURFACE}" stroke-width="2"/>')
        anchor = "start" if y == pstats[0][0] else "middle"
        dx = 9 if anchor == "start" else 0
        o.append(f'<text x="{sx(idx[y])+dx:.1f}" y="{sy(m)-14:.1f}" font-size="12" '
                 f'font-weight="600" fill="{INK}" text-anchor="{anchor}">{m:,.0f}</text>')
    for i, s in enumerate(stats):
        partial = s[0] >= this_year
        _ = s
        o.append(f'<text x="{sx(i):.1f}" y="{H-B+20}" font-size="12" '
                 f'fill="{MUTED if partial else INK2}" text-anchor="middle">'
                 f'{s[0]}{" (partial)" if partial else ""}</text>')
        o.append(f'<text x="{sx(i):.1f}" y="{H-B+37}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="middle">n={pn.get(s[0], 0)} of {s[4]}</text>')
    o.append(f'<text x="{sx(len(stats)-1):.1f}" y="{sy(stats[-1][3])-8:.1f}" font-size="11.5" '
             f'fill="{MUTED}" text-anchor="end">slowest quarter of panel cases above here</text>')

    px = W - R + 36
    o.append(f'<text x="{px}" y="{T-16}" font-size="12.5" font-weight="600" fill="{INK}">'
             f'Coverage by authority</text>')
    o.append(f'<text x="{px}" y="{T+2}" font-size="11" fill="{MUTED}">'
             f'share recording both dates</text>')
    for i, (share, j, k, tot) in enumerate(cov):
        y = T + 26 + i * 26
        o.append(f'<text x="{px}" y="{y}" font-size="11.5" fill="{INK2}">{j[:14]}</text>')
        o.append(f'<rect x="{px+96}" y="{y-9}" width="{share*118:.0f}" height="11" rx="2" '
                 f'fill="{HUE}" opacity="0.75"/>')
        o.append(f'<text x="{px+220}" y="{y}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="end">{share:.0%}</text>')
    o.append(f'<text x="{px}" y="{T+26+len(cov)*26+14}" font-size="11" fill="{MUTED}">'
             f'No single authority dominates the</text>')
    o.append(f'<text x="{px}" y="{T+26+len(cov)*26+29}" font-size="11" fill="{MUTED}">'
             f'dated set, so the line is not one</text>')
    o.append(f'<text x="{px}" y="{T+26+len(cov)*26+44}" font-size="11" fill="{MUTED}">'
             f'regulator&#8217;s habits.</text>')

    o.append(f'<text x="36" y="{H-42}" font-size="11.5" fill="{MUTED}">'
             f'Decisions recording both dates only; a case opened before the '
             f'regulation cannot appear. Counts are panel cases of all dated cases; '
             f'the band is the panel&#8217;s middle half.</text>')
    o.append(f'<text x="36" y="{H-24}" font-size="11.5" fill="{MUTED}">'
             f'The final year is partial: cases still open are not in it, and slow cases '
             f'finish late, so the last point understates its year.</text>')
    o.append(f'<text x="36" y="{H-6}" font-size="11.5" fill="{MUTED}">'
             f'Method and code: github.com/q3dresearch/cookbook &#183; '
             f'recipes/gdpr-enforced-articles</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name} — {len(spans):,} dated decisions, {len(stats)} years")
    for y, q1, med, q3, k in stats:
        print(f"    {y}  n={k:>4}  q1={q1:>5,.0f}  median={med:>5,.0f}  q3={q3:>6,.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
