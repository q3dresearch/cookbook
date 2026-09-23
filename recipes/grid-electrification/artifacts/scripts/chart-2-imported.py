#!/usr/bin/env python3
"""A grid's own fuel mix is not what its customers consume.

    python3 chart-2-imported.py

Every balancing authority publishes two things that sound like the same fact: the mix of fuel
it *generates*, and the carbon in the electricity its customers actually *consume*, imports
included. They disagree, and the disagreement is systematic.

**Seattle City Light generates 100% carbon-free and consumes at 57 kg CO2 per MWh.** Puget
Sound Energy, next door, generates only **40%** carbon-free -- and consumes at **133**, among
the cleanest in the country, because it generates just 23% of what it uses and buys the rest
from Bonneville's hydro.

**And it runs the other way.** Northwestern Energy generates 43% carbon-free, better than
Puget Sound, and its customers consume at **582 kg/MWh** -- four times the carbon. It
generates 155% of its own demand and exports the clean part.

**Which makes own-generation share the flattering number wherever a grid imports.** Ten of the
forty balancing authorities here generate under 75% of what they consume, so their fuel mix
describes a minority of the power they deliver. Any siting decision made on that number is
made on the wrong one, and the right one is published beside it.

**The intensity is summed over matched hours.** Consumption-based CO2 begins in July 2024
and covers 87.5% of 2025, while demand covers all of it. Dividing one annual total by the
other understates every intensity here by 11% to 15% -- not by a constant, so it moves the
ranking as well as the levels. `matched.py` keeps both series hourly and sums them over
their intersection instead.

**What this cannot show.** Contracts. A power purchase agreement lets a buyer claim renewable
supply while the wires deliver the local mix; nothing here sees a PPA. This measures what the
wires carried.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import eba, matched, plate                                               # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "2-imported.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
CLEAN = ("WAT", "SUN", "WND", "NUC", "GEO")
Y = "2025"


def main():
    d = eba.load()
    # The intensity comes from matched.py, which sums CO2 and demand over the hours BOTH
    # series cover. The annual totals in eba.py divide a numerator missing an eighth of the
    # year by a complete denominator, which understates every grid here by 11% to 15%.
    mh = matched.load()["ba"]
    rows = []
    for c, v in d["ba"].items():
        dem = v.get("D", {}).get(Y)
        gen = {k[3:]: s.get(Y, 0.0) for k, s in v.items() if k.startswith("NG.")}
        tot = sum(gen.values())
        con = (mh.get(c) or {}).get("intensity")
        if not dem or not con or dem < 8e6 or not tot:
            continue
        rows.append({"ba": c, "twh": dem / 1e6,
                     "own": sum(gen.get(k, 0.0) for k in CLEAN) / tot,
                     "int": con, "cover": tot / dem})
    rows.sort(key=lambda r: -r["twh"])
    imp = [r for r in rows if r["cover"] < 0.75]

    W, H = 1180, 830
    s = plate.open_svg(
        W, H, "A grid's own fuel mix is not what its customers consume",
        subtitle=f"{len(rows)} US balancing authorities in {Y}. Horizontal: the carbon-free "
                 f"share of what each one generates. Vertical: the carbon in what its "
                 f"customers actually use, imports included.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone siting a load on a grid's published renewable share",
        decide="whether to judge a grid by what it generates or by what it delivers",
        wrong="the marks fall on a single downward line, or the importers sit on it with "
              "everyone else")
    s += fr

    AX, AY, AW, AH = 92, y0 + 66, W - 210, 470
    ax = lambda v: AX + 54 + (AW - 78) * v
    ay = lambda v: AY + AH - 46 - (AH - 64) * min(v, 750) / 750
    s.append(txt(AX - 64, AY - 38, "what it generates, against what it delivers",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(AX - 64, AY - 21, "area is demand; a hollow ring marks a grid that "
                                   "generates under 75% of what it consumes",
                 size=10, fill=MUTED))
    for g in (0, 0.25, 0.5, 0.75, 1.0):
        s.append(f'<line x1="{ax(g):.1f}" y1="{ay(0):.1f}" x2="{ax(g):.1f}" '
                 f'y2="{ay(750):.1f}" stroke="{GRID}"/>')
        s.append(txt(ax(g), ay(0) + 17, f"{g:.0%}", size=9, fill=MUTED, anchor="middle"))
    for v in (0, 150, 300, 450, 600, 750):
        s.append(f'<line x1="{ax(0):.1f}" y1="{ay(v):.1f}" x2="{ax(1):.1f}" '
                 f'y2="{ay(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(ax(0) - 8, ay(v) + 3, f"{v:,}", size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX - 64, ay(0) + 36, "carbon-free share of the grid's OWN generation",
                 size=9.5, fill=MUTED))
    s.append(f'<text x="{AX-42}" y="{ay(0):.1f}" font-size="9.5" fill="{INK2}" '
             f'transform="rotate(-90 {AX-42} {ay(0):.1f})">'
             f'kg CO2 per MWh CONSUMED, imports included</text>')
    LAB = {"SCL": (1, -9), "BPAT": (1, 4), "PSEI": (-1, 4), "PGE": (-1, 4),
           "PACW": (1, -9), "NWMT": (1, 4), "LGEE": (-1, 4), "SC": (-1, 4),
           "WACM": (1, 4), "ERCO": (1, 4), "CISO": (1, -9), "MISO": (1, 4),
           "PJM": (-1, 4), "SOCO": (1, 4), "AECI": (1, 4), "PACE": (-1, 4)}
    for r in rows:
        rad = max(3.4, math.sqrt(r["twh"]) / 1.5)
        importer = r["cover"] < 0.75
        col = BLUE if importer else SLATE
        s.append(f'<circle cx="{ax(r["own"]):.1f}" cy="{ay(r["int"]):.1f}" r="{rad:.1f}" '
                 f'fill="{"none" if importer else col}" fill-opacity="0.22" '
                 f'stroke="{col}" stroke-width="{2.0 if importer else 1.2:.1f}"/>')
        if r["ba"] in LAB:
            sx, dy = LAB[r["ba"]]
            s += halo(ax(r["own"]) + sx * (rad + 5), ay(r["int"]) + dy, r["ba"], size=9.5,
                      fill=col, anchor="start" if sx > 0 else "end", weight="700")
    # the two that make the point, joined only by an annotation, not by a mark
    for ba, txt2 in (("PSEI", "generates 40% clean, consumes at 133"),
                     ("NWMT", "generates 43% clean, consumes at 582")):
        r = next(x for x in rows if x["ba"] == ba)
        s += halo(ax(r["own"]), ay(r["int"]) + (26 if ba == "PSEI" else -20), txt2,
                  size=9.5, fill=BLUE if ba == "PSEI" else RED, anchor="middle",
                  weight="700")
    s += halo(ax(0.02), ay(720), f"{len(imp)} of {len(rows)} generate under 75% of what "
              f"they consume", size=9.5, fill=BLUE, weight="700")
    s += halo(ax(0.02), ay(720) - 13, "for those, the horizontal axis describes a minority "
              "of their power", size=9.5, fill=INK2)

    foot = (
        "EIA Hourly Electric Grid Monitor (EBA) bulk file, no key, fetched 2026-09-23. "
        "Consumed carbon and demand are summed over the 7,666 hours of 2025 that both series "
        "cover: CO2 reporting began mid-2024, and an annual ratio understates every intensity "
        "by 11% to 15%. Carbon-free counts water, sun, wind, nuclear and geothermal at "
        "generation. CAVEAT: this is what the wires carried, not what anyone contracted for "
        "-- a power purchase agreement is invisible here. Under 8 TWh is not drawn.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=178, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=178, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {len(rows)} BAs; {len(imp)} generate under 75% of demand")
    for r in sorted(rows, key=lambda x: x["int"])[:3] + sorted(rows, key=lambda x: -x["int"])[:3]:
        hb = mh[r["ba"]]["hours_both"]
        print(f"      {r['ba']:<6}own {r['own']:>5.0%}  consumed {r['int']:>5,.0f} kg/MWh  "
              f"gen/dem {r['cover']:>4.0%}  over {hb:,} matched hours")
    return 0


if __name__ == "__main__":
    sys.exit(main())
