#!/usr/bin/env python3
"""A control sample: companies nobody shorted, measured the same way as the targets.

    python capture_control_firms.py

Describing targets cannot say what ATTRACTS a short seller. Every measurement in this
recipe so far is on companies that were picked, and a sample selected on the outcome
cannot identify the selection. What it needs is the same measurements on companies
that were passed over.

So: draw companies at random from SEC's registry, drop any that a firm in this corpus
targeted, and read the same filing history — auditor changes, officer departures,
impairments, restatements, delisting notices, late filings. The comparison is crude
by construction (no sector match, no size match, no era match) and it is still the
difference between a description and a claim.

Sampling is seeded so the draw is reproducible, and the seed is in the file rather
than in someone's shell history.
"""
import json, random, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw"
UA = "q3dresearch cookbook research dl.eeee.nv@gmail.com"
N = 140
SEED = 20260912
FLAG_ITEMS = {"4.01": "auditor change", "5.02": "officer departure", "2.06": "impairment",
              "1.03": "bankruptcy", "4.02": "restatement", "3.01": "delisting notice"}


def submissions(cik):
    r = subprocess.run(["curl", "-sS", "--max-time", "35", "-A", UA,
                        f"https://data.sec.gov/submissions/CIK{cik:010d}.json"],
                       capture_output=True, timeout=50)
    try:
        return json.loads(r.stdout.decode("utf-8", "replace"))
    except Exception:
        return None


def main():
    reg = json.loads((RAW / "sec" / "company_tickers_exchange.json").read_text())
    targets = {t.upper() for m in json.loads((RAW / "tickers.json").read_text()).values()
               for t in m.values()}
    pool = [(c, name, tick, exch) for c, name, tick, exch in reg["data"]
            if tick and tick.upper() not in targets]
    rng = random.Random(SEED)
    pick = rng.sample(pool, min(N, len(pool)))
    print(f"  {len(pool):,} filers not targeted; drawing {len(pick)} with seed {SEED}")

    out = {}
    for i, (cik, name, tick, exch) in enumerate(pick, 1):
        time.sleep(0.3)
        d = submissions(cik)
        if not d:
            continue
        rec = d["filings"]["recent"]
        flags = []
        for k in range(len(rec["form"])):
            it = rec["items"][k] or ""
            for code, lab in FLAG_ITEMS.items():
                if code in it:
                    flags.append((lab, rec["filingDate"][k]))
        late = sum(1 for k in range(len(rec["form"])) if rec["form"][k].startswith("NT "))
        out[tick.upper()] = {"cik": cik, "name": name, "exchange": exch,
                             "flags": sorted(flags, key=lambda x: x[1]),
                             "late_filings": late, "filings_indexed": len(rec["form"])}
        if i % 25 == 0:
            print(f"    {i}/{len(pick)}", flush=True)
    (RAW / "control_firms.json").write_text(json.dumps(out, indent=1))
    print(f"  {len(out)} control firms read -> raw/control_firms.json")


if __name__ == "__main__":
    main()
