#!/usr/bin/env python3
"""Pull the RCRA Biennial Report by management category and cycle, resumably.

    python3 brpull.py [--all]

The question this exists to settle: **the row counts say recovery is collapsing and
disposal is growing, and rows are not tons.** Metals recovery falls from 20,569 rows in
2001 to 8,255 in 2023 while landfill rises from 20,650 to 58,668 -- but the table's total
row count also grew from 1.13M to 1.77M over the same span, so the whole pattern could be
reporting granularity. Only `managed_tons` settles it.

Three things learned by probing before writing this:

**The path API cannot filter a value containing a slash.** `MANAGEMENT_CATEGORY/SLUDGE
TRTMNT / STAB / ENCAP` returns zero rows, silently, because the slash is read as a path
separator -- and zero is exactly what an absent category looks like. Three real categories
disappeared that way. `BEGINNING/SLUDGE` recovers all 32,184 of them. Any category here is
matched by an unambiguous prefix for that reason.

**Column selection is not supported.** `COLUMNS/...`, a leading column list and a
`?columns=` query string all return the full 68 columns unchanged. CSV rather than JSON is
the only lever, and it is worth about 4x: 358 bytes a row against roughly 1,500.

**`COUNT/JSON` works on any filter**, so every slice's size is known before it is fetched
and a partial pull can be checked against what it should have been.

**And `urllib` is unusable against this host.** A first version of this script used
`urllib.request` and read 1.9 MB in thirteen minutes -- about 2.4 KB/s. `curl` fetched the
same kind of slice at 341 KB/s plain and **476 KB/s with `--compressed`**, and a bare
`urllib` attempt on a 25 MB slice did not finish inside three minutes at all. Whatever the
cause -- no keep-alive, no content encoding, buffer behaviour -- the fix is to shell out
to curl rather than diagnose it, because a hundredfold is the difference between a
half-hour campaign and an impossible one.

Each slice is cached as it lands. A connection that drops mid-stream then costs one slice
rather than the campaign, which is the same lesson the landfill recipe learned from a
Census fetch that ran fifteen minutes without finishing.

**The cache lives beside the recipe, not in `/tmp`.** A first version defaulted to
`/tmp/br-cache`, and the first time the machine cleared it, thirty-five minutes and 1.67
million rows went with it. The derived `br_trend.json` survived because it was written into
the recipe, which is the only reason the figure could still be rebuilt. A cache that is
expensive to refill is not temporary.
"""
import csv, gzip, io, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
CACHE = os.environ.get("HWF_CACHE") or os.path.join(DATA, "br-cache")
BASE = "https://data.epa.gov/efservice/BR_REPORTING"
AGENT = "public-record-research/1.0 (hazardous waste flows recipe; contact dl.eeee.nv@gmail.com)"
CYCLES = list(range(2001, 2024, 2))

# (label, filter path). Prefix filters are used where the value contains a slash, which
# the path API cannot match, and where an exact value would be ambiguous it is spelled out.
CATS = [
    ("METALS RECOVERY", "MANAGEMENT_CATEGORY/METALS%20RECOVERY"),
    ("SOLVENTS RECOVERY", "MANAGEMENT_CATEGORY/SOLVENTS%20RECOVERY"),
    ("ENERGY RECOVERY", "MANAGEMENT_CATEGORY/ENERGY%20RECOVERY"),
    ("OTHER RECOVERY", "MANAGEMENT_CATEGORY/OTHER%20RECOVERY"),
    ("LANDFILL", "MANAGEMENT_CATEGORY/LANDFILL"),
    ("DEEPWELL", "MANAGEMENT_CATEGORY/BEGINNING/DEEPWELL"),
]
CATS_ALL = CATS + [
    ("INCINERATION", "MANAGEMENT_CATEGORY/INCINERATION"),
    ("FUEL BLENDING", "MANAGEMENT_CATEGORY/FUEL%20BLENDING"),
    ("WASTEWATER TREATMENT", "MANAGEMENT_CATEGORY/WASTEWATER%20TREATMENT"),
    ("SLUDGE TREATMENT", "MANAGEMENT_CATEGORY/BEGINNING/SLUDGE"),
    ("LAND TREATMENT", "MANAGEMENT_CATEGORY/BEGINNING/LAND%20TREATMENT"),
    ("OTHER TREATMENT", "MANAGEMENT_CATEGORY/OTHER%20TREATMENT"),
]
# 19 of the table's 67 columns. A later schema survey found several that matter and are
# now carried: `management_location` states ONSITE/OFFSITE explicitly rather than leaving it
# to be inferred from `br_form`; the `*_included_in_nbr` flags say whether EPA counts a row
# in its own National Biennial Report, and the share of tonnage they cover moves between
# cycles (90.6% in 2001, 99.7% in 2011, 89.8% in 2023), so they are part of any trend;
# `priority_chemical` is Y on 28% of rows and `acute_nonacute_status` marks the P-listed
# wastes that are lethal in small quantities.
#
# Adding a column does not invalidate a cached slice, it just means the slice lacks it.
# Delete the cache to re-pull with the wider set.
KEEP = ["report_cycle", "management_category", "management_method", "management_location",
        "br_form", "handler_id", "handler_name", "state", "county_name", "location_zip",
        "primary_naics", "form_code", "source_code", "federal_waste_codes",
        "generation_tons", "managed_tons", "shipped_tons", "received_tons",
        "receiver_id", "receiver_state", "shipper_id", "description",
        "gen_waste_included_in_nbr", "mgmt_waste_included_in_nbr",
        "priority_chemical", "acute_nonacute_status", "waste_min_code",
        "calculated_generator_status", "wastewater", "mixed_waste"]


