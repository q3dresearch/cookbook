#!/usr/bin/env python3
"""Southern has the best typical forecast hour in the country and a 36-fold tail.

    python3 chart-6-tail.py

Figure 5 scored each operator on average error against a naive baseline. An average is the
wrong statistic for a demand forecast, because the hours that matter operationally are the
ones in the tail -- the surprise, the peak, the hour nobody planned for. So this figure keeps
the two apart.

**The typical hour and the bad hour rank operators differently.** Southern Company's median
absolute error is **0.39% of demand, the best of the 53**, and its 99th percentile is
**14.05% -- thirty-six times its median.** Southwest Power Pool's median is 5.33%, more than
thirteen times worse, and its 99th percentile is 19.22%: only **3.6 times** its own median.
On the typical hour Southern is far ahead; on the worst hour of the year they are closer than
the median suggests.

**The spread of tail shapes is ten-fold and it is not predicted by the median.** The ratio of
p99 to p50 runs from 3.6x to 36.1x, with a median of **5.7x**, and that reference line is
drawn. A grid above it has a fatter tail than the field; below it, a forecast that fails
gracefully.

**A note on the peak, which is the other tail question and a smaller finding than it looks.**
After each forecast is corrected so it is right on the median hour, **44 of 53 still come in
low across the top 5% of demand hours** -- under-forecasting the peak, the operationally
dangerous direction. But it is strongly graded by size: **13 of 13 grids under 1 GW, and 4 of
6 above 20 GW**, with the median bias falling from -3.05% to -0.24%. PJM is -0.46% and ERCOT
-0.12%. At the sizes that matter it is close to nothing, and reporting it without the size
split would be the misleading version.

**All errors here are scope-corrected**, so a grid that forecasts a different quantity is not
punished twice. See figure 5.
"""
import json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate, shape, skill                                               # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "7-tail.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
Y = "2025"
XLO, XHI = 0.0030, 0.24        # p50, log
YLO, YHI = 0.030, 1.5          # p99, log
LAB = {"SOCO": (1, 4), "SWPP": (-1, 4), "CISO": (1, 4), "PJM": (1, 4), "MISO": (-1, 4),
       "ERCO": (1, 4), "PSCO": (1, 4), "FMPP": (-1, 4), "PACW": (1, 4), "SEC": (-1, 4),
       "WAUW": (1, 4), "SPA": (-1, 4), "TVA": (1, -9), "NYIS": (-1, 4), "FPL": (1, 4),
       "ISNE": (-1, -9), "DUK": (1, 4), "PSEI": (1, 4), "SCL": (-1, 4), "AECI": (1, 4)}


