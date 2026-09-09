"""Harvest public-records request logs from three jurisdictions into one table.

Sources are Socrata datasets that each jurisdiction publishes in full, back to
2011-2016. Nothing here is captured for preservation — the publishers keep their
own history, so nothing here needs preserving: fetch, normalise, analyse,
discard.

PERSONAL DATA. Every source names the requester, and two go further: Oregon
carries the *site address* of residential properties, Vermont's pre-2020 table
carries state employees' email addresses. None of it is needed to answer "who
asks, for what, and do agencies meet their deadline".

So names are fetched, used once to classify the requester as person or
organisation, and never written. The output carries no name, address, email or
postcode. Deleting the name column does not weaken this dataset because the
name column is never created.
"""
import csv, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

UA  = "q3dresearch-cookbook/1.0 (+https://github.com/q3dresearch/cookbook)"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "foia"
# Output directory is an argument so a reader is not required to reproduce this
# repository's layout. It defaults beside the working directory, never inside
# the recipe: the corpus is 730k rows and no data is committed here.
PAGE = 20000

SOURCES = [
    # (jurisdiction, domain, dataset id)
    ("new-orleans",   "data.nola.gov",    "jsrk-e98x"),
    ("vermont",       "data.vermont.gov", "476u-uxxa"),
    ("vermont-pre2020","data.vermont.gov","fwxs-ckd2"),
    ("oregon-deq",    "data.oregon.gov",  "r59j-htxm"),
    ("new-york-city",  "data.cityofnewyork.us", "kegn-anvq"),
]

# Tokens that mark a requester as an organisation rather than an individual.
ORG = re.compile(r"\b(inc|llc|l\.l\.c|ltd|corp|corporation|company|co|associates|"
                 r"assoc|group|partners|llp|pllc|plc|firm|law|legal|attorney|"
                 r"news|times|post|herald|tribune|press|media|radio|tv|journal|"
                 r"university|college|institute|foundation|society|association|"
                 r"council|coalition|union|department|agency|bureau|office|"
                 r"services|solutions|systems|holdings|insurance|bank|realty|"
                 r"environmental|engineering|consulting|title|escrow)\b", re.I)

def classify(name: str) -> str:
    """person | organisation | unknown — from the name alone, then discarded."""
    n = (name or "").strip()
    if not n:
        return "unknown"
    if ORG.search(n):
        return "organisation"
    # A bare "First Last" or "First M. Last" reads as an individual.
    if re.fullmatch(r"[A-Za-z.'-]+(?:\s+[A-Za-z.'-]+){1,3}", n) and not any(ch.isdigit() for ch in n):
        return "person"
    return "unknown"

def fetch(domain, ds):
    rows, off = [], 0
    while True:
        url = (f"https://{domain}/resource/{ds}.json"
               f"?$limit={PAGE}&$offset={off}&$order=:id")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            batch = json.loads(urllib.request.urlopen(req, timeout=120).read())
        except Exception as e:
            print(f"    ! {ds} offset {off}: {e}", file=sys.stderr); break
        if not batch:
            break
        rows += batch; off += len(batch)
        print(f"    {ds}: {len(rows):,}", flush=True)
        if len(batch) < PAGE:
            break
        time.sleep(0.3)
    return rows

def d10(v):
    return (v or "")[:10] or None

