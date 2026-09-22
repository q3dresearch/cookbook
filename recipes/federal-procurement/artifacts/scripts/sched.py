#!/usr/bin/env python3
"""Shared fold for the two schedule figures: option time, and who holds it.

Not a chart. `chart-6-schedule.py` draws the shape of the quantity and
`chart-7-holders.py` draws who carries it; both need the same award-level fold of the
two period-of-performance columns, which costs a few minutes per year, so it lives here
and caches beside the data.

The split exists because the two subjects were one plate with four panels and a reader
said it was too loaded. Two panels is the ceiling for a figure in this recipe.
"""
import collections, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L, plate                                                  # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

DATA = os.path.join(HERE, "..", "data")
YEARS = ("2016", "2015")
RED, AMBER, GREEN, BLUE, PLUM = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#6b4a80"

C_CUR = "period_of_performance_current_end_date"
C_POT = "period_of_performance_potential_end_date"
C_ST = "period_of_performance_start_date"

# Bands are contract-term boundaries (a month, a quarter, half a year, a year, 18 months,
# two, three, five), not equal steps: the quantity being measured is itself quantised.
BANDS = [(0, 31), (31, 92), (92, 184), (184, 275), (275, 366), (366, 550), (550, 731),
         (731, 1096), (1096, 1826), (1826, 3650)]
CAP = 1826                          # 5 years; 99% of potential periods are at or under it
COMP = {"FULL AND OPEN COMPETITION": 1, "COMPETED UNDER SAP": 1,
        "FULL AND OPEN COMPETITION AFTER EXCLUSION OF SOURCES": 1,
        "COMPETITIVE DELIVERY ORDER": 1, "NOT COMPETED": 0,
        "NOT COMPETED UNDER SAP": 0, "NOT AVAILABLE FOR COMPETITION": 0,
        "NON-COMPETITIVE DELIVERY ORDER": 0}
SHORT = {"Department of Veterans Affairs": "Veterans Affairs",
         "Department of Justice": "Justice",
         "Department of Health and Human Services": "Health & Human Svcs",
         "Department of Homeland Security": "Homeland Security",
         "Department of Agriculture": "Agriculture",
         "Department of the Interior": "Interior",
         "Department of Commerce": "Commerce",
         "Department of Transportation": "Transportation",
         "National Aeronautics and Space Administration": "NASA",
         "Environmental Protection Agency": "EPA",
         "Department of Energy": "Energy"}
ATYPE = {"DELIVERY ORDER": "delivery order", "PURCHASE ORDER": "purchase order",
         "BPA CALL": "BPA call", "DEFINITIVE CONTRACT": "definitive contract"}


def days(a, b):
    """Whole days from ISO date a to ISO date b, or None. Proleptic, no calendar import."""
    def ordn(s):
        try:
            y, m, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
        except ValueError:
            return None
        if not (1 <= m <= 12 and 1 <= d <= 31 and 1900 <= y <= 2200):
            return None
        m = (m + 9) % 12
        y = y - m // 10
        return 365 * y + y // 4 - y // 100 + y // 400 + (m * 306 + 5) // 10 + (d - 1)
    x, z = ordn(a), ordn(b)
    return None if x is None or z is None else z - x


def qtl(v, p):
    v = sorted(v)
    return v[min(int(p * (len(v) - 1)), len(v) - 1)] if v else 0


def fold(path):
    """One pass over a year's transactions -> a small summary. Max per award, not last."""
    acc = {}
    ntx = 0
    for r in L.transactions(path):
        ntx += 1
        k = r.get(L.KEY) or r.get("award_id_piid")
        if not k:
            continue
        cu, po, st = (r.get(C_CUR) or "")[:10], (r.get(C_POT) or "")[:10], (r.get(C_ST) or "")[:10]
        ad = (r.get("action_date") or "")[:10]
        a = acc.get(k)
        if a is None:
            a = acc[k] = {"cu": "", "po": "", "st": "", "lad": "", "lcu": "", "lpo": "",
                          "ag": (r.get("awarding_agency_name") or "?"),
                          "cmp": (r.get("extent_competed") or "?").strip(),
                          "aty": (r.get("award_type") or "?").strip(),
                          "ob": 0.0, "tx": 0, "ncur": 0, "npot": 0}
        a["tx"] += 1
        a["ncur"] += bool(cu)
        a["npot"] += bool(po)
        a["ob"] += L.num(r.get("federal_action_obligation")) or 0.0
        if cu > a["cu"]:
            a["cu"] = cu
        if po > a["po"]:
            a["po"] = po
        if st and (not a["st"] or st < a["st"]):
            a["st"] = st
        if ad >= a["lad"]:
            a["lad"], a["lcu"], a["lpo"] = ad, cu, po
    return summarise(acc, ntx, os.path.basename(path))


