#!/usr/bin/env python3
"""Measure the intervention-name join before anything is built on it.

    python3 joincheck.py

The question "do phase 1, 2 and 3 of the same product differ" needs a product key. This
register has none — no NDC, no UNII, no ChEMBL id — so the only candidate is the free-text
intervention name the sponsor typed.

**This project has now had three joins that looked obvious and matched almost nothing**, so
the rule is to measure the overlap first and report the number, whatever it is. A join is not
usable because it is the only one available.

What this prints, in the order it would kill the idea:

1. **How concentrated are the names.** If "Placebo" and "Standard of care" dominate, the key
   is mostly a word meaning "no product".
2. **How many trials survive normalisation** into a name shared by more than one trial.
3. **How many of those name-groups span more than one phase** — which is the actual
   requirement. A product key that never sees the same molecule at two phases answers nothing.
4. **What a normalised group looks like**, printed raw, so the failure mode is visible rather
   than summarised. Dose strings, formulations and arm labels all collapse differently.

Normalisation is deliberately shallow: lowercase, strip dose and unit tokens, strip
punctuation. Anything more aggressive starts merging distinct molecules, and the point here is
to find out whether a *cheap* key works, not to build a drug dictionary.
"""
import collections, csv, gzip, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
NAMES = os.path.join(DATA, "names.csv.gz")
MAIN = os.path.join(DATA, "studies.csv.gz")

# tokens that are dose, form or packaging rather than identity
NOISE = re.compile(r"\b(\d+(\.\d+)?\s*(mg|g|mcg|ug|ml|l|iu|units?|%|mg/kg|mg/m2|kg)"
                   r"|tablet|capsule|injection|infusion|solution|oral|iv|im|sc|topical"
                   r"|placebo\s*comparator|active\s*comparator|arm|group|cohort|dose|daily"
                   r"|weekly|bid|qd|tid|once|twice|per\s*day)\b")
STOP = {"placebo", "standard of care", "control", "no intervention", "usual care",
        "saline", "normal saline", "sham", "vehicle", "observation", "none",
        "standard care", "best supportive care", "water", "sham comparator"}


def norm(s):
    s = s.lower().strip()
    s = re.sub(r"[\(\[].*?[\)\]]", " ", s)
    s = NOISE.sub(" ", s)
    s = re.sub(r"[^a-z0-9\- ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" -")
    return s


def main():
    if not os.path.exists(NAMES):
        raise SystemExit("  run ctg4.py first")
    try:
        with gzip.open(NAMES, "rt", newline="", encoding="utf-8") as f:
            nm = {r["nct_id"]: r for r in csv.DictReader(f)}
    except EOFError:
        raise SystemExit("  names.csv.gz is truncated — re-run ctg4.py to finish")
    with gzip.open(MAIN, "rt", newline="", encoding="utf-8") as f:
        mn = {r["nct_id"]: r for r in csv.DictReader(f)}
    print(f"\n  {len(nm):,} rows with intervention names, joined to {len(mn):,} studies")

    raw = collections.Counter()
    for r in nm.values():
        for n in (r["names"] or "").split("|"):
            if n:
                raw[n] += 1
    print(f"\n== 1. raw names: {len(raw):,} distinct across {sum(raw.values()):,} mentions")
    for k, v in raw.most_common(12):
        print(f"     {v:>7,}  {k[:60]!r}")

    # drug-type interventions only, dropping the words that mean "no product"
    prod = collections.defaultdict(set)
    kept = dropped = 0
    for nct, r in nm.items():
        names = [x for x in (r["names"] or "").split("|") if x]
        types = [x for x in (r["types"] or "").split("|") if x]
        for i, n in enumerate(names):
            t = types[i] if i < len(types) else ""
            if t not in ("DRUG", "BIOLOGICAL"):
                continue
            k = norm(n)
            if not k or k in STOP or len(k) < 3:
                dropped += 1
                continue
            kept += 1
            prod[k].add(nct)
    print(f"\n== 2. after normalising DRUG/BIOLOGICAL names and dropping placebo-like terms")
    print(f"     {kept:,} usable mentions, {dropped:,} dropped, "
          f"{len(prod):,} distinct product keys")
    sizes = collections.Counter(len(v) for v in prod.values())
    single = sizes[1]
    print(f"     keys appearing in exactly one trial: {single:,} "
          f"({single/len(prod):.1%}) <- these can never link phases")
    multi = {k: v for k, v in prod.items() if len(v) > 1}
    print(f"     keys in 2+ trials: {len(multi):,}, covering "
          f"{len(set().union(*multi.values())) if multi else 0:,} trials")

    print(f"\n== 3. THE TEST: do the multi-trial keys span more than one phase?")
    spans = collections.Counter()
    phased = {}
    for k, ncts in multi.items():
        ph = set()
        for n in ncts:
            m = mn.get(n)
            if m:
                p = (m["phases"] or "").split("|")[0]
                if p.startswith("PHASE"):
                    ph.add(p)
        spans[len(ph)] += 1
        if len(ph) >= 2:
            phased[k] = (ncts, ph)
    tot = sum(spans.values())
    for n_ph in sorted(spans):
        print(f"     keys touching {n_ph} distinct phase(s): {spans[n_ph]:>7,}  "
              f"{spans[n_ph]/tot:>6.1%}")
    print(f"     -> {len(phased):,} keys support a within-product phase comparison")
    if phased:
        cov = len(set().union(*(v[0] for v in phased.values())))
        print(f"        covering {cov:,} trials, {cov/len(nm):.1%} of the register")

    print(f"\n== 4. what the key actually looks like — the ten largest multi-phase groups")
    for k, (ncts, ph) in sorted(phased.items(), key=lambda kv: -len(kv[1][0]))[:10]:
        print(f"     {len(ncts):>5} trials  {sorted(ph)}  {k[:52]!r}")
    print(f"\n== 5. a random group, printed raw, so the failure mode is visible")
    for k in list(phased)[:3]:
        ncts = sorted(phased[k][0])[:6]
        print(f"     key {k[:44]!r}:")
        for n in ncts:
            orig = [x for x in (nm[n]["names"] or "").split("|") if norm(x) == k]
            print(f"       {n}  {(orig[0] if orig else '?')[:64]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
