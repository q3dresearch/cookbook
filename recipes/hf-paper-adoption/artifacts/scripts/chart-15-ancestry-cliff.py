#!/usr/bin/env python3
"""The backwards walk can only see papers written before 2022.

**Correction to Q19, 2026-09-14.** The reachability gap was reported as a record-type
effect -- "`type=preprint` returns zero references, `type=conference-paper` returns
38". That is wrong twice. **384 of the 388 resolved seed papers are preprints**, so
the type cannot separate anything, and preprints are not empty: 23% of them carry a
reference list. The `conference-paper` comparison rested on **three papers**.

What actually determines it is the year, and it is not a gradient. It is a cliff:

    2019  89% walkable      2022   0% walkable
    2020  82%               2023   3%
    2021  61%               2024   0%

OpenAlex stopped ingesting reference lists for arXiv preprints after 2021. Before the
cliff most papers are walkable; after it, essentially none are -- **0 of 77 in 2024,
0 of 52 in 2025, 0 of 39 in 2026.**

**This bounds every lineage result in the recipe.** The walk finds BERT in 51 of 94
lineages, then RoBERTa, ResNet, GLUE, GloVe, word2vec, ImageNet -- and that list is old
*by construction*, because nothing newer than 2021 can be walked at all. Q21's real
claim survives, but it must be stated with the cliff attached: **the backwards walk
sees infrastructure the forward view cannot -- no model card ever cites an optimizer --
and it sees only the infrastructure of a closed era.**

A paper published in 2024 has no reachable ancestry here. Whatever the current
generation rests on, this instrument cannot say.

**The fix is a citation source with preprint coverage.** Semantic Scholar has it and
throttles anonymous callers to a 429 on the first request. Until then the cliff is not
a limitation to be noted in passing; it is the finding about the instrument.
"""
import sys, collections, json, pathlib
sys.path.insert(0, ".")
import paperlib as P


def main():
    cache = json.loads((P.RAW / "openalex.json").read_text())
    anc = json.loads((P.RAW / "ancestry.json").read_text())
    ms = P.models(latest_only=False)
    seeds = set()
    for m in ms: seeds |= P.arxiv_ids(m)
    byid = {}
    for v in cache.values():
        if isinstance(v, dict) and v.get("doi") and "arxiv." in v["doi"].lower():
            byid[v["doi"].lower().split("arxiv.")[-1]] = v
    year = collections.defaultdict(lambda: [0, 0])
    for a in seeds:
        v = byid.get(a)
        if not v or not P.pub_month(a): continue
        y = 2000 + int(a.split(".")[0][:2])
        year[y][0] += 1
        if v.get("referenced_works"): year[y][1] += 1
    ys = [y for y in sorted(year) if year[y][0] >= 3]

    W, L, R, T = 940, 84, 250, 182
    PH = 250
    H = T + PH + 164
    pw = W - L - R
    sx = lambda i: L + i/(len(ys)-1)*pw
    sy = lambda v: T + PH - v/100*PH
    body = []
    for g in (0, 25, 50, 75, 100):
        body.append(f'<line x1="{L}" y1="{sy(g):.1f}" x2="{L+pw:.1f}" y2="{sy(g):.1f}" '
                    f'stroke="{P.INK if g == 0 else P.GRID}" stroke-width="{1.3 if g == 0 else 1}"/>')
        body.append(P.txt(L-10, sy(g)+4, f"{g}%", size=11, fill=P.MUTED, anchor="end", tab=True))
    cliff = next(i for i, y in enumerate(ys) if y >= 2022)
    cx = sx(cliff) - (sx(1)-sx(0))/2
    body.append(f'<rect x="{cx:.1f}" y="{T}" width="{L+pw-cx:.1f}" height="{PH}" '
                f'fill="{P.HOT}" fill-opacity="0.06"/>')
    body.append(f'<line x1="{cx:.1f}" y1="{T}" x2="{cx:.1f}" y2="{T+PH:.1f}" '
                f'stroke="{P.INK}" stroke-width="1.5" stroke-dasharray="5 3"/>')
    body.append(P.txt(cx+12, T+PH*0.42, "OpenAlex stops ingesting", size=11.5, fill=P.HOT, weight="600"))
    body.append(P.txt(cx+12, T+PH*0.42+15, "references for arXiv preprints", size=11.5, fill=P.HOT, weight="600"))
    body.append(P.txt(cx+12, T+PH*0.42+31, "everything right of here", size=11, fill=P.HOT))
    body.append(P.txt(cx+12, T+PH*0.42+45, "is unwalkable", size=11, fill=P.HOT))
    pts = [(sx(i), sy(year[y][1]/year[y][0]*100)) for i, y in enumerate(ys)]
    d = " ".join(("M" if i == 0 else "L") + f"{x:.1f} {yy:.1f}" for i, (x, yy) in enumerate(pts))
    body.append(f'<path d="{d}" fill="none" stroke="{P.COOL}" stroke-width="2.6"/>')
    for i, y in enumerate(ys):
        n, k = year[y]
        body.append(f'<circle cx="{pts[i][0]:.1f}" cy="{pts[i][1]:.1f}" r="4.6" fill="{P.COOL}"/>')
        body.append(P.txt(pts[i][0], T+PH+20, y, size=11, fill=P.MUTED, anchor="middle", tab=True))
        body.append(P.txt(pts[i][0], T+PH+34, f"{k}/{n}", size=9.5,
                          fill=P.HOT if k == 0 else P.MUTED, anchor="middle", tab=True))
    body.append(P.txt(L-10, T-44, "share of that year's model-cited papers whose references OpenAlex holds",
                      size=12, fill=P.INK2))
    body.append(P.txt(L-10, T-26, "the whole seed set is preprints — 384 of 388 — so record type explains none of this",
                      size=11, fill=P.MUTED))

    top = anc["ancestors"][:9]
    y0 = T + 4
    body.append(P.txt(L+pw+22, y0-22, f"what the walk finds", size=11.5, fill=P.INK, weight="600"))
    body.append(P.txt(L+pw+22, y0-8, f"in {anc['walkable']} walkable lineages", size=10, fill=P.MUTED))
    for i, r in enumerate(top):
        yy = y0 + 14 + i*23
        body.append(P.txt(L+pw+22, yy, f"{r['n']:>3}", size=11, fill=P.COOL, weight="600", tab=True))
        t = r["title"].split(":")[0].split(",")[0][:22]
        body.append(P.txt(L+pw+46, yy, t, size=10.5, fill=P.INK2))
        yr = r.get("year")
        body.append(P.txt(L+pw+46, yy+10, f"{yr}" + ("  [repaired]" if "repaired" in r else ""),
                          size=9, fill=P.MUTED))

    foot = ["Retracts the stated cause in Q19: 384 of 388 resolved seeds are preprints, 23% of preprints DO carry "
            "references, and the 'conference-paper' case rested on 3 papers.",
            "The real cause is a date cliff: 0 of 77 papers from 2024, 0 of 52 from 2025, 0 of 39 from 2026 are "
            "walkable. Same record type on both sides of it.",
            "So every ancestry result is about a closed era: the walk sees infrastructure no model card cites, and "
            "only the infrastructure of pre-2022 work.",
            "Whatever the 2024-2026 generation rests on, this instrument cannot say. Unblocking it needs a citation "
            "source with preprint coverage."]
    print(P.write("15-ancestry-cliff.svg", P.frame(
        W, H, "The backwards walk can only see papers written before 2022",
        "Of the papers a top-1,000 model cites, the share whose reference list OpenAlex actually holds — by the "
        "year the paper was published.", body, foot, chars=124)))


main()
