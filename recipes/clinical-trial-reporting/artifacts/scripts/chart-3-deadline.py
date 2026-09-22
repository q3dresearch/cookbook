#!/usr/bin/env python3
"""Reporting sped up. It did not spread.

    python3 chart-3-deadline.py

FDAAA 801 gives a sponsor **12 months from the primary completion date** to submit summary
results. Both dates are in the register, so the gap is measured, not estimated.

**The deadline is powerfully salient** -- figure 1 measures it properly, as a hazard, and
finds a twentyfold spike in the month it falls.

**And it barely changes whether anyone reports at all.** With the non-reporters kept in the
denominator, the share of a completion-year cohort that has ever submitted results reaches
about **25% at three years, and has sat there for fifteen years**: 20.5% for 2008 completions,
25.2% for 2013, 24.1% for 2017, 24.5% for 2023. One-year reporting roughly tripled over the
same period, 5.5% to 14.7%. **The rule moved the reporters earlier; it did not recruit new
ones.** Neither the 2017 rule taking effect nor the first enforcement letters in 2021 leaves a
step in the series.

**Why this is a curve and not a histogram of lags.** A lag distribution can only contain
trials that eventually reported, and the worst offenders never did. Among reporters the median
lag is 458 days and 64% are past the deadline -- a statistic conditioned on its own outcome.
The left panel keeps every trial in the denominator forever, so a trial that never reports
drags the curve down instead of vanishing from it, and **the gap between each plateau and 100%
is the share that never reported**.

**The population is declared, and one obvious filter had to be thrown away.** The register has
no "applicable clinical trial" flag: ACT status under 42 CFR 11.22 is a legal determination,
not a field. The natural stand-in is the sponsor's own `isFdaRegulatedDrug`/`Device` answer,
and using it would have manufactured a finding -- that field's coverage runs **3.4% in 2010 to
98.5% in 2024**, and filtering on it turns this flat series into a rise from 9.4% to 28.3%.
That is a chart of a form field being rolled out. The base used here is the one whose
definition does not move: interventional, an ACTUAL primary completion date, not phase 1.
It is broader than the regulated population, so **no rate here is a rate of law-breaking**.
"""
import collections, csv, datetime, gzip, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                            # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID         # noqa: E402

ROWS = os.path.join(HERE, "..", "data", "studies.csv.gz")
OUT = os.path.join(HERE, "..", "charts", "3-deadline.svg")
TODAY = datetime.date(2026, 9, 22)
DEADLINE = 365
MIN_AT_RISK = 500
COHORTS = [2008, 2012, 2016, 2020, 2023]
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
SHADES = ["#a9b4bd", "#8aa2b6", "#5f87a6", "#33698f", "#14425f"]


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


