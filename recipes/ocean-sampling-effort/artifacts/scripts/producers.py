#!/usr/bin/env python3
"""Depth and temperature distributions for marine plants, algae and single cells.

    python3 producers.py       # fetch and cache

`classes.py` covers animals. This is the same pull for the other half of the ocean: the
primary producers and the single-celled things. Everything here is `taxonRank` Class and
`taxonomicStatus` accepted, checked against /v3/taxon, because OBIS silently resolves
synonyms: `Fragilariophyceae` and `Bacillariophyceae` both return 6,389,742 records, and
`Prymnesiophyceae` and `Coccolithophyceae` both return 1,252,644. Putting a synonym pair on
one axis draws the same records twice under two names -- the same trap as Aves inside
Reptilia in classes.py.

**The new field is `dna_share`.** These groups are not all measured the same way. Kelp is
counted by divers in a forest; Alphaproteobacteria is amplified out of a water sample. A
sequencing run and a dive survey reach different depths for reasons that have nothing to do
with the organism, so the instrument has to be on the page beside the distribution. It is a
keyword match on dataset titles (see DNA below), measured over each class's 100 largest
datasets, which covers 93-99% of records -- `dna_cover` records exactly how much.
"""
import json, os, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("OBIS_DATA") or os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "producers.json")
UA = "web-snapshots research bot (dl.eeee.nv@gmail.com)"

# A dataset title claiming any of these is a sequencing run, not an observation of an
# organism. Deliberately narrow: these name the method or the named sequencing programme,
# never a taxon or a place, so a plankton net survey cannot match.
DNA = ("16s", "18s", "metagenom", "amplicon", "sequencing", "tara oceans", "microbiome",
       "edna", "metabarcod", " asv", "marine microbes")

PRODUCERS = [
    # macroalgae and flowering plants -- counted by divers, quadrats and aerial survey
    ("Phaeophyceae", "brown algae, kelp"), ("Florideophyceae", "red algae"),
    ("Ulvophyceae", "green algae"), ("Magnoliopsida", "seagrasses"),
    # phytoplankton -- counted down a microscope, increasingly sequenced
    ("Bacillariophyceae", "diatoms"), ("Dinophyceae", "dinoflagellates"),
    ("Coccolithophyceae", "coccolithophores"), ("Cryptophyceae", "cryptophytes"),
    ("Chrysophyceae", "golden algae"), ("Dictyochophyceae", "silicoflagellates"),
    # bacteria -- almost entirely sequenced
    ("Cyanophyceae", "cyanobacteria"), ("Alphaproteobacteria", "alphaproteobacteria"),
    # single-celled non-plants, kept because they are the control on instrument:
    # forams are mostly drill core, ciliates mostly sequencing, neither is a producer
    ("Globothalamea", "forams"), ("Oligotrichea", "ciliates"),
]


def g(path, params=None):
    u = f"https://api.obis.org/v3/{path}" + (
        "?" + urllib.parse.urlencode(params) if params else "")
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}),
                                timeout=300) as r:
        return json.load(r)


def load():
    if not os.path.exists(OUT):
        raise SystemExit("  producers.json not cached -- run producers.py first")
    return json.load(open(OUT))


def main():
    if os.path.exists(OUT):
        print(f"  cached: {len(load())} classes")
        return 0
    out = {}
    for sci, common in PRODUCERS:
        try:
            tx = (g(f"taxon/{urllib.parse.quote(sci)}").get("results") or [{}])[0]
            if tx.get("taxonomicStatus") != "accepted" or tx.get("taxonRank") != "Class":
                print(f"  {sci}: SKIPPED, {tx.get('taxonRank')}/{tx.get('taxonomicStatus')}"
                      f" -> {tx.get('acceptedNameUsage')}")
                continue
            env = g("statistics/env", {"scientificname": sci})
            n = g("occurrence", {"scientificname": sci, "size": 0})["total"]
            sp = g("checklist", {"scientificname": sci, "size": 1}).get("total", 0)
            ds = (g("dataset", {"scientificname": sci, "size": 100}).get("results") or [])
        except Exception as e:                                           # noqa: BLE001
            print(f"  {sci}: {type(e).__name__}")
            continue
        cov = sum(x.get("records", 0) for x in ds) or 1
        dna = sum(x.get("records", 0) for x in ds
                  if any(k in str(x.get("title", "")).lower() for k in DNA))
        out[sci] = {"common": common, "kingdom": tx.get("kingdom"), "records": n,
                    "species": sp, "depth": env.get("depth", []), "sst": env.get("sst", []),
                    "sss": env.get("sss", []),
                    "top_share": (ds[0].get("records", 0) / n) if ds and n else None,
                    "top_dataset": str(ds[0].get("title"))[:80] if ds else "",
                    "dna_share": dna / cov, "dna_cover": cov / n if n else 0}
        print(f"  {sci:<21}{n:>12,} records, {sp:>6,} species, "
              f"DNA {dna/cov:5.1%} of top-100 (covering {cov/n:5.1%})")
        time.sleep(0.4)
    os.makedirs(DATA, exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"\n  {len(out)} classes written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
