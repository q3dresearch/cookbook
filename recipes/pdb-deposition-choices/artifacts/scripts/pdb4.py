#!/usr/bin/env python3
"""Fourth fetch phase: the two crosstabs that turn ranked lists into two-axis figures.

    python3 pdb4.py            # appends to pdb.json

Figures 6 and 7 both shipped as sorted bar lists with the counts printed beside them, which is
a table drawn slowly. Each has a second axis available and neither was spending it.

**Concentration by year** (`concentration_by_year`). Figure 7 reported three top-category shares
measured once. Q18's falsifier needs them over time: if the concentration is a property of what
is *solvable* it should sit flat, and if it is a property of *practice* it should move. One
terms facet per field per deposition year.

**Ligand by method** (`ligand_by_method`). Figure 6 sorted the top components into ADDITIVE,
AMBIGUOUS and BIOLOGICAL by hand, and nothing tested the labels. Crystallisation additives are
by definition an artefact of growing a crystal, so they should be scarce in cryo-EM entries,
while a genuine cofactor should not care how the structure was determined. That makes the hand
labels falsifiable against the method split.

**One correction this fetch forces.** The cached `temperature` facet is a *histogram*, so its
"100.0" bucket is everything in [100, 125) K -- 173,631 entries. The exact terms value is
166,568. Figure 7 reported the bucket as though it were the value.
"""
import json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdb as P                                                          # noqa: E402

DEP = "rcsb_accession_info.deposit_date"
FIELDS = {
    "temperature": ("diffrn.ambient_temp", 120),
    "space_group": ("symmetry.space_group_name_H_M", 400),
    "em_method": ("em_experiment.reconstruction_method", 20),
}
LIGAND = "rcsb_nonpolymer_entity_container_identifiers.nonpolymer_comp_id"
METHODS = ["X-RAY DIFFRACTION", "ELECTRON MICROSCOPY"]
YEARS = range(2005, 2026)


def in_year(y, *extra):
    n = [P.term(DEP, {"from": f"{y}-01-01", "to": f"{y}-12-31"}, "range"), *extra]
    return P.AND(*n) if len(n) > 1 else n[0]


def main():
    d = P.load()
    add = {}

    if "concentration_by_year" not in d:
        out = {}
        for key, (attr, n) in FIELDS.items():
            out[key] = {}
            for y in YEARS:
                try:
                    b = P.terms(in_year(y), attr, n)
                except Exception as e:                                   # noqa: BLE001
                    print(f"    {key} {y}: {type(e).__name__}", flush=True)
                    continue
                tot = sum(p for _, p in b)
                if tot:
                    top = sorted((p for _, p in b), reverse=True)
                    out[key][y] = {"recorded": tot, "buckets": len(b),
                                   "top1": top[0], "top3": sum(top[:3]),
                                   "leader": max(b, key=lambda x: x[1])[0]}
                time.sleep(0.15)
            hit = sum(1 for v in out[key].values() if v["buckets"] >= n)
            print(f"  {key:<12} {len(out[key])} years"
                  + (f"  — {hit} hit the {n}-bucket cap" if hit else "  — no year hit the cap"),
                  flush=True)
        add["concentration_by_year"] = out

    if "ligand_by_method" not in d:
        top = [c for c, _ in d["ligands"][:30]]
        out = {}
        for c in top:
            lq = P.term(LIGAND, c)
            row = {"total": P.count(lq)}
            for m in METHODS:
                row[m] = P.count(P.AND(lq, P.term("exptl.method", m)))
                time.sleep(0.15)
            out[c] = row
            xr, em = row[METHODS[0]], row[METHODS[1]]
            print(f"  {c:<5}{row['total']:>8,}   X-ray {xr:>7,}  cryo-EM {em:>6,}"
                  f"   EM share {em/(xr+em) if xr+em else 0:6.2%}", flush=True)
        add["ligand_by_method"] = out

    if not add:
        print("  everything already cached")
        return 0
    d.update(add)
    json.dump(d, open(P.OUT, "w"), indent=1)
    print(f"\n  added {', '.join(add)} to pdb.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
