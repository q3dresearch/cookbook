#!/usr/bin/env python3
"""Where the below-threshold bunching sits, and whether anything is missing above the line.

    python3 subthresh.py        # fold, then print every subgroup estimate with its n

Not a chart. `chart-13-bunching.py` draws it. The fold costs a few minutes per year, so it
caches beside the data; delete `subthresh-window.json` to rebuild.

**Two questions, one fold.** Figure 12 measured the excess just below the simplified
acquisition threshold on the whole register. Q30 asks whether that excess is spread thinly
or sits with particular buyers, product families or contract vehicles. Q32 asks whether the
awards just *above* the line are correspondingly missing -- if work is being held under the
threshold, the excess below has to come from somewhere.

**The estimator is figure 12's, imported rather than rebuilt**, so every number here is
directly comparable to that figure. `thresh.excess` fits a local exponential trend on a
+/-$60,000 window with the bins around the tested value held out, and reports the observed
count in the two $5,000 bins below against what that trend predicts.

**The deficit above is the same estimator with the value axis reflected.** `mirror()` maps
each award value to `2*thr - v`, which turns "the two bins just below the line" into "the two
bins just above it" and mirrors the held-out set with it. Nothing is reimplemented, so the
excess and the deficit are measured the same way on the same window and can be divided.

**Why the window is cached rather than the estimates.** Only awards within +/-$60,000 of the
year's rule can affect any estimate here, and a sorted list of those is all `thresh.excess`
reads. Caching the window with each award's department, product family and parent vehicle
lets every subgroup be re-cut without re-reading 300MB of transactions.

**Which years.** FY2017 and FY2025. FY2016's peak is not identified -- it ties its own
threshold against $310,000, where no rule exists -- so it cannot carry a subgroup claim.
"""
import bisect, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L                                                         # noqa: E402
import thresh                                                            # noqa: E402
from cats import FAM                                                     # noqa: E402

DATA = os.path.join(HERE, "..", "data")
CACHE = os.path.join(DATA, "subthresh-window.json")
YEARS = ("2017", "2025")
HALF = thresh.HALF
MIN_WINDOW = 400          # thresh.excess returns None below this; stated here to report it
EPS = 1e-3                # keeps the reflected bin edges half-open the same way
# Wide enough that every value on figure 12's sweep grid ($80,000 to $400,000) can be tested
# inside the cache, so a subgroup's placebo costs no fold.
BAND = (thresh.GRID[0] - HALF, thresh.GRID[-1] + HALF)
# Two of figure 12's declared placebos, both far enough from either rule to be null and both
# holding enough awards that ordinary subgroups can still be scored at them.
PLACEBO = (200000, 300000)

DEPT = {"Department of Homeland Security": "Homeland Security",
        "National Aeronautics and Space Administration": "NASA",
        "Environmental Protection Agency": "EPA",
        "Department of Veterans Affairs": "Veterans Affairs",
        "Department of Health and Human Services": "Health and Human Services",
        "Department of Agriculture": "Agriculture",
        "Department of the Interior": "Interior",
        "Department of Justice": "Justice",
        "Department of Commerce": "Commerce",
        "Department of Transportation": "Transportation",
        "Department of Energy": "Energy",
        "Department of Labor": "Labor",
        "Department of Education": "Education",
        "Department of State": "State",
        "Department of the Treasury": "Treasury"}


def short(name):
    return DEPT.get(name, name.replace("Department of ", ""))


def mirror(v, thr):
    """The window reflected about `thr`, so `thresh.excess` reads the two bins ABOVE it.

    Bins are half-open on the left, and award values pile on exact multiples of $5,000, so
    a plain reflection would put a $250,000.00 award on the wrong side of its own edge. The
    epsilon keeps the reflected binning an exact mirror of the original.

    **The two sides have to partition, or the ratio between them is meaningless.** Summing
    obligations in floating point lands a handful of awards a few billionths of a dollar
    below a round threshold. Figure 12's estimator counts those below; reflected, they would
    come back inside the pair above and be counted twice. One award does this in FY2025 and
    none in FY2017, and it is parked in the held-out bin rather than counted again, which
    makes the measured pairs exactly [thr-$10,000, thr) and [thr, thr+$10,000).
    """
    return sorted(thr + EPS if thr - EPS < x < thr else 2 * thr - x - EPS for x in v)


def fold(path, thr):
    """Awards inside BAND, with the three subgroup keys each one carries."""
    acc = {}
    for r in L.transactions(path):
        k = r.get(L.KEY)
        if not k:
            continue
        a = acc.get(k)
        if a is None:
            a = acc[k] = [0.0, "", "", ""]
        a[0] += L.num(r.get("federal_action_obligation")) or 0.0
        for i, c in ((1, "awarding_agency_name"), (2, "product_or_service_code"),
                     (3, "parent_award_id_piid")):
            if not a[i]:
                a[i] = sys.intern((r.get(c) or "").strip())
    lo, hi = BAND
    pos = veh_all = 0
    seen = set()
    rows = []
    for v, ag, psc, par in acc.values():
        if v <= 0:
            continue
        pos += 1
        if par:
            veh_all += 1
            seen.add(par)
        if lo <= v < hi:
            rows.append((v, short(ag), psc[:1].upper(), par))
    rows.sort()
    win = sum(1 for r in rows if thr - HALF <= r[0] < thr + HALF)
    return rows, {"n_awards": len(acc), "n_positive": pos, "window_n": win,
                  "n_with_vehicle": veh_all, "n_vehicles": len(seen)}


