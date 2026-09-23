#!/usr/bin/env python3
"""The ATB collapsed to what the figures need, so the 88 MB CSV is optional.

    python3 atbfold.py

**What ATB is.** NREL's Annual Technology Baseline is a **model output**, not a register of
transactions. Nobody paid these prices; NREL assembled them from market data, engineering
estimates and its own projections. Of the 30 years it covers, **2021 to 2023 are the vintage
year's estimates and 2024 to 2050 are projections** -- a distinction that disappears the
moment someone quotes "the 2035 cost of wind" without saying so.

**Why a fold rather than a lookup.** There is no such thing as "the" ATB cost of a
technology. Land-based wind in 2030 has **120 published LCOE values spanning 23.5-fold**,
and every one of them is the official number for some combination of:

- `scenario` -- Conservative, Moderate or Advanced technology progress
- `core_metric_case` -- Market (tax credits counted) or R&D (not counted)
- `crpyears` -- the cost recovery period the financing assumes
- `techdetail` -- the resource class, which for wind and solar means where you put it

So the fold keeps the **spread and its decomposition**, not a value. For each technology,
parameter and year it stores the min, median and max across all cells, and the median within
each level of each dimension -- which is what says whether the number moves because of
geography, tax policy, financing or engineering optimism.

**The coverage matrix is part of the output, not a diagnostic.** Every fossil technology
here -- `NaturalGas_FE`, `Coal_FE` and both retrofit families -- publishes CAPEX, OCC, fixed
and variable O&M and a heat rate, and **no LCOE and no capacity factor**. Both of those
depend on how often the plant is dispatched and what the fuel costs, and ATB assumes neither.
Storage is missing them for the same reason and also reports its capital cost as **OCC rather
than CAPEX**, so a matrix that looks only for CAPEX reports storage as having no capital cost
at all. It has one, under the other name.

The consequence is worth stating plainly: **the "renewables are cheaper than gas" comparison
cannot be made inside this file.** Anyone who has made it brought the gas number from
somewhere else, and the comparison inherits every assumption that source made about fuel
price and capacity factor. The matrix is how a reader finds that out first.
"""
import collections, csv, json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
SRC = os.path.join(DATA, "atb-2023.csv")
CACHE = os.path.join(DATA, "atb-folded.json")

PARAMS = ("CAPEX", "OCC", "LCOE", "CF", "Fixed O&M", "Variable O&M", "Heat Rate")
DIMS = {"scenario": "scenario", "case": "core_metric_case", "crp": "crpyears",
        "detail": "techdetail"}
FOCUS = "2030"                    # the cross-section year the figures cut at
SERIES = [str(y) for y in range(2022, 2051, 2)]
VINTAGE_LAST_HISTORICAL = 2023    # everything after this is projection, and must be drawn so


def build():
    if not os.path.exists(SRC):
        raise SystemExit("  atb-2023.csv missing - run atb.py")
    cells = collections.defaultdict(list)
    cover = collections.defaultdict(collections.Counter)
    units = {}
    csv.field_size_limit(1 << 24)
    with open(SRC, encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            p, t, y = r["core_metric_parameter"], r["technology"], r["core_metric_variable"]
            cover[t][p] += 1
            if p not in PARAMS:
                continue
            try:
                v = float(r["value"])
            except (TypeError, ValueError):
                continue
            units.setdefault((t, p), r["units"])
            if y == FOCUS or y in SERIES:
                cells[(t, p, y)].append(
                    (v, r["scenario"], r["core_metric_case"], r["crpyears"],
                     r["techdetail"]))

    out = {"vintage": 2023, "focus": FOCUS, "last_historical": VINTAGE_LAST_HISTORICAL,
           "cover": {t: dict(c) for t, c in cover.items()},
           "units": {f"{t}|{p}": u for (t, p), u in units.items()}, "cell": {}}
    idx = {"scenario": 1, "case": 2, "crp": 3, "detail": 4}
    for (t, p, y), rows in cells.items():
        vs = [r[0] for r in rows]
        rec = {"n": len(vs), "min": min(vs), "med": statistics.median(vs), "max": max(vs)}
        for dim, i in idx.items():
            g = collections.defaultdict(list)
            for r in rows:
                g[r[i]].append(r[0])
            meds = {k: statistics.median(v) for k, v in g.items()}
            if len(meds) > 1:
                rec[dim] = meds
        out["cell"][f"{t}|{p}|{y}"] = rec
    return out


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    print("  folding the ATB (one pass over 500,544 rows) ...", flush=True)
    d = build()
    tmp = CACHE + ".tmp"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return d


def spread(d, tech, param, year=None):
    """The cell record, or None. `span` is max/min: how far apart the official numbers are."""
    r = d["cell"].get(f"{tech}|{param}|{year or d['focus']}")
    if r:
        r = dict(r)
        r["span"] = r["max"] / r["min"] if r["min"] else None
    return r


def drivers(rec):
    """Each dimension's own max/min across its level medians, largest first."""
    out = []
    for dim in ("detail", "case", "scenario", "crp"):
        m = rec.get(dim)
        if not m or len(m) < 2:
            continue
        lo, hi = min(m.values()), max(m.values())
        if lo:
            out.append((hi / lo, dim, min(m, key=m.get), max(m, key=m.get), lo, hi))
    out.sort(reverse=True)
    return out


NICE = {"detail": "where you put it", "case": "whether tax credits count",
        "scenario": "technology optimism", "crp": "the financing period"}


def main():
    d = load()
    print(f"\n  ATB vintage {d['vintage']}, cross-section {d['focus']}, "
          f"{len(d['cell']):,} folded cells")
    print(f"\n  HOW FAR APART ARE THE OFFICIAL NUMBERS, {d['focus']}")
    print(f"  {'technology':<30}{'param':<12}{'cells':>7}{'min':>10}{'median':>10}"
          f"{'max':>10}{'span':>8}")
    techs = sorted({k.split("|")[0] for k in d["cell"]})
    for t in techs:
        for p in ("LCOE", "CAPEX"):
            r = spread(d, t, p)
            if not r:
                continue
            print(f"  {t:<30}{p:<12}{r['n']:>7}{r['min']:>10,.1f}{r['med']:>10,.1f}"
                  f"{r['max']:>10,.1f}{r['span']:>7.1f}x")
    print(f"\n  WHAT MOVES IT, {d['focus']} LCOE")
    for t in ("LandbasedWind", "UtilityPV", "OffShoreWind", "Geothermal", "Nuclear"):
        r = spread(d, t, "LCOE")
        if not r:
            continue
        print(f"  {t}  ({r['span']:.1f}x overall, {r['n']} numbers)")
        for span, dim, klo, khi, lo, hi in drivers(r):
            print(f"      {NICE[dim]:<28}{span:>5.2f}x   {klo} {lo:,.1f}  ->  "
                  f"{khi} {hi:,.1f}")
    print(f"\n  WHAT EACH TECHNOLOGY PUBLISHES")
    key = ("CAPEX", "OCC", "LCOE", "CF", "Fixed O&M", "Variable O&M", "Heat Rate")
    print(f"  {'technology':<30}" + "".join(f"{k[:9]:>11}" for k in key))
    for t in sorted(d["cover"]):
        c = d["cover"][t]
        print(f"  {t:<30}" + "".join(f"{(str(c[k]) if c.get(k) else '--'):>11}"
                                     for k in key))
    return 0


if __name__ == "__main__":
    sys.exit(main())
