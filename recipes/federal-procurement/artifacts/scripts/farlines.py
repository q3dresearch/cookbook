#!/usr/bin/env python3
"""Every FAR dollar line this recipe can test, measured with figure 12's estimator.

Not a chart. `chart-14-farlines.py` draws it. Caches beside the data.

**Why four rules and not one.** Figure 12 shows award values bunching below the simplified
acquisition threshold, and the bunching moving when that threshold moved. One line could be
a coincidence of that line. Three that moved give three natural experiments, and a rule whose
value barely changed gives a control.

**The thresholds are the FAR's, not inferred.** Micro-purchase $3,500 to FY2017 and $10,000
from FY2018; simplified acquisition $150,000 then $250,000; certified cost or pricing data
$750,000 then $2,000,000; the subcontracting-plan floor $700,000 then $750,000 -- a 7% move
against the others' 167% to 186%, which is why it is the control rather than a fourth test.
"""
import collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L, thresh                                                 # noqa: E402

DATA = os.path.join(HERE, "..", "data")
CACHE = os.path.join(DATA, "farlines.json")
YEARS = ("2016", "2017", "2025")
# name, value per year, half-window, and whether the move is big enough to be a test
RULES = [("micro-purchase", {"2016": 3500, "2017": 3500, "2025": 10000}, 2000, True),
         ("simplified acquisition", {"2016": 150000, "2017": 150000, "2025": 250000},
          60000, True),
         ("cost or pricing data", {"2016": 750000, "2017": 750000, "2025": 2000000},
          300000, True),
         ("subcontracting plan", {"2016": 700000, "2017": 700000, "2025": 750000},
          300000, False)]


def positives(y):
    p = os.path.join(DATA, f"civilian-fy{y}.zip")
    if not os.path.exists(p):
        raise SystemExit(f"  civilian-fy{y}.zip missing - run usa2.py {y}")
    acc = collections.defaultdict(float)
    for r in L.transactions(p):
        k = r.get(L.KEY)
        if k:
            acc[k] += L.num(r.get("federal_action_obligation")) or 0.0
    return sorted(v for v in acc.values() if v > 0)


def build():
    out = {"years": list(YEARS), "rules": []}
    V = {}
    for y in YEARS:
        print(f"  folding civilian-fy{y}.zip ...", flush=True)
        V[y] = positives(y)
    out["n"] = {y: len(V[y]) for y in YEARS}
    for name, byyear, half, is_test in RULES:
        vals = sorted({v for v in byyear.values()})
        r = {"name": name, "rule": byyear, "half": half, "is_test": is_test,
             "values": vals, "at": {}}
        for y in YEARS:
            r["at"][y] = {}
            for v in vals:
                e = thresh.excess(V[y], v, half=half)
                r["at"][y][str(v)] = None if e is None else {
                    "excess": e["excess"], "obs": e["obs"], "window_n": e["window_n"]}
        out["rules"].append(r)
    return out


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    d = build()
    tmp = CACHE + ".tmp"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return d


if __name__ == "__main__":
    d = load()
    for r in d["rules"]:
        tag = "test " if r["is_test"] else "ctrl "
        print(f"  {tag}{r['name']:<24}" + "   ".join(
            f"FY{y} @{r['rule'][y]:,}: "
            f"{r['at'][y][str(r['rule'][y])]['excess']:+6.1f}%" for y in d["years"]))
