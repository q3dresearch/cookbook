#!/usr/bin/env python3
"""How often an article is cited, against what it costs when it is.

    python chart-gdpr-exposure.py <gdprhub.jsonl>

Two measures of the same articles that disagree, so they go on two axes of one
scatter rather than two y-scales of one bar chart. A dual-axis chart would let
the scale choice manufacture whatever relationship suited the story.

The y-axis is the median fine of DECISIONS CITING an article, which is not what
the article costs and must never be labelled as such. A fine is imposed on a
decision, and most decisions cite several articles, so each article inherits the
whole fine of every case it appears in. Run gdpr-cocitation.py for the size of
the problem: Art 32 and Art 33 are close to one population, and an article that
is never cited alone has no independently measurable price at all. Points whose
median rests entirely on shared cases are marked.

The y-axis is logarithmic because median fines span three orders of magnitude,
and the point of the figure is the ordering, not the ratios.

Articles with fewer than MIN_FINED fined decisions are dropped: a median over
four values moves by tens of thousands of euro when one case is added, and a
label on such a point invites a reader to act on noise.
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
OUT = RECIPE / "artifacts" / "charts" / "gdpr-exposure.svg"
MIN_FINED = 10
# The quadrant thresholds are stated, not derived. Using the median of the
# filtered set made "common" mean "above the middle of the fourteen articles I
# chose to plot", which moves when MIN_FINED moves and is not a fact about
# anything.
COMMON = 0.10          # cited in at least a tenth of all decisions
EXPENSIVE = 100_000    # median fine of at least this many euro

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE, HUE, DIM, BAND = "#e3e2db", "#2361b0", "#b9c2ce", "#eaf0f8"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


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
    n = len(rows)

    cited: collections.Counter = collections.Counter()
    fines: dict[int, list[float]] = collections.defaultdict(list)
    for r in rows:
        arts = {g.artnum(x) for x in r["articles"]}
        arts = {a for a in arts if a and a not in g.SCAFFOLD}
        for a in arts:
            cited[a] += 1
        cur = (r.get("currency") or "").strip().upper()
        if cur in ("EUR", "€") or (not cur and r.get("juris") in g.EUROZONE):
            v = g.money(r.get("fine", ""))
            if v:
                for a in arts:
                    fines[a].append(v)

    pts = [(a, cited[a] / n, statistics.median(vs), len(vs))
           for a, vs in fines.items() if len(vs) >= MIN_FINED]
    if not pts:
        print("  no article has enough fined decisions yet")
        return 1
    pts.sort(key=lambda p: -p[1])

    W, H, L, R, T, B = 980, 636, 108, 236, 196, 112
    xs = [p[1] for p in pts]
    ys = [p[2] for p in pts]
    x0, x1 = 0, max(xs) * 1.12
    y0, y1 = min(ys) / 1.7, max(ys) * 1.7

    def sx(v):
        return L + v / x1 * (W - L - R)

    def sy(v):
        return H - B - (math.log10(v) - math.log10(y0)) / \
            (math.log10(y1) - math.log10(y0)) * (H - T - B)

    med_x, med_y = COMMON, EXPENSIVE
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'The articles you are most likely to be cited for sit in the cheaper '
             f'cases.</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Each article that appears in at least {MIN_FINED} fined decisions, placed by how '
             f'often it is cited and the median fine when it is.</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'The fine belongs to the decision, not the article: most decisions cite '
             f'several, so every article inherits the whole fine of each case</text>')
    o.append(f'<text x="36" y="106" font-size="13.5" fill="{INK2}">'
             f'it appears in. Read the vertical axis as &#8220;the company this article '
             f'keeps&#8221;, never as a price.</text>')

    o.append(f'<rect x="{sx(med_x):.0f}" y="{T}" width="{W-R-sx(med_x):.0f}" '
             f'height="{sy(med_y)-T:.0f}" fill="{BAND}"/>')
    o.append(f'<text x="{W-R-8:.0f}" y="{T+18}" font-size="11.5" fill="{MUTED}" '
             f'text-anchor="end">cited in &#8805;{COMMON:.0%} of decisions AND median fine '
             f'&#8805;&#8364;{EXPENSIVE:,}</text>')

    for gy in (1e3, 1e4, 1e5, 1e6):
        if not y0 <= gy <= y1:
            continue
        o.append(f'<line x1="{L}" y1="{sy(gy):.1f}" x2="{W-R}" y2="{sy(gy):.1f}" '
                 f'stroke="{RULE}"/>')
        lab = f"&#8364;{gy:,.0f}" if gy < 1e6 else "&#8364;1,000,000"
        o.append(f'<text x="{L-10}" y="{sy(gy)+4:.1f}" font-size="11.5" fill="{MUTED}" '
                 f'text-anchor="end">{lab}</text>')
    for gx in (0.1, 0.2, 0.3, 0.4, 0.5):
        if gx > x1:
            continue
        o.append(f'<line x1="{sx(gx):.1f}" y1="{T}" x2="{sx(gx):.1f}" y2="{H-B}" '
                 f'stroke="{RULE}"/>')
        o.append(f'<text x="{sx(gx):.1f}" y="{H-B+20}" font-size="11.5" fill="{MUTED}" '
                 f'text-anchor="middle">{gx:.0%}</text>')
    o.append(f'<line x1="{L}" y1="{H-B}" x2="{W-R}" y2="{H-B}" stroke="{MUTED}"/>')
    o.append(f'<text x="{(L+W-R)/2:.0f}" y="{H-B+42}" font-size="11.5" fill="{MUTED}" '
             f'text-anchor="middle">share of all decisions citing the article</text>')
    o.append(f'<text x="36" y="{T-12}" font-size="11.5" fill="{MUTED}">'
             f'median fine of decisions citing the article &#8212; not the article&#8217;s '
             f'own cost (log scale)</text>')

    # Labels sit right of their dot and are nudged apart vertically until none
    # overlap. Points cluster tightly at the cheap end, and overlapping labels
    # there made four articles unreadable.
    lab = []
    for a, share, med, k in pts:
        x, y = sx(share), sy(med)
        text = f"{escape(g.TITLES.get(a, ''))[:30]}"
        width = 46 + len(text) * 5.9
        solo = sum(1 for r in rows
                   if {g.artnum(x) for x in r["articles"]} - set(g.SCAFFOLD) == {a}
                   and g.money(r.get("fine", "")))
        lab.append({"a": a, "x": x, "y": y, "ly": y, "w": width, "text": text,
                    "never_alone": solo == 0,
                    "hot": share >= med_x and med >= med_y})
    lab.sort(key=lambda d: d["ly"])
    for _ in range(240):
        moved = False
        for i in range(len(lab)):
            for j in range(i + 1, len(lab)):
                p1, p2 = lab[i], lab[j]
                if abs(p1["ly"] - p2["ly"]) >= 15:
                    continue
                if p1["x"] + 11 + p1["w"] < p2["x"] + 8 or p2["x"] + 11 + p2["w"] < p1["x"] + 8:
                    continue                     # side by side, no overlap
                p1["ly"] -= 0.6
                p2["ly"] += 0.6
                moved = True
        if not moved:
            break
    for d in lab:
        r = 6.5 if d["hot"] else 5.2
        o.append(f'<circle cx="{d["x"]:.1f}" cy="{d["y"]:.1f}" r="{r}" '
                 f'fill="{"none" if d["never_alone"] else (HUE if d["hot"] else DIM)}" '
                 f'stroke="{HUE if d["hot"] else DIM}" stroke-width="2"'
                 f'{" stroke-dasharray=\"2.6 2.2\"" if d["never_alone"] else ""}/>')
        if abs(d["ly"] - d["y"]) > 3:            # leader line to the nudged label
            o.append(f'<line x1="{d["x"]+r+1:.1f}" y1="{d["y"]:.1f}" x2="{d["x"]+9:.1f}" '
                     f'y2="{d["ly"]:.1f}" stroke="{MUTED}" stroke-width="0.7"/>')
        o.append(f'<text x="{d["x"]+11:.1f}" y="{d["ly"]+4:.1f}" font-size="12" '
                 f'font-weight="{"600" if d["hot"] else "400"}" '
                 f'fill="{INK if d["hot"] else INK2}">'
                 f'Art {d["a"]} <tspan font-size="11" font-weight="400" fill="{MUTED}">'
                 f'{d["text"]}</tspan></text>')

    solo_note = ", ".join(f"Art {d['a']}" for d in lab if d.get("never_alone"))
    o.append(f'<text x="36" y="{H-40}" font-size="11.5" fill="{MUTED}">'
             f'{n:,} decisions. Never cited alone in a fined case, so their medians are '
             f'borrowed entirely from co-cited articles: {solo_note or "none"}.</text>')
    o.append(f'<text x="36" y="{H-22}" font-size="11.5" fill="{MUTED}">'
             f'Euro-denominated fines only. Citation is not a finding of breach. '
             f'Method: github.com/q3dresearch/cookbook &#183; recipes/gdpr-enforced-articles</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name} — {len(pts)} articles with >={MIN_FINED} fined decisions")
    for a, s_, m, k in pts:
        print(f"    Art {a:<4}{s_:>6.1%} cited   median {m:>10,.0f}   n={k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
