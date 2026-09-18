#!/usr/bin/env python3
"""How long UK companies last, estimated from a register that publishes only survivors.

    python3 survive.py

THE PROBLEM THIS WORKS AROUND. The monthly bulk file contains live companies only --
every status in it is one a company holds while still on the register, and the
DissolutionDate column is never populated. So a death is not an event in the data; it
is a company that was in last year's file and is not in this year's.

THE DESIGN. Consecutive snapshots give intervals. A company present at the start of an
interval is under observation for it; a company absent at the end died during it. Its
age at the start is known, because incorporation date is on every live row. That is a
LEFT-TRUNCATED sample -- nothing that died before the first snapshot is visible -- and
a discrete-time hazard by age is still estimable from it, PROVIDED the hazard depends
on age rather than on the calendar.

That proviso is testable here rather than assumed, and testing it is the point of
using three snapshots instead of two: the same age band is measured in two different
years, and if the two disagree the design is wrong and says so.

WHAT A DEATH IS NOT. Leaving the register is not the same as failing. A company is
struck off after acquisition, after a founder tidies up a dormant shell, and after
simply not filing. The register does not say which, so neither does this.
"""
import collections, csv, gzip, glob, json, math, os, re, sys

DATA = os.environ.get("FSB_DATA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
BANDS = [(0, 1), (1, 2), (2, 3), (3, 5), (5, 8), (8, 12), (12, 20), (20, 200)]
# SIC 2007 sections, the standard grouping. Division -> section letter.
SECTION = [(1, 3, "Agriculture"), (5, 9, "Mining"), (10, 33, "Manufacturing"),
           (35, 35, "Utilities"), (36, 39, "Water & waste"), (41, 43, "Construction"),
           (45, 47, "Retail & wholesale"), (49, 53, "Transport"), (55, 56, "Hospitality"),
           (58, 63, "Information & communication"), (64, 66, "Finance & insurance"),
           (68, 68, "Real estate"), (69, 75, "Professional & scientific"),
           (77, 82, "Administrative & support"), (84, 84, "Public administration"),
           (85, 85, "Education"), (86, 88, "Health & social work"),
           (90, 93, "Arts & recreation"), (94, 96, "Other services"),
           (97, 99, "Households & extraterritorial")]


def section(code):
    if not code:
        return "Not stated"
    d = int(code[:2])
    if code == "99999":
        return "Not stated"
    for lo, hi, name in SECTION:
        if lo <= d <= hi:
            return name
    return "Not stated"


def months_between(a, b):
    ya, ma = int(a[:4]), int(a[5:7])
    yb, mb = int(b[:4]), int(b[5:7])
    return (yb - ya) * 12 + (mb - ma)


def load(path):
    out = {}
    with gzip.open(path, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            out[r["number"]] = (r["incorp"], r["sic"], r["category"], r["status"])
    return out


def band(age_years):
    for lo, hi in BANDS:
        if lo <= age_years < hi:
            return f"{lo}-{hi}" if hi < 200 else f"{lo}+"
    return None


def main():
    files = sorted(glob.glob(os.path.join(DATA, "compact-*.csv.gz")))
    if len(files) < 2:
        print(f"  need two snapshots, found {len(files)}")
        return 1
    dates = [os.path.basename(f)[8:18] for f in files]
    print("  snapshots:", ", ".join(dates))
    snaps = {}
    for f, d in zip(files, dates):
        snaps[d] = load(f)
        print(f"    {d}: {len(snaps[d]):,} live companies")

    intervals = list(zip(dates, dates[1:]))
    haz = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))   # interval -> band -> [risk, died]
    sec = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))   # section -> band -> [risk, died]
    for t0, t1 in intervals:
        a, b = snaps[t0], snaps[t1]
        for num, (inc, sc, cat, st) in a.items():
            if not inc:
                continue
            age = months_between(inc, t0) / 12
            if age < 0:
                continue
            bd = band(age)
            if bd is None:
                continue
            died = num not in b
            haz[f"{t0}→{t1}"][bd][0] += 1
            haz[f"{t0}→{t1}"][bd][1] += died
            s = section(sc)
            sec[s][bd][0] += 1
            sec[s][bd][1] += died

    # WHAT A DEATH IS. The register flags a company as "Active - Proposal to Strike off"
    # before removing it for not filing. If deaths come overwhelmingly from companies
    # already carrying that flag, the series is measuring administrative strike-off and
    # should not be called failure. Measured rather than assumed.
    print("\n== what a death is: was it already flagged before it went? ==")
    flag = collections.Counter()
    for t0, t1 in intervals:
        a, b = snaps[t0], snaps[t1]
        for num, (inc, sc, cat, st) in a.items():
            if num in b:
                continue
            flag["flagged for strike-off" if "Strike off" in st
                 else "in liquidation or administration" if any(w in st for w in ("Liquidation", "Administration", "Receiver"))
                 else "no warning: plain Active" if st.startswith("Active") else st] += 1
    tot = sum(flag.values())
    for k, n in flag.most_common(6):
        print(f"   {n:9,} ({n/tot:5.1%})  {k}")
    print(f"   {tot:,} departures across {len(intervals)} interval(s)")

    print(f"\n== annual hazard of leaving the register, by age, measured twice ==")
    print(f"  {'age (years)':<14}" + "".join(f"{k:>22}" for k in haz) + f"{'difference':>14}")
    labels = [f"{lo}-{hi}" if hi < 200 else f"{lo}+" for lo, hi in BANDS]
    for bd in labels:
        cells, rates = [], []
        for k in haz:
            risk, died = haz[k][bd]
            r = died / risk if risk else float("nan")
            rates.append(r)
            cells.append(f"{r:>13.2%} of {risk/1e6:>4.1f}M")
        diff = (rates[1] - rates[0]) if len(rates) > 1 else float("nan")
        print(f"  {bd:<14}" + "".join(f"{c:>22}" for c in cells) + f"{diff:>+13.2%}")
    print("  The two columns are the same ages measured a year apart. If they disagree, the")
    print("  hazard moves with the calendar and an age-only curve is not a valid summary.")

    print(f"\n== survival to each age, from the pooled hazards ==")
    surv, out = 1.0, []
    for (lo, hi), bd in zip(BANDS, labels):
        risk = sum(haz[k][bd][0] for k in haz)
        died = sum(haz[k][bd][1] for k in haz)
        h = died / risk if risk else 0.0
        width = min(hi, 25) - lo
        surv *= (1 - h) ** width
        out.append({"band": bd, "hazard": h, "risk": risk, "survival_to_end": surv})
        print(f"  {bd:<10} hazard {h:6.2%}/yr   survival to age {min(hi,25):>3}: {surv:6.1%}")

    print(f"\n== hazard by sector, ages 1-5, the years where the risk is highest ==")
    rows = []
    for s, bands_ in sec.items():
        risk = sum(bands_[b][0] for b in ("1-2", "2-3", "3-5"))
        died = sum(bands_[b][1] for b in ("1-2", "2-3", "3-5"))
        if risk >= 20000:
            rows.append((died / risk, risk, s))
    rows.sort(reverse=True)
    for h, risk, s in rows:
        print(f"  {s:<32} {h:6.2%}/yr   on {risk/1e6:>5.2f}M company-years at risk")

    # per-sector, per-band hazards so the figure can draw curves rather than one number
    curves = {}
    for sname, bands_ in sec.items():
        tot_risk = sum(bands_[b][0] for b in labels)
        if tot_risk < 100000:
            continue
        surv_, pts = 1.0, []
        for (lo, hi), bd in zip(BANDS, labels):
            risk, died = bands_[bd]
            h = died / risk if risk else 0.0
            width = min(hi, 25) - lo
            surv_ *= (1 - h) ** width
            pts.append({"age": min(hi, 25), "hazard": h, "survival": surv_, "risk": risk})
        curves[sname] = pts

    json.dump({"intervals": {k: {b: v for b, v in d.items()} for k, d in haz.items()},
               "survival": out,
               "sectors": [{"section": s, "hazard_1_5": h, "at_risk": r} for h, r, s in rows],
               "curves": curves,
               "departures_by_prior_status": dict(flag),
               "snapshot_dates": dates,
               "live_counts": {d: len(snaps[d]) for d in dates}},
              open(os.path.join(DATA, "survival.json"), "w"), indent=1)
    print(f"\n  wrote {os.path.join(DATA, 'survival.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
