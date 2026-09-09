#!/usr/bin/env python3
"""What a GDPR fine tracks: how many things went wrong, not which thing.

    python chart-gdpr-compound.py <gdprhub.jsonl>

Each row holds one article constant and varies only how many OTHER articles the
decision cited. If a fine were priced per article, the three points on a row
would sit on top of each other. They do not — except on one row, which is the
finding.

This exists because the earlier exposure figure was wrong. It plotted a median
fine per article, which attributes a decision's fine to each article in it, and
most decisions cite several. Nearly all of that chart's vertical spread turned
out to be co-citation: articles that look expensive are the ones that show up in
pile-on cases. Holding the article fixed removes that, and is the only clean
comparison the corpus supports.

Log x-axis: the spread inside a single row reaches a factor of forty, and the
point is the ratio between the points, not the absolute euro.
"""
from __future__ import annotations

import collections
import importlib.util
import json
import math
import statistics
import sys
from pathlib import Path
from xml.sax.saxutils import escape

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "gdpr-compound.svg"
MIN_BUCKET = 8          # a median under this many cases is not drawn

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE, RISES, FLAT = "#e3e2db", "#2361b0", "#b5651d"   # CVD-checked: dEdeutan 17.2
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
BUCKETS = [(1, "cited alone"), (2, "with one other"), (3, "with two or more")]


