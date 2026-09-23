#!/usr/bin/env python3
"""Where forecast skill is falling, and whether rooftop solar explains it.

    python3 geo.py

Figure 5 found California's day-ahead forecast skill falling from +0.69 in 2021 to -0.18 in
2025, four consecutive years, with its scope ratio sliding in step. The obvious next question
is whether that is a California story or a **geography** story, and the decliners are
suggestive on their own: CISO, PacifiCorp West, Arizona Public Service and Nevada Power are
California, Oregon, Arizona and Nevada.

**The candidate mechanism is behind-the-meter solar.** Rooftop generation never passes through
a meter the grid operator reads. It appears as demand that did not happen, in the middle of
the day, so a balancing authority's recorded demand becomes a *net* quantity that is
increasingly weather-dependent and increasingly unlike whatever the operator's forecast was
built to predict.

**An earlier note in this recipe said that variable was invisible in this dataset. That was
wrong**, and worth correcting rather than quietly fixing: it is invisible in **EBA**, which is
what figures 3 and 7 read. EIA publishes an estimate of it in **ELEC**, as
`ELEC.GEN.DPV-{ST}-{sector}.Q`, quarterly by state from 2016.

**It is an estimate, and that bounds the claim.** EIA models small-scale PV from capacity
filings and assumed yields; nobody meters it. So this cannot be read as a measurement, and a
strong relationship would be partly a relationship with EIA's own model. It is stated as a
modelled covariate wherever it appears.

**Two geographies, because a balancing authority is not a place.** The 41 single-state
authorities get their state's rooftop penetration. The multi-state RTOs -- PJM, MISO, SPP,
Bonneville, PacifiCorp East, WACM -- get nothing and are reported separately, because
assigning them one state would be mostly wrong.
"""
import collections, json, math, os, re, statistics, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
sys.path.insert(0, HERE)
import predict, shape, skill as SK                                        # noqa: E402

SRC = os.path.join(DATA, "eia-elec.zip")
CACHE = os.path.join(DATA, "geo.json")
DPV = re.compile(r"^ELEC\.GEN\.DPV-([A-Z]{2})-(\d+)\.Q$")
SUN = re.compile(r"^ELEC\.GEN\.(SUN|SPV|STH)-([A-Z]{2})-(\d+)\.Q$")
SALES = re.compile(r"^ELEC\.SALES\.([A-Z]{2})-ALL\.Q$")
A, B = "2019", "2025"

# Census divisions, so "geography" is a published grouping rather than one I invented.
DIVISION = {
    "WA": "Pacific", "OR": "Pacific", "CA": "Pacific", "AK": "Pacific", "HI": "Pacific",
    "MT": "Mountain", "ID": "Mountain", "WY": "Mountain", "CO": "Mountain",
    "NM": "Mountain", "AZ": "Mountain", "UT": "Mountain", "NV": "Mountain",
    "ND": "West North Central", "SD": "West North Central", "NE": "West North Central",
    "KS": "West North Central", "MN": "West North Central", "IA": "West North Central",
    "MO": "West North Central",
    "WI": "East North Central", "IL": "East North Central", "IN": "East North Central",
    "MI": "East North Central", "OH": "East North Central",
    "NY": "Middle Atlantic", "PA": "Middle Atlantic", "NJ": "Middle Atlantic",
    "CT": "New England", "ME": "New England", "MA": "New England", "NH": "New England",
    "RI": "New England", "VT": "New England",
    "DE": "South Atlantic", "MD": "South Atlantic", "DC": "South Atlantic",
    "VA": "South Atlantic", "WV": "South Atlantic", "NC": "South Atlantic",
    "SC": "South Atlantic", "GA": "South Atlantic", "FL": "South Atlantic",
    "KY": "East South Central", "TN": "East South Central", "AL": "East South Central",
    "MS": "East South Central",
    "AR": "West South Central", "LA": "West South Central", "OK": "West South Central",
    "TX": "West South Central",
}


def fold_elec():
    if not os.path.exists(SRC):
        raise SystemExit("  eia-elec.zip missing - run eia.py ELEC")
    dpv = collections.defaultdict(lambda: collections.defaultdict(float))
    sun = collections.defaultdict(lambda: collections.defaultdict(float))
    sal = collections.defaultdict(lambda: collections.defaultdict(float))
    sectors = collections.Counter()
    with zipfile.ZipFile(SRC).open("ELEC.txt") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            sid = d.get("series_id", "")
            m = DPV.match(sid)
            if m:
                sectors[m.group(2)] += 1
                if m.group(2) != "99":          # 99 is all sectors; the rest are its parts
                    continue
                tgt, st = dpv, m.group(1)
            else:
                m2 = SUN.match(sid)
                if m2 and m2.group(3) == "99":
                    tgt, st = sun, m2.group(2)
                else:
                    m3 = SALES.match(sid)
                    if not m3:
                        continue
                    tgt, st = sal, m3.group(1)
            for stamp, v in (d.get("data") or []):
                q = str(stamp)
                if len(q) != 6 or v is None:
                    continue
                try:
                    tgt[st][q[:4]] += float(v)
                except (TypeError, ValueError):
                    pass
    return dpv, sun, sal, sectors


