#!/usr/bin/env python3
"""Depth and temperature distributions, one pull per animal class.

    python3 classes.py         # fetch and cache

The first five figures in this recipe are all about the register's defects. That is a real
pattern and it is not marine biology, so this pulls the thing that is: `statistics/env` accepts
a taxon filter and returns 38 depth bins and 8 sea-surface-temperature bins for any group.

**What the numbers are, exactly.** Where members of a class were *recorded*, not where they
live. Every bias the earlier figures found still applies — 88% of all records come from the top
200 m, and a class sampled mainly by divers will look shallow whatever it does.

**Why it is still worth doing.** The biases are largely shared. Two classes sampled by the same
fleet, in the same water, with the same gear, differing in recorded depth by an order of
magnitude is a difference in the animals and not only in the method. The figures compare
classes to each other and never to the ocean.
"""
import json, os, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("OBIS_DATA") or os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "classes.json")
UA = "web-snapshots research bot (dl.eeee.nv@gmail.com)"

# Reptilia is NOT included. OBIS follows modern phylogeny, in which Aves sits inside Reptilia:
# Reptilia returns 28,177,335 records against Aves' 27,480,906, and its top three datasets are
# European Seabirds At Sea and two herring gull tracking studies. The two are not disjoint and
# putting both on one axis would double-count seabirds and label them reptiles.
CLASSES = [
    ("Actinopterygii", "ray-finned fish"), ("Elasmobranchii", "sharks and rays"),
    ("Cephalopoda", "squid and octopus"), ("Malacostraca", "crabs and shrimp"),
    ("Gastropoda", "sea snails"), ("Bivalvia", "clams and mussels"),
    ("Polychaeta", "bristle worms"), ("Anthozoa", "corals and anemones"),
    ("Hydrozoa", "hydroids"), ("Scyphozoa", "true jellyfish"),
    ("Echinoidea", "sea urchins"), ("Asteroidea", "sea stars"),
    ("Holothuroidea", "sea cucumbers"), ("Demospongiae", "sponges"),
    ("Mammalia", "marine mammals"), ("Aves", "seabirds"),
]


def g(path, params):
    u = f"https://api.obis.org/v3/{path}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}),
                                timeout=300) as r:
        return json.load(r)


def load():
    if not os.path.exists(OUT):
        raise SystemExit("  classes.json not cached — run classes.py first")
    return json.load(open(OUT))


def main():
    if os.path.exists(OUT):
        d = load()
        print(f"  cached: {len(d)} classes")
        return 0
    out = {}
    for sci, common in CLASSES:
        try:
            env = g("statistics/env", {"scientificname": sci})
            n = g("occurrence", {"scientificname": sci, "size": 0})["total"]
            sp = g("checklist", {"scientificname": sci, "size": 1}).get("total", 0)
        except Exception as e:                                           # noqa: BLE001
            print(f"  {sci}: {type(e).__name__}")
            continue
        # How much of the class is one survey? Figure 5 established that a cell's median
        # record share from its top dataset is 45%, so a class at 80% is not a taxon with a
        # niche — it is a project with a study area.
        try:
            ds = g("dataset", {"scientificname": sci, "size": 3})
            res = ds.get("results") or []
            top = (res[0].get("records", 0) / n) if res and n else None
            topname = str(res[0].get("title"))[:80] if res else ""
            nds = ds.get("total", len(res))
        except Exception:                                                # noqa: BLE001
            top, topname, nds = None, "", None
        out[sci] = {"common": common, "records": n, "species": sp,
                    "depth": env.get("depth", []), "sst": env.get("sst", []),
                    "sss": env.get("sss", []),
                    "top_share": top, "top_dataset": topname, "datasets": nds}
        d = sum(r["records"] for r in out[sci]["depth"])
        print(f"  {sci:<16}{n:>12,} records, {sp:>6,} species, {d:>11,} with depth, "
              f"top dataset {top:.0%}" if top else f"  {sci:<16}{n:>12,} records")
        time.sleep(0.4)
    os.makedirs(DATA, exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"\n  {len(out)} classes written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