def main():
    sk = skill.load()
    rows = [dict(ba=ba, p50=v[Y]["p50"], p99=v[Y]["p99"], gw=v[Y]["mean_mw"] / 1000,
                 pk=v[Y]["peak_bias"])
            for ba, v in sk["ba"].items() if Y in v and ba not in shape.REGION
            and v[Y]["p50"] > 0]
    for r in rows:
        r["ratio"] = r["p99"] / r["p50"]
    med = statistics.median(r["ratio"] for r in rows)
    fat = sum(1 for r in rows if r["ratio"] > med)

    W, H = 1160, 880
    s = plate.open_svg(
        W, H, "Southern has the best typical forecast hour in the country and a 36-fold tail",
        subtitle=f"{len(rows)} US balancing authorities, {Y}. Horizontal: the median hour's "
                 f"absolute error. Vertical: the 99th percentile hour's. Both as a share of "
                 f"demand, both corrected for scope.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone choosing a forecast-accuracy metric, or reading one someone else chose",
        decide="whether a median error number tells you anything about the bad hours",
        wrong="the marks fall on one straight line, so the median fixes the tail")
    s += fr

    AX, AY, AW, AH = 250, y0 + 44, W - 566, 500
    lx = lambda v: AX + AW * (math.log10(min(max(v, XLO), XHI)) - math.log10(XLO)) / (
        math.log10(XHI) - math.log10(XLO))
    ay = lambda v: (AY + AH - 40 - (AH - 66)
                    * (math.log10(min(max(v, YLO), YHI)) - math.log10(YLO))
                    / (math.log10(YHI) - math.log10(YLO)))

    for g in (0.003, 0.01, 0.03, 0.1, 0.2):
        s.append(f'<line x1="{lx(g):.1f}" y1="{ay(YHI):.1f}" x2="{lx(g):.1f}" '
                 f'y2="{ay(YLO):.1f}" stroke="{GRID}"/>')
        s.append(txt(lx(g), ay(YLO) + 17, f"{g*100:g}%", size=9, fill=MUTED,
                     anchor="middle"))
    for v in (0.03, 0.1, 0.3, 1.0):
        s.append(f'<line x1="{lx(XLO):.1f}" y1="{ay(v):.1f}" x2="{lx(XHI):.1f}" '
                 f'y2="{ay(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(lx(XLO) - 8, ay(v) + 3, f"{v*100:g}%", size=9, fill=MUTED,
                     anchor="end"))
    # the reference: a constant p99/p50 ratio is a straight line on log-log axes
    a, b = XLO, XHI
    s.append(f'<line x1="{lx(a):.1f}" y1="{ay(a*med):.1f}" x2="{lx(b):.1f}" '
             f'y2="{ay(b*med):.1f}" stroke="{INK2}" stroke-width="1.1" '
             f'stroke-dasharray="5 4"/>')
    s += halo(lx(0.075), ay(0.075 * med) - 8, f"the median tail: p99 is {med:.1f}x p50",
              size=9.5, fill=INK2, weight="700")
    s.append(txt(AX, ay(YLO) + 36, "the median hour's absolute error (log scale)",
                 size=10, fill=INK2))
    s.append(f'<text x="{AX-42}" y="{ay(YLO):.1f}" font-size="10" fill="{INK2}" '
             f'transform="rotate(-90 {AX-42} {ay(YLO):.1f})">'
             f'the 99th percentile hour\'s absolute error (log scale)</text>')

    for r in sorted(rows, key=lambda x: -x["gw"]):
        col = RED if r["ratio"] > med else BLUE
        rad = max(3.4, math.sqrt(max(r["gw"], 0.04)) * 1.5)
        x, y = lx(r["p50"]), ay(r["p99"])
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad:.1f}" fill="{col}" '
                 f'fill-opacity="0.18" stroke="{col}" stroke-width="1.5"/>')
        if r["ba"] in LAB:
            sx_, dy = LAB[r["ba"]]
            s += halo(x + sx_ * (rad + 5), y + dy, r["ba"], size=9.5, fill=col,
                      anchor="start" if sx_ > 0 else "end", weight="700")

    soco = next(r for r in rows if r["ba"] == "SOCO")
    swpp = next(r for r in rows if r["ba"] == "SWPP")
    for v, body, col, wt in (
            (1.30, f"SOCO   median {soco['p50']:.2%}, p99 {soco['p99']:.2%}   "
                   f"{soco['ratio']:.1f}x", RED, "700"),
            (1.12, "best typical hour of the 53, and a tail six times", RED, "normal"),
            (0.96, "fatter than the field", RED, "normal"),
            (0.70, f"SWPP   median {swpp['p50']:.2%}, p99 {swpp['p99']:.2%}   "
                   f"{swpp['ratio']:.1f}x", BLUE, "700"),
            (0.60, "thirteen times the median error, and the", BLUE, "normal"),
            (0.515, "flattest tail in the country", BLUE, "normal")):
        s.append(txt(lx(0.0033), ay(v), body, size=9.5, fill=col, weight=wt))

    TX, ty = W - 236, AY + 26
    for head, body, col in (
            ("the dashed line", f"Constant ratio. {fat} of {len(rows)} grids sit above it "
                                f"with a fatter tail than the field median of "
                                f"{med:.1f}x.", INK2),
            ("why it is not one line", "If the median error determined the tail, every mark "
                                       "would sit on it. The ratio runs 3.6x to 36.1x -- a "
                                       "ten-fold spread the median cannot see.", INK),
            ("the peak, separately", "44 of 53 under-forecast the top 5% of hours, but 13 "
                                     "of 13 under 1 GW against 4 of 6 above 20 GW. PJM is "
                                     "-0.46%. Mostly a small-grid effect.", MUTED)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        w = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=33, leading=12.5)
        s += w
        ty += 12.5 * len(w) + 16

    foot = (
        "EIA Hourly Electric Grid Monitor (EBA) bulk file, no key, fetched 2026-09-23; "
        "EBA.{BA}-ALL.DF.H against EBA.{BA}-ALL.D.H over the 2025 hours both cover. Errors "
        "are absolute and scope-corrected, so a grid forecasting a different quantity is not "
        "penalised twice. Circle area is mean demand. CAVEAT: percentile errors on grids "
        "under 1 GW are moved by single hours; the 14 EIA region aggregates are excluded.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {len(rows)} grids; tail ratio median {med:.1f}x, "
          f"range {min(r['ratio'] for r in rows):.1f}x to "
          f"{max(r['ratio'] for r in rows):.1f}x")
    for r in sorted(rows, key=lambda x: -x["ratio"])[:3]:
        print(f"      {r['ba']:<6}p50 {r['p50']:>6.2%}  p99 {r['p99']:>7.2%}  "
              f"{r['ratio']:>5.1f}x  {r['gw']:>6,.1f} GW")
    return 0


if __name__ == "__main__":
    sys.exit(main())
