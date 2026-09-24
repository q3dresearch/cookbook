#!/usr/bin/env python3
"""The modality a dataset is, rebuilt from the field that actually holds one.

    python3 modality.py

Not a chart. `chart-1-modality.py` reads this.

**`primaryModality` does not always contain a modality.** Across 1,859 published datasets it
holds `t1w` 21 times, `channels` 9, `beh` 5, `bold` 2 and `coordsystem` 2 -- those are BIDS
*suffixes*, the name of a file type inside the dataset, not the instrument that produced it.
58 more are blank. That is 93 rows, 5% of the archive, where the field named for the modality
is not one.

The `modalities` LIST is cleaner and longer, so the modality is taken from the union of both
and resolved against a declared order. `ieeg` is tested before `eeg` because an intracranial
recording is also an EEG and the list often carries both; taking the first match the other way
round would file every iEEG dataset as EEG.

**63 remain unresolvable** and are kept as `unknown` rather than forced into a bucket. They
are visible in the figures: their median size is 0.0 GB and their median subject count is 0,
so most of them are empty or broken rather than unlabelled.
"""
import math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fold                                                              # noqa: E402

# iEEG before EEG: an intracranial recording lists both, and the reverse order files
# every iEEG dataset as EEG.
ORDER = ("ieeg", "eeg", "meg", "nirs", "pet", "mri")
MRI_SUFFIX = {"t1w", "t2w", "bold", "dwi", "func", "anat", "flair", "swi", "asl"}
NICE = {"mri": "MRI", "eeg": "EEG", "ieeg": "iEEG", "meg": "MEG", "pet": "PET",
        "nirs": "fNIRS", "unknown": "unresolved"}
MIN_AGE = 1.0                  # a rate under a year is extrapolated from weeks


def modality(r):
    s = set(r.get("modalities") or [])
    if r.get("modality"):
        s.add(r["modality"])
    for k in ORDER:
        if k in s:
            return k
    return "mri" if (s & MRI_SUFFIX) else "unknown"


def rows(min_age=MIN_AGE):
    d = fold.load()
    out = []
    for r in d["rows"]:
        if r["dl_yr"] is None or r["age"] < min_age:
            continue
        r = dict(r)
        r["mod"] = modality(r)
        out.append(r)
    return out


def main():
    all_rows = [dict(r, mod=modality(r)) for r in fold.load()["rows"]
                if r["dl_yr"] is not None]
    mature = rows()
    print(f"\n  {len(all_rows):,} datasets with a defined rate; {len(mature):,} at least "
          f"{MIN_AGE:.0f} year old")
    print(f"\n  REUSE DECAYS, which is why a rate needs an age floor")
    for lo, hi, lab in ((0, .25, "under 3 months"), (.25, .5, "3-6 months"),
                        (.5, 1, "6-12 months"), (1, 2, "1-2 years"),
                        (2, 4, "2-4 years"), (4, 99, "over 4 years")):
        g = [r for r in all_rows if lo <= r["age"] < hi]
        if g:
            print(f"    {lab:<16}{len(g):>5}  median {statistics.median(x['dl_yr'] for x in g):>6,.1f}"
                  f" downloads/yr   raw {statistics.median(x['downloads'] for x in g):>5,.0f}")
    by = {}
    for r in mature:
        by.setdefault(r["mod"], []).append(r)
    base = statistics.median(x["dl_yr"] for x in by["mri"])
    print(f"\n  BY MODALITY, age {MIN_AGE:.0f}+ only")
    print(f"    {'modality':<12}{'n':>6}{'median dl/yr':>14}{'vs MRI':>9}{'median GB':>11}"
          f"{'median subjects':>17}")
    for k, g in sorted(by.items(), key=lambda t: -statistics.median(
            x["dl_yr"] for x in t[1])):
        m = statistics.median(x["dl_yr"] for x in g)
        print(f"    {NICE.get(k, k):<12}{len(g):>6}{m:>14,.1f}{m/base:>8,.1f}x"
              f"{statistics.median(x['size'] for x in g)/1e9:>11,.1f}"
              f"{statistics.median(x['subjects'] for x in g):>17,.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