def summarise(acc, ntx, fname):
    s = {"file": fname, "transactions": ntx, "awards": len(acc)}
    rows = []
    for a in acc.values():
        g = days(a["cu"], a["po"])
        if g is None:
            continue
        a["gap"] = g
        a["dur"] = days(a["st"], a["cu"]) if a["st"] else None
        a["pdur"] = days(a["st"], a["po"]) if a["st"] else None
        a["far"] = a["po"][:4] > "2040"
        rows.append(a)
    s["both"] = len(rows)
    s["every"] = sum(1 for a in rows if a["ncur"] == a["tx"] and a["npot"] == a["tx"])
    s["neg"] = sum(1 for a in rows if a["gap"] < 0)
    pos = [a for a in rows if a["gap"] > 0]
    s["pos"] = len(pos)
    gp = [a["gap"] for a in pos]
    s["gapq"] = {str(p): qtl(gp, p) for p in (.25, .5, .75, .9)}
    s["year_share"] = sum(1 for g in gp if min(abs(g - 365 * k) for k in range(1, 8)) <= 5) / len(gp)
    s["month_share"] = sum(1 for g in gp if 28 <= g <= 31) / len(gp)
    s["exact365"] = sum(1 for g in gp if g == 365) / len(gp)

    # 7-day histogram of the gap. Linear, because the claim is that the spikes are EVENLY
    # spaced -- a log axis would hide exactly the periodicity being asserted.
    h = collections.Counter()
    for g in gp:
        h[min(g, 1904) // 7] += 1
    s["hist"] = {str(k): v for k, v in sorted(h.items())}
    s["hist_over"] = sum(1 for g in gp if g > 1904)

    # sensitivity to max-vs-last on the awards where the two can differ
    mt = [a for a in rows if a["tx"] > 1 and a["lcu"] and a["lpo"]]
    s["multi"] = len(mt)
    s["multi_max"] = sum(1 for a in mt if a["gap"] > 0) / max(len(mt), 1)
    s["multi_last"] = sum(1 for a in mt if (days(a["lcu"], a["lpo"]) or 0) > 0) / max(len(mt), 1)

    dur = [a for a in rows if a["dur"] is not None and a["dur"] >= 0]
    s["with_dur"] = len(dur)
    drop = [a for a in rows if a["st"] and a["dur"] is not None and a["dur"] < 0]
    s["drop_any"] = sum(1 for a in drop if a["gap"] > 0) / max(len(drop), 1)
    s["kept_any"] = sum(1 for a in dur if a["gap"] > 0) / len(dur)
    s["durq"] = {str(p): qtl([a["dur"] for a in dur], p) for p in (.25, .5, .75, .9)}
    s["pdurq"] = {str(p): qtl([a["pdur"] for a in dur], p) for p in (.5, .95, .99)}
    s["over_cap"] = sum(1 for a in dur if a["pdur"] > CAP) / len(dur)

    def bandrow(pool):
        out = []
        for lo, hi in BANDS:
            sub = [a for a in pool if lo <= a["dur"] < hi] if hi < 3650 else \
                  [a for a in pool if a["dur"] >= lo]
            p = [a for a in sub if a["gap"] > 0]
            out.append({"lo": lo, "hi": hi, "n": len(sub),
                        "np": sum(1 for a in p if not a["far"]),
                        "nd": sum(a["gap"] for a in p if not a["far"]),
                        "any": len(p) / len(sub) if sub else 0,
                        "med": qtl([a["gap"] for a in p], .5),
                        "mdur": qtl([a["dur"] for a in sub], .5),
                        "room": qtl([max(CAP - a["dur"], 0) for a in sub], .5)})
        return out
    s["bands"] = bandrow(dur)
    s["bands_nova"] = bandrow([a for a in dur if "Veterans" not in a["ag"]])
    s["va_share_dur"] = sum(1 for a in dur if "Veterans" in a["ag"]) / len(dur)

    def group(field, minn=500):
        acc2 = collections.defaultdict(list)
        for a in rows:
            acc2[a[field]].append(a)
        out = []
        for k, v in acc2.items():
            if len(v) < minn:
                continue
            p = [x for x in v if x["gap"] > 0]
            out.append({"k": k, "n": len(v), "any": len(p) / len(v),
                        "med": qtl([x["gap"] for x in p], .5),
                        "optdays": sum(x["gap"] for x in p if not x["far"])})
        out.sort(key=lambda d: -d["n"])
        return out
    s["ag"] = group("ag")
    s["aty"] = group("aty")

    ba = collections.defaultdict(lambda: collections.defaultdict(list))
    for a in rows:
        c = COMP.get(a["cmp"])
        if c is not None:
            ba[a["ag"]][c].append(a)
    cmp_rows = []
    for ag, dd in ba.items():
        c, nc = dd.get(1, []), dd.get(0, [])
        if len(c) < 500 or len(nc) < 500:
            continue
        sc = sum(1 for a in c if a["gap"] > 0) / len(c)
        sn = sum(1 for a in nc if a["gap"] > 0) / len(nc)
        se = math.sqrt(sc * (1 - sc) / len(c) + sn * (1 - sn) / len(nc))
        cmp_rows.append({"k": SHORT.get(ag, ag), "nc": len(c), "nn": len(nc),
                         "d": 100 * (sc - sn), "ci": 196 * se})
    cmp_rows.sort(key=lambda d: -d["d"])
    s["cmp"] = cmp_rows

    # The linear summary, kept because it is the one a reader would reach for and it is
    # wrong here: a point-biserial near zero across a shape that rises then collapses.
    def corr(xs, ys):
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        cv = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        dn = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
        return cv / dn if dn else 0.0
    s["r_any"] = corr([math.log10(max(a["dur"], 1)) for a in dur],
                      [1.0 if a["gap"] > 0 else 0.0 for a in dur])
    gp2 = [a for a in dur if a["gap"] > 0]
    s["r_size"] = corr([math.log10(max(a["dur"], 1)) for a in gp2],
                       [math.log10(a["gap"]) for a in gp2])

    far = [a for a in pos if a["far"]]
    s["far_n"] = len(far)
    s["far_days"] = sum(a["gap"] for a in far)
    s["far_year"] = max((int(a["po"][:4]) for a in far), default=0)
    s["optdays"] = sum(a["gap"] for a in pos if not a["far"])
    s["obl_slack"] = qtl([a["ob"] for a in pos], .5)
    s["obl_none"] = qtl([a["ob"] for a in rows if a["gap"] == 0], .5)
    return s


def load_year(y):
    src = os.path.join(DATA, f"civilian-fy{y}.zip")
    cache = os.path.join(DATA, f"schedule-civilian-fy{y}.json")
    if os.path.exists(cache):
        return json.load(open(cache))
    if not os.path.exists(src):
        raise SystemExit(f"  civilian-fy{y}.zip missing — run usa2.py")
    print(f"  folding {os.path.basename(src)} ...", flush=True)
    s = fold(src)
    tmp = cache + ".tmp"
    json.dump(s, open(tmp, "w"))
    os.replace(tmp, cache)
    return s


def nlines(s, chars):
    n, line = 1, []
    for w in str(s).split():
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            line, n = [], n + 1
        line.append(w)
    return n


def step(pts, x, y, col, width, dash=None):
    """Band estimates as a step: thick where the estimate holds, thin where it changes.

    Not a line through points. Each estimate is flat across the band it was measured on,
    and the connectors are hairlines so the eye does not read a trend between two bands
    that were never measured together.
    """
    out, prev = [], None
    d = f' stroke-dasharray="{dash}"' if dash else ""
    for lo, hi, v in pts:
        x1, x2 = x(max(lo, 1)), x(hi)
        if prev is not None:
            out.append(f'<line x1="{x1:.1f}" y1="{y(prev):.1f}" x2="{x1:.1f}" '
                       f'y2="{y(v):.1f}" stroke="{col}" stroke-width="0.8" '
                       f'stroke-opacity="0.55"/>')
        out.append(f'<line x1="{x1:.1f}" y1="{y(v):.1f}" x2="{x2:.1f}" y2="{y(v):.1f}" '
                   f'stroke="{col}" stroke-width="{width}"{d}/>')
        prev = v
    return out

