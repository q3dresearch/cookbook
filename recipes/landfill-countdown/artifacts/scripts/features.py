#!/usr/bin/env python3
"""Everything measurable about a landfill, in one table, with coverage stated.

    python3 features.py

The register plus two Census tables give a landfill about twenty numbers. This assembles
them once so the charts do not each re-derive their own, and prints how many sites carry
each, because a feature present on a fifth of the register cannot classify it.

Derived rather than copied, and each with a reason:

    countdown        (capacity - stock) / rate        how long it has
    fullness         stock / capacity                 how far through it is
    turnover         rate / capacity                  how fast it consumes itself
    density          stock / (area * depth)           tons per acre-foot, a compaction
                                                      and cover proxy, and the only
                                                      engineering quality in the file
    capture          collected / generated            emissions control
    used share       (collected - flared) / generated harvest rather than disposal
    people_25km      sum of urban-area population     who is downwind. Urban areas are
                     within 25 km                     points here, not polygons, so this
                                                      is a centroid measure and under-
                                                      counts a landfill on the edge of a
                                                      large sprawling area.
    urban_km         distance to the nearest urban    isolation
                     area over 50,000 people
    county_density   county population / land area    the grain permits are argued at

The awkward one is `people_25km`. Census urban areas are published as polygons but the
gazetteer gives a single interior point, so a landfill 10 km from the edge of Chicago and
40 km from its centroid scores zero. Treat it as "near the middle of somewhere" rather
than "near people", and prefer county density where the distinction matters.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lmopdata import DATA, load, num, owner_key, countdown
import geo

CAP, WIP, RATE = ("Landfill Design Capacity (tons)", "Waste in Place (tons)",
                  "Annual Waste Acceptance Rate (tons per year)")
GEN, COL, FLR = "LFG Generated (mmscfd)", "LFG Collected (mmscfd)", "LFG Flared (mmscfd)"
AREA, DEPTH = "Current Landfill Area (acres)", "Current Landfill Depth (feet)"
EDITION_YEAR = 2024


def build(edition="2024"):
    b = load(edition)
    urb = geo.urban()
    big = [(la, lo) for la, lo, p in urb if p >= 50000]
    co = geo.counties()
    out = []
    for k, r in b.items():
        st = str(r.get("Current Landfill Status") or "").strip()
        if st not in ("Open", "Closed"):
            continue
        cap, wip, rate = num(r.get(CAP)), num(r.get(WIP)), num(r.get(RATE))
        gen, col, flr = num(r.get(GEN)), num(r.get(COL)), num(r.get(FLR))
        area, depth = num(r.get(AREA)), num(r.get(DEPTH))
        la, lo = num(r.get("Latitude")), num(r.get("Longitude"))
        opened, closes = num(r.get("Year Landfill Opened")), num(r.get("Landfill Closure Year"))
        d = {
            "key": k, "name": str(r.get("Landfill Name") or "")[:40],
            "state": str(r.get("State") or "").strip(), "open": st == "Open",
            "lat": la, "lon": lo,
            "opened": opened, "age": (EDITION_YEAR - opened) if opened else None,
            "closure_year": closes,
            "since_close": (EDITION_YEAR - closes) if (closes and st == "Closed") else None,
            "cap": cap, "wip": wip, "rate": rate,
            "countdown": countdown(r)[0],
            "fullness": (wip / cap) if (cap and wip and cap > 0) else None,
            "turnover": (rate / cap) if (cap and rate and cap > 0) else None,
            "density": (wip / (area * depth)) if (wip and area and depth and area > 0 and depth > 0) else None,
            "gen": gen, "col": col, "flr": flr,
            "capture": (min(col, gen) / gen) if (gen and col is not None and gen > 0) else None,
            "used": ((min(col, gen) - min(flr or 0, min(col or 0, gen))) / gen)
                    if (gen and col is not None and flr is not None and gen > 0) else None,
            "has_gas": str(r.get("LFG Collection System In Place?") or "").strip() == "Yes",
            "passive": str(r.get("Passive Venting/Flaring?") or "").strip() == "Yes",
            "recirc": str(r.get("Does LF Recirculate Leachate?") or "").strip() == "Yes",
            "rdd": str(r.get("Permitted as RD&D LF?") or "").strip() == "Yes",
            "compost": str(r.get("Composting?") or "").strip() == "Yes",
            "private": str(r.get("Ownership Type") or "").strip() == "Private",
            "owner": owner_key(r.get("Landfill Owner Organization(s)")),
            "ghgrp": num(r.get("GHGRP ID")) is not None,
        }
        if la and lo:
            p = (la, lo)
            d["people_25km"] = sum(pp for xla, xlo, pp in urb if geo.km(p, (xla, xlo)) <= 25)
            d["people_50km"] = sum(pp for xla, xlo, pp in urb if geo.km(p, (xla, xlo)) <= 50)
            d["urban_km"] = min((geo.km(p, q) for q in big), default=None)
        else:
            d["people_25km"] = d["people_50km"] = d["urban_km"] = None
        ck = geo.county_key(d["state"], r.get("County"))
        if ck in co:
            pop, sqmi = co[ck]
            d["county_pop"] = pop
            d["county_density"] = (pop / sqmi) if sqmi > 0 else None
        else:
            d["county_pop"] = d["county_density"] = None
        out.append(d)
    return out


def main():
    rows = build()
    n = len(rows)
    print(f"{n:,} landfills (open or closed) in the 2024 edition\n")
    fields = ["age", "countdown", "fullness", "turnover", "density", "capture", "used",
              "people_25km", "urban_km", "county_density", "since_close"]
    print(f"  {'feature':<18}{'coverage':>10}{'p10':>12}{'median':>12}{'p90':>12}")
    for f in fields:
        v = sorted(x for x in (r.get(f) for r in rows) if x is not None)
        if not v:
            continue
        print(f"  {f:<18}{len(v)/n:>10.0%}{v[len(v)//10]:>12,.2f}{v[len(v)//2]:>12,.2f}"
              f"{v[9*len(v)//10]:>12,.2f}")
    for f in ["has_gas", "passive", "recirc", "rdd", "compost", "private", "ghgrp"]:
        print(f"  {f:<18}{sum(bool(r[f]) for r in rows)/n:>10.0%}  (flag)")
    path = os.path.join(DATA, "features.json")
    json.dump(rows, open(path, "w"), indent=0)
    print(f"\n  wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
