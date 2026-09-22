#!/usr/bin/env python3
"""Run every walk in order, then say how far the result has drifted.

    python3 fetch.py

Four phases. Each appends to its own file and skips work already done, so re-running is cheap
and interrupting is safe — every walk checkpoints its page token.

    ctg.py    totals, twelve marginals in one request, and the four screens
    ctg2.py   the register: 604 pages, 21 columns
    ctg3.py   start date, intervention type, conditions, location country
    ctg4.py   intervention names, for the product key

**Expect drift.** ClinicalTrials.gov is updated daily and the register is additive, so a
refetch will not reproduce the published numbers. The comparison against `provenance.json` is
the point — a difference is visible rather than silent. `verify.py` then recomputes every
number in the README from whatever this produced and says which sentences no longer hold.

**One property worth knowing before you time it.** This host charges roughly 134 seconds to
open a connection and under a second per request after that, so each walk is one handshake
plus about ten minutes. Measured through `urllib`, which opens a fresh connection per call,
every request instead reads as 135 seconds and the job looks impossible. The toll is
host-pair specific — `search.rcsb.org` answered in 0.3 s from the same machine — so a
reproducer elsewhere may see none of it.
"""
import hashlib, json, os, runpy, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
DATA = os.path.join(HERE, "..", "data")
PHASES = ["ctg.py", "ctg2.py", "ctg3.py", "ctg4.py"]


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
    if not os.path.exists(prov_path):
        print("\n  no provenance.json to compare against")
        return 0
    prov = json.load(open(prov_path))
    print("\n== drift against provenance.json")
    print(f"  published {prov['retrieved']}")
    for name, rec in prov["cache"]["files"].items():
        p = os.path.join(DATA, name)
        if not os.path.exists(p):
            print(f"  {name:<18}MISSING")
            continue
        raw = open(p, "rb").read()
        got = hashlib.sha256(raw).hexdigest()
        same = got == rec["sha256"]
        delta = len(raw) - rec["bytes"]
        print(f"  {name:<18}{'identical' if same else 'DIFFERENT':<10}"
              f"{len(raw):>12,}B  {delta:+,}B")
    print("\n  A difference here is expected and is not an error. Run verify.py next: it "
          "recomputes\n  every number in the README and reports what no longer matches the "
          "prose.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
