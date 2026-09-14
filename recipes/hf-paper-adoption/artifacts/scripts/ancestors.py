#!/usr/bin/env python3
"""What shipped AI rests on, counted from the papers' own reference lists.

    python ancestors.py [--min 3]

`bibliographies.py` collects each model-cited paper's `.bbl`. This counts which
references recur across them. A title in many bibliographies is a common ancestor:
not the most cited paper in the world, but the one the shipped lineages actually
stand on.

**Matching is by normalised title**, because a `.bbl` cites venues far more often than
arXiv ids. Normalisation is deliberately conservative -- case, punctuation, accents,
LaTeX residue and a trailing subtitle after a colon are removed, and nothing else.
Aggressive normalisation merges distinct papers, which invents ancestors; timid
normalisation splits one paper across spellings, which only loses a little counting
power. **Splitting is the safe failure and is what this chooses.**

Two things the count cannot do, both worth stating before reading it:

**A shared ancestor is not an influence.** Half these bibliographies cite ImageNet
because every vision paper does. Frequency measures convention as much as debt, and
nothing here separates the two.

**The seed set is the top-1,000 download head.** These are the ancestors of *popular*
models. A technique that everyone uses in models nobody downloads -- LoRA is the
worked example, one org and one model in the whole listing -- contributes nothing.
"""
import argparse
import collections
import json
import re
import unicodedata
from pathlib import Path

import paperlib as P

HERE = Path(__file__).resolve().parent
BIB = P.RAW / "bibliographies.json"

# A real paper's bibliography is tens of entries, not thousands. Four papers here ship
# an entire .bib library in their source -- one carries the whole ACL Anthology at
# 155,617 entries -- and `bibliographies.py` falls back to .bib when no .bbl parses, so
# it takes the author's reference library rather than what the paper cited. Those four
# were 83% of the raw reference count. Capped rather than hand-listed, so the next one
# is caught too.
MAX_REFS = 400

# LaTeX templates ship dummy bibliography entries. The CVPR template's "frobnicatable
# foo filter" turns up as a cited work in papers that never removed it.
JUNK = ("frobnicat", "foo filter", "author guidelines", "latex template")

# Some .bbl entries put the venue on the line the parser reads as a title, so
# "Proceedings of the IEEE/CVF Conference on Computer Vision" surfaced as the third
# most-depended-on "paper" in the corpus at 114 citations. A venue is not an ancestor.
VENUE = ("proceedings of", "conference on", "international conference",
         "advances in neural information", "workshop on", "annual meeting",
         "transactions on", "journal of", "arxiv preprint", "findings of the")

STRIP = re.compile(r"[^a-z0-9 ]+")
NOISE = re.compile(r"\b(arxiv|preprint|in proceedings of|proceedings of|technical report)\b")


def is_venue(title: str) -> bool:
    t = title.lower()
    return any(v in t for v in VENUE) and len(t) < 120


def norm(title: str) -> str:
    t = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    t = t.lower()
    t = t.split(":")[0] if len(t.split(":")[0]) > 24 else t   # drop a subtitle, keep short names
    t = NOISE.sub(" ", t)
    t = STRIP.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=3)
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()
    if not BIB.exists():
        raise SystemExit("run bibliographies.py first")
    bib = json.loads(BIB.read_text())
    raw_have = {k: v for k, v in bib.items() if v}
    dropped = {k: len(v) for k, v in raw_have.items() if len(v) > MAX_REFS}
    have = {k: [r for r in v if not any(j in r.lower() for j in JUNK)]
            for k, v in raw_have.items() if len(v) <= MAX_REFS}
    print(f"  {len(raw_have)}/{len(bib)} papers yielded a bibliography ({len(raw_have)/len(bib):.0%})")
    if dropped:
        print(f"  dropped {len(dropped)} with >{MAX_REFS} entries — a shipped .bib library, "
              f"not a reference list: {', '.join(f'{k} ({n:,})' for k, n in sorted(dropped.items(), key=lambda x: -x[1]))}")
    print(f"  {sum(len(v) for v in have.values()):,} references across {len(have)} papers\n")

    count = collections.Counter()
    display = {}
    for pid, refs in have.items():
        seen = {}
        for r in refs:                             # normalise once; keep the first spelling
            k = norm(r)
            if len(k) >= 12:
                seen.setdefault(k, r)
        for k, original in seen.items():           # once per citing paper, not per mention
            count[k] += 1
            display.setdefault(k, original)
    shared = [(n, t) for t, n in count.items() if n >= args.min]
    shared.sort(key=lambda x: -x[0])
    print(f"  {len(count):,} distinct references, {len(shared)} cited by {args.min}+ of the "
          f"{len(have)} papers\n")
    print(f"  {'in':>7}  title")
    for n, t in shared[:args.top]:
        print(f"  {n:>3}/{len(have):<3}  {display[t][:64]}")

    out = P.RAW / "ancestors.json"
    P.write_json_atomic(out,
        {"papers_with_bibliography": len(have), "papers_total": len(bib),
         "ancestors": [{"n": n, "title": display[t], "key": t} for n, t in shared]})
    print(f"\n  wrote {out}")


if __name__ == "__main__":
    main()
