#!/usr/bin/env python3
"""The papers everything is built on, and the ones no model card ever names.

Two counts per paper. How many of the 424 recovered bibliographies cite it -- what the
literature actually rests on. And how many of the top-1,000 model cards name it -- what
the forward-looking measurement can see.

**They disagree completely at the top.** Attention Is All You Need is cited by 173 of
424 bibliographies and named by zero model cards. AdamW by 74 and zero. An optimizer
and a transformer architecture underpin the field and are invisible to every
adoption measure in this recipe, because a model card names the model you started
from, not the mathematics you used.

**Matching is by hand-verified arXiv id, not by title.** A `.bbl` cites venues far
more often than arXiv numbers -- ViT's 58 entries carry four -- so the ids below were
looked up one at a time. An earlier attempt matched titles through the daily feed,
which only reaches back to 2023 and therefore declared every pre-2023 paper invisible
including ones that are plainly named. The ids are the fix; the list is short because
hand-verification does not scale.
"""
import sys, collections, json, math
sys.path.insert(0, ".")
import paperlib as P
from ancestors import norm, MAX_REFS, JUNK, is_venue

# Hand-verified. Papers with no arXiv id at all (GPT-2, Natural Questions) are omitted
# rather than guessed at.
IDS = {
    "attention is all you need": ("1706.03762", "Attention Is All You Need"),
    "bert": ("1810.04805", "BERT"),
    "language models are few-shot learners": ("2005.14165", "GPT-3"),
    "exploring the limits of transfer learning with a unified text": ("1910.10683", "T5"),
    "decoupled weight decay regularization": ("1711.05101", "AdamW"),
    "learning transferable visual models from natural language supervision": ("2103.00020", "CLIP"),
    "roberta": ("1907.11692", "RoBERTa"),
    "measuring massive multitask language understanding": ("2009.03300", "MMLU"),
    "an image is worth 16x16 words": ("2010.11929", "ViT"),
    "llama": ("2302.13971", "LLaMA"),
    "evaluating large language models trained on code": ("2107.03374", "Codex / HumanEval"),
    "microsoft coco": ("1405.0312", "MS COCO"),
    "llama 2": ("2307.09288", "Llama 2"),
    "deep residual learning for image recognition": ("1512.03385", "ResNet"),
    "roformer": ("2104.09864", "RoPE"),
    "visual instruction tuning": ("2304.08485", "LLaVA"),
    "glue": ("1804.07461", "GLUE"),
    "measuring mathematical problem solving with the math dataset": ("2103.03874", "MATH"),
    "adam": ("1412.6980", "Adam"),
}

def main():
    raw = json.loads((P.RAW / "bibliographies.json").read_text())
    bib = {k: [r for r in v if not any(j in r.lower() for j in JUNK) and not is_venue(r)]
           for k, v in raw.items() if v and len(v) <= MAX_REFS}
    anc = collections.Counter()
    for refs in bib.values():
        for r in refs:
            t = norm(r)
            if len(t) >= 12: anc[t] += 1
    cards = collections.Counter()
    for m in P.models():
        for a in P.arxiv_ids(m): cards[a] += 1
    pts = []
    for key, (aid, label) in IDS.items():
        n = max((v for t, v in anc.items() if t.startswith(key[:26])), default=0)
        if n >= 15: pts.append((n, cards.get(aid, 0), label))
    W, H, L, R, T, B = 900, 510, 82, 58, 140, 116
    pw, ph = W-L-R, H-T-B
    mxx = max(p[0] for p in pts)*1.15
    sx = lambda v: L + v/mxx*pw
    sy = lambda v: T + ph - math.log10(v+1)/math.log10(max(p[1] for p in pts)+1.6)*ph
    body = []
    mxc = max(p[1] for p in pts)
    for g in (0, 1, 3, 10, 30):
        if g > mxc: continue          # a gridline above the data drew through the title
        y = sy(g)
        body.append(f'<line x1="{L}" y1="{y:.1f}" x2="{L+pw:.1f}" y2="{y:.1f}" '
                    f'stroke="{P.INK if g==0 else P.GRID}" stroke-width="{1.4 if g==0 else 1}"/>')
        body.append(P.txt(L-10, y+4, g, size=11, fill=P.MUTED, anchor="end", tab=True))
    for g in (0, 50, 100, 150):
        x = sx(g)
        body.append(f'<line x1="{x:.1f}" y1="{T}" x2="{x:.1f}" y2="{T+ph:.1f}" stroke="{P.GRID}" stroke-width="1"/>')
        body.append(P.txt(x, T+ph+20, g, size=11, fill=P.MUTED, anchor="middle", tab=True))
    body.append(P.txt(L+pw/2, T+ph+44, "bibliographies citing it   (of 424 papers)", size=12, fill=P.INK2, anchor="middle"))
    body.append(P.txt(L-10, T-16, "model cards naming it   (log)", size=12, fill=P.INK2))
    placed = []
    for n, c, lab in sorted(pts, key=lambda p: -p[0]):
        x, y = sx(n), sy(c)
        col = P.FIELD_COLOR["image-gen"] if c == 0 else P.FIELD_COLOR["LLM-core"]
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6.5" fill="{col}" fill-opacity="0.9" '
                    f'stroke="{P.SURFACE}" stroke-width="1.6"/>')
        # Dodge AWAY from the nearer edge. Always dodging up walked the top cluster
        # straight through the chart title.
        step = 15 if y < T + ph*0.45 else -15
        ty = y + (17 if step > 0 else -13)
        while any(abs(x-px) < 82 and abs(ty-py) < 15 for px, py in placed): ty += step
        placed.append((x, ty))
        body.append(P.txt(x, ty, lab, size=11.5, fill=col, anchor="middle", weight="600"))
    inv = [p for p in pts if p[1] == 0]
    foot = [f"Orange sits on the zero line: {len(inv)} of these {len(pts)} foundational papers are named by no model "
            f"card at all, including the two most-depended-on in the corpus.",
            "A model card names the model you started from, not the optimizer, the architecture, or the benchmark you used.",
            "Every adoption measure built on those cards is therefore blind to exactly the ideas that carry the field."]
    print(P.write("5-invisible.svg", P.frame(W, H, "What the field rests on, and what a model card can see",
        "Papers by how many recovered bibliographies cite them against how many model cards name them.",
        body, foot, chars=104)))

main()
