#!/usr/bin/env python3
"""Every department labels more work competed than draws a second bid, and restricting who
may bid raises the count.

    python3 chart-6-labelgap.py

Figure 5 shows the competed label and the bid count disagreeing on a third of the file. This
asks whether that gap is one department's habit, and whether reserving a competition for a
class of firm shrinks the field.

**It is nobody's habit: the gap is positive in 11 of 11 departments**, and it is not a
constant offset either -- it runs from 18 to 43 points, so the label is not a usable rate and
it is not a correctable one.

**And set-asides run the opposite way to intuition.** Restricting who may bid raises the
number of bids in **11 of 11** departments. A reserved competition draws a second firm more
often than an open one, and the size confound runs *against* the finding, because set-aside
awards are smaller and smaller awards draw fewer bids.

**What this cannot show.** Why. A set-aside pool is a smaller, self-selected set of firms who
may be likelier to answer a notice aimed at them; nothing here separates that from the
restriction itself doing the work.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import offers, plate                                                     # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "6-labelgap.svg")
RED, GREEN, BLUE, SLATE = "#8c2318", "#1b7f5a", "#4a7fa8", "#9aa4ad"


def main():
    S = offers.stats()
    ags = [a for a in S["ags"] if a["nopen"] >= 300 and a["nsa"] >= 300]
    gaps = sorted(a["lab"] - a["multi"] for a in S["ags"])
    below = sum(1 for a in ags if a["sa1"] < a["open1"])
    diffs = sorted(a["sa1"] - a["open1"] for a in ags)
    med = lambda v: v[len(v) // 2]

    W, H = 1240, 740
    s = plate.open_svg(
        W, H, "Every department labels more work competed than draws a second bid",
        subtitle=f"And restricting who may bid raises the number of bids in {below} of "
                 f"{len(ags)} departments. One mark per department; area is its awards.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone ranking agencies on a competition rate, or scoring a set-aside on "
            "bidder turnout",
        decide="whether the label can be corrected with a constant, and whether reserving "
               "a competition shrinks the field",
        wrong="the departments sit on the zero-gap line, every gap is the same width, or "
              "set-asides sit above the diagonal")
    s += fr

    # ---- panel A: label against count --------------------------------------
    AX, AY, AS = 92, y0 + 62, 396
    lo, hi = 0.18, 0.95
    ax = lambda v: AX + 52 + (AS - 70) * (v - lo) / (hi - lo)
    ay = lambda v: AY + AS - 44 - (AS - 62) * (v - lo) / (hi - lo)
    s.append(txt(AX - 64, AY - 36, "the label against the count, per department",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(AX - 64, AY - 19, "both axes are the same scale, so a constant gap would "
                                   "be a 45 degree line", size=10, fill=MUTED))
    for g in (0.2, 0.4, 0.6, 0.8):
        s.append(f'<line x1="{ax(g):.1f}" y1="{ay(lo):.1f}" x2="{ax(g):.1f}" '
                 f'y2="{ay(hi):.1f}" stroke="{GRID}"/>')
        s.append(f'<line x1="{ax(lo):.1f}" y1="{ay(g):.1f}" x2="{ax(hi):.1f}" '
                 f'y2="{ay(g):.1f}" stroke="{GRID}"/>')
        s.append(txt(ax(g), ay(lo) + 16, f"{g:.0%}", size=9, fill=MUTED, anchor="middle"))
        s.append(txt(ax(lo) - 8, ay(g) + 3, f"{g:.0%}", size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX - 64, ay(lo) + 34, "share of its awards labelled competed",
                 size=9.5, fill=MUTED))
    s.append(f'<text x="{AX-42}" y="{ay(lo):.1f}" font-size="9.5" fill="{INK2}" '
             f'transform="rotate(-90 {AX-42} {ay(lo):.1f})">'
             f'share that drew more than one offer</text>')
    s.append(f'<path d="M{ax(lo):.1f},{ay(lo):.1f} L{ax(hi):.1f},{ay(hi):.1f}" fill="none" '
             f'stroke="{INK2}" stroke-width="1.4" stroke-dasharray="5 3"/>')
    s += halo(ax(0.30), ay(0.34), "on this line the two", size=9.5, fill=INK2)
    s += halo(ax(0.30), ay(0.34) + 12, "measures would agree", size=9.5, fill=INK2)
    OFF = {"Veterans Affairs": (1, 4), "Health & Human Svcs": (1, 4), "Justice": (1, 4),
           "Homeland Security": (-1, 14), "Interior": (1, -8), "Agriculture": (1, 4),
           "Transportation": (1, 4), "Commerce": (-1, 4), "NASA": (-1, 4),
           "EPA": (1, 4), "Energy": (-1, 4)}
    for a in sorted(S["ags"], key=lambda z: -z["n"]):
        r = max(3.4, math.sqrt(a["n"]) / 44)
        s.append(f'<circle cx="{ax(a["lab"]):.1f}" cy="{ay(a["multi"]):.1f}" r="{r:.1f}" '
                 f'fill="{RED}" fill-opacity="0.16" stroke="{RED}" stroke-width="1.3"/>')
        sx, dy = OFF.get(a["ag"], (1, 4))
        s += halo(ax(a["lab"]) + sx * (r + 5), ay(a["multi"]) + dy, a["ag"], size=9.5,
                  fill=RED, anchor="start" if sx > 0 else "end", weight="700")
    s += halo(ax(0.20), ay(0.90), f"all 11 below the line; the gap runs "
              f"{gaps[0]*100:.0f} to {gaps[-1]*100:.0f} points", size=9.5, fill=RED,
              weight="700")

    # ---- panel B: set-aside against open -----------------------------------
    BX, BY, BS = 690, AY, 396
    blo, bhi = 0.10, 0.80
    bx = lambda v: BX + 52 + (BS - 70) * (v - blo) / (bhi - blo)
    by = lambda v: BY + BS - 44 - (BS - 62) * (v - blo) / (bhi - blo)
    s.append(txt(BX - 30, AY - 36, "and the reserved field draws more bidders",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(BX - 30, AY - 19, "competed-labelled awards only, so sole-source "
                                   "set-asides are out", size=10, fill=MUTED))
    for g in (0.2, 0.4, 0.6, 0.8):
        s.append(f'<line x1="{bx(g):.1f}" y1="{by(blo):.1f}" x2="{bx(g):.1f}" '
                 f'y2="{by(bhi):.1f}" stroke="{GRID}"/>')
        s.append(f'<line x1="{bx(blo):.1f}" y1="{by(g):.1f}" x2="{bx(bhi):.1f}" '
                 f'y2="{by(g):.1f}" stroke="{GRID}"/>')
        s.append(txt(bx(g), by(blo) + 16, f"{g:.0%}", size=9, fill=MUTED, anchor="middle"))
        s.append(txt(bx(blo) - 8, by(g) + 3, f"{g:.0%}", size=9, fill=MUTED, anchor="end"))
    s.append(txt(BX - 30, by(blo) + 34, "single-bid share of its OPEN competitions",
                 size=9.5, fill=MUTED))
    s.append(f'<text x="{BX-8}" y="{by(blo):.1f}" font-size="9.5" fill="{INK2}" '
             f'transform="rotate(-90 {BX-8} {by(blo):.1f})">'
             f'single-bid share of its SET-ASIDE competitions</text>')
    s.append(f'<path d="M{bx(blo):.1f},{by(blo):.1f} L{bx(bhi):.1f},{by(bhi):.1f}" '
             f'fill="none" stroke="{INK2}" stroke-width="1.4" stroke-dasharray="5 3"/>')
    s += halo(bx(0.16), by(0.62), "on this line a set-aside", size=9.5, fill=INK2)
    s += halo(bx(0.16), by(0.62) + 12, "makes no difference", size=9.5, fill=INK2)
    BOFF = {"Veterans Affairs": (1, 4), "Health & Human Svcs": (1, 4), "Justice": (-1, 14),
            "Homeland Security": (1, 4), "Interior": (-1, 4), "Agriculture": (1, -8),
            "Transportation": (-1, 4), "Commerce": (-1, -8), "NASA": (1, 4),
            "EPA": (-1, 4), "Energy": (1, 4)}
    for a in sorted(ags, key=lambda z: -z["n"]):
        r = max(3.4, math.sqrt(a["nsa"] + a["nopen"]) / 30)
        s.append(f'<circle cx="{bx(a["open1"]):.1f}" cy="{by(a["sa1"]):.1f}" r="{r:.1f}" '
                 f'fill="{GREEN}" fill-opacity="0.16" stroke="{GREEN}" '
                 f'stroke-width="1.3"/>')
        sx, dy = BOFF.get(a["ag"], (1, 4))
        s += halo(bx(a["open1"]) + sx * (r + 5), by(a["sa1"]) + dy, a["ag"], size=9.5,
                  fill=GREEN, anchor="start" if sx > 0 else "end", weight="700")
    s += halo(bx(bhi) - 4, by(0.14), f"all {below} below it: the restricted field",
              size=9.5, fill=GREEN, anchor="end", weight="700")
    s += halo(bx(bhi) - 4, by(0.14) + 13, f"drew more bidders, median "
              f"{med(diffs)*100:.1f} points", size=9.5, fill=GREEN, anchor="end",
              weight="700")

    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2016, eleven civilian "
        "departments, awards carrying a usable bid count. Departments need 300 awards in "
        "each arm to be scored on the right. CAVEAT: set-aside awards are smaller and "
        "smaller awards draw fewer bids, so the size confound runs against the finding "
        "rather than producing it. Defense (68.6% of federal contract awards) is absent.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=186, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=186, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    label-minus-count gap: {gaps[0]*100:.1f} to {gaps[-1]*100:.1f} pts, "
          f"median {med(gaps)*100:.1f}, positive in {sum(1 for g in gaps if g>0)}/11")
    print(f"    set-aside lower in {below}/{len(ags)}, median {med(diffs)*100:.1f} pts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
