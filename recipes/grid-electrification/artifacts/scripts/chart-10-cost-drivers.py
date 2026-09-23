#!/usr/bin/env python3
"""For wind and solar, where you put it decides the cost. For nuclear, the loan does.

    python3 chart-2-drivers.py

Figure 9 showed that a single ATB technology carries up to 120 published costs. This one
separates the four choices that produce them, by asking of each: **holding everything else
as published, how far does moving this one dimension alone shift the median?**

- **where you put it** -- the resource class, which for wind and solar is a proxy for site
  quality and therefore for how much energy comes out per dollar installed
- **whether tax credits count** -- ATB's Market case counts them and its R&D case does not
- **technology optimism** -- the Conservative, Moderate and Advanced progress scenarios
- **the financing period** -- how many years the cost recovery is spread across

**The ordering is not the same for every technology, and that is the finding.** Land-based
wind moves **3.4x on siting** and 1.2x on financing. Nuclear moves **1.3x on financing** and
1.02x on siting -- essentially nothing, because a reactor's output does not depend on the
weather where it stands. A single sensitivity analysis applied across technologies is
therefore testing the wrong variable for most of them.

**What this says about the question "what does it cost by location".** For wind and solar,
ATB's capital cost is **identical across every resource class** -- utility solar is $1,038
per kW in 2030 in Class 1 and in Class 10. Location does not change what you pay to build.
It changes what you get out, and the whole location effect arrives through the capacity
factor into the levelised cost. Anyone looking for regional capex in this file will not find
it, because ATB does not model it.

**Tax credits are the second lever and the most perishable.** The Market-against-R&D gap is
2.2x for land-based wind. It is a policy setting, not a property of the technology, and a
quoted cost that does not say which case it came from is not reproducible.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import atbfold, plate                                                    # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "10-cost-drivers.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
DIM = [("detail", "where you put it", RED),
       ("case", "whether tax credits count", AMBER),
       ("scenario", "technology optimism", GREEN),
       ("crp", "the financing period", BLUE)]
NICE = {"LandbasedWind": "Land-based wind", "Geothermal": "Geothermal",
        "DistributedWind": "Distributed wind", "Hydropower": "Hydropower",
        "OffShoreWind": "Offshore wind", "UtilityPV": "Utility solar",
        "ResPV": "Residential solar", "CommPV": "Commercial solar",
        "CSP": "Concentrating solar", "Nuclear": "Nuclear", "Biopower": "Biopower",
        "Utility-Scale PV-Plus-Battery": "Utility solar plus battery"}
XLO, XHI = 0.98, 5.6


def main():
    d = atbfold.load()
    Y = d["focus"]
    rows = []
    for t in NICE:
        rec = atbfold.spread(d, t, "LCOE")
        if not rec:
            continue
        mult = {}
        for dim, _, _ in DIM:
            m = rec.get(dim)
            if m and len(m) > 1 and min(m.values()):
                mult[dim] = max(m.values()) / min(m.values())
        if len(mult) >= 3:
            rows.append(dict(t=t, mult=mult, top=max(mult, key=mult.get)))
    rows.sort(key=lambda r: -r["mult"][r["top"]])

    W = 1160
    H = 268 + 40 * len(rows) + 116
    s = plate.open_svg(
        W, H, "For wind and solar, where you put it decides the cost. For nuclear, the "
              "loan does.",
        subtitle=f"Each of the four choices behind an ATB levelised cost in {Y}, and how far "
                 f"moving that one alone shifts the median. 1.0x means the choice makes no "
                 f"difference.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone running a sensitivity analysis on generation cost, or quoting one number",
        decide="which assumption to state alongside a cost, and which to vary in a test",
        wrong="the same dimension dominates every technology")
    s += fr

    ly = y0 + 46
    for i, (_, lab, col) in enumerate(DIM):
        x = 268 + i * 218
        s.append(f'<circle cx="{x:.1f}" cy="{ly-4:.1f}" r="5" fill="{col}" '
                 f'fill-opacity="0.25" stroke="{col}" stroke-width="1.6"/>')
        s.append(txt(x + 11, ly, lab, size=10, fill=col, weight="700"))

    AX, AW = 268, W - 400
    lx = lambda v: AX + AW * (math.log10(max(v, XLO)) - math.log10(XLO)) / (
        math.log10(XHI) - math.log10(XLO))
    top = ly + 70
    bot = top + 40 * len(rows) - 12
    for g in (1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0):
        one = abs(g - 1.0) < 1e-9
        s.append(f'<line x1="{lx(g):.1f}" y1="{top-14:.1f}" x2="{lx(g):.1f}" '
                 f'y2="{bot:.1f}" stroke="{RULE if one else GRID}" '
                 f'stroke-width="{1.4 if one else 1}"/>')
        s.append(txt(lx(g), top - 22, f"{g:g}x", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, top - 40, "how far this one choice alone moves the median cost "
                               "(log scale)", size=10, fill=INK2))

    for i, r in enumerate(rows):
        y = top + 40 * i + 8
        s.append(txt(AX - 16, y + 4, NICE[r["t"]], size=11, fill=INK, anchor="end"))
        s.append(f'<line x1="{lx(XLO):.1f}" y1="{y:.1f}" '
                 f'x2="{lx(max(r["mult"].values())):.1f}" y2="{y:.1f}" stroke="{FAINT}" '
                 f'stroke-width="1"/>')
        for dim, lab, col in DIM:
            v = r["mult"].get(dim)
            if v is None:
                continue
            lead = dim == r["top"]
            s.append(f'<circle cx="{lx(v):.1f}" cy="{y:.1f}" r="{6.6 if lead else 5:.1f}" '
                     f'fill="{col}" fill-opacity="{0.34 if lead else 0.18}" '
                     f'stroke="{col}" stroke-width="{2.0 if lead else 1.3}"/>')
        tcol = dict((k, c) for k, _, c in DIM)[r["top"]]
        s.append(txt(W - 124, y + 4, f"{r['mult'][r['top']]:.2f}x", size=11, fill=tcol,
                     weight="700"))
        s.append(txt(W - 78, y + 4, dict((k, l) for k, l, _ in DIM)[r["top"]].split()[-1]
                     if r["top"] != "detail" else "siting", size=9, fill=MUTED))

    pv = next(r for r in rows if r["t"] == "UtilityPV")
    s += halo(AX, bot + 28, "utility solar capital cost in 2030 is $1,038 per kW in resource "
              "class 1 and $1,038 in class 10", size=10.5, fill=INK2, weight="700")
    s += halo(AX, bot + 43, "location does not change what you pay to build; it changes what "
              "comes out, and reaches the cost through the capacity factor", size=10.5,
              fill=INK2)

    foot = (
        "NREL Annual Technology Baseline, 2023 vintage, ATBe.csv from the Open Energy Data "
        "Initiative lake; fetched 2026-09-23, no key. Each multiplier is the ratio of the "
        "highest to the lowest median across that dimension's levels, with the other three "
        "dimensions left as published. CAVEAT: ATB is a model output and 2030 is a "
        "projection; the tax-credit multiplier reflects policy as assumed in the 2023 "
        "vintage and is the least durable number here.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for r in rows:
        print(f"    {NICE[r['t']]:<28}" + "  ".join(
            f"{k}={r['mult'].get(k, float('nan')):.2f}x" for k, _, _ in DIM)
            + f"   led by {r['top']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
