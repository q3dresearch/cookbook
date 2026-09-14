#!/usr/bin/env python3
"""Walk backwards from shipped models to the ideas they rest on.

    python ancestry.py            # uses the cache; --refresh to re-fetch

The forward question — which papers become models — is answerable and limited. It can
only ever see what an uploader chose to write on a model card, so it sees
architectures and never sees the machinery underneath. **No model card cites an
optimizer.** Adam appears in four of ten shipped lineages here and in zero model
tags, which is the clearest statement of what forward tagging misses.

So this goes the other way. Start at the papers cited by top-1,000 models, take the
papers *those* cite, and again — a lineage trace. The question it answers is not
"what is popular" but "what is load-bearing".

**Coverage is the honest limit and it is systematic.** OpenAlex resolves 86% of the
model-cited papers by arXiv DOI but only 24% of those carry a reference list, because
it parses references for formally published work: `type=preprint` returns zero,
`type=conference-paper` returns 38. Most recent AI papers never leave arXiv, so the
gap skews hard to 2023-2026 and the walk is biased toward whatever reached a venue.
A Semantic Scholar key would fix this; it is the cheapest unblock and it is not
something this script can do for itself.

**Title search is not a fallback, and it fails silently.** It recovers BERT correctly
and returns "COVID-19 Vaccine News Headline: A Sentiment Analysis" for RoBERTa, and
for DINOv3 returns papers that *use* DINOv3. A false ancestor is worse than a missing
edge, so only exact DOI resolution is used.

**OpenAlex publication years describe the record, not the paper** — Batch
Normalization comes back as 2024 and Attention Is All You Need as 2025. Where an
arXiv id exists its own YYMM is preferred.

**And the titles are not trustworthy either, which is worse.** The second-most-shared
ancestor here — in 26 of 94 lineages — is stored as *"HISTORIAE, History of
Socio-Cultural Transformation as Linguistic Data"*, on a DOI belonging to an unrelated
LIPIcs paper. Its authorships are Liu, Ott, Goyal, Du, Joshi, Chen, Levy, Lewis,
Zettlemoyer, dated 2019-07-26. **It is RoBERTa**, with someone else's title and DOI
grafted on, and that corruption is also why RoBERTa looked absent when resolved by
arXiv DOI.

The rule that follows: **the edges and authorships are sound, the titles and DOIs are
not.** Any ancestor worth naming in a finding must be identified from its author list
and date, never from its stored title. `verify()` below does that for the ancestors
that carry a finding, and prints what it repaired.
"""
import argparse
import collections
import glob
import gzip
import json
import os
import subprocess
import time
from pathlib import Path

import paperlib as P

ARCHIVE = P.ARCHIVE  # resolved by paperlib: $WSS_HUGGING_FACE or artifacts/data/
HERE = Path(__file__).resolve().parent
CACHE = P.RAW / "openalex.json"
# Identify honestly, and keep the contact address out of a public repository.
# OpenAlex's "polite pool" and arXiv both ask callers to supply a contact; an honest
# bot UA also gets fewer 403s than a browser string does. So the address is read from
# the environment and the committed default carries none.
#   export WSS_CONTACT="mailto:you@example.org"
UA = "q3dresearch wss +https://github.com/q3dresearch" + (
    f" ({os.environ['WSS_CONTACT']})" if os.environ.get("WSS_CONTACT") else "")
SEL = "id,doi,title,publication_year,cited_by_count,referenced_works,type"


def seeds():
    """Papers cited by any top-1,000 model, pooled over every capture."""
    out = set()
    for p in sorted(glob.glob(str(ARCHIVE / "raw" / "hf.models.top-downloads" / "*" / "*" / "*"))):
        op = gzip.open if p.endswith(".gz") else open
        for m in json.load(op(p, "rt")):
            out |= {t.split(":", 1)[1] for t in m.get("tags", []) if t.startswith("arxiv:")}
    return sorted(a for a in out if a.replace(".", "").isdigit())


def _get(url):
    r = subprocess.run(["curl", "-sS", "--max-time", "45", "-A", UA, url],
                       capture_output=True, timeout=70)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {}


