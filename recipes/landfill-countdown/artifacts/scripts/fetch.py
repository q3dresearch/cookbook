#!/usr/bin/env python3
"""Retrieve what can still be retrieved, and say plainly what cannot.

    python3 fetch.py            # check the workbooks, pull the Census files
    python3 fetch.py --verify   # hash what is here against provenance.json

**The unusual part of this recipe is that half its evidence no longer exists at source.**
EPA's Landfill Methane Outreach Program publishes its database at a dated path and
overwrites the listing. Editions live at `.../lmop-database-<month><year>.xlsx` and **only
the current one resolves**. September 2021 returns 404, and no web archive holds it.

So the 2021 workbook is **committed**, against this repo's own rule that data is never
committed, because the rule's stated exception is exactly this: *a snapshot that cannot be
reconstructed*. It is 756 KB. Without it the recipe has one edition and no interval, and the
central finding — that 1.3 billion tons of new capacity was permitted where the clock was
shortest — cannot be computed at all.

The 2024 workbook is committed too, for a duller reason: it will be overwritten on the same
path by the next edition, and then the pair here is the only place the interval survives.
`--verify` reports drift against the hashes in `provenance.json` rather than hiding it.

The Census files are ordinary: they are versioned by year at stable URLs and re-fetch fine.
"""
import hashlib, json, os, sys, urllib.request, zipfile, io

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
UA = "cookbook/landfill-countdown (+https://github.com/q3dresearch/cookbook)"

WORKBOOKS = {
    "lmop-2024-09.xlsx": "https://www.epa.gov/system/files/documents/2024-09/lmop-database-september-2024.xlsx",
    "lmop-2021-09.xlsx": None,        # gone from the internet; see the docstring
}
CENSUS = {
    "census-counties.csv.gz": "https://www2.census.gov/programs-surveys/popest/datasets/"
                              "2020-2023/counties/totals/co-est2023-alldata.csv",
    "census-urban-areas.csv.gz": "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
                                 "2023_Gazetteer/2023_Gaz_ua_national.zip",
}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    os.makedirs(DATA, exist_ok=True)
    verify = "--verify" in sys.argv
    prov = {}
    p = os.path.join(HERE, "..", "..", "provenance.json")
    if os.path.exists(p):
        prov = {s["file"]: s for s in json.load(open(p)).get("sources", [])}

    for name, url in WORKBOOKS.items():
        path = os.path.join(DATA, name)
        if not os.path.exists(path):
            if url is None:
                print(f"  {name}: MISSING and unobtainable — it is committed to this repo; "
                      f"restore it from git rather than re-fetching")
                continue
            print(f"  {name}: fetching")
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r, open(path, "wb") as fh:
                fh.write(r.read())
        h = sha(path)
        want = prov.get(name, {}).get("sha256")
        state = "matches provenance" if want == h else (
            f"DRIFT — provenance says {want[:12]}…" if want else "no recorded hash")
        print(f"  {name}: {os.path.getsize(path):,} bytes, sha {h[:12]}… — {state}")

    if verify:
        return 0
    for name, url in CENSUS.items():
        path = os.path.join(DATA, name)
        if os.path.exists(path):
            print(f"  {name}: present")
            continue
        print(f"  {name}: fetching")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=300) as r:
            raw = r.read()
        if url.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                raw = z.read(max(z.namelist(), key=lambda n: z.getinfo(n).file_size))
        import gzip
        with gzip.open(path, "wb") as fh:
            fh.write(raw)
        print(f"     {os.path.getsize(path):,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
