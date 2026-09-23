#!/usr/bin/env python3
"""What a state burns owns the volatility of its power price. What it sells owns the level.

    python3 chart-12-price.py

**This is a Shapley decomposition, and the earlier version of this plate was not.** It showed
standardised regression coefficients, which answer "move this one standard deviation and hold
the rest still" -- an *effect*, signed. That is the wrong statistic for *importance* when the
predictors are correlated, and generation shares are worse than correlated: they sum to one.
Fit all of them and the coefficients blow up into uninterpretable nonsense -- gas **-1.13**,
coal **-1.52**, hydro **-1.19**, wind and solar **-1.04**, every one large and negative,
because the algebra has nothing to anchor on.

**The Shapley value for R-squared fixes exactly that.** Each predictor's incremental
R-squared is averaged over **every order the predictors could enter in** -- all 256 subsets
here, computed exactly rather than sampled -- so variance two predictors share is split
between them instead of handed to whichever the algebra favours. The shares sum to the
model's R-squared by construction. The cost is the sign: a Shapley value is always positive,
so direction is printed beside each bar rather than encoded in it.

**And the split survives the better statistic.** Gas is the largest single owner of price
volatility at **29%** of the explained variance, with coal at 23% and hydro at 18% -- the
generation mix owns 88% of it between them, and the demand mix 6%. On the price *level* it
inverts: the **industrial share of retail sales owns 47%**, and every generation variable
together owns 45% of a much weaker model.

**Rooftop solar is excluded, and this is why.** Included, it takes 56% of the level model and
lifts R-squared to 0.78 -- and the arrow points backwards. Electricity price is enormously
persistent (2010-14 against 2022+, **r = +0.93**), expensive states adopted more rooftop
(**+0.69**), and controlling for the earlier price collapses rooftop's effect on volatility
from +0.24 to **+0.06** and on level from +0.80 to +0.30. It is a consequence of dear
electricity at least as much as a cause, and a decomposition that includes it is measuring
that loop.

**Retail price is regulated and lagged**, which bounds all of this: it is set by a commission,
it contains network charges, and generation economics reach it slowly. Hourly wholesale prices
live with the ISOs. Whether *location* adds anything on top of these features is figure 13.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate, price                                                      # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "12-price.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
KEYS = ["gas", "coal", "var_ren", "nuclear", "hydro", "hhi", "ind_share", "res_share"]
NICE = {"gas": "gas share of generation", "coal": "coal share of generation",
        "var_ren": "wind and utility solar share", "nuclear": "nuclear share",
        "hydro": "hydro share", "hhi": "fuel-mix concentration",
        "ind_share": "industrial share of retail sales",
        "res_share": "residential share of retail sales"}
KIND = {"gas": "what it burns", "coal": "what it burns", "var_ren": "what it burns",
        "nuclear": "what it burns", "hydro": "what it burns", "hhi": "what it burns",
        "ind_share": "what it sells", "res_share": "what it sells"}
XHI = 0.235          # must clear the largest Shapley value, not the axis
LEAD = 0.06


def main():
    rows = price.mainland(price.load())
    shv, r2v, nv = price.shapley(rows, KEYS, "price_vol")
    shl, r2l, nl = price.shapley(rows, KEYS, "price")
    dirv = {k: price.corr([(r.get(k), r.get("price_vol")) for r in rows])[0] for k in KEYS}
    dirl = {k: price.corr([(r.get(k), r.get("price")) for r in rows])[0] for k in KEYS}
    burn_v = sum(shv[k] for k in KEYS if KIND[k] == "what it burns") / r2v
    sell_l = sum(shl[k] for k in KEYS if KIND[k] == "what it sells") / r2l
    items = sorted(KEYS, key=lambda k: (0 if KIND[k] == "what it burns" else 1,
                                        -max(shv[k] / r2v, shl[k] / r2l)))

    W = 1150
    H = 300 + 62 * len(items) + 128
    s = plate.open_svg(
        W, H, "What a state burns owns the volatility of its power price. What it sells "
              "owns the level.",
        subtitle=f"{nv} US states, 2010 to 2026. Each bar is the share of the model's "
                 f"explained variance that this one thing owns, averaged over every order "
                 f"the predictors could enter in.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone claiming a state's generation mix does or does not move its power price",
        decide="which question you are asking -- how stable the price is, or how high",
        wrong="the same predictor owns the largest share of both")
    s += fr

    ly = y0 + 42
    for i, (lab, col, r2) in enumerate(((f"volatility of the price  (R2 = {r2v:.2f})", RED,
                                         r2v),
                                        (f"the level of the price  (R2 = {r2l:.2f})", BLUE,
                                         r2l))):
        x = 366 + i * 288
        s.append(f'<rect x="{x-7:.1f}" y="{ly-10:.1f}" width="14" height="12" fill="{col}" '
                 f'fill-opacity="0.34" stroke="{col}" stroke-width="1.5"/>')
        s.append(txt(x + 13, ly, lab, size=10, fill=col, weight="700"))

    AX, AW = 366, W - 566
    lx = lambda v: AX + AW * min(max(v, 0.0), XHI) / XHI
    top = ly + 68
    bot = top + 62 * len(items) - 18
    for g in (0.0, 0.05, 0.10, 0.15, 0.20):
        s.append(f'<line x1="{lx(g):.1f}" y1="{top-18:.1f}" x2="{lx(g):.1f}" '
                 f'y2="{bot:.1f}" stroke="{RULE if g == 0 else GRID}" '
                 f'stroke-width="{1.5 if g == 0 else 1}"/>')
        s.append(txt(lx(g), top - 26, f"{g:.2f}", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX - 4, top - 44, "Shapley share of explained variance  -- the bars in each "
                                   "colour sum to that model's R2", size=10, fill=INK2))

    last = None
    for i, k in enumerate(items):
        y = top + 62 * i + 12
        if KIND[k] != last:
            s.append(txt(30, y + 4, KIND[k], size=10, fill=MUTED, weight="700"))
            last = KIND[k]
        lead = max(shv[k] / r2v, shl[k] / r2l) >= LEAD * 2
        s.append(txt(AX - 20, y + 4, NICE[k], size=11,
                     fill=INK if lead else MUTED, anchor="end"))
        for j, (val, col, tot, dr) in enumerate(((shv[k], RED, r2v, dirv[k]),
                                                 (shl[k], BLUE, r2l, dirl[k]))):
            yy = y - 10 + j * 11
            big = val >= LEAD
            s.append(f'<rect x="{lx(0):.1f}" y="{yy:.1f}" '
                     f'width="{max(lx(val)-lx(0), 0.8):.1f}" height="9" fill="{col}" '
                     f'fill-opacity="{0.42 if big else 0.20}" stroke="{col}" '
                     f'stroke-width="{1.4 if big else 1}"/>')
            s.append(txt(W - 178 + j * 56, y + 4, f"{val/tot*100:.0f}%", size=11, fill=col,
                         weight="700" if big else "normal"))
        sgn = "+" if (dirv[k] or 0) > 0 else "-"
        sgl = "+" if (dirl[k] or 0) > 0 else "-"
        s.append(txt(W - 62, y + 4, f"{sgn} / {sgl}", size=9.5, fill=MUTED))

    s.append(txt(W - 178, top - 26, "share of", size=9, fill=MUTED))
    s.append(txt(W - 62, top - 26, "direction", size=9, fill=MUTED))
    s += halo(30, bot + 32, f"the generation mix owns {burn_v:.0%} of the volatility model; "
              f"the demand mix owns {sell_l:.0%} of the level model", size=10.5, fill=INK2,
              weight="700")
    s += halo(30, bot + 47, "a Shapley share is always positive, so the last column carries "
              "the direction: volatility first, then level", size=10.5, fill=INK2)
    s += halo(30, bot + 65, "rooftop solar is left out on purpose -- it takes 56% of the "
              "level model, and price predicts rooftop adoption (+0.69) as well as the "
              "reverse", size=10.5, fill=AMBER, weight="700")

    foot = (
        "EIA ELEC bulk file, no key, fetched 2026-09-23; ELEC.PRICE, ELEC.GEN and ELEC.SALES, "
        "state-quarters from 2010. Volatility is the standard deviation of the year-over-year "
        "log change in average retail price. Shapley values are exact over all 256 subsets. "
        "CAVEAT: this is REGULATED RETAIL price -- set by a commission, lagged, and carrying "
        "network charges. It is not a wholesale market price.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=172, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=172, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    n={nv}; volatility R2={r2v:.3f}, level R2={r2l:.3f}")
    for k in items:
        print(f"      {NICE[k]:<34}vol {shv[k]/r2v*100:>5.0f}%   level "
              f"{shl[k]/r2l*100:>5.0f}%")
    print(f"    generation mix owns {burn_v:.0%} of volatility; demand mix owns "
          f"{sell_l:.0%} of level")
    return 0


if __name__ == "__main__":
    sys.exit(main())
