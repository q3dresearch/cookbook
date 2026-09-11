#!/usr/bin/env python3
"""Shares outstanding for each target, so a report can be sized by the company it hit.

    python capture_marketcap.py

Market capitalisation at publication needs two numbers: the price, which the event
study already has, and the share count, which it does not. SEC's XBRL API publishes
`dei:EntityCommonStockSharesOutstanding` per filer, one observation per filing, back
to about 2009 — so the share count in force on a report's date is the most recent
filing before it.

The count is a point-in-time cover-page figure, not a float: it includes insider and
restricted stock, and it is stale by up to a quarter. That is fine for sorting
targets into size bands and wrong for anything needing precision, which is why this
recipe uses it only for bands.

Two limits worth stating. A company that never filed with SEC has no entry at all —
J Capital's Chinese and Hong Kong targets are absent for the same reason they were
absent from the ticker registry. And a company that has since deregistered keeps its
historical filings, so unlike the price source this one does NOT drop the dead.
"""
import json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw"
OUT = RAW / "shares"
# SEC asks for a declared identity rather than a browser string, and 403s without it.
UA = "q3dresearch cookbook research dl.eeee.nv@gmail.com"
CONCEPT = ("https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:010d}/dei/"
           "EntityCommonStockSharesOutstanding.json")
PAUSE = 0.35          # SEC asks for 10 requests/second or fewer; this is far under


def curl(url):
    r = subprocess.run(["curl", "-sS", "-L", "--compressed", "--max-time", "40", "-A", UA, url],
                       capture_output=True, timeout=60)
    return r.stdout.decode("utf-8", "replace")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reg = json.loads((RAW / "sec" / "company_tickers_exchange.json").read_text())
    cik = {}
    for c, name, tick, exch in reg["data"]:
        if tick:
            cik[tick.upper()] = c
    cands = json.loads((RAW / "join_candidates.json").read_text())
    syms = sorted({c["ticker"] for c in cands})
    print(f"  {len(syms)} symbols; {sum(1 for s in syms if s.upper() in cik)} have a CIK")

    log = {}
    for i, s in enumerate(syms, 1):
        f = OUT / f"{s}.json"
        if f.exists():
            log[s] = "cached"
            continue
        c = cik.get(s.upper()) or cik.get(s.split(".")[0].upper())
        if not c:
            log[s] = "no CIK"
            continue
        time.sleep(PAUSE)
        body = curl(CONCEPT.format(cik=c))
        try:
            d = json.loads(body)
        except json.JSONDecodeError:
            log[s] = "not json"
            continue
        units = d.get("units", {}).get("shares", [])
        if not units:
            log[s] = "no share observations"
            continue
        f.write_text(json.dumps([{"end": u["end"], "val": u["val"], "form": u.get("form")}
                                 for u in units]))
        log[s] = f"{len(units)} obs"
        if i % 20 == 0:
            print(f"    {i}/{len(syms)}", flush=True)
    (OUT / "coverage.json").write_text(json.dumps(log, indent=1))
    from collections import Counter
    kinds = Counter("ok" if v[0].isdigit() or v == "cached" else v for v in log.values())
    print("  " + ", ".join(f"{v} {k}" for k, v in kinds.most_common()))


if __name__ == "__main__":
    main()
