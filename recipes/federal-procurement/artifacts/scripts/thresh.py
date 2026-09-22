#!/usr/bin/env python3
"""Excess mass just below a dollar threshold, swept across candidate values, per year.

Not a chart. `chart-10-thresholds.py` draws it. Caches beside the data.

**The design.** The simplified acquisition threshold was $150,000 through FY2017 and
$250,000 from FY2018. A raw "more awards below than above" ratio proves nothing, because
contract values decline in frequency as they grow -- more below is the null. So each
candidate value gets a local trend fitted on a +/-$60,000 window with the two bins either
side of the threshold held out, and the excess is the observed count in the two bins just
below against what that trend predicts.

**Why the sweep rather than two numbers.** Testing only the real thresholds cannot
distinguish a rule effect from a round-number effect, because the rules sit on round
numbers. Sweeping every $10,000 step from $80,000 to $400,000 shows whether the peak
*moves when the rule moves* and whether values with no rule behind them stay flat.
"""
import bisect, collections, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L                                                         # noqa: E402

DATA = os.path.join(HERE, "..", "data")
CACHE = os.path.join(DATA, "thresholds.json")
GRID = list(range(80000, 401000, 10000))
BINW = 5000
HALF = 60000
# the rule in force in each fiscal year, from the FAR's own history
RULE = {"2015": 150000, "2016": 150000, "2017": 150000,
        "2024": 250000, "2025": 250000}


def positives(path):
    acc = collections.defaultdict(float)
    for r in L.transactions(path):
        k = r.get(L.KEY)
        if k:
            acc[k] += L.num(r.get("federal_action_obligation")) or 0.0
    return sorted(v for v in acc.values() if v > 0), len(acc)


def excess(v, thr, half=HALF, nb=24):
    """Observed count in the two bins below `thr`, against a locally fitted trend."""
    lo, hi = thr - half, thr + half
    step = 2 * half / nb
    xs = [lo + step * (i + 0.5) for i in range(nb)]
    c = [0] * nb
    for x in v[bisect.bisect_left(v, lo):bisect.bisect_left(v, hi)]:
        c[min(int((x - lo) / step), nb - 1)] += 1
    mid = nb // 2
    keep = [i for i in range(nb) if abs(i - mid) > 1 and c[i] > 0]
    if len(keep) < 8 or sum(c) < 400:
        return None
    X = [xs[i] for i in keep]
    Y = [math.log(c[i]) for i in keep]
    mx, my = sum(X) / len(X), sum(Y) / len(Y)
    b = sum((x - mx) * (y - my) for x, y in zip(X, Y)) / sum((x - mx) ** 2 for x in X)
    a = my - b * mx
    jb = [i for i in range(nb) if 0 < mid - i <= 2]
    o = sum(c[i] for i in jb)
    e = sum(math.exp(a + b * xs[i]) for i in jb)
    return {"excess": (o / e - 1) * 100, "obs": o, "exp": e, "window_n": sum(c)}


def wide(v):
    """Share of the $60k-$400k window in each $10,000 bin.

    The raw evidence, normalised so two years of very different size overlay on one axis.
    The derived excess exists because a reader cannot eyeball a 1.3x step against a
    declining background; it does not exist because the step is invisible.
    """
    lo, hi, bw = 60000, 400000, 10000
    nb = (hi - lo) // bw
    c = [0] * nb
    for x in v[bisect.bisect_left(v, lo):bisect.bisect_left(v, hi)]:
        c[int((x - lo) // bw)] += 1
    tot = sum(c) or 1
    return {"lo": lo, "binw": bw, "n": tot, "share": [x / tot * 100 for x in c]}


def step(w, thr):
    """Share in the bin just below a value, over the share just above it."""
    i = (thr - w["lo"]) // w["binw"]
    return w["share"][i - 1] / w["share"][i] if w["share"][i] else None


def histogram(v, thr):
    """Counts in $5,000 bins either side of the year's own rule, for the shape panel."""
    lo, hi = thr - HALF, thr + HALF
    nb = int(2 * HALF / BINW)
    c = [0] * nb
    for x in v[bisect.bisect_left(v, lo):bisect.bisect_left(v, hi)]:
        c[min(int((x - lo) / BINW), nb - 1)] += 1
    return {"lo": lo, "binw": BINW, "counts": c}


def build(years):
    out = {"grid": GRID, "rule": RULE, "years": {}}
    for y in years:
        p = os.path.join(DATA, f"civilian-fy{y}.zip")
        if not os.path.exists(p):
            print(f"  civilian-fy{y}.zip missing, skipping", flush=True)
            continue
        print(f"  folding civilian-fy{y}.zip ...", flush=True)
        v, n_awards = positives(p)
        out["years"][y] = {
            "n_awards": n_awards, "n_positive": len(v),
            "sweep": {str(t): excess(v, t) for t in GRID},
            "hist": histogram(v, RULE[y]),
            "wide": wide(v),
            "at_rule": excess(v, RULE[y]),
            "at_other": excess(v, 250000 if RULE[y] == 150000 else 150000)}
        w = out["years"][y]["wide"]
        out["years"][y]["step_150k"] = step(w, 150000)
        out["years"][y]["step_250k"] = step(w, 250000)
    return out


def load(years=("2016", "2017", "2025")):
    if os.path.exists(CACHE):
        d = json.load(open(CACHE))
        if all(y in d.get("years", {}) for y in years):
            return d
    d = build(years)
    tmp = CACHE + ".tmp"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return d


if __name__ == "__main__":
    d = load()
    for y, g in sorted(d["years"].items()):
        pk = max(((int(t), v["excess"]) for t, v in g["sweep"].items() if v),
                 key=lambda r: r[1])
        print(f"  FY{y}: rule ${d['rule'][y]:,}  at-rule {g['at_rule']['excess']:+.0f}%  "
              f"elsewhere {g['at_other']['excess']:+.0f}%  sweep peak ${pk[0]:,} {pk[1]:+.0f}%")
        print(f"         raw step below $150k {g['step_150k']:.2f}x, "
              f"below $250k {g['step_250k']:.2f}x")
