#!/usr/bin/env python3
"""What makes a grid hard to forecast is how flat its load is. Everything else collapses.

    python3 chart-7-drivers.py

Figure 5 measured difficulty as the error a same-hour-last-week forecast makes: the honest
version of "volatility", running from 4.5% to 34.1% of mean demand across these grids. This
figure asks what explains it, and the answer is one variable -- with one surprise beside it.

**Taken one at a time, four things look like they matter.** Seasonal amplitude correlates at
+0.40, wind and solar share at -0.26, grid size at -0.12, load flatness at -0.72. Put them in
one model and **flatness keeps its whole effect while the others go to nearly nothing**:
seasonality flips sign to +0.12, renewable share falls to -0.14, size to +0.05. Their
marginal correlations were flatness wearing a hat -- industrial share of state electricity
correlates with flatness at +0.67, size at +0.46.

**So generation mix does not predict demand-forecast difficulty**, which is the right answer
rather than a disappointing one: the series being forecast is *demand*, not net load, and it
does not know what is generating it. The same goes for population, industrial mix and
industrial price, none of which survive either.

**The temperature proxy is the instructive failure.** Seasonal amplitude is a real
temperature-sensitivity measure and its marginal correlation is a respectable +0.40. It
contributes nothing once flatness is in, because a weather-driven grid *is* a peaky grid, and
flatness already measures that with less noise.

**Data centre density is the one that survives.** Facilities per million people holds a
**-0.36 standard deviation effect alongside flatness's -0.49** -- the two are correlated only
at +0.42, so it is carrying its own information. Compute makes a grid easier to forecast,
which is what a flat 24/7 load should do, and it is detectable *here* after failing as a
predictor of load growth in figures 3 and 4 and failing again on state electricity growth at
r = +0.03.

**It is the weakest result on this plate and gets the strongest caveat.** It rests on 41
balancing authorities whose footprint sits inside one state, against a directory nobody is
obliged to file into, and only per capita: the raw facility count correlates at **-0.03**.
Facilities per million may also be reading urbanisation or economic structure rather than
compute. It is a lead, not a finding.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate, predict                                                    # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "8-drivers.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
NICE = {"flat": "load flatness, overnight trough over peak",
        "fac_per_m": "data centres per million people",
        "var_share": "wind and solar share of own generation",
        "season": "seasonal amplitude (temperature proxy)",
        "gw": "grid size in GW"}
XLO, XHI = -0.92, 0.34
SURVIVES = 0.25               # a partial effect this size or larger is doing real work


def main():
    rows = predict.load()["rows"]
    sub = [r for r in rows if r.get("fac_per_m") is not None]
    beta, r2, n = predict.regress(sub, predict.MODEL_B, "difficulty")
    betaA, r2A, nA = predict.regress(rows, predict.MODEL_A, "difficulty")
    lg = dict(predict.MODEL_B)
    items = []
    for k, b in beta.items():
        m, _ = predict.marginal(sub, k, lg[k], "difficulty")
        items.append(dict(k=k, beta=b, marg=m))
    items.sort(key=lambda d: d["beta"])

    W = 1160
    H = 290 + 54 * len(items) + 120
    s = plate.open_svg(
        W, H, "What makes a grid hard to forecast is how flat its load is",
        subtitle=f"Each thing measured by itself, then again with all five competing to "
                 f"explain the same grids. Where the two disagree, the first one was "
                 f"standing in for another. {n} balancing authorities.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone modelling which grids are hard to forecast, or why",
        decide="which variable to carry, and which one-at-a-time correlations to stop "
               "quoting",
        wrong="the hollow and filled marks sit on top of each other, so nothing was "
              "standing in for anything else")
    s += fr

    ly = y0 + 42
    for i, (lab, fill, col) in enumerate((
            ("if you look at this alone", False, SLATE),
            ("once the other four can explain it too", True, INK))):
        x = 330 + i * 250
        if fill:
            s.append(f'<circle cx="{x:.1f}" cy="{ly-4:.1f}" r="6" fill="{BLUE}" '
                     f'fill-opacity="0.3" stroke="{BLUE}" stroke-width="1.8"/>')
        else:
            s.append(f'<circle cx="{x:.1f}" cy="{ly-4:.1f}" r="4.4" fill="none" '
                     f'stroke="{SLATE}" stroke-width="1.5"/>')
        s.append(txt(x + 12, ly, lab, size=10, fill=col, weight="700"))

    AX, AW = 330, W - 520
    lx = lambda v: AX + AW * (min(max(v, XLO), XHI) - XLO) / (XHI - XLO)
    top = ly + 68
    bot = top + 54 * len(items) - 16
    for g in (-0.75, -0.5, -0.25, 0.0, 0.25):
        zero = abs(g) < 1e-9
        s.append(f'<line x1="{lx(g):.1f}" y1="{top-16:.1f}" x2="{lx(g):.1f}" '
                 f'y2="{bot:.1f}" stroke="{RULE if zero else GRID}" '
                 f'stroke-width="{1.5 if zero else 1}"/>')
        s.append(txt(lx(g), top - 24, f"{g:+.2f}" if not zero else "0", size=9,
                     fill=MUTED, anchor="middle"))
    s.append(txt(AX - 4, top - 42, "how much a grid's forecast difficulty moves when this "
                                   "one thing does, in standard deviations", size=10,
                 fill=INK2))

    for i, d in enumerate(items):
        y = top + 54 * i + 12
        strong = abs(d["beta"]) >= SURVIVES
        col = BLUE if strong else SLATE
        s.append(txt(AX - 18, y + 4, NICE[d["k"]], size=11,
                     fill=INK if strong else MUTED, anchor="end"))
        s.append(f'<line x1="{lx(d["marg"]):.1f}" y1="{y:.1f}" x2="{lx(d["beta"]):.1f}" '
                 f'y2="{y:.1f}" stroke="{FAINT}" stroke-width="1.6"/>')
        s.append(f'<circle cx="{lx(d["marg"]):.1f}" cy="{y:.1f}" r="4.4" fill="none" '
                 f'stroke="{SLATE}" stroke-width="1.5"/>')
        s.append(f'<circle cx="{lx(d["beta"]):.1f}" cy="{y:.1f}" r="6.6" fill="{col}" '
                 f'fill-opacity="0.30" stroke="{col}" stroke-width="1.8"/>')
        s.append(txt(W - 168, y + 4, f"{d['beta']:+.2f}", size=11, fill=col, weight="700"))
        s.append(txt(W - 126, y + 4, f"was {d['marg']:+.2f}", size=9.5, fill=MUTED))
        if not strong:
            s.append(txt(W - 60, y + 4, "collapses", size=9.5, fill=MUTED))

    s += halo(AX - 18 - 270, bot + 30,
              f"the five together explain R2 = {r2:.2f} of the spread in difficulty; "
              f"without the data-centre variable, on all {nA} grids,", size=10.5,
              fill=INK2, weight="700")
    s += halo(AX - 18 - 270, bot + 45,
              f"flatness alone carries {betaA['flat']:+.2f} and nothing else exceeds "
              f"{max(abs(v) for k, v in betaA.items() if k != 'flat'):.2f}",
              size=10.5, fill=INK2)

    foot = (
        "EIA Hourly Electric Grid Monitor and PeeringDB, fetched 2026-09-23; state "
        "predictors from EIA SEDS 2023. Difficulty is the error a same-hour-last-week "
        "forecast makes, as a share of mean demand, 2025. CAVEAT: the data-centre variable "
        "exists only for the 41 balancing authorities whose footprint sits inside one state, "
        "against a directory nobody is obliged to file into, and only per capita -- the raw "
        "facility count correlates at -0.03. It is a lead, not a finding.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    model n={n}, R2={r2:.2f}; without data centres n={nA}, R2={r2A:.2f}")
    for d in items:
        print(f"      {NICE[d['k']]:<44}beta {d['beta']:>+6.2f}   was {d['marg']:>+6.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
