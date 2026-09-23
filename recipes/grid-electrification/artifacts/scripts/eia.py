#!/usr/bin/env python3
"""EIA bulk files, on one held-open connection, streamed to disk.

    python3 eia.py SEDS          # or EBA, ELEC -- several may be named

**No key.** `api.eia.gov/v2/...` returns 403 `API_KEY_MISSING`, but the *bulk* endpoint
does not ask for one. That is the difference that lets this recipe exist without anybody
registering for anything.

**The toll, measured rather than assumed.** On one connection to www.eia.gov the first
request cost **270.7s** and the second **0.3s**. It is charged on connection setup, per
host pair -- the same shape as USAspending (~135s) and PeeringDB (816.8s then 0.7s).

**And `api.eia.gov` 301s to `www.eia.gov`.** urllib follows that silently, which is why an
earlier probe read 540s: it paid the toll on *both* hosts. http.client does not follow
redirects, which is how it surfaced. Going straight to the real host halves the cost.

**Streamed, not read whole.** A bulk file is tens to hundreds of MB. `urlopen(...).read()`
on one of those has already failed once in this project, on a 1.1M-row download; this
writes in chunks and reports as it goes.
"""
import http.client, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
HOST = "www.eia.gov"      # api.eia.gov 301s here, and a redirect across hosts
                          # costs the connection toll a SECOND time
UA = "web-snapshots/1.0 (research; contact dl.eeee.nv@gmail.com) python-urllib"
PATH = "/opendata/bulk/"


class Session:
    def __init__(self):
        self.c = http.client.HTTPSConnection(HOST, timeout=1800)
        self.n, self.spent = 0, 0.0

    def _req(self, path):
        self.c.request("GET", path, headers={"User-Agent": UA})
        return self.c.getresponse()

    def manifest(self):
        t0 = time.time()
        r = self._req(PATH + "manifest.txt")
        body = r.read()
        self.n += 1
        self.spent += time.time() - t0
        print(f"    manifest {r.status} {len(body):,}b in {time.time()-t0:.0f}s", flush=True)
        return json.loads(body)

    def grab(self, name, dest):
        """Stream one bulk zip to disk, reporting progress."""
        t0 = time.time()
        r = self._req(f"{PATH}{name}.zip")
        if r.status != 200:
            raise SystemExit(f"  {r.status} for {name}.zip")
        total = int(r.headers.get("Content-Length") or 0)
        got = 0
        tmp = dest + ".part"
        with open(tmp, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
                if got % (20 << 20) < (1 << 20):
                    pct = f"{got/total:.0%}" if total else "?"
                    print(f"      {got/1e6:>7.0f} MB  {pct}  "
                          f"{got/1e6/max(time.time()-t0, .1):>5.1f} MB/s", flush=True)
        os.replace(tmp, dest)
        self.n += 1
        self.spent += time.time() - t0
        print(f"    {name}.zip -> {got/1e6:.0f} MB in {time.time()-t0:.0f}s", flush=True)
        return got

    def close(self):
        self.c.close()


def main():
    want = [a.upper() for a in sys.argv[1:]] or ["SEDS"]
    os.makedirs(DATA, exist_ok=True)
    s = Session()
    try:
        m = s.manifest()
        ds = m.get("dataset", m)
        for name in want:
            if name not in ds:
                print(f"  {name}: not in the manifest ({len(ds)} datasets)")
                continue
            info = ds[name]
            dest = os.path.join(DATA, f"eia-{name.lower()}.zip")
            if os.path.exists(dest):
                print(f"  {name}: already on disk, {os.path.getsize(dest)/1e6:.0f} MB")
                continue
            print(f"  {name}: {info.get('title','')[:60]} "
                  f"(updated {str(info.get('last_updated',''))[:10]})", flush=True)
            s.grab(name, dest)
    finally:
        s.close()
        print(f"\n  {s.n} request(s), {s.spent:.0f}s on one connection")
    return 0


if __name__ == "__main__":
    sys.exit(main())
