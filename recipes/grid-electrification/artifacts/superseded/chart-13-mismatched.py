#!/usr/bin/env python3
"""SUPERSEDED. The mismatched-window version of figure 13. Do not cite.

    python3 chart-13-mismatched.py

Kept because it is persuasive and wrong, which is the only kind worth keeping. Nothing on
this plate looks broken: the marks are real states, the histograms are the real counts, the
regression numbers are correctly computed, and the correlation is correctly computed from
what it was given.

**What it was given was two axes measured over different periods.** The price level is the
mean over **2022 onward**. The swing is the standard deviation of the year-over-year log
change over **2010 onward**. Neither window is wrong on its own, and their mismatch is
invisible in the drawing.

It reports **r = +0.32** and 33 of 49 states on the cheap-and-steady to dear-and-swingy
diagonal, with a between-region reading built on top of that. Matching both axes to 2018-2025
gives **+0.18**, and within each region +0.09, +0.09, -0.06 and -0.08 -- nothing. The change
comes from the swing axis alone (+0.32 to +0.22 by moving only that one): the long window
includes 2011-2014, when the dear Northeastern states also happened to be the moving ones.

Its title -- *the Northeast pays double and swings hardest* -- is also false on matched years,
where the South swings 0.065 against the Northeast's 0.064.

See `../superseded/README.md`. The live figure is `scripts/chart-13-location.py`.

Figure 12 asked what *features* of a state predict its electricity price. This asks whether
**location** adds anything on top of them, and the two halves of the question answer
differently.

**For the price level it adds nearly everything.** Eight census-division indicators, on top of
six generation-mix and two demand-mix features, lift **adjusted** R-squared from **0.373 to
0.805** -- larger than everything the features contributed, and adjusted so the extra
parameters are paid for. **For volatility it adds 0.004**, from 0.310 to 0.314. Divisions do
differ in volatility, but that difference is already inside the fuel mix: the most volatile
division is also the most gas-exposed.

**The two histograms are that result.** Along the price axis the regions occupy different
parts of the range and barely overlap. Along the volatility axis they sit on top of one
another. A regional term is real work on one and decoration on the other.

**They are overlaid rather than stacked, which is not a cosmetic choice.** A stacked bar moves
every group's baseline, so a reader can see each region's *share of a bin* and cannot see its
*distribution*. The claim on this plate is about where each region lives along an axis, which
is a statement about its own shape. Every region is therefore drawn from the same baseline at
0.3 opacity, and the scale is the largest single-region bin rather than the largest total.

**And the middle panel shows what neither margin can: the joint position, which is close to
empty.** Price and swing correlate at **r = +0.18**, and inside each region at +0.09, +0.09,
-0.06 and -0.08 -- nothing anywhere. New England pays **1.79x** what the West pays and swings
about as much as the South.

**Both axes are measured over the same years, and an earlier version of this plate was not.**
It took the price level from 2022 onward and the swing from 2010 onward, and reported
**r = +0.32**. Matching the windows takes it to +0.18, and the change comes from the swing
axis: the full window includes 2011-2014, when the dear Northeastern states also happened to
be the moving ones. Two axes on different windows will find a relationship between the
windows.

**Collapsing time to one mark per state was checked, not assumed.** Volatility on 2011-2017
against volatility on **2018-2025 -- disjoint halves -- ranks the same states alike, rho
+0.62**. A state that swung then swings now, which one shared national event cannot produce.

**The level of that axis is another matter.** The median state's year-over-year price move was
0.020 to 0.037 in every year through 2020, **0.086 in 2022**, and 0.052 in 2025; 2021 to 2023
carries 34% of fifteen years of movement, where an even share would be 20%. The **ranking**
here is durable. The **number** is a statement about a window containing a gas shock.

**No density contours, deliberately.** At 49 points a two-dimensional kernel estimate mostly
draws its own bandwidth. The marks are the density, and each one is a state somebody can
check.

**Regions, not the nine divisions, for the colour.** Nine categorical colours are past what a
reader can hold. The division-level medians are in the recipe notes; what survives here is the
grouping coarse enough to read, and the finding does not depend on the finer cut.
"""
import collections, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))   # the live modules, unchanged
import geo, plate, price                                                 # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "13-location-mismatched.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
GRID_F = ["gas", "coal", "var_ren", "nuclear", "hydro", "hhi"]
DEM_F = ["ind_share", "res_share"]
REGION = {"New England": "Northeast", "Middle Atlantic": "Northeast",
          "East North Central": "Midwest", "West North Central": "Midwest",
          "South Atlantic": "South", "East South Central": "South",
          "West South Central": "South", "Mountain": "West", "Pacific": "West"}
