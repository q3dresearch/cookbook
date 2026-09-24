#!/usr/bin/env python3
"""Splitting OpenNeuro by the population a dataset studied, and what that is worth.

    python3 population.py

`dxStatus` is a dropdown with a free-text escape. The dropdown values are recognisable by
their counts -- "healthy / control" on 403 datasets, then epilepsy, alzheimers, parkinson's
disease, schizophrenia, asd, depression, fibromyalgia and "other". Everything below those is
somebody typing, and it is **not a controlled vocabulary**: it contains mixed arms
("parkinson's disease; control"), non-clinical groups ("healthy/control, gifted children"),
an animal rearing condition ("control vs dark reared") and at least one modality
("intracranial data").

**The rule is stated rather than curated.** CONTROL is exactly the dropdown's healthy/control
value. NAMED is every other non-blank answer. Hand-picking which free-text values to drop
after seeing the result is how a finding gets manufactured, so the rule is fixed and the
sensitivity is reported instead: `main()` prints what happens when the three values with no
clinical arm are removed.

**Blank is not a third population, it is an era.** 66% of datasets leave `dxStatus` empty, and
the fill rate runs 0% before 2018 and 31-44% every year since 2019 -- the field arrived, like
the consent fields, partway through the archive's life. Blanks are excluded from the
comparison rather than treated as controls.

**Era is matched because reuse front-loads.** Downloads per year falls with age, so any
comparison between two groups with different age profiles measures the calendar. The window
is 2018-2023, where both groups are present in every modality that has enough of them.
"""
import collections, json, os, random, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fold, modality                                                    # noqa: E402

DATA = os.path.join(HERE, "..", "data")
CONTROL = "healthy / control"
LO, HI = 2018, 2023             # the matched window
MIN_AGE = 1.0
# free-text answers that name no clinical arm at all; used only for the sensitivity check,
# never to build the headline groups
NOT_CLINICAL = {"healthy/control, gifted children", "control vs dark reared",
                "intracranial data"}


def rows(lo=LO, hi=HI):
    raw = json.load(open(os.path.join(DATA, "datasets.json")))["datasets"]
    md = {n["id"]: (n.get("metadata") or {}) for n in raw}
    out = []
    for r in fold.load()["rows"]:
        if r["dl_yr"] is None or r["age"] < MIN_AGE:
            continue
        dx = str(md.get(r["id"], {}).get("dxStatus") or "").strip().lower()
        yr = int(r["pub"][:4])
        if not dx or not (lo <= yr <= hi):
            continue
        out.append(dict(r, dx=dx, yr=yr, mod=modality.modality(r),
                        grp="control" if dx == CONTROL else "named"))
    return out


def perm(a, b, iters=20000, seed=11):
    """Permutation test on the gap between two medians. Stdlib only, seeded, so it is
    reproducible byte for byte -- determinism.py checks that it is."""
    rng = random.Random(seed)
    obs = statistics.median(b) - statistics.median(a)
    pool = list(a) + list(b)
    n, hits = len(a), 0
    for _ in range(iters):
        rng.shuffle(pool)
        if abs(statistics.median(pool[n:]) - statistics.median(pool[:n])) >= abs(obs):
            hits += 1
    return obs, (hits + 1) / (iters + 1)


def strata(rs, min_ctrl=20, min_named=10):
    """Per-modality comparison. Pooling across modalities inflates the gap, because the
    named-population datasets skew toward EEG and iEEG, which are more reused anyway."""
    by = collections.defaultdict(lambda: {"control": [], "named": []})
    for r in rs:
        by[r["mod"]][r["grp"]].append(r)
    out = []
    for m, g in by.items():
        if len(g["control"]) >= min_ctrl and len(g["named"]) >= min_named:
            a = [x["dl_yr"] for x in g["control"]]
            b = [x["dl_yr"] for x in g["named"]]
            d, p = perm(a, b)
            out.append({"mod": m, "control": g["control"], "named": g["named"],
                        "med_c": statistics.median(a), "med_n": statistics.median(b),
                        "ratio": statistics.median(b) / statistics.median(a), "p": p})
    return sorted(out, key=lambda s: -len(s["control"]))


def main():
    rs = rows()
    st = strata(rs)
    print(f"\n  {len(rs)} datasets published {LO}-{HI} that answered dxStatus")
    print(f"  {sum(1 for r in rs if r['grp']=='control')} control : "
          f"{sum(1 for r in rs if r['grp']=='named')} named a population\n")
    print(f"  {'modality':<8}{'ctrl n':>8}{'ctrl':>8}{'named n':>9}{'named':>8}"
          f"{'ratio':>8}{'p':>9}")
    for s in st:
        print(f"  {modality.NICE.get(s['mod'], s['mod']):<8}{len(s['control']):>8}"
              f"{s['med_c']:>8.1f}{len(s['named']):>9}{s['med_n']:>8.1f}"
              f"{s['ratio']:>7.2f}x{s['p']:>9.4f}")

    a = [r["dl_yr"] for r in rs if r["grp"] == "control"]
    b = [r["dl_yr"] for r in rs if r["grp"] == "named"]
    d, p = perm(a, b)
    print(f"\n  pooled across modalities: {statistics.median(b)/statistics.median(a):.2f}x "
          f"at p {p:.4f} -- INFLATED by composition, not the headline")

    b2 = [r["dl_yr"] for r in rs if r["grp"] == "named" and r["dx"] not in NOT_CLINICAL]
    print(f"  SENSITIVITY: dropping {len(b)-len(b2)} free-text answers with no clinical arm "
          f"moves the pooled ratio to "
          f"{statistics.median(b2)/statistics.median(a):.2f}x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
