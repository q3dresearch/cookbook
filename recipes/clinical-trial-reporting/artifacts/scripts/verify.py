#!/usr/bin/env python3
"""Recompute every number this recipe leans on, and catch a figure that has gone stale.

    python3 verify.py

**Why this exists.** Twelve figures and a README share the same facts, and a sentence that was
right when written goes wrong silently. Building this recipe that happened five times: a
reporting trend that was a form field's rollout, a "flat for fifteen years" claim whose first
cohort was 20.5% rather than 25%, two multi-line annotations rendered bottom-to-top, a Unicode
arrow that shipped as an empty box, and a docstring describing a panel that had been replaced.
Three of the five were caught by recomputation.

If a number here disagrees with the README, **this script is authoritative and the prose is a
bug**, per the repo's own rule.
"""
import collections, csv, datetime, glob, gzip, math, os, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
CHARTS = os.path.join(HERE, "..", "charts")
TODAY = datetime.date(2026, 9, 22)
FAILED = []


def chk(label, claimed, actual, tol=0.0):
    ok = abs(claimed - actual) <= tol if tol else claimed == actual
    print(f"  {'ok  ' if ok else 'FAIL'}  {label:<52} README {claimed!s:>11}   "
          f"computed {actual!s:>11}")
    if not ok:
        FAILED.append(label)


def parse(d):
    if not d:
        return None, None
    try:
        if len(d) == 7:
            return datetime.date(int(d[:4]), int(d[5:7]), 15), "month"
        if len(d) == 10:
            return datetime.date(int(d[:4]), int(d[5:7]), int(d[8:10])), "day"
    except ValueError:
        pass
    return None, None


