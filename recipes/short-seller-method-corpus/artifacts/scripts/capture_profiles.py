#!/usr/bin/env python3
"""What the targets ARE, against companies nobody shorted.

    python capture_profiles.py

An earlier pass at this question compared targets and controls on the only attribute
both sets happened to carry: which exchange they list on. That found nothing, and
finding nothing was uninformative — the exchange a stock trades on is not a fact about
the business. It was measuring the easy thing and reporting the null as an answer.

SEC's submissions endpoint carries the facts that matter, on the same call already
used for filing history:

    sic / sicDescription    the industry the company files under
    ownerOrg                SEC's own desk assignment, e.g. "09 Crypto Assets"
    category                Large accelerated / accelerated / non-accelerated filer,
                            which is a size class defined by public float
    stateOfIncorporation    Nevada against Delaware is a governance signal in itself
    entityType              operating, shell, and so on

and `companyconcept` adds the financials a report would actually be arguing about —
revenue and net income at the last filing before the report date, so a target is
described as it stood when it was picked rather than as it stands now.

Targets and controls are read identically and written to one file so the comparison
cannot drift apart.
"""
import json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw"
UA = "q3dresearch cookbook research dl.eeee.nv@gmail.com"
PAUSE = 0.3
PROFILE = ("sic", "sicDescription", "ownerOrg", "category", "stateOfIncorporation",
           "entityType", "name", "fiscalYearEnd")
CONCEPTS = {"Revenues": "revenue", "NetIncomeLoss": "net_income", "Assets": "assets"}


def get(url):
    r = subprocess.run(["curl", "-sS", "--max-time", "35", "-A", UA, url],
                       capture_output=True, timeout=50)
    try:
        return json.loads(r.stdout.decode("utf-8", "replace"))
    except Exception:
        return None


def concept_at(cik, tag, before):
    """The most recent reported value dated on or before `before`."""
    d = get(f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:010d}/us-gaap/{tag}.json")
    if not d:
        return None
    vals = []
    for unit, rows in d.get("units", {}).items():
        for r in rows:
            if r.get("end") and (before is None or r["end"] <= before) and r.get("val") is not None:
                vals.append((r["end"], r["val"]))
    return max(vals)[1] if vals else None


def profile(cik, report_date=None, with_financials=True):
    d = get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
    if not d:
        return None
    out = {k: d.get(k) for k in PROFILE}
    out["cik"] = cik
    if with_financials:
        for tag, name in CONCEPTS.items():
            time.sleep(PAUSE)
            out[name] = concept_at(cik, tag, report_date)
    return out


def main():
    outcomes = json.loads((RAW / "target_outcomes.json").read_text())
    controls = json.loads((RAW / "control_firms.json").read_text())
    dest = RAW / "profiles.json"
    done = json.loads(dest.read_text()) if dest.exists() else {"targets": {}, "controls": {}}

    print(f"  {len(outcomes)} targets, {len(controls)} controls")
    for i, (sym, v) in enumerate(sorted(outcomes.items()), 1):
        if sym in done["targets"]:
            continue
        time.sleep(PAUSE)
        p = profile(v["cik"], v["date"])
        if p:
            done["targets"][sym] = {**p, "report_date": v["date"], "firm": v["firm"]}
        if i % 15 == 0:
            print(f"    targets {i}/{len(outcomes)}", flush=True)
            dest.write_text(json.dumps(done, indent=1))
    dest.write_text(json.dumps(done, indent=1))

    for i, (sym, v) in enumerate(sorted(controls.items()), 1):
        if sym in done["controls"]:
            continue
        time.sleep(PAUSE)
        # Controls have no report date, so their financials are the latest available.
        p = profile(v["cik"], None)
        if p:
            done["controls"][sym] = p
        if i % 15 == 0:
            print(f"    controls {i}/{len(controls)}", flush=True)
            dest.write_text(json.dumps(done, indent=1))
    dest.write_text(json.dumps(done, indent=1))
    print(f"  {len(done['targets'])} target profiles, {len(done['controls'])} control profiles")


if __name__ == "__main__":
    main()
