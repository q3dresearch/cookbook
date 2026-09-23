#!/usr/bin/env python3
"""Three hourly measures that an annual total cannot give you.

    python3 matched.py

One pass over the 691 MB EBA archive. Three separate questions all need the hour rather
than the year, and a pass costs a minute, so they share one.

**1. Carbon intensity over matched hours.** Demand runs hourly from 2019. Consumption based
CO2 (`CO2.CON`) starts 2024-07-15 and covers about **87.5% of 2025's hours**. Dividing an
annual CO2 sum by an annual demand sum therefore understates every intensity, because the
numerator is missing hours the denominator has. Measured, the understatement runs **10.8%
to 14.6%** -- it is not constant, so it moves the ranking and not only the levels. Scaling
by the coverage ratio would assume the missing hours are average, and an outage in a
reporting feed is not a random sample of hours. Both series are kept hourly and summed over
their intersection.

**2. Load shape.** A data centre is a flat 24/7 load. A grid absorbing compute should see
its overnight trough rise faster than its afternoon peak, so the ratio between them should
climb. This is the successor to the facility-count proxy, which failed its falsifier
(r = +0.03 against state electricity growth 2015-2024).

Load shape reads the **`.HL` local-time twin**, not `.H`. In UTC a US calendar day begins
around 7pm local, which splits every night across two days and makes a daily minimum
meaningless. Everything else reads `.H`.

**3. Forecast against outcome.** `DF` is what the balancing authority expected; `D` is what
happened. Matched hours again, for the same reason as (1).

The statistic that matters is not the average error. It is the **hourly ratio DF/D**, kept as
a median and an inter-quartile range, because those two measure different things and this
feed separates on both. The median is SCOPE: Duke Energy Florida's forecast is 0.766 of its
reported demand in every hour of 2025, 100.0% of them, with an IQR of 0.036 -- it forecasts a
different quantity, and forecasts it precisely. The IQR is SKILL: Southern runs a median of
0.991 at an IQR of 0.010, and SPA a median of 1.679 at an IQR of 1.339. Averaging the signed
error mixes the two together and reports a single number that is neither.

**`CO2.EM.{fuel}` is excluded, not caveated.** ERCOT's coal series carries 4,436 hourly
points in an 11,000-hour window, which is why an own-generation intensity built from it came
out roughly twenty times too low.
"""
import collections, json, os, re, statistics, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
SRC = os.path.join(DATA, "eia-eba.zip")
CACHE = os.path.join(DATA, "eba-hourly.json")

D_UTC = re.compile(r"^EBA\.([A-Z0-9]+)-ALL\.D\.H$")
F_UTC = re.compile(r"^EBA\.([A-Z0-9]+)-ALL\.DF\.H$")
D_LOC = re.compile(r"^EBA\.([A-Z0-9]+)-ALL\.D\.HL$")
C_UTC = re.compile(r"^EBA\.([A-Z0-9]+)\.CO2\.CON\.H$")

MATCH_YEAR = "2025"                 # the only near-full year CO2.CON covers
SHAPE_YEARS = ("2019", "2020", "2021", "2022", "2023", "2024", "2025")
MIN_HOURS = 2000                    # below this a BA is a reporting stub, not a grid
MIN_DAYS = 300                      # a partial year cannot carry a load-shape number


