#!/usr/bin/env python3
"""Is the register saturating? A species accumulation curve per class, with a holdout.

    python3 saturation.py      # fetch and cache

Figures 1-8 describe. This is the one thing in the recipe that makes a claim about data that
does not exist yet, and it is checkable: fit the curve on everything OBIS holds dated 2000 or
earlier, extrapolate, and compare against what it actually holds now.

**The x-axis is effort, not time.** Species-against-year measures how hard people worked, which
changed by orders of magnitude over the century. Species against *cumulative records* is the
accumulation curve proper: it asks how many new species the next million records buy. Both are
fetched; the fit uses records.

**What the asymptote is and is not.** The fitted ceiling is how many species THIS REGISTER will
eventually hold for a class, not how many exist. It is bounded by what gets observed and
digitised and shipped to OBIS, and a group nobody surveys has a low ceiling for that reason and
not a biological one. The useful reading is the ratio: a class at 98% of its own ceiling is one
where the next survey of the same kind returns nothing new, and that is a procurement fact.

**The curve is not a discovery record.** A specimen collected in 1911 may have been keyed in
in 2019. Everything here is "what OBIS now holds dated on or before year Y", so the horizontal
axis is the date on the record, never the date it became known.
"""
import json, os, sys, time, urllib.parse, urllib.request
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("OBIS_DATA") or os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "saturation.json")
UA = "web-snapshots research bot (dl.eeee.nv@gmail.com)"

CUT = 2000                                   # fit on <= CUT, hold out everything after
YEARS = list(range(1900, 2001, 5)) + [2005, 2010, 2015, 2020, 2024]

CLASSES = [
    ("Actinopterygii", "ray-finned fish"), ("Elasmobranchii", "sharks and rays"),
    ("Cephalopoda", "squid and octopus"), ("Malacostraca", "crabs and shrimp"),
    ("Gastropoda", "sea snails"), ("Bivalvia", "clams and mussels"),
    ("Polychaeta", "bristle worms"), ("Anthozoa", "corals and anemones"),
    ("Hydrozoa", "hydroids"), ("Echinoidea", "sea urchins"),
    ("Asteroidea", "sea stars"), ("Holothuroidea", "sea cucumbers"),
    ("Demospongiae", "sponges"), ("Mammalia", "marine mammals"),
    ("Aves", "seabirds"), ("Bacillariophyceae", "diatoms"),
]


def g(path, params=None):
    u = f"https://api.obis.org/v3/{path}" + (
        "?" + urllib.parse.urlencode(params) if params else "")
    for a in range(4):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(u, headers={"User-Agent": UA}), timeout=300) as r:
                return json.load(r)
        except Exception:                                                # noqa: BLE001
            if a == 3:
                raise
            time.sleep(1.5 * (a + 1))


def load():
    if not os.path.exists(OUT):
        raise SystemExit("  saturation.json not cached -- run saturation.py first")
    return json.load(open(OUT))


def main():
    if os.path.exists(OUT):
        print(f"  cached: {len(load()['classes'])} classes")
        return 0
    out = {"cut": CUT, "years": YEARS, "classes": {}}
    for sci, common in CLASSES:
        yr = g("statistics/years", {"scientificname": sci}) or []
        per = {r["year"]: r.get("records", 0) for r in yr}

        def cum_species(y):
            return g("checklist", {"scientificname": sci, "enddate": f"{y}-12-31",
                                   "size": 1}).get("total") or 0
        with cf.ThreadPoolExecutor(5) as ex:
            sp = list(ex.map(cum_species, YEARS))
        rec = [sum(n for y2, n in per.items() if y2 <= y) for y in YEARS]
        out["classes"][sci] = {"common": common, "species": sp, "records": rec}
        print(f"  {common:<20}{sp[-1]:>7,} species on {rec[-1]:>12,} records "
              f"(at {CUT}: {sp[YEARS.index(CUT)]:,})")
        time.sleep(0.3)
    os.makedirs(DATA, exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"\n  written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
