#!/usr/bin/env python3
"""A third walk, for intervention NAMES — the key that links trials of the same product.

    python3 ctg4.py

`ctg3.py` fetched intervention *type* (DRUG, DEVICE, BEHAVIORAL). That answers "what kind of
thing is being tested" and cannot answer "is this the same thing being tested again", which is
what a question about phase 1 versus phase 2 versus phase 3 of one product requires.

**Names are the only within-register key to a compound.** There is no compound identifier
here: no NDC, no UNII, no ChEMBL id. `interventions.name` is free text the sponsor typed, so
linking on it is a join on a string and will be wrong in both directions — "Pembrolizumab",
"MK-3475", "Keytruda" and "pembrolizumab 200mg IV" are one molecule and four keys, while
"Placebo" and "Standard of care" are tens of thousands of trials sharing a key that means
nothing.

**So this fetch is the cheap half and the join is the expensive half.** What arrives is a
string per intervention. Whether it supports a product-level claim is a separate question that
has to be answered with a measured overlap, not assumed — the last three recipes in this
project each found a join that looked obvious and matched almost nothing.

`otherNames` is taken as well, because it is where sponsors put the code name next to the
brand name, and it is the only material in the register for collapsing synonyms without an
external vocabulary.
"""
import csv, gzip, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ctg as C                                                          # noqa: E402

DATA = os.path.join(HERE, "..", "data")
ROWS = os.path.join(DATA, "names.csv.gz")
CKPT = os.path.join(DATA, "names.checkpoint.json")
PAGE = 1000
P = "protocolSection"
FIELDS = [f"{P}.identificationModule.nctId",
          f"{P}.armsInterventionsModule.interventions.name",
          f"{P}.armsInterventionsModule.interventions.type",
          f"{P}.armsInterventionsModule.interventions.otherNames"]
COLS = ["nct_id", "names", "types", "other_names"]


def clean(x):
    return (x or "").replace("|", "/").replace("\n", " ").replace("\r", " ").strip()


def extract(st):
    iv = (st.get(P, {}).get("armsInterventionsModule", {}) or {}).get("interventions", []) or []
    names, types, other = [], [], []
    for i in iv[:12]:
        i = i or {}
        if i.get("name"):
            names.append(clean(i["name"])[:80])
        if i.get("type"):
            types.append(clean(i["type"]))
        for o in (i.get("otherNames") or [])[:4]:
            other.append(clean(o)[:60])
    return [st.get(P, {}).get("identificationModule", {}).get("nctId", ""),
            "|".join(names), "|".join(types), "|".join(other[:8])]


def main():
    os.makedirs(DATA, exist_ok=True)
    total = C.load().get("total")
    ck = (json.load(open(CKPT)) if os.path.exists(CKPT)
          else {"token": None, "rows": 0, "pages": 0, "done": False})
    if ck.get("done"):
        print(f"  already complete: {ck['rows']:,} rows")
        return 0
    s = C.Session()
    t0 = time.time()
    f = gzip.open(ROWS, "at" if ck["rows"] else "wt", newline="", encoding="utf-8")
    w = csv.writer(f)
    if not ck["rows"]:
        w.writerow(COLS)
    try:
        while True:
            kw = {"pageSize": PAGE, "fields": ",".join(FIELDS), "format": "json"}
            if ck["token"]:
                kw["pageToken"] = ck["token"]
            r = s.get("/api/v2/studies", **kw)
            studies = r.get("studies", [])
            if not studies:
                ck["done"] = True
                json.dump(ck, open(CKPT, "w"))
                break
            recs = [extract(st) for st in studies]
            if ck["pages"] == 0:
                empty = [COLS[i] for i in range(len(COLS)) if not any(x[i] for x in recs)]
                print(f"  path check: " + ("every column populated somewhere" if not empty
                                           else f"NEVER POPULATED -> {empty}"), flush=True)
                if "names" in empty:
                    raise SystemExit("  names are the point; aborting")
            for rec in recs:
                w.writerow(rec)
            ck["rows"] += len(recs)
            ck["pages"] += 1
            ck["token"] = r.get("nextPageToken")
            f.flush()
            json.dump(ck, open(CKPT, "w"))
            if ck["pages"] % 150 == 0:
                print(f"    page {ck['pages']:>4}  {ck['rows']:>8,} rows"
                      + (f" ({ck['rows']/total:.0%})" if total else "")
                      + f"   {time.time()-t0:.0f}s", flush=True)
            if not ck["token"]:
                ck["done"] = True
                json.dump(ck, open(CKPT, "w"))
                break
        f.close()
    finally:
        s.close()
        print(f"\n  {s.n} request(s), {s.spent:.0f}s")
    print(f"  {ck['rows']:,} rows -> {os.path.basename(ROWS)} "
          f"({os.path.getsize(ROWS)/1e6:.0f} MB gzipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