CURL = shutil.which("curl")


def fetch(url, tries=4, timeout=900):
    """Fetch through curl. See the module docstring for why not urllib."""
    if not CURL:
        raise RuntimeError("curl is required: urllib is ~100x slower against this host")
    for attempt in range(tries):
        fd, tmp = tempfile.mkstemp(suffix=".part")
        os.close(fd)
        try:
            r = subprocess.run(
                [CURL, "-sS", "--compressed", "--fail", "--max-time", str(timeout),
                 "-H", f"User-Agent: {AGENT}", url, "-o", tmp],
                capture_output=True, text=True)
            if r.returncode == 0 and os.path.getsize(tmp) > 0:
                with open(tmp, "rb") as f:
                    return f.read()
            print(f"      attempt {attempt+1} failed (curl {r.returncode} "
                  f"{r.stderr.strip()[:70]}), retrying", flush=True)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        time.sleep(4 * (attempt + 1))
    return None


def count(filt, cycle):
    b = fetch(f"{BASE}/{filt}/REPORT_CYCLE/{cycle}/COUNT/JSON")
    if not b:
        return None
    try:
        return int("".join(c for c in b.decode() if c.isdigit()))
    except ValueError:
        return None


def slice_path(label, cycle):
    return os.path.join(CACHE, f"{label.replace(' ', '_')}-{cycle}.csv.gz")


def main():
    cats = CATS_ALL if "--all" in sys.argv else CATS
    os.makedirs(CACHE, exist_ok=True)
    os.makedirs(DATA, exist_ok=True)
    total_rows = 0
    for label, filt in cats:
        for cycle in CYCLES:
            path = slice_path(label, cycle)
            if os.path.exists(path):
                # Count CSV records, not lines. `description` is free text and carries embedded
                # newlines on 40 of the 144 slices, so a line count reports 2,036 rows that do
                # not exist -- more than the API's own COUNT says are there. The cold path below
                # counts DictReader records, and a warm re-run that disagrees with the fetch
                # which filled the cache is the same corpus reporting two sizes.
                with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
                    have = sum(1 for _ in csv.DictReader(f))
                total_rows += have
                print(f"  {label:<22}{cycle}  cached {have:>8,}", flush=True)
                continue
            n = count(filt, cycle)
            if n == 0:
                with gzip.open(path, "wt", encoding="utf-8", newline="") as f:
                    csv.writer(f).writerow(KEEP)
                print(f"  {label:<22}{cycle}  {0:>8,}  (none reported)", flush=True)
                continue
            t0 = time.time()
            blob = fetch(f"{BASE}/{filt}/REPORT_CYCLE/{cycle}/CSV")
            if blob is None:
                print(f"  {label:<22}{cycle}  FAILED, leaving uncached", flush=True)
                continue
            rd = csv.DictReader(io.StringIO(blob.decode("latin-1")))
            got = 0
            tmp = path + ".tmp"
            with gzip.open(tmp, "wt", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(KEEP)
                for r in rd:
                    w.writerow([(r.get(k) or "") for k in KEEP])
                    got += 1
            # A short read is the failure mode that matters: it looks like a real answer.
            if n is not None and got < n * 0.999:
                os.remove(tmp)
                print(f"  {label:<22}{cycle}  SHORT {got:,} of {n:,}, discarded", flush=True)
                continue
            os.replace(tmp, path)
            total_rows += got
            print(f"  {label:<22}{cycle}  {got:>8,}  ({time.time()-t0:.0f}s, "
                  f"{len(blob)/1e6:.1f} MB)", flush=True)
    print(f"\n  {total_rows:,} rows across {len(cats)} categories and {len(CYCLES)} cycles")
    return 0


if __name__ == "__main__":
    sys.exit(main())
