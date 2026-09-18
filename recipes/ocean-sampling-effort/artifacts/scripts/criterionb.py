#!/usr/bin/env python3
"""Could criterion B have produced these listings? A lower bound on area of occupancy.

    python3 criterionb.py      # fetch and cache (background; ~600 grid pulls)

IUCN assigns a threatened category under any one of five criteria, and the thresholds are
published (Categories and Criteria v3.1, portals.iucn.org/library RL-2001-001-2nd.pdf):

  A  population size reduction      CR >=90%/80%, EN >=70%/50%, VU >=50%/30%
  B  geographic range               B1 extent of occurrence  CR <100, EN <5,000, VU <20,000 km2
                                    B2 area of occupancy     CR <10,  EN <500,   VU <2,000 km2
  C  small population and decline   CR <250, EN <2,500, VU <10,000 mature individuals
  D  very small population          CR <50,  EN <250,   VU <1,000 mature individuals
  E  quantitative extinction risk   CR >=50% in 10 yr, EN >=20% in 20 yr, VU >=10% in 100 yr

**Four of the five need abundance, and OBIS has none.** A, C, D and E all rest on counts of
mature individuals or their rate of change. This register is presence-only with uncontrolled
effort, so it cannot supply any of them, at any quality. Criterion B is the only one whose
threshold is spatial, and therefore the only one this data can even be compared against.

**Even B is not decidable here.** The area threshold alone never lists a species: B additionally
requires **at least two of** (a) severe fragmentation or few locations, (b) continuing decline in
range, habitat, locations or individuals, (c) extreme fluctuations. Fragmentation and decline are
not readable from a presence-only register with no effort control. So OBIS can rule a species
*out* of criterion B and can never rule one in.

**Which makes one test available, and it only runs one way.** Occupied geohash cells at
precision 5 measure 4.75 x 4.86 km, about 23 km2 -- larger than the 2 x 2 km grid IUCN
recommends for area of occupancy. Every occupied cell therefore contains at least one occupied
2 km square, so `cells x 4 km2` is a **strict lower bound** on area of occupancy. If that lower
bound already exceeds the B2 threshold for a species' category, criterion B2 cannot have been
what listed it, and the listing must rest on A, C, D or E -- none of which are visible here.
The converse does not hold: a small measured area may only mean nobody has looked.
"""
import json, os, sys, time, urllib.parse, urllib.request
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("OBIS_DATA") or os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "criterionb.json")
UA = "web-snapshots research bot (dl.eeee.nv@gmail.com)"
PRECISION = 5
CELL_KM2 = 4.0                      # one 2x2 km IUCN square per occupied cell, conservatively
B2 = {"CR": 10, "EN": 500, "VU": 2000}
SAMPLE = {"CR": 10**9, "EN": 220, "VU": 220}     # every CR; a seeded sample of the rest
SEED = 20260919


def g(path, params=None):
    u = f"https://api.obis.org/v3/{path}" + (
        "?" + urllib.parse.urlencode(params) if params else "")
    for a in range(3):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(u, headers={"User-Agent": UA}), timeout=600) as r:
                return json.load(r)
        except Exception:                                                # noqa: BLE001
            if a == 2:
                raise
            time.sleep(2 * (a + 1))


def load():
    if not os.path.exists(OUT):
        raise SystemExit("  criterionb.json not cached -- run criterionb.py first")
    return json.load(open(OUT))


def main():
    if os.path.exists(OUT):
        print(f"  cached: {len(load()['species'])} species")
        return 0
    import random
    rl = json.load(open(os.path.join(DATA, "redlist.json")))["threatened"]
    rng = random.Random(SEED)
    picked = []
    for cat, k in SAMPLE.items():
        rows = [x for x in rl if x["category"] == cat]
        rng.shuffle(rows)
        picked += rows[:k]
    print(f"  {len(picked)} species: " + ", ".join(
        f"{c} {sum(1 for x in picked if x['category']==c)}" for c in ("CR", "EN", "VU")))

    def cells(x):
        try:
            r = g(f"occurrence/grid/{PRECISION}", {"scientificname": x["name"]})
            return x, len(r.get("features") or [])
        except Exception:                                                # noqa: BLE001
            return x, None
    out, done = [], 0
    with cf.ThreadPoolExecutor(5) as ex:
        for x, n in ex.map(cells, picked):
            done += 1
            if n is not None:
                out.append({"name": x["name"], "category": x["category"],
                            "class": x["class"], "records": x["dated"], "cells": n,
                            "aoo_min_km2": n * CELL_KM2,
                            "over_b2": (n * CELL_KM2) > B2[x["category"]]})
            if done % 100 == 0:
                print(f"    {done}/{len(picked)}")
    os.makedirs(DATA, exist_ok=True)
    json.dump({"precision": PRECISION, "cell_km2": CELL_KM2, "b2": B2, "seed": SEED,
               "species": out}, open(OUT, "w"), indent=2)
    print(f"\n  {len(out)} species measured")
    for c in ("CR", "EN", "VU"):
        v = [x for x in out if x["category"] == c]
        if v:
            print(f"    {c}  n={len(v):<4} above the B2 threshold: "
                  f"{sum(1 for x in v if x['over_b2'])} ({sum(1 for x in v if x['over_b2'])/len(v):.0%})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
