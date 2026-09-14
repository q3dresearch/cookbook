#!/usr/bin/env python3
"""Re-derive every headline number in this recipe from the archive.

    python verify.py

`promote.py` does the mechanical half of promotion and prints, as a checklist it
refuses to tick for you, "re-derive the numbers rather than trusting what the draft
says". This is that. Each CLAIM below is a number written somewhere in `questions.md`,
the README or a chart docstring; the check recomputes it from the capture and prints
OK or MISMATCH.

**The README is covered too, not only the questions file.** The README is the part a
stranger reads and the part least likely to be re-checked, which makes it the most
likely to drift.

**It is not a test suite and should not become one.** The archive grows, so some of
these will drift and that is correct behaviour, not failure. It happened the same day:
the arXiv corpus was re-fetched on 2026-09-14 and came back with 424 usable
bibliographies rather than 428 and 173 citations of Attention rather than 175 — papers
get revised, and a `.bbl` is whatever the current source says. The numbers here are the
re-derived ones. The point is that a drift
is *visible* — the 2026-09-14 audit found nine stale numbers, two wrong conventions and
one genuine error (a 'random baseline' that was a stable sort on a constant key), none
of which announced itself.

Conventions that bit during that audit, recorded here so they stop biting:

- **org counts are quoted two ways.** 87 papers sit at two or more raw org strings, 80
  once same-company namespaces are merged. Both appear in the text; they must say which.
- **`cited` is "named by any top-1,000 model"**, including models that declare a foreign
  `base_model:`. The derivative filter belongs to the *independent-org* measure, not to
  this one. Q32 was computed the other way and read 0.99% where the shared convention
  gives 1.08%.
- **bibliography ref counts** are over the <=400-ref filtered set (30,710 refs), not the
  raw 189,128.
- **the independent-adoption count is scoped.** Two papers clear two independent orgs
  across the whole feed; **one** clears it inside the exposure-matched cohort, because
  DINOv3 was published after the cohort's cutoff. Q31 quoted the feed-wide 2 against
  the cohort denominator of 6,134.
- **word-boundary matching is not optional.** A first pass at the Q39 artifact test
  counted 739 models "tagged dpo". Every one was `endpoints_compatible` — `dpo` inside
  `en(dpo)ints`. The real count is zero.
- **`5-invisible` does not deduplicate** within a bibliography and `6-credit-gap` does,
  which is why Attention reads 173 in one and 165 in the other. Both are correct.
"""
import collections, json, math, re, statistics, sys
sys.path.insert(0, ".")
import paperlib as P
from adoption import ALIASES
from ancestors import norm, MAX_REFS, JUNK, is_venue

FAIL = []


def chk(where, label, claim, actual, tol=0):
    try:
        ok = abs(float(claim) - float(actual)) <= tol
    except (TypeError, ValueError):
        ok = str(claim) == str(actual)
    if not ok:
        FAIL.append(f"{where} {label}: claim {claim}, actual {actual}")
    print(f"  {'OK ' if ok else '!! '} {where:14s} {label:44s} {claim!s:>22s}  {actual}")


