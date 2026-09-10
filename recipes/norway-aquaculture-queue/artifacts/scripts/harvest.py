#!/usr/bin/env python3
"""Fetch Norway's aquaculture licence queue into one table.

    python harvest.py <outdir>

Fiskeridirektoratet publishes the whole pipeline as two layers of one public
ArcGIS MapServer: applications still being processed, and applications already
decided. No key, no account, and both layers sit under the service's 2,000-feature
cap, so there is no pagination to get wrong.

The two layers are fetched separately and stacked, because the interesting
comparison is between them. A decided-only view answers "what share was granted"
and cannot answer "what share of what was asked for has been answered", and the
pending pile is older than the typical decision — which means the slow cases are
still in it and any rate computed on decisions alone is measured on the fast half.

Dates arrive as epoch MILLISECONDS. Left raw, `1676547547000` is not a date, a
year or a quantity, and every duration computed from it is nonsense.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import subprocess
import sys
import urllib.parse
from pathlib import Path

UA = "q3dresearch-cookbook/1.0 (+https://github.com/q3dresearch/cookbook)"
BASE = ("https://gis.fiskeridir.no/server/rest/services/Yggdrasil/"
        "Akvakultursøknader/MapServer")
LAYERS = {0: "pending", 4: "decided"}

COLS = ["layer", "application_no", "applicant", "org_number", "application_type",
        "status", "result", "submitted", "decided", "days_to_decide",
        "biomass_tonnes", "site_name", "municipality", "county", "species",
        "production_area"]


def fetch(layer: int) -> list[dict]:
    """One layer, all fields. curl because the host answers it and it is one call."""
    q = urllib.parse.urlencode({"where": "1=1", "outFields": "*",
                                "returnGeometry": "false", "f": "json"})
    url = f"{BASE}/{layer}/query?{q}"
    p = subprocess.run(["curl", "-sS", "-A", UA, "--max-time", "120", url],
                       capture_output=True)
    if p.returncode != 0 or not p.stdout:
        raise RuntimeError(f"layer {layer}: curl rc={p.returncode} "
                           f"{p.stderr[:200].decode('utf-8', 'replace')}")
    d = json.loads(p.stdout)
    if "error" in d:
        raise RuntimeError(f"layer {layer}: {d['error']}")
    return [f.get("attributes", {}) for f in d.get("features", [])]


def as_date(ms) -> str:
    """Epoch milliseconds to ISO. Anything else is dropped rather than guessed."""
    if ms in (None, "", 0):
        return ""
    try:
        v = float(ms)
    except (TypeError, ValueError):
        return ""
    if not 0 < v < 4e12:                    # outside ~1970-2096
        return ""
    return (dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds=v)).date().isoformat()


def num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return ""
    return "" if f <= 0 else f


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    a = ap.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for layer, label in LAYERS.items():
        recs = fetch(layer)
        print(f"  layer {layer} ({label}): {len(recs):,} records", file=sys.stderr, flush=True)
        for r in recs:
            sub = as_date(r.get("submittedat"))
            dec = as_date(r.get("evaluationfinishedat"))
            days = ""
            if sub and dec:
                d = (dt.date.fromisoformat(dec) - dt.date.fromisoformat(sub)).days
                days = d if 0 <= d < 5000 else ""
            rows.append({
                "layer": label,
                "application_no": r.get("applicationno") or "",
                "applicant": r.get("applicantorganisationname") or "",
                "org_number": r.get("applicantorganisationnumber") or "",
                "application_type": (r.get("soeknadstype") or "").strip(),
                "status": r.get("status_application") or "",
                "result": (r.get("evaluation_result") or "").strip(),
                "submitted": sub, "decided": dec, "days_to_decide": days,
                "biomass_tonnes": num(r.get("desiredbiomass_value")),
                "site_name": r.get("sitename") or "",
                "municipality": r.get("municipalityname") or "",
                "county": r.get("countymunicipalityname") or "",
                "species": (r.get("art_popularname") or "").strip(),
                "production_area": (r.get("sitedata_prodareaname") or "").strip(),
            })

    p = out / "applications.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    import collections
    per = collections.Counter((r["layer"], r["result"] or "-") for r in rows)
    print(f"\n  {len(rows):,} applications -> {p}", file=sys.stderr)
    for (layer, res), n in sorted(per.items()):
        print(f"    {layer:<9}{res:<12}{n:>6,}", file=sys.stderr)
    dated = sum(1 for r in rows if r["submitted"])
    print(f"  {dated:,} carry a submission date ({dated/len(rows):.0%})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
