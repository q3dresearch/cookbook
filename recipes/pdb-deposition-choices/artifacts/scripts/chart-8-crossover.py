#!/usr/bin/env python3
"""The weight at which the field switches method, and how far it has moved.

    python3 chart-8-crossover.py

For every structure the register records a molecular weight and a method. Cross the two and a
decision boundary appears: **below some weight the field uses crystallography, above it cryo-EM**,
and the share crosses 50% at a weight that can be read off.

**That weight has moved by a factor of eleven in ten years.** In 2005-2011 it did not exist --
X-ray held 79.5% even above 1000 kDa. By 2012-2016 cryo-EM crossed 50% at about **1530 kDa**, by
2017-2021 at **315 kDa**, and in 2022-2026 at **133 kDa**. A 150 kDa complex was a crystallography
target in 2015 and is a cryo-EM target now, without anything about the molecule changing.

**This is the prescriptive read the register does support.** It does not say which method will
work on your target -- see the boundary below. It says what the field currently does with a
target of a given size, which is what you actually want when choosing where to apply for time.

**Below 50 kDa nothing has moved.** X-ray is at 90.9% and cryo-EM at 4.0%, essentially where they
were twenty years ago, and NMR's surviving 5.0% is entirely here. The boundary has swept down
through the mid-range and stopped.

**The boundary on all of it.** The PDB records solved structures. A target that resisted every
method is not in it, so none of these shares are success rates -- they are shares of the attempts
that worked. The curve tells you what the field chose and got, not what it would have got.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdb as P, plate                                                   # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID     # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "8-crossover.svg")
BANDS = ["0-50", "50-100", "100-200", "200-500", "500-1000", "1000-100000"]
# nominal plotting position, kDa: geometric midpoint, with the open ends placed by hand
MID = {"0-50": 25, "50-100": 70, "100-200": 141, "200-500": 316,
       "500-1000": 707, "1000-100000": 2000}
ERAS = ["2005-2011", "2012-2016", "2017-2021", "2022-2026"]
COL = {"2005-2011": "#c3c9ce", "2012-2016": "#8fa6b8",
       "2017-2021": "#4a7fa8", "2022-2026": "#14425f"}
RED, GREEN = "#8c2318", "#1b7f5a"


def crossover(pts):
    """Weight at which cryo-EM's share passes 50%, log-interpolated between band midpoints."""
    for (x0, s0), (x1, s1) in zip(pts, pts[1:]):
        if s0 < 0.5 <= s1:
            f = (0.5 - s0) / (s1 - s0)
            return 10 ** (math.log10(x0) + f * (math.log10(x1) - math.log10(x0)))
    return None


