#!/usr/bin/env python3
"""How far back each register remembers, and what a resolved shortage lasted.

    python memory.py            # writes artifacts/data/memory.csv

One row per register record: the register, its status folded into one of three
classes every register has -- an open SHORTAGE, a DISCONTINUANCE notice, or a
RESOLVED shortage -- the year the row sits at, the date string that year came from,
and, for a resolved row carrying both a start and an end, its duration in days.

WHICH YEAR A ROW SITS AT. An open row is placed at the year the shortage began, the
only date it has. A resolved row is placed at the year it was resolved (FDA: the
year it was last updated, which for a Resolved row is the resolution), because that
is when a purge clock would start.

THE TEST NEEDS ONE CAPTURE. A register that holds both open and closed records,
each with a date, carries its own control: open rows reaching back years say the
register is not size-limited; closed rows reaching back months say closed rows are
removed. The lone survivors -- one TGA resolution from 2022, one ANSM from 2025 --
prove a closed row CAN sit there for years, so the emptiness beside them is
sweeping, not a young field.

WHAT ONE CAPTURE CANNOT SAY: whether the horizon rolls. A twelve-month window and a
one-off purge look identical in a single snapshot.
"""
import csv, datetime as dt, re, sys
sys.path.insert(0, ".")
import shortagelib as S

FR_DATE = re.compile(r"(\d{2})/(\d{2})/(\d{4})")
# FDA's two oldest posting dates hold 79 rows and nothing else is posted before
# 2015: a bulk load at the database's creation, not events. Pinned by hand -- a
# rule ("many rows, few dates") also flagged 2016, where one drug simply posted its
# package NDCs together. verify.py checks these are still the only dates before 2015.
BULK_LOAD = {"01/01/2012", "02/22/2012"}
CLASS = {  # every register's vocabulary, folded to the three states every register has
    "FDA (US)":  {"Current": "shortage", "To Be Discontinued": "discontinuance", "Resolved": "resolved"},
    "TGA (AU)":  {"C": "shortage", "A": "shortage", "D": "discontinuance", "R": "resolved"},
}


def _d(s, fmt):
    try:
        return dt.datetime.strptime(str(s or "").strip(), fmt).date()
    except ValueError:
        return None


def _year(s):
    m = re.search(r"(19|20)\d{2}", str(s or ""))
    return int(m.group(0)) if m else None


def rows():
    out = []
    for r in S.fda_rows():
        cls = CLASS["FDA (US)"].get(r.get("status"), r.get("status"))
        a, b = _d(r.get("initial_posting_date"), "%m/%d/%Y"), _d(r.get("update_date"), "%m/%d/%Y")
        when = r.get("update_date") if cls == "resolved" else r.get("initial_posting_date")
        out.append({"register": "FDA (US)", "status": r.get("status"), "cls": cls,
                    "year": _year(when), "dated": str(when or ""),
                    "duration_days": (b - a).days if cls == "resolved" and a and b else "",
                    "bulk_load": cls != "resolved" and r.get("initial_posting_date") in BULK_LOAD})
    for c in S.ansm_table():
        st = c[0]
        cls = ("resolved" if "remise" in st.lower() else
               "discontinuance" if "arr" in st.lower() and "commercialisation" in st.lower() else "shortage")
        dates = [m.group(0) for x in c for m in [FR_DATE.search(x)] if m]
        latest = max(dates, key=lambda d: (d[6:], d[3:5], d[:2])) if dates else ""
        # no column is the START of a shortage; both dates on a resolved row are
        # restoration dates, so a duration is never computable here
        out.append({"register": "ANSM (FR)", "status": st, "cls": cls, "year": _year(latest),
                    "dated": latest, "duration_days": "", "bulk_load": False})
    for r in S.tga_records():
        cls = CLASS["TGA (AU)"].get(r.get("status"), r.get("status"))
        a, b = S.tga_date(r.get("shortage_start")), S.tga_date(r.get("shortage_end"))
        when = r.get("shortage_end") if cls == "resolved" else r.get("shortage_start")
        out.append({"register": "TGA (AU)", "status": r.get("status"), "cls": cls,
                    "year": _year(when), "dated": str(when or ""),
                    "duration_days": (b - a).days if cls == "resolved" and a and b else "",
                    "bulk_load": False})
    return out


def main():
    out = rows()
    S.DATA.mkdir(parents=True, exist_ok=True)
    with open(S.DATA / "memory.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print(f"  {len(out)} rows -> artifacts/data/memory.csv")
    for reg in ("FDA (US)", "ANSM (FR)", "TGA (AU)"):
        rr = [r for r in out if r["register"] == reg]
        by = {}
        for c in ("shortage", "discontinuance", "resolved"):
            ys = [r["year"] for r in rr if r["cls"] == c and r["year"]]
            by[c] = (len(ys), min(ys) if ys else None, max(ys) if ys else None)
        d = sorted(int(r["duration_days"]) for r in rr if r["duration_days"] != "")
        print(f"  {reg:<10} " + "  ".join(f"{c} {n} [{lo}-{hi}]" for c, (n, lo, hi) in by.items())
              + (f"  | durations n={len(d)} median {d[len(d)//2]}d" if d else "  | no durations"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
