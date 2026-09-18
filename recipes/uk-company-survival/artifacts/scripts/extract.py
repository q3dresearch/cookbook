#!/usr/bin/env python3
"""Reduce a 470 MB registry snapshot to the five columns this recipe needs.

    python3 extract.py                 # every ch-*.zip in artifacts/data

Writes artifacts/data/compact-<date>.csv.gz: company number, incorporation month,
SIC division, company category, status. About 5.5 million rows in, 50 MB out, so the
pairwise work afterwards is cheap and fits in memory without care.

csv.reader with fixed column indices, not DictReader. The same loop written with
DictReader over 55 columns took an order of magnitude longer on a file this shape
earlier in this workspace, and the only thing it bought was readability.
"""
import csv, glob, gzip, io, os, re, sys, zipfile

DATA = os.environ.get("FSB_DATA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
WANT = ["CompanyNumber", "IncorporationDate", "CompanyStatus",
        "SICCode.SicText_1", "CompanyCategory"]
DATE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def sic(text):
    """The SIC code only. The column is 'NNNNN - Free text description'."""
    m = re.match(r"\s*(\d{4,5})", text or "")
    return m.group(1) if m else ""


def month(d):
    """DD/MM/YYYY -> YYYY-MM. British order; reading it as US would mangle every day
    past the twelfth and leave the first twelve looking right."""
    m = DATE.match((d or "").strip())
    return f"{m.group(3)}-{m.group(2)}" if m else ""


def one(path):
    out = os.path.join(DATA, "compact-" + os.path.basename(path)[3:13] + ".csv.gz")
    if os.path.exists(out):
        print(f"  have {os.path.basename(out)}")
        return out
    zf = zipfile.ZipFile(path)
    name = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
    n = kept = 0
    with zf.open(name) as raw, gzip.open(out + ".tmp", "wt", newline="") as fh:
        rd = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", errors="replace"))
        hdr = [h.strip() for h in next(rd)]
        idx = [hdr.index(c) for c in WANT]
        w = csv.writer(fh)
        w.writerow(["number", "incorp", "status", "sic", "category"])
        for r in rd:
            n += 1
            try:
                num, inc, st, sc, cat = (r[i] for i in idx)
            except IndexError:
                continue
            if not num.strip():
                continue
            kept += 1
            w.writerow([num.strip(), month(inc), st.strip(), sic(sc), cat.strip()])
    os.replace(out + ".tmp", out)
    print(f"  {os.path.basename(path)}: {n:,} rows -> {kept:,} kept -> {os.path.basename(out)} "
          f"({os.path.getsize(out)/1e6:.0f} MB)")
    return out


def main():
    zips = sorted(glob.glob(os.path.join(DATA, "ch-*.zip")))
    if not zips:
        print(f"  no snapshots in {DATA}")
        return 1
    for z in zips:
        one(z)
    return 0


if __name__ == "__main__":
    sys.exit(main())
