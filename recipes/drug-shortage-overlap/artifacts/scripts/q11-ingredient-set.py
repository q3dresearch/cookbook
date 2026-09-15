#!/usr/bin/env python3
"""Q11: does keying on the full ingredient SET change anything?

`coded()` keys a substance on ONE RxNorm ingredient code, because the resolver used to
return from inside its concept loop on the first hit. `acetaminophen oxycodone` became
`acetaminophen`, so two different combinations could land on one key and be counted as
the same molecule in the three-country overlap.

`coded_set()` keys on the whole set. This script reports the difference rather than
quietly adopting it -- a key change that moves the headline is a thing a reader has to
be told about, and a key change that moves nothing is worth saying too.

It refuses to report anything if the cache is not fully re-resolved, because a partial
set-key cache silently mixes the two schemes and would look like a small effect.
"""
import sys, collections, json
sys.path.insert(0, ".")
import shortagelib as S

MIN_COVERAGE = 0.99


def main():
    regs = S.registers()
    old_keys, cd_old = S.shared_coded(regs)
    new_keys, cd_new, cov = S.shared_coded_set(regs)

    print(f"  set-key cache coverage: {cov:.1%}")
    if cov < MIN_COVERAGE:
        print(f"  REFUSING to compare — below {MIN_COVERAGE:.0%}. A partial cache mixes the")
        print("  two key schemes and would read as a small effect. Finish rxnorm.py first.")
        return 1

    print(f"\n  three-country overlap, one-ingredient key : {len(old_keys)}")
    print(f"  three-country overlap, ingredient-SET key : {len(new_keys)}")

    combos = collections.Counter()
    for c, m in cd_new.items():
        combos[c] = sum(1 for v in m.values() if v[2] > 1)
    print(f"\n  combination products per register: "
          + ", ".join(f"{c} {n}" for c, n in sorted(combos.items())))

    # a collision is one old key now split across several sets
    rx = json.loads((S.DATA / "rxnorm.json").read_text())
    by_first = collections.defaultdict(set)
    for v in rx.values():
        if v.get("set_key") and v.get("rxcui"):
            by_first[v["rxcui"]].add(v["set_key"])
    split = {k: s for k, s in by_first.items() if len(s) > 1}
    print(f"  ingredient codes that were hiding more than one product: {len(split)}")
    for k, s in sorted(split.items(), key=lambda kv: -len(kv[1]))[:10]:
        nm = next((v.get("ingredient") for v in rx.values() if v.get("rxcui") == k), k)
        print(f"     {nm or k:24s} -> {len(s)} distinct ingredient sets")

    gone = [k for k in old_keys if k not in {n.split("+")[0] for n in new_keys}]
    print(f"\n  substances leaving the three-country overlap under the set key: {len(gone)}")
    for k in gone:
        print(f"     {cd_old['US'].get(k, ('?',))[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
