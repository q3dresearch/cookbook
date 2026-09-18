#!/usr/bin/env python3
"""How many independent observations is this map actually made of?

    python3 depth_of_map.py       # sample cells, cache the result

229 million records sounds like 229 million independent looks at the sea. The invasive-species
figure in this recipe found one cell where 299 of 300 sampled records came from a single
dataset, which raises the general question: **how much of the map is one project deep?**

**Method.** For a stratified sample of grid cells, ask `/dataset?geometry=<cell>` how many
records each contributing dataset holds inside that cell, and take the largest one's share.

**Verified before use, because the answer depends on it.** `records` on a dataset returned with
a geometry filter could plausibly be the dataset's global total, which would make every share
meaningless. It is not: the same query on a 0.04-degree box returns 1,263 where a 1.6-degree box
returns 2,547,766, and in both cases the top datasets sum to less than the occurrences in the
box. It is scoped to the geometry.

**Stratified rather than random.** A uniform sample of 27,168 cells would be almost entirely
empty ocean, which is a different question. Cells are drawn across the record-count
distribution so the busy cells — the ones the map is actually made of — are represented.
"""
import json, os, random, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("OBIS_DATA") or os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "map-depth.json")
UA = "web-snapshots research bot (dl.eeee.nv@gmail.com)"
PER_BAND = 22
BANDS = [(1e6, 1e12, "over 1M"), (1e5, 1e6, "100k-1M"), (1e4, 1e5, "10k-100k"),
         (1e3, 1e4, "1k-10k"), (1e2, 1e3, "100-1k")]


def poly(coords):
    pts = coords[0]
    return "POLYGON((" + ",".join(f"{p[0]:.4f} {p[1]:.4f}" for p in pts) + "))"


def datasets(geom):
    u = "https://api.obis.org/v3/dataset?" + urllib.parse.urlencode({"geometry": geom, "size": 60})
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}),
                                timeout=300) as r:
        return json.load(r)


def main():
    if os.path.exists(OUT):
        d = json.load(open(OUT))
        print(f"  cached: {len(d['cells'])} cells sampled")
        return 0
    import obis
    feats = obis.load("grid3.json")["features"]
    rnd = random.Random(17)
    rows = []
    for lo, hi, lab in BANDS:
        pool = [f for f in feats if lo <= f["properties"].get("n", 0) < hi]
        take = rnd.sample(pool, min(PER_BAND, len(pool)))
        print(f"  {lab}: {len(pool):,} cells, sampling {len(take)}")
        for f in take:
            n = f["properties"]["n"]
            c = f["geometry"]["coordinates"][0]
            lon = sum(p[0] for p in c) / len(c)
            lat = sum(p[1] for p in c) / len(c)
            try:
                d = datasets(poly(f["geometry"]["coordinates"]))
            except Exception as e:                                       # noqa: BLE001
                print(f"    {lat:.1f},{lon:.1f}: {type(e).__name__}")
                continue
            res = d.get("results") or []
            counts = sorted((x.get("records", 0) for x in res), reverse=True)
            tot = sum(counts)
            top = res[0] if res else {}
            rows.append({"lat": round(lat, 2), "lon": round(lon, 2), "cell_records": n,
                         "datasets": d.get("total", len(res)),
                         "top_share": (counts[0] / tot) if tot else None,
                         "top3_share": (sum(counts[:3]) / tot) if tot else None,
                         "top_title": str(top.get("title"))[:90],
                         "band": lab})
            time.sleep(0.25)
    os.makedirs(DATA, exist_ok=True)
    json.dump({"per_band": PER_BAND, "cells": rows}, open(OUT, "w"), indent=2)
    print(f"\n  {len(rows)} cells written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
