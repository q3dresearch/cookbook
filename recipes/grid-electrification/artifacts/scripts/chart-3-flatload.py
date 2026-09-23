#!/usr/bin/env python3
"""PJM's overnight trough grew twice as fast as its peak. So did California's.

    python3 chart-3-flatload.py

A data centre is a flat 24/7 load. Add L megawatts of it to a grid whose overnight trough is
T and whose afternoon peak is P, and both rise by L -- so the trough grows by L/T and the
peak by only L/P. Because T is always smaller than P, **the trough has to grow faster**. The
gap between the two growth rates is the signature, and it is the successor to the facility
count, which failed its falsifier at r = +0.03.

**It fires where it should.** PJM contains Northern Virginia, the densest concentration of
data centres on earth. Its trough grew 6.0% from 2019 to 2025 while its peak grew 2.8% -- a
gap of 3.2 points, which works out to **about 10 GW of implied flat load**, 9.6% of its peak.
No other American grid implies anything like that volume.

**And it fires just as hard on a grid with no such story.** California's trough grew 6.0%
against a peak that grew 0.2%: a gap of 5.8 points, larger than PJM's. California's
electricity consumption *fell* 5.9% over the same period. What California has is rooftop
solar, which never appears in generation data at all -- it appears as demand that did not
happen, in the middle of the day, suppressing the recorded peak while leaving the overnight
trough alone. **From the shape alone the two are the same picture.**

**Which is why the vertical position is the finding and the horizontal position is the
test.** Flat load pushes a grid up and to the right, because both halves of the day grow.
Suppressed daytime demand pushes it straight up, because only one half does.

**A correction to an earlier version of this note.** It said behind-the-meter solar was
invisible in this dataset by construction. It is invisible in **EBA**, which is what this
plate reads. EIA does publish a modelled estimate of it per state in the ELEC file
(`ELEC.GEN.DPV-{ST}`), and figure 6 uses it -- where it turns out not to explain the thing it
was the obvious candidate for, on a within-state control rather than a correlation.

**Grids under 5 GW are in figure 4**, which is about what size does to this measure: the
largest gaps in the country all belong to grids small enough for one customer to move.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate, shape                                                      # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "3-flatload.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
FLOOR = 5.0                      # GW of peak; below this, figure 4
LO, HI = -0.09, 0.34             # the SAME range on both axes, or the diagonal is a lie
LAB = {"PJM": (1, 4), "CISO": (-1, 4), "ERCO": (1, 4), "SOCO": (1, 4), "MISO": (-1, 15),
       "SWPP": (1, 4), "FPL": (-1, 4), "TVA": (1, 4), "DUK": (1, 13), "NYIS": (-1, 4),
       "ISNE": (1, 4), "BPAT": (-1, 4), "FPC": (1, -9), "CPLE": (-1, 13),
       "PACE": (1, -9), "PSCO": (-1, 4), "LGEE": (1, 4)}


def main():
    rows = [r for r in shape.rows() if r["peak_gw"] >= FLOOR]
    up = [r for r in rows if r["gap"] > 0]

    W, H = 1150, 900
    s = plate.open_svg(
        W, H, "PJM's overnight trough grew twice as fast as its peak. So did California's.",
        subtitle=f"The {len(rows)} US balancing authorities peaking above {FLOOR:.0f} GW, "
                 f"2019 against 2025. Flat 24/7 load lifts the overnight trough faster than "
                 f"the afternoon peak, so it lands above the diagonal.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone using hourly demand shape to find where data centre load has landed",
        decide="whether load shape can stand in for compute siting, after facility counts "
               "failed at r = +0.03",
        wrong="the grids with known compute separate cleanly from the rest, or nothing "
              "without a compute story sits as high")
    s += fr

    # ---- one square panel, because a 45 degree line must actually be 45 degrees ----
    SIDE = 560
    AX, AY = 250, y0 + 44
    sc = lambda v: SIDE * (v - LO) / (HI - LO)
    ax = lambda v: AX + sc(v)
    ay = lambda v: AY + SIDE - sc(v)

    for g in (-0.05, 0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30):
        zero = abs(g) < 1e-9
        col = RULE if zero else GRID
        s.append(f'<line x1="{ax(g):.1f}" y1="{ay(LO):.1f}" x2="{ax(g):.1f}" '
                 f'y2="{ay(HI):.1f}" stroke="{col}"/>')
        s.append(f'<line x1="{ax(LO):.1f}" y1="{ay(g):.1f}" x2="{ax(HI):.1f}" '
                 f'y2="{ay(g):.1f}" stroke="{col}"/>')
        s.append(txt(ax(g), ay(LO) + 17, f"{g*100:.0f}", size=9, fill=MUTED,
                     anchor="middle"))
        s.append(txt(ax(LO) - 8, ay(g) + 3, f"{g*100:.0f}", size=9, fill=MUTED,
                     anchor="end"))
    # the diagonal: equal growth in both halves of the day
    s.append(f'<line x1="{ax(LO):.1f}" y1="{ay(LO):.1f}" x2="{ax(HI):.1f}" '
             f'y2="{ay(HI):.1f}" stroke="{INK2}" stroke-width="1.1" '
             f'stroke-dasharray="5 4"/>')
    s += halo(ax(0.245) + 6, ay(0.245) - 7, "trough and peak grew equally", size=9.5,
              fill=INK2, weight="700")
    s.append(txt(AX, ay(LO) + 36, "the afternoon PEAK, percent change 2019 to 2025",
                 size=10, fill=INK2))
    s.append(f'<text x="{AX-46}" y="{ay(LO):.1f}" font-size="10" fill="{INK2}" '
             f'transform="rotate(-90 {AX-46} {ay(LO):.1f})">'
             f'the overnight TROUGH, percent change 2019 to 2025</text>')

    for r in sorted(rows, key=lambda x: -x["peak_gw"]):
        col = BLUE if r["gap"] > 0 else SLATE
        rad = max(3.6, math.sqrt(r["peak_gw"]) * 1.15)
        x, y = ax(r["peak_growth"]), ay(r["trough_growth"])
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad:.1f}" fill="{col}" '
                 f'fill-opacity="0.16" stroke="{col}" stroke-width="1.5"/>')
        if r["jump"]:                       # cause unresolved, marked not excluded
            s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad+3.5:.1f}" fill="none" '
                     f'stroke="{AMBER}" stroke-width="1.1" stroke-dasharray="2.5 2.5"/>')
        sx, dy = LAB.get(r["ba"], (1, 4))
        s += halo(x + sx * (rad + 5), y + dy, r["ba"], size=9.5, fill=col,
                  anchor="start" if sx > 0 else "end", weight="700")

    # The two marks that carry the argument. Their callouts go in the empty upper left of
    # the panel and name the grid, rather than floating beside it: at the sizes here the two
    # bubbles sit close enough that adjacent text lands on the other one.
    for v, body, col, wt in (
            (0.318, "PJM   +3.2 points, about 10 GW of implied flat load", BLUE, "700"),
            (0.306, "the largest implied flat load of any US grid", INK2, "normal"),
            (0.272, "CISO   +5.8 points -- a LARGER gap than PJM's", RED, "700"),
            (0.260, "and California's electricity consumption fell 5.9%", RED, "normal"),
            (0.248, "rooftop solar suppresses the peak, not the trough", RED, "normal")):
        s.append(txt(ax(LO) + 14, ay(v), body, size=9.5, fill=col, weight=wt))

    # ---- the reading, as text beside the panel, not as a second chart ----
    TX, TW = 42, 190
    ty = AY + 26
    for head, body, col in (
            ("above the line", f"{len(up)} of {len(rows)} grids. The overnight trough grew "
                               f"faster than the afternoon peak.", BLUE),
            ("what puts it there", "Flat load raises both halves of the day, so it moves a "
                                   "grid right as well as up.", INK2),
            ("what also puts it there", "Daytime demand that stops being recorded. Rooftop "
                                        "solar moves a grid straight up.", RED),
            ("the dashed ring", "A year where trough and peak both rose over 10% at once. "
                                "No other grid lost matching load, so the cause is "
                                "unresolved.", AMBER)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        s += wrap(TX, ty, body, size=9.5, fill=MUTED, chars=30, leading=12.5)
        ty += 12.5 * len(wrap(0, 0, body, size=9.5, fill=MUTED, chars=30, leading=12.5)) + 16

    foot = (
        "EIA Hourly Electric Grid Monitor (EBA) bulk file, no key, fetched 2026-09-23. "
        "Trough and peak are the median daily minimum and maximum of LOCAL-time hourly "
        "demand; UTC would split every night across two days. CAVEAT: behind-the-meter "
        "solar is absent from EBA, appearing only as demand that did not happen. EIA "
        "estimates it per STATE in the ELEC file, which figure 6 uses and which is too "
        "coarse to correct a balancing authority; the two readings here are separated by "
        "shape alone.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=172, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=172, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {len(rows)} grids above {FLOOR:.0f} GW, {len(up)} above the diagonal")
    for r in sorted(rows, key=lambda x: -x["gap"])[:5]:
        print(f"      {r['ba']:<6}peak {r['peak_growth']:>+6.1%}  trough "
              f"{r['trough_growth']:>+6.1%}  gap {r['gap']:>+5.1%}  "
              f"{r['peak_gw']:>5,.1f} GW{'  [jump ' + r['jump'] + ']' if r['jump'] else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