def _analysis():
    spec = importlib.util.spec_from_file_location(
        "gdpr_analysis", str(Path(__file__).with_name("gdpr-article-concentration.py")))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    g = _analysis()
    rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]

    cases = []
    for r in rows:
        arts = {g.artnum(x) for x in r["articles"]}
        arts = {a for a in arts if a and a not in g.SCAFFOLD}
        cur = (r.get("currency") or "").strip().upper()
        if not (cur in ("EUR", "€") or (not cur and r.get("juris") in g.EUROZONE)):
            continue
        v = g.money(r.get("fine", ""))
        if v and arts:
            cases.append((arts, v))

    series = []
    for a in {x for arts, _ in cases for x in arts}:
        grp = collections.defaultdict(list)
        for arts, v in cases:
            if a in arts:
                grp[min(len(arts), 3)].append(v)
        pts = [(k, statistics.median(grp[k]), len(grp[k]))
               for k, _ in BUCKETS if len(grp.get(k, [])) >= MIN_BUCKET]
        if len(pts) == len(BUCKETS):
            series.append((a, pts))
    if not series:
        print("  no article has enough cases in every bucket yet")
        return 1
    series.sort(key=lambda s: -(s[1][-1][1] / s[1][0][1]))

    lo = min(p[1] for _, pts in series for p in pts) / 1.6
    hi = max(p[1] for _, pts in series for p in pts) * 1.6
    W, L, R, T, RH = 980, 250, 208, 196, 74
    H = T + len(series) * RH + 178

    def sx(v):
        return L + (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)) \
            * (W - L - R)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'A GDPR fine tracks how many things went wrong, not which thing.</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Each row holds one article fixed and varies only how many others the same '
             f'decision cited. Priced per article, the three</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'points on a row would coincide. On one row the fine does not rise with '
             f'company, and that is the one worth acting on.</text>')

    lx = L
    for i, (k, label) in enumerate(BUCKETS):
        o.append(f'<circle cx="{lx+7}" cy="{115}" r="{4+i*1.4:.1f}" fill="{MUTED}"/>')
        o.append(f'<text x="{lx+20}" y="119" font-size="12" fill="{INK2}">{label}</text>')
        lx += 34 + len(label) * 6.6
    o.append(f'<text x="36" y="{T-22}" font-size="11.5" fill="{MUTED}">'
             f'median fine of the decision, euro (log scale)</text>')

    for gx in (1e3, 1e4, 1e5, 1e6):
        if not lo <= gx <= hi:
            continue
        o.append(f'<line x1="{sx(gx):.1f}" y1="{T-8}" x2="{sx(gx):.1f}" '
                 f'y2="{T+len(series)*RH-24}" stroke="{RULE}"/>')
        lab = f"&#8364;{gx:,.0f}"
        o.append(f'<text x="{sx(gx):.1f}" y="{T+len(series)*RH-6}" font-size="11.5" '
                 f'fill="{MUTED}" text-anchor="middle">{lab}</text>')

    for i, (a, pts) in enumerate(series):
        y = T + i * RH
        ratio = pts[-1][1] / pts[0][1]
        colour = FLAT if ratio < 1.6 else RISES
        o.append(f'<text x="{L-18}" y="{y+4}" font-size="14" font-weight="600" '
                 f'fill="{INK}" text-anchor="end">Article {a}</text>')
        o.append(f'<text x="{L-18}" y="{y+21}" font-size="11.5" fill="{MUTED}" '
                 f'text-anchor="end">{escape(g.TITLES.get(a, ""))[:30]}</text>')
        # Span the line across the row's own extremes. Article 6 is not monotonic —
        # it is cheapest with one companion — so drawing first-to-last leaves a
        # point stranded off the end of its own line.
        vals = [m for _, m, _ in pts]
        left, right = min(vals), max(vals)
        o.append(f'<line x1="{sx(left):.1f}" y1="{y}" x2="{sx(right):.1f}" '
                 f'y2="{y}" stroke="{colour}" stroke-width="2.4"/>')
        for j, (k, med, cnt) in enumerate(pts):
            o.append(f'<circle cx="{sx(med):.1f}" cy="{y}" r="{4.6+j*1.6:.1f}" '
                     f'fill="{colour}" stroke="{SURFACE}" stroke-width="1.8"/>')
        o.append(f'<text x="{sx(left)-11:.1f}" y="{y+4}" font-size="11.5" '
                 f'fill="{INK2}" text-anchor="end">&#8364;{left:,.0f}</text>')
        rises = pts[-1][1] / pts[0][1]
        note = ("no higher in company than alone" if rises < 1.6
                else f"{rises:.0f}&#215; more when others are cited")
        o.append(f'<text x="{sx(right)+13:.1f}" y="{y+4}" font-size="12" '
                 f'font-weight="600" fill="{colour}">&#8364;{right:,.0f}</text>')
        o.append(f'<text x="{L-18}" y="{y+38}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="end">n={"/".join(str(c) for _, _, c in pts)}</text>')
        o.append(f'<text x="{sx(pts[-1][1])+13:.1f}" y="{y+21}" font-size="11.5" '
                 f'fill="{MUTED}">{note}</text>')

    yb = T + len(series) * RH + 24
    o.append(f'<line x1="36" y1="{yb-14}" x2="{W-36}" y2="{yb-14}" stroke="{RULE}"/>')
    flat = [a for a, pts in series if pts[-1][1] / pts[0][1] < 1.6]
    if flat:
        o.append(f'<text x="36" y="{yb+8}" font-size="13.5" fill="{INK2}">'
                 f'<tspan font-weight="600" fill="{INK}">Article '
                 f'{", ".join(str(a) for a in flat)} is the exception</tspan> &#8212; '
                 f'processing without a lawful basis is the one failure that is expensive '
                 f'on its own.</text>')
    o.append(f'<text x="36" y="{yb+29}" font-size="13.5" fill="{INK2}">'
             f'Everything else is cheap alone and severe in combination, so the exposure is '
             f'compound &#8212; and a per-article</text>')
    o.append(f'<text x="36" y="{yb+48}" font-size="13.5" fill="{INK2}">'
             f'&#8220;cost of non-compliance&#8221; ranking is an artefact of which articles '
             f'travel together.</text>')
    o.append(f'<text x="36" y="{yb+80}" font-size="11.5" fill="{MUTED}">'
             f'{len(cases):,} euro-denominated fined decisions. Fines as imposed, not as paid. '
             f'Association, not effect: article count may also proxy for case severity and '
             f'company size,</text>')
    o.append(f'<text x="36" y="{yb+98}" font-size="11.5" fill="{MUTED}">'
             f'neither of which GDPRhub records. The pattern holds within a single '
             f'authority, which removes authority scale but not the other two.</text>')
    o.append(f'<text x="36" y="{yb+116}" font-size="11.5" fill="{MUTED}">'
             f'Method and code: github.com/q3dresearch/cookbook &#183; '
             f'recipes/gdpr-enforced-articles</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name} — {len(series)} articles with >={MIN_BUCKET} cases in each bucket")
    for a, pts in series:
        print(f"    Art {a:<4}" + "  ".join(f"{m:>9,.0f}(n={c})" for _, m, c in pts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
