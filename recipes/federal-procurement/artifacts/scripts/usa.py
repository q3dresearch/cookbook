#!/usr/bin/env python3
"""Session and bulk-download helpers for USAspending, built around two measured properties.

    python3 usa.py            # runs the screens and caches them

**One: the cost is charged on the connection.** ~130 s to open one, then 0.3-1.6 s per
request. Measured through a client that opens a fresh connection per call, every request reads
as two minutes and the source looks unusable. Four hosts measured from this machine now range
0.3 s to 240 s, so the toll is a property of the route rather than of any API -- but it is
always per connection, so everything here runs down one held-open socket.

**Two: a bad field name does not fail.** Asking `spending_by_award` for a field that does not
exist returns HTTP 200 with that key present and `null` on every row -- indistinguishable from
a real but empty column. A bad *filter* value, by contrast, returns 400 and enumerates what is
valid. So filters can be trusted to complain and fields cannot, and `prove_fields()` exists to
check a field is non-null on a sample before any figure relies on it.

**The search endpoint cannot answer this recipe's question.** The three values the FAR
distinguishes -- base, base-plus-exercised-options, base-plus-all-options -- are not search
fields; they are silently null there. They exist on the single-award endpoint and in the bulk
download's 297 columns, and at 5,927,888 contract awards in one fiscal year the per-award route
is not available. So the bulk download is the only way in, and it is asynchronous: request,
poll, then fetch a zip from a different host.

**Generation time is the real cost, not bytes.** GSA for one month took 530 s to build and is
21 MB. One month of DoD did not finish in ten minutes. Size the request before committing to
it.
"""
import datetime, http.client, json, os, ssl, sys, time, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "usa.json")
API = "api.usaspending.gov"
FILES = "files.usaspending.gov"
UA = {"User-Agent": "web-snapshots/0.1 (public-record research; +https://github.com/neldivad)",
      "Accept": "application/json", "Content-Type": "application/json",
      "Connection": "keep-alive"}
CONTRACTS = ["A", "B", "C", "D"]


class Session:
    """One connection, reused, reconnecting on hang-up. See the module docstring."""

    def __init__(self, host=API):
        self.host, self.c, self.n, self.spent = host, None, 0, 0.0

    def _connect(self):
        t = time.time()
        self.c = http.client.HTTPSConnection(self.host, 443, timeout=600,
                                             context=ssl.create_default_context())
        self.c.connect()
        el = time.time() - t
        self.spent += el
        print(f"      [connected to {self.host} in {el:.0f}s]", flush=True)

    def call(self, method, path, body=None, tries=3, raw=False):
        for a in range(tries):
            if self.c is None:
                self._connect()
            t = time.time()
            try:
                h = dict(UA)
                if raw:
                    h["Accept"] = "*/*"
                self.c.request(method, path, body=json.dumps(body) if body else None,
                               headers=h)
                r = self.c.getresponse()
                data = r.read()
                el = time.time() - t
                self.n += 1
                self.spent += el
                print(f"      {r.status} in {el:.1f}s, {len(data):,}B", flush=True)
                if r.getheader("Connection", "").lower() == "close":
                    self.close()
                if raw:
                    return r.status, data
                try:
                    return r.status, json.loads(data)
                except Exception:
                    return r.status, data[:400]
            except Exception as e:
                print(f"      {type(e).__name__}, reconnecting", flush=True)
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


def prove_fields(s, fields, sample=20):
    """A field that does not exist returns null on every row rather than an error, so the
    only way to tell a wrong name from an empty column is to find one row where it is set."""
    st, d = s.call("POST", "/api/v2/search/spending_by_award/",
                   {"filters": {"award_type_codes": CONTRACTS,
                                "time_period": [{"start_date": "2023-10-01",
                                                 "end_date": "2024-09-30"}]},
                    "fields": fields, "page": 1, "limit": sample})
    rows = (d or {}).get("results", [])
    return {f: sum(1 for r in rows if r.get(f) not in (None, "", [])) for f in fields}


def count(s, **filters):
    st, d = s.call("POST", "/api/v2/search/spending_by_award_count/", {"filters": filters})
    r = (d or {}).get("results", d) or {}
    return r.get("contracts")


