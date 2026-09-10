#!/usr/bin/env python3
"""Fetch the CAISO and MISO interconnection queues into one table.

    python harvest.py <outdir>

FERC requires US transmission providers to publish their interconnection queues,
so the conceptual shape is identical everywhere and only the delivery format
differs. CAISO ships an .xlsx with three sheets — active, completed, withdrawn —
and MISO a JSON array with an `applicationStatus` field carrying the same three
states under other names. Both are normalised here to one row per project.

Reads .xlsx with `zipfile` and `xml.etree` rather than a spreadsheet library,
because a recipe that needs pip is a recipe most readers will not run. An xlsx is
a zip of XML; the only fiddly part is that text cells store an index into a shared
string table instead of the string.

**Why curl and not urllib.** Both hosts stall indefinitely against Python's
urllib — no error, no timeout, just silence — while curl answers in a second.
That silence previously got read as "the source is gone". If you swap the fetch
for a Python client, prove it returns bytes before believing any number that
comes out downstream.
"""
from __future__ import annotations

import argparse
import csv
import json
import datetime as dt
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

UA = "q3dresearch-cookbook/1.0 (+https://github.com/q3dresearch/cookbook)"
CAISO = "https://www.caiso.com/PublishedDocuments/PublicQueueReport.xlsx"
MISO = "https://www.misoenergy.org/api/giqueue/getprojects"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}

# One vocabulary for both operators. CAISO puts state in the sheet name; MISO
# puts it in a field. "active" means no outcome yet and is excluded from every
# survival rate — counting it as either built or dead would be a guess.
STATUS = {"completed": "built", "withdrawn": "withdrawn", "grid": "active",
          "done": "built", "active": "active",
          "pending revision approval": "active", "pending transfer": "active"}


def as_date(v: str) -> str:
    """Normalise to ISO. CAISO stores dates as Excel serials, MISO as ISO text.

    An .xlsx date cell holds a number of days since 1899-12-30, so '37943.33' is
    2003-11-06 and not a year, an id, or a quantity. Left raw it silently poisons
    anything time-based downstream.
    """
    v = (v or "").strip()
    if not v:
        return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", v):
        return v[:10]
    try:
        n = float(v)
    except ValueError:
        return v[:10]
    if not 1 < n < 80000:                # outside any plausible spreadsheet date
        return ""
    return (dt.date(1899, 12, 30) + dt.timedelta(days=int(n))).isoformat()


def fetch(url: str, out: Path) -> Path:
    p = subprocess.run(["curl", "-sSL", "-A", UA, "--max-time", "180", "-o", str(out), url],
                       capture_output=True)
    if p.returncode != 0 or not out.exists() or out.stat().st_size == 0:
        raise RuntimeError(f"fetch failed: {url} rc={p.returncode} "
                           f"{p.stderr[:200].decode('utf-8', 'replace')}")
    return out


def sheet_rows(z: zipfile.ZipFile, target: str, shared: list[str]):
    root = ET.fromstring(z.read(target))
    for row in root.find("m:sheetData", NS):
        cells = {}
        for c in row:
            ref = c.get("r") or ""
            col = re.match(r"[A-Z]+", ref)
            v = c.find("m:v", NS)
            if col is None or v is None or v.text is None:
                continue
            val = shared[int(v.text)] if c.get("t") == "s" else v.text
            cells[col.group()] = val
        if cells:
            yield cells