COL = {"Northeast": RED, "South": AMBER, "Midwest": BLUE, "West": GREEN}
ORDER = ["Northeast", "South", "Midwest", "West"]
PLO, PHI, PBIN = 8.0, 26.0, 1.5
VLO, VHI, VBIN = 0.020, 0.120, 0.010
NAME = {"CA": "California", "ND": "North Dakota", "NV": "Nevada", "LA": "Louisiana",
        "SD": "South Dakota", "MA": "Massachusetts", "TX": "Texas", "ME": "Maine"}


def adj(r2, n, p):
    return 1 - (1 - r2) * (n - 1) / (n - p - 1) if r2 is not None and n > p + 1 else None


def main():
    d = price.load()
    rows = []
    for st, v in d["state"].items():
        if st in price.ISLANDS:
            continue
        dv = geo.DIVISION.get(st)
        if dv and v.get("price") and v.get("price_vol"):
            rows.append(dict(st=st, div=dv, reg=REGION[dv], p=v["price"],
                             v=v["price_vol"], pe=v.get("vol_early")))
    n = len(rows)
    rr, rho, _ = price.corr([(r["p"], r["v"]) for r in rows])
    divs = sorted(set(geo.DIVISION.values()))[1:]
    mrows = [dict(v, **{f"d_{x}": (1.0 if geo.DIVISION.get(st) == x else 0.0)
                        for x in divs})
             for st, v in d["state"].items()
             if st not in price.ISLANDS and st in geo.DIVISION]
    loc = [f"d_{x}" for x in divs]
    lad = {yk: [adj(price._r2(mrows, k, yk), len(mrows), len(k))
                for k in (GRID_F + DEM_F, GRID_F + DEM_F + loc)]
           for yk in ("price", "price_vol")}
    stab = price.corr([(r["pe"], r["v"]) for r in rows if r.get("pe")])
    mp = statistics.median(r["p"] for r in rows)
    mv = statistics.median(r["v"] for r in rows)
    diag = sum(1 for r in rows if (r["p"] > mp) == (r["v"] > mv))

    W, H = 1180, 900
    s = plate.open_svg(
        W, H, "SUPERSEDED -- The Northeast pays double and swings hardest",
        subtitle=f"KEPT AS A NEGATIVE EXAMPLE. {n} states, price from 2022 onward against "
                 f"a swing from 2010 onward -- two different windows, which is invisible "
                 f"here and worth +0.14 of correlation.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone adding a regional term to a model of electricity prices",
        decide="whether location earns its parameters, for the level or for the swing",
        wrong="the regions separate on both histograms, or on neither")
    s += fr

    AX, AW = 250, 560
    MT, MH = y0 + 52, 92                  # the marginal over price, on top
    AY, AH = MT + MH + 16, 400            # the main panel
    RW = 118                              # the marginal over volatility, on the right
    px = lambda v: AX + AW * (min(max(v, PLO), PHI) - PLO) / (PHI - PLO)
    py = lambda v: AY + AH - AH * (min(max(v, VLO), VHI) - VLO) / (VHI - VLO)

    for g in (10, 15, 20, 25):
        s.append(f'<line x1="{px(g):.1f}" y1="{AY:.1f}" x2="{px(g):.1f}" '
                 f'y2="{AY+AH:.1f}" stroke="{GRID}"/>')
        s.append(txt(px(g), AY + AH + 17, f"{g}", size=9, fill=MUTED, anchor="middle"))
    for g in (0.03, 0.06, 0.09, 0.12):
        s.append(f'<line x1="{AX:.1f}" y1="{py(g):.1f}" x2="{AX+AW:.1f}" '
                 f'y2="{py(g):.1f}" stroke="{GRID}"/>')
        s.append(txt(AX - 8, py(g) + 3, f"{g:.2f}", size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, AY + AH + 36, "average retail price 2022+, cents per kWh",
                 size=10, fill=INK2))
    s.append(f'<text x="{AX-40}" y="{AY+AH:.1f}" font-size="10" fill="{INK2}" '
             f'transform="rotate(-90 {AX-40} {AY+AH:.1f})">'
             f'year-to-year swing in it, 2010 onward</text>')

    # ---- the two marginals: the same states, counted along each axis ----
    # OVERLAID, not stacked. Stacking moves every group's baseline, so a reader cannot
    # read any one region's distribution -- only its share of each bin. The claim here is
    # about where each region LIVES along the axis, which is a statement about its own
    # shape, so every region is drawn from the same baseline at low opacity and the scale
    # is the largest single-region bin rather than the largest total.
    def bars(lo, hi, wid, key, horizontal):
        edges = []
        x = lo
        while x < hi - 1e-9:
            edges.append((x, min(x + wid, hi)))
            x += wid
        counts = [collections.Counter() for _ in edges]
        for r in rows:
            for i, (a, b) in enumerate(edges):
                if a <= r[key] < b or (i == len(edges) - 1 and r[key] >= b):
                    counts[i][r["reg"]] += 1
                    break
        top = max((c.get(reg, 0) for c in counts for reg in ORDER), default=0) or 1
        for reg in ORDER:
            for i, (a, b) in enumerate(edges):
                k = counts[i].get(reg, 0)
                if not k:
                    continue
                if horizontal:
                    x0, x1 = px(a) + 0.6, px(b) - 0.6
                    h = MH * k / top
                    s.append(f'<rect x="{x0:.1f}" y="{MT+MH-h:.1f}" '
                             f'width="{max(x1-x0,1):.1f}" height="{h:.1f}" '
                             f'fill="{COL[reg]}" fill-opacity="0.30" stroke="{COL[reg]}" '
                             f'stroke-width="1.1" stroke-opacity="0.85"/>')
                else:
                    y0b, y1b = py(b) + 0.6, py(a) - 0.6
                    wdt = RW * k / top
                    s.append(f'<rect x="{AX+AW+18:.1f}" y="{y0b:.1f}" width="{wdt:.1f}" '
                             f'height="{max(y1b-y0b,1):.1f}" fill="{COL[reg]}" '
                             f'fill-opacity="0.30" stroke="{COL[reg]}" '
                             f'stroke-width="1.1" stroke-opacity="0.85"/>')
        return top
    tp = bars(PLO, PHI, PBIN, "p", True)
    tv = bars(VLO, VHI, VBIN, "v", False)
    s.append(txt(AX, MT - 22, "how many states at each price", size=9.5, fill=MUTED))
    s.append(txt(AX, MT - 10, f"each region from the same baseline, overlaid not stacked; "
                              f"tallest bar = {tp} states", size=9, fill=MUTED))
    s.append(txt(AX + AW + 18, AY - 20, "and at each swing", size=9.5, fill=MUTED))
    s.append(txt(AX + AW + 18, AY - 8, f"longest bar = {tv} states", size=9,
                 fill=MUTED))

    # ---- the joint panel ----
    s.append(f'<line x1="{px(mp):.1f}" y1="{AY:.1f}" x2="{px(mp):.1f}" '
             f'y2="{AY+AH:.1f}" stroke="{RULE}" stroke-dasharray="3 3"/>')
    s.append(f'<line x1="{AX:.1f}" y1="{py(mv):.1f}" x2="{AX+AW:.1f}" '
             f'y2="{py(mv):.1f}" stroke="{RULE}" stroke-dasharray="3 3"/>')
    for r in rows:
        c = COL[r["reg"]]
        s.append(f'<circle cx="{px(r["p"]):.1f}" cy="{py(r["v"]):.1f}" r="5" fill="{c}" '
                 f'fill-opacity="0.30" stroke="{c}" stroke-width="1.5"/>')
        if r["st"] in NAME:
            s += halo(px(r["p"]) + 8, py(r["v"]) + 4, NAME[r["st"]], size=9, fill=c,
                      weight="700")

    ly = AY + AH + 62
    for i, reg in enumerate(ORDER):
        g = [r for r in rows if r["reg"] == reg]
        x = AX + i * 152
        s.append(f'<circle cx="{x:.1f}" cy="{ly-4:.1f}" r="5.5" fill="{COL[reg]}" '
                 f'fill-opacity="0.35" stroke="{COL[reg]}" stroke-width="1.6"/>')
        s.append(txt(x + 11, ly, f"{reg}  ({len(g)})", size=10, fill=COL[reg],
                     weight="700"))
        s.append(txt(x + 11, ly + 13,
                     f"{statistics.median(v['p'] for v in g):.1f}c, "
                     f"swing {statistics.median(v['v'] for v in g):.3f}", size=9,
                     fill=MUTED))

    TX, ty = W - 214, AY - 44
    for head, body, col in (
            ("along the price axis", "The regions occupy different parts of the range. "
                                     "Adding the nine divisions to a model of grid and "
                                     f"demand features moves adjusted R2 from "
                                     f"{lad['price'][0]:.3f} to "
                                     f"{lad['price'][1]:.3f}.", BLUE),
            ("along the swing axis", f"They sit on top of each other. The same addition "
                                     f"moves adjusted R2 from {lad['price_vol'][0]:.3f} to "
                                     f"{lad['price_vol'][1]:.3f} -- it makes the model "
                                     f"WORSE once the parameters are paid for.", RED),
            ("in the middle", f"Nearly empty. Price and swing correlate at r = {rr:+.2f}, "
                              f"and inside each region at +0.09, +0.09, -0.06 and -0.08. "
                              f"Expensive does not mean unstable.", INK),
            ("why one mark per state", f"Volatility on 2011-17 against 2018-25 -- disjoint "
                                       f"halves -- ranks the states alike, rho "
                                       f"{stab[1]:+.2f}. The ranking is durable.", GREEN),
            ("but not the level", "The median state moved 0.020-0.037 a year to 2020 and "
                                  "0.086 in 2022. This axis contains a gas shock.",
             AMBER)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        w = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=29, leading=12.5)
        s += w
        ty += 12.5 * len(w) + 15

    foot = (
        "EIA ELEC bulk file, no key, fetched 2026-09-23; ELEC.PRICE against ELEC.GEN and "
        "ELEC.SALES, state-quarters, US census regions and divisions. BOTH axes cover 2018 "
        "to 2025; the swing ranks states the same way on 2011-2017 (rho +0.62). CAVEAT: "
        "this is REGULATED RETAIL price, and 2022 was a gas shock -- the ranking on the "
        "swing axis is durable, its level is not. Hawaii and Alaska are excluded.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=176, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=176, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {n} states; price vs swing r {rr:+.2f}, {diag} of {n} on the diagonal")
    print(f"    adjusted R2 price      {lad['price'][0]:.3f} -> {lad['price'][1]:.3f}")
    print(f"    adjusted R2 volatility {lad['price_vol'][0]:.3f} -> "
          f"{lad['price_vol'][1]:.3f}")
    for reg in ORDER:
        g = [r for r in rows if r["reg"] == reg]
        wr = price.corr([(x["p"], x["v"]) for x in g])[0]
        print(f"      {reg:<11}n={len(g):>3}  {statistics.median(x['p'] for x in g):>6.2f}c"
              f"  swing {statistics.median(x['v'] for x in g):.3f}  within r {wr:+.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
