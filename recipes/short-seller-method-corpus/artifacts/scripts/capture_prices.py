#!/usr/bin/env python3
"""Daily prices for the report targets, and an honest account of who is missing.

    python capture_prices.py

The event study this feeds — what a target's stock did from 30 trading days before
a report to 30 after — needs three things to line up: a report date, a ticker, and
a price series. The first is free, the second works for a third of reports (see
tickers.py), and the third is the subject of this file.

There is no free daily-price API that covers what this corpus needs. Tested cold:
Stooq now serves a JS challenge, Yahoo returns 429 from shared addresses, Nasdaq's
endpoint returns zero rows, WSJ 401s. stockanalysis.com serves a JSON history
endpoint with 20+ years of daily OHLCV and no key, and that is what this uses.

**Its coverage is not neutral, and the bias points the wrong way for this study.**
The endpoint keys on a company's CURRENT symbol. A target that went bankrupt moved
to OTC under a new one — Zynex is ZYXIQ now, Nikola is NKLAQ, and the old symbol
returns 400. A target that was acquired, taken private, or delisted from a foreign
exchange is not there at all: Sino-Forest, China MediaExpress and Spreadtrum return
nothing under any spelling.

So the companies easiest to price are the ones that survived the report, which is
the opposite of the sample you want when asking whether short reports were right.
Every missing ticker is recorded with its reason so the size of that hole is
visible in the figure rather than quietly dropped.
"""
import json, re, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw"
OUT = RAW / "prices"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/128.0 Safari/537.36")
API = "https://stockanalysis.com/api/symbol/s/{t}/history?period=Daily&range=Max"
PAGE = "https://stockanalysis.com/stocks/{t}/"
PAUSE = 1.4


def curl(url, headers=(), head=False):
    cmd = ["curl", "-sS", "-L" if not head else "-I", "--compressed", "--max-time", "30", "-A", UA]
    for h in headers:
        cmd += ["-H", h]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, timeout=45)
    return r.stdout.decode("utf-8", "replace")


def redirect_symbol(t):
    """Where the site sends an old symbol. A bankruptcy moves ZYXI to /quote/otc/ZYXIQ/,
    so the redirect is a symbol-change map — and a 'Q' suffix is itself a finding."""
    h = curl(PAGE.format(t=t.lower()), head=True)
    m = re.search(r"(?im)^location:\s*(\S+)", h)
    if not m:
        return None
    parts = [p for p in m.group(1).strip().split("/") if p]
    return parts[-1] if parts else None


def history(t):
    body = curl(API.format(t=t.lower()), ("Referer: https://stockanalysis.com/",))
    try:
        d = json.loads(body)
    except json.JSONDecodeError:
        return None, "not json"
    if d.get("status") != 200:
        return None, f"api {d.get('status')}"
    rows = d["data"] if isinstance(d.get("data"), list) else d.get("data", {}).get("data", [])
    return (rows, "") if rows else (None, "empty")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cands = json.loads((RAW / "join_candidates.json").read_text())
    symbols = sorted({c["ticker"] for c in cands})
    print(f"  {len(cands)} report-ticker pairs, {len(symbols)} distinct symbols")
    log = {}
    for i, sym in enumerate(symbols, 1):
        f = OUT / f"{sym}.json"
        if f.exists():
            log[sym] = {"outcome": "cached"}
            continue
        time.sleep(PAUSE)
        rows, why = history(sym)
        if rows:
            f.write_text(json.dumps(rows))
            ts = sorted(r["t"] for r in rows)
            log[sym] = {"outcome": "listed", "rows": len(rows), "from": ts[0], "to": ts[-1]}
        else:
            # Not under that symbol. Ask the site where it went.
            time.sleep(PAUSE)
            moved = redirect_symbol(sym)
            if moved and moved.upper() != sym.upper():
                log[sym] = {"outcome": "renamed", "now": moved.upper(),
                            "reason": "bankruptcy or symbol change; history not served under either"}
            else:
                log[sym] = {"outcome": "absent", "reason": why}
        if i % 10 == 0:
            print(f"    {i}/{len(symbols)}", flush=True)
    (OUT / "coverage.json").write_text(json.dumps(log, indent=1))
    from collections import Counter
    c = Counter(v["outcome"] for v in log.values())
    print("  " + ", ".join(f"{v} {k}" for k, v in c.most_common()))
    print(f"  -> {OUT}")


if __name__ == "__main__":
    main()
