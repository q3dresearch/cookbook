#!/usr/bin/env python3
"""Which species get more records than their spread of sources warrants.

    python3 attention.py       # fetch and cache (a few minutes)

OBIS holds no field for "commercially important" or "farmed". The question is whether either
falls out of the record profile anyway. Two numbers per species: how many records it has, and
how many separate datasets report it. Datasets are a breadth measure -- a species turning up in
300 datasets is genuinely encountered by many programmes -- so records regressed on datasets
gives an expected attention, and the residual is the interesting quantity.

**Above the line** is a species recorded far more than its spread of sources implies: a few
programmes counting it over and over. **Below the line** is a species many programmes meet and
nobody counts much.

**The controls are declared before the fetch, not chosen after it.** FARMED and WILD below are
hand-entered from the well-known FAO production lists, so they are an outside judgement, not
something read off this data. Whether they separate is the test. Two outcomes are worth having:
if farmed species sit high, the residual detects aquaculture; if they sit flat while wild-caught
species sit high, then it detects *fishery survey effort* and cannot see farms at all -- which
would be the more useful result, because it says what the register is an instrument for.

**`node` cannot be used for breadth.** `/v3/node?scientificname=X` returns 39 for every species,
which is the total node count -- the filter is accepted and ignored. Dataset count is the only
breadth measure that responds to the taxon.

**Records per species come from the checklist, not a per-species count call.** That is one
request per class instead of one per species, and the checklist's `records` field agrees with
`/occurrence?size=0` on spot checks.
"""
import json, math, os, random, sys, time, urllib.parse, urllib.request
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("OBIS_DATA") or os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "attention.json")
UA = "web-snapshots research bot (dl.eeee.nv@gmail.com)"
SEED = 20260919
PER_CLASS = 260                     # sampled across the record range, not the top of it

CLASSES = ["Actinopterygii", "Bivalvia", "Malacostraca", "Gastropoda", "Elasmobranchii"]

# Declared before looking. Major farmed marine species, FAO production lists.
FARMED = {
    "Magallana gigas", "Crassostrea gigas", "Crassostrea virginica", "Ostrea edulis",
    "Mytilus edulis", "Mytilus galloprovincialis", "Mytilus chilensis", "Perna canaliculus",
    "Ruditapes philippinarum", "Pecten maximus", "Argopecten irradians", "Patinopecten yessoensis",
    "Salmo salar", "Oncorhynchus mykiss", "Oncorhynchus kisutch", "Sparus aurata",
    "Dicentrarchus labrax", "Scophthalmus maximus", "Seriola lalandi", "Seriola quinqueradiata",
    "Penaeus vannamei", "Litopenaeus vannamei", "Penaeus monodon", "Penaeus japonicus",
    "Haliotis discus", "Haliotis rufescens", "Haliotis midae", "Anadara granosa",
}
# Major wild-capture species that are NOT farmed at scale.
WILD = {
    "Gadus morhua", "Melanogrammus aeglefinus", "Pollachius virens", "Clupea harengus",
    "Sardina pilchardus", "Scomber scombrus", "Engraulis encrasicolus", "Engraulis ringens",
    "Merluccius merluccius", "Merlangius merlangus", "Trisopterus esmarkii",
    "Thunnus thynnus", "Thunnus albacares", "Katsuwonus pelamis", "Xiphias gladius",
    "Pleuronectes platessa", "Solea solea", "Hippoglossoides platessaides",
    "Pandalus borealis", "Nephrops norvegicus", "Homarus gammarus", "Homarus americanus",
    "Cancer pagurus", "Chionoecetes opilio", "Paralithodes camtschaticus",
    "Illex illecebrosus", "Loligo vulgaris", "Theragra chalcogramma", "Gadus chalcogrammus",
    "Micromesistius poutassou", "Mallotus villosus", "Limanda limanda", "Trachurus trachurus",
}


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


def checklist(sci):
    """Paged with skip: the endpoint caps at 10,000 and sorts by records descending, so a
    single page is a sample drawn on the very variable being modelled."""
    out, seen, skip, total = [], set(), 0, None
    while True:
        r = g("checklist", {"scientificname": sci, "size": 10000, "skip": skip})
        page = r.get("results") or []
        total = r.get("total") if total is None else total
        if not page:
            break
        for x in page:
            nm = x.get("scientificName")
            if nm and nm not in seen and (x.get("taxonRank") or "").lower() == "species":
                seen.add(nm)
                out.append(x)
        skip += len(page)
        if len(page) < 10000 or skip >= (total or 0):
            break
        time.sleep(0.3)
    return out


def load():
    if not os.path.exists(OUT):
        raise SystemExit("  attention.json not cached -- run attention.py first")
    return json.load(open(OUT))


def main():
    if os.path.exists(OUT):
        print(f"  cached: {len(load()['species'])} species")
        return 0
    rng = random.Random(SEED)
    picked, pool = [], {}
    for sci in CLASSES:
        rows = [x for x in checklist(sci) if (x.get("records") or 0) > 0]
        pool[sci] = len(rows)
        # stratify by log10(records) so the sample is not just the famous end
        buckets = {}
        for x in rows:
            buckets.setdefault(int(math.log10(x["records"])), []).append(x)
        per = max(1, PER_CLASS // max(len(buckets), 1))
        chosen = []
        for b in sorted(buckets):
            rng.shuffle(buckets[b])
            chosen += buckets[b][:per]
        # every declared control that exists in this class goes in regardless of the draw
        names = {x["scientificName"] for x in chosen}
        for x in rows:
            if x["scientificName"] in (FARMED | WILD) and x["scientificName"] not in names:
                chosen.append(x)
        for x in chosen:
            picked.append({"name": x["scientificName"], "class": sci,
                           "family": x.get("family"), "records": x["records"]})
        print(f"  {sci:<18}{len(rows):>7,} species with records -> {len(chosen):>4} sampled")

    def ds(x):
        try:
            return x, g("dataset", {"scientificname": x["name"], "size": 1}).get("total")
        except Exception:                                                # noqa: BLE001
            return x, None
    out, done = [], 0
    with cf.ThreadPoolExecutor(6) as ex:
        for x, n in ex.map(ds, picked):
            done += 1
            if n:
                lbl = ("farmed" if x["name"] in FARMED else
                       "wild" if x["name"] in WILD else None)
                out.append({**x, "datasets": n, "control": lbl})
            if done % 250 == 0:
                print(f"    {done}/{len(picked)}")
    os.makedirs(DATA, exist_ok=True)
    json.dump({"seed": SEED, "pool": pool, "species": out,
               "farmed": sorted(FARMED), "wild": sorted(WILD)}, open(OUT, "w"), indent=2)
    nf = sum(1 for x in out if x["control"] == "farmed")
    nw = sum(1 for x in out if x["control"] == "wild")
    print(f"\n  {len(out)} species with a dataset count; {nf} farmed and {nw} wild controls found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
