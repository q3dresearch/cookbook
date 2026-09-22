#!/usr/bin/env python3
"""FY2016 against FY2025 by award-value band, cached beside the data.

Not a chart. `chart-16-comparability.py` draws it.

**Why this exists.** Eight of this recipe's figures are built on FY2016 alone, and FY2025
has 41% fewer awards and 84% more dollars from the same eleven departments under the same
collapse rule. Until that gap is explained, every cross-year claim is unsafe and every
single-year claim is a statement about FY2016 rather than about federal procurement.
"""
import collections, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L                                                         # noqa: E402

DATA = os.path.join(HERE, "..", "data")
CACHE = os.path.join(DATA, "comparability.json")
YEARS = ("2016", "2025")
# Bands straddle both micro-purchase thresholds on purpose: $3,500 through FY2017 and
# $10,000 from FY2018. Below that line a purchase goes on a card and is not reported as a
# contract action at all, so the threshold moving is a reporting change, not a behaviour one.
EDGES = [0, 1000, 3500, 10000, 31623, 100000, 316228, 1e6, 3.162e6, 1e7, 1e8,
         float("inf")]
NAMES = ["under $1k", "$1k to $3.5k", "$3.5k to $10k", "$10k to $32k", "$32k to $100k",
         "$100k to $316k", "$316k to $1m", "$1m to $3.2m", "$3.2m to $10m",
         "$10m to $100m", "over $100m"]
MICRO = {"2016": 3500, "2025": 10000}


def band(v):
    for i in range(len(EDGES) - 1):
        if EDGES[i] <= v < EDGES[i + 1]:
            return i
    return len(EDGES) - 2


def fold(y):
    p = os.path.join(DATA, f"civilian-fy{y}.zip")
    if not os.path.exists(p):
        raise SystemExit(f"  civilian-fy{y}.zip missing - run usa2.py {y}")
    print(f"  folding civilian-fy{y}.zip ...", flush=True)
    acc = collections.defaultdict(float)
    tx = collections.Counter()
    par = {}
    for r in L.transactions(p):
        k = r.get(L.KEY)
        if not k:
            continue
        acc[k] += L.num(r.get("federal_action_obligation")) or 0.0
        tx[k] += 1
        if k not in par:
            par[k] = bool((r.get("parent_award_id_piid") or "").strip())
    pos = [v for v in acc.values() if v > 0]
    b = collections.Counter(band(v) for v in pos)
    d = collections.Counter()
    for k, v in acc.items():
        if v > 0:
            d[band(v)] += v
    return {"awards": len(acc), "transactions": sum(tx.values()),
            "positive": len(pos), "net": sum(acc.values()),
            "median_positive": sorted(pos)[len(pos) // 2],
            "tx_per_award": sum(tx.values()) / len(acc),
            "with_parent": sum(1 for v in par.values() if v) / len(par),
            "counts": [b[i] for i in range(len(NAMES))],
            "dollars": [d[i] for i in range(len(NAMES))]}


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    d = {"names": NAMES, "edges": EDGES[:-1] + [None], "micro": MICRO,
         "years": {y: fold(y) for y in YEARS}}
    tmp = CACHE + ".tmp"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return d


if __name__ == "__main__":
    d = load()
    a, b = d["years"]["2016"], d["years"]["2025"]
    loss = a["positive"] - b["positive"]
    print(f"  FY2016 {a['positive']:,} positive awards, ${a['net']/1e9:.1f}bn, "
          f"median ${a['median_positive']:,.0f}")
    print(f"  FY2025 {b['positive']:,} positive awards, ${b['net']/1e9:.1f}bn, "
          f"median ${b['median_positive']:,.0f}")
    under = sum(a["counts"][:3]) - sum(b["counts"][:3])
    print(f"  net loss {loss:,}; awards under $10,000 account for {under/loss:.0%} of it")
