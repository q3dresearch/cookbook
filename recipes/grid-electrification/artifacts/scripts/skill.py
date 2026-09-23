#!/usr/bin/env python3
"""Forecast skill measured against what it is actually hard to beat.

    python3 skill.py

**Why the first version of this was weak.** It scored each balancing authority's day-ahead
forecast by the inter-quartile range of forecast-over-actual. The IQR is the middle 50% of
hours, so it says nothing about the tail -- and the tail is the entire operational point of a
demand forecast. It also does not normalise for difficulty: a grid whose load swings wildly
is genuinely harder to forecast, so a raw error spread partly measures the grid rather than
the forecaster. A reader asked both questions and both were right.

**So skill is scored against a naive baseline instead.** The baseline is persistence -- the
same hour one week earlier, which for electricity demand is the honest naive forecast because
it carries the weekday and the hour of day for free.

    skill = 1 - MAE(forecast) / MAE(persistence)

1.0 is perfect, 0.0 is no better than repeating last week, and **negative means worse than
doing nothing**. This normalises difficulty automatically: a volatile grid has a large
baseline error, so beating it is what counts, and no separate volatility index is needed.

**Scope is separated from skill rather than mixed into it.** Duke Energy Florida forecasts
0.766 of the demand it reports, in every hour. Raw, that is a catastrophic error; corrected
for the level, it is one of the tighter forecasts in the country. So every statistic is
computed twice -- once on the published forecast, and once on the forecast rescaled by the
year's median actual-over-forecast ratio. The gap between them **is** the scope penalty, and
it is reported as its own number instead of contaminating the skill one.

**Tails and peaks are reported, not summarised away.** p95 and p99 of absolute percentage
error, and separately the signed error across the **top 5% of demand hours**, because
under-forecasting the peak and under-forecasting a Tuesday in April are not the same failure.

**And it is per year**, 2019 to 2025, so skill can be read as a trajectory rather than a
single number for one year.
"""
import array, collections, datetime as dt, json, math, os, re, statistics, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
SRC = os.path.join(DATA, "eia-eba.zip")
CACHE = os.path.join(DATA, "eba-skill.json")

