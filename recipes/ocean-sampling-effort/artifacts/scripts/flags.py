#!/usr/bin/env python3
"""What OBIS flags as wrong with itself, and whether removing it changes anything.

    python3 flags.py           # fetch and cache

`statistics/qc` publishes the register's own error signature and nothing in this recipe had
opened it. Against 229.7M records it reports **43.2M ON_LAND**, 44.0M NO_MATCH, 8.5M
DEPTH_EXCEEDS_BATH, 2.3M NOT_MARINE, and half a million coordinates outside the possible range.
Nineteen percent of a marine register flagged as being on land is the kind of number that ends
an analysis, so it is worth finding out what it is before acting on it.

**The flags are filterable, and that was checked the usual way.** `flags=ON_LAND` returns
34.6M and `exclude=ON_LAND` returns 195.1M against an unfiltered 229.7M, so both are honoured.
`flags=BANANA` returns 0 rather than the total, which is what distinguishes a working filter
from an ignored parameter; `banana=ON_LAND` returns the unfiltered total, which is what an
ignored one looks like.

**Two different numbers for the same flag, and neither is wrong.** `statistics/qc` says ON_LAND
is 43,236,520 and an `occurrence` count with the filter says 34,582,170. The qc table counts
across everything the register has ever ingested, including rows dropped before they reach the
searchable index; the filter counts what a query can actually return. This file records both and
uses the filter count, because that is the population every other figure in the recipe drew from.

**The point of the pull is the per-class breakdown.** A flag that lands uniformly is noise to be
removed. A flag that lands on particular organisms is a habitat, and removing it deletes the
habitat. Which of those is true here is a measurement, not a judgement, and it is the one this
script makes.
"""
import json, os, sys, time, urllib.parse, urllib.request
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("OBIS_DATA") or os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "flags.json")
UA = "web-snapshots research bot (dl.eeee.nv@gmail.com)"

FLAGS = ["ON_LAND", "DEPTH_EXCEEDS_BATH", "NO_MATCH", "NOT_MARINE", "MIN_DEPTH_EXCEEDS_MAX"]
# the exclusions a careful person would apply without thinking about it
CLEAN = "ON_LAND,DEPTH_EXCEEDS_BATH,NO_MATCH,NOT_MARINE"

CLASSES = [
    ("Aves", "seabirds"), ("Magnoliopsida", "seagrasses"), ("Bivalvia", "clams and mussels"),
    ("Gastropoda", "sea snails"), ("Malacostraca", "crabs and shrimp"),
    ("Actinopterygii", "ray-finned fish"), ("Mammalia", "marine mammals"),
    ("Phaeophyceae", "kelp"), ("Polychaeta", "bristle worms"),
    ("Bacillariophyceae", "diatoms"), ("Demospongiae", "sponges"),
    ("Anthozoa", "corals and anemones"), ("Elasmobranchii", "sharks and rays"),
    ("Holothuroidea", "sea cucumbers"), ("Florideophyceae", "red algae"),
    ("Echinoidea", "sea urchins"),
]
# the recipe's own claims, re-measured on the cleaned subset
CLIFF = [("Magnoliopsida", "seagrasses"), ("Phaeophyceae", "kelp"),
         ("Florideophyceae", "red algae"), ("Ulvophyceae", "green algae"),
         ("Demospongiae", "sponges"), ("Polychaeta", "bristle worms"),
         ("Actinopterygii", "ray-finned fish")]


def g(path, params=None):
    u = f"https://api.obis.org/v3/{path}" + (
        "?" + urllib.parse.urlencode(params) if params else "")
    for a in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    u, headers={"User-Agent": UA}), timeout=300) as r:
                return json.load(r)
        except Exception:                                                # noqa: BLE001
            if a == 3:
                raise
            time.sleep(1.5 * (a + 1))


def load():
    if not os.path.exists(OUT):
        raise SystemExit("  flags.json not cached -- run flags.py first")
    return json.load(open(OUT))


