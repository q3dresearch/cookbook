#!/usr/bin/env python3
"""Who is actually inside the scans: every subject's age, across the whole archive.

    python3 cohort.py

**`ages` holds one number per participant, not a range.** A first pass read it as [min, max]
and produced an age table from the fifteen datasets that happen to have exactly two subjects.
Read correctly it is **52,970 individual people across 945 datasets** -- the largest single
measurement anywhere in this recipe, and it had been sitting unused since the first fetch.

**The corpus is a young adult.** Median age 24. **18-30 year olds are 54.0% of everyone ever
scanned**, against roughly 17% of the population of most OECD countries. **Over-65s are 7.6%**
against roughly 18-20% -- and they carry most of the neurodegeneration a brain model would be
built to say anything about.

**It is not a few large cohorts doing it.** Dropping the five biggest datasets -- 12% of all
people -- moves the median from 24 to 23 and pushes the 18-30 share *up* to 55.9%. The skew is
the whole archive, not its outliers.

**Per dataset the window is narrow.** Median within-dataset age span 16 years, 23% span under
ten, and **only 13% of datasets contain a single person over 65**.

**And it is turning, recently and for real.** The over-65 share runs 3.7% of 2024's people,
7.0% of 2025's and **20.3% of 2026's**. 2025's jump was 44% one dataset; 2026's is spread over
stroke outcomes, the Precision Aging Network, Michigan Neural Distinctiveness and two
Parkinson's EEG sets, and survives removing the largest at 16.6%.

**Population shares are context, not a matched comparison.** A research corpus is not a census
and has no obligation to be one -- a study of adolescent development should be full of
adolescents. The claim is about what a model trained on the *whole archive* would represent,
which is a different and fair question.
"""
import collections, json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fold, modality                                                    # noqa: E402

DATA = os.path.join(HERE, "..", "data")
BANDS = ((0, 12, "under 13"), (13, 17, "13-17"), (18, 25, "18-25"),
         (26, 40, "26-40"), (41, 64, "41-64"), (65, 200, "65+"))
# rough OECD population shares, for context only -- these are not a matched comparison
POP = {"under 13": .145, "13-17": .058, "18-25": .095, "26-40": .195,
       "41-64": .325, "65+": .182}


def rows():
    raw = json.load(open(os.path.join(DATA, "datasets.json")))["datasets"]
    md = {n["id"]: (n.get("metadata") or {}) for n in raw}
    nm = {n["id"]: ((n.get("latestSnapshot") or {}).get("description") or {}).get("Name", "")
          for n in raw}
    out = []
    for r in fold.load()["rows"]:
        v = md.get(r["id"], {}).get("ages")
        if not isinstance(v, list):
            continue
        ages = [x for x in v if isinstance(x, (int, float)) and 0 <= x <= 120]
        if not ages:
            continue
        out.append(dict(r, ages=ages, name=nm.get(r["id"], ""),
                        mod=modality.modality(r), yr=int(r["pub"][:4])))
    return out


def people(rs):
    return [a for r in rs for a in r["ages"]]


def bands(vals):
    n = len(vals)
    return [{"label": lab, "n": sum(1 for a in vals if lo <= a <= hi),
             "share": sum(1 for a in vals if lo <= a <= hi) / n, "pop": POP[lab]}
            for lo, hi, lab in BANDS]


def robustness(rs, k=5):
    """The archive is a lottery in reuse; check it is not one in demography either."""
    big = sorted(rs, key=lambda r: -len(r["ages"]))[:k]
    rest = [r for r in rs if r not in big]
    f = lambda v: {"median": statistics.median(v),
                   "young": sum(1 for a in v if 18 <= a <= 30) / len(v),
                   "old": sum(1 for a in v if a >= 65) / len(v)}
    return {"top": [{"id": r["id"], "n": len(r["ages"]), "name": r["name"],
                     "median": statistics.median(r["ages"])} for r in big],
            "with": f(people(rs)), "without": f(people(rest)),
            "share_of_people": sum(len(r["ages"]) for r in big) / len(people(rs))}


def by_year(rs, min_ds=15):
    out = []
    for y in sorted({r["yr"] for r in rs}):
        g = [r for r in rs if r["yr"] == y]
        if len(g) < min_ds:
            continue
        p = people(g)
        top = max(g, key=lambda r: sum(1 for a in r["ages"] if a >= 65))
        rest = [a for r in g if r is not top for a in r["ages"]]
        out.append({"year": y, "datasets": len(g), "people": len(p),
                    "median": statistics.median(p),
                    "old": sum(1 for a in p if a >= 65) / len(p),
                    "old_ex_top": (sum(1 for a in rest if a >= 65) / len(rest)
                                   if rest else None),
                    "top_id": top["id"]})
    return out


def main():
    rs = rows()
    p = people(rs)
    print(f"\n  {len(rs):,} datasets, {len(p):,} individual people, median age "
          f"{statistics.median(p):.0f}\n")
    print(f"  {'band':<12}{'people':>9}{'archive':>9}{'population':>12}{'ratio':>8}")
    for b in bands(p):
        print(f"  {b['label']:<12}{b['n']:>9,}{b['share']:>9.1%}{b['pop']:>12.1%}"
              f"{b['share']/b['pop']:>7.1f}x")
    rb = robustness(rs)
    print(f"\n  top 5 datasets are {rb['share_of_people']:.0%} of all people:")
    for t in rb["top"]:
        print(f"    {t['id']}  {t['n']:>6,} people  median {t['median']:>3.0f}  "
              f"{t['name'][:42]}")
    print(f"    with them   median {rb['with']['median']:.0f}  18-30 "
          f"{rb['with']['young']:.1%}  65+ {rb['with']['old']:.1%}")
    print(f"    without     median {rb['without']['median']:.0f}  18-30 "
          f"{rb['without']['young']:.1%}  65+ {rb['without']['old']:.1%}")
    print(f"\n  {'year':<6}{'datasets':>10}{'people':>9}{'median':>8}{'65+':>8}"
          f"{'65+ ex-top':>12}")
    for c in by_year(rs):
        print(f"  {c['year']:<6}{c['datasets']:>10}{c['people']:>9,}{c['median']:>8.0f}"
              f"{c['old']:>8.1%}"
              + (f"{c['old_ex_top']:>12.1%}" if c["old_ex_top"] is not None else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
