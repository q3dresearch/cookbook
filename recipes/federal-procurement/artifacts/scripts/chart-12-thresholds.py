#!/usr/bin/env python3
"""Contract values bunch below the competition threshold, and the bunching moved when it did.

    python3 chart-12-thresholds.py

The simplified acquisition threshold was **$150,000 through FY2017 and $250,000 from FY2018**.
That gives a natural experiment for a pattern that is otherwise unprovable: award values
cluster just under the line above which a contract must be competed more heavily.

**A raw below-versus-above count proves nothing**, because contract values decline in frequency
as they grow -- more below is the null, not the finding. Each candidate value here gets a local
trend fitted on a +/-$60,000 window with the bins either side held out, and the excess is the
observed count in the two bins just below against what that trend predicts.

**The step is visible in the raw distribution, before any model.** The share of a year's
awards in the $10,000 bin just below its own threshold, over the share in the bin just above:

    year     rule      step below $150k    step below $250k
    FY2016   $150k           1.28x               1.11x
    FY2017   $150k           1.36x               1.09x
    FY2025   $250k           1.16x               1.34x

**Three years, three times the larger step sits on that year's own rule.** The fitted excess in
the right-hand panel exists because a reader cannot eyeball a 1.3x step against a background
that is already falling, not because the step needs a model to appear.

**Measured, the bunching follows the rule.** FY2017 peaks at **$150,000 (+29%)**, FY2025 at
**$250,000 (+37%)** while $150,000 falls to +5%. $150,000 is exactly as round a number in 2025
as it was in 2017, so roundness cannot explain a peak that packed up and moved.

**Why bars and not a line.** Each test uses a +/-$60,000 window, so candidate values $10,000
apart share about 92% of their data. A line would assert a continuous function through points
that are overlapping re-tests of the same awards; bars claim only what each test found.

**And the placebos stay flat.** Values with no rule behind them -- $200,000, $300,000, $350,000
-- sit within a few points of zero in every year, so the estimator is not manufacturing peaks
wherever it is pointed.

**One year does not cooperate on the fitted measure, and that is stated rather than hidden.**
FY2016 reaches +18% at its own threshold but ties it at $310,000, where no rule exists, so its
sweep peak is not identified and it is not drawn in either panel. Its *raw* step does point the
right way -- 1.28x at $150,000 against 1.11x at $250,000 -- which is why the raw table above
carries three years and the panels carry two.

**What this cannot show.** Whether any individual award was split to stay under the line. This
is a distribution-level result: the shape of the population moves with the rule. A single
contract at $249,000 is not evidence of anything, and nothing here identifies one.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate, thresh                                                     # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "12-thresholds.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
COL = {"2016": SLATE, "2017": BLUE, "2025": RED}
PLACEBO = (200000, 300000, 350000)


def main():
    d = thresh.load()
    ys = sorted(d["years"])
    grid = d["grid"]

    W, H = 1240, 772
    s = plate.open_svg(
        W, H,
        "Contract values bunch below the competition threshold, and the bunching moved "
        "when the threshold did",
        subtitle="The simplified acquisition threshold was $150,000 through FY2017 and "
                 "$250,000 from FY2018. Excess is measured against a locally fitted trend, "
                 "not against a flat line.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone deciding whether below-threshold clustering is a rule effect or a "
            "round-number habit",
        decide="whether to screen awards on their distance below the threshold in force "
               "that year",
        wrong="the peak stays at $150,000 after the rule moved, or the placebo values "
              "rise with it")
    s += fr

    # ---- panel A: the raw distribution, both years on one axis ---------------
    # The overlaid histogram is the evidence; the fitted excess in panel B is a way of
    # reading a 1.3x step against a declining background, not a substitute for seeing it.
    AX, AY, AW, AH = 64, y0 + 58, 556, 400
    w17, w25 = d["years"]["2017"]["wide"], d["years"]["2025"]["wide"]
    lo, binw = w17["lo"], w17["binw"]
    n = len(w17["share"])
    xhi = lo + n * binw
    ax = lambda v: AX + 58 + (AW - 76) * (v - lo) / (xhi - lo)
    smax = max(max(w17["share"]), max(w25["share"]))
    ay = lambda v: AY + AH - 44 - (AH - 60) * v / smax
    s.append(txt(AX - 36, AY - 34, "the raw distribution, both years on one axis",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(AX - 36, AY - 17, "share of each year's awards in the window, per $10,000 "
                                   "bin", size=10, fill=MUTED))
    for g in (0, 2, 4, 6, 8, 10):
        if g > smax:
            continue
        s.append(f'<line x1="{ax(lo):.1f}" y1="{ay(g):.1f}" x2="{ax(xhi):.1f}" '
                 f'y2="{ay(g):.1f}" stroke="{GRID}"/>')
        s.append(txt(ax(lo) - 8, ay(g) + 3, f"{g}%", size=9, fill=MUTED, anchor="end"))
    for v in (100000, 150000, 200000, 250000, 300000, 350000, 400000):
        s.append(txt(ax(v), ay(0) + 16, f"${v//1000}k", size=9, fill=MUTED,
                     anchor="middle"))
    s.append(txt(AX - 36, ay(0) + 34, "award value", size=9.5, fill=MUTED))
    s.append(f'<text x="{AX-16}" y="{ay(0):.1f}" font-size="9.5" fill="{INK2}" '
             f'transform="rotate(-90 {AX-16} {ay(0):.1f})">'
             f"share of that year's awards in this window</text>")
    for v in (150000, 250000):
        s.append(f'<line x1="{ax(v):.1f}" y1="{ay(0):.1f}" x2="{ax(v):.1f}" '
                 f'y2="{ay(smax):.1f}" stroke="{INK2}" stroke-width="1.2" '
                 f'stroke-dasharray="4 3"/>')
    for y, w in (("2017", w17), ("2025", w25)):
        pts = []
        for j, sh in enumerate(w["share"]):
            x0, x1 = ax(lo + j * binw), ax(lo + (j + 1) * binw)
            pts += [(x0, ay(sh)), (x1, ay(sh))]
        s.append('<path d="' + f"M{pts[0][0]:.1f},{ay(0):.1f} "
                 + " ".join(f"L{p:.1f},{q:.1f}" for p, q in pts)
                 + f" L{pts[-1][0]:.1f},{ay(0):.1f} Z\" fill=\"{COL[y]}\" "
                   f"fill-opacity=\"0.16\" stroke=\"none\"/>")
        s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{p:.1f},{q:.1f}"
                                        for i, (p, q) in enumerate(pts))
                 + f'" fill="none" stroke="{COL[y]}" stroke-width="1.8"/>')
    for y, rule, side in (("2017", 150000, -1), ("2025", 250000, 1)):
        st = d["years"][y][f"step_{rule//1000}k"]
        j = (rule - lo) // binw
        sh = d["years"][y]["wide"]["share"][j - 1]
        s += halo(ax(rule) + side * 8, ay(sh) - 8, f"FY{y}", size=10, fill=COL[y],
                  anchor="start" if side > 0 else "end", weight="700")
        s += halo(ax(rule) + side * 8, ay(sh) + 5,
                  f"{st:.2f}x the bin above", size=9.5, fill=COL[y],
                  anchor="start" if side > 0 else "end", weight="700")
    s += halo(ax(xhi) - 4, ay(smax * 0.92),
              "each year steps down at its own threshold", size=9.5, fill=INK2,
              anchor="end", weight="700")
    s += halo(ax(xhi) - 4, ay(smax * 0.92) + 13,
              "and runs smoothly past the other one", size=9.5, fill=INK2, anchor="end")

    # ---- panel B: the same thing measured, with placebos --------------------
    BX, BY, BW2, BH = 700, AY, 508, 400
    grid = d["grid"]
    bx = lambda v: BX + 58 + (BW2 - 76) * (v - grid[0]) / (grid[-1] - grid[0])
    elo, ehi = -20, 42
    by = lambda v: BY + BH - 44 - (BH - 60) * (max(min(v, ehi), elo) - elo) / (ehi - elo)
    s.append(txt(BX - 26, AY - 34, "the same step, fitted at every candidate value",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(BX - 26, AY - 17, "one bar per test; the windows overlap, so these are "
                                   "re-tests and not a curve", size=10, fill=MUTED))
    for g in (-20, -10, 0, 10, 20, 30, 40):
        s.append(f'<line x1="{bx(grid[0]):.1f}" y1="{by(g):.1f}" '
                 f'x2="{bx(grid[-1]):.1f}" y2="{by(g):.1f}" '
                 f'stroke="{RULE if g == 0 else GRID}"/>')
        s.append(txt(bx(grid[0]) - 8, by(g) + 3, f"{g:+d}%", size=9, fill=MUTED,
                     anchor="end"))
    for v in (100000, 150000, 200000, 250000, 300000, 350000, 400000):
        s.append(txt(bx(v), by(elo) + 16, f"${v//1000}k", size=9, fill=MUTED,
                     anchor="middle"))
    s.append(txt(BX - 26, by(elo) + 34, "candidate value being tested", size=9.5,
                 fill=MUTED))
    s.append(f'<text x="{BX-16}" y="{by(elo):.1f}" font-size="9.5" fill="{INK2}" '
             f'transform="rotate(-90 {BX-16} {by(elo):.1f})">'
             f'excess just below, against the local trend</text>')
    bw = (bx(grid[1]) - bx(grid[0])) * 0.40
    for k, y in enumerate(("2017", "2025")):
        for tv in grid:
            e = d["years"][y]["sweep"].get(str(tv))
            if not e:
                continue
            v = e["excess"]
            x = bx(tv) + (k - 0.5) * bw
            top, bot = by(max(v, 0)), by(min(v, 0))
            s.append(f'<rect x="{x-bw/2:.1f}" y="{top:.1f}" width="{bw:.1f}" '
                     f'height="{max(bot-top,0.6):.1f}" fill="{COL[y]}" '
                     f'fill-opacity="0.85"/>')
        r = d["rule"][y]
        e = d["years"][y]["at_rule"]["excess"]
        s += halo(bx(r), by(e) - 9, f"FY{y} {e:+.0f}%", size=9.5, fill=COL[y],
                  anchor="middle", weight="700")
    for v in PLACEBO:
        s.append(f'<line x1="{bx(v):.1f}" y1="{by(elo)+2:.1f}" x2="{bx(v):.1f}" '
                 f'y2="{by(elo)+7:.1f}" stroke="{MUTED}"/>')
    s += halo(bx(PLACEBO[1]), by(elo) + 30, "placebo values, no rule behind them",
              size=9, fill=MUTED, anchor="middle")
    lx = bx(330000)
    for k, y in enumerate(("2017", "2025")):
        s.append(f'<rect x="{lx:.1f}" y="{by(ehi)+4+k*14:.1f}" width="9" height="9" '
                 f'fill="{COL[y]}" fill-opacity="0.85"/>')
        s.append(txt(lx + 14, by(ehi) + 13 + k * 14,
                     f"FY{y}, rule ${d['rule'][y]//1000}k", size=9.5, fill=INK2))

    # Trimmed from the plate per doctrine/what-a-footnote-carries.md; kept here because it is method: f
    # oot = (USAspending API v2 bulk download; contract transactions for eleven civilian
    # departments, collapsed to awards on contract_award_unique_key and summed to a net
    # obligation, positive awards only. FY2016 {d['years']['2016']['n_positive']:,} , FY2017
    # {d['years']['2017']['n_positive']:,}, FY2025 {d['years']['2025']['n_positive']:,}.
    # Excess is the count in the two $5,000 bins below the tested value against an exponential
    # trend fitted on the rest of a +/-$60,000 window, with the two bins either side of the
    # value held out, so the estimate never sees the bunching it is measuring. A raw below-
    # against-above ratio is not used because the underlying density falls with size and would
    # give a positive reading everywhere. FY2016 reaches +18% at its own threshold and also
    # +18% at $310,000 where no rule exists, so its peak is not identified; FY2017 and FY2025
    # peak on their own rules. The threshold history is the FAR's, not inferred from the data.
    # This is a distribution-level result: it says the population's shape tracks the rule, and
    # it identifies no individual award as split. These eleven departments are 8.5% of federal
    # contract awards and Defense is 68.6%, so nothing here describes federal procurement as a
    # whole.)
    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2016, FY2017 and FY2025, "
        "positive awards only. The threshold history is the FAR's. CAVEAT: this is "
        "distribution-level -- the population's shape tracks the rule, and no individual "
        "award is identified as split. FY2016's peak is not identified and is not drawn. "
        "These eleven civilian departments are 8.5% of federal contract awards; Defense "
        "(68.6%) is absent, so this is not federal procurement as a whole.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=186, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=186, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for y in ys:
        g = d["years"][y]
        pk = max(((int(t), v["excess"]) for t, v in g["sweep"].items() if v),
                 key=lambda r: r[1])
        print(f"    FY{y} rule ${d['rule'][y]:,}: at-rule {g['at_rule']['excess']:+.1f}% "
              f"(obs {g['at_rule']['obs']:,} vs {g['at_rule']['exp']:,.0f}), "
              f"elsewhere {g['at_other']['excess']:+.1f}%, peak ${pk[0]:,} {pk[1]:+.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