def crossing(env, glob, edges):
    """The depth at which a group falls under a tenth of its 0-20 m share -- figure 8's
    statistic, recomputed here so the two can be compared directly."""
    e = {x["from"]: x["records"] for x in env}
    gg = {x["from"]: x["records"] for x in glob}
    denom = sum(gg.get(x, 0) for x in edges[:2])
    base = sum(e.get(x, 0) for x in edges[:2]) / denom if denom else 0
    if not base:
        return None
    rel = [(e.get(x, 0) / gg[x] if gg.get(x) else 0) / base for x in edges]
    return next((edges[i] for i in range(len(rel)) if all(r < .1 for r in rel[i:])), None)


def main():
    if os.path.exists(OUT):
        print(f"  cached: {len(load()['classes'])} classes")
        return 0
    qc = g("statistics/qc")
    total = g("occurrence", {"size": 0})["total"]
    # the control that separates a working filter from an ignored parameter
    probe = {
        "flags_on_land": g("occurrence", {"flags": "ON_LAND", "size": 0})["total"],
        "exclude_on_land": g("occurrence", {"exclude": "ON_LAND", "size": 0})["total"],
        "flags_nonsense": g("occurrence", {"flags": "BANANA", "size": 0})["total"],
        "nonsense_param": g("occurrence", {"banana": "ON_LAND", "size": 0})["total"],
    }
    print(f"  {total:,} records; flags=ON_LAND {probe['flags_on_land']:,}, "
          f"exclude {probe['exclude_on_land']:,}, flags=BANANA {probe['flags_nonsense']:,}")

    def per_class(t):
        sci, common = t
        n = g("occurrence", {"scientificname": sci, "size": 0})["total"]
        out = {f: g("occurrence", {"scientificname": sci, "flags": f, "size": 0})["total"]
               for f in FLAGS}
        return {"sci": sci, "common": common, "records": n, "flags": out}
    with cf.ThreadPoolExecutor(4) as ex:
        classes = list(ex.map(per_class, CLASSES))
    for c in classes:
        print(f"  {c['common']:<20}{c['records']:>12,}  on land "
              f"{c['flags']['ON_LAND']/max(c['records'],1):6.1%}  deeper than the floor "
              f"{c['flags']['DEPTH_EXCEEDS_BATH']/max(c['records'],1):5.1%}")

    raw_g = g("statistics/env")["depth"]
    cln_g = g("statistics/env", {"exclude": CLEAN})["depth"]
    edges = sorted({x["from"] for x in raw_g})[:21]
    checks = []
    for sci, common in CLIFF:
        a = g("statistics/env", {"scientificname": sci})["depth"]
        b = g("statistics/env", {"scientificname": sci, "exclude": CLEAN})["depth"]
        checks.append({"common": common,
                       "records_raw": sum(x["records"] for x in a),
                       "records_clean": sum(x["records"] for x in b),
                       "cross_raw": crossing(a, raw_g, edges),
                       "cross_clean": crossing(b, cln_g, edges)})
        print(f"  {common:<20}10% crossing {checks[-1]['cross_raw']} m raw -> "
              f"{checks[-1]['cross_clean']} m cleaned")
        time.sleep(0.3)

    shallow = lambda d: (sum(x["records"] for x in d if x["from"] < 200)
                         / sum(x["records"] for x in d))
    out = {"total": total, "probe": probe, "qc_flags": qc.get("flags", {}),
           "qc_fields": qc.get("fields", {}), "onland": qc.get("onland", {}),
           "clean_exclusions": CLEAN, "classes": classes, "checks": checks,
           "depth_raw": raw_g, "depth_clean": cln_g,
           "top200_raw": shallow(raw_g), "top200_clean": shallow(cln_g)}
    os.makedirs(DATA, exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"\n  top 200 m: {out['top200_raw']:.1%} raw -> {out['top200_clean']:.1%} cleaned")
    print(f"  written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
