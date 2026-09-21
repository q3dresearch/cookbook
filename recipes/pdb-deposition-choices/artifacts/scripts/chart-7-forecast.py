#!/usr/bin/env python3
"""The best-fitting model is the only one that is wrong.

    python3 chart-7-forecast.py

Cryo-EM's growth fitted over 2012-2019 is **+57.2% a year at R^2 0.99**, the cleanest
exponential in the register. Extrapolated, it passes crystallography in 2023.

**It did not.** Held out against the years it never saw, the same fit over-predicts by 25% in
2022, 43% in 2023, 56% in 2024 and **74% in 2025** -- 25,147 forecast against 6,453 actual. An
R^2 of 0.99 on the fit window said nothing about the forecast.

**Because the growth rate is itself collapsing.** The rolling three-year rate peaked at +65% a
year in 2018 and has fallen every window since: +55.6% in 2021, +22.3% in 2024, **+9.8% in
2025**. A constant-rate model cannot represent a rate that decays, and fitting one to a
decaying rate fails in the same direction every time.

**Once the deceleration is respected, the forecast is stable.** Six scenarios -- two cryo-EM
models (hold the current rate, or continue the measured decay) crossed with three X-ray
trajectories (flat, -3% a year, -8% a year) -- land on **2026, 2027 or 2028**. Every one of
them. The disagreement in this register is not about when cryo-EM overtakes crystallography; it
is entirely between the falsified fit and everything else.

**A correction, kept visible.** An earlier version of this figure asserted a third scenario in
which the deceleration continues and cryo-EM "levels off below X-ray". That was never computed.
It is wrong: the decay model still compounds to about 4.2x the 2024 level, and it crosses in
2027 like the others.

**What this cannot tell you.** Nothing here is about capability. It counts what was deposited,
and a slowdown is equally consistent with a maturing method, with easy targets running out, and
with a funding cycle.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdb as P, plate                                                   # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "7-forecast.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
OLIVE = "#5f6f33"
XRATES = [(0.0, "flat"), (-0.03, "-3% a year"), (-0.08, "-8% a year")]


def fit(series, yrs):
    xs = list(yrs)
    ys = [math.log(series[y]) for y in xs]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    a = my - b * mx
    r2 = 1 - (sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
              / sum((y - my) ** 2 for y in ys))
    return a, b, r2


def main():
    d = P.load()
    mx = {int(k): v for k, v in d["method_by_year"]["X-RAY DIFFRACTION"].items()}
    me = {int(k): v for k, v in d["method_by_year"]["ELECTRON MICROSCOPY"].items()}
    mn = {int(k): v for k, v in d["method_by_year"]["SOLUTION NMR"].items()}
    ae, be, r2e = fit(me, range(2012, 2020))

    cagr = {y: (me[y] / me[y - 3]) ** (1 / 3) - 1 for y in range(2011, 2026)}
    # decay of log-growth, fitted across the three three-year windows
    g16 = math.log(me[2018] / me[2015]) / 3
    g22 = math.log(me[2024] / me[2021]) / 3
    kdec = (g22 / g16) ** (1 / 6)
    gnow = math.log(me[2025] / me[2022]) / 3

    def project(mode, xr_rate, upto=2034):
        e, x, out = me[2024], mx[2024], {2024: (me[2024], mx[2024])}
        for y in range(2025, upto + 1):
            g = g22 * kdec ** (y - 2024) if mode == "decay" else gnow
            e *= math.exp(g)
            x *= (1 + xr_rate)
            out[y] = (e, x)
        return out

    crosses = []
    for mode in ("decay", "current"):
        for xr_rate, _ in XRATES:
            pr = project(mode, xr_rate)
            crosses.append(next((y for y in sorted(pr) if pr[y][0] >= pr[y][1]), None))
    clo, chi = min(crosses), max(crosses)

    W, H = 1200, 770
    s = plate.open_svg(W, H, "The best-fitting model is the only one that is wrong")
    fr, _ = plate.frame(W, 62,
                        who="anyone planning instrument capacity on a method's growth rate",
                        decide="whether to trust an extrapolation with a high R²",
                        wrong="the six deceleration scenarios disagree with each other")
    s += fr

    # ---- left: actuals, the falsified fit, and the scenario fan
    AX, AY, AH, AW = 28, 168, 400, 700
    s.append(txt(AX, AY - 18, "structures deposited that year, by method (log scale)",
                 size=11, fill=INK2))
    y0, y1 = 2012, 2032
    x0, pw = AX + 50, AW - 96
    px = lambda y: x0 + pw * ((y - y0) / (y1 - y0))
    lo, hi = 150, 40000
    py = lambda v: (AY + AH - 52 - (AH - 84)
                    * ((math.log10(max(v, lo)) - math.log10(lo))
                       / (math.log10(hi) - math.log10(lo))))
    for v in (200, 1000, 10000):
        s.append(f'<line x1="{x0:.1f}" y1="{py(v):.1f}" x2="{px(y1):.1f}" y2="{py(v):.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(x0 - 7, py(v) + 3, f"{v//1000}k" if v >= 1000 else str(v), size=9,
                     fill=MUTED, anchor="end"))
    for y in range(2012, 2033, 4):
        s.append(txt(px(y), AY + AH - 34, str(y), size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, AY + AH - 16, "year the structure was deposited", size=10, fill=MUTED))
    s.append(f'<rect x="{px(2025.5):.1f}" y="{AY-6:.1f}" '
             f'width="{px(y1)-px(2025.5):.1f}" height="{AH-46:.1f}" fill="{SLATE}" '
             f'fill-opacity="0.07"/>')
    s += halo(px(2025.7), AY - 10, "projection", size=9, fill=MUTED)

    # the crossover band every deceleration scenario lands in
    s.append(f'<rect x="{px(clo-0.5):.1f}" y="{AY-6:.1f}" width="{px(chi+0.5)-px(clo-0.5):.1f}" '
             f'height="{AH-46:.1f}" fill="{GREEN}" fill-opacity="0.13"/>')
    s += halo((px(clo - .5) + px(chi + .5)) / 2, AY + AH - 62,
              f"{clo}–{chi}", size=11, fill=GREEN, anchor="middle", weight="700")
    s += halo((px(clo - .5) + px(chi + .5)) / 2, AY + AH - 50,
              "all six scenarios", size=8.5, fill=GREEN, anchor="middle")

    for mode, dash in (("decay", "1 3"), ("current", "1 3")):
        for xr_rate, _ in XRATES:
            pr = project(mode, xr_rate)
            for idx, col in ((0, BLUE), (1, SLATE)):
                pts = [(px(y), py(pr[y][idx])) for y in sorted(pr) if y <= y1]
                s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                                for i, (a, b) in enumerate(pts))
                         + f'" fill="none" stroke="{col}" stroke-width="1.1" '
                           f'stroke-opacity="0.55" stroke-dasharray="{dash}"/>')
    proj = [(px(y), py(math.exp(ae + be * y))) for y in range(2012, y1 + 1)
            if math.exp(ae + be * y) <= hi]
    s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                    for i, (a, b) in enumerate(proj))
             + f'" fill="none" stroke="{RED}" stroke-width="1.8" stroke-dasharray="5 3"/>')
    s += halo(px(2023.4), py(hi) + 14, "the 2012–19 fit, +57%/yr, R² 0.99",
              size=9.5, fill=RED, anchor="end", weight="700")
    s += halo(px(2023.4), py(hi) + 26, "falsified by its own holdout years",
              size=9, fill=RED, anchor="end")
    for series, col, lab in ((me, BLUE, "cryo-EM"), (mx, SLATE, "X-ray"), (mn, OLIVE, "NMR")):
        pts = [(px(y), py(series[y])) for y in range(y0, 2026) if y in series]
        s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                        for i, (a, b) in enumerate(pts))
                 + f'" fill="none" stroke="{col}" stroke-width="2.6"/>')
        for a, b in pts:
            s.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="2.4" fill="{col}"/>')
        dy = {"cryo-EM": 16, "X-ray": -10, "NMR": -10}[lab]
        s += halo(pts[-1][0] - 3, pts[-1][1] + dy, lab, size=10.5, fill=col,
                  anchor="end", weight="700")
    y = 2025
    pred = math.exp(ae + be * y)
    s.append(f'<line x1="{px(y):.1f}" y1="{py(me[y]):.1f}" x2="{px(y):.1f}" '
             f'y2="{py(pred):.1f}" stroke="{RED}" stroke-width="1.3"/>')
    s += halo(px(y) - 5, py(math.exp((math.log(me[y]) + math.log(pred)) / 2)),
              "74% below the fit", size=9.5, fill=RED, anchor="end", weight="700")

    # ---- right: the rate that is collapsing, which is why the fit fails
    BX, BY, BH, BW = 790, 168, 250, 382
    s.append(txt(BX, BY - 18, "cryo-EM's rolling three-year growth rate", size=11, fill=INK2))
    gy = lambda r: BY + BH - 40 - (BH - 66) * (r / 0.70)
    gx = lambda y: BX + (BW - 30) * ((y - 2011) / (2025 - 2011))
    for r in (0, .2, .4, .6):
        s.append(f'<line x1="{BX+22:.1f}" y1="{gy(r):.1f}" x2="{gx(2025):.1f}" '
                 f'y2="{gy(r):.1f}" stroke="{GRID}"/>')
        s.append(txt(BX + 16, gy(r) + 3, f"{r:.0%}", size=9, fill=MUTED, anchor="end"))
    for y in (2012, 2016, 2020, 2024):
        s.append(txt(gx(y), gy(0) + 18, str(y), size=9, fill=MUTED, anchor="middle"))
    pts = [(gx(y), gy(cagr[y])) for y in sorted(cagr)]
    s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                    for i, (a, b) in enumerate(pts))
             + f'" fill="none" stroke="{BLUE}" stroke-width="2.6"/>')
    for (a, b), yy in zip(pts, sorted(cagr)):
        s.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3" fill="{BLUE}"/>')
    for yy, side in ((2018, "n"), (2025, "s")):
        a, b = gx(yy), gy(cagr[yy])
        s += halo(a, b + (-9 if side == "n" else 16), f"{cagr[yy]:+.0%}", size=10, fill=BLUE,
                  anchor="middle", weight="700")
    s.append(txt(BX + 22, gy(0) + 36, "growth over the previous three years, by year",
                 size=9.5, fill=MUTED))
    s += wrap(BX, BY + BH + 34,
              f"Peaked at +65% a year in 2018 and has fallen every window since — +22% in 2024 "
              f"and +10% in 2025. This is what the 2012–19 fit assumed was constant, and it is "
              f"why that fit fails in one direction and keeps failing by more.",
              size=10.5, fill=INK2, chars=56, leading=14)

    by = AY + AH + 10
    s.append(txt(AX, by, "respect the deceleration and the forecast stops disagreeing",
                 size=12.5, fill=INK, weight="600"))
    s += wrap(AX, by + 20,
              f"Two cryo-EM models — hold the current rate, or continue the measured decay — "
              f"crossed with three X-ray trajectories give six projections, and every one "
              f"crosses in {clo}, {clo+1} or {chi}. The spread in this register is not between "
              f"forecasts; it is between the falsified fit and everything else. An earlier "
              f"version of this figure claimed a scenario where the decay makes cryo-EM level "
              f"off below X-ray: that was asserted and never computed, and it is wrong — the "
              f"decay still compounds to about 4.2x the 2024 level.",
              size=11, fill=INK2, chars=98, leading=15)

    fy = H - 22 - 14 * 3
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"RCSB PDB search API, fetched {d['fetched']}, deposition date. 2025 is down "
              f"across the whole register — all depositions -13%, X-ray -14%, cryo-EM -9% — so "
              f"the last point is not cryo-EM specific; cryo-EM fell least and its share of all "
              f"depositions still rose, 40.0% to 41.8%. The deceleration is visible from 2021 "
              f"and does not depend on 2025. Solution NMR is drawn because it is the one method "
              f"that fell, {mn[2010]:,} depositions in 2010 against {mn[2025]:,} in 2025, and "
              f"figure 8 shows why it was never displaced. None of this is about capability: a "
              f"slowdown in depositions is equally consistent with a maturing method, easy "
              f"targets running out, and a funding cycle.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    fit R² {r2e:.2f}, over-predicts 2025 by "
          f"{(math.exp(ae+be*2025)-me[2025])/math.exp(ae+be*2025):.0%}")
    print(f"    six scenarios cross in {sorted(set(crosses))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
