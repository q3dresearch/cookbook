#!/usr/bin/env python3
"""Bigger trials get reported. Only if industry runs them.

    python3 chart-9-size.py

Enrollment is the register's one real sample-size field, populated on **98.8%** of studies,
and it is the obvious thing to test against reporting. Pooled, it produces a U: **31.7%** of
trials enrolling 1-10 report within three years, falling to **20.8%** at 51-100, rising to
**38.4%** at 501-1,000, then falling again to **26.0%** above 5,000.

**A U-shape invites a story and there is no U.** Split by sponsor class and the two halves of
the register point in opposite directions. Industry rises monotonically with size, **36.7% to
68.6%** -- a bigger trial is a more reported trial, every step of the way. University and
hospital sponsors do the reverse, drifting **29.6% down to 16.1%**. The pooled curve is
neither; it is the mixing ratio changing, because the industry share of trials rises with
size and industry reports three times as often.

**So sample size is not a property of the trial here.** It is a proxy for who is running it,
and it stops predicting anything the moment that is held fixed -- for one of the two classes
it reverses. Any model that puts enrollment in without the sponsor is fitting composition.

**Two things the field cannot bear without care.** Enrollment spans **eight orders of
magnitude**, from 0 to a recorded 188,814,085, so it must be logged before it enters anything
and its top end contains values no trial has. And 35% of the numbers are `ESTIMATED` --
a plan, not a measurement -- which is why only ACTUAL completions are used here.

**Zero is a real category, not a missing value.** 16,750 studies record zero participants and
2,511 of them fall in this window; **not one reports results**, which is correct rather than
delinquent. They are drawn because leaving them out would quietly raise every other number.
"""
import collections, csv, datetime, gzip, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                            # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID         # noqa: E402

ROWS = os.path.join(HERE, "..", "data", "studies.csv.gz")
OUT = os.path.join(HERE, "..", "charts", "9-size.svg")
TODAY = datetime.date(2026, 9, 22)
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
BANDS = [(1, 11, "1–10", 3), (11, 26, "11–25", 17), (26, 51, "26–50", 37),
         (51, 101, "51–100", 72), (101, 251, "101–250", 160), (251, 501, "251–500", 355),
         (501, 1001, "501–1k", 710), (1001, 5001, "1k–5k", 2200),
         (5001, 10 ** 9, "5k+", 9000)]


def parse(d):
    if not d:
        return None
    try:
        if len(d) == 7:
            return datetime.date(int(d[:4]), int(d[5:7]), 15)
        if len(d) == 10:
            return datetime.date(int(d[:4]), int(d[5:7]), int(d[8:10]))
    except ValueError:
        pass
    return None


