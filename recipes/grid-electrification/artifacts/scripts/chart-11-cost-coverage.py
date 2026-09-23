#!/usr/bin/env python3
"""No fossil or storage technology in the ATB has a levelised cost. Eight of twenty.

    python3 chart-3-coverage.py

The comparison everyone wants from this file is renewables against gas. **It cannot be made
inside it.**

`NaturalGas_FE` publishes capital cost, overnight capital cost, fixed and variable O&M and a
heat rate. It publishes **no levelised cost and no capacity factor**, and neither does coal,
neither do the retrofit families, and neither does any of the four storage technologies.
Twelve technologies carry an LCOE; eight do not, and the eight are exactly the dispatchable
ones.

**The reason is structural rather than an omission.** A levelised cost needs to be divided by
the energy produced, and for a dispatchable plant that depends on how often it is asked to
run and what its fuel costs on the day. ATB sets neither. For wind and solar the same two
numbers are properties of the site and the weather, which ATB does model, so the division is
defined.

**Which makes the familiar chart a splice.** Every "solar is now cheaper than gas" comparison
sourced to ATB took the solar number from here and the gas number from somewhere else -- EIA's
Annual Energy Outlook, a Lazard study, an internal model. The comparison then inherits that
source's fuel price and capacity factor assumptions, and those are doing more work than
anything on the ATB side. None of that is visible in a chart with two bars on it.

**Storage hides its capital cost under a different name.** The four storage families publish
`OCC` and not `CAPEX`, so a script that looks only for CAPEX concludes they have no capital
cost at all. They have one. This figure draws both columns for exactly that reason.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import atbfold, plate                                                    # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "11-cost-coverage.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
COLS = [("OCC", "overnight\ncapital"), ("CAPEX", "capital\ncost"),
        ("Fixed O&M", "fixed\nO&M"), ("Variable O&M", "variable\nO&M"),
        ("Heat Rate", "heat\nrate"), ("CF", "capacity\nfactor"),
        ("LCOE", "levelised\ncost")]
FAMILY = {"Coal_FE": "fossil", "Coal_Retrofits": "fossil", "NaturalGas_FE": "fossil",
          "NaturalGas_Retrofits": "fossil", "Commercial Battery Storage": "storage",
          "Residential Battery Storage": "storage", "Pumped Storage Hydropower": "storage",
          "Utility-Scale Battery Storage": "storage"}
NICE = {"NaturalGas_FE": "Natural gas", "NaturalGas_Retrofits": "Natural gas retrofit",
        "Coal_FE": "Coal", "Coal_Retrofits": "Coal retrofit",
        "Utility-Scale Battery Storage": "Utility battery",
        "Commercial Battery Storage": "Commercial battery",
        "Residential Battery Storage": "Residential battery",
        "Pumped Storage Hydropower": "Pumped hydro", "LandbasedWind": "Land-based wind",
        "OffShoreWind": "Offshore wind", "DistributedWind": "Distributed wind",
        "UtilityPV": "Utility solar", "CommPV": "Commercial solar", "ResPV": "Residential solar",
        "CSP": "Concentrating solar", "Utility-Scale PV-Plus-Battery": "Solar plus battery",
        "Geothermal": "Geothermal", "Hydropower": "Hydropower", "Nuclear": "Nuclear",
        "Biopower": "Biopower"}


def main():
    d = atbfold.load()
    cover = d["cover"]
    order = sorted(cover, key=lambda t: ({"fossil": 0, "storage": 1}.get(FAMILY.get(t), 2),
                                         -len([c for c in COLS if cover[t].get(c[0])]),
                                         NICE.get(t, t)))
    nolcoe = [t for t in order if not cover[t].get("LCOE")]

    W = 1000
    H = 250 + 30 * len(order) + 132
    s = plate.open_svg(
        W, H, "No fossil or storage technology in the ATB has a levelised cost",
        subtitle=f"What each of the {len(order)} technologies actually publishes. "
                 f"{len(nolcoe)} carry no levelised cost and no capacity factor, and they "
                 f"are exactly the dispatchable ones.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone comparing a renewable cost against a gas or storage cost",
        decide="whether the two sides of that comparison came from the same file",
        wrong="the missing cells are scattered, rather than falling in one block")
    s += fr

    AX = 232
    CW = 86
    top = y0 + 74
    for j, (_, lab) in enumerate(COLS):
        x = AX + CW * j + CW / 2
        for k, part in enumerate(lab.split("\n")):
            s.append(txt(x, top - 32 + 12 * k, part, size=9.5, fill=INK2, anchor="middle",
                         weight="700" if k == 0 else "normal"))

    lastfam = None
    for i, t in enumerate(order):
        y = top + 30 * i + 10
        fam = FAMILY.get(t, "all others")
        if fam != lastfam:
            if lastfam is not None:
                s.append(f'<line x1="28" y1="{y-16:.1f}" x2="{W-28}" y2="{y-16:.1f}" '
                         f'stroke="{RULE}"/>')
            s.append(txt(28, y + 4, fam, size=9.5, fill=MUTED, weight="700"))
            lastfam = fam
        col = RED if not cover[t].get("LCOE") else BLUE
        s.append(txt(AX - 14, y + 4, NICE.get(t, t), size=10.5, fill=INK, anchor="end"))
        for j, (key, _) in enumerate(COLS):
            x = AX + CW * j + CW / 2
            if cover[t].get(key):
                s.append(f'<rect x="{x-24:.1f}" y="{y-8:.1f}" width="48" height="16" '
                         f'rx="2.5" fill="{col}" fill-opacity="0.24" stroke="{col}" '
                         f'stroke-width="1.1"/>')
            else:
                s.append(f'<line x1="{x-9:.1f}" y1="{y:.1f}" x2="{x+9:.1f}" '
                         f'y2="{y:.1f}" stroke="{FAINT}" stroke-width="1.4"/>')

    bot = top + 30 * len(order) + 6
    s += halo(AX, bot + 20, "a filled cell is published; a dash is not published",
              size=10, fill=MUTED)
    s += halo(AX, bot + 38, "the two missing columns are the two that need a fuel price and "
              "a dispatch assumption", size=10.5, fill=RED, weight="700")
    s += halo(AX, bot + 53, "so every renewables-against-gas comparison sourced to this file "
              "took the gas number from another one", size=10.5, fill=RED)

    foot = (
        "NREL Annual Technology Baseline, 2023 vintage, ATBe.csv from the Open Energy Data "
        "Initiative lake; fetched 2026-09-23, no key. A cell is filled where the file "
        "contains at least one row of that parameter for that technology. CAVEAT: this shows "
        "what is published, not what could be computed -- a gas levelised cost can be derived "
        "from the heat rate and O&M here given a fuel price and a capacity factor, but both "
        "of those must be brought from outside.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=150, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {len(nolcoe)} of {len(order)} publish no LCOE: "
          f"{', '.join(NICE.get(t, t) for t in nolcoe)}")
    nocf = [t for t in order if not cover[t].get("CF")]
    print(f"    {len(nocf)} publish no capacity factor -- same set: "
          f"{sorted(nocf) == sorted(nolcoe)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
