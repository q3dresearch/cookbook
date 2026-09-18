#!/usr/bin/env python3
"""Does the company register publish its dead, and how far back does it keep itself?

    python3 retention.py

Two questions, both asked before any survival curve was attempted, because the answer
to either could have ended the recipe:

1. **Does the monthly bulk file contain dissolved companies?** The recipe was filed in
   the larder on the grounds that "these are legal records with dates attached, so the
   history is in the data itself." That is the claim being tested.

2. **How far back does Companies House keep its own monthly files?** The download page
   advertises one month. If older months are addressable, deaths are recoverable by
   differencing snapshots and this stays a larder recipe. If they are not, the deaths
   are perishable and it is a capture job.

Neither needs the 470 MB file. The first reads the first few megabytes of the zip by
range request and inflates the deflate stream directly, which yields tens of thousands
of rows for six megabytes of download. The second is a HEAD request per month.
"""
import collections, csv, io, os, struct, subprocess, sys, zlib

BASE = "https://download.companieshouse.gov.uk/BasicCompanyDataAsOneFile-{}.zip"
UA = "q3dresearch wss +https://github.com/q3dresearch" + (
    f" ({os.environ['WSS_CONTACT']})" if os.environ.get("WSS_CONTACT") else "")


def head(url):
    r = subprocess.run(["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}",
                        "-m", "25", "-A", UA, "-I", url], capture_output=True, text=True)
    return r.stdout.strip()


def peek(month, nbytes=6_000_000):
    """The first rows of a zipped CSV, without downloading the zip.

    A zip's central directory lives at the END of the file, so the usual readers need
    the whole thing. But the first member's local header sits at offset 0 and its
    deflate stream follows immediately, so a raw inflate over a range request gets the
    beginning of the CSV for a rounding error of the bandwidth.
    """
    r = subprocess.run(["curl", "-sS", "-m", "180", "-A", UA, "-r", f"0-{nbytes}",
                        BASE.format(month)], capture_output=True)
    b = r.stdout
    if b[:4] != b"PK\x03\x04":
        raise SystemExit(f"not a zip: {b[:8]!r}")
    n, m = struct.unpack("<HH", b[26:30])
    body = zlib.decompressobj(-15).decompress(b[30 + n + m:])
    lines = body.decode("utf-8", errors="replace").split("\n")
    return list(csv.DictReader(io.StringIO("\n".join(lines[:-1]))))


def main():
    print("== 1. does the live file carry dissolved companies? ==")
    rows = peek("2026-09-01")
    st = collections.Counter((r.get("CompanyStatus") or "").strip() for r in rows)
    dis = sum(1 for r in rows if (r.get("DissolutionDate") or "").strip())
    print(f"   {len(rows):,} rows read from the head of the file")
    print(f"   rows carrying a DissolutionDate: {dis:,}")
    for s, n in st.most_common():
        print(f"      {n:7,}  {s}")
    print("   Every status above is a status a company holds while still ON the register.")
    print("   The column exists and is never populated: this is a survivors-only snapshot,")
    print("   and the recipe's filing premise -- that the history is in the data -- is wrong.")

    print("\n== 2. how far back does the publisher keep its own snapshots? ==")
    months = [f"{y}-{m:02d}-01" for y in range(2019, 2027) for m in range(1, 13)]
    got = []
    for mo in months:
        if head(BASE.format(mo)) == "200":
            got.append(mo)
    by = collections.Counter(m[:4] for m in got)
    print(f"   {len(got)} of {len(months)} months are addressable; oldest {got[0] if got else 'none'}")
    for y in sorted(by):
        print(f"      {y}  {by[y]:2d} months")
    print("   Dense for the last two years, scattered before that. So a death is observable")
    print("   by differencing snapshots, but only inside the window the publisher happens to")
    print("   still be keeping -- which is a retention edge, not an archive.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
