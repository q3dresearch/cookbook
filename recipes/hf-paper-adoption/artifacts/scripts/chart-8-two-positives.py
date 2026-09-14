#!/usr/bin/env python3
"""The label a funding model would need, and how many examples of it exist.

Everything prescriptive in this recipe eventually wants to say "back papers that look
like X". That requires a training label: papers that demonstrably got adopted by
someone who did not write them. This counts how many of those there are.

**Two.** Across 15,890 papers and three and a half years of Hugging Face's curated
daily feed, two are named on the model cards of two independent organisations, and
**both of them look like undeclared redistribution on inspection**:

- *Gemma 3 Technical Report* -- `google/gemma-3-270m` and
  `Infomaniak-AI/vllm-translategemma-4b-it`. The second is plainly a Gemma derivative
  and declares no `base_model:` at all, so the filter cannot see it.
- *DINOv3* -- `facebook/dinov3-*` and `timm/vit_small_patch16_dinov3.lvd1689m`, which
  is timm hosting the same weights.

So two is an upper bound that does not survive looking at the two. The recipe already
warns that 611 models declare no `base_model:` and that the filter therefore removes
only the derivatives that say they are derivatives; this is what that warning costs.

The attrition is drawn twice because the two chains fail at different steps:

- **the feed chain** -- what an allocator could actually have funded -- loses 99.2% at
  the first step, because being on the feed and being implemented are largely
  different populations (Q12: 70% of adopted papers were never on the feed at all).
- **the model-tag chain** -- every paper any top-1,000 model cites, feed or not --
  survives its first step far better and then loses three quarters of what is left to
  *redistribution*: quantized re-uploads inherit the original card's arxiv tags and
  vote again.

**The gap between 21 and 2 is the whole problem.** Both chains reach 21 papers with
two or more orgs, and the feed chain keeps 2 of them once derivative uploads are
removed. The 19 that survive in the model-tag chain and not the feed chain are older
than the feed: ViT, BERT, ResNet, CLIP and the rest predate 2023-05-04 and could never
have appeared on it.

**So this is not a lag that patience fixes.** A reader could assume the recent
quarters are simply too young, and the quarterly series says otherwise: the
independent-adoption rate is 0.00% in *every* quarter of the feed's existence, the two
survivors falling in 2025Q1 and 2025Q3. Waiting produces more of chain B, whose
members were never fundable through this feed.

**What to do instead is the point of `7-budget`**: score on "named by anyone", accept
that it is mostly a lab citing itself, and use it to shrink a haystack rather than to
pick a winner.
"""
import sys, collections, math
sys.path.insert(0, ".")
import paperlib as P
from adoption import ALIASES


def main():
    f = P.feed(); ms = P.models()
    cited, allorg, indep = set(), collections.defaultdict(set), collections.defaultdict(set)
    for m in ms:
        o = ALIASES.get(m["id"].split("/")[0], m["id"].split("/")[0])
        for a in P.arxiv_ids(m):
            cited.add(a); allorg[a].add(o)
            if not P.foreign_base(m): indep[a].add(o)
    onfeed = [k for k in f if k in cited]

    chains = [
        ("the feed chain — what an allocator could have funded", P.HOT, [
            (len(f),                                                  "on the daily feed"),
            (len(onfeed),                                             "named by a top-1,000 model"),
            (sum(1 for k in onfeed if len(allorg[k]) >= 2),            "named by two or more orgs"),
            (sum(1 for k in onfeed if len(indep[k]) >= 2),             "two INDEPENDENT orgs"),
        ]),
        ("the model-tag chain — every paper a top-1,000 model cites", P.COOL, [
            (len(cited),                                              "cited by a top-1,000 model"),
            (sum(1 for a in cited if len(allorg[a]) >= 2),             "two or more orgs"),
            (sum(1 for a in cited if len(indep[a]) >= 2),              "two INDEPENDENT orgs"),
        ]),
    ]

    W, H, L, R, T = 940, 496, 96, 60, 182
    pw = W - L - R
    lo, hi = math.log10(1.5), math.log10(20000)
    sx = lambda v: L + (math.log10(max(v, 1.6)) - lo)/(hi - lo)*pw
    body = []
    for g in (2, 10, 100, 1000, 10000):
        body.append(f'<line x1="{sx(g):.1f}" y1="{T-50:.1f}" x2="{sx(g):.1f}" y2="{T+196:.1f}" '
                    f'stroke="{P.GRID}" stroke-width="1"/>')
        body.append(P.txt(sx(g), T-58, f"{g:,}", size=11, fill=P.MUTED, anchor="middle", tab=True))
    body.append(P.txt(L, T-78, "papers surviving the filter   (log scale)", size=12, fill=P.INK2))

    y = T
    for title, col, steps in chains:
        body.append(P.txt(28, y - 38, title, size=11.5, fill=P.INK, weight="600"))
        body.append(f'<line x1="{sx(steps[0][0]):.1f}" y1="{y:.1f}" x2="{sx(steps[-1][0]):.1f}" '
                    f'y2="{y:.1f}" stroke="{col}" stroke-width="1.6" stroke-opacity="0.35"/>')
        for i, (n, label) in enumerate(steps):
            x = sx(n)
            body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{col}" '
                        f'fill-opacity="{0.9 if i == len(steps)-1 else 0.28}" stroke="{col}" stroke-width="1.8"/>')
            body.append(P.txt(x, y - 15, f"{n:,}", size=13, fill=col, anchor="middle",
                              weight="600", tab=True))
            # labels alternate above/below the count so the dense right-hand end stays legible
            body.append(P.txt(x, y + 26 if i % 2 == 0 else y + 42, label, size=10.5,
                              fill=P.MUTED, anchor="middle"))
            if i % 2:
                body.append(f'<line x1="{x:.1f}" y1="{y+8:.1f}" x2="{x:.1f}" y2="{y+31:.1f}" '
                            f'stroke="{P.GRID}" stroke-width="1"/>')
        y += 150

    foot = ["Two papers in three and a half years clear the bar the word 'adoption' implies. A rule trained on "
            "that label has two positive examples.",
            "The feed chain loses 99.2% at step one — curated and implemented are different populations. The "
            "model-tag chain loses three quarters to redistribution.",
            "Not a lag that patience fixes: the independent-adoption rate is 0.00% in every quarter of the "
            "feed's existence.",
            "The 19 papers chain B keeps and chain A cannot are older than the feed itself — ViT, BERT, ResNet "
            "and CLIP all predate 2023-05-04.",
            "Top-1,000-by-download listing only, so adoption by models nobody downloads is invisible here."]
    print(P.write("8-two-positives.svg", P.frame(
        W, H, "The label a funding rule would need has two examples",
        "Attrition from two starting populations to the papers named by two organisations that are not "
        "redistributing each other's models.", body, foot, chars=122)))


main()
