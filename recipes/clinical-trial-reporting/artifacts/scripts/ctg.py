#!/usr/bin/env python3
"""Base fetch for ClinicalTrials.gov, built around one measured property of the host.

    python3 ctg.py

**The measurement.** Six requests from here, each opening a fresh connection, took 133-135
seconds regardless of payload: 818 bytes and 10,030 bytes cost the same to within a second,
and a bare TCP connect to port 443 took 15 s. For comparison `search.rcsb.org` answered in
under a second from the same machine in the same session. A server doing work does not behave
like that. A fixed toll on the way in does.

**So this module holds one connection open and sends everything down it.** `urllib` cannot:
it opens a new connection per call, which is why the first measurements looked like a
per-request cost. If the toll is per connection it is paid once here; if it turns out to be
per request, nothing is lost by pooling anyway. `artifacts/research-questions/fetch-constraint.md`
records the measurements either way, because a reproducer on another vantage point will see
different numbers and needs a baseline.

**What follows from it.** Request count is the only budget that matters, so:

- Every marginal goes in **one** call. `/stats/field/values` takes a comma-separated field
  list and returns each field's distribution plus its `missingStudiesCount`.
- Nothing pages for rows. 603,730 studies at the API's 1,000-row maximum is 604 requests.
- The cache is written beside the artifact after every phase, atomically, and no phase
  refetches what is already there. At this price a cache is not a temporary file.

**Screens, before any figure.** A nonsense field, a nonsense value, a nonsense page token, and
the same query twice. A bad request here returns HTTP 400 rather than silently handing back
the unfiltered total, which is the failure mode that has cost this project findings elsewhere;
that is worth recording as a property of the source rather than assuming it.
"""
import datetime, http.client, json, os, ssl, sys, time, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "ctg.json")
HOST = "clinicaltrials.gov"
HEADERS = {"User-Agent": "web-snapshots/0.1 (public-record research; +https://github.com/neldivad)",
           "Accept": "application/json", "Connection": "keep-alive"}
TIMEOUT = 420

FACETS = ["OverallStatus", "StudyType", "Phase", "LeadSponsorClass", "EnrollmentType",
          "HasResults", "IsFDARegulatedDrug", "IsFDARegulatedDevice", "OversightHasDMC",
          "DesignAllocation", "DesignMasking", "DesignPrimaryPurpose"]


class Session:
    """One connection, reused. Reconnects if the server hangs up or a request fails."""

    def __init__(self):
        self.c = None
        self.n = 0
        self.spent = 0.0

    def _connect(self):
        t = time.time()
        self.c = http.client.HTTPSConnection(HOST, 443, timeout=TIMEOUT,
                                             context=ssl.create_default_context())
        self.c.connect()
        el = time.time() - t
        self.spent += el
        print(f"      [connected in {el:.0f}s]", flush=True)

    def get(self, path, tries=3, **params):
        if params:
            path += "?" + urllib.parse.urlencode(params)
        for a in range(tries):
            if self.c is None:
                self._connect()
            t = time.time()
            try:
                self.c.request("GET", path, headers=HEADERS)
                r = self.c.getresponse()
                body = r.read()
                el = time.time() - t
                self.n += 1
                self.spent += el
                print(f"      {r.status} in {el:.0f}s, {len(body):,}B  (request {self.n})",
                      flush=True)
                if r.getheader("Connection", "").lower() == "close":
                    self.close()
                if r.status >= 400:
                    raise HTTPStatus(r.status, body[:200].decode("utf-8", "replace"))
                return json.loads(body) if body.strip() else {}
            except HTTPStatus:
                raise
            except Exception as e:
                print(f"      {type(e).__name__} in {time.time()-t:.0f}s", flush=True)
                self.close()
                if a == tries - 1:
                    raise
                time.sleep(3)

    def close(self):
        if self.c is not None:
            try:
                self.c.close()
            except Exception:
                pass
            self.c = None


class HTTPStatus(Exception):
    def __init__(self, code, body):
        super().__init__(f"HTTP {code}: {body}")
        self.code, self.body = code, body


def count(s, **filters):
    """Total matching studies. pageSize=1 because 0 is rejected; the row is discarded."""
    return s.get("/api/v2/studies", pageSize=1, countTotal="true", **filters).get("totalCount")


def load():
    return json.load(open(OUT)) if os.path.exists(OUT) else {}


def save(d):
    os.makedirs(DATA, exist_ok=True)
    tmp = OUT + ".tmp"
    json.dump(d, open(tmp, "w"), indent=1)
    os.replace(tmp, OUT)


def main():
    d = load()
    started = len(d)
    s = Session()
    try:
        d.setdefault("fetched", datetime.date.today().isoformat())

        if "total" not in d:
            print("  total studies")
            d["total"] = count(s)
            print(f"    {d['total']:,}")
            save(d)

        if "facets" not in d:
            print(f"  {len(FACETS)} marginals in one request")
            r = s.get("/api/v2/stats/field/values", fields=",".join(FACETS))
            fields = r if isinstance(r, list) else r.get("fields", [])
            d["facets"] = {f["piece"]: {"field": f["field"],
                                        "missing": f.get("missingStudiesCount"),
                                        "unique": f.get("uniqueValuesCount"),
                                        "values": [(v["value"], v["studiesCount"])
                                                   for v in f.get("topValues", [])]}
                           for f in fields}
            for k, v in d["facets"].items():
                top = v["values"][0] if v["values"] else ("-", 0)
                print(f"    {k:<24}{(v['unique'] or 0):>5} values  "
                      f"{(v['missing'] or 0):>8,} missing   top {top[0]} {top[1]:,}")
            save(d)

        if "screens" not in d:
            print("  screens")
            sc = {"same_query_twice": [d["total"], count(s)]}
            for label, kw in (("nonsense_field", {"filter.banana": "COMPLETED"}),
                              ("nonsense_value", {"filter.overallStatus": "BANANA"}),
                              ("nonsense_page_token", {"pageToken": "BANANA"})):
                try:
                    sc[label] = {"returned": count(s, **kw)}
                except HTTPStatus as e:
                    sc[label] = {"http": e.code, "body": e.body[:120]}
            d["screens"] = sc
            for k, v in sc.items():
                print(f"    {k:<22}{v}")
            save(d)
    finally:
        s.close()
        print(f"\n  {s.n} request(s), {s.spent:.0f}s total, "
              f"{s.spent/max(s.n,1):.0f}s each")
    print(f"  ctg.json has {len(d)} keys ({len(d)-started} added this run)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
