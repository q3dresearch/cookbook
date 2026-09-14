#!/usr/bin/env python3
"""Where a technique lands when everybody uses it and nobody names it.

Every paper a top-1,000 model cites, counted by how many *independent* organisations
name it -- derivative re-uploads dropped, same-company namespaces merged. The shape is
the finding: **the overwhelming majority sit at one organisation**, which is the lab
that wrote the paper citing itself.

**LoRA is the paper to look at.** `2106.09685` is plausibly the most widely used
technique in the entire ecosystem -- the standard way people finetune anything -- and
in this listing it sits at **one organisation and one model**, indistinguishable from a
paper nobody has heard of. Two structural reasons, neither fixable by better code:

- LoRA adapters are small, numerous and long-tail. They are not in the download head,
  and this is the download head.
- A model finetuned with LoRA does not usually cite the LoRA paper. The tag records
  what an uploader chose to write on a card, not what the training run did.

So the honest scope line is narrower than "which research ideas ship". **This measures
which papers the uploaders of already-popular models chose to name.** A technique can
be universal and invisible here, and LoRA is the example anyone can check in a minute.

The named papers are placed at their actual counts, so the distribution and the
examples are the same measurement rather than a bar chart with anecdotes bolted on.
"""
import sys, collections, json
sys.path.insert(0, ".")
import paperlib as P
from adoption import ALIASES

MARK = {"2106.09685": ("LoRA", "plausibly the most-used technique in the ecosystem"),
        "1910.09700": ("carbon-emissions boilerplate", "a model-card template field, not an implementation"),
        "1810.04805": ("BERT", None), "2010.11929": ("ViT", None),
        "1907.11692": ("RoBERTa", None), "1512.03385": ("ResNet", None)}


def main():
    ms = P.models()
    indep = collections.defaultdict(set)
    for m in ms:
        if P.foreign_base(m): continue
        o = ALIASES.get(m["id"].split("/")[0], m["id"].split("/")[0])
        for a in P.arxiv_ids(m): indep[a].add(o)
    cited = set()
    for m in ms: cited |= P.arxiv_ids(m)
    counts = collections.Counter(len(indep.get(a, ())) for a in cited)
    ks = sorted(counts)

    W, L, R, T, B = 940, 92, 300, 190, 168
    PH = 300
    H = T + PH + B
    pw = W - L - R
    mx = max(counts.values())*1.1
    bw = pw/len(ks)
    sy = lambda v: T + PH - v/mx*PH
    body = []
    for g in (0, 100, 200, 300):
        if g > mx: continue
        body.append(f'<line x1="{L}" y1="{sy(g):.1f}" x2="{L+pw:.1f}" y2="{sy(g):.1f}" '
                    f'stroke="{P.INK if g == 0 else P.GRID}" stroke-width="{1.3 if g == 0 else 1}"/>')
        body.append(P.txt(L-10, sy(g)+4, g, size=11, fill=P.MUTED, anchor="end", tab=True))
    for i, k in enumerate(ks):
        x = L + bw*i
        n = counts[k]
        col = P.HOT if k <= 1 else P.COOL
        body.append(f'<rect x="{x+bw*0.16:.1f}" y="{sy(n):.1f}" width="{bw*0.68:.1f}" '
                    f'height="{T+PH-sy(n):.1f}" rx="2" fill="{col}" fill-opacity="0.85"/>')
        body.append(P.txt(x+bw/2, sy(n)-8, n, size=11.5, fill=col, anchor="middle", weight="600", tab=True))
        body.append(P.txt(x+bw/2, T+PH+20, k, size=12, fill=P.INK, anchor="middle", tab=True))
    body.append(P.txt(L+pw/2, T+PH+44, "independent organisations naming the paper", size=12,
                      fill=P.INK2, anchor="middle"))
    body.append(P.txt(L+pw/2, T+PH+60, "categorical — only these counts occur, so the gap between 3 and 10 is "
                      "not a distance", size=9.5, fill=P.MUTED, anchor="middle"))
    body.append(P.txt(L-10, T-44, f"papers, of the {len(cited)} that any top-1,000 model cites", size=12, fill=P.INK2))
    one = counts[0]+counts[1]
    body.append(P.txt(L-10, T-26, f"{one} of {len(cited)} — {one*100//len(cited)}% — are named by one organisation "
                      f"or none: the lab citing itself", size=11, fill=P.HOT))

    ty = T + 10
    body.append(P.txt(L+pw+22, ty, "where the famous ones land", size=11.5, fill=P.INK, weight="600"))
    ty += 20
    for aid, (lab, note) in MARK.items():
        if aid not in cited: continue
        n = len(indep.get(aid, ()))
        col = P.HOT if n <= 1 else P.COOL
        body.append(P.txt(L+pw+22, ty, f"{n}", size=12, fill=col, weight="600", tab=True))
        body.append(P.txt(L+pw+42, ty, lab, size=11, fill=P.INK2))
        ty += 14
        if note:
            wrapped, dy = P.para(L+pw+42, ty, note, size=9.5, fill=P.MUTED, chars=28)
            body += wrapped; ty += dy
        ty += 8

    foot = [f"{one*100//len(cited)}% of cited papers reach one organisation or none. An arXiv tag is overwhelmingly "
            f"a lab citing its own paper.",
            "LoRA sits in the '1' bar, indistinguishable from a paper nobody has heard of: its adapters are "
            "long-tail so they miss the download head, and a LoRA finetune rarely cites the LoRA paper.",
            "The carbon-emissions paper sits high not because anyone implemented it but because it is a field in "
            "Hugging Face's model-card template.",
            "So this measures which papers the uploaders of already-popular models chose to name. A technique can "
            "be universal and invisible here."]
    print(P.write("17-invisible-technique.svg", P.frame(
        W, H, "A technique can be universal and still register once",
        "Papers cited by a top-1,000 model, by how many independent organisations name them.",
        body, foot, chars=124)))


main()
