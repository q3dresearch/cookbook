#!/usr/bin/env python3
"""Every count this recipe needs, from the RCSB search API's server-side facets.

    python3 pdb.py             # fetch and cache, writes a dated snapshot

The PDB holds 260,089 experimentally determined structures. Pulling them as rows would be a
bulk download; the search API instead answers `terms`, `date_histogram` and `histogram`
aggregations server-side, so a whole recipe is about twenty requests.

**Dates: deposit, not release.** The two differ by up to 2,203 entries in a single year — 2024
saw 17,659 depositions and 15,456 releases, 2025 the reverse. Release date measures the embargo
as much as the science, so every "when did this happen" here uses `deposit_date` and says so.

**Screens run before any of this was built, on 2026-09-19.**

*The same query twice* returned 260,089 both times. The PDB grows weekly, so each figure is a
statement about one fetch and the snapshot records which.

*A nonsense attribute fails loudly.* `exptl.banana` returns HTTP 400. This matters because the
previous recipe in this workspace met four parameters that silently returned the unfiltered
total, and the habit of checking carried over.

*A nonsense value returns nothing, not everything.* `exptl.method = "BANANA MICROSCOPY"` gives
HTTP 204 and zero results, which is what a working filter does with a value it does not know.

**One quirk worth knowing.** A `date_histogram` bucket label comes back as epoch milliseconds
for one date attribute and an ISO string for another, in the same API. Both are handled.
"""
import datetime, json, os, socket, sys, time, urllib.parse, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("PDB_DATA") or os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "pdb.json")
UA = "web-snapshots research bot (dl.eeee.nv@gmail.com)"
BASE = "https://search.rcsb.org/rcsbsearch/v2/query?json="
socket.setdefaulttimeout(90)

ALL = {"type": "terminal", "service": "text",
       "parameters": {"attribute": "rcsb_entry_info.structure_determination_methodology",
                      "operator": "exists"}}
METHODS = ["X-RAY DIFFRACTION", "ELECTRON MICROSCOPY", "SOLUTION NMR",
           "ELECTRON CRYSTALLOGRAPHY", "NEUTRON DIFFRACTION", "SOLID-STATE NMR"]


def q(body, tries=4):
    u = BASE + urllib.parse.quote(json.dumps(body))
    for a in range(tries):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(u, headers={"User-Agent": UA}), timeout=120) as r:
                raw = r.read()
                # 204 with an empty body is "no hits", not an error and not everything
                return json.loads(raw) if raw.strip() else {"total_count": 0, "facets": []}
        except urllib.error.HTTPError as e:
            if e.code == 400:
                raise SystemExit(f"  HTTP 400 — the attribute or value is not one the API "
                                 f"knows:\n  {json.dumps(body)[:300]}")
            if a == tries - 1:
                raise
            time.sleep(2 * (a + 1))
        except Exception:                                                # noqa: BLE001
            if a == tries - 1:
                raise
            time.sleep(2 * (a + 1))


def yr(label):
    """One API, two bucket-label formats. Epoch ms from one date attribute, ISO from another."""
    if isinstance(label, (int, float)):
        return datetime.datetime.utcfromtimestamp(label / 1000).year
    return int(str(label)[:4])


def term(attr, value, op="exact_match"):
    return {"type": "terminal", "service": "text",
            "parameters": {"attribute": attr, "operator": op, "value": value}}


def AND(*nodes):
    return {"type": "group", "logical_operator": "and", "nodes": list(nodes)}


def count(query):
    return q({"query": query, "return_type": "entry",
              "request_options": {"paginate": {"start": 0, "rows": 0}}})["total_count"]


def by_year(query, attr="rcsb_accession_info.deposit_date"):
    r = q({"query": query, "return_type": "entry", "request_options": {
        "paginate": {"start": 0, "rows": 0},
        "facets": [{"name": "y", "aggregation_type": "date_histogram",
                    "attribute": attr, "interval": "year"}]}})
    return {yr(b["label"]): b["population"] for b in (r.get("facets") or [{}])[0].get("buckets", [])}


def terms(query, attr, n=40):
    r = q({"query": query, "return_type": "entry", "request_options": {
        "paginate": {"start": 0, "rows": 0},
        "facets": [{"name": "t", "aggregation_type": "terms",
                    "attribute": attr, "max_num_intervals": n}]}})
    return [(b["label"], b["population"])
            for b in (r.get("facets") or [{}])[0].get("buckets", [])]


def hist(query, attr, interval):
    r = q({"query": query, "return_type": "entry", "request_options": {
        "paginate": {"start": 0, "rows": 0},
        "facets": [{"name": "h", "aggregation_type": "histogram",
                    "attribute": attr, "interval": interval}]}})
    return [(b["label"], b["population"])
            for b in (r.get("facets") or [{}])[0].get("buckets", [])]


def snapshot(path):
    import gzip, shutil
    d = os.path.join(DATA, "snapshots")
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, f"pdb-{datetime.date.today().isoformat()}.json.gz")
    if os.path.exists(out):
        return out, False
    with open(path, "rb") as fh, gzip.open(out, "wb") as gz:
        shutil.copyfileobj(fh, gz)
    return out, True


def load():
    if not os.path.exists(OUT):
        raise SystemExit("  pdb.json not cached — run pdb.py first")
    return json.load(open(OUT))


def main():
    if os.path.exists(OUT):
        d = load()
        print(f"  cached: {d['total']:,} entries, fetched {d['fetched']}")
        return 0
    out = {"fetched": datetime.date.today().isoformat(), "total": count(ALL)}
    print(f"  {out['total']:,} entries with a determination methodology")

    UNPUB = term("rcsb_primary_citation.rcsb_journal_abbrev", "To be published")
    out["unpublished_total"] = count(UNPUB)
    out["deposit_by_year"] = by_year(ALL)
    out["release_by_year"] = by_year(ALL, "rcsb_accession_info.initial_release_date")
    out["unpublished_by_year"] = by_year(UNPUB)
    print(f"  'To be published': {out['unpublished_total']:,} "
          f"({out['unpublished_total']/out['total']:.1%})")

    out["method_by_year"] = {}
    out["method_total"] = {}
    out["resolution_by_method"] = {}
    for m in METHODS:
        mq = term("exptl.method", m)
        out["method_total"][m] = count(mq)
        out["method_by_year"][m] = by_year(mq)
        out["resolution_by_method"][m] = hist(mq, "rcsb_entry_info.resolution_combined", 0.25)
        print(f"  {m:<26}{out['method_total'][m]:>9,}")
        time.sleep(0.3)

    out["authors"] = terms(ALL, "audit_author.name", 60)
    out["organisms"] = terms(ALL, "rcsb_entity_source_organism.ncbi_scientific_name", 40)
    out["journals"] = terms(ALL, "rcsb_primary_citation.rcsb_journal_abbrev", 40)
    out["resolution_all"] = hist(ALL, "rcsb_entry_info.resolution_combined", 0.25)
    out["synthetic_by_year"] = by_year(
        term("rcsb_entity_source_organism.ncbi_scientific_name", "synthetic construct"))
    print(f"  {len(out['authors'])} authors, {len(out['organisms'])} organisms, "
          f"{len(out['journals'])} journals")

    os.makedirs(DATA, exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    p, fresh = snapshot(OUT)
    print(f"\n  written to {OUT}")
    print(f"  {'wrote' if fresh else 'already have'} {os.path.basename(p)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
