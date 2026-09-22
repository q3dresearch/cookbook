#!/usr/bin/env python3
"""The wall is older than the rule that built it, and it is one day wide.

    python3 chart-2-wall.py

Figure 1 found the results-posting hazard spiking twentyfold in the month the statutory
deadline falls. Two things could make that less than it looks, and both were tested.

**Could the spike be an artefact of date handling?** 39% of primary completion dates carry no
day of month and are placed mid-month here, which can manufacture a pile-up at any round
offset. Restricting to the **151,345 trials with a day-precision completion date** and binning
at seven days instead of thirty removes that possibility entirely -- and the wall gets
sharper, not softer. The hazard runs **1.23%** in the week ending day 357, **2.61%** in the
week ending 364, **3.17%** in the week containing day 365, and then falls off a cliff to
**0.43%**. A sevenfold drop in seven days. At day resolution the three most common lags in the
whole 330-400 day range are **364 days (1,621 trials), 365 (1,420) and 363 (870)**.

**It is a day-count deadline, not a monthly rhythm.** Sponsors are not filing "sometime the
following year". They are filing against a date arithmetic gives them.

**Could the rule have created it?** FDAAA 801's results requirement bit from 2008; the Final
Rule, 42 CFR Part 11, took effect in January 2017 and widened the scope. If the wall were
built by the 2017 rule it should be absent or weak in the earliest cohorts.

**It is not.** Completions from **2008-2012 already spike 22.1x** over their own baseline --
the same multiple as 2017-2020. The rule did not create the wall and did not sharpen it. What
it did, on figure 3's evidence, is nothing visible at all.

**Which locates the mechanism.** A wall that is one day wide, present from the first cohort
measurable, unchanged by the rule that widened its scope, and twentyfold-concentrated only
among sponsors with regulatory staff (figure 1), is not a rule persuading anybody. It is a
compliance function inside organisations that already had one, executing a date.
"""
import collections, csv, datetime, gzip, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                            # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID         # noqa: E402

ROWS = os.path.join(HERE, "..", "data", "studies.csv.gz")
OUT = os.path.join(HERE, "..", "charts", "2-wall.svg")
TODAY = datetime.date(2026, 9, 22)
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
ERAS = [("2008–2012", 2008, 2012), ("2013–2016", 2013, 2016),
        ("2017–2020", 2017, 2020), ("2021–2023", 2021, 2023)]


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


