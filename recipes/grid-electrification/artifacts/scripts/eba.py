#!/usr/bin/env python3
"""EBA folded to annual demand and fuel mix per balancing authority. Cached.

    python3 eba.py

**Why the balancing authority and not the state.** At state resolution compute load is
invisible: facility counts do not predict electricity growth at all (r = +0.03), and
California holds the largest concentration in the country while its consumption fell 5.9%.
Loudoun County is a rounding error inside Virginia and Virginia is one inside the nation.
A balancing authority is finer, and some of them are nearly coextensive with a hub.

**The file is 4.35 GB of hourly series**, one JSON object per line, each carrying every
hour from 2019-01-01 to the present. It is streamed and folded to annual totals; nothing
is held in memory but the accumulator.

**Hours are UTC.** A "year" here is a UTC year, which is the right unit for an annual
total and the wrong one for anything about local peak hours. Nothing in this module
touches time of day; a marginal-mix question needs the hourly series, not this fold.
"""
import collections, json, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
SRC = os.path.join(DATA, "eia-eba.zip")
CACHE = os.path.join(DATA, "eba-annual.json")
# EBA.{BA}-ALL.D.H  = demand;  EBA.{BA}-ALL.NG.{FUEL}.H = net generation by fuel
# Fuel codes are NOT fixed width: NG is two characters, COL/WAT/SUN/WND/NUC/OIL/OTH/UNK
# are three. An earlier {3} here silently dropped natural gas from every balancing
# authority -- the largest fossil fuel in the country -- and inflated every carbon-free
# share. The tell was ERCOT reporting 288 TWh of generation against 488 TWh of demand.
# The series ids do NOT share one shape. Enumerated across all 3,074:
#   EBA.{BA}-ALL.D.H            demand            EBA.{BA}-ALL.DF.H    demand FORECAST
#   EBA.{BA}-ALL.NG.{FUEL}.H    generation        EBA.{BA}-ALL.TI.H    total interchange
#   EBA.{BA}.CO2.CON.H          CO2 of power CONSUMED, imports included -- note: no "-ALL"
#   EBA.{BA}.CO2.EXPR.H         CO2 leaving in exports
#   EBA.{BA}.CO2.EM.{FUEL}.H    CO2 by fuel burned
# Fuel codes are two OR three characters: NG is two. An earlier {3} silently dropped
# natural gas from every balancing authority and inflated every carbon-free share; the
# tell was ERCOT reporting 288 TWh of generation against 488 TWh of demand.
# Every series has an .HL twin in LOCAL time. Taking both would double everything, so
# only .H (UTC) is read.
PAT = re.compile(
    r"^EBA\.([A-Z0-9]+)-ALL\.(D|DF|TI|NG\.([A-Z]{2,3}))\.H$")
CO2 = re.compile(
    r"^EBA\.([A-Z0-9]+)\.CO2\.(CON|EXPR|EM\.([A-Z]{2,3}))\.H$")
CLEAN = {"WAT", "SUN", "WND", "NUC", "GEO"}
FOSSIL = {"COL", "NG", "OIL"}


def build():
    if not os.path.exists(SRC):
        raise SystemExit("  eia-eba.zip missing - run eia.py EBA")
    ba = collections.defaultdict(lambda: collections.defaultdict(
        lambda: collections.defaultdict(float)))
    seen = 0
    z = zipfile.ZipFile(SRC)
    with z.open("EBA.txt") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            sid = d.get("series_id", "")
            m = PAT.match(sid)
            c2 = None if m else CO2.match(sid)
            if not m and not c2:
                continue
            if m:
                code, kind, fuel = m.group(1), m.group(2), m.group(3)
                key = kind if kind in ("D", "DF", "TI") else "NG." + fuel
            else:
                code, key = c2.group(1), "CO2." + c2.group(2)
            acc = ba[code][key]
            for stamp, v in (d.get("data") or []):
                if v is None:
                    continue
                try:
                    acc[stamp[:4]] += float(v)
                except (TypeError, ValueError):
                    continue
            seen += 1
            if seen % 400 == 0:
                print(f"    {seen:,} series folded, {len(ba)} balancing authorities",
                      flush=True)
    out = {c: {k: dict(v) for k, v in d.items()} for c, d in ba.items()}
    return {"ba": out, "clean": sorted(CLEAN), "fossil": sorted(FOSSIL),
            "series": seen}


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    print("  folding EBA.txt (4.35 GB, streamed) ...", flush=True)
    d = build()
    tmp = CACHE + ".tmp"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return d


def year(d, code, key, y):
    return d["ba"].get(code, {}).get(key, {}).get(str(y))


if __name__ == "__main__":
    d = load()
    ba = d["ba"]
    print(f"\n  {len(ba)} balancing authorities, {d['series']:,} series folded")
    rows = []
    for c, v in ba.items():
        a, b = v.get("D", {}).get("2019"), v.get("D", {}).get("2025")
        if not a or not b or a < 1e6:
            continue
        gen = {k[3:]: s.get("2025", 0.0) for k, s in v.items() if k.startswith("NG.")}
        tot = sum(gen.values())
        clean = sum(gen.get(k, 0.0) for k in CLEAN)
        # a generation total far below demand means a fuel is missing, not that the grid
        # imports that much: flag it rather than publish a share computed on a hole
        rows.append({"ba": c, "twh": b / 1e6, "g": b / a - 1,
                     "clean": clean / tot if tot else None,
                     "cover": tot / b if b else None})
    rows.sort(key=lambda r: -r["g"])
    print(f"  {len(rows)} with demand in both 2019 and 2025\n")
    print(f"  {'BA':<8}{'TWh 2025':>10}{'2019-25':>10}{'carbon-free':>13}{'gen/demand':>12}")
    for r in rows[:10] + [None] + rows[-5:]:
        if r is None:
            print("  " + "." * 53); continue
        cs = f"{r['clean']:.0%}" if r["clean"] is not None else "--"
        cv = f"{r['cover']:.0%}" if r["cover"] is not None else "--"
        print(f"  {r['ba']:<8}{r['twh']:>10,.1f}{r['g']:>10.1%}{cs:>13}{cv:>12}")
