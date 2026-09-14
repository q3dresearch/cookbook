#!/usr/bin/env python3
"""The thousand models are not a thousand opinions.

Every adoption rate in this recipe is counted from the top-1,000 models by download.
That listing is not a thousand independent judgements about a paper. Qwen alone
publishes 114 of the 1,000, and each of its cards repeats the same citation list.

Plotted here: for each publisher, how many models it has in the listing against how
many DISTINCT papers it cites. A publisher on the diagonal brings a new reference for
every model. One that flattens is shipping variants -- the same decision, counted
again.

This is why `orgs_implementing` exists in the archive's parser and why it, not the
model count, is the honest unit. An earlier version of this chart set counted models
anyway, which inflated every field's payoff by 2.1x on average and silently reordered
the middle of the ranking.
"""
import sys, collections, math
sys.path.insert(0, ".")
import paperlib as P

def main():
    ms = P.models()
    mods = collections.Counter(); papers = collections.defaultdict(set)
    for m in ms:
        o = m["id"].split("/")[0]
        mods[o] += 1
        papers[o] |= P.arxiv_ids(m)
    pts = [(mods[o], len(papers[o]), o) for o in mods if mods[o] >= 5]
    W, H, L, R, T, B = 860, 500, 76, 66, 116, 142
    pw, ph = W-L-R, H-T-B
    mxx = max(p[0] for p in pts)*1.25; mxy = max(p[1] for p in pts)*1.25
    sx = lambda v: L + math.log10(max(v,1))/math.log10(mxx)*pw
    sy = lambda v: T + ph - math.log10(max(v,1)+1)/math.log10(mxy+1)*ph
    body = []
    for g in (1, 3, 10, 30, 100):
        if g <= mxy:
            y = sy(g)
            body.append(f'<line x1="{L}" y1="{y:.1f}" x2="{L+pw:.1f}" y2="{y:.1f}" stroke="{P.GRID}" stroke-width="1"/>')
            body.append(P.txt(L-10, y+4, g, size=11, fill=P.MUTED, anchor="end", tab=True))
        if g <= mxx:
            x = sx(g)
            body.append(f'<line x1="{x:.1f}" y1="{T}" x2="{x:.1f}" y2="{T+ph:.1f}" stroke="{P.GRID}" stroke-width="1"/>')
            body.append(P.txt(x, T+ph+20, g, size=11, fill=P.MUTED, anchor="middle", tab=True))
    # the one-new-paper-per-model line: anything below it is repetition
    dl = " ".join(f"{sx(v):.1f},{sy(v):.1f}" for v in range(1, int(mxx)+1))
    body.append(f'<polyline points="{dl}" fill="none" stroke="{P.BASELINE}" stroke-width="1.4" stroke-dasharray="5 4"/>')
    body.append(P.txt(sx(2.2), sy(2.2)-10, "one new paper per model", size=10.5, fill=P.MUTED))
    body.append(P.txt(L+pw/2, T+ph+44, "models this publisher has in the top 1,000   (log)", size=12, fill=P.INK2, anchor="middle"))
    body.append(P.txt(L-10, T-16, "distinct papers it cites   (log)", size=12, fill=P.INK2))
    NAME = {"Qwen", "google", "unsloth", "nvidia", "facebook", "microsoft", "lmstudio-community", "sentence-transformers"}
    placed = []
    for mm, pp, o in sorted(pts, key=lambda p: -p[0]):
        x, y = sx(mm), sy(pp)
        big = o in NAME
        col = P.FIELD_COLOR["image-gen"] if (mm >= 20 and pp < mm*0.5) else P.FIELD_COLOR["LLM-core"]
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{6 if big else 3.4}" fill="{col}" '
                    f'fill-opacity="{0.9 if big else 0.3}"'
                    + (f' stroke="{P.SURFACE}" stroke-width="1.6"' if big else '') + '/>')
        if big:
            # nvidia / microsoft / facebook sit almost on top of each other; alternate
            # the label above and below rather than letting three names overprint.
            # Track LABEL positions, not dot positions: microsoft and facebook sit at
            # 27 models each, so dodging both relative to the dots put them in the same
            # place. Walk the label down until it clears everything already drawn.
            ty = y - 14
            while any(abs(x-px) < 92 and abs(ty-py) < 17 for px, py in placed):
                ty += 17
            placed.append((x, ty))
            sy_ = ty + 36 if ty < y else ty + 14
            body.append(P.txt(x, ty, o, size=11.5, fill=col, anchor="middle", weight="600"))
            body.append(P.txt(x, sy_, f"{mm} models · {pp} papers", size=10, fill=P.MUTED, anchor="middle", tab=True))
    tot_m = sum(mods.values()); citing = sum(1 for o in papers if papers[o])
    foot = [f"{len(ms):,} models, {len(mods)} publishers, and only {citing} of them cite anything at all.",
            f"Qwen alone is {mods['Qwen']} models citing {len(papers['Qwen'])} distinct papers — one decision, "
            f"repeated {mods['Qwen']//max(1,len(papers['Qwen']))}x over.",
            "Orange marks publishers citing fewer than one paper per two models.",
            "Counting models rather than publishers inflates every rate by 2.1x and reorders the field ranking."]
    print(P.write("2-denominator.svg", P.frame(W, H, "A thousand models are not a thousand opinions",
        "Each publisher by how many models it has in the listing and how many distinct papers those models cite.",
        body, foot, chars=100)))

main()