PAT = re.compile(r"^EBA\.([A-Z0-9]+)-ALL\.(D|DF)\.H$")
Y0, Y1 = 2019, 2025
EPOCH = dt.datetime(Y0, 1, 1)
NH = int((dt.datetime(Y1 + 1, 1, 1) - EPOCH).total_seconds() // 3600)
LAG = 168                 # one week: the naive forecast that already knows the weekday
PEAK_Q = 0.95             # the top 5% of demand hours get scored on their own
MIN_HOURS = 6000          # a year below this cannot carry an annual number


def hour_index(stamp):
    """'20250101T05' -> hours since Y0-01-01T00. Returns None outside the window."""
    try:
        y, mo, d = int(stamp[0:4]), int(stamp[4:6]), int(stamp[6:8])
        h = int(stamp[9:11])
    except (ValueError, IndexError):
        return None
    if not Y0 <= y <= Y1:
        return None
    return int((dt.datetime(y, mo, d) - EPOCH).total_seconds() // 3600) + h


def read():
    if not os.path.exists(SRC):
        raise SystemExit("  eia-eba.zip missing - run eia.py EBA")
    nan = float("nan")
    D, F = {}, {}
    with zipfile.ZipFile(SRC).open("EBA.txt") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            m = PAT.match(rec.get("series_id", ""))
            if not m:
                continue
            ba, kind = m.group(1), m.group(2)
            tgt = (D if kind == "D" else F)
            a = tgt.get(ba)
            if a is None:
                a = tgt[ba] = array.array("d", [nan]) * NH
            for stamp, v in (rec.get("data") or []):
                if v is None:
                    continue
                i = hour_index(stamp)
                if i is None:
                    continue
                try:
                    a[i] = float(v)
                except (TypeError, ValueError):
                    pass
    return D, F


def year_slice(y):
    a = int((dt.datetime(y, 1, 1) - EPOCH).total_seconds() // 3600)
    b = int((dt.datetime(y + 1, 1, 1) - EPOCH).total_seconds() // 3600)
    return a, b


def score(d, f, lo, hi):
    """Everything for one balancing authority and one year, or None."""
    idx = [i for i in range(lo, hi)
           if not math.isnan(d[i]) and not math.isnan(f[i]) and d[i] > 0]
    if len(idx) < MIN_HOURS:
        return None
    md = sum(d[i] for i in idx) / len(idx)
    ratio = statistics.median(f[i] / d[i] for i in idx)
    k = 1.0 / ratio if ratio else 1.0          # rescale the forecast to the right LEVEL

    # persistence: same hour one week earlier, scored on the hours it can reach
    pidx = [i for i in idx if i - LAG >= 0 and not math.isnan(d[i - LAG])]
    if len(pidx) < MIN_HOURS:
        return None
    mae_p = sum(abs(d[i] - d[i - LAG]) for i in pidx) / len(pidx)
    mae_f = sum(abs(f[i] - d[i]) for i in pidx) / len(pidx)
    mae_a = sum(abs(f[i] * k - d[i]) for i in pidx) / len(pidx)

    ape = sorted(abs(f[i] * k - d[i]) / d[i] for i in idx)
    q = lambda p: ape[min(len(ape) - 1, int(len(ape) * p))]
    cut = sorted(d[i] for i in idx)[int(len(idx) * PEAK_Q)]
    pk = [i for i in idx if d[i] >= cut]
    months = collections.defaultdict(list)
    for i in idx:
        months[(EPOCH + dt.timedelta(hours=i)).month].append(d[i])
    mm = sorted(sum(v) / len(v) for v in months.values() if len(v) > 200)

    return {"hours": len(idx), "mean_mw": md, "ratio": ratio,
            "nmae_f": mae_f / md, "nmae_adj": mae_a / md, "nmae_naive": mae_p / md,
            "skill": 1 - mae_f / mae_p if mae_p else None,
            "skill_adj": 1 - mae_a / mae_p if mae_p else None,
            "p50": q(.50), "p95": q(.95), "p99": q(.99),
            "peak_bias": (sum((f[i] * k - d[i]) / d[i] for i in pk) / len(pk)) if pk else None,
            "peak_p95": sorted(abs(f[i] * k - d[i]) / d[i] for i in pk)[int(len(pk) * .95)]
            if pk else None,
            "season": (mm[-1] / mm[0]) if len(mm) >= 10 and mm[0] else None}


def build():
    D, F = read()
    out = {"lag": LAG, "years": list(range(Y0, Y1 + 1)), "ba": {}}
    for ba in sorted(set(D) & set(F)):
        d, f = D[ba], F[ba]
        yrs = {}
        for y in range(Y0, Y1 + 1):
            lo, hi = year_slice(y)
            r = score(d, f, lo, hi)
            if r:
                yrs[str(y)] = r
        if yrs:
            out["ba"][ba] = yrs
    return out


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    print("  folding hourly demand and forecast, 2019-2025 ...", flush=True)
    d = build()
    tmp = CACHE + ".tmp"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return d


def main():
    d = load()
    Y = "2025"
    rows = sorted(((v[Y], ba) for ba, v in d["ba"].items() if Y in v),
                  key=lambda t: -(t[0]["skill_adj"] or -9))
    print(f"\n  SKILL against same-hour-last-week persistence, {Y}   "
          f"({len(rows)} balancing authorities)")
    print("  1.0 perfect, 0.0 no better than repeating last week, negative is worse\n")
    print(f"  {'BA':<7}{'GW':>7}{'skill':>8}{'adj':>8}{'scope':>8}{'nMAE':>8}"
          f"{'naive':>8}{'p95':>8}{'p99':>8}{'peak':>8}")
    for v, ba in rows[:10] + [(None, "")] + rows[-8:]:
        if v is None:
            print("  " + "." * 70)
            continue
        print(f"  {ba:<7}{v['mean_mw']/1000:>7,.1f}{v['skill']:>8.2f}"
              f"{v['skill_adj']:>8.2f}{v['ratio']:>8.3f}{v['nmae_adj']:>8.2%}"
              f"{v['nmae_naive']:>8.2%}{v['p95']:>8.1%}{v['p99']:>8.1%}"
              f"{v['peak_bias']:>+8.1%}")
    sk = [v["skill_adj"] for v, _ in rows]
    print(f"\n  median adjusted skill {statistics.median(sk):+.2f}; "
          f"{sum(1 for s in sk if s < 0)} of {len(sk)} are worse than persistence")
    sc = [(v["skill"], v["skill_adj"], ba) for v, ba in rows]
    worst = sorted(sc, key=lambda t: t[1] - t[0])[-5:]
    print(f"  largest scope penalty (adjusted minus raw skill):")
    for a, b, ba in reversed(worst):
        print(f"    {ba:<7}raw {a:>+6.2f}  adjusted {b:>+6.2f}  gain {b-a:>+5.2f}")
    print(f"\n  SKILL OVER TIME, adjusted, the eight largest grids")
    big = sorted(d["ba"], key=lambda b: -(d["ba"][b].get(Y, {}).get("mean_mw", 0)))[:8]
    print(f"  {'BA':<7}" + "".join(f"{y:>8}" for y in d["years"]))
    for ba in big:
        print(f"  {ba:<7}" + "".join(
            f"{d['ba'][ba][str(y)]['skill_adj']:>8.2f}" if str(y) in d["ba"][ba]
            else f"{'--':>8}" for y in d["years"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
