#!/usr/bin/env python3
"""Public float for targets and controls, as it stood before the report.

    python capture_float.py

Market cap is the obvious size axis and this recipe only had it for targets -- it was
built from captured prices, and no prices were captured for the 139 control filers.
`dei:EntityPublicFloat` replaces it: every domestic filer states its own public float
on the cover of its 10-K, it is in XBRL, and a single-concept request is 2-4 KB rather
than the 2 MB a full `companyfacts` pull costs. 216 companies take about two minutes.

Point-in-time, by FILED date, for the same reason as everything else here: a float
first reported after the report date was not public when the short seller wrote.

**Foreign private issuers do not file it.** Companies on 20-F or 40-F return 404, so
the coverage gap is not random -- it removes exactly the Canadian and Chinese filers
this corpus is full of. That is recorded per company rather than silently dropped, so
any figure built on this can state who is missing.
"""
import json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw"
UA = "q3dresearch cookbook research dl.eeee.nv@gmail.com"
PAUSE = 0.25


def get(cik):
    try:
        r = subprocess.run(
            ["curl", "-sS", "--max-time", "25", "-A", UA,
             f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:010d}/dei/EntityPublicFloat.json"],
            capture_output=True, timeout=40)
        return json.loads(r.stdout.decode("utf-8", "replace"))
    except Exception:
        return None


def float_at(cik, before):
    d = get(cik)
    if not d:
        return {"status": "not filed (usually a foreign private issuer)"}
    rows = [r for u in d.get("units", {}).values() for r in u
            if r.get("val") is not None and (not before or (r.get("filed") or "9999") <= before)]
    if not rows:
        return {"status": "none filed before the report"}
    best = max(rows, key=lambda r: r.get("filed") or "")
    return {"status": "ok", "float": best["val"], "as_of": best.get("end"),
            "filed": best.get("filed")}


def run(items, dest, label):
    done = json.loads(dest.read_text()) if dest.exists() else {}
    todo = [x for x in items if x[0] not in done]
    print(f"  {label}: {len(todo)} to read ({len(done)} cached)")
    for i, (key, cik, before) in enumerate(todo, 1):
        time.sleep(PAUSE)
        done[key] = {"cik": cik, **float_at(cik, before)}
        if i % 25 == 0:
            print(f"    {label} {i}/{len(todo)}", flush=True)
            dest.write_text(json.dumps(done, indent=1))
    dest.write_text(json.dumps(done, indent=1))
    ok = sum(1 for v in done.values() if v["status"] == "ok")
    print(f"  {label}: {ok}/{len(done)} with a float filed before the cutoff")
    return done


def main():
    T = json.loads((RAW / "jackpot_targets.json").read_text())
    C = json.loads((RAW / "jackpot_controls.json").read_text())
    run([(k, v["cik"], v["as_of"]) for k, v in sorted(T.items())],
        RAW / "float_targets.json", "targets")
    run([(k, v["cik"], v["as_of"]) for k, v in sorted(C.items())],
        RAW / "float_controls.json", "controls")


if __name__ == "__main__":
    main()