def build():
    if not os.path.exists(SRC):
        raise SystemExit("  eia-eba.zip missing - run eia.py EBA")
    dem = collections.defaultdict(dict)          # BA -> {stamp: MW}    2025 UTC
    fc = collections.defaultdict(dict)           # BA -> {stamp: MW}    2025 UTC
    co2 = collections.defaultdict(dict)          # BA -> {stamp: tCO2}  2025 UTC
    day = collections.defaultdict(dict)          # BA -> {YYYYMMDD: [min, max]}  local
    n = 0
    with zipfile.ZipFile(SRC).open("EBA.txt") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            sid = d.get("series_id", "")
            hit = None
            for pat, tgt in ((D_UTC, dem), (F_UTC, fc), (C_UTC, co2)):
                m = pat.match(sid)
                if m:
                    hit = tgt[m.group(1)]
                    break
            if hit is not None:
                n += 1
                for stamp, v in (d.get("data") or []):
                    if v is None or stamp[:4] != MATCH_YEAR:
                        continue
                    try:
                        hit[stamp] = float(v)
                    except (TypeError, ValueError):
                        pass
                continue
            m = D_LOC.match(sid)
            if not m:
                continue
            n += 1
            t = day[m.group(1)]
            for stamp, v in (d.get("data") or []):
                if v is None or stamp[:4] not in SHAPE_YEARS:
                    continue
                try:
                    x = float(v)
                except (TypeError, ValueError):
                    continue
                if x <= 0:              # a zero or negative hour is a reporting gap
                    continue
                k = stamp[:8]
                c = t.get(k)
                if c is None:
                    t[k] = [x, x]
                else:
                    if x < c[0]:
                        c[0] = x
                    if x > c[1]:
                        c[1] = x

    out = {"year": MATCH_YEAR, "series_read": n, "ba": {}, "shape": {}}
    for ba in sorted(set(dem) & set(co2)):
        D, C = dem[ba], co2[ba]
        both = sorted(set(D) & set(C))
        if len(both) < MIN_HOURS:
            continue
        md = sum(D[h] for h in both)
        ad = sum(D.values())
        rec = {"hours_both": len(both), "hours_demand": len(D), "hours_co2": len(C),
               "mwh_matched": md, "tco2_matched": sum(C[h] for h in both),
               "intensity": sum(C[h] for h in both) / md * 1000 if md else None,
               "naive_intensity": sum(C.values()) / ad * 1000 if ad else None}
        F = fc.get(ba) or {}
        fh = sorted(set(D) & set(F))
        if len(fh) >= MIN_HOURS:
            err = [(F[h] - D[h]) / D[h] for h in fh if D[h] > 0]
            ratio = sorted(F[h] / D[h] for h in fh if D[h] > 0)
            if err:
                rec["fc_hours"] = len(err)
                rec["fc_bias"] = statistics.median(err)
                rec["fc_miss"] = statistics.median(abs(e) for e in err)
                q = lambda p: ratio[min(len(ratio) - 1, int(len(ratio) * p))]
                rec["fc_ratio"] = statistics.median(ratio)     # scope: what it forecasts
                rec["fc_iqr"] = q(.75) - q(.25)                # skill: how tightly
                rec["fc_p5"], rec["fc_p95"] = q(.05), q(.95)
                rec["fc_under"] = sum(1 for x in ratio if x < 1) / len(ratio)
        out["ba"][ba] = rec

    for ba, days in sorted(day.items()):
        by = collections.defaultdict(list)
        for k, (lo, hi) in days.items():
            by[k[:4]].append((lo, hi))
        yrs = {}
        for y, v in sorted(by.items()):
            if len(v) < MIN_DAYS:
                continue
            lo = statistics.median(a for a, _ in v)
            hi = statistics.median(b for _, b in v)
            yrs[y] = {"days": len(v), "trough": lo, "peak": hi,
                      "ratio": lo / hi if hi else None}
        if len(yrs) >= 2:
            out["shape"][ba] = yrs
    return out


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    print("  folding hourly demand, forecast, CO2 and local load shape ...", flush=True)
    d = build()
    tmp = CACHE + ".tmp"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return d


def main():
    d = load()
    rows = sorted(d["ba"].items(), key=lambda kv: kv[1]["intensity"])
    print(f"\n  CARBON over matched hours, {d['year']}  "
          f"({len(rows)} balancing authorities, {d['series_read']} series read)")
    print(f"  {'BA':<7}{'hours both':>12}{'coverage':>10}{'matched kg/MWh':>16}"
          f"{'naive':>9}{'naive is':>11}")
    for ba, v in rows[:5] + [("", None)] + rows[-5:]:
        if v is None:
            print("  " + "." * 65)
            continue
        print(f"  {ba:<7}{v['hours_both']:>12,}"
              f"{v['hours_both']/v['hours_demand']:>10.1%}{v['intensity']:>16,.0f}"
              f"{v['naive_intensity']:>9,.0f}"
              f"{v['naive_intensity']/v['intensity']-1:>11.1%}")
    errs = sorted(v["naive_intensity"] / v["intensity"] - 1 for _, v in rows)
    print(f"  an annual ratio understates intensity by {-errs[-1]:.1%} to {-errs[0]:.1%}, "
          f"so it moves the ranking too")

    sh = d["shape"]
    moves = []
    for ba, yrs in sh.items():
        ks = sorted(yrs)
        a, b = yrs[ks[0]], yrs[ks[-1]]
        if a["ratio"] and b["ratio"]:
            moves.append((b["ratio"] - a["ratio"], ba, ks[0], ks[-1], a, b))
    moves.sort(reverse=True)
    print(f"\n  LOAD SHAPE, local time: median daily trough / median daily peak")
    print(f"  {len(moves)} balancing authorities with two or more full years")
    print(f"  {'BA':<7}{'span':>12}{'then':>9}{'now':>8}{'change':>9}{'peak GW':>10}")
    for dv, ba, k0, k1, a, b in moves[:8] + [(None, "", "", "", None, None)] + moves[-5:]:
        if a is None:
            print("  " + "." * 55)
            continue
        print(f"  {ba:<7}{k0 + '-' + k1:>12}{a['ratio']:>9.3f}{b['ratio']:>8.3f}"
              f"{dv:>+9.3f}{b['peak']/1000:>10,.1f}")
    big = [m for m in moves if m[5]["peak"] >= 5000]
    if big:
        print(f"  among the {len(big)} grids peaking above 5 GW, the median change is "
              f"{statistics.median(m[0] for m in big):+.3f}")

    fc = sorted((v["fc_bias"], ba) for ba, v in d["ba"].items()
                if v.get("fc_bias") is not None)
    if fc:
        print(f"\n  FORECAST minus ACTUAL over matched hours, median share of actual")
        print(f"  {len(fc)} balancing authorities")
        for bias, ba in fc[:4] + [(None, "")] + fc[-4:]:
            if bias is None:
                print("  " + "." * 42)
                continue
            v = d["ba"][ba]
            print(f"  {ba:<7}{bias:>+9.2%}   ratio {v['fc_ratio']:.3f}  "
                  f"IQR {v['fc_iqr']:.3f}  under {v['fc_under']:.0%}")
        print(f"  median bias across all {len(fc)}: "
              f"{statistics.median(b for b, _ in fc):+.2%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
