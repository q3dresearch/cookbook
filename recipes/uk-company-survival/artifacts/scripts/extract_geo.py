#!/usr/bin/env python3
"""Re-extract the Companies House snapshots keeping location and size.

    python3 extract_geo.py

The first extract kept five columns -- number, incorporation month, status, SIC, category
-- which was enough for a national survival curve and is not enough for anything else. The
source ZIPs hold 55, and three of the discarded ones matter:

    RegAddress.PostCode         98.9% populated, the only location in the file
    Accounts.AccountCategory    a size proxy: MICRO ENTITY 34%, DORMANT 14%, FULL 1.3%
    RegAddress.PostTown         a human-readable place for naming entities on a chart

`DissolutionDate` is also present and is **0.0% populated**, which confirms rather than
contradicts the recipe's premise: this is a register of live companies, and a death is
still only observable as a disappearance between two snapshots.

**The postcode area is the leading letters and nothing else.** EC1V is area EC, not "ECV";
stripping digits out of the middle of an outward code invents areas that do not exist and
splits London's EC into several. Take characters until the first digit.
"""
import csv, gzip, io, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("FSB_DATA") or os.path.join(HERE, "..", "data")
OUT_COLS = ["number", "incorp", "status", "sic", "category", "postcode", "area",
            "town", "accounts"]


def area(postcode):
    """Postcode area: the letters before the first digit of the outward code."""
    p = (postcode or "").strip().upper()
    if not p:
        return ""
    out = p.split()[0] if " " in p else p[:-3]
    m = re.match(r"^([A-Z]+)", out)
    return m.group(1) if m else ""


def run(snapshot):
    src = os.path.join(DATA, f"ch-{snapshot}.zip")
    dst = os.path.join(DATA, f"geo-{snapshot}.csv.gz")
    if os.path.exists(dst):
        print(f"  {snapshot}: already extracted", flush=True)
        return
    z = zipfile.ZipFile(src)
    member = z.namelist()[0]
    n = 0
    tmp = dst + ".tmp"
    with z.open(member) as f, gzip.open(tmp, "wt", newline="", encoding="utf-8") as g:
        rd = csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"))
        w = csv.writer(g)
        w.writerow(OUT_COLS)
        for r in rd:
            pc = (r.get("RegAddress.PostCode") or "").strip().upper()
            inc = (r.get("IncorporationDate") or "").strip()      # dd/mm/yyyy
            ym = f"{inc[6:10]}-{inc[3:5]}" if len(inc) == 10 else ""
            sic = (r.get("SICCode.SicText_1") or "").strip()[:5]
            w.writerow([r.get(" CompanyNumber") or r.get("CompanyNumber") or "",
                        ym,
                        (r.get("CompanyStatus") or "").strip(),
                        sic,
                        (r.get("CompanyCategory") or "").strip(),
                        pc, area(pc),
                        (r.get("RegAddress.PostTown") or "").strip().upper(),
                        (r.get("Accounts.AccountCategory") or "").strip()])
            n += 1
            if n % 1_000_000 == 0:
                print(f"    {snapshot}: {n:,}", flush=True)
    os.replace(tmp, dst)
    print(f"  {snapshot}: {n:,} companies -> {os.path.basename(dst)}", flush=True)


def main():
    for s in ("2024-09-01", "2025-09-01", "2026-09-01"):
        if os.path.exists(os.path.join(DATA, f"ch-{s}.zip")):
            run(s)
        else:
            print(f"  {s}: no zip on disk, skipped", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
