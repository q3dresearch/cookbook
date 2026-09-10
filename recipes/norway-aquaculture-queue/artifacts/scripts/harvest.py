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
# The same service also publishes what has already been licensed and whether
# anything is currently in it. Without those, a queue length cannot be read as a
# constraint: capacity already granted and sitting empty is the obvious
# alternative explanation, and it turns out to be the larger number.
BIOMASS = ("Biomasse", 0)

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


def capacity_tonnes(raw) -> float | None:
    """Licensed capacity, tonnes only.

    The field mixes units: TN for tonnes, STK for a count of individual fish, DA
    for an area in dekar, and one row in KG. Summing them produced 87 million
    tonnes against a national output near 1.5 million, because a hatchery
    licensed for 3,000,000 fish was read as 3,000,000 tonnes. Anything not
    explicitly TN is returned as None and counted separately.
    """
    import re
    m = re.match(r"([\d.]+)\s*TN$", str(raw or "").strip())
    if not m:
        return None
    try:
        v = float(m.group(1))
    except ValueError:
        return None
    return v if v > 0 else None


def fetch_biomass(out: Path) -> None:
    svc, layer = BIOMASS
    q = urllib.parse.urlencode({"where": "1=1", "outFields": "*",
                                "returnGeometry": "false", "f": "json"})
    url = f"{BASE.replace('Akvakultursøknader', svc)}/{layer}/query?{q}"
    p = subprocess.run(["curl", "-sS", "-A", UA, "--max-time", "120", url],
                       capture_output=True)
    if p.returncode != 0 or not p.stdout:
        raise RuntimeError(f"biomass: curl rc={p.returncode}")
    recs = [f.get("attributes", {}) for f in json.loads(p.stdout).get("features", [])]
    other = 0
    rows = []
    for r in recs:
        t = capacity_tonnes(r.get("kapasitet_lok"))
        if t is None:
            other += 1
            continue
        rows.append({"site_no": r.get("loknr") or "", "site_name": r.get("navn") or "",
                     "status": r.get("status_lokalitet") or "",
                     "has_fish": r.get("har_fisk") or "",
                     "species": r.get("art") or "",
                     "capacity_tonnes": t,
                     "placement": r.get("plassering") or "",
                     "county": r.get("fylke") or "",
                     "last_report": as_date(r.get("siste_rapport"))})
    f = out / "sites.csv"
    with f.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    tot = sum(r["capacity_tonnes"] for r in rows)
    idle = sum(r["capacity_tonnes"] for r in rows if r["has_fish"] == "Nei")
    print(f"  biomass layer: {len(rows):,} sites in tonnes ({other} in fish-counts, "
          f"area or kg, excluded)", file=sys.stderr)
    print(f"    licensed {tot:,.0f} t, of which {idle:,.0f} t ({idle/tot:.0%}) has no fish",
          file=sys.stderr)


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
    fetch_biomass(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
