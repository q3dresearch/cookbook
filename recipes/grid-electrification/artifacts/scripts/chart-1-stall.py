#!/usr/bin/env python3
"""US electrification tripled, then stopped in 2000 -- and the apparent reversal is the
generators getting better.

    python3 chart-1-stall.py

Electricity as a share of the energy a country actually uses has two defensible bases, and
they answer differently:

- **at the meter**, electricity delivered against total end-use energy: 6.0% in 1960, 16.2%
  by 2000, **18.0% in 2024**. Most of that journey was over before 2000; twenty-four years
  since moved it 1.8 points.
- **including the fuel burned to make it**, adding transmission and generation losses to both
  sides: 16.1% in 1960, 37.3% in 2000, **34.7% in 2024**. On this basis electrification has
  been *falling* for two decades.

**The reversal is not a decline in electrification.** Electricity delivered rose 16.2% from
2000 to 2024. The losses attributed to delivering it fell **21.3%**, because generation got
more efficient -- 2.09 units of loss per unit delivered in 2000 against **1.42** in 2024, a
32% improvement. The primary ratio fell because its numerator's *waste* component shrank
faster than its useful component grew.

**Which is why the two lines have to be drawn together.** Either alone supports a headline the
other contradicts, and the second panel is the arithmetic that reconciles them.

**What this cannot show.** Why end uses stopped converting. The denominator is dominated by
transport and industrial heat, and this plate measures that they did not electrify, not what
stopped them. Electric-vehicle charging, the one series that isolates the conversion, is 2.35%
of California's electricity in 2024 and less than half a point of Texas's.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate, seds                                                       # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "1-stall.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
YEARS = [str(y) for y in range(1960, 2025)]


def main():
    d = seds.load()
    us = d["states"]["US"]
    site, prim, ratio = {}, {}, {}
    for y in YEARS:
        e, t, lo = us["ESTXB"].get(y), us["TNTCB"].get(y), us["LOTXB"].get(y)
        if None in (e, t, lo) or not t:
            continue
        site[y] = e / t
        prim[y] = (e + lo) / (t + lo)
        ratio[y] = lo / e
    ys = sorted(site)
    W, H = 1240, 836
    s = plate.open_svg(
        W, H,
        "US electrification tripled, then stopped in 2000",
        subtitle=f"Electricity as a share of the energy the country uses, on both defensible "
                 f"bases. {ys[0]} to {ys[-1]}, from EIA's State Energy Data System.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone sizing how much more of civilisation's energy could arrive as "
            "electricity",
        decide="whether electrification is still advancing, and on which basis the "
               "question was asked",
        wrong="the two bases move together after 2000, or the primary ratio falls because "
              "delivered electricity fell")
    s += fr

    # ---- panel A: the two ratios ------------------------------------------
    AX, AY, AW, AH = 64, y0 + 62, 556, 400
    ax = lambda y: AX + 52 + (AW - 70) * (int(y) - 1960) / (2024 - 1960)
    ay = lambda v: AY + AH - 40 - (AH - 58) * v / 0.42
    s.append(txt(AX - 36, AY - 36, "the same quantity, two bases", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(AX - 36, AY - 19, "at the meter, and including the fuel burned to deliver "
                                   "it", size=10, fill=MUTED))
    for g in (0.0, 0.1, 0.2, 0.3, 0.4):
        s.append(f'<line x1="{ax("1960"):.1f}" y1="{ay(g):.1f}" x2="{ax("2024"):.1f}" '
                 f'y2="{ay(g):.1f}" stroke="{GRID}"/>')
        s.append(txt(ax("1960") - 8, ay(g) + 3, f"{g:.0%}", size=9, fill=MUTED,
                     anchor="end"))
    for y in ("1960", "1980", "2000", "2020"):
        s.append(txt(ax(y), ay(0) + 16, y, size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX - 36, ay(0) + 34, "year", size=9.5, fill=MUTED))
    s.append(f'<text x="{AX-16}" y="{ay(0):.1f}" font-size="9.5" fill="{INK2}" '
             f'transform="rotate(-90 {AX-16} {ay(0):.1f})">'
             f"electricity's share of the energy actually used</text>")
    # 2000 is where both series turn, so it is marked once
    s.append(f'<line x1="{ax("2000"):.1f}" y1="{ay(0):.1f}" x2="{ax("2000"):.1f}" '
             f'y2="{ay(0.42):.1f}" stroke="{FAINT}" stroke-dasharray="3 3"/>')
    s += halo(ax("2000") + 5, ay(0.41), "2000", size=9, fill=MUTED, weight="700")
    for key, col, lab in ((prim, RED, "including generation and grid losses"),
                          (site, BLUE, "as delivered to the meter")):
        pts = [(ax(y), ay(key[y])) for y in ys]
        s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                        for i, (a, b) in enumerate(pts))
                 + f'" fill="none" stroke="{col}" stroke-width="2.4"/>')
        s += halo(ax("2024") + 7, ay(key["2024"]) + 3, f"{key['2024']:.1%}", size=11,
                  fill=col, weight="700")
        s += halo(ax("1996"), ay(key["1996"]) - 10, lab, size=9.5, fill=col, anchor="end",
                  weight="700")
    s += halo(ax("2002"), ay(0.055), f"1960-2000: {site['1960']:.1%} to {site['2000']:.1%}",
              size=9.5, fill=INK2, anchor="end", weight="700")
    s += halo(ax("2002") + 6, ay(0.055), f"2000-2024: to {site['2024']:.1%}",
              size=9.5, fill=INK2, weight="700")

    # ---- panel B: why the red line falls ----------------------------------
    BX, BY, BW, BH = 700, AY, 476, 400
    bx = lambda y: BX + 56 + (BW - 76) * (int(y) - 1960) / (2024 - 1960)
    by = lambda v: BY + BH - 40 - (BH - 58) * (v - 1.2) / (2.4 - 1.2)
    s.append(txt(BX - 30, AY - 36, "and why the red line turns down", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(BX - 30, AY - 19, "units of energy lost per unit of electricity actually "
                                   "delivered", size=10, fill=MUTED))
    for g in (1.2, 1.5, 1.8, 2.1, 2.4):
        s.append(f'<line x1="{bx("1960"):.1f}" y1="{by(g):.1f}" x2="{bx("2024"):.1f}" '
                 f'y2="{by(g):.1f}" stroke="{GRID}"/>')
        s.append(txt(bx("1960") - 8, by(g) + 3, f"{g:.1f}", size=9, fill=MUTED,
                     anchor="end"))
    for y in ("1960", "1980", "2000", "2020"):
        s.append(txt(bx(y), by(1.2) + 16, y, size=9, fill=MUTED, anchor="middle"))
    s.append(txt(bx("1960") - 8, by(1.2) + 34, "year", size=9.5, fill=MUTED))
    pts = [(bx(y), by(ratio[y])) for y in ys]
    s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                    for i, (a, b) in enumerate(pts))
             + f'" fill="none" stroke="{AMBER}" stroke-width="2.4"/>')
    s.append(f'<line x1="{bx("2000"):.1f}" y1="{by(1.2):.1f}" x2="{bx("2000"):.1f}" '
             f'y2="{by(2.4):.1f}" stroke="{FAINT}" stroke-dasharray="3 3"/>')
    for y, side in (("2000", 1), ("2024", -1)):
        s.append(f'<circle cx="{bx(y):.1f}" cy="{by(ratio[y]):.1f}" r="4.2" '
                 f'fill="{AMBER}"/>')
        s += halo(bx(y) + side * 8, by(ratio[y]) + 3, f"{ratio[y]:.2f}", size=11,
                  fill=AMBER, weight="700", anchor="start" if side > 0 else "end")
    s += halo(bx("1963"), by(1.38), "flat for forty years, then a 32% improvement",
              size=9.5, fill=INK2, weight="700")
    s += halo(bx("1963"), by(1.38) - 13, "in the fuel burned per unit delivered",
              size=9.5, fill=INK2)

    cy = AY + AH + 62
    s.append(txt(28, cy, "so the reversal is the generators improving, not the country "
                         "un-electrifying", size=12, fill=INK, weight="600"))
    e0, e1 = us["ESTXB"]["2000"], us["ESTXB"]["2024"]
    l0, l1 = us["LOTXB"]["2000"], us["LOTXB"]["2024"]
    s += wrap(28, cy + 20,
              f"From 2000 to 2024 electricity delivered rose {e1/e0-1:.1%}, from "
              f"{e0/3412:,.0f} to {e1/3412:,.0f} TWh. The losses attributed to delivering it "
              f"fell {1-l1/l0:.1%}. The primary ratio is a fraction whose numerator contains "
              f"both, so it falls when the waste term shrinks faster than the useful term "
              f"grows -- which is what an improving fleet looks like. Anyone quoting the "
              f"primary basis alone would report that the United States is de-electrifying, "
              f"and anyone quoting the meter basis alone would miss that a third of the fuel "
              f"cost of electricity has disappeared.",
              size=10.5, fill=INK2, chars=186, leading=14.5)

    foot = (
        "EIA State Energy Data System, bulk endpoint, no key, fetched 2026-09-23; series "
        "ESTXB, TNTCB and LOTXB for the US roll-up, 1960 to 2024. CAVEAT: the denominator is "
        "dominated by transport and industrial heat, so the ratio also moves when petrol "
        "demand moves and not only when an end use converts. This is the US only; the same "
        "ratio for other countries needs a different source.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=186, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=186, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for y in ("1960", "1980", "2000", "2024"):
        print(f"    {y}  site {site[y]:>6.1%}  primary {prim[y]:>6.1%}  "
              f"loss/delivered {ratio[y]:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
