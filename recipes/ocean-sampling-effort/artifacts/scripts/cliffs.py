#!/usr/bin/env python3
"""Where the register can support a claim about composition, and where it cannot.

    python3 cliffs.py          # fetch and cache

Figure 7 showed that for plants and single cells the recorded *depth* of a class is mostly the
sampling gear. That kills depth as a property of a taxon. It does not kill it as a property of
a **place**: the question "what lives at 40 m" is answerable even when "how deep does kelp go"
is not, because every taxon in a depth bin was reached by the same cruises. So this pulls
composition -- taxon records in a bin over *all* records in that bin -- which cancels effort as
long as the bin is not one expedition.

**That proviso is the second half of the pull.** For each depth band it also fetches the
largest dataset's share of the band. Shallow water is spread over 1,559-2,665 datasets with the
top one at 9-12%; below 5,000 m a single cruise holds 47-53%. A composition ratio is a
measurement in the first case and a description of one ship's itinerary in the second.

**Two traps, both recorded because both nearly shipped.**

*Bin width.* `statistics/env` returns 38 depth bins that are **not** equal: 10 m wide to 200 m,
then 100 m to 1,000 m, then 1,000 m. The raw counts show an obvious step up at 200 m and
another at 1,000 m. Both are the bin getting ten times wider. Per metre, 190-200 m holds 67,390
records and 200-300 m holds 45,865 -- a fall, drawn as a rise.

*The depth filter double-counts.* `startdepth`/`enddepth` match a record's depth *range*, not a
point, so a record spanning 3-8 m is returned by both 0-5 and 5-10. Laminaria gives 29,278 +
177,023 = 206,301 across two abutting bins against 201,830 for their union. Band shares here are
ratios computed inside a single query, where the overlap cancels; the counts must not be summed.

**A filter that is not honoured returns the unfiltered total.** `startbathymetry`,
`startshoredistance`, `startsst` and `startsss` all come back equal to no filter at all -- and so
does `startbanana`, which is how that was established. OBIS attaches `bathymetry`, `sst`, `sss`
and `shoredistance` to every record, but only `depth` can be filtered on server-side.
"""
import json, os, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("OBIS_DATA") or os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "cliffs.json")
UA = "web-snapshots research bot (dl.eeee.nv@gmail.com)"

# Four benthic photosynthesisers, which must both attach to the bottom and be lit; one
# mixed case; three controls that live on the same bottom and do not photosynthesise.
# Scleractinia is the interesting one: reef-building corals carry photosynthetic symbionts
# and azooxanthellate corals do not, so a partial cliff is the prediction.
PANEL = [
    ("Magnoliopsida", "seagrasses", "photo"),
    ("Phaeophyceae", "kelp / brown algae", "photo"),
    ("Ulvophyceae", "green algae", "photo"),
    ("Florideophyceae", "red algae", "photo"),
    ("Scleractinia", "stony corals", "mixed"),
    ("Demospongiae", "sponges", "control"),
    ("Polychaeta", "bristle worms", "control"),
    ("Actinopterygii", "ray-finned fish", "control"),
]

BANDS = [(0, 20), (20, 50), (50, 100), (100, 200), (200, 500), (500, 1000),
         (1000, 2000), (2000, 3000), (3000, 4000), (4000, 5000), (5000, 6000), (6000, 11000)]


def g(path, params=None):
    u = f"https://api.obis.org/v3/{path}" + (
        "?" + urllib.parse.urlencode(params) if params else "")
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}),
                                timeout=300) as r:
        return json.load(r)


def load():
    if not os.path.exists(OUT):
        raise SystemExit("  cliffs.json not cached -- run cliffs.py first")
    return json.load(open(OUT))


def main():
    if os.path.exists(OUT):
        print(f"  cached: {len(load()['taxa'])} taxa, {len(load()['bands'])} bands")
        return 0
    out = {"global": g("statistics/env")["depth"], "taxa": {}, "bands": []}
    for sci, common, kind in PANEL:
        env = g("statistics/env", {"scientificname": sci})["depth"]
        out["taxa"][sci] = {"common": common, "kind": kind, "depth": env}
        print(f"  {common:<20}{sum(x['records'] for x in env):>12,} records with a depth")
        time.sleep(0.4)
    for lo, hi in BANDS:
        tot = g("occurrence", {"startdepth": lo, "enddepth": hi, "size": 0})["total"]
        ds = g("dataset", {"startdepth": lo, "enddepth": hi, "size": 1})
        res = ds.get("results") or []
        out["bands"].append({
            "lo": lo, "hi": hi, "records": tot,
            "top_share": (res[0].get("records", 0) / tot) if res and tot else None,
            "top_dataset": str(res[0].get("title"))[:80] if res else "",
            "datasets": ds.get("total", len(res))})
        print(f"  band {lo:>5}-{hi:<6}{tot:>12,} records, top dataset "
              f"{(out['bands'][-1]['top_share'] or 0):5.1%} of {ds.get('total', 0):,} datasets")
        time.sleep(0.4)
    os.makedirs(DATA, exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"\n  written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
