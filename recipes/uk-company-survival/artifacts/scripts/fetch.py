#!/usr/bin/env python3
"""Retrieve the four corpora, and explain why the first one is retrievable at all.

    python3 fetch.py               # everything missing, resumably
    python3 fetch.py --verify      # hash what is here against provenance.json
    python3 fetch.py ch ons        # named sources only

**The recipe was filed on a premise that turned out to be wrong.** Companies House publishes a
free monthly bulk extract of the whole register, and the argument for building on it was that
these are legal records with dates attached, so the history is in the data. **It is not.** The
file is a live-register snapshot: in the first 73,146 rows, the number carrying a
`DissolutionDate` is **zero**. Every status present — Active, Proposal to Strike off,
Liquidation, Administration, Receiver, Voluntary Arrangement — is one a company holds *while
still on the register*. The column exists and is never populated. The register publishes its
survivors and drops its dead.

**What rescued it is that the publisher keeps its own back-catalogue, quietly.** The monthly
file lives at a dated URL, `BasicCompanyDataAsOneFile-YYYY-MM-01.zip`, and old months keep
resolving even though nothing links to them. Three snapshots a year apart make survival
measurable the only way this register allows: **a company is dead when it stops appearing.**

That is why `fetch.py` is the deliverable here and no data is committed. Each snapshot is
about 490 MB. If a month you want has stopped resolving, that month is gone — take a copy of
the current one before reading further, because it is the same file that will be overwritten.

**The other three are ordinary.** ONS business demography is a published workbook, used as an
external check on ordering rather than level. Colorado and Norway are national registers used
as controls: Colorado records six kinds of death and still cannot measure lifespan, and Norway
is the closest thing to a matched comparison.
"""
import gzip, hashlib, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("FSB_DATA") or os.path.join(HERE, "..", "data")
UA = "cookbook/uk-company-survival (+https://github.com/q3dresearch/cookbook)"
SNAPSHOTS = ["2024-09-01", "2025-09-01", "2026-09-01"]

SOURCES = {
    "ch": [(f"ch-{d}.zip",
            f"https://download.companieshouse.gov.uk/BasicCompanyDataAsOneFile-{d}.zip")
           for d in SNAPSHOTS],
    "ons": [("ons-business-demography-2024.xlsx",
             "https://www.ons.gov.uk/file?uri=/businessindustryandtrade/business/"
             "activitysizeandlocation/datasets/businessdemographyreferencetable/2024/"
             "businessdemographyexceltables2024.xlsx")],
    "colorado": [("colorado.csv.gz",
                  "https://data.colorado.gov/resource/4ykn-tg5h.csv?$limit=2000000")],
    # norway.py fetches and pages the Enhetsregisteret itself, writing norway-enheter.json.gz;
    # it is listed here so --verify accounts for it rather than silently skipping it.
    "norway": [("norway-enheter.json.gz", None),
               ("norway-as-2019.csv.gz", None)],
}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def get(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Encoding": "gzip, deflate"})
    tmp = path + ".part"
    with urllib.request.urlopen(req, timeout=900) as r, open(tmp, "wb") as fh:
        n = 0
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            fh.write(b)
            n += len(b)
            if n % (64 << 20) < (1 << 20):
                print(f"     {n/1e6:,.0f} MB")
    if path.endswith(".csv.gz") and not url.endswith(".gz"):
        raw = open(tmp, "rb").read()
        with gzip.open(path, "wb") as fh:
            fh.write(raw)
        os.remove(tmp)
    else:
        os.replace(tmp, path)
    return os.path.getsize(path)


def main():
    os.makedirs(DATA, exist_ok=True)
    verify = "--verify" in sys.argv
    want = [a for a in sys.argv[1:] if not a.startswith("-")] or list(SOURCES)
    prov = {}
    p = os.path.join(HERE, "..", "..", "provenance.json")
    if os.path.exists(p):
        prov = {s["file"]: s for s in json.load(open(p)).get("sources", [])}

    for key in want:
        if key not in SOURCES:
            print(f"  unknown source: {key}")
            continue
        for name, url in SOURCES[key]:
            path = os.path.join(DATA, name)
            if not os.path.exists(path):
                if verify or url is None:
                    print(f"  {name}: absent"
                          + (" — run norway.py, which pages the register itself"
                             if url is None else ""))
                    continue
                print(f"  {name}: fetching")
                try:
                    get(url, path)
                except Exception as e:                       # noqa: BLE001
                    print(f"     failed: {type(e).__name__} {e}")
                    if name.startswith("ch-"):
                        print("     a dated Companies House month that stops resolving is gone;"
                              " nothing archives it")
                    continue
            h = sha(path)
            rec = prov.get(name, {})
            state = ("matches provenance" if rec.get("sha256") == h else
                     f"DRIFT — provenance says {rec['sha256'][:12]}…" if rec.get("sha256")
                     else "no recorded hash")
            print(f"  {name}: {os.path.getsize(path):,} bytes, sha {h[:12]}… — {state}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
