import os
HERE = os.path.dirname(os.path.abspath(__file__))
RECIPE = os.path.dirname(os.path.dirname(HERE))          # recipes/cfr-staleness
CHARTS = os.path.join(RECIPE, "artifacts", "charts")
# This recipe commits no data. capture.py writes into a work directory and every
# other script reads from the same one: set CFR_WORK, or accept ./work in the
# current directory. Nothing here reaches outside the recipe except that dir.
WORK = os.environ.get("CFR_WORK") or os.path.join(os.getcwd(), "work")
DERIVED = os.path.join(WORK, "derived")
RAW = os.path.join(WORK, "raw")
os.makedirs(DERIVED, exist_ok=True)
import json, subprocess, time, csv
rows=[]
for pg in range(1, 20):
    p=subprocess.run(["curl","-sS","--compressed","--max-time","90",
        f"https://www.ecfr.gov/api/versioner/v1/versions/title-12.json?page={pg}"],
        capture_output=True, text=True)
    d=json.loads(p.stdout)
    rows += d.get("content_versions", [])
    time.sleep(0.5)
cols=["date","amendment_date","issue_date","identifier","name","part","subpart","substantive","removed","type"]
with open(os.path.join(DERIVED, "cfr-title12-version-events.csv"), "w", newline="") as f:
    w=csv.DictWriter(f, cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
print("rows:", len(rows))
ds=sorted(r["amendment_date"] for r in rows if r.get("amendment_date"))
print("amendment_date range:", ds[0], "->", ds[-1])
rm=[r for r in rows if r.get("removed")]
print("removal events:", len(rm), "sections:", len({r["identifier"] for r in rm}))
from collections import Counter
print("removals/yr:", sorted(Counter(r["amendment_date"][:4] for r in rm if r.get("amendment_date")).items()))
print("all events/yr:", sorted(Counter(r["amendment_date"][:4] for r in rows if r.get("amendment_date")).items()))
