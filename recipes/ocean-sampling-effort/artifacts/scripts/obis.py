#!/usr/bin/env python3
"""Fetch and load OBIS, the Ocean Biodiversity Information System.

    python3 obis.py            # fetch what is missing, write a dated snapshot

**What it is.** 229.5 million occurrence records, 168,352 species, 6,918 datasets, spanning
1103 to 2026. It is the reference source for where marine life has been seen, and it is used
to site marine protected areas, to assess extinction risk, and to compute national and global
biodiversity indicators.

**Why it is worth a recipe.** Step 1 was three GETs and both of the obvious biases were already
visible in the summary endpoints. Birds are 12.9% of the records and 0.5% of the species —
32,638 records per bird species against 848 for the invertebrates and algae that make up 88%
of the species list. And at the coarsest grid the API offers, the top 1% of cells hold 37.7%
of every record ever contributed.

**The question that follows is the one this project keeps meeting.** A gap in a map like this
can mean nothing lives there or nobody went. The register records presences and never absences,
so the distinction is not in the data and has to be built from effort.

**A dated snapshot on every run.** OBIS is additive rather than overwriting — records are
contributed, not withdrawn — so the history is less perishable than most sources here. It is
snapshotted anyway, because "additive" is an assumption about the publisher's behaviour and
not a guarantee, and checking it needs two dates.
"""
import datetime, gzip, json, os, shutil, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("OBIS_DATA") or os.path.join(HERE, "..", "data")
API = "https://api.obis.org/v3"
UA = "web-snapshots research bot (dl.eeee.nv@gmail.com)"

PULLS = {
    "statistics.json": "statistics",
    "composition.json": "statistics/composition",
    "years.json": "statistics/years",
    "env.json": "statistics/env",
    "grid2.json": "occurrence/grid/2",
    "grid3.json": "occurrence/grid/3",
    "nodes.json": "node",
    "institutes.json": "institute",
    # WRiMS is the World Register of Introduced Marine Species. ?wrims=true filters occurrences
    # and every aggregation endpoint to introduced species only.
    #
    # TRAP RECORDED: the filter works one way. wrims=false returns zero and so does
    # wrims=banana, so the complement is not reachable and a garbage value is
    # indistinguishable from an empty result. Non-introduced counts are computed as
    # total minus introduced, never asked for.
    "years-wrims.json": "statistics/years?wrims=true",
    "grid3-wrims.json": "occurrence/grid/3?wrims=true",
    "composition-wrims.json": "statistics/composition?wrims=true",
}


def get(path, params=None):
    url = f"{API}/{path}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
    # paths in PULLS may already carry a query string
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=600) as r:
        return r.read()


def fetch(name, path, params=None):
    p = os.path.join(DATA, name)
    if os.path.exists(p):
        return p, False
    os.makedirs(DATA, exist_ok=True)
    with open(p, "wb") as fh:
        fh.write(get(path, params))
    return p, True


def snapshot(p):
    d = os.path.join(DATA, "snapshots")
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, f"{os.path.basename(p)[:-5]}-{datetime.date.today().isoformat()}.json.gz")
    if os.path.exists(out):
        return out, False
    with open(p, "rb") as fh, gzip.open(out, "wb") as gz:
        shutil.copyfileobj(fh, gz)
    return out, True


def load(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        raise SystemExit(f"  {name} not cached — run obis.py first")
    return json.load(open(p))


def main():
    for name, path in PULLS.items():
        p, got = fetch(name, path)
        snapshot(p)
        print(f"  {name}: {os.path.getsize(p)/1e6:,.2f} MB{' (fetched)' if got else ' (cached)'}")
    st = load("statistics.json")
    print(f"\n  {st['records']:,} records, {st['species']:,} species, "
          f"{st['datasets']:,} datasets, years {st['yearrange'][0]}-{st['yearrange'][1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
