#!/usr/bin/env python3
"""NREL's Annual Technology Baseline, fetched once on a held connection.

    python3 atb.py

**What this is, stated before anything is built on it.** ATB is a **model output**, not a
register of what anyone paid. NREL assembles it from market data, engineering estimates and
its own projections, and publishes capital cost, fixed and variable O&M, capacity factor and
LCOE by technology, year, financing case and scenario -- including years that have not
happened. Treating an ATB capex figure as an observed transaction price is the mistake this
recipe exists to avoid making, and the projection years must be separated from the historical
ones before any of it is drawn.

**Where it lives.** `oedi-data-lake.s3.amazonaws.com` serves the Open Energy Data Initiative
lake. `/ATB/electricity/csv/2024/ATBe.csv` is a 404; **2023 is the vintage at that path**, at
88,390,227 bytes. robots.txt is a 404, which is no restriction rather than a permission, and
the fetch is a plain public read of a file published to be read.

**No toll here.** Unlike www.eia.gov (270.7s to first byte) and www.peeringdb.com (816.8s),
S3 answered a range request in 0.6 seconds. The connection-setup cost that dominates the
rest of this project does not apply to this host, so there is nothing to amortise and no
reason to hold the connection open for more than the one file.
"""
import http.client, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
HOST = "oedi-data-lake.s3.amazonaws.com"
UA = "web-snapshots/1.0 (research; contact dl.eeee.nv@gmail.com) python-urllib"
VINTAGE = "2023"
PATH = f"/ATB/electricity/csv/{VINTAGE}/ATBe.csv"
DEST = os.path.join(DATA, f"atb-{VINTAGE}.csv")


def main():
    if os.path.exists(DEST):
        print(f"  have {DEST} ({os.path.getsize(DEST):,}b)")
        return 0
    os.makedirs(DATA, exist_ok=True)
    t0 = time.time()
    c = http.client.HTTPSConnection(HOST, timeout=1800)
    c.request("GET", PATH, headers={"User-Agent": UA})
    r = c.getresponse()
    if r.status != 200:
        raise SystemExit(f"  {r.status} for {PATH}")
    total = int(r.headers.get("Content-Length") or 0)
    tmp, got, mark = DEST + ".part", 0, 0
    with open(tmp, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            got += len(chunk)
            if got - mark >= 16 << 20:
                mark = got
                print(f"    {got/1e6:,.0f} MB of {total/1e6:,.0f} in "
                      f"{time.time()-t0:.0f}s", flush=True)
    os.replace(tmp, DEST)
    c.close()
    print(f"  wrote {DEST}  {got:,}b in {time.time()-t0:.0f}s")
    with open(DEST, encoding="utf-8", errors="replace") as f:
        print(f"  header: {f.readline().strip()[:220]}")
        for _ in range(3):
            print(f"    {f.readline().strip()[:220]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