def build(years=YEARS):
    out = {"years": {}}
    for y in years:
        p = os.path.join(DATA, f"civilian-fy{y}.zip")
        if not os.path.exists(p):
            print(f"  civilian-fy{y}.zip missing, skipping", flush=True)
            continue
        thr = thresh.RULE[y]
        print(f"  folding civilian-fy{y}.zip around ${thr:,} ...", flush=True)
        rows, meta = fold(p, thr)
        depts = sorted({r[1] for r in rows})
        vehs = sorted({r[3] for r in rows if r[3]})
        di = {d: i for i, d in enumerate(depts)}
        vi = {v: i for i, v in enumerate(vehs)}
        meta.update({"rule": thr, "band_n": len(rows), "depts": depts, "vehicles": vehs,
                     "v": [r[0] for r in rows],
                     "d": [di[r[1]] for r in rows],
                     "f": [r[2] for r in rows],
                     "p": [vi[r[3]] if r[3] else -1 for r in rows]})
        out["years"][y] = meta
    return out


def load(years=YEARS):
    if os.path.exists(CACHE):
        d = json.load(open(CACHE))
        if all(y in d.get("years", {}) for y in years):
            return d
    d = build(years)
    tmp = CACHE + f".tmp.{os.getpid()}"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return d


def cuts(g):
    """The three subgroup cuts, as {label: [values]}, plus the whole window under 'ALL'."""
    v, thr = g["v"], g["rule"]
    dep = collections.defaultdict(list)
    fam = collections.defaultdict(list)
    veh = collections.defaultdict(list)
    for i, x in enumerate(v):
        dep[g["depts"][g["d"][i]]].append(x)
        if g["f"][i]:
            fam[g["f"][i]].append(x)
        if g["p"][i] >= 0:
            veh[g["vehicles"][g["p"][i]]].append(x)
    return {"department": dict(dep), "family": dict(fam), "vehicle": dict(veh)}


def win_n(v, thr):
    """How many of `v` land in the +/-$60,000 window the estimator reads."""
    s = sorted(v)
    return bisect.bisect_left(s, thr + HALF) - bisect.bisect_left(s, thr - HALF)


def pair(v, thr):
    """Excess in the two bins below `thr`, and deficit in the two bins above it."""
    below = thresh.excess(sorted(v), thr)
    above = thresh.excess(mirror(v, thr), thr)
    if not below or not above:
        return None
    return {"n": below["window_n"], "below": below, "above": above,
            "surplus": below["obs"] - below["exp"],
            "shortfall": above["exp"] - above["obs"],
            "ratio": (above["exp"] - above["obs"]) / (below["obs"] - below["exp"])
                     if below["obs"] > below["exp"] else None}




def quant(a, f):
    s = sorted(a)
    return s[int(f * (len(s) - 1))] if s else 0.0


def sweep_rank(g, drop_exact=False):
    """Both sides at every value on figure 12's grid, and where the rule ranks among them.

    **This is the control that decides Q32, and it is harsher than the subgroup band.** A
    deficit above the line only means something if it is bigger than the deficit this
    estimator reports at values with no rule behind them. Sweeping the whole grid gives 32
    such values per year.

    `drop_exact` removes awards priced at exactly the value being tested. That pile is a
    round-number habit rather than a rule effect -- in FY2017 it is 1.95x the local $1,000
    background at $150,000 and 2.09x at $300,000, where no rule exists -- and figure 12's
    binning puts it in the first bin ABOVE the line, which is the single thing keeping the
    deficit from appearing. Dropping it from both sides is the friendliest reading the
    displacement story can get, so it is the one worth reporting against a control.
    """
    v, thr = g["v"], g["rule"]
    out = {"rule": None, "below": [], "above": []}
    for t in thresh.GRID:
        vs = [x for x in v if abs(x - t) >= 0.005] if drop_exact else v
        r = pair(vs, t)
        if not r:
            continue
        if t == thr:
            out["rule"] = (r["below"]["excess"], r["above"]["excess"], r["ratio"])
        else:
            out["below"].append(r["below"]["excess"])
            out["above"].append(r["above"]["excess"])
    b, a = out["rule"][0], out["rule"][1]
    out["below_beats"] = sum(1 for x in out["below"] if x < b) / len(out["below"])
    out["above_under"] = sum(1 for x in out["above"] if x > a) / len(out["above"])
    out["below_median"] = quant(out["below"], 0.5)
    out["above_median"] = quant(out["above"], 0.5)
    return out


