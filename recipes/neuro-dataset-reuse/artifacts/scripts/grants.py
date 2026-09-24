#!/usr/bin/env python3
"""What the grant behind a shared dataset was awarded, from NIH RePORTER.

    python3 grants.py

**Why this is possible at all.** 443 of 1,891 OpenNeuro datasets name a grant in
`metadata.grantIdentifier`, and 133 of those carry an NIH project number. NIH RePORTER
publishes the award amount for every project number, by fiscal year, with no key. So a
dataset can be joined to the money that produced it.

**What the join gives, and what it does not.** An NIH R01 funds a project for four or five
years: staff, scanner time, analysis, papers, students. The dataset is one output among many.
So the award total is an **upper bound on what the dataset cost**, not the cost, and it is
reported as such. The useful comparison is not absolute -- it is between datasets, where the
same overstatement applies to all of them.

**Grant numbers arrive dirty.** `R01-DC-006706`, `R01 DC014281`, `R01MH080243`,
`"ZIAMH002783", "ZICMH002884"` are all in the field, some as quoted lists of two. The parser
pulls every activity-code + institute + serial triple it can find and queries the CORE project
number, which is what RePORTER keys renewals on -- querying the full project number with its
`-05` suffix returns one year of a five-year award and understates it fivefold.

**Intramural projects (ZIA, ZIC) are kept.** They are NIH-funded work at NIH itself and carry
award amounts like any other, but their totals mean something different -- an intramural
project number can run for decades.

**robots.txt is a 404** on api.reporter.nih.gov, which is an absence of restriction rather
than a grant, and this is a public API documented for programmatic use. The toll is 271
seconds to first byte and 0.6 afterwards, so one held connection does the whole job.
"""
import collections, http.client, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
SRC = os.path.join(DATA, "datasets.json")
CACHE = os.path.join(DATA, "grants.json")
HOST = "api.reporter.nih.gov"
UA = "web-snapshots/1.0 (research; contact dl.eeee.nv@gmail.com) python-urllib"
BATCH = 40

# activity code (R01, R21, K99, ZIA...) + institute (2 letters) + 6-digit serial
PAT = re.compile(r"\b([A-Z]{1,3}\d{0,2})[-\s]?([A-Z]{2})[-\s]?(\d{6})\b")
ACTIVITY = re.compile(r"^(?:[A-Z]\d{2}|Z[A-Z]{2}|[A-Z]{2}\d)$")


def core_numbers(text):
    """Every CORE project number in a messy grantIdentifier string."""
    out = []
    for act, ic, serial in PAT.findall(str(text).upper()):
        if not ACTIVITY.match(act):
            continue
        out.append(f"{act}{ic}{serial}")
    return list(dict.fromkeys(out))


def main():
    raw = json.load(open(SRC))["datasets"]
    want = collections.defaultdict(list)          # core number -> [dataset ids]
    for n in raw:
        gi = (n.get("metadata") or {}).get("grantIdentifier")
        if not gi:
            continue
        for cn in core_numbers(gi):
            want[cn].append(n["id"])
    print(f"  {len(want):,} distinct NIH core project numbers across "
          f"{len({d for v in want.values() for d in v}):,} datasets")
    if os.path.exists(CACHE):
        have = json.load(open(CACHE))
        print(f"  cache has {len(have['project']):,} of them")
        if set(have["project"]) >= set(want):
            return report(have, want)
    else:
        have = {"retrieved": time.strftime("%Y-%m-%d"), "project": {}}
    todo = [k for k in want if k not in have["project"]]
    print(f"  querying {len(todo):,}; the first request pays the toll", flush=True)
    c = http.client.HTTPSConnection(HOST, timeout=900)
    t0 = time.time()
    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        body = json.dumps({
            "criteria": {"project_nums": chunk},
            "include_fields": ["ProjectNum", "CoreProjectNum", "AwardAmount", "FiscalYear",
                               "Organization", "ProjectTitle", "AgencyIcAdmin"],
            "offset": 0, "limit": 500})
        c.request("POST", "/v2/projects/search", body=body,
                  headers={"User-Agent": UA, "Content-Type": "application/json"})
        r = c.getresponse()
        b = r.read()
        if r.status != 200:
            print(f"    {r.status} on batch {i//BATCH}: {b[:160]}")
            time.sleep(3)
            continue
        d = json.loads(b)
        by = collections.defaultdict(list)
        for x in d.get("results", []):
            cn = (x.get("core_project_num") or "").upper()
            by[cn].append({"fy": x.get("fiscal_year"),
                           "amount": x.get("award_amount") or 0,
                           "org": (x.get("organization") or {}).get("org_name"),
                           "title": x.get("project_title"),
                           "ic": (x.get("agency_ic_admin") or {}).get("abbreviation")})
        for cn in chunk:
            have["project"][cn] = by.get(cn, [])
        print(f"    {min(i+BATCH,len(todo)):,} of {len(todo):,} in "
              f"{time.time()-t0:.0f}s", flush=True)
        time.sleep(0.4)
    c.close()
    tmp = CACHE + ".tmp"
    json.dump(have, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return report(have, want)


def report(have, want):
    hit = {k: v for k, v in have["project"].items() if v and k in want}
    print(f"\n  {len(hit):,} of {len(want):,} core numbers resolved in RePORTER "
          f"({len(hit)/max(len(want),1):.0%})")
    tot = sum(sum(y["amount"] for y in v) for v in hit.values())
    print(f"  total awarded across them: ${tot/1e6:,.1f}m")
    per = sorted(((sum(y["amount"] for y in v), k, v) for k, v in hit.items()),
                 reverse=True)
    print(f"\n  {'core project':<16}{'years':>7}{'total award':>15}  institute  title")
    for amt, k, v in per[:8]:
        print(f"  {k:<16}{len(v):>7}{amt:>15,.0f}  {str(v[0]['ic'] or ''):<9}"
              f"  {str(v[0]['title'])[:52]}")
    unres = [k for k in want if not have["project"].get(k)]
    print(f"\n  {len(unres):,} core numbers returned nothing -- kept as unresolved, "
          f"not treated as zero")
    if unres:
        print(f"    examples: {', '.join(unres[:8])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
