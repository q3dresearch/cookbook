#!/usr/bin/env python3
"""There is no ATB cost of land-based wind. There are 120, and they span 23-fold.

    python3 chart-1-spread.py

NREL's Annual Technology Baseline is where most public statements about what generation
costs ultimately come from. It does not publish a cost. It publishes a **grid** of costs,
and every cell in it is the official number for some set of assumptions.

**Land-based wind in 2030: 120 published LCOE values, from $3.1 to $73.0 per MWh.** Every one
of them is correctly sourced to ATB. A writer who wants wind to look cheap and a writer who
wants it to look expensive can both cite this file, without either of them misquoting it.

**The spread is not uncertainty.** It is four explicit choices, and figure 10 separates them:
where the plant goes, whether tax credits are counted, which technology-progress scenario is
assumed, and how long the financing runs. None of those is a confidence interval, and
averaging across them produces a number that describes no project.

**Biopower spans 1.2x and land-based wind spans 23.5x**, which is the practical point: how
badly a single quoted figure misleads depends entirely on which technology it is about. For
nuclear the choice barely matters. For wind it decides the answer.

**Eight of the twenty technologies publish no LCOE at all** -- every fossil family and every
storage family. That is figure 11, and it is the more consequential gap.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import atbfold, plate                                                    # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "9-cost-spread.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
XLO, XHI = 2.5, 620.0
NICE = {"LandbasedWind": "Land-based wind", "DistributedWind": "Distributed wind",
        "Geothermal": "Geothermal", "Hydropower": "Hydropower", "UtilityPV": "Utility solar",
        "OffShoreWind": "Offshore wind", "CommPV": "Commercial solar",
        "ResPV": "Residential solar", "CSP": "Concentrating solar",
        "Utility-Scale PV-Plus-Battery": "Utility solar plus battery", "Nuclear": "Nuclear",
        "Biopower": "Biopower"}


def main():
    d = atbfold.load()
    Y = d["focus"]
    rows = []
    for k, v in d["cell"].items():
        t, p, y = k.split("|")
        if p != "LCOE" or y != Y or t not in NICE:
            continue
        rows.append(dict(t=t, lo=v["min"], med=v["med"], hi=v["max"], n=v["n"],
                         span=v["max"] / v["min"]))
    rows.sort(key=lambda r: -r["span"])
    nolcoe = sorted(t for t in d["cover"] if "LCOE" not in d["cover"][t])

    W = 1160
    H = 250 + 40 * len(rows) + 120
    s = plate.open_svg(
        W, H, f"There is no ATB cost of land-based wind. There are 120, and they span "
              f"23-fold.",
        subtitle=f"Levelised cost in {Y}, every published value. The bar is the full range "
                 f"of official numbers; the tick is their median. {len(nolcoe)} further "
                 f"technologies publish no LCOE at all -- see figure 11.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone about to quote what a generation technology costs",
        decide="whether a single ATB figure is safe to quote for this technology",
        wrong="the ranges are narrow, or they do not overlap each other")
    s += fr

    AX, AW = 268, W - 430
    lx = lambda v: AX + AW * (math.log10(max(v, XLO)) - math.log10(XLO)) / (
        math.log10(XHI) - math.log10(XLO))
    top = y0 + 56
    for g in (3, 10, 30, 100, 300, 600):
        s.append(f'<line x1="{lx(g):.1f}" y1="{top-14:.1f}" x2="{lx(g):.1f}" '
                 f'y2="{top + 40*len(rows) - 12:.1f}" stroke="{GRID}"/>')
        s.append(txt(lx(g), top - 22, f"${g}", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, top - 40, f"levelised cost of energy, dollars per MWh, {Y} "
                               f"(log scale)", size=10, fill=INK2))

    for i, r in enumerate(rows):
        y = top + 40 * i + 8
        col = RED if r["span"] >= 6 else (AMBER if r["span"] >= 3 else BLUE)
        s.append(txt(AX - 16, y + 4, NICE[r["t"]], size=11, fill=INK, anchor="end"))
        s.append(f'<line x1="{lx(r["lo"]):.1f}" y1="{y:.1f}" x2="{lx(r["hi"]):.1f}" '
                 f'y2="{y:.1f}" stroke="{col}" stroke-width="9" stroke-opacity="0.26" '
                 f'stroke-linecap="butt"/>')
        for v in (r["lo"], r["hi"]):
            s.append(f'<line x1="{lx(v):.1f}" y1="{y-7:.1f}" x2="{lx(v):.1f}" '
                     f'y2="{y+7:.1f}" stroke="{col}" stroke-width="1.6"/>')
        s.append(f'<line x1="{lx(r["med"]):.1f}" y1="{y-9:.1f}" x2="{lx(r["med"]):.1f}" '
                 f'y2="{y+9:.1f}" stroke="{col}" stroke-width="2.6"/>')
        s.append(txt(lx(r["lo"]) - 7, y + 3.5, f"{r['lo']:,.0f}", size=9, fill=col,
                     anchor="end"))
        s.append(txt(lx(r["hi"]) + 7, y + 3.5, f"{r['hi']:,.0f}", size=9, fill=col))
        s.append(txt(W - 128, y + 4, f"{r['span']:.1f}x", size=11, fill=col, weight="700"))
        s.append(txt(W - 88, y + 4, f"{r['n']} values", size=9, fill=MUTED))

    base = top + 40 * len(rows) + 6
    wind = rows[0]
    s += halo(AX, base + 18, f"the widest and the narrowest differ by a factor of "
              f"{wind['span']/rows[-1]['span']:.0f} in how much the choice matters",
              size=10.5, fill=INK2, weight="700")
    s += halo(AX, base + 33, "so 'what does it cost' has a safe single answer for some of "
              "these technologies and no safe single answer for others", size=10.5,
              fill=INK2)

    foot = (
        "NREL Annual Technology Baseline, 2023 vintage, ATBe.csv from the Open Energy Data "
        "Initiative lake; fetched 2026-09-23, no key. CAVEAT: ATB is a MODEL OUTPUT, not a "
        "record of transactions -- nobody paid these prices. Its 2021-2023 values are the "
        "vintage year's estimates and everything after is projection, so 2030 here is a "
        "projection. Ranges are across scenario, tax-credit case, financing period and "
        "resource class; they are not confidence intervals.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for r in rows[:3] + rows[-2:]:
        print(f"    {NICE[r['t']]:<28}{r['lo']:>8,.1f} to {r['hi']:>8,.1f}  "
              f"{r['span']:>5.1f}x  on {r['n']} values")
    print(f"    {len(nolcoe)} technologies publish no LCOE: {', '.join(nolcoe)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
