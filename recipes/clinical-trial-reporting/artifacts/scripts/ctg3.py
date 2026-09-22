#!/usr/bin/env python3
"""A second walk, for the columns the first one fetched and threw away.

    python3 ctg3.py

`ctg2.py` requested whole modules — including `statusModule`, which carries the study **start**
date — and then extracted only the paths its column map named. The start date was downloaded
and discarded, so trial *duration* was never available, only registration-to-completion.

This walk adds what the first one dropped, plus three fields it never asked for:

    start date + type      trial duration, and whether the start is real or planned
    intervention types     DRUG / DEVICE / BIOLOGICAL / BEHAVIORAL / PROCEDURE / OTHER
    conditions             the disease area, as free text the sponsor chose
    location countries     the US-site criterion, which is one of FDAAA's four tests

**Why it is cheap enough to redo.** The host charges ~134 s on connect and ~1 s per 1,000-study
page, so a full re-walk is one handshake and about twelve minutes. Discovering a missing column
is not expensive here; assuming one is.

**Why the fields are requested as leaves this time, not modules.** `armsInterventionsModule`
carries full intervention descriptions and `contactsLocationsModule` carries every site's
address. Both would multiply the payload for text no question needs. Requesting
`...interventions.type` and `...locations.country` keeps the pages small. The path check from
`ctg2.py` still runs, because a leaf path that the API silently ignores returns empty strings
rather than an error.

**Countries are deduplicated per study** and stored as a sorted pipe-joined list, so a trial
with forty US sites and one Canadian one stores `CA|US` rather than forty-one rows of nothing.
"""
import csv, gzip, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ctg as C                                                          # noqa: E402

DATA = os.path.join(HERE, "..", "data")
ROWS = os.path.join(DATA, "extra.csv.gz")
CKPT = os.path.join(DATA, "extra.checkpoint.json")
PAGE = 1000
P = "protocolSection"

FIELDS = [f"{P}.identificationModule.nctId",
          f"{P}.statusModule.startDateStruct",
          f"{P}.armsInterventionsModule.interventions.type",
          f"{P}.conditionsModule.conditions",
          f"{P}.contactsLocationsModule.locations.country"]
COLS = ["nct_id", "start", "start_type", "itypes", "conditions", "countries"]


def extract(st):
    sm = st.get(P, {}).get("statusModule", {}).get("startDateStruct", {}) or {}
    iv = (st.get(P, {}).get("armsInterventionsModule", {}) or {}).get("interventions", []) or []
    cond = (st.get(P, {}).get("conditionsModule", {}) or {}).get("conditions", []) or []
    loc = (st.get(P, {}).get("contactsLocationsModule", {}) or {}).get("locations", []) or []
    types = sorted({(i or {}).get("type", "") for i in iv} - {""})
    ctry = sorted({(l or {}).get("country", "") for l in loc} - {""})
    return [st.get(P, {}).get("identificationModule", {}).get("nctId", ""),
            sm.get("date", ""), sm.get("type", ""),
            "|".join(types),
            "|".join(c.replace("|", "/").replace("\n", " ") for c in cond[:6]),
            "|".join(ctry)]


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
                empty = [COLS[i] for i in range(len(COLS))
                         if not any(rec[i] for rec in recs)]
                print(f"  path check on {len(recs)} studies: "
                      + ("every column populated somewhere" if not empty
                         else f"NEVER POPULATED -> {empty}"), flush=True)
                if empty:
                    raise SystemExit("  dead paths; not walking 604 pages")
            for rec in recs:
                w.writerow(rec)
            ck["rows"] += len(recs)
            ck["pages"] += 1
            ck["token"] = r.get("nextPageToken")
            f.flush()
            json.dump(ck, open(CKPT, "w"))
            if ck["pages"] % 100 == 0:
                print(f"    page {ck['pages']:>4}  {ck['rows']:>8,} rows"
                      + (f" of {total:,} ({ck['rows']/total:.0%})" if total else "")
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
