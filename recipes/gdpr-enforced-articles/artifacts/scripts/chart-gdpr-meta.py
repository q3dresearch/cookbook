#!/usr/bin/env python3
"""What a builder needs to know about GDPR enforcement, in one figure.

    python chart-gdpr-meta.py <gdprhub.jsonl>

One series — share of decisions citing each article — with the tail
de-emphasised. Emphasis, not category: the colours mean "this is the story" and
"this is context", not two different kinds of thing.

The article classification and the fine parser are imported from
gdpr-article-concentration.py rather than restated. They were duplicated here
once and immediately drifted: Art 83 was reclassified as scaffolding in the
analysis and this file went on ranking it fourth.
"""
from __future__ import annotations

import collections
import importlib.util
import sys
from pathlib import Path
from xml.sax.saxutils import escape

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "gdpr-enforced-articles.svg"

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE, HUE, DEEMPH = "#e3e2db", "#2361b0", "#c9c8c0"
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
    rows = [__import__("json").loads(l)
            for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
    n = len(rows)

    cited: collections.Counter = collections.Counter()
    for r in rows:
        for a in {g.artnum(x) for x in r["articles"]}:
            if a:
                cited[a] += 1
    enforced = [(a, c) for a, c in cited.most_common() if a not in g.SCAFFOLD][:10]
    tot = sum(c for a, c in cited.items() if a not in g.SCAFFOLD)
    lead = [a for a, _ in enforced[:3]]
    top3 = sum(c for _, c in enforced[:3]) / tot

    W, L, R, T, BH, GAP = 980, 300, 150, 172, 26, 17
    H = T + len(enforced) * (BH + GAP) + 150
    mx = enforced[0][1]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'Ninety-nine articles. Three of them are the game.</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Share of {n:,} published GDPR decisions citing each article '
             f'(GDPRhub, the whole corpus, not a sample). The decision this</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'supports: what to get right first, if you are building something and '
             f'have not read the regulation.</text>')
    o.append(f'<text x="36" y="{T-22}" font-size="11.5" fill="{MUTED}">'
             f'share of all decisions citing the article</text>')

    for i, (a, c) in enumerate(enforced):
        y = T + i * (BH + GAP)
        w = c / mx * (W - L - R)
        hot = a in lead
        o.append(f'<text x="{L-14}" y="{y+13}" font-size="13.5" '
                 f'font-weight="{"600" if hot else "400"}" '
                 f'fill="{INK if hot else INK2}" text-anchor="end">Article {a}</text>')
        o.append(f'<text x="{L-14}" y="{y+29}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="end">{escape(g.TITLES.get(a, ""))[:38]}</text>')
        o.append(f'<rect x="{L}" y="{y}" width="{max(w,2):.1f}" height="{BH}" rx="3.5" '
                 f'fill="{HUE if hot else DEEMPH}"/>')
        o.append(f'<text x="{L+max(w,2)+11:.1f}" y="{y+18}" font-size="13" '
                 f'font-weight="{"600" if hot else "400"}" fill="{INK}">{c/n:.0%}</text>')

    yb = T + len(enforced) * (BH + GAP) + 16
    o.append(f'<line x1="36" y1="{yb-12}" x2="{W-36}" y2="{yb-12}" stroke="{RULE}"/>')
    o.append(f'<text x="36" y="{yb+10}" font-size="13" fill="{INK2}">'
             f'Articles 5, 6 and 32 &#8212; <tspan font-weight="600" fill="{INK}">have a lawful '
             f'basis, collect only what you need, and secure it</tspan> &#8212; are '
             f'{top3:.0%} of all enforced citations.</text>')
    o.append(f'<text x="36" y="{yb+31}" font-size="13" fill="{INK2}">'
             f'The remaining {len([a for a in cited if a not in g.SCAFFOLD])-3} cited articles share the rest. '
             f'The regulation&#8217;s surface area is far larger than its enforced surface '
             f'area.</text>')
    scaff = ", ".join(f"Art {a}" for a in sorted(g.SCAFFOLD))
    o.append(f'<text x="36" y="{yb+62}" font-size="11.5" fill="{MUTED}">'
             f'Excluded as scaffolding &#8212; cited, but a controller cannot breach them: '
             f'{scaff}. You are fined under Art 83, not for it.</text>')
    o.append(f'<text x="36" y="{yb+80}" font-size="11.5" fill="{MUTED}">'
             f'Jurisdiction mix reflects which authorities publish, not where breaches '
             f'happen, and there is no denominator to normalise it. Citation is not a '
             f'finding of breach.</text>')
    o.append(f'<text x="36" y="{yb+98}" font-size="11.5" fill="{MUTED}">'
             f'Source and method: github.com/q3dresearch/cookbook &#183; '
             f'recipes/gdpr-enforced-articles</text>')
    o.append("</svg>")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name} — {n:,} decisions, top 3 = {top3:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