def request_download(s, start, end, agencies=None, label=""):
    f = {"prime_award_types": CONTRACTS, "date_type": "action_date",
         "date_range": {"start_date": start, "end_date": end}}
    if agencies:
        f["agencies"] = [{"type": "awarding", "tier": "toptier", "name": a}
                         for a in agencies]
    st, d = s.call("POST", "/api/v2/bulk_download/awards/",
                   {"filters": f, "subawards": False, "columns": [], "file_format": "csv"})
    fn = (d or {}).get("file_name")
    print(f"    requested {label or start+'..'+end}: {fn}", flush=True)
    return fn


def poll(s, file_name, every=30, limit=400):
    """Returns the finished status dict, or None if it never finished."""
    q = "/api/v2/download/status?" + urllib.parse.urlencode({"file_name": file_name})
    t0 = time.time()
    for i in range(limit):
        st, d = s.call("GET", q)
        status = (d or {}).get("status")
        if i % 6 == 0 or status in ("finished", "failed"):
            print(f"    [{i:>3}] {status:<10} rows={(d or {}).get('total_rows')} "
                  f"{time.time()-t0:.0f}s", flush=True)
        if status == "finished":
            return d
        if status == "failed":
            print(f"    FAILED: {json.dumps(d)[:200]}", flush=True)
            return None
        time.sleep(every)
    return None


def download(file_name, dest):
    """The zip lives on a different host, so this pays its own connection toll once."""
    s = Session(FILES)
    try:
        st, data = s.call("GET", f"/generated_downloads/{file_name}", raw=True)
        if st != 200:
            raise SystemExit(f"  download returned {st}")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        tmp = dest + ".tmp"
        open(tmp, "wb").write(data)
        os.replace(tmp, dest)
        print(f"    -> {dest} ({len(data)/1e6:.1f} MB)", flush=True)
        return dest
    finally:
        s.close()


def load():
    return json.load(open(OUT)) if os.path.exists(OUT) else {}


def save(d):
    os.makedirs(DATA, exist_ok=True)
    tmp = OUT + ".tmp"
    json.dump(d, open(tmp, "w"), indent=1)
    os.replace(tmp, OUT)


AGENCIES = ["Department of Defense", "General Services Administration",
            "Department of Veterans Affairs", "Department of Justice",
            "Department of Health and Human Services", "Department of Agriculture",
            "Department of Homeland Security", "Department of the Interior",
            "Department of Transportation", "Department of Commerce",
            "National Aeronautics and Space Administration",
            "Environmental Protection Agency", "Department of Energy"]


def main():
    d = load()
    s = Session()
    try:
        d.setdefault("fetched", datetime.date.today().isoformat())
        if "screens" not in d:
            print("  screens")
            sc = {}
            a = count(s, award_type_codes=CONTRACTS,
                      time_period=[{"start_date": "2023-10-01", "end_date": "2024-09-30"}])
            b = count(s, award_type_codes=CONTRACTS,
                      time_period=[{"start_date": "2023-10-01", "end_date": "2024-09-30"}])
            sc["same_query_twice"] = [a, b]
            st, r = s.call("POST", "/api/v2/search/spending_by_award/",
                           {"filters": {"award_type_codes": ["BANANA"],
                                        "time_period": [{"start_date": "2023-10-01",
                                                         "end_date": "2024-09-30"}]},
                            "fields": ["Award ID"], "page": 1, "limit": 1})
            sc["nonsense_filter_value"] = {"http": st, "body": str(r)[:150]}
            sc["nonsense_field"] = prove_fields(s, ["Award ID", "Banana Amount"])
            d["screens"] = sc
            for k, v in sc.items():
                print(f"    {k:<24}{str(v)[:110]}")
            save(d)
        if "agency_awards_fy2024" not in d:
            print("  contract awards by agency, FY2024")
            out = {}
            for a in AGENCIES:
                out[a] = count(s, award_type_codes=CONTRACTS,
                               agencies=[{"type": "awarding", "tier": "toptier", "name": a}],
                               time_period=[{"start_date": "2023-10-01",
                                             "end_date": "2024-09-30"}])
                print(f"    {a:<48}{out[a]:>12,}")
            out["ALL"] = count(s, award_type_codes=CONTRACTS,
                               time_period=[{"start_date": "2023-10-01",
                                             "end_date": "2024-09-30"}])
            print(f"    {'ALL AGENCIES':<48}{out['ALL']:>12,}")
            d["agency_awards_fy2024"] = out
            save(d)
    finally:
        s.close()
        print(f"\n  {s.n} request(s), {s.spent:.0f}s "
              f"(one handshake plus {s.spent - 130:.0f}s of work)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