def read_caiso(path: Path):
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        sroot = ET.fromstring(z.read("xl/sharedStrings.xml"))
        shared = ["".join(t.text or "" for t in si.iter(
            "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"))
            for si in sroot]
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = {r.get("Id"): r.get("Target")
            for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    for sh in wb.find("m:sheets", NS):
        name = sh.get("name") or ""
        tgt = rels[sh.get(f"{{{NS['r']}}}id")].lstrip("/")
        if not tgt.startswith("xl/"):
            tgt = "xl/" + tgt
        key = next((k for k in STATUS if name.lower().startswith(k)), None)
        status = STATUS.get(key, "active")
        rows = list(sheet_rows(z, tgt, shared))
        if not rows:
            continue
        # The header is not the first row. CAISO puts a report date, a title and a
        # merged group header above it, so row 0 is "Report Run Date: ..." and
        # taking it as the header silently matched no columns and yielded zero
        # projects. Find the row that actually names the fields.
        hdr_i = next((i for i, r in enumerate(rows[:12])
                      if any("queue position" in (v or "").lower() for v in r.values())
                      and any("project name" in (v or "").lower() for v in r.values())), None)
        if hdr_i is None:
            print(f"    {name}: no header row found — skipped", file=sys.stderr)
            continue
        header = {k: (v or "").strip() for k, v in rows[hdr_i].items()}
        idx = {v.lower().replace("\n", " "): k for k, v in header.items() if v}
        rows = rows[hdr_i + 1:]

        def g(cells, *names):
            for n in names:
                for lbl, col in idx.items():
                    if n in lbl:
                        return cells.get(col, "")
            return ""

        for cells in rows:
            pid = g(cells, "queue position", "project name")
            if not pid:
                continue
            yield {
                "iso": "CAISO", "project_id": pid, "status": status,
                "technology": g(cells, "type-1", "technology"),
                # Fuel is a separate column and does not follow from the type. A
                # steam turbine may be gas, geothermal, solar thermal or biomass,
                # so folding "Steam Turbine" into a gas family without checking
                # this would invent a category.
                "fuel": g(cells, "fuel-1", "fuel"),
                "mw": g(cells, "net mws to grid", "mw"),
                "county": g(cells, "county"), "state": g(cells, "state"),
                "queue_date": as_date(g(cells, "queue date", "interconnection request")),
                "withdrawn_date": as_date(g(cells, "withdrawn date")),
                # How far through the study process a project got. CAISO fills
                # these in order, so the last non-empty one is where it stopped —
                # which is the difference between a project nobody spent money on
                # and one that died holding a signed agreement.
                "feasibility": g(cells, "feasibility study"),
                "sys_impact": g(cells, "system impact study"),
                "facilities": g(cells, "facilities study"),
                "ia_status": g(cells, "interconnection agreement"),
                # When a built project actually left the queue. Needed to censor
                # it correctly in a survival curve: it exited alive, and treating
                # it as still-at-risk until today inflates survival at long
                # durations, which is exactly where the interesting shape is.
                "online_date": as_date(g(cells, "actual on-line date")),
            }


def read_miso(path: Path):
    data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    rows = data if isinstance(data, list) else next(
        (v for v in data.values() if isinstance(v, list)), [])
    for r in rows:
        raw = (r.get("applicationStatus") or "").strip().lower()
        yield {
            "iso": "MISO", "project_id": str(r.get("projectNumber") or r.get("id") or ""),
            "status": STATUS.get(raw, "active"),
            "technology": r.get("fuelType") or "",
            "fuel": r.get("fuelType") or "",
            "mw": r.get("summerNetMW") or "",
            "county": r.get("county") or "", "state": r.get("state") or "",
            "queue_date": as_date(r.get("queueDate") or ""),
            "withdrawn_date": "",
            "online_date": "",
            "feasibility": "", "sys_impact": "", "facilities": "", "ia_status": "",
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    a = ap.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    print("  CAISO ...", file=sys.stderr, flush=True)
    rows += list(read_caiso(fetch(CAISO, out / "caiso.xlsx")))
    print("  MISO ...", file=sys.stderr, flush=True)
    rows += list(read_miso(fetch(MISO, out / "miso.json")))

    cols = ["iso", "project_id", "status", "technology", "fuel", "mw", "county", "state",
            "queue_date", "withdrawn_date", "online_date",
            "feasibility", "sys_impact", "facilities", "ia_status"]
    p = out / "queue.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    import collections
    per = collections.Counter((r["iso"], r["status"]) for r in rows)
    print(f"\n  {len(rows):,} projects -> {p}", file=sys.stderr)
    for iso in ("CAISO", "MISO"):
        b, wd, ac = (per[(iso, s)] for s in ("built", "withdrawn", "active"))
        res = b + wd
        print(f"    {iso}: built {b:,}  withdrawn {wd:,}  active {ac:,}   "
              f"survival {b/res if res else 0:.1%}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
