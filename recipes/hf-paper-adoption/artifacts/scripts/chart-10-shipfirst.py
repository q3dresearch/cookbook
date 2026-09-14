#!/usr/bin/env python3
"""How often the artifact precedes the paper -- and the null that sits beside it.

**Retraction, 2026-09-14.** The first version of this chart plotted median lag against
the share of model-first pairs as a two-axis scatter, and reported that "embeddings
reach a model in 7 months, vision in 18". Both moves were wrong.

**The two axes were the same number twice.** The y-axis is the share of a field's lags
below zero; the x-axis is the median of those same lags. A field with a quarter of its
mass negative is forced to a lower median, so the axes correlated at **r = -0.86** by
construction, two of the four quadrants were empty for arithmetic reasons, and a 1-D
result was drawn as 2-D.

**And the field-speed claim did not survive decoupling.** Take the wait among only the
pairs where the paper genuinely came first and every field lands in the same place:

    LLM-core 20   embedding 22   vision 21   speech 25   time-series 23   image-gen 21

A five-month spread across six fields with heavily overlapping quartiles -- not the 2.5x
the scatter showed. The apparent speed difference was the model-first pairs dragging
the median down. It measured **how often the paper is documentation**, not how fast a
field moves.

So there is one finding and one null, and both are drawn here:

- **The finding.** The share of model-first pairs is a real and large field
  difference: 26% in time-series and 24% in embeddings against 1.2% in vision and 0%
  in image-generation. Some fields ship and then write.
- **The null.** Once the paper comes first, the wait is ~21 months everywhere. The
  grey line is the pooled positive median and every field's own median sits within
  four months of it.

A distribution strip carries both and cannot fake a second dimension: the negative mass
plainly differs between rows while the positive bulk sits under the same line.

**Caveats unchanged.** Measured on models in the top 1,000 by download, so this is the
wait among models that succeeded. Fields come from `pipeline_tag`, which has no value
for agents or reinforcement learning -- those ship as `text-generation` and are pooled
into LLM-core. 1.9% of pairs run past 84 months and are drawn pinned at the edge.
"""
import sys, collections, statistics
sys.path.insert(0, ".")
import paperlib as P

LO, HI = -24, 84


def main():
    lag = collections.defaultdict(list)
    for m in P.models():
        c = m.get("createdAt"); fl = P.FIELD_TAG.get(m.get("pipeline_tag"))
        if not c or not fl: continue
        cm = int(c[:4])*12 + int(c[5:7])
        for a in P.arxiv_ids(m):
            pm = P.pub_month(a)
            if pm and -24 <= cm-pm <= 180: lag[fl].append(cm-pm)
    pooled = statistics.median([x for v in lag.values() for x in v if x > 0])
    order = sorted(lag, key=lambda f: -sum(1 for x in lag[f] if x < 0)/len(lag[f]))

    RH, W, L, R, T = 74, 940, 168, 118, 196
    H = T + RH*len(order) + 128
    pw = W - L - R
    sx = lambda v: L + (min(max(v, LO), HI)-LO)/(HI-LO)*pw
    body = []
    for g in range(LO, HI+1, 12):
        x = sx(g)
        body.append(f'<line x1="{x:.1f}" y1="{T-40:.1f}" x2="{x:.1f}" y2="{T+RH*len(order)-14:.1f}" '
                    f'stroke="{P.INK if g == 0 else P.GRID}" stroke-width="{1.6 if g == 0 else 1}"/>')
        body.append(P.txt(x, T-48, g, size=11, fill=P.INK2 if g == 0 else P.MUTED, anchor="middle", tab=True))
    body.append(f'<rect x="{sx(LO):.1f}" y="{T-40:.1f}" width="{sx(0)-sx(LO):.1f}" '
                f'height="{RH*len(order)-14-(T-40)+T:.1f}" fill="{P.HOT}" fill-opacity="0.05"/>')
    body.append(P.txt(sx(0)-8, T-72, "<- model first", size=11, fill=P.HOT, anchor="end", weight="600"))
    body.append(P.txt(sx(0)+8, T-72, "paper first ->", size=11, fill=P.COOL, weight="600"))
    body.append(P.txt(L+pw/2, T+RH*len(order)+14, "months between the paper and the model that cites it",
                      size=12, fill=P.INK2, anchor="middle"))
    # the null, drawn once and spanning every row
    body.append(f'<line x1="{sx(pooled):.1f}" y1="{T-40:.1f}" x2="{sx(pooled):.1f}" '
                f'y2="{T+RH*len(order)-14:.1f}" stroke="{P.INK2}" stroke-width="1.6" stroke-dasharray="5 4"/>')
    body.append(P.txt(sx(pooled), T-94, f"pooled median once the paper is first: {pooled:.0f} months",
                      size=11, fill=P.INK2, weight="600", anchor="middle"))

    import random
    for i, fl in enumerate(order):
        v = lag[fl]
        y = T + RH*i + RH/2 - 14
        neg = sum(1 for x in v if x < 0)
        pos = [x for x in v if x > 0]
        med = statistics.median(pos)
        rng = random.Random(hash(fl) & 0xffff)
        body.append(f'<line x1="{L}" y1="{y-RH/2+6:.1f}" x2="{L+pw:.1f}" y2="{y-RH/2+6:.1f}" '
                    f'stroke="{P.RULE}" stroke-width="1"/>')
        for x in v:
            jy = y + rng.uniform(-17, 17)
            col = P.HOT if x < 0 else P.COOL
            body.append(f'<circle cx="{sx(x):.1f}" cy="{jy:.1f}" r="2.4" fill="{col}" fill-opacity="0.45"/>')
        body.append(f'<line x1="{sx(med):.1f}" y1="{y-21:.1f}" x2="{sx(med):.1f}" y2="{y+21:.1f}" '
                    f'stroke="{P.INK}" stroke-width="2.2"/>')
        body.append(P.txt(L-16, y-4, fl, size=12.5, fill=P.INK, anchor="end", weight="600"))
        body.append(P.txt(L-16, y+12, f"{len(v)} pairs", size=10.5, fill=P.MUTED, anchor="end"))
        pct = neg/len(v)*100
        body.append(P.txt(L+pw+12, y-4, f"{pct:.0f}%", size=13, fill=P.HOT if pct >= 10 else P.MUTED,
                          weight="600", tab=True))
        body.append(P.txt(L+pw+12, y+12, "model first", size=10, fill=P.MUTED))
        body.append(P.txt(sx(med), y-26, f"{med:.0f}", size=10.5, fill=P.INK, anchor="middle", tab=True))

    foot = ["Black ticks are each field's median once the paper comes first. They land within four months of each "
            "other and of the pooled line — that is the null.",
            "The field difference is the orange mass left of zero — the model created BEFORE the paper it cites, "
            "so the paper documents what already shipped.",
            "This replaces a scatter whose two axes were the same distribution counted twice (r = -0.86), and "
            "which reported a 2.5x field speed difference that decoupling removes.",
            "Top-1,000-by-download listing, so this is the wait among models that succeeded. Agents and RL have "
            "no pipeline_tag and sit inside LLM-core.",
            "1.9% of pairs run past 84 months and are drawn pinned at the right edge."]
    print(P.write("10-shipfirst.svg", P.frame(
        W, H, "Where the artifact comes first — and the wait that does not differ",
        "Every (model, paper) pair by the months between them, one row per field. One dot is one pair.",
        body, foot, chars=126)))


main()
