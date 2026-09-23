#!/usr/bin/env python3
"""SEDS folded to the electrification ratio, by state and year. Cached beside the data.

    python3 seds.py

**The ratio has two defensible bases and they differ by about three times.**

- *Site*: electricity as delivered, against total end-use energy. `ESTXB / TNTCB`.
- *Primary*: the same, with the generation and transmission losses that were burned to
  deliver it added to both sides. `(ESTXB + LOTXB) / (TNTCB + LOTXB)`.

A kilowatt-hour arrives at a meter having cost roughly three kilowatt-hours of fuel, so the
site basis flatters electricity and the primary basis flatters everything else. Neither is
wrong. Quoting one without saying which is.

**The denominator contains transport fuel**, which is most of the primary energy in a US
state and barely electrified until recently. So the ratio can rise because electricity grew
*or* because petrol demand fell, and those are different facts. `ESVHP` -- electricity for
electric vehicles, and only from 2018 -- is the one series that isolates the first.
"""
import collections, json, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
SRC = os.path.join(DATA, "eia-seds.zip")
CACHE = os.path.join(DATA, "seds-electrification.json")
# electricity at the meter, total end use, system losses, and EV charging
CODES = ("ESTXB", "TNTCB", "LOTXB", "ESVHP", "ESTXP", "TETCB", "ESTPP", "TPOPP")
SKIP = {"US"}          # the national roll-up is kept separately, not mixed with states


def build():
    if not os.path.exists(SRC):
        raise SystemExit("  eia-seds.zip missing - run eia.py SEDS")
    pat = re.compile(r"^SEDS\.(%s)\.([A-Z]{2})\.A$" % "|".join(CODES))
    out = collections.defaultdict(dict)
    z = zipfile.ZipFile(SRC)
    with z.open("SEDS.txt") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            m = pat.match(d.get("series_id", ""))
            if not m:
                continue
            code, st = m.group(1), m.group(2)
            series = {str(y): v for y, v in (d.get("data") or []) if v is not None}
            out[st][code] = series
    return {"states": out, "codes": list(CODES)}


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    print("  folding SEDS.txt ...", flush=True)
    d = build()
    tmp = CACHE + ".tmp"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return d


def ratios(d, st, year):
    """Both bases for one state-year, or None where a series is missing."""
    s = d["states"].get(st, {})
    e = s.get("ESTXB", {}).get(year)
    t = s.get("TNTCB", {}).get(year)
    lo = s.get("LOTXB", {}).get(year)
    if e is None or t is None or not t:
        return None
    site = e / t
    prim = ((e + lo) / (t + lo)) if lo is not None and (t + lo) else None
    return {"site": site, "primary": prim, "elec_btu": e, "total_btu": t, "loss_btu": lo}


if __name__ == "__main__":
    d = load()
    sts = sorted(k for k in d["states"] if k not in SKIP and len(k) == 2)
    print(f"  {len(sts)} states plus {sorted(set(d['states']) - set(sts))}")
    for y in ("1960", "1980", "2000", "2024"):
        vals = [(ratios(d, s, y), s) for s in sts]
        vals = [(r, s) for r, s in vals if r]
        if not vals:
            continue
        site = sorted(r["site"] for r, _ in vals)
        prim = [r["primary"] for r, _ in vals if r["primary"] is not None]
        hi = max(vals, key=lambda v: v[0]["site"])
        lo = min(vals, key=lambda v: v[0]["site"])
        print(f"\n  {y}: {len(vals)} states")
        print(f"    site basis    median {site[len(site)//2]:.1%}  "
              f"range {site[0]:.1%} to {site[-1]:.1%}   "
              f"({lo[1]} lowest, {hi[1]} highest)")
        if prim:
            prim.sort()
            print(f"    primary basis median {prim[len(prim)//2]:.1%}  "
                  f"range {prim[0]:.1%} to {prim[-1]:.1%}")
    ev = [(s, d["states"][s].get("ESVHP", {})) for s in sts]
    ev = [(s, v) for s, v in ev if v.get("2024")]
    ev.sort(key=lambda kv: -kv[1]["2024"])
    print(f"\n  EV charging (ESVHP) reported by {len(ev)} states in 2024; top 5 GWh:")
    for s, v in ev[:5]:
        g18 = v.get("2018")
        print(f"    {s}  2024 {v['2024']:>10,.0f}" +
              (f"   2018 {g18:>9,.0f}   x{v['2024']/g18:>5.1f}" if g18 else ""))