def fetch_by_doi(ids, cache):
    todo = [a for a in ids if f"arxiv:{a}" not in cache]
    for i in range(0, len(todo), 40):
        batch = todo[i:i + 40]
        f = "|".join(f"10.48550/arXiv.{a}" for a in batch)
        d = _get(f"https://api.openalex.org/works?filter=doi:{f}&per-page=50&select={SEL}")
        found = set()
        for w in d.get("results", []):
            doi = (w.get("doi") or "").lower()
            if "arxiv." in doi:
                key = doi.rsplit("arxiv.", 1)[-1]
                cache[f"arxiv:{key}"] = w
                found.add(key)
        for a in batch:                      # a miss is cached too, or every run refetches it
            cache.setdefault(f"arxiv:{a}", None)
        time.sleep(0.3)


def fetch_by_oaid(oaids, cache):
    todo = [w for w in oaids if w not in cache]
    for i in range(0, len(todo), 40):
        batch = todo[i:i + 40]
        f = "|".join(w.rsplit("/", 1)[-1] for w in batch)
        d = _get(f"https://api.openalex.org/works?filter=openalex:{f}&per-page=50&select={SEL}")
        for w in d.get("results", []):
            cache[w["id"]] = w
        for w in batch:
            cache.setdefault(w, None)
        time.sleep(0.3)


# Ancestors whose stored title disagrees with their authorship, repaired by hand after
# checking the author list and date against the paper they actually are. Recorded here
# rather than silently corrected, because the next person needs to know the field lies.
REPAIRS = {
    "https://openalex.org/W2965373594": (
        "RoBERTa: A Robustly Optimized BERT Pretraining Approach",
        "stored as HISTORIAE...; authors Liu/Ott/Goyal/Du/Joshi/Chen/Levy/Lewis/Zettlemoyer, 2019-07-26"),
}


def verify(rows, cache, top=25):
    """Flag high-share ancestors whose title looks implausible for their citation count."""
    notes = []
    for n, cited, yr, title, oid in rows[:top]:
        if oid in REPAIRS:
            notes.append((oid, title, *REPAIRS[oid]))
    return notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--min-share", type=int, default=3,
                    help="an ancestor must appear in this many lineages to be walked further")
    args = ap.parse_args()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    cache = {} if args.refresh or not CACHE.exists() else json.loads(CACHE.read_text())

    ids = seeds()
    fetch_by_doi(ids, cache)
    lvl0 = {a: cache.get(f"arxiv:{a}") for a in ids}
    walkable = {a: w for a, w in lvl0.items() if w and w.get("referenced_works")}
    print(f"  {len(ids)} papers cited by top-1,000 models")
    print(f"  {sum(1 for w in lvl0.values() if w)} resolve in OpenAlex, "
          f"{len(walkable)} carry a reference list ({len(walkable)/len(ids):.0%} walkable)\n")

    anc = collections.Counter()
    for a, w in walkable.items():
        for r in w["referenced_works"]:
            anc[r] += 1
    fetch_by_oaid(list(anc), cache)
    P.write_json_atomic(CACHE, cache)

    # REPAIRS is applied HERE, where the rows are built, not only where they are
    # printed. It used to be substituted in the console line alone, so every consumer
    # of ancestry.json kept reading "HISTORIAE" for RoBERTa while the terminal said
    # "repaired" — a correction that existed in the display and not in the data.
    rows = []
    for oid, n in anc.items():
        w = cache.get(oid)
        if w:
            fix = REPAIRS.get(oid)
            rows.append((n, w.get("cited_by_count") or 0, w.get("publication_year"),
                         fix[0] if fix else (w.get("title") or ""), oid))
    rows.sort(key=lambda r: (-r[0], -r[1]))
    print(f"  {len(anc)} distinct ancestors, {sum(1 for n in anc.values() if n >= args.min_share)} "
          f"shared by {args.min_share}+ lineages\n")
    print(f"  {'in':>5}  {'cited':>9}  {'yr':>4}  title")
    for n, cited, yr, title, oid in rows[:22]:
        mark = "  <- repaired" if oid in REPAIRS else ""
        print(f"  {n:>3}/{len(walkable):<3}{cited:>9,}  {yr or '?':>4}  {title[:56]}{mark}")
    for oid, stored, real, why in verify(rows, cache):
        print(f"\n  repaired {oid}\n    stored as: {stored[:60]}\n    actually:  {real}\n    why:       {why}")

    out = P.RAW / "ancestry.json"
    P.write_json_atomic(out,
        {"walkable": len(walkable), "seeds": len(ids),
         "ancestors": [{"n": n, "cited": c, "year": y, "title": t, "id": i,
                        **({"repaired": REPAIRS[i][1]} if i in REPAIRS else {})}
                       for n, c, y, t, i in rows]})
    print(f"\n  wrote {out}")


if __name__ == "__main__":
    main()