def load():
    try:
        with gzip.open(ROWS, "rt", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except EOFError:
        raise SystemExit("  studies.csv.gz is truncated — re-run ctg2.py")


def population(rows):
    """Declared, not derived. Deliberately NOT filtered on isFdaRegulatedDrug/Device:
    that field's coverage runs 3.4% (2010) to 98.5% (2024), so filtering on it draws the
    field's rollout and calls it behaviour."""
    keep = []
    for r in rows:
        if r["study_type"] != "INTERVENTIONAL":
            continue
        if r["primary_completion_type"] != "ACTUAL":
            continue
        if (r["phases"] or "") in ("PHASE1", "EARLY_PHASE1", "EARLY_PHASE1|PHASE1"):
            continue
        pc, prec = parse(r["primary_completion"])
        if not pc or pc > TODAY:
            continue
        rs, _ = parse(r["results_submit"])
        keep.append({"pc": pc, "prec": prec, "lag": (rs - pc).days if rs else None,
                     "fu": (TODAY - pc).days})
    return keep


def incidence(pop, grid):
    out = []
    for t in grid:
        ar = [p for p in pop if p["fu"] >= t]
        if len(ar) < MIN_AT_RISK:
            break
        out.append((t, sum(1 for p in ar if p["lag"] is not None and p["lag"] <= t) / len(ar)))
    return out


def main():
    rows = load()
    pop = population(rows)
    by = collections.defaultdict(list)
    for p in pop:
        by[p["pc"].year].append(p)
    grid = list(range(0, 2001, 20))

    W, H = 1200, 720
    s = plate.open_svg(W, H, "Reporting sped up. It did not spread.")
    fr, _ = plate.frame(W, 62,
                        who="anyone reading a reporting rate as a compliance rate",
                        decide="whether a deadline that visibly works is changing the outcome",
                        wrong="the cohort curves climb toward 100%, or the horizons move together")
    s += fr

    # ---------- left: cumulative incidence, non-reporters kept in
    AX, AY, AH, AW = 28, 156, 500, 620
    x0, pw = AX + 46, AW - 92
    px = lambda t: x0 + pw * (t / 2000)
    py = lambda f: AY + AH - 56 - (AH - 90) * f
    s.append(txt(AX, AY - 18, "share of the completion-year cohort that has ever submitted "
                              "results", size=11, fill=INK2))
    for f in (0, .25, .5, .75, 1.0):
        s.append(f'<line x1="{x0:.1f}" y1="{py(f):.1f}" x2="{px(2000):.1f}" y2="{py(f):.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(x0 - 8, py(f) + 3, f"{f:.0%}", size=9, fill=MUTED, anchor="end"))
    for t in range(0, 2001, 365):
        s.append(f'<line x1="{px(t):.1f}" y1="{py(0):.1f}" x2="{px(t):.1f}" '
                 f'y2="{py(0)+5:.1f}" stroke="{MUTED}"/>')
        s.append(txt(px(t), py(0) + 18, f"{t:,}", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, py(0) + 36, "days since the primary completion date — the statutory "
                                 "clock starts here", size=10, fill=MUTED))
    s.append(f'<rect x="{px(DEADLINE-15):.1f}" y="{py(1.0):.1f}" '
             f'width="{px(DEADLINE+15)-px(DEADLINE-15):.1f}" height="{py(0)-py(1.0):.1f}" '
             f'fill="{RED}" fill-opacity="0.14"/>')
    s += halo(px(DEADLINE) + 9, py(0.97), "the 12-month deadline, drawn ±15 days",
              size=10, fill=RED, weight="700")
    s += halo(px(DEADLINE) + 9, py(0.97) + 12, "because 39% of start dates carry no day",
              size=9, fill=RED)

    ends = []
    for i, y in enumerate(COHORTS):
        pts = incidence(by.get(y, []), grid)
        if len(pts) < 3:
            continue
        col = SHADES[i]
        s.append('<path d="' + " ".join(("M" if j == 0 else "L") + f"{px(t):.1f},{py(f):.1f}"
                                        for j, (t, f) in enumerate(pts))
                 + f'" fill="none" stroke="{col}" stroke-width="2.6"/>')
        ends.append((pts[-1][0], pts[-1][1], y, col, len(by[y])))
    ends.sort(key=lambda e: e[1])
    last = None
    for t_end, f_end, y, col, n in ends:
        yy = py(f_end) + 3
        if last is not None and abs(yy - last) < 13:
            yy = last - 13
        last = yy
        s += halo(px(t_end) + 7, yy, f"completed {y}  ({n:,})", size=10, fill=col,
                  weight="700")

    # the gap that is the finding
    gx = px(1820)
    s.append(f'<line x1="{gx:.1f}" y1="{py(0.255):.1f}" x2="{gx:.1f}" y2="{py(1.0):.1f}" '
             f'stroke="{RED}" stroke-width="1.4" stroke-dasharray="3 3"/>')
    s += halo(gx - 8, py(0.62), "about three quarters of every cohort", size=10.5, fill=RED,
              anchor="end", weight="700")
    s += halo(gx - 8, py(0.62) + 13, "has never submitted results at all", size=10.5,
              fill=RED, anchor="end", weight="700")
    s += halo(gx - 8, py(0.62) + 27, "and that has not moved in fifteen years",
              size=9.5, fill=MUTED, anchor="end")

    # ---------- right: the horizons, which is what "flat" actually means
    BX, BY, BH, BW = 780, 156, 330, 392
    s.append(txt(BX, BY - 18, "share of each completion-year cohort reporting by each "
                              "horizon", size=11, fill=INK2))
    hx0, hpw = BX + 40, BW - 132
    yrs = [y for y in range(2008, 2025) if len(by.get(y, [])) > 2000]
    hpx = lambda y: hx0 + hpw * ((y - yrs[0]) / (yrs[-1] - yrs[0]))
    hpy = lambda f: BY + BH - 44 - (BH - 74) * (f / 0.36)
    for f in (0, .1, .2, .3):
        s.append(f'<line x1="{hx0:.1f}" y1="{hpy(f):.1f}" x2="{hpx(yrs[-1]):.1f}" '
                 f'y2="{hpy(f):.1f}" stroke="{GRID}"/>')
        s.append(txt(hx0 - 7, hpy(f) + 3, f"{f:.0%}", size=9, fill=MUTED, anchor="end"))
    for y in range(2010, 2025, 5):
        s.append(txt(hpx(y), hpy(0) + 17, str(y), size=9, fill=MUTED, anchor="middle"))
    s.append(txt(BX, hpy(0) + 34, "year the trial's primary completion fell", size=9.5,
                 fill=MUTED))
    HOR = [(1825, "within 5 years", "#14425f"), (1095, "within 3 years", "#33698f"),
           (730, "within 2 years", "#6f93ad"), (365, "within 1 year", RED)]
    for t, lab, col in HOR:
        pts = [(hpx(y), hpy(v)) for y in yrs
               for v in [incidence(by[y], [t])] if v for v in [v[0][1]]]
        pts = []
        for y in yrs:
            r_ = incidence(by[y], [t])
            if r_:
                pts.append((hpx(y), hpy(r_[0][1])))
        if len(pts) < 3:
            continue
        s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a_:.1f},{b_:.1f}"
                                        for i, (a_, b_) in enumerate(pts))
                 + f'" fill="none" stroke="{col}" stroke-width="2.2"/>')
        for a_, b_ in pts:
            s.append(f'<circle cx="{a_:.1f}" cy="{b_:.1f}" r="2.4" fill="{col}"/>')
        s += halo(pts[-1][0] + 6, pts[-1][1] + 3, lab, size=9.5, fill=col, weight="700")

    cy = BY + BH + 24
    s.append(txt(BX, cy, "sped up, not recruited", size=12, fill=INK, weight="600"))
    s += wrap(BX, cy + 18,
              "One-year reporting roughly tripled, 5.5% to 14.7%. Three-year reporting has "
              "not moved since 2008 and five-year reporting fell. The rule pulled forward "
              "the sponsors who were going to report anyway and added almost nobody.",
              size=10.5, fill=INK2, chars=54, leading=14)
    fy = H - 24 - 14 * 4
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"ClinicalTrials.gov API v2, fetched 2026-09-22, all {len(rows):,} registered "
              f"studies walked in one pass. Population: interventional, an ACTUAL primary "
              f"completion date, not phase 1 — {len(pop):,} studies. This is broader than the "
              f"set FDAAA 801 actually binds: the register carries no applicable-clinical-trial "
              f"flag, and two of the statute's four tests cannot be applied here at all, since "
              f"IND/IDE status is never published and the US-site criterion needs a location "
              f"field not fetched. So no rate on this plate is a rate of law-breaking; it is "
              f"reporting behaviour in a stable population. Curves stop where a cohort's "
              f"follow-up runs out or its denominator falls below {MIN_AT_RISK}.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    population {len(pop):,} of {len(rows):,}")
    for y in COHORTS:
        pts = dict(incidence(by.get(y, []), [365, 1095]))
        print(f"    completed {y}: {pts.get(365, 0):.1%} by 1y, "
              + (f"{pts[1095]:.1%} by 3y" if 1095 in pts else "3y not reached"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
