#!/usr/bin/env python3
"""Third fetch phase: size x method x era, for the decision questions.

    python3 pdb3.py            # appends to pdb.json

Figures 1-7 describe. These three crosstabs are for the questions that end in an action:
which method the field uses for a target of a given size, how that boundary has moved, and
what resolution a given (size, method) choice has actually produced.

**The boundary that kills a whole class of question.** The PDB contains only structures that
were solved. There is no record of a protein someone failed to crystallise, so *success rate by
method* is not computable here at any quality, and "will this work" is not a question this
register can answer. What it can answer is "what has the field done for targets like mine",
which is a description of practice, and how that has changed, which is the prescriptive part.

Queries are size band x method, and size band x method x era. 6 x 3 x 4 is 72 counts plus a
resolution histogram inside each of the 18 band-method cells.
"""
import json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdb as P                                                          # noqa: E402

BANDS = [(0, 50), (50, 100), (100, 200), (200, 500), (500, 1000), (1000, 100000)]
METHODS = ["X-RAY DIFFRACTION", "ELECTRON MICROSCOPY", "SOLUTION NMR"]
ERAS = [(2005, 2011), (2012, 2016), (2017, 2021), (2022, 2026)]
MW = "rcsb_entry_info.molecular_weight"
DEP = "rcsb_accession_info.deposit_date"


def band_q(lo, hi, method=None, era=None):
    nodes = [P.term(MW, {"from": lo, "to": hi, "include_lower": True,
                         "include_upper": False}, "range")]
    if method:
        nodes.append(P.term("exptl.method", method))
    if era:
        nodes.append(P.term(DEP, {"from": f"{era[0]}-01-01", "to": f"{era[1]}-12-31"},
                            "range"))
    return P.AND(*nodes) if len(nodes) > 1 else nodes[0]


def main():
    d = P.load()
    if "size_method" in d and "size_method_era" in d:
        print("  already cached")
        return 0

    if "size_method" not in d:
        out = {}
        for lo, hi in BANDS:
            k = f"{lo}-{hi}"
            out[k] = {"total": P.count(band_q(lo, hi)), "by_method": {}, "resolution": {}}
            for m in METHODS:
                out[k]["by_method"][m] = P.count(band_q(lo, hi, m))
                if out[k]["by_method"][m] >= 50:
                    out[k]["resolution"][m] = P.hist(
                        band_q(lo, hi, m), "rcsb_entry_info.resolution_combined", 0.25)
                time.sleep(0.2)
            print(f"  {k:<14}{out[k]['total']:>8,}   "
                  + "  ".join(f"{m.split()[0][:5]}={out[k]['by_method'][m]:,}"
                              for m in METHODS), flush=True)
        d["size_method"] = out

    if "size_method_era" not in d:
        out = {}
        for era in ERAS:
            ek = f"{era[0]}-{era[1]}"
            out[ek] = {}
            for lo, hi in BANDS:
                k = f"{lo}-{hi}"
                out[ek][k] = {m: P.count(band_q(lo, hi, m, era)) for m in METHODS}
                time.sleep(0.15)
            print(f"  era {ek}: " + ", ".join(
                f"{k}={sum(v.values()):,}" for k, v in out[ek].items()), flush=True)
        d["size_method_era"] = out

    json.dump(d, open(P.OUT, "w"), indent=1)
    print("\n  cached size_method and size_method_era")
    return 0


if __name__ == "__main__":
    sys.exit(main())
