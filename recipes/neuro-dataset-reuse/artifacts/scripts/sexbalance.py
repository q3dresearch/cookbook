#!/usr/bin/env python3
"""Sex in the archive: balanced where it is readable, and half of it is not readable.

    python3 sexbalance.py

**Sex is genuinely balanced, and not by averaging skewed studies.** Pooled across 50,437
classifiable records it is **54.4% female**; the median *within-dataset* female share is
**53.8%**, and 68% of the 716 datasets with ten or more classifiable subjects sit inside a
35-65% band. It holds across every modality: MRI 54.8%, EEG 53.8%, MEG 54.5%, PET 50.0%,
iEEG 49.3%.

**Which is the interesting part, because age is not.** Plate 11 has 18-25 year olds at 4.4
times their population share and over-65s at 0.4. The same community that evidently fixed sex
balance has left the age distribution alone -- so this is not general carelessness about who
gets scanned. It is one demographic critique answered and another not.

**And half the field is missing rather than mangled, which is a different problem.** Of
101,536 subject records: **50,437 are usable** (50%), **44,309 are simply blank** (44%),
**2,272 say n/a or none** (2%) and **3,980 are bare numbers** -- `1`, `0`, `2`, `-1` -- with
nothing in the record saying which sex `1` means, because the convention is per-dataset (4%).
A first pass called this "half unusable", which conflated a field nobody filled in with a
field filled in badly. The tail is long -- 192 distinct raw values for a binary-ish variable --
but it is a tail, not the story.
"""
import collections, json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fold, modality                                                    # noqa: E402

DATA = os.path.join(HERE, "..", "data")
MIN_SUBJ = 10
F = {"f", "female", "w", "woman"}
M = {"m", "male", "man"}
BANDS = ((0, .10, "under 10%"), (.10, .35, "10-35%"), (.35, .65, "35-65%"),
         (.65, .90, "65-90%"), (.90, 1.01, "over 90%"))


def norm(v):
    s = str(v or "").strip().lower()
    return "F" if s in F else ("M" if s in M else None)


def rows():
    """Reads the CONDENSED receipt. The raw per-subject file is 4.4 MB and carries identities
    this plate never uses; the fold carries counts per dataset and is 2% of the size."""
    d = json.load(open(os.path.join(DATA, "demographics-fold.json")))
    base = {r["id"]: r for r in fold.load()["rows"]}
    out = []
    for r in d["rows"]:
        ok = r["F"] + r["M"]
        b = base.get(r["id"])
        out.append({"id": r["id"], "n_records": r["n_records"], "n_ok": ok,
                    "female": (r["F"] / ok) if ok else None,
                    "mod": modality.modality(b) if b else "unknown"})
    return out


def vocabulary():
    d = json.load(open(os.path.join(DATA, "demographics-fold.json")))
    agg = collections.Counter()
    for r in d["rows"]:
        for k in ("F", "M", "blank", "numeric", "na", "other"):
            agg[k] += r[k]
    total = sum(agg.values())
    return {"total": total, "classifiable": agg["F"] + agg["M"], "numeric": agg["numeric"],
            "distinct": d["distinct_raw_values"],
            "top": sorted(d["vocab"].items(), key=lambda z: -z[1])[:10],
            "blank": agg["blank"], "na": agg["na"], "other": agg["other"]}


def distribution(rs, min_subj=MIN_SUBJ):
    g = [r for r in rs if r["n_ok"] >= min_subj]
    out = [{"label": lab, "n": sum(1 for r in g if lo <= r["female"] < hi)}
           for lo, hi, lab in BANDS]
    for b in out:
        b["share"] = b["n"] / len(g)
    return {"datasets": len(g), "bands": out,
            "median": statistics.median(r["female"] for r in g),
            "pooled": (sum(r["female"] * r["n_ok"] for r in g)
                       / sum(r["n_ok"] for r in g)),
            "skewed": sum(1 for r in g if r["female"] < .35 or r["female"] > .65) / len(g)}


def by_modality(rs, min_ds=15):
    out = []
    for m in ("mri", "eeg", "ieeg", "meg", "pet"):
        g = [r for r in rs if r["mod"] == m and r["n_ok"] >= MIN_SUBJ]
        if len(g) >= min_ds:
            out.append({"mod": m, "n": len(g),
                        "median": statistics.median(r["female"] for r in g)})
    return out


def main():
    rs = rows()
    v = vocabulary()
    d = distribution(rs)
    print(f"\n  {v['total']:,} sex records, {v['distinct']} distinct raw values")
    for k, lab in (("classifiable", "usable"), ("blank", "blank, never filled in"),
                   ("numeric", "bare numbers, no key"), ("na", "n/a or none"),
                   ("other", "everything else")):
        print(f"    {lab:<26}{v[k]:>8,}{v[k]/v['total']:>7.1%}")
    print(f"  top values: {v['top'][:8]}")
    print(f"\n  {d['datasets']:,} datasets with >={MIN_SUBJ} classifiable subjects")
    print(f"  pooled {d['pooled']:.1%} female, median within-dataset {d['median']:.1%}")
    print(f"  {'band':<12}{'datasets':>10}{'share':>8}")
    for b in d["bands"]:
        print(f"  {b['label']:<12}{b['n']:>10}{b['share']:>8.0%}")
    print(f"  skewed beyond 35-65: {d['skewed']:.0%}")
    print(f"\n  by modality:")
    for m in by_modality(rs):
        print(f"    {modality.NICE.get(m['mod'], m['mod']):<7}n={m['n']:>4}  "
              f"median {m['median']:.1%} female")
    return 0


if __name__ == "__main__":
    sys.exit(main())
