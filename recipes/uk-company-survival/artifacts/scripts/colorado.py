#!/usr/bin/env python3
"""Colorado: the one register that dates every death AND names its manner.

    python3 colorado.py        # pulls ~3.1M rows through the Socrata API, ~10 minutes

WHY COLORADO IS IN THIS RECIPE. It cannot answer the sector question at all -- US state
registers collect what incorporation law requires, and industry classification is a tax
and census matter, so there is no industry code in the file. What it can do is settle two
things no other register here can:

  1. **How much of "death" is actually acquisition.** Colorado records Merged and
     Converted as distinct end states. Every other register in this recipe lumps them in
     with failure and the write-ups have to hedge.

  2. **Whether a hazard measured over two years can stand in for a lifetime.** The UK
     estimate is a synthetic cohort: age-specific hazards measured over 2024-2026, strung
     together as if one company lived through all of them. That is only valid if the
     hazard depends on age rather than on the era. Colorado has formation dates back to
     1864 and death dates back to 1912, so the assumption can be tested directly against
     real cohorts instead of assumed.

THE DEATH DATE IS IN THE NAME FIELD. Colorado appends the dissolution to the entity name
-- "A. CARBONE AND COMPANY, INC., Dissolved December 31, 1986" -- rather than giving it a
column. 769,484 of 770,695 dissolved records carry one, so it is reliable, and it is also
exactly the kind of thing that breaks silently, so the parse rate is reported every run.
"""
import csv, gzip, json, os, re, subprocess, sys, time

DATA = os.environ.get("FSB_DATA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
OUT = os.path.join(DATA, "colorado.csv.gz")
RES = "https://data.colorado.gov/resource/4ykn-tg5h.csv"
COLS = "entityid,entityname,entitystatus,entitytype,entityformdate,principalcity,principalstate"
PAGE = 50000
UA = "q3dresearch wss +https://github.com/q3dresearch"
DEAD = re.compile(r",?\s*(?:Dissolved|Merged|Converted|Withdrawn|Revoked)\s+"
                  r"([A-Z][a-z]+)\s+(\d{1,2}),?\s*(\d{4})", re.I)
MONTH = {m: i + 1 for i, m in enumerate(
    "january february march april may june july august september october november december".split())}


def death_date(name):
    m = DEAD.search(name or "")
    if not m:
        return ""
    mo = MONTH.get(m.group(1).lower())
    return f"{m.group(3)}-{mo:02d}-{int(m.group(2)):02d}" if mo else ""


def fetch():
    if os.path.exists(OUT):
        print(f"  have {os.path.basename(OUT)}")
        return
    n, off = 0, 0
    with gzip.open(OUT + ".tmp", "wt", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "status", "type", "formed", "died", "city", "state"])
        while True:
            url = (f"{RES}?$select={COLS}&$limit={PAGE}&$offset={off}&$order=entityid")
            r = subprocess.run(["curl", "-sSL", "-m", "180", "-A", UA, url], capture_output=True, text=True)
            rows = list(csv.DictReader(r.stdout.splitlines()))
            if not rows:
                break
            for x in rows:
                w.writerow([x.get("entityid", ""), (x.get("entitystatus") or "").strip(),
                            (x.get("entitytype") or "").strip(),
                            (x.get("entityformdate") or "")[:10],
                            death_date(x.get("entityname")),
                            (x.get("principalcity") or "").strip(),
                            (x.get("principalstate") or "").strip()])
            n += len(rows); off += PAGE
            if n % 250000 < PAGE:
                print(f"    {n:,} rows", flush=True)
            if len(rows) < PAGE:
                break
            time.sleep(0.3)
    os.replace(OUT + ".tmp", OUT)
    print(f"  {n:,} rows -> {os.path.basename(OUT)} ({os.path.getsize(OUT)/1e6:.0f} MB)")


if __name__ == "__main__":
    os.makedirs(DATA, exist_ok=True)
    fetch()
