#!/usr/bin/env python3
"""Second population: civilian agencies across a decade, requested year by year.

    python3 usa2.py

**Why a second population at all.** The all-agency FY2024 file is the register -- DoD is 68.6%
of contract awards and GSA another 22.9%, so a civilian-only study is a study of the 8.5%
remainder and must say so. But one fiscal year cannot answer a question about *change*, and an
all-agency decade is not affordable: generation time, not bytes, is the cost here, and one
month of DoD did not finish in ten minutes.

So there are two files with different jobs, and every figure names which one it used:

    all-agency FY2024   cross-sectional, includes DoD, answers "what does this look like"
    civilian FY2015-24  longitudinal, 8.5% of awards, answers "what has moved"

**Requested per year rather than as one range**, because a failed ten-year generation costs
ten years of waiting and a failed one-year generation costs one. Each year is checkpointed, so
an interrupted run resumes at the year it stopped.

**The agencies are declared here**, not derived from a size cut, so the population is
arguable: every cabinet department and major independent agency *except* Defense and GSA, the
two that would dominate any pooled number.
"""
import json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import usa as U                                                          # noqa: E402

DATA = os.path.join(HERE, "..", "data")
CKPT = os.path.join(DATA, "civilian.checkpoint.json")
CIVILIAN = ["Department of Veterans Affairs", "Department of Justice",
            "Department of Health and Human Services", "Department of Agriculture",
            "Department of Homeland Security", "Department of the Interior",
            "Department of Transportation", "Department of Commerce",
            "National Aeronautics and Space Administration",
            "Environmental Protection Agency", "Department of Energy"]
YEARS = list(range(2015, 2026))          # FY2025 is the last complete year as of 2026-09

# Years may be named on the command line, newest first when that is what the question
# needs: `python3 usa2.py 2025 2024`. A column's coverage is not stable across this
# range -- the ceiling column fills up over it and the bid count empties out -- so which
# years a figure can use is a per-column question, not a per-recipe one.


def main():
    want = [int(a) for a in sys.argv[1:] if a.isdigit()] or YEARS
    bad = [y for y in want if y not in YEARS]
    if bad:
        raise SystemExit("  not in range: %s" % bad)
    os.makedirs(DATA, exist_ok=True)
    ck = json.load(open(CKPT)) if os.path.exists(CKPT) else {"done": {}, "pending": {}}
    s = U.Session()
    try:
        for fy in want:
            key = str(fy)
            dest = os.path.join(DATA, f"civilian-fy{fy}.zip")
            if ck["done"].get(key) and os.path.exists(dest):
                print(f"  FY{fy}: already have it")
                continue
            fn = ck["pending"].get(key)
            if not fn:
                fn = U.request_download(s, f"{fy-1}-10-01", f"{fy}-09-30",
                                        agencies=CIVILIAN, label=f"civilian FY{fy}")
                if not fn:
                    print(f"  FY{fy}: no file name returned, skipping")
                    continue
                ck["pending"][key] = fn
                json.dump(ck, open(CKPT, "w"))
            st = U.poll(s, fn)
            if not st:
                print(f"  FY{fy}: did not finish; rerun to resume")
                continue
            U.download(fn, dest)
            ck["done"][key] = {"file": os.path.basename(dest),
                               "rows": st.get("total_rows"),
                               "size_kb": st.get("total_size")}
            ck["pending"].pop(key, None)
            json.dump(ck, open(CKPT, "w"))
            print(f"  FY{fy}: {st.get('total_rows'):,} rows", flush=True)
    finally:
        s.close()
        print(f"\n  {s.n} request(s), {s.spent:.0f}s")
    got = sum(v.get("rows") or 0 for v in ck["done"].values())
    print(f"  {len(ck['done'])} of {len(YEARS)} years on disk, {got:,} transactions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