def load(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        raise SystemExit(f"  {name} missing — run the ctg*.py walks first")
    try:
        with gzip.open(p, "rt", newline="", encoding="utf-8") as f:
            return {r["nct_id"]: r for r in csv.DictReader(f)}
    except EOFError:
        raise SystemExit(f"  {name} is truncated — re-run its walk to finish")


def main():
    mn = load("studies.csv.gz")
    ex = load("extra.csv.gz")
    nmf = os.path.join(DATA, "names.csv.gz")

    print("\nthe register")
    chk("total studies walked", 603730, len(mn))
    st = collections.Counter(r["status"] for r in mn.values())
    chk("UNKNOWN studies", 96931, st["UNKNOWN"])
    chk("COMPLETED studies", 329839, st["COMPLETED"])
    chk("TERMINATED studies", 34352, st["TERMINATED"])
    chk("WITHDRAWN studies", 16791, st["WITHDRAWN"])
    prec = collections.Counter(parse(r["primary_completion"])[1]
                               for r in mn.values() if r["primary_completion"])
    chk("primary completion, month-precision (%)", 39.3,
        round(prec["month"] / sum(prec.values()) * 100, 1))
    pt = collections.Counter(r["primary_completion_type"] for r in mn.values())
    chk("primary completion ACTUAL", 370668, pt["ACTUAL"])
    chk("hasResults vs a results date, disagreements", 0,
        sum(1 for r in mn.values()
            if (r["has_results"] == "true") != bool(r["results_submit"])))

    # the population every figure shares
    pop = []
    for k, r in mn.items():
        if r["study_type"] != "INTERVENTIONAL" or r["primary_completion_type"] != "ACTUAL":
            continue
        if (r["phases"] or "") in ("PHASE1", "EARLY_PHASE1", "EARLY_PHASE1|PHASE1"):
            continue
        pc, pr = parse(r["primary_completion"])
        if not pc or pc > TODAY:
            continue
        rs, _ = parse(r["results_submit"])
        fp, _ = parse(r["first_post"])
        pop.append({"nct": k, "pc": pc, "prec": pr, "fp": fp,
                    "lag": (rs - pc).days if rs else None, "fu": (TODAY - pc).days,
                    "sp": r["sponsor_class"] or "?", "stt": r["status"],
                    "en": int(r["enrollment"]) if (r["enrollment"] or "").isdigit() else None})
    chk("shared population", 253429, len(pop))

    def share(P, t=1095, floor=100):
        ar = [p for p in P if p["fu"] >= t]
        if len(ar) < floor:
            return None
        return sum(1 for p in ar if p["lag"] is not None and p["lag"] <= t) / len(ar)

    def haz(P, lo, hi, floor=200):
        at = [p for p in P if p["fu"] >= hi and (p["lag"] is None or p["lag"] >= lo)]
        if len(at) < floor:
            return None
        return sum(1 for p in at if p["lag"] is not None and lo <= p["lag"] < hi) / len(at)

    print("\nI — the wall (figure 1)")
    base = sum(haz(pop, i * 30, (i + 1) * 30) for i in range(4)) / 4
    chk("baseline hazard a month (%)", 0.23, round(base * 100, 2))
    chk("deadline-window hazard (%)", 4.59, round(haz(pop, 360, 390) * 100, 2))
    chk("the month after (%)", 1.25, round(haz(pop, 390, 420) * 100, 2))
    chk("deadline / baseline", 20, round(haz(pop, 360, 390) / base))
    for sp, claim in (("INDUSTRY", 82), ("OTHER", 9), ("OTHER_GOV", 1.4)):
        P = [p for p in pop if p["sp"] == sp]
        b = sum(haz(P, i * 30, (i + 1) * 30, 150) for i in range(4)) / 4
        r = haz(P, 360, 390, 150) / b
        chk(f"{sp} spike vs own baseline", claim, round(r, 1) if claim < 10 else round(r),
            0.6 if claim < 10 else 1)

    print("\nII — older than the rule, one day wide (figure 2)")
    day = [p for p in pop if p["prec"] == "day"]
    chk("day-precision population", 151345, len(day))
    pk = haz(day, 364, 371)
    nx = haz(day, 371, 378)
    chk("day-precision peak week (%)", 3.17, round(pk * 100, 2))
    chk("the week after (%)", 0.43, round(nx * 100, 2))
    chk("drop across one week", 7.4, round(pk / nx, 1), 0.15)
    ex_lag = collections.Counter(p["lag"] for p in day
                                 if p["lag"] is not None and 330 <= p["lag"] <= 400)
    top = ex_lag.most_common(3)
    chk("most common exact lag (days)", 364, top[0][0])
    chk("trials at that exact lag", 1621, top[0][1])
    for lab, a, b, claim in (("2008-2012", 2008, 2012, 22.1), ("2017-2020", 2017, 2020, 22.1)):
        P = [p for p in pop if a <= p["pc"].year <= b]
        bb = sum(haz(P, i * 30, (i + 1) * 30) for i in range(4)) / 4
        chk(f"{lab} spike vs own baseline", claim, round(haz(P, 360, 390) / bb, 1), 0.1)

    print("\nIII — sped up, not spread (figure 3)")
    by = collections.defaultdict(list)
    for p in pop:
        by[p["pc"].year].append(p)
    for y, c1, c3 in ((2008, 5.5, 20.5), (2016, 11.6, 25.7), (2023, 12.8, 24.5)):
        chk(f"{y} completions, by 1 year (%)", c1, round(share(by[y], 365, 500) * 100, 1))
        chk(f"{y} completions, by 3 years (%)", c3, round(share(by[y], 1095, 500) * 100, 1))

    print("\nIV — sponsor classes (figure 4)")
    win = [p for p in pop if 2015 <= p["pc"].year <= 2021]
    chk("pooled 3-year rate (%)", 24.6, round(share(win, 1095, 500) * 100, 1))
    for sp, claim in (("NIH", 83.1), ("INDUSTRY", 50.0), ("OTHER", 17.1), ("OTHER_GOV", 3.3)):
        chk(f"{sp} 3-year rate (%)", claim,
            round(share([p for p in win if p["sp"] == sp], 1095, 150) * 100, 1))
    chk("OTHER share of the window (%)", 75,
        round(sum(1 for p in win if p["sp"] == "OTHER") / len(win) * 100))

    print("\nV — UNKNOWN is a timer (figure 5)")
    cy = collections.defaultdict(collections.Counter)
    for r in mn.values():
        d, _ = parse(r["first_post"])
        if d:
            cy[d.year][r["status"]] += 1
    for y, claim in ((2005, 8.4), (2023, 27.1), (2025, 0.3), (2026, 0.0)):
        t = sum(cy[y].values())
        chk(f"{y} cohort, UNKNOWN (%)", claim, round(cy[y]["UNKNOWN"] / t * 100, 1))

    print("\nVI — two duties (figure 6)")
    withfp = [p for p in pop if p["fp"]]
    byy = collections.defaultdict(list)
    for p in withfp:
        byy[p["pc"].year].append(p)
    rates = [sum(1 for p in byy[y] if p["fp"] > p["pc"]) / len(byy[y])
             for y in range(2008, 2025) if len(byy[y]) > 2000]
    chk("retrospective band low (%)", 18.1, round(min(rates) * 100, 1))
    chk("retrospective band high (%)", 23.6, round(max(rates) * 100, 1))
    for sp, a, b in (("INDUSTRY", 51.1, 17.2), ("OTHER", 20.8, 4.2)):
        P = [p for p in withfp if p["sp"] == sp and 2012 <= p["pc"].year <= 2021]
        chk(f"{sp} prospective 3-year (%)", a,
            round(share([p for p in P if p["fp"] <= p["pc"]], 1095, 150) * 100, 1))
        chk(f"{sp} retrospective 3-year (%)", b,
            round(share([p for p in P if p["fp"] > p["pc"]], 1095, 150) * 100, 1))

    print("\nVII — stopped early (figure 7)")
    w2 = [p for p in pop if 2012 <= p["pc"].year <= 2021]
    for stt, claim in (("COMPLETED", 24.3), ("TERMINATED", 37.9)):
        chk(f"{stt} 3-year rate (%)", claim,
            round(share([p for p in w2 if p["stt"] == stt], 1095, 120) * 100, 1))
    for stt, claim in (("COMPLETED", 16.4), ("TERMINATED", 31.6)):
        chk(f"OTHER, {stt} (%)", claim,
            round(share([p for p in w2 if p["stt"] == stt and p["sp"] == "OTHER"],
                        1095, 120) * 100, 1))

    print("\nVIII — lead time and scale (figure 8)")
    cnt = collections.Counter(mn[p["nct"]]["sponsor_name"] for p in w2)
    for lab, lo, hi, claim in (("1", 1, 2, 19.0), ("6-20", 6, 21, 17.6),
                               ("101-500", 101, 501, 30.9), ("501+", 501, 10**9, 50.0)):
        P = [p for p in w2 if lo <= cnt[mn[p["nct"]]["sponsor_name"]] < hi]
        chk(f"sponsor runs {lab} trials (%)", claim, round(share(P, 1095, 120) * 100, 1))

    print("\nIX — sample size (figure 9)")
    for sp, lo, hi, claim in (("INDUSTRY", 1, 11, 36.7), ("INDUSTRY", 5001, 10**9, 68.6),
                              ("OTHER", 1, 11, 29.6), ("OTHER", 5001, 10**9, 16.1)):
        P = [p for p in w2 if p["sp"] == sp and p["en"] is not None and lo <= p["en"] < hi]
        chk(f"{sp} {lo}-{hi if hi < 10**9 else '+'} enrolled (%)", claim,
            round(share(P, 1095, 100) * 100, 1))

    print("\nX — the statutory scope (figure 10)")
    REG = {"DRUG", "BIOLOGICAL", "DEVICE", "COMBINATION_PRODUCT", "GENETIC", "RADIATION"}
    Q = []
    for p in w2:
        e = ex.get(p["nct"])
        if not e or not e["itypes"] or not e["countries"]:
            continue
        Q.append({**p, "reg": bool(set(e["itypes"].split("|")) & REG),
                  "us": "United States" in e["countries"]})
    chk("scope population", 120984, len(Q))
    cells = {}
    for reg in (True, False):
        for us in (True, False):
            cells[(reg, us)] = share([p for p in Q if p["reg"] == reg and p["us"] == us],
                                     1095, 150)
    for (reg, us), claim in (((True, True), 67.1), ((True, False), 13.3),
                             ((False, True), 17.9), ((False, False), 3.4)):
        chk(f"reg={reg!s:<5} us={us!s:<5} (%)", claim, round(cells[(reg, us)] * 100, 1))
    chk("US-site effect among regulated", 5.0,
        round(cells[(True, True)] / cells[(True, False)], 1), 0.1)
    chk("US-site effect among everything else", 5.3,
        round(cells[(False, True)] / cells[(False, False)], 1), 0.1)

    print("\nXI — tempo (figure 11)")
    T = []
    for k, r in mn.items():
        e = ex.get(k)
        if not e or r["study_type"] != "INTERVENTIONAL":
            continue
        s0, _ = parse(e["start"])
        pc, _ = parse(r["primary_completion"])
        if not s0 or s0.year < 2000 or s0 > TODAY:
            continue
        d = ((pc - s0).days if pc and r["primary_completion_type"] == "ACTUAL" else None)
        T.append({"st": s0, "dur": d if (d is None or 0 < d < 7000) else None,
                  "ph": (r["phases"] or "NA").split("|")[0],
                  "en": int(r["enrollment"]) if (r["enrollment"] or "").isdigit() else None})
    chk("trials with a start date", 449259, len(T))
    fin = [t["dur"] for t in T if t["st"].year == 2024 and t["dur"]]
    chk("naive median duration, 2024 starts (d)", 243, round(statistics.median(fin)))

    def done(P, d, floor=300):
        ar = [p for p in P if (TODAY - p["st"]).days >= d]
        return (sum(1 for p in ar if p["dur"] is not None and p["dur"] <= d) / len(ar)
                if len(ar) >= floor else None)
    for y, claim in ((2008, 77), (2021, 64)):
        chk(f"{y} starts finished within 5 years (%)", claim,
            round(done([t for t in T if t["st"].year == y], 1825) * 100))
    for ph, claim in (("PHASE1", 37), ("PHASE2", 17)):
        P = [t for t in T if 2010 <= t["st"].year <= 2018 and t["ph"] == ph]
        chk(f"{ph} finished within 1 year (%)", claim, round(done(P, 365) * 100))

    print("\nXII — product keys (figure 12)")
    if os.path.exists(nmf):
        chk("names walk rows", 603730, len(load("names.csv.gz")))
    else:
        print("  ..    names.csv.gz absent — run ctg4.py to check figure 12's numbers")

    print("\nfigures newer than the scripts that draw them")
    stale = 0
    for scr in sorted(glob.glob(os.path.join(HERE, "chart-*.py"))):
        svg = os.path.join(CHARTS, os.path.basename(scr)[6:-3] + ".svg")
        if os.path.exists(svg) and os.path.getmtime(svg) < os.path.getmtime(scr):
            print(f"  FAIL  {os.path.basename(svg)} is older than its script")
            stale += 1
    if not stale:
        print("  ok    0 stale figure(s)")

    print(f"\n{len(FAILED)} disagreement(s) with the README"
          + (": " + ", ".join(FAILED) if FAILED else ""))
    return 1 if FAILED or stale else 0


if __name__ == "__main__":
    sys.exit(main())
