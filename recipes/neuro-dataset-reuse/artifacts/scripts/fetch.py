#!/usr/bin/env python3
"""Every public OpenNeuro dataset, with what is in it and how much it gets used.

    python3 fetch.py

**What this archive is.** OpenNeuro publishes neuroimaging datasets under CC0 in BIDS
format -- MRI, EEG, MEG, iEEG, PET, NIRS. Nobody is obliged to deposit; people do it to
satisfy a journal, a funder, or their own intentions. That makes it a **voluntary** register,
and the question it can answer is not "what exists" but "what happens to a dataset after
somebody publishes it".

**Why it is worth asking.** A neuroimaging study costs scanner time measured in hundreds of
dollars an hour. If something observable at publication predicts whether anyone downloads the
result, that is directly prescriptive for the next person deciding what to collect and how to
describe it.

**The trap, stated before any number is fetched.** `analytics.downloads` is cumulative and
never resets, so a 2018 dataset has had eight years to accumulate and a 2026 one has had
weeks. Ranking on raw downloads measures the calendar. Every rate here is per unit of time
since publication, and the raw counts are kept so the difference can be shown rather than
asserted.

**A field nobody asks for looks exactly like a field nobody fills.** A first version of this
query omitted `grantIdentifier`, so every dataset reported no grant number and the archive
looked as though it carried none. That zero measured the query. It is requested here for that
reason, along with `seniorAuthor`.

**No key and no toll.** robots.txt is `User-agent: * / Allow: /`, the GraphQL endpoint answers
in 0.2s, and the whole archive is about 1,900 datasets -- a few hundred KB of metadata for
something that would otherwise be terabytes of imaging.

**This endpoint intermittently returns nulls, at two different levels.** One run got
`edges[i].node == null`; the next got a null `edges[i]` itself. The identical query re-sent
minutes later returns 100 complete records, and bisecting field by field found nothing --
every field answers cleanly alone and in combination. The cause is not known and is not
guessed at here.

So each page is **retried up to RETRIES times**, and anything still missing is **counted and
recorded in the cache** rather than silently dropped. A quiet skip would turn an intermittent
server fault into a hole in the population that no later figure could see. The count belongs
in the receipts for the same reason.
"""
import http.client, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "datasets.json")
HOST = "openneuro.org"
UA = "web-snapshots/1.0 (research; contact dl.eeee.nv@gmail.com) python-urllib"
PAGE = 100
RETRIES = 4                 # this endpoint returns intermittent nulls; see the docstring

Q = """
query($after: String) {
  datasets(first: %d, after: $after, orderBy: {created: ascending}) {
    pageInfo { count hasNextPage endCursor }
    edges { node {
      id created publishDate public
      stars { userId } followers { userId }
      analytics { views downloads }
      metadata { species studyDomain studyDesign studyLongitudinal trialCount ages
                 associatedPaperDOI openneuroPaperDOI grantFunderName grantIdentifier seniorAuthor dxStatus
                 affirmedConsent affirmedDefaced modalities tasksCompleted
                 firstSnapshotCreatedAt latestSnapshotCreatedAt }
      snapshots { id tag created }
      latestSnapshot {
        tag created size issuesStatus { errors warnings }
        summary { modalities primaryModality secondaryModalities subjects sessions
                  tasks totalFiles dataProcessed }
        description { Name Authors DatasetDOI License } }
    } }
  }
}""" % PAGE


def main():
    if os.path.exists(OUT):
        d = json.load(open(OUT))
        print(f"  have {OUT} ({len(d['datasets']):,} datasets, "
              f"fetched {d['retrieved']})")
        return 0
    os.makedirs(DATA, exist_ok=True)
    c = http.client.HTTPSConnection(HOST, timeout=600)
    got, after, total, t0, skipped, retried = [], None, None, time.time(), 0, 0

    def fetch_page(after):
        body = json.dumps({"query": Q, "variables": {"after": after}})
        c.request("POST", "/crn/graphql", body=body,
                  headers={"User-Agent": UA, "Content-Type": "application/json"})
        r = c.getresponse()
        raw = r.read()
        if r.status != 200:
            raise SystemExit(f"  {r.status}: {raw[:200]}")
        d = json.loads(raw)
        if not (d.get("data") or {}).get("datasets"):
            raise SystemExit(f"  graphql: {json.dumps(d.get('errors'))[:300]}")
        return d["data"]["datasets"]

    while True:
        page = None
        for attempt in range(RETRIES):
            page = fetch_page(after)
            nodes = [(e or {}).get("node") for e in (page.get("edges") or [])]
            if all(n is not None for n in nodes) and nodes:
                break
            retried += 1
            print(f"    page has {sum(1 for n in nodes if n is None)} null(s) -- "
                  f"retry {attempt+1} of {RETRIES}", flush=True)
            time.sleep(1.5 * (attempt + 1))
        nodes = [(e or {}).get("node") for e in (page.get("edges") or [])]
        bad = sum(1 for n in nodes if n is None)
        if bad:
            skipped += bad
            print(f"    {bad} still null after {RETRIES} tries -- counted, not dropped",
                  flush=True)
        total = page["pageInfo"]["count"]
        got += [n for n in nodes if n is not None]
        print(f"    {len(got):,} of {total:,} in {time.time()-t0:.0f}s", flush=True)
        if not page["pageInfo"]["hasNextPage"]:
            break
        after = page["pageInfo"]["endCursor"]
    c.close()
    tmp = OUT + ".tmp"
    json.dump({"retrieved": time.strftime("%Y-%m-%d"), "host": HOST,
               "reported_count": total, "null_nodes_skipped": skipped,
               "pages_retried": retried,
               "datasets": got}, open(tmp, "w"))
    os.replace(tmp, OUT)
    print(f"  wrote {OUT}: {len(got):,} datasets "
          f"({os.path.getsize(OUT)/1e6:.1f} MB) in {time.time()-t0:.0f}s")
    if skipped:
        print(f"  {skipped} null node(s) skipped and recorded in the cache")
    if total and len(got) != total:
        print(f"  NOTE: the API reported {total:,} and returned {len(got):,}. "
              f"The gap is not assumed to be zero.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