def main():
    d = P.load()
    sme = d["size_method_era"]
    share, cross = {}, {}
    for e in ERAS:
        pts = []
        for b in BANDS:
            m = sme[e][b]
            t = sum(m.values())
            pts.append((MID[b], m["ELECTRON MICROSCOPY"] / t if t else 0.0))
        share[e] = pts
        cross[e] = crossover(pts)

    W, H = 1200, 845
    s = plate.open_svg(W, H, "The weight at which the field switches method, "
                             "and how far it has moved")
    fr, _ = plate.frame(W, 62,
                        who="anyone choosing a method for a target of known size",
                        decide="whether the field would currently crystallise it or freeze it",
                        wrong="the 50% crossing sits in the same band in every era")
    s += fr

    AX, AY, AH, AW = 28, 150, 470, 740
    lo, hi = 20, 2600
    x0, pw = AX + 54, AW - 110
    px = lambda v: x0 + pw * ((math.log10(v) - math.log10(lo))
                              / (math.log10(hi) - math.log10(lo)))
    py = lambda f: AY + AH - 54 - (AH - 90) * f
    for f in (0, 0.25, 0.5, 0.75, 1.0):
        y = py(f)
        hard = f == 0.5
        s.append(f'<line x1="{x0:.1f}" y1="{y:.1f}" x2="{px(hi):.1f}" y2="{y:.1f}" '
                 f'stroke="{INK2 if hard else GRID}" '
                 f'{"stroke-dasharray=\"4 3\"" if hard else ""}/>')
        s.append(txt(x0 - 9, y + 3, f"{f:.0%}", size=9,
                     fill=INK2 if hard else MUTED, anchor="end",
                     weight="700" if hard else "400"))
    s += halo(px(hi) - 2, py(0.5) - 7, "half of all structures at this weight",
              size=9, fill=INK2, anchor="end", weight="700")
    s.append(txt(AX, AY - 18, "share of structures at this weight solved by cryo-EM",
                 size=11, fill=INK2))
    for v, lab in ((25, "25"), (50, "50"), (100, "100"), (200, "200"),
                   (500, "500"), (1000, "1000"), (2000, "2000")):
        s.append(f'<line x1="{px(v):.1f}" y1="{AY+AH-54:.1f}" x2="{px(v):.1f}" '
                 f'y2="{AY+AH-49:.1f}" stroke="{MUTED}"/>')
        s.append(txt(px(v), AY + AH - 36, lab, size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, AY + AH - 16, "molecular weight of the deposited structure, kilodaltons "
                                   "(log scale)", size=10, fill=MUTED))

    for e in ERAS:
        pts = [(px(x), py(f)) for x, f in share[e]]
        s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                        for i, (a, b) in enumerate(pts))
                 + f'" fill="none" stroke="{COL[e]}" stroke-width="2.6"/>')
        for a, b in pts:
            s.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3.2" fill="{COL[e]}"/>')
        s += halo(pts[-1][0] + 8, pts[-1][1] + 3, e, size=10.5, fill=COL[e], weight="700")
        c = cross[e]
        if c:
            s.append(f'<line x1="{px(c):.1f}" y1="{py(0.5):.1f}" x2="{px(c):.1f}" '
                     f'y2="{AY+AH-54:.1f}" stroke="{COL[e]}" stroke-width="1.1" '
                     f'stroke-dasharray="2 3"/>')
            s.append(f'<circle cx="{px(c):.1f}" cy="{py(0.5):.1f}" r="4.6" fill="{COL[e]}" '
                     f'stroke="#faf8f3" stroke-width="1.4"/>')
    for e, dy in (("2012-2016", -14), ("2017-2021", -14), ("2022-2026", -14)):
        c = cross[e]
        s += halo(px(c), AY + AH - 62 + dy, f"{c:,.0f} kDa", size=10, fill=COL[e],
                  anchor="middle", weight="700")
    s += halo(px(2000), py(0.205) - 12, "in 2005–2011 it never crosses:",
              size=9.5, fill=RED, anchor="end")
    s += halo(px(2000), py(0.205) - 1, "X-ray held 79.5% even above 1000 kDa",
              size=9.5, fill=RED, anchor="end")

    by = AY + AH + 16
    s.append(txt(AX, by, "the boundary moved 11-fold; the bottom end did not move at all",
                 size=12.5, fill=INK, weight="600"))
    by += 22
    s += wrap(AX, by,
              "A 150 kDa complex was a crystallography target in 2015 and is a cryo-EM target "
              "now, with nothing about the molecule having changed. Below 50 kDa nothing moved: "
              "X-ray is at 90.9% and cryo-EM at 4.0%, about where they were twenty years ago, "
              "and NMR's surviving 5.0% is entirely in that band. The boundary swept down "
              "through the middle and stopped.",
              size=11, fill=INK2, chars=98, leading=15)
    s += halo(AX + 700, by + 2, "read it as: above this weight,", size=10.5, fill=GREEN)
    s += halo(AX + 700, by + 17, "the field now reaches for cryo-EM", size=10.5, fill=GREEN,
              weight="700")
    s += halo(AX + 700, by + 36, "1530 kDa, then 315, then 133", size=12, fill=GREEN, weight="700")
    s += halo(AX + 700, by + 52, "across 2012–16, 2017–21, 2022–26", size=9.5, fill=MUTED)

    fy = H - 26 - 14 * 4
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"RCSB PDB search API, fetched {d['fetched']}; deposition date and "
              f"rcsb_entry_info.molecular_weight, {sum(sum(m.values()) for e in ERAS for m in sme[e].values()):,} "
              f"structures. Each point sits at its band's geometric midpoint, with 0–50 placed at "
              f"25 and the 1000-and-up band at 2000 by hand; the crossings are interpolated between those "
              f"positions, so they are accurate to the band and not to the kilodalton. "
              f"The PDB holds solved structures only: a target that resisted every method is not "
              f"in it, so these are shares of the attempts that worked, never success rates. "
              f"The boundary's movement is not a trend to extend — see figure 7 on what "
              f"extrapolating a clean curve in this register cost.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for e in ERAS:
        print(f"    {e}: crossover "
              + (f"{cross[e]:,.0f} kDa" if cross[e] else "never reaches 50%"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
