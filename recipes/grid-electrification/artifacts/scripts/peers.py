#!/usr/bin/env python3
"""PeeringDB facilities, fetched on one held-open connection and cached.

    python3 peers.py            # fetch every facility, cache, print a summary

**Why a session and not requests-in-a-loop.** The first request to www.peeringdb.com from
here costs about **360 seconds** before a byte arrives; later requests on the same
connection cost a fraction of a second. That is the connection toll this project has
measured on USAspending and api.eia.gov too -- it is charged on setup, per host pair, not
on payload. Opening a fresh connection per query would make a twelve-query walk an hour.

**What this is and is not.** PeeringDB is a voluntary directory of *interconnection*
facilities. Networks list themselves because they want to be found for peering. It is not
an inventory of data centres: a single-tenant hyperscale campus with no public peering
presence does not appear, and those are among the largest loads. Every count here
undercounts in a known direction, and the recipe says so rather than correcting for it.

The API key is read from `.env.local` and never printed or written to the cache.
"""
import collections, http.client, json, os, sys, time, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
CACHE = os.path.join(DATA, "peeringdb-fac.json")
HOST = "www.peeringdb.com"
UA = "web-snapshots/1.0 (research; contact dl.eeee.nv@gmail.com) python-urllib"
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))


def api_key():
    for p in (os.path.join(ROOT, ".env.local"), ".env.local"):
        if os.path.exists(p):
            for line in open(p):
                if line.startswith("PEERINGDB_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


class Session:
    """One TLS connection, reused. `spent` is wall clock; `n` is requests."""

    def __init__(self):
        self.key = api_key()
        self.c = http.client.HTTPSConnection(HOST, timeout=900)
        self.n, self.spent = 0, 0.0

    def get(self, path):
        h = {"User-Agent": UA, "Accept": "application/json"}
        if self.key:
            h["Authorization"] = f"Api-Key {self.key}"
        t0 = time.time()
        for attempt in (1, 2):
            try:
                self.c.request("GET", path, headers=h)
                r = self.c.getresponse()
                body = r.read()
                break
            except Exception:
                if attempt == 2:
                    raise
                self.c.close()
                self.c = http.client.HTTPSConnection(HOST, timeout=900)
        dt = time.time() - t0
        self.n += 1
        self.spent += dt
        print(f"    [{self.n:>2}] {r.status} {len(body):>9,}b {dt:>7.1f}s  {path[:56]}",
              flush=True)
        if r.status != 200:
            raise SystemExit(f"  {r.status} from {path}: {body[:200]!r}")
        return json.loads(body)

    def close(self):
        self.c.close()


def fetch():
    s = Session()
    if not s.key:
        raise SystemExit("  PEERINGDB_API_KEY not found in .env.local")
    try:
        out, seen = [], 0
        while True:
            q = urllib.parse.urlencode({"limit": 5000, "skip": seen})
            d = s.get(f"/api/fac?{q}")["data"]
            if not d:
                break
            out += d
            seen += len(d)
            if len(d) < 5000:
                break
        print(f"  {len(out):,} facilities on {s.n} request(s), {s.spent:.0f}s total")
    finally:
        s.close()
    keep = ("id", "name", "city", "state", "zipcode", "country", "latitude", "longitude",
            "net_count", "status", "created", "updated", "org_id")
    return [{k: f.get(k) for k in keep} for f in out]


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    os.makedirs(DATA, exist_ok=True)
    d = fetch()
    tmp = CACHE + ".tmp"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return d


if __name__ == "__main__":
    f = load()
    print(f"\n  {len(f):,} facilities cached")
    byc = collections.Counter(x.get("country") or "(blank)" for x in f)
    print("  top countries: " + ", ".join(f"{k} {v:,}" for k, v in byc.most_common(10)))
    us = [x for x in f if x.get("country") == "US"]
    geo = sum(1 for x in us if x.get("latitude") and x.get("longitude"))
    st = collections.Counter((x.get("state") or "").strip().upper() or "(blank)" for x in us)
    print(f"\n  US: {len(us):,} facilities; {geo:,} ({geo/len(us):.1%}) carry lat/lon; "
          f"{len(st)} distinct state strings, blank on {st['(blank)']}")
    print("  top US states: " + ", ".join(f"{k} {v}" for k, v in st.most_common(8)
                                          if k != "(blank)"))
    nets = sorted(x.get("net_count") or 0 for x in us)
    print(f"  networks per US facility: median {nets[len(nets)//2]}, "
          f"p90 {nets[9*len(nets)//10]}, max {nets[-1]}")
    print(f"  US facilities with 10+ networks: "
          f"{sum(1 for n in nets if n >= 10):,} -- the interconnection-dense ones")