def build():
    dpv, sun, sal, sectors = fold_elec()
    sk = SK.load()
    rows = []
    for ba, yrs in sk["ba"].items():
        if ba in shape.REGION or A not in yrs or B not in yrs:
            continue
        st = predict.BA_STATE.get(ba)
        rec = {"ba": ba, "state": st, "division": DIVISION.get(st) if st else None,
               "gw": yrs[B]["mean_mw"] / 1000,
               "skill_a": yrs[A]["skill_adj"], "skill_b": yrs[B]["skill_adj"],
               "d_skill": yrs[B]["skill_adj"] - yrs[A]["skill_adj"],
               "ratio_a": yrs[A]["ratio"], "ratio_b": yrs[B]["ratio"],
               "d_ratio": yrs[B]["ratio"] - yrs[A]["ratio"]}
        if st:
            s_b = sal[st].get(B) or sal[st].get("2024")
            s_a = sal[st].get(A)
            d_b, d_a = dpv[st].get(B), dpv[st].get(A)
            u_b = sun[st].get(B)
            if s_b and d_b is not None:
                rec["dpv_share"] = d_b / s_b
                rec["util_share"] = (u_b / s_b) if u_b is not None else None
            if s_a and s_b and d_a is not None and d_b is not None:
                rec["dpv_growth"] = (d_b / s_b) - (d_a / s_a)
        rows.append(rec)
    return {"a": A, "b": B, "sectors": dict(sectors), "rows": rows}


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    print("  folding distributed PV, utility solar and retail sales by state ...", flush=True)
    d = build()
    tmp = CACHE + ".tmp"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return d


def corr(pairs):
    pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
    n = len(pairs)
    if n < 6:
        return None, None, n
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]

    def pe(a, b):
        ma, mb = sum(a) / n, sum(b) / n
        sa = sum((x - ma) ** 2 for x in a) ** .5
        sb = sum((y - mb) ** 2 for y in b) ** .5
        return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb) \
            if sa and sb else None

    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for p, i in enumerate(o):
            r[i] = float(p)
        return r
    return pe(xs, ys), pe(rk(xs), rk(ys)), n


def main():
    d = load()
    rows = d["rows"]
    mapped = [r for r in rows if r.get("dpv_share") is not None]
    print(f"\n  {len(rows)} balancing authorities, {len(mapped)} with a single-state "
          f"mapping and a rooftop estimate")
    print(f"  DPV sector codes seen: {d['sectors']}")

    print(f"\n  SKILL CHANGE {d['a']} to {d['b']}, BY CENSUS DIVISION")
    by = collections.defaultdict(list)
    for r in rows:
        by[r["division"] or "multi-state RTO or unmapped"].append(r)
    print(f"  {'division':<30}{'n':>4}{'median change':>15}{'worsened':>11}"
          f"{'median rooftop':>16}")
    for k in sorted(by, key=lambda k: statistics.median(x["d_skill"] for x in by[k])):
        g = by[k]
        dp = [x["dpv_share"] for x in g if x.get("dpv_share") is not None]
        print(f"  {k:<30}{len(g):>4}{statistics.median(x['d_skill'] for x in g):>+15.3f}"
              f"{sum(1 for x in g if x['d_skill'] < 0):>6} of {len(g):<4}"
              f"{(statistics.median(dp) if dp else float('nan')):>15.1%}")

    print(f"\n  DOES ROOFTOP SOLAR EXPLAIN IT?  (n = {len(mapped)} single-state authorities)")
    for key, lab in (("dpv_share", "rooftop PV as a share of state retail sales"),
                     ("dpv_growth", "growth in that share, 2019 to 2025"),
                     ("util_share", "utility-scale solar as a share of sales"),
                     ("gw", "grid size in GW")):
        for out, olab in (("d_skill", "skill change"), ("d_ratio", "scope-ratio change")):
            p, s, n = corr([(r.get(key), r.get(out)) for r in mapped])
            f = lambda x: f"{x:+.2f}" if x is not None else "  .  "
            print(f"    {lab:<44}{olab:<20}r {f(p)}  rho {f(s)}  n={n}")

    print(f"\n  THE STEEPEST DECLINES, with their rooftop penetration")
    print(f"  {'BA':<7}{'state':>6}{'GW':>7}{'skill':>17}{'change':>9}{'rooftop':>10}"
          f"   division")
    for r in sorted(rows, key=lambda x: x["d_skill"])[:10]:
        dp = r.get("dpv_share")
        print(f"  {r['ba']:<7}{(r['state'] or '--'):>6}{r['gw']:>7,.1f}"
              f"{r['skill_a']:>9.2f} ->{r['skill_b']:>6.2f}{r['d_skill']:>+9.2f}"
              f"{(f'{dp:.1%}' if dp is not None else '--'):>10}"
              f"   {r['division'] or '--'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
