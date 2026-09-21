#!/usr/bin/env python3
"""Fifth fetch phase: the size of the proteins each ligand is found in.

    python3 pdb5.py            # appends to pdb.json

`ligand_by_method` shows every declared crystallisation additive sitting near zero cryo-EM
share, which reads as a clean confirmation of the hand-made classification -- until you notice
that NAD (8.2%), HEM (7.9%) and FAD (5.8%) are also below the register's 14.1% cryo-EM
baseline, and those are unambiguous biological cofactors.

**The obvious explanation is size, and it is testable rather than assertable.** Cryo-EM does
big things (figure 8). If a ligand's cryo-EM share mostly tracks how large its host proteins
are, then a high share is evidence about the target and not about the ligand, and only the
*near-zero* end carries the mechanism -- no crystallisation drop, no additive.

So: the molecular-weight distribution of entries carrying each of the same 30 components, which
turns "presumably confounded with size" into a measured covariate.
"""
import json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdb as P                                                          # noqa: E402

LIGAND = "rcsb_nonpolymer_entity_container_identifiers.nonpolymer_comp_id"


def main():
    d = P.load()
    if "ligand_mw" in d:
        print("  already cached")
        return 0
    out = {}
    for c in d["ligand_by_method"]:
        h = P.hist(P.term(LIGAND, c), "rcsb_entry_info.molecular_weight", 50)
        out[c] = h
        pts = sorted((float(a), b) for a, b in h)
        n = sum(b for _, b in pts)
        med, run = None, 0
        for a, b in pts:
            run += b
            if med is None and run >= 0.5 * n:
                med = a
        print(f"  {c:<5}{n:>8,} entries   median mass {med:>7,.0f} kDa", flush=True)
        time.sleep(0.2)
    d["ligand_mw"] = out
    json.dump(d, open(P.OUT, "w"), indent=1)
    print(f"\n  added ligand_mw for {len(out)} components")
    return 0


if __name__ == "__main__":
    sys.exit(main())