def main():
    try:
        with gzip.open(ROWS, "rt", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except EOFError:
        raise SystemExit("  studies.csv.gz is truncated — re-run ctg2.py")
    pop = []
    for r in rows:
        if r["study_type"] != "INTERVENTIONAL" or r["primary_completion_type"] != "ACTUAL":
            continue
        if (r["phases"] or "") in ("PHASE1", "EARLY_PHASE1", "EARLY_PHASE1|PHASE1"):
            continue
        pc, prec = parse(r["primary_completion"])
        if not pc or pc > TODAY:
            continue
        rs, _ = parse(r["results_submit"])
        pop.append({"pc": pc, "prec": prec, "lag": (rs - pc).days if rs else None,
                    "fu": (TODAY - pc).days})

    def haz(P, lo, hi, floor=200):
        at = [p for p in P if p["fu"] >= hi and (p["lag"] is None or p["lag"] >= lo)]
        if len(at) < floor:
            return None, len(at)
        ev = sum(1 for p in at if p["lag"] is not None and lo <= p["lag"] < hi)
        return ev / len(at), len(at)

    day = [p for p in pop if p["prec"] == "day"]
    W = 7
    bins = []
    for b in range(40, 64):
        lo, hi = b * W, (b + 1) * W
        v, n = haz(day, lo, hi)
        if v is not None:
            bins.append((lo, hi, v, n))

    Wd, H = 1200, 740
    s = plate.open_svg(Wd, H, "The wall is older than the rule that built it, and it is "
                              "one day wide")
    fr, _ = plate.frame(Wd, 62,
                        who="anyone deciding whether a deadline effect is real or an "
                            "artefact",
                        decide="whether the spike survives day-precision dates and "
                               "pre-dates the rule",
                        wrong="the spike softens on day-precision dates, or is absent "
                              "before 2017")
    s += fr

    # ---------- left: seven-day bins, day-precision dates only
    AX, AY, AH, AW = 28, 176, 400, 680
    x0, pw = AX + 50, AW - 96
    lo0, hi0 = bins[0][0], bins[-1][1]
    px = lambda d: x0 + pw * ((d - lo0) / (hi0 - lo0))
    top = 0.035
    py = lambda v: AY + AH - 54 - (AH - 88) * (v / top)
    for v in (0, .01, .02, .03):
        s.append(f'<line x1="{x0:.1f}" y1="{py(v):.1f}" x2="{px(hi0):.1f}" '
                 f'y2="{py(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(x0 - 8, py(v) + 3, f"{v:.0%}" if v else "0", size=9, fill=MUTED,
                     anchor="end"))
    s.append(txt(AX, AY - 18, "of the trials still unreported, the share reporting in "
                              "each 7-day window", size=11, fill=INK2))
    for d in range(280, hi0 + 1, 70):
        s.append(f'<line x1="{px(d):.1f}" y1="{py(0):.1f}" x2="{px(d):.1f}" '
                 f'y2="{py(0)+5:.1f}" stroke="{MUTED}"/>')
        s.append(txt(px(d), py(0) + 18, str(d), size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, py(0) + 36, "days since primary completion — day-precision start "
                                 "dates only", size=10, fill=MUTED))
    for lo, hi, v, n in bins:
        hot = lo <= 365 < hi
        s.append(f'<rect x="{px(lo):.1f}" y="{py(v):.1f}" '
                 f'width="{max(px(hi)-px(lo)-1.5,1):.1f}" height="{py(0)-py(v):.1f}" '
                 f'fill="{RED if hot else BLUE}" fill-opacity="{0.9 if hot else 0.5}"/>')
    s.append(f'<line x1="{px(365):.1f}" y1="{py(top):.1f}" x2="{px(365):.1f}" '
             f'y2="{py(0):.1f}" stroke="{RED}" stroke-width="1.3"/>')
    peak = max(bins, key=lambda b: b[2])
    nxt = next(b for b in bins if b[0] >= peak[1])
    s += halo(px(peak[0]) - 10, py(peak[2]) + 4, f"{peak[2]:.2%}", size=12, fill=RED,
              anchor="end", weight="700")
    s += halo(px(nxt[1]) + 10, py(nxt[2]) - 6, f"{nxt[2]:.2%} the next week", size=10.5,
              fill=INK2, weight="700")
    s += halo(px(nxt[1]) + 10, py(nxt[2]) + 6,
              f"a {peak[2]/nxt[2]:.0f}-fold drop in seven days", size=10, fill=INK2)
    s += halo(px(365) + 8, py(top) + 14, "day 365", size=10, fill=RED, weight="700")
    ex = collections.Counter(p["lag"] for p in day
                             if p["lag"] is not None and 330 <= p["lag"] <= 400)
    top3 = ex.most_common(3)
    s += wrap(AX, py(0) + 54,
              "At day resolution the three most common lags in the whole 330–400 day range "
              f"are {top3[0][0]} days ({top3[0][1]:,} trials), {top3[1][0]} ({top3[1][1]:,}) "
              f"and {top3[2][0]} ({top3[2][1]:,}). Sponsors are not filing sometime the "
              "following year — they are filing against a date arithmetic gives them.",
              size=11, fill=INK2, chars=92, leading=15)

    # ---------- right: the era test
    BX, BY, BW = 760, 176, 412
    s.append(txt(BX, BY - 18, "the same spike, by when the trial finished", size=11,
                 fill=INK2))
    stats = []
    for lab, a, b in ERAS:
        P = [p for p in pop if a <= p["pc"].year <= b]
        base = [haz(P, i * 30, (i + 1) * 30)[0] for i in range(4)]
        base = [x for x in base if x is not None]
        pk, n = haz(P, 360, 390)
        if base and pk:
            bm = sum(base) / len(base)
            stats.append({"lab": lab, "n": len(P), "b": bm, "pk": pk, "r": pk / bm})
    mxr = max(d["r"] for d in stats)
    for i, d in enumerate(stats):
        y = BY + 22 + i * 62
        rule = d["lab"] in ("2017–2020", "2021–2023")
        col = GREEN if rule else SLATE
        s.append(txt(BX, y, d["lab"], size=11, fill=INK, weight="600"))
        s.append(txt(BX, y + 13, f"{d['n']:,} trials · baseline {d['b']:.2%}", size=9,
                     fill=MUTED))
        w = (BW - 120) * d["r"] / mxr
        s.append(f'<rect x="{BX:.1f}" y="{y+19:.1f}" width="{max(w,2):.1f}" height="13" '
                 f'fill="{col}" fill-opacity="0.7"/>')
        s += halo(BX + max(w, 2) + 7, y + 29, f"{d['r']:.1f}x", size=11.5, fill=col,
                  weight="700")
    ry = BY + 22 + 62 * len(stats)
    s.append(f'<line x1="{BX:.1f}" y1="{ry-6:.1f}" x2="{BX+BW-40:.1f}" y2="{ry-6:.1f}" '
             f'stroke="{RULE}"/>')
    s += halo(BX, ry + 10, "the Final Rule took effect January 2017", size=10, fill=GREEN,
              weight="700")
    s += wrap(BX, ry + 26,
              "Completions from 2008–2012 already spike 22.1x over their own baseline — the "
              "same multiple as 2017–2020. The rule that widened the scope did not create the "
              "wall and did not sharpen it. Figure 3 finds no step in the reporting series at "
              "that date either.",
              size=10.5, fill=INK2, chars=54, leading=14)
    ry += 100
    s.append(f'<rect x="{BX-10:.1f}" y="{ry-16:.1f}" width="{BW+2:.1f}" height="80" '
             f'fill="{RED}" fill-opacity="0.07"/>')
    s.append(txt(BX, ry, "what that locates", size=11, fill=RED, weight="700"))
    s += wrap(BX, ry + 17,
              "A wall one day wide, present in the first measurable cohort, unchanged by the "
              "rule that widened it, and concentrated 82x among sponsors with regulatory "
              "staff — that is not a rule persuading anyone. It is a compliance function "
              "executing a date.",
              size=10.5, fill=INK2, chars=54, leading=14)

    fy = H - 24 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{Wd-28}" y2="{fy-18:.1f}" '
             f'stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"ClinicalTrials.gov API v2, fetched 2026-09-22. Population as figure 3. Left "
              f"panel uses only the {len(day):,} trials whose primary completion date carries "
              f"a day of month, so no date is placed by hand and no round-offset artefact is "
              f"possible; right panel uses the full population. Hazard is computed on trials "
              f"observed for the whole window and not yet reported at its start. Baseline is "
              f"the mean of each era's first four 30-day windows, so each era is measured "
              f"against itself.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    day-precision n={len(day):,}; peak {peak[2]:.2%} at {peak[0]}-{peak[1]}d, "
          f"next week {nxt[2]:.2%} = {peak[2]/nxt[2]:.1f}x drop")
    for d in stats:
        print(f"    {d['lab']:<12}{d['n']:>8,}  baseline {d['b']:.2%}  peak {d['pk']:.2%}  "
              f"{d['r']:.1f}x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