def report(d, years=YEARS):
    """Everything the chart draws: one block of scored subgroups per cut, per year.

    The null band is the same subgroups measured at PLACEBO values, where no rule exists.
    Pooling the below and above readings there gives the spread this estimator produces on
    a subgroup of this size with nothing to find, which is what a subgroup at the rule has
    to clear to mean anything. The placebo windows hold fewer awards than the rule's does,
    so the band is if anything too wide.
    """
    out = {}
    for y in years:
        g = d["years"][y]
        thr = g["rule"]
        cu = cuts(g)
        win = win_n(g["v"], thr)
        blocks, plac = [], []
        for cut in ("department", "family"):
            rs = []
            for lab, vs in cu[cut].items():
                n = win_n(vs, thr)
                if n < MIN_WINDOW:
                    continue
                r = pair(vs, thr)
                if not r:
                    continue
                rs.append({"label": lab, "name": FAM.get(lab, lab) if cut == "family"
                           else lab, "n": r["n"], "below": r["below"]["excess"],
                           "above": r["above"]["excess"], "surplus": r["surplus"],
                           "shortfall": r["shortfall"]})
                for p in PLACEBO:
                    if p == thr or win_n(vs, p) < MIN_WINDOW:
                        continue
                    q = pair(vs, p)
                    if q:
                        plac += [q["below"]["excess"], q["above"]["excess"]]
            rs.sort(key=lambda r: -r["below"])
            blocks.append({"cut": cut, "rows": rs, "n_groups": len(cu[cut]),
                           "covered": sum(r["n"] for r in rs)})
        vn = sorted(win_n(vs, thr) for vs in cu["vehicle"].values())
        veh = {"n_groups": len(vn), "biggest": vn[-1] if vn else 0,
               "scored": sum(1 for n in vn if n >= MIN_WINDOW),
               "covered": sum(vn)}
        lo, hi = quant(plac, 0.10), quant(plac, 0.90)
        rows = [r for b in blocks for r in b["rows"]]
        out[y] = {"rule": thr, "window_n": win, "n_positive": g["n_positive"],
                  "blocks": blocks, "vehicle": veh, "band": (lo, hi),
                  "n_placebo": len(plac),
                  "clear_below": sum(1 for r in rows if r["below"] > hi),
                  "clear_above": sum(1 for r in rows if r["above"] < lo),
                  "n_rows": len(rows),
                  "all": pair(g["v"], thr), "all_statutory": pair(g["v"], thr + 1),
                  "placebo": {p: pair(g["v"], p) for p in PLACEBO if p != thr},
                  "placebo_statutory": {p: pair(g["v"], p + 1)
                                        for p in PLACEBO if p != thr}}
    return out


def main():
    d = load()
    rep = report(d)
    for y in sorted(rep):
        o = rep[y]
        a, s = o["all"], o["all_statutory"]
        print(f"\nFY{y}  rule ${o['rule']:,}  {o['n_positive']:,} positive awards, "
              f"{o['window_n']:,} in the +/-$60,000 window")
        for tag, r in (("figure 12's binning", a), ("at-or-below counts below", s)):
            rt = f"{r['ratio']:+.2f}" if r["ratio"] is not None else "-"
            print(f"  ALL, {tag:<26} below {r['below']['excess']:+6.1f}% "
                  f"({r['surplus']:+,.0f} awards)  above {r['above']['excess']:+6.1f}% "
                  f"({-r['shortfall']:+,.0f} awards)  deficit-to-excess {rt}")
        for p, r in sorted(o["placebo"].items()):
            if r:
                print(f"  placebo ${p:,}: below {r['below']['excess']:+6.1f}%  "
                      f"above {r['above']['excess']:+6.1f}%")
        print(f"  null band from {o['n_placebo']} placebo readings: "
              f"{o['band'][0]:+.1f}% to {o['band'][1]:+.1f}%; "
              f"{o['clear_below']} of {o['n_rows']} subgroups clear it below, "
              f"{o['clear_above']} below it above")
        for tag, de in (("figure 12's binning", False), ("exact-value pile dropped", True)):
            r = sweep_rank(d["years"][y], drop_exact=de)
            print(f"  sweep control, {tag}: below {r['rule'][0]:+.1f}% beats "
                  f"{r['below_beats']:.0%} of {len(r['below'])} other grid values "
                  f"(median {r['below_median']:+.1f}%); above {r['rule'][1]:+.1f}% is under "
                  f"{r['above_under']:.0%} of them (median {r['above_median']:+.1f}%)")
        for b in o["blocks"]:
            print(f"  {b['cut']}: {len(b['rows'])} of {b['n_groups']} scored, "
                  f"{b['covered']:,} of {o['window_n']:,} awards")
            for r in b["rows"]:
                k = r["label"] if r["label"] != r["name"] else ""
                print(f"      {k:<3}{r['name'][:38]:<40} n {r['n']:>6,}  "
                      f"below {r['below']:+6.1f}%  above {r['above']:+6.1f}%  "
                      f"surplus {r['surplus']:+6.0f}")
        v = o["vehicle"]
        print(f"  vehicle: {v['scored']} of {v['n_groups']:,} scored "
              f"(largest holds {v['biggest']}, floor is {MIN_WINDOW}); "
              f"{v['covered']:,} of {o['window_n']:,} window awards carry one")
    return 0


if __name__ == "__main__":
    sys.exit(main())
