#!/usr/bin/env python3
"""What the field builds on, against what the adoption metric is able to credit.

`chart-5-invisible` makes this point on 19 hand-picked papers and one binary: named
on a model card, or not. This is the same measurement carried to the whole head of
the canon and scored on the unit the rest of the recipe uses -- **independent
organisations**, after foreign `base_model:` derivatives and same-company aliases are
removed, exactly as `adoption.py` does it.

Three results, and the second is the one worth the chart:

**Nineteen of the thirty-nine most-depended-on papers in the corpus have zero
independent adopters.** Attention Is All You Need, Adam, AdamW, PyTorch, the
Transformers library, BPE, chain-of-thought, the scaling laws and Chinchilla are the
substrate the field is written on and the metric cannot see any of them.

**Where the metric does see a benchmark, it is one lab's eval list.** MMLU, MATH,
GSM8K, HellaSwag, WinoGrande, PIQA, MBPP, SQuAD, MultiNLI and HumanEval each read
exactly one independent org, and it is **the same org every time** -- Google, because
Gemma-3's model card lists its evaluation suite. Ten separate "adoptions" are one
card. Counted in models rather than orgs they read 7 each and look like a trend.

**Only five papers clear two independent orgs**: BERT, CLIP, RoBERTa, ViT, ResNet --
the encoders and vision backbones the recipe's stable core already consists of.

So the prescription is not "watch for undervalued papers". It is that a whole
*category* of work -- optimizers, libraries, tokenizers, training recipes, benchmarks
-- is structurally uncreditable by any measure built on model cards, because a card
names the model you started from. Anyone allocating on adoption numbers is allocating
against infrastructure by construction, and the gap is not noise to be corrected but a
blind spot to be funded around.

**Ids are hand-verified, as in chart 5.** A canon entry whose arXiv id cannot be
confirmed is omitted, never scored zero: 20 of the referenced ids are missing from the
title cache, so absence from it is not evidence of absence from a card. Papers with no
arXiv id at all (GPT-2, GPT-1, ImageNet, Natural Questions) are left out for the same
reason, and all four would sit in the zero band.

**Counts are bibliographies, deduplicated.** A `.bbl` that cites a paper twice votes
once here; chart 5 does not dedup, which is why it reads 173 for Attention and this
reads 165.
"""
import sys, collections, json
sys.path.insert(0, ".")
import paperlib as P
from ancestors import norm, MAX_REFS, JUNK, is_venue
from adoption import ALIASES

# (normalised-title prefix, arXiv id, label, band). Hand-verified ids.
CANON = [
    ("attention is all you need",                    "1706.03762", "Attention Is All You Need", 0),
    ("decoupled weight decay regularization",        "1711.05101", "AdamW", 0),
    ("adam a method for stochastic optimization",    "1412.6980",  "Adam", 0),
    ("transformers state of the art natural",        "1910.03771", "Transformers (library)", 0),
    ("training language models to follow instr",     "2203.02155", "InstructGPT / RLHF", 0),
    ("neural machine translation of rare words",     "1508.07909", "BPE subword units", 0),
    ("chain of thought prompting",                   "2201.11903", "Chain-of-thought", 0),
    ("scaling laws for neural language models",      "2001.08361", "Scaling laws", 0),
    ("training compute optimal large language",      "2203.15556", "Chinchilla", 0),
    ("pytorch an imperative style",                  "1912.01703", "PyTorch", 0),

    ("measuring massive multitask language",         "2009.03300", "MMLU", 1),
    ("evaluating large language models trained on",  "2107.03374", "HumanEval", 1),
    ("microsoft coco common objects",                "1405.0312",  "MS COCO", 1),
    ("glue a multi task benchmark",                  "1804.07461", "GLUE", 1),
    ("measuring mathematical problem solving",       "2103.03874", "MATH", 1),
    ("training verifiers to solve math word",        "2110.14168", "GSM8K", 1),
    ("squad 100 000 questions",                      "1606.05250", "SQuAD", 1),
    ("think you have solved question answering",     "1803.05457", "ARC", 1),
    ("hellaswag can a machine really finish",        "1905.07830", "HellaSwag", 1),
    ("winogrande an adversarial winograd",           "1907.10641", "WinoGrande", 1),
    ("program synthesis with large language",        "2108.07732", "MBPP", 1),
    ("a broad coverage challenge corpus",            "1704.05426", "MultiNLI", 1),
    ("piqa reasoning about physical commonsense",    "1911.11641", "PIQA", 1),
    ("making the v in vqa matter",                   "1612.00837", "VQA v2", 1),
    ("towards vqa models that can read",             "1904.08920", "TextVQA", 1),
    ("docvqa a dataset for vqa on document",         "2007.00398", "DocVQA", 1),

    ("bert pre training of deep bidirectional",      "1810.04805", "BERT", 2),
    ("exploring the limits of transfer learning",    "1910.10683", "T5", 2),
    ("learning transferable visual models",          "2103.00020", "CLIP", 2),
    ("roberta a robustly optimized",                 "1907.11692", "RoBERTa", 2),
    ("an image is worth 16x16 words",                "2010.11929", "ViT", 2),
    ("deep residual learning for image",             "1512.03385", "ResNet", 2),
    ("roformer enhanced transformer",                "2104.09864", "RoPE", 2),
    ("deep contextualized word representations",     "1802.05365", "ELMo", 2),

    ("language models are few shot learners",        "2005.14165", "GPT-3", 3),
    ("llama open and efficient foundation",          "2302.13971", "LLaMA", 3),
    ("llama 2 open foundation",                      "2307.09288", "Llama 2", 3),
    ("the llama 3 herd of models",                   "2407.21783", "Llama 3", 3),
    ("palm scaling language modeling",               "2204.02311", "PaLM", 3),
    ("flamingo a visual language model",             "2204.14198", "Flamingo", 3),
    ("gemini a family of highly capable",            "2312.11805", "Gemini", 3),
    ("visual instruction tuning",                    "2304.08485", "LLaVA", 3),
]
BANDS = ["infrastructure: optimizers, libraries, training recipes",
         "benchmarks and datasets",
         "architectures and encoders",
         "model releases"]


