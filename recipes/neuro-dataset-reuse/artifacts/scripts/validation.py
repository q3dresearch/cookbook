#!/usr/bin/env python3
"""The live validator field, fetched separately so no existing figure's numbers move.

    python3 validation.py

**`issuesStatus` is deprecated and `validation` replaced it.** Plate 3 was built on
`issuesStatus` and read its emptiness as a collapse in validation coverage -- 100% of 2016
deposits down to 1% of 2026 -- and concluded the recent half of the archive could not be
audited. That was the plate's own stated falsifier and it fired: on a 66-dataset probe,
**`validation` is populated on 66 of 66, every year, while `issuesStatus` is empty on 16 of
them. Not one dataset has both empty.**

**The two fields are not the same measurement.** ds000001 reports 3,950 warnings under
`validation` and 4 under `issuesStatus`. Error counts agree on the datasets checked; warning
counts do not, because the v2 validator counts instances where v1 counted types.

**And the validator changed major version.** Versions seen: 1.10.0, 1.14.6, 1.14.8 against
2.0.3, 2.0.8, 2.2.5, 2.3.2. `validatorMetadata` only appears alongside v2, which is why it
reads as absent before 2024.

**A partial fetch that reports success is the failure this project keeps finding elsewhere.**
The first run stopped at 1,100 of 1,891 because one dataset's `latestSnapshot` returns a
server-side 404 and the loop broke on any GraphQL error. GraphQL returns partial data alongside
errors, so the fix is to use what came back, count the bad nodes and keep paging.

This fetch is deliberately **additive**. Re-running the main fetch would move every download
count and silently change all seven plates, so this writes `data/validation.json` keyed by
dataset id and nothing else is touched.
"""
import http.client, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "validation.json")
UA = "web-snapshots/1.0 (research; contact dl.eeee.nv@gmail.com) python-urllib"
PAGE, RETRIES = 100, 4

Q = """query($after: String){ datasets(first: %d, after: $after){
  pageInfo{ hasNextPage endCursor }
  edges{ node{ id publishDate created holdDeletion
    latestSnapshot{ tag
      validation{ errors warnings }
      issuesStatus{ errors warnings }
      summary{ validatorMetadata{ validator version } }
      deprecated{ reason timestamp user }
      related{ kind relation id } } } } } }""" % PAGE


def main():
    c = http.client.HTTPSConnection("openneuro.org", timeout=120)
    c.connect()
    rows, after, pages, nulls, node_errs = [], None, 0, 0, 0
    t0 = time.time()
    while True:
        body = json.dumps({"query": Q, "variables": {"after": after}}).encode()
        j = None
        for a in range(RETRIES):
            try:
                c.request("POST", "/crn/graphql", body=body,
                          headers={"User-Agent": UA, "Content-Type": "application/json"})
                j = json.loads(c.getresponse().read())
                break
            except Exception:
                try: c.close()
                except Exception: pass
                time.sleep(1 + a); c.connect()
        # GraphQL returns partial data ALONGSIDE errors. One dataset whose latestSnapshot
        # 404s server-side killed a 1,891-row fetch at 1,100 and reported success, which is
        # exactly the silent-truncation failure this project keeps finding in other people's
        # data. Use whatever came back and keep paging; only stop if there is no data at all.
        if not j:
            print(f"  page {pages}: no response"); break
        d = (j.get("data") or {}).get("datasets") or {}
        if j.get("errors"):
            node_errs += len(j["errors"])
            bad = [".".join(str(x) for x in (e.get("path") or [])) for e in j["errors"]]
            print(f"  page {pages}: {len(j['errors'])} node error(s), continuing "
                  f"-- {bad[0][:60]}", flush=True)
        if not d.get("edges") and not (d.get("pageInfo") or {}).get("hasNextPage"):
            print(f"  page {pages}: no edges and no next page, stopping"); break
        for e in (d.get("edges") or []):
            n = (e or {}).get("node")
            if not n or not n.get("id"):
                nulls += 1; continue
            ls = n.get("latestSnapshot") or {}
            rows.append({
                "id": n.get("id"), "pub": (n.get("publishDate") or n.get("created") or "")[:10],
                "hold": n.get("holdDeletion"), "tag": ls.get("tag"),
                "validation": ls.get("validation"), "issuesStatus": ls.get("issuesStatus"),
                "validator": ((ls.get("summary") or {}).get("validatorMetadata") or {}),
                "deprecated": ls.get("deprecated"), "related": ls.get("related") or []})
        pages += 1
        pi = d.get("pageInfo") or {}
        if not pi.get("hasNextPage"): break
        after = pi.get("endCursor")
        print(f"  page {pages}: {len(rows)} rows, {time.time()-t0:.0f}s", flush=True)
    c.close()
    out = {"retrieved": time.strftime("%Y-%m-%d"), "null_nodes_skipped": nulls,
           "node_errors": node_errs, "reported_total": 1891, "rows": rows}
    json.dump(out, open(OUT + ".tmp", "w")); os.replace(OUT + ".tmp", OUT)
    v = sum(1 for r in rows if r["validation"])
    i = sum(1 for r in rows if r["issuesStatus"])
    print(f"\n  {len(rows):,} datasets, {nulls} null nodes, {node_errs} node errors, "
          f"{time.time()-t0:.0f}s")
    print(f"  validation populated   {v:>5} ({v/len(rows):.0%})")
    print(f"  issuesStatus populated {i:>5} ({i/len(rows):.0%})")
    print(f"  both empty             {sum(1 for r in rows if not r['validation'] and not r['issuesStatus']):>5}")
    print(f"  deprecated snapshots   {sum(1 for r in rows if r['deprecated']):>5}")
    print(f"  holdDeletion set       {sum(1 for r in rows if r['hold']):>5}")
    print(f"  related populated      {sum(1 for r in rows if r['related']):>5}")
    print(f"  wrote {OUT} ({os.path.getsize(OUT):,}B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