def norm(juris, r):
    """Map each jurisdiction's columns onto one shape. Names are read here and
    do not leave this function.

    `request_id` is the publisher's own case number, kept so a cohort can be
    followed across harvests. **The key is the pair (jurisdiction, request_id),
    never the id alone** — each publisher numbers its own cases, and 107 ids in
    this corpus appear in two jurisdictions at once. Joining on the id by itself
    silently merges unrelated requests. It was dropped in the first version, which made the
    only longitudinal question this recipe asks — what becomes of requests that
    are still open past their deadline — impossible to answer without re-deriving
    everything from scratch. It is not personal data: it is the reference the
    agency itself publishes in the same row, and the largest source names no
    requester at all. Oregon publishes no identifier, so its rows carry none and
    cannot be followed.
    """
    if juris == "new-orleans":
        name = r.get("requester_name")
        return dict(request_id=r.get("request_id"),
                    received=d10(r.get("request_date") or r.get("created_date")),
                    closed=d10(r.get("closed_date")), due=d10(r.get("due_date")),
                    status=r.get("status"), outcome=r.get("closure_reasons"),
                    agency=r.get("responsible_department"),
                    channel=r.get("submission_type"),
                    requester_type=classify(name),
                    source_type_native=None)
    if juris.startswith("vermont"):
        name = r.get("requestor") or " ".join(
            x for x in (r.get("requestor_first_name"), r.get("requestor_last_name")) if x)
        return dict(request_id=r.get("foia_id"),
                    received=d10(r.get("date_received") or r.get("request_date")),
                    closed=d10(r.get("date_closed") or r.get("actual_completion_date")),
                    due=None, status=r.get("status"),
                    outcome=r.get("action") or r.get("action_taken"),
                    agency=r.get("state_entity") or r.get("agency"),
                    channel=r.get("type_of_request") or r.get("category"),
                    requester_type=classify(name),
                    source_type_native=None)
    if juris == "new-york-city":
        # NYC OpenRecords names no requester at all, so nothing to classify.
        return dict(request_id=r.get("request_id"),
                    received=d10(r.get("request_submitted_date") or r.get("request_created_date")),
                    closed=d10(r.get("request_close_date")),
                    due=d10(r.get("request_due_date")),
                    status=r.get("request_status"), outcome=None,
                    agency=r.get("agency_name"),
                    channel=r.get("submission_method"),
                    requester_type="not published", source_type_native=None)
    name = r.get("requester_name")
    native = r.get("requester_type")
    return dict(request_id=None,          # Oregon DEQ publishes no request identifier
                received=d10(r.get("create_date")), closed=d10(r.get("close_date")),
                due=None, status=("Closed" if r.get("close_date") else "Open"),
                outcome=r.get("request_outcome"), agency=r.get("assigned_department"),
                channel=r.get("request_type"),
                requester_type=(native.strip().lower() if native else classify(name)),
                source_type_native=native)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    out = []
    for juris, dom, ds in SOURCES:
        print(f"  {juris}", flush=True)
        for r in fetch(dom, ds):
            n = norm(juris, r)
            n["jurisdiction"] = juris
            out.append(n)
    cols = ["jurisdiction","request_id","received","closed","due","status","outcome",
            "agency","channel","requester_type","source_type_native"]
    p = OUT / "requests.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(out)
    have_id = sum(1 for r in out if r.get("request_id"))
    print(f"\n  wrote {len(out):,} rows -> {p}")
    print(f"  {have_id:,} rows carry the publisher's case number "
          f"({have_id/len(out):.0%}); Oregon publishes none")

    # Loud check: no personal data may reach disk. The case-number column is
    # excluded from the scan rather than the scan being loosened — a numeric case
    # number matches the postcode pattern, and widening the pattern to tolerate it
    # would also stop it catching a real postcode.
    scanned = 0
    with p.open(encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        parts = []
        for row in rdr:
            parts.append(",".join(v or "" for k, v in row.items() if k != "request_id"))
            scanned += 1
    text = "\n".join(parts)
    for pat, label in ((r"@[\w.]+\.\w+","email"), (r"\b\d{5}(-\d{4})?\b","postcode"),
                       (r"\b\d+\s+[A-Z]{2,}\s+(ST|AVE|RD|BLVD|DR|LN|CT)\b","street address")):
        hits = len(re.findall(pat, text))
        print(f"  PII check {label:<15} {hits} matches {'OK' if hits==0 else '<-- INSPECT'}"
              f"   ({scanned:,} rows, case-number column excluded)")

if __name__ == "__main__":
    main()