def main():
    raw = json.loads((P.RAW / "bibliographies.json").read_text())
    bib = {k: [r for r in v if not any(j in r.lower() for j in JUNK) and not is_venue(r)]
           for k, v in raw.items() if v and len(v) <= MAX_REFS}
    anc = collections.Counter()
    for refs in bib.values():
        seen = set()
        for r in refs:                      # dedup: one bibliography votes once
            t = norm(r)
            if len(t) >= 12 and t not in seen:
                seen.add(t); anc[t] += 1

    # Credit, on the recipe's standard unit: distinct orgs, foreign-base derivatives
    # dropped, same-company namespaces merged.
    own = collections.defaultdict(set)
    for m in P.models():
        if P.foreign_base(m):
            continue
        o = m["id"].split("/")[0]
        for a in P.arxiv_ids(m):
            own[a].add(ALIASES.get(o, o))

    rows = []
    for pre, aid, label, band in CANON:
        n = max((v for t, v in anc.items() if t.startswith(pre[:26])), default=0)
        if n < 25:
            continue
        rows.append((band, n, len(own.get(aid, set())), label, sorted(own.get(aid, set()))))

    RH, BH = 15.2, 30
    W, L, R, T = 1010, 268, 170, 158
    H = int(T + sum(RH for _ in rows) + BH * len(BANDS) + 150)
    pw = W - L - R
    mx = max(r[1] for r in rows) * 1.06
    sx = lambda v: L + v / mx * pw
    body, y = [], T

    for g in (0, 50, 100, 150):
        body.append(f'<line x1="{sx(g):.1f}" y1="{T-14:.1f}" x2="{sx(g):.1f}" '
                    f'y2="{H-150:.1f}" stroke="{P.GRID}" stroke-width="1"/>')
        body.append(P.txt(sx(g), T - 22, g, size=11, fill=P.MUTED, anchor="middle", tab=True))
    body.append(P.txt(L, T - 46, "bibliographies citing it   (of 424)", size=12, fill=P.INK2))
    body.append(P.txt(W - R + 16, T - 46, "independent orgs", size=12, fill=P.INK2))
    body.append(P.txt(W - R + 16, T - 30, "naming it", size=12, fill=P.INK2))

    for b, name in enumerate(BANDS):
        rs = sorted([r for r in rows if r[0] == b], key=lambda r: -r[1])
        if not rs:
            continue
        y += 20
        body.append(P.txt(28, y, name.upper(), size=10.5, fill=P.MUTED, weight="600"))
        body.append(f'<line x1="28" y1="{y+7:.1f}" x2="{W-28}" y2="{y+7:.1f}" '
                    f'stroke="{P.RULE}" stroke-width="1"/>')
        y += BH - 20
        for _, n, orgs, label, who in rs:
            y += RH
            col = P.HOT if orgs == 0 else P.COOL
            body.append(P.txt(L - 14, y + 4, label, size=11.5, fill=P.INK,
                              anchor="end", weight="600" if orgs == 0 else "normal"))
            body.append(f'<line x1="{L}" y1="{y:.1f}" x2="{sx(n):.1f}" y2="{y:.1f}" '
                        f'stroke="{col}" stroke-width="1" stroke-opacity="0.3"/>')
            body.append(f'<circle cx="{sx(n):.1f}" cy="{y:.1f}" r="4.6" fill="{col}" '
                        f'fill-opacity="{0.25 if orgs == 0 else 0.9}" stroke="{col}" stroke-width="1.5"/>')
            body.append(P.txt(sx(n) + 11, y + 4, n, size=10.5, fill=P.MUTED, tab=True))
            body.append(P.txt(W - R + 34, y + 4, orgs, size=12, fill=col,
                              anchor="middle", weight="600", tab=True))
            if who and orgs <= 1:
                body.append(P.txt(W - R + 46, y + 4, who[0][:13], size=10, fill=P.MUTED))
        y += 6

    zero = sum(1 for r in rows if r[2] == 0)
    two = sum(1 for r in rows if r[2] >= 2)
    foot = [f"{zero} of these {len(rows)} papers have no independent adopter at all — hollow rings. "
            f"Only {two} reach two: BERT, CLIP, RoBERTa, ViT, ResNet.",
            "Every benchmark reading 1 is the SAME org — Google, because Gemma-3's card lists its eval suite. "
            "Ten separate 'adoptions' are one model card.",
            "Counted in models rather than orgs those same ten read 7 apiece and look like a trend.",
            "A model card names the model you started from — not the optimizer, the tokenizer or the benchmark.",
            "Ids hand-verified; a canon paper whose id could not be confirmed is omitted rather than scored zero. "
            "Top-1,000-by-download listing only."]
    print(P.write("6-credit-gap.svg", P.frame(
        W, H, "The field's canon, and the part an adoption metric can credit",
        "The most-depended-on papers across 424 recovered bibliographies, scored on independent organisations "
        "naming them on a model card — derivatives and same-company namespaces removed.",
        body, foot, chars=126)))


main()