def main():
    ms, f = P.models(), P.feed()
    cited, indep, allorg = set(), collections.defaultdict(set), collections.defaultdict(set)
    for m in ms:
        raw = m["id"].split("/")[0]
        o = ALIASES.get(raw, raw)
        for a in P.arxiv_ids(m):
            cited.add(a); allorg[a].add(raw)
            if not P.foreign_base(m): indep[a].add(o)

    print("\n-- the adoption chain --")
    chk("Q1", "distinct papers cited by the top 1,000", 430, len(cited))
    chk("Q1", "models carrying at least one tag", 522, sum(1 for m in ms if P.arxiv_ids(m)))
    chk("Q3", "models with a foreign base_model", 251, sum(1 for m in ms if P.foreign_base(m)))
    chk("Q3", "papers at 2+ RAW org strings", 87, sum(1 for a in allorg if len(allorg[a]) >= 2))
    chk("Q3", "papers at 2+ independent orgs", 21, sum(1 for a in cited if len(indep[a]) >= 2))
    chk("Q6", "LoRA 2106.09685: orgs naming it", 1, len({m["id"].split("/")[0] for m in ms if "2106.09685" in P.arxiv_ids(m)}))

    print("\n-- lag --")
    lag = collections.defaultdict(list); allp = []
    for m in ms:
        c = m.get("createdAt"); fl = P.FIELD_TAG.get(m.get("pipeline_tag"))
        if not c: continue
        cm = int(c[:4])*12 + int(c[5:7])
        for a in P.arxiv_ids(m):
            pm = P.pub_month(a)
            if pm is None: continue
            allp.append(cm-pm)
            if fl and -24 <= cm-pm <= 180: lag[fl].append(cm-pm)
    chk("Q7", "(model, paper) pairs", 1133, len(allp))
    chk("Q7", "median lag over all pairs", 13, round(statistics.median(allp)))
    chk("Q8", "pairs where the model came first", 131, sum(1 for x in allp if x < 0))
    pos = [x for v in lag.values() for x in v if x > 0]
    chk("Q23", "pooled median once the paper is first", 21, round(statistics.median(pos)))
    meds = sorted(round(statistics.median([x for x in v if x > 0])) for v in lag.values())
    chk("Q23", "per-field positive medians, min-max", "20-25", f"{meds[0]}-{meds[-1]}")

    print("\n-- attention and uptake --")
    both = [v for v in f.values() if v.get("githubStars") is not None]
    chk("Q10", "papers with upvotes and stars", 10078, len(both))
    pp = [(v["upvotes"], v["githubStars"]) for v in both if v["upvotes"] > 0 and v["githubStars"] > 0]
    chk("Q10", "r on logs", 0.47, round(statistics.correlation(
        [math.log10(a) for a, _ in pp], [math.log10(b) for _, b in pp]), 2), tol=0.01)
    ad = [v for k, v in f.items() if k in cited]; na = [v for k, v in f.items() if k not in cited]
    chk("Q11", "median upvotes, adopted", 51, round(statistics.median(v["upvotes"] for v in ad)))
    chk("Q12", "share of adopted papers ever on the feed", "30%", f"{len(cited & set(f))/len(cited)*100:.0f}%")

    print("\n-- the calendar (per year, not pooled) --")
    import datetime as dt
    DEAD = {5, 6, 20, 21, 22, 23, 24}
    byy = collections.defaultdict(collections.Counter)
    for p in f.values():
        d = dt.date.fromisoformat(p["publishedAt"][:10])
        y, w = d.isocalendar()[0], d.isocalendar()[1]
        if w <= 52: byy[y][w] += 1
    for y, want in ((2024, 0.92), (2025, 1.43)):
        dv = statistics.mean(byy[y][w] for w in DEAD)
        ov = statistics.mean(byy[y][w] for w in range(1, 53) if w not in DEAD)
        chk("Q24", f"{y}: deadline weeks vs the rest", want, round(dv/ov, 2), tol=0.01)

    print("\n-- funding --")
    coh = [(k, v) for k, v in f.items() if "2023-06-01" <= v["publishedAt"][:10] <= "2025-03-31"]
    tot = sum(1 for k, _ in coh if k in cited)
    chk("Q31", "exposure-matched cohort", 6134, len(coh))
    chk("Q31", "adopted in cohort", 73, tot)
    chk("Q31", "COHORT papers at 2+ independent orgs", 1, sum(1 for k, _ in coh if len(indep.get(k, ())) >= 2))
    chk("ch8", "FEED-WIDE papers at 2+ independent orgs", 2, sum(1 for k in f if len(indep.get(k, ())) >= 2))
    s = sorted(coh, key=lambda kv: kv[1]["upvotes"], reverse=True)[:int(len(coh)*0.10)]
    chk("Q33", "top 10% by upvotes captures", "56%", f"{sum(1 for k, _ in s if k in cited)/tot*100:.0f}%")
    for lo, hi, want in ((1, 2, 0.41), (25, 10**6, 9.28)):
        sel = [k for k, v in coh if lo <= len(v.get("authors") or []) <= hi]
        chk("Q30", f"authors {lo}-{hi if hi < 10**5 else '+'} adoption rate",
            want, round(sum(1 for k in sel if k in cited)/len(sel)*100, 2), tol=0.01)

    print("\n-- README figures not covered above --")
    chk("README", "models declaring no base_model at all", 611,
        sum(1 for m in ms if not any(t.startswith("base_model:") for t in m.get("tags", []))))
    chk("README", "top-1,000 listing size", 1000, len(ms))
    chk("README", "papers pooled from the whole feed", 17534, len(P.feed(one_extractor=False)))
    big = [k for k, v in f.items() if (v.get("githubStars") or 0) >= 1000]
    chk("README", "best single feature: 1000+ star repos adopted", "7%",
        f"{sum(1 for k in big if k in cited)/len(big)*100:.0f}%")
    mods = collections.Counter(m["id"].split("/")[0] for m in ms)
    chk("README", "Qwen models in the listing", 114, mods.get("Qwen", 0))
    papers = collections.defaultdict(set)
    for m in ms: papers[m["id"].split("/")[0]] |= P.arxiv_ids(m)
    chk("README", "inflation from counting models not publishers", "2.1x",
        f"{sum(len(P.arxiv_ids(m)) for m in ms)/sum(len(v) for v in papers.values()):.1f}x")

    chk("Q16", "feed papers carrying an organization", "28%",
        f"{sum(1 for p in f.values() if p.get('organization'))/len(f)*100:.0f}%")
    chk("Q16", "adopted feed papers carrying an organization", 46,
        sum(1 for k, p in f.items() if k in cited and p.get("organization")))

    print("\n-- supersession vs absorption (Q39) --")
    kq = collections.defaultdict(collections.Counter); tq = collections.Counter()
    for pa in f.values():
        q = P.quarter(pa["publishedAt"]); tq[q] += 1
        for k in set(x.lower() for x in (pa.get("ai_keywords") or [])): kq[q][k] += 1
    def pk(term):
        qs2 = [q for q in sorted(tq) if tq[q] >= 200]
        ser = [(kq[q][term]/tq[q]*100, q) for q in qs2]
        return max(ser)
    for term, want_pct, want_q in (("rlhf", 1.50, "2023Q3"),
                                   ("direct preference optimization", 1.95, "2024Q2"),
                                   ("grpo", 3.08, "2025Q3")):
        v, q = pk(term)
        chk("Q39", f"{term[:30]} peak", f"{want_pct:.2f}% {want_q}", f"{v:.2f}% {q}", tol=0)
    import re as _re
    for term in ("mamba", "gaussian", "nerf", "dpo"):
        pat = _re.compile(r"(?<![a-z])" + term + r"(?![a-z])")
        n = sum(1 for m in ms if pat.search(m["id"].lower())
                or any(pat.search(t.lower()) for t in m.get("tags", [])))
        chk("Q39", f"models named/tagged '{term}' in the listing", 0, n)

    print("\n-- the ancestry cliff (Q19) --")
    import json as _j
    cache = _j.loads((P.RAW/"openalex.json").read_text())
    seeds = set()
    for m in P.models(latest_only=False): seeds |= P.arxiv_ids(m)
    byid = {v["doi"].lower().split("arxiv.")[-1]: v for v in cache.values()
            if isinstance(v, dict) and v.get("doi") and "arxiv." in v["doi"].lower()}
    res = [a for a in seeds if a in byid]
    chk("Q19", "seed papers", 449, len(seeds))
    chk("Q19", "resolved by arXiv DOI", "86%", f"{round(len(res)*100/len(seeds))}%")
    walk = [a for a in res if byid[a].get("referenced_works")]
    chk("Q19", "walkable share of all seeds", "21%", f"{round(len(walk)*100/len(seeds))}%")
    chk("Q19", "resolved seeds that are preprints", 384,
        sum(1 for a in res if byid[a].get("type") == "preprint"))
    for yr, want in ((2022, 0), (2024, 0), (2025, 0)):
        n = [a for a in res if a.split(".")[0][:2] == str(yr)[2:]]
        chk("Q19", f"{yr} papers walkable", want, sum(1 for a in n if byid[a].get("referenced_works")))

    print("\n-- the canon --")
    raw = json.loads((P.RAW/"bibliographies.json").read_text())
    bib = {k: [r for r in v if not any(j in r.lower() for j in JUNK) and not is_venue(r)]
           for k, v in raw.items() if v and len(v) <= MAX_REFS}
    chk("Q34", "bibliographies recovered", 424, len(bib))
    filt = {k: v for k, v in raw.items() if v and len(v) <= MAX_REFS}
    chk("Q34", "refs in the filtered set", 30710, sum(len(v) for v in filt.values()))
    chk("Q34", "refs carrying an arXiv id", 5,
        sum(1 for v in filt.values() for r in v if re.search(r"ar[xX]iv[:. ]*\d{4}\.\d{4,5}", r)))
    nod, ded = collections.Counter(), collections.Counter()
    for refs in bib.values():
        seen = set()
        for r in refs:
            t = norm(r)
            if len(t) < 12: continue
            nod[t] += 1
            if t not in seen: seen.add(t); ded[t] += 1
    att = next(t for t in ded if t.startswith("attention is all you need"))
    chk("ch5", "Attention, NOT deduplicated", 173, nod[att])
    chk("ch6", "Attention, deduplicated", 165, ded[att])

    print("\n-- the instrument --")
    rows = []
    for p in P.feed(one_extractor=False).values():
        d = (p.get("submittedOnDailyAt") or p["publishedAt"])[:10]
        rows.append((d, [x.strip().lower() for x in (p.get("ai_keywords") or []) if x.strip()]))
    r1 = [x for d, ks in rows if d < "2025-12-25" for x in ks]
    r2 = [x for d, ks in rows if "2025-12-25" <= d < "2026-07-23" for x in ks]
    chk("Q38", "single-word share before the break", 0.26,
        round(sum(1 for x in r1 if " " not in x)/len(r1), 2), tol=0.01)
    chk("Q38", "single-word share after", 0.14,
        round(sum(1 for x in r2 if " " not in x)/len(r2), 2), tol=0.01)

    print()
    if FAIL:
        print(f"{len(FAIL)} MISMATCH(ES) — the text and the archive disagree:")
        for x in FAIL: print("   " + x)
        return 1
    print("all claims re-derived; text and archive agree.")
    return 0


sys.exit(main())
