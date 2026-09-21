#!/usr/bin/env python3
"""Run every fetch phase in order, then say how far the result has drifted.

    python3 fetch.py

The five phases each append to `artifacts/data/pdb.json` and skip work already cached, so
re-running is cheap and interrupting is safe. Nothing is downloaded in bulk: the RCSB search
API facets server-side, so about two hundred queries stand in for 260,089 rows.

**Expect drift.** The PDB grows weekly and the register is additive, so a refetch will not
reproduce the published numbers exactly. The comparison against `provenance.json` is the
point — a difference is visible rather than silent. `verify.py` then recomputes every number
in the README from whatever this produced.

Phases, in order and in rough cost:

    pdb.py    base facets: totals, method x year, resolution, authors, organisms, journals
    pdb2.py   targets, publication lag per deposition cohort, depositor unpublished shares
    pdb3.py   size x method and size x method x era, plus resolution inside each cell
    pdb4.py   concentration by deposition year, and ligand x method
    pdb5.py   the molecular-weight distribution of the entries carrying each ligand

`pdb3.py` and `pdb4.py` are the slow ones, a few minutes each behind the API's rate limit.
"""
import hashlib, json, os, runpy, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
CACHE = os.path.join(HERE, "..", "data", "pdb.json")
PHASES = ["pdb.py", "pdb2.py", "pdb3.py", "pdb4.py", "pdb5.py"]


def main():
    for name in PHASES:
        print(f"\n== {name}")
        sys.argv = [name]
        try:
            runpy.run_path(os.path.join(HERE, name), run_name="__main__")
        except SystemExit as e:
            if e.code:
                print(f"  {name} exited {e.code}")
                return e.code

    prov_path = os.path.join(ROOT, "provenance.json")
    if not os.path.exists(prov_path) or not os.path.exists(CACHE):
        print("\n  no provenance.json to compare against")
        return 0
    prov = json.load(open(prov_path))
    raw = open(CACHE, "rb").read()
    d = json.loads(raw)
    got = hashlib.sha256(raw).hexdigest()

    print("\n== drift against provenance.json")
    print(f"  retrieved        published {prov['retrieved']}   now {d['fetched']}")
    same = got == prov["cache"]["sha256"]
    print(f"  cache sha256     {'identical' if same else 'DIFFERENT'}")
    if not same:
        print(f"                   published {prov['cache']['sha256'][:32]}…")
        print(f"                   now       {got[:32]}…")
    for label, key, now in (("entries", "entries_at_fetch", d["total"]),
                            ("unpublished", "unpublished_at_fetch", d["unpublished_total"])):
        then = prov["source"][key]
        delta = now - then
        print(f"  {label:<16} published {then:>9,}   now {now:>9,}   "
              f"{delta:+,} ({delta/then:+.2%})")
    print("\n  A difference here is expected and is not an error. Run verify.py next: it "
          "recomputes\n  every number in the README from this cache and reports what no longer "
          "matches the prose.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
