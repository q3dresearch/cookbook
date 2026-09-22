#!/usr/bin/env python3
"""Page the whole register once, over one connection, into a compressed local table.

    python3 ctg2.py

**Why this is affordable.** The host charges ~134 s to open a connection and ~0.3 s per
request after that (`artifacts/research-questions/fetch-constraint.md`). All 604 pages cost
one handshake plus about three minutes, and every question afterwards is a local scan.

**Why page rather than facet.** `/stats/field/values` gives marginals in one request, but the
question the statute makes worth asking needs *two dates from the same row* — primary
completion and results submission — and no faceting endpoint can produce that.

**Why JSON rather than CSV.** `format=csv` was tried first, because letting the server flatten
the record avoids hard-coding a path per field. It rejects the field vocabulary the rest of
the API uses: asking for `NCTId` returns *"Parameter 'fields' contains invalid CSV column
name: 'NCTId'"*. CSV takes different column names, and its response carries no
`nextPageToken`, so it cannot be paged anyway. JSON takes the piece names, returns the token,
and costs a path map.

**Whole modules are requested, not leaf names.** The first attempt asked for the leaf
`PrimaryCompletionDate` and got back the struct's `.date` with its `.type` silently omitted.
That type is ACTUAL or ESTIMATED, and it is the difference between a trial that has finished
and one that plans to — starting a statutory clock from an estimated date measures nothing.
Asking for the module returns every struct whole. Bytes are free here; a 640 KB page arrives
in one second.

**The path map is validated, not trusted.** A wrong path does not error — it yields an empty
string for every row, which looks exactly like a field that happens to be blank. So the first
page is checked: any path that is empty across all 1,000 studies is reported before the walk
continues, because that is what a typo looks like and it is indistinguishable from a real
absence at row level.

**Dates are month precision.** `2014-01`, not `2014-01-27`. The statute's clock is 365 days,
so any deadline test carries an inherent ±15 days and a figure that draws a hard line at the
deadline is drawing it through the middle of the uncertainty. Day-of-month is recorded when
present and the precision of each date is recorded alongside it.

**It checkpoints.** The toll is charged on connect, so a run that dies half way resumes from
its page token rather than starting over.
"""
import csv, gzip, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ctg as C                                                          # noqa: E402

DATA = os.path.join(HERE, "..", "data")
ROWS = os.path.join(DATA, "studies.csv.gz")
CKPT = os.path.join(DATA, "studies.checkpoint.json")
PAGE = 1000

P = "protocolSection"
S = f"{P}.statusModule"
# column -> path in the returned document. Validated against the first page.
PATHS = {
    "nct_id": f"{P}.identificationModule.nctId",
    "status": f"{S}.overallStatus",
    "study_type": f"{P}.designModule.studyType",
    "phases": f"{P}.designModule.phases",
    "first_submit": f"{S}.studyFirstSubmitDate",
    "first_post": f"{S}.studyFirstPostDateStruct.date",
    "primary_completion": f"{S}.primaryCompletionDateStruct.date",
    "primary_completion_type": f"{S}.primaryCompletionDateStruct.type",
    "completion": f"{S}.completionDateStruct.date",
    "completion_type": f"{S}.completionDateStruct.type",
    "results_submit": f"{S}.resultsFirstSubmitDate",
    "results_post": f"{S}.resultsFirstPostDateStruct.date",
    "last_update_post": f"{S}.lastUpdatePostDateStruct.date",
    "sponsor_class": f"{P}.sponsorCollaboratorsModule.leadSponsor.class",
    "sponsor_name": f"{P}.sponsorCollaboratorsModule.leadSponsor.name",
    "enrollment": f"{P}.designModule.enrollmentInfo.count",
    "enrollment_type": f"{P}.designModule.enrollmentInfo.type",
    "why_stopped": f"{S}.whyStopped",
    "fda_drug": f"{P}.oversightModule.isFdaRegulatedDrug",
    "fda_device": f"{P}.oversightModule.isFdaRegulatedDevice",
    "has_results": "hasResults",
}
# Whole modules, not leaf names. Asking for the leaf `PrimaryCompletionDate` returned the
# struct's `.date` and silently omitted its `.type` — and ACTUAL vs ESTIMATED is exactly what
# says whether a trial has really completed, so a 365-day statutory clock started from an
# estimated date would be measuring nothing. Requesting the module returns every struct whole,
# which costs bytes (free here: a 640 KB page arrives in one second) and removes a class of
# error where a missing subfield looks like a blank column.
FIELDS = ["protocolSection.identificationModule.nctId",
          "protocolSection.statusModule",
          "protocolSection.designModule.studyType",
          "protocolSection.designModule.phases",
          "protocolSection.designModule.enrollmentInfo",
          "protocolSection.sponsorCollaboratorsModule.leadSponsor",
          "protocolSection.oversightModule",
          "hasResults"]
COLS = list(PATHS)


def dig(o, path):
    for k in path.split("."):
        if not isinstance(o, dict):
            return ""
        o = o.get(k)
        if o is None:
            return ""
    if isinstance(o, list):
        return "|".join(str(x) for x in o)
    if isinstance(o, bool):
        return "true" if o else "false"
    return str(o).replace("\n", " ").replace("\r", " ")


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

            if ck["pages"] == 0:
                empty = [c for c in COLS
                         if not any(dig(st, PATHS[c]) for st in studies)]
                print(f"  path check on {len(studies)} studies: "
                      + ("every column populated somewhere" if not empty
                         else f"NEVER POPULATED -> {empty}"), flush=True)
                if len(empty) > 3:
                    raise SystemExit("  too many dead paths; not walking 604 pages")

            for st in studies:
                w.writerow([dig(st, PATHS[c]) for c in COLS])
            ck["rows"] += len(studies)
            ck["pages"] += 1
            ck["token"] = r.get("nextPageToken")
            f.flush()
            json.dump(ck, open(CKPT, "w"))
            if ck["pages"] % 50 == 0:
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
        print(f"\n  {s.n} request(s), {s.spent:.0f}s "
              f"({s.spent/max(s.n,1):.1f}s each including the one-off handshake)")
    print(f"  {ck['rows']:,} rows -> {os.path.basename(ROWS)} "
          f"({os.path.getsize(ROWS)/1e6:.0f} MB gzipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