def main():
    try:
        with gzip.open(ROWS, "rt", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except EOFError:
        raise SystemExit("  studies.csv.gz is truncated — re-run ctg2.py")
    pop, allen = [], []
    for r in rows:
        try:
            n = int(r["enrollment"])
        except (ValueError, TypeError):
            n = None
        if n is not None:
            allen.append(n)
        if r["study_type"] != "INTERVENTIONAL" or r["primary_completion_type"] != "ACTUAL":
            continue
        if (r["phases"] or "") in ("PHASE1", "EARLY_PHASE1", "EARLY_PHASE1|PHASE1"):
            continue
        pc = parse(r["primary_completion"])
        if not pc or not (2012 <= pc.year <= 2021) or n is None:
            continue
        rs = parse(r["results_submit"])
        pop.append({"n": n, "lag": (rs - pc).days if rs else None,
                    "fu": (TODAY - pc).days, "sp": r["sponsor_class"] or "?"})

    def share(P, floor=100):
        ar = [p for p in P if p["fu"] >= 1095]
        if len(ar) < floor:
            return None, len(ar)
        return sum(1 for p in ar if p["lag"] is not None and p["lag"] <= 1095) / len(ar), len(ar)

    series = {"pooled": [], "INDUSTRY": [], "OTHER": []}
    for lo, hi, lab, mid in BANDS:
        B = [p for p in pop if lo <= p["n"] < hi]
        for key in series:
            P = B if key == "pooled" else [p for p in B if p["sp"] == key]
            v, n = share(P, 150 if key == "pooled" else 100)
            if v is not None:
                series[key].append((mid, v, n, lab))
    zero, zn = share([p for p in pop if p["n"] == 0], 150)

    W, H = 1200, 820
    s = plate.open_svg(W, H, "Bigger trials get reported. Only if industry runs them.")
    fr, _ = plate.frame(W, 62,
                        who="anyone putting trial size into a model of reporting",
                        decide="whether sample size is a property of the trial or of its "
                               "sponsor",
                        wrong="the two classes bend the same way as the pooled curve")
    s += fr

    AX, AY, AH, AW = 28, 176, 420, 700
    x0, pw = AX + 50, AW - 96
    lo_, hi_ = 2, 12000
    px = lambda v: x0 + pw * ((math.log10(max(v, lo_)) - math.log10(lo_))
                              / (math.log10(hi_) - math.log10(lo_)))
    py = lambda f: AY + AH - 58 - (AH - 92) * (f / 0.75)
    for f in (0, .2, .4, .6):
        s.append(f'<line x1="{x0:.1f}" y1="{py(f):.1f}" x2="{px(hi_):.1f}" '
                 f'y2="{py(f):.1f}" stroke="{GRID}"/>')
        s.append(txt(x0 - 8, py(f) + 3, f"{f:.0%}", size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, AY - 18, "share reporting results within three years", size=11,
                 fill=INK2))
    for v_, lab in ((10, "10"), (100, "100"), (1000, "1,000"), (10000, "10,000")):
        s.append(f'<line x1="{px(v_):.1f}" y1="{py(0):.1f}" x2="{px(v_):.1f}" '
                 f'y2="{py(0)+5:.1f}" stroke="{MUTED}"/>')
        s.append(txt(px(v_), py(0) + 18, lab, size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, py(0) + 36, "participants enrolled (log scale)", size=10, fill=MUTED))

    STYLE = {"pooled": (INK, "pooled — neither curve", "5 3", 2.8),
             "INDUSTRY": (GREEN, "industry", "", 2.6),
             "OTHER": (BLUE, "university, hospital", "", 2.6)}
    for key, (col, lab, dash, wdt) in STYLE.items():
        pts = [(px(m), py(v)) for m, v, n, _ in series[key]]
        if len(pts) < 3:
            continue
        s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                        for i, (a, b) in enumerate(pts))
                 + f'" fill="none" stroke="{col}" stroke-width="{wdt}"'
                 + (f' stroke-dasharray="{dash}"' if dash else "") + '/>')
        for a, b in pts:
            s.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3.4" fill="{col}"/>')
        s += halo(pts[-1][0] + 8, pts[-1][1] + 3, lab, size=10.5, fill=col, weight="700")
        s += halo(pts[-1][0] + 8, pts[-1][1] + 15, f"{series[key][-1][1]:.1%}", size=9.5,
                  fill=col)
        s += halo(pts[0][0] - 8, pts[0][1] + 3, f"{series[key][0][1]:.1%}", size=9.5,
                  fill=col, anchor="end")
    if zero is not None:
        s.append(f'<circle cx="{px(lo_):.1f}" cy="{py(zero):.1f}" r="4.4" fill="none" '
                 f'stroke="{RED}" stroke-width="1.8"/>')
        s += halo(px(lo_) + 9, py(zero) - 8, f"{zn:,} trials enrolled nobody", size=9.5,
                  fill=RED, weight="700")
        s += halo(px(lo_) + 9, py(zero) + 3, "and none of them reported — correct, "
                                             "not delinquent", size=9, fill=RED)

    ty = AY + AH + 30
    s.append(txt(AX, ty, "the pooled U is the mixing ratio, not a relationship",
                 size=12.5, fill=INK, weight="600"))
    s += wrap(AX, ty + 20,
              "Industry rises monotonically with size and universities drift the other way, "
              "so the dashed pooled curve is neither. The industry share of trials climbs "
              "with enrollment and industry reports three times as often, which bends the "
              "average upward at the top and pulls it down in the middle. Sample size is not "
              "a property of the trial here — it is a proxy for who is running it, and it "
              "reverses sign for one of the two classes once that is held fixed.",
              size=11, fill=INK2, chars=88, leading=15)
    s += halo(AX + 790, ty + 2, "the field's own limits", size=11, fill=MUTED, weight="700")
    s += wrap(AX + 790, ty + 20,
              f"Enrollment spans eight orders of magnitude, 0 to a recorded "
              f"{max(allen):,}, so it is logged here and its top end holds values no trial "
              f"has. 35% of the numbers are ESTIMATED — a plan, not a measurement.",
              size=10.5, fill=INK2, chars=44, leading=14)

    fy = H - 24 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"ClinicalTrials.gov API v2, fetched 2026-09-22. Population as figure 3, "
              f"completions 2012–2021 with an enrollment recorded — {len(pop):,} trials. "
              f"Points sit at each band's midpoint on a log axis; the zero-enrollment group "
              f"cannot be placed on a log scale and is drawn hollow at the left margin. "
              f"Bands with under 150 trials pooled, or 100 within a class, are not drawn.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for key in series:
        f = series[key]
        print(f"    {key:<10}{f[0][3]:>8} {f[0][1]:.1%}  ->  {f[-1][3]:>6} {f[-1][1]:.1%}")
    print(f"    zero-enrollment: {zn:,} trials, {zero:.1%} reported")
    return 0


if __name__ == "__main__":
    sys.exit(main())
