#!/usr/bin/env python3
"""Did the target later concede the point, in a filing it had to make?

    python capture_outcomes.py

This recipe can say what a firm claimed to look at and what the market did about it.
It could not say whether the firm was RIGHT, and the reason was that no outcome
variable existed. This is the outcome variable.

SEC's submissions API returns every filing a company has made, each 8-K carrying its
ITEM codes, and two of those items are a company conceding something in writing:

    Item 4.02   non-reliance on previously issued financial statements — a restatement
    Item 3.01   notice of delisting or failure to satisfy a listing rule

Neither is a verdict on the allegation. A delisting notice can follow a late filing
or a share price under a dollar; a restatement can be an honest error. And absence is
not exoneration — most short-seller claims are not accounting claims at all. What
these are is corroboration that is hard, dated, mandatory and free, which is more
than a price series can offer.

Four softer items are collected alongside for context: auditor changes, officer
departures, impairments and bankruptcies. Filings are split at the report date so
that "before" can be compared against a control sample and "after" read as outcome.

One limit the API imposes: it returns roughly the most recent 1000 filings, so older
history is truncated for companies that file often.
"""
import json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw"
sys.path.insert(0, str(HERE))
import validate_tickers as V

UA = "q3dresearch cookbook research dl.eeee.nv@gmail.com"
PAUSE = 0.3                     # SEC asks for 10 requests/second or fewer
ITEMS = {"4.02": "restatement", "3.01": "delisting notice", "1.03": "bankruptcy",
         "4.01": "auditor change", "5.02": "officer departure", "2.06": "impairment"}
HARD = {"restatement", "delisting notice", "bankruptcy"}


def submissions(cik):
    r = subprocess.run(["curl", "-sS", "--max-time", "35", "-A", UA,
                        f"https://data.sec.gov/submissions/CIK{cik:010d}.json"],
                       capture_output=True, timeout=50)
    try:
        return json.loads(r.stdout.decode("utf-8", "replace"))
    except Exception:
        return None


def main():
    reg = V.registry()
    cands = json.loads((RAW / "join_candidates.json").read_text())
    tg = {}
    for c in cands:
        hit = reg.get(c["ticker"]) or reg.get(c["ticker"].split(".")[0])
        if hit and c["ticker"] not in tg:
            tg[c["ticker"]] = (hit["cik"], c["date"], c["firm"])
    print(f"  {len(tg)} targets with a CIK")

    res = {}
    for i, (sym, (cik, date, firm)) in enumerate(sorted(tg.items()), 1):
        time.sleep(PAUSE)
        d = submissions(cik)
        if not d:
            print(f"    {sym}: no submissions")
            continue
        rec = d["filings"]["recent"]
        before, after = [], []
        for k in range(len(rec["form"])):
            it = rec["items"][k] or ""
            fd = rec["filingDate"][k]
            for code, lab in ITEMS.items():
                if code in it:
                    (after if fd > date else before).append((lab, fd))
        nt = [rec["filingDate"][k] for k in range(len(rec["form"]))
              if rec["form"][k].startswith("NT ")]
        res[sym] = {"cik": cik, "date": date, "firm": firm,
                    "before": sorted(before, key=lambda x: x[1]),
                    "after": sorted(after, key=lambda x: x[1]),
                    "late_filings_before": sum(1 for x in nt if x < date),
                    "late_filings_after": sum(1 for x in nt if x >= date),
                    "filings_indexed": len(rec["form"])}
        if i % 20 == 0:
            print(f"    {i}/{len(tg)}", flush=True)
    (RAW / "target_outcomes.json").write_text(json.dumps(res, indent=1))
    bad = [s for s, v in res.items() if any(l in HARD for l, _ in v["after"])]
    print(f"  {len(res)} targets read; {len(bad)} filed a restatement, delisting notice "
          f"or bankruptcy after the report ({len(bad)/len(res):.0%})")


if __name__ == "__main__":
    main()
