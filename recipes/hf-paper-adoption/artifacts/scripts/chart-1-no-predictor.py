#!/usr/bin/env python3
"""Nothing about a paper predicts whether a model will use it.

The base rate is the whole story: **0.8% of papers on Hugging Face's daily feed are
ever named on the card of a top-1,000 model.** Every feature available at publication
is tested against that base here, and the best of them reaches 7%.

Which means 93 of every 100 papers with a large popular repo are still never used.
That is not a predictor; it is a weak correlate of an outcome that almost never
happens.

**The one that looks strong is the one to distrust most.** Stars are counted today,
after adoption, and for the biggest repos the repository IS the released model — so
the 1,000+ bucket is substantially measuring the outcome rather than forecasting it.
The giveaway is the shape: a mid-sized repo (100-999 stars) does WORSE than no repo at
all, which no real predictor does.
"""
import sys, collections, math
sys.path.insert(0, ".")
import paperlib as P

def wil(k, n, z=1.96):
    if not n: return (0, 0)
    p = k/n; d = 1+z*z/n; c = (p+z*z/(2*n))/d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return max(0, c-h), min(1, c+h)

def main():
    f = P.feed(); ms = P.models()
    cited = set()
    for m in ms: cited |= P.arxiv_ids(m)
    base = sum(1 for a in f if a in cited) / len(f)
    tests = [
        ("repo with 1,000+ stars",  lambda pa: (pa.get("githubStars") or -1) >= 1000, True),
        ("top-decile upvotes",      lambda pa: (pa.get("upvotes") or 0) >= 54, False),
        ("a named organisation",    lambda pa: bool(pa.get("_org")), False),
        ("no repo listed",          lambda pa: pa.get("githubStars") is None, False),
        ("repo, 100-999 stars",     lambda pa: 100 <= (pa.get("githubStars") or -1) < 1000, False),
        ("repo, under 100 stars",   lambda pa: 0 <= (pa.get("githubStars") or -1) < 100, False),
    ]
    rows = []
    for lab, sel, suspect in tests:
        g = [a for a, pa in f.items() if sel(pa)]
        k = sum(1 for a in g if a in cited)
        rows.append((k/len(g), k, len(g), lab, suspect))
    rows.sort(reverse=True)
    W, H, L, R, T, B = 880, 460, 210, 176, 118, 116
    pw, ph = W-L-R, H-T-B
    mx = max(wil(k, n)[1] for _, k, n, _, _ in rows) * 1.08
    sx = lambda v: L + v/mx*pw
    body = [P.txt(L, T-16, "share of papers ever named on a top-1,000 model's card", size=12, fill=P.INK2)]
    g = 0.0
    while g <= mx:
        x = sx(g)
        body.append(f'<line x1="{x:.1f}" y1="{T-4}" x2="{x:.1f}" y2="{T+ph:.1f}" stroke="{P.GRID}" stroke-width="1"/>')
        body.append(P.txt(x, T+ph+20, f"{g:.0%}", size=11, fill=P.MUTED, anchor="middle", tab=True))
        g += 0.02
    bx = sx(base)
    body.append(f'<line x1="{bx:.1f}" y1="{T-10}" x2="{bx:.1f}" y2="{T+ph+4:.1f}" '
                f'stroke="{P.INK}" stroke-width="1.6" stroke-dasharray="5 4"/>')
    # Below the plot, not beside the axis title it was overlapping.
    body.append(P.txt(bx, T+ph+38, f"base rate {base:.1%}", size=11.5, fill=P.INK,
                      anchor="middle", weight="600"))
    step = ph/len(rows)
    for i, (r, k, n, lab, suspect) in enumerate(rows):
        y = T + step*(i+.5)
        col = P.FIELD_COLOR["image-gen"] if suspect else P.FIELD_COLOR["LLM-core"]
        body.append(P.txt(L-14, y+4, lab, size=12, fill=P.INK, anchor="end", weight="600"))
        lo, hi = wil(k, n)
        body.append(f'<line x1="{sx(lo):.1f}" y1="{y:.1f}" x2="{sx(hi):.1f}" y2="{y:.1f}" '
                    f'stroke="{col}" stroke-width="8" stroke-opacity="0.22" stroke-linecap="round"/>')
        body.append(f'<circle cx="{sx(r):.1f}" cy="{y:.1f}" r="6" fill="{col}" stroke="{P.SURFACE}" stroke-width="2"/>')
        body.append(P.txt(L+pw+14, y+4, f"{r:>5.1%}   {r/base:>4.1f}x base   n={n:,}", size=11, fill=P.INK2, tab=True))
    # A plain word: the arrow glyph rendered as a tofu box under the fallback font.
    body.append(P.txt(L+pw+14, T+step*0.5-13, "suspect, see footer", size=10,
                      fill=P.FIELD_COLOR["image-gen"]))
    top = rows[0]
    foot = [f"Best case reaches {top[0]:.1%} — so {1-top[0]:.0%} of even those papers are never used.",
            "And stars are counted AFTER adoption, so that bucket is partly the outcome itself.",
            "The tell: a mid-sized repo scores BELOW having no repo. A real signal does not reverse mid-range."]
    print(P.write("1-no-predictor.svg", P.frame(W, H, "Nothing about a paper predicts whether a model will use it",
        "Every feature available when a paper is published, against the 0.8% of papers that are ever adopted.",
        body, foot, chars=96)))

main()
