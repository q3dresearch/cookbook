#!/usr/bin/env python3
"""This is the computing niche, and no amount of data widens it.

Hugging Face's daily-papers feed is curated AI/ML and nothing else. There is no
category or discipline field in the payload at all, so the check has to be a keyword
scan -- and the scan finds almost nothing from another field.

**What it does find is AI applied to that field, not the field.** Of the papers
mentioning biotech vocabulary, the overwhelming majority also carry an AI/ML term:
*LLaMo: LLM-based Molecular Graph Assistant*, *CellForge: Agentic Design of Virtual
Cell Models*. The scan even over-counts, because a substring like "diagnos" catches
*Diagnosing Metalinguistic Reasoning*.

So this recipe answers **how AI research reaches AI artifacts on one platform.** It
cannot support a sentence about research reaching production in general, and the
temptation to write one should be resisted: the mechanism it measures -- a model card
citing an arXiv id -- does not exist outside software.

**What the analogue needs in another field**, since the question is fair and the answer
is not "no":

| field | paper source | what "shipped" means |
| --- | --- | --- |
| biotech / clinical | bioRxiv, medRxiv, PubMed | trial phase advance, then approval |
| drugs | ClinicalTrials.gov | NCT registration -> phase -> market |
| chemistry / materials | ChemRxiv, arXiv cond-mat | patent citation |
| any discipline | OpenAlex | citations only -- no production signal |

The hard part is not the papers. It is that every field measures "shipped" differently,
and only software hands you a free, dated, public uptake number like a star count.
"""
import sys, collections
sys.path.insert(0, ".")
import paperlib as P

FIELDS = {
    "biotech / bio": ("protein", "genom", "molecul", "cell ", "biolog", "drug discovery",
                      "clinical", "diagnos", "medical", "biomed"),
    "finance": ("financ", "trading", "stock market", "portfolio", "credit risk"),
    "chemistry": ("chemic", "catalys", "molecular dynamics", "reaction predict"),
    "climate / earth": ("climate", "weather forecast", "remote sensing", "atmospher"),
    "physics": ("physics", "quantum mechan", "particle", "astronom", "cosmolog"),
}
AIML = ("llm", "large language model", "transformer", "neural", "deep learning",
        "machine learning", "diffusion model", "foundation model", "fine-tun",
        "pretrain", "embedding", "attention", "benchmark", "dataset", "agent")


def main():
    f = P.feed(one_extractor=False)
    rows = []
    for name, pats in FIELDS.items():
        hits, both, ex = 0, 0, []
        for p in f.values():
            blob = ((p.get("title") or "") + " " + " ".join(p.get("ai_keywords") or [])).lower()
            if any(w in blob for w in pats):
                hits += 1
                if any(w in blob for w in AIML):
                    both += 1
                    if len(ex) < 2 and len(p["title"]) < 70: ex.append(p["title"].replace("\n", " "))
        rows.append((name, hits, both, ex))
    rows.sort(key=lambda r: -r[1])
    n = len(f)

    W, L, R, T = 940, 176, 300, 190
    RH = 62
    H = T + RH*len(rows) + 152
    pw = W - L - R
    mx = max(r[1] for r in rows)/n*100*1.25
    sx = lambda v: L + v/mx*pw
    body = []
    for g in (0, 1, 2, 3, 4):
        if g > mx: continue
        body.append(f'<line x1="{sx(g):.1f}" y1="{T-12:.1f}" x2="{sx(g):.1f}" y2="{T+RH*len(rows)-18:.1f}" '
                    f'stroke="{P.GRID}" stroke-width="1"/>')
        body.append(P.txt(sx(g), T-20, f"{g}%", size=11, fill=P.MUTED, anchor="middle", tab=True))
    body.append(P.txt(L, T-42, f"share of the {n:,} papers mentioning the field's vocabulary at all",
                      size=12, fill=P.INK2))
    for i, (name, hits, both, ex) in enumerate(rows):
        y = T + RH*i + 18
        body.append(f'<rect x="{L}" y="{y-9:.1f}" width="{sx(hits/n*100)-L:.1f}" height="18" rx="2.5" '
                    f'fill="{P.MUTED}" fill-opacity="0.3"/>')
        body.append(f'<rect x="{L}" y="{y-9:.1f}" width="{sx(both/n*100)-L:.1f}" height="18" rx="2.5" '
                    f'fill="{P.HOT}" fill-opacity="0.8"/>')
        body.append(P.txt(L-16, y+5, name, size=12, fill=P.INK, anchor="end", weight="600"))
        body.append(P.txt(sx(hits/n*100)+12, y+5, f"{hits/n*100:.1f}%", size=11.5,
                          fill=P.INK2, weight="600", tab=True))
        body.append(P.txt(sx(hits/n*100)+62, y+5, f"{both*100//max(hits,1)}% also AI/ML",
                          size=10.5, fill=P.HOT))
        if ex:
            body.append(P.txt(L, y+24, "e.g. " + ex[0][:58], size=9.5, fill=P.MUTED))

    tot = sum(r[1] for r in rows)
    body.append(P.txt(L, T+RH*len(rows)+4, f"ORANGE = the mentions that also carry an AI/ML term",
                      size=11, fill=P.HOT, weight="600"))
    foot = [f"Every discipline together accounts for {tot/n*100:.1f}% of the feed, and most of those papers are "
            f"AI applied to the field rather than the field itself.",
            "There is no category or discipline field in the payload, so this is a keyword scan — and it "
            "OVER-counts: 'diagnos' catches 'Diagnosing Metalinguistic Reasoning'.",
            "So this recipe answers how AI research reaches AI artifacts on one platform. It cannot support a "
            "sentence about research reaching production in general.",
            "The mechanism it measures — a model card citing an arXiv id — does not exist outside software.",
            "Another field needs its own definition of 'shipped': a trial phase advance, a patent citation, a "
            "market approval."]
    print(P.write("20-scope.svg", P.frame(
        W, H, "Everything here is the computing niche, and no amount of data widens it",
        "Papers on the feed mentioning another discipline's vocabulary, and how many of those also carry an AI/ML "
        "term.", body, foot, chars=124)))


main()
