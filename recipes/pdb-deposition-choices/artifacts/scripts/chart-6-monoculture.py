#!/usr/bin/env python3
"""Two of the three monocultures are practice. One is the crystals.

    python3 chart-6-monoculture.py

Three fields in the register are each dominated by a single value. Measured once, that is three
numbers and no way to tell what they mean. Q18 named the falsifier: **if the concentration is a
property of what is solvable it should sit flat over time, and if it is a property of practice
it should move.** Faceting each field by deposition year separates them, and they do not give
the same answer.

All three figures below are three-year means at each end, because single years move several
points on their own.

**Temperature tightened.** 100 K went from 80.1% of entries recording a temperature in
2005-2007 to 89.1% in 2023-2025 -- **+9.0 points**. Cryo-cooling was a choice that became the
default, and the room-temperature fraction was squeezed out across twenty years.

**Cryo-EM's reconstruction method tightened hardest.** Single particle went from 80.3% in
2013-2015 to **93.5%** -- **+13.2 points**. The method diversified far less than it grew. Its
window starts later because before 2013 it records under 160 entries a year.

**The space group did not move.** `P 21 21 21` was 21.7% in 2005-2007 and 22.2% in 2023-2025,
**+0.5 points**, wandering between 19.6% and 27.2% with no trend across two decades. This is
the one that is not practice: **a protein crystallises in the space group it crystallises in**,
and twenty years of changing everything else did not shift the distribution.

**Which changes what the concentration means.** The two that moved are correlated failure modes
the field chose and could in principle choose differently. The one that did not move is a
property of the objects, and no amount of depositing differently touches it.

**The denominator is drawn because it has to be.** Cryo-EM recorded 27 to 79 entries a year
before 2012, so the left end of that line is three or four structures moving it several points.
The right panel is there to stop the reader trusting it.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdb as P, plate                                                   # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "6-monoculture.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
SERIES = [("temperature", RED, "collected at 100 K", "of entries recording a temperature"),
          ("em_method", AMBER, "reconstructed as single particle", "of cryo-EM entries"),
          ("space_group", BLUE, "crystallised in P 21 21 21", "of crystallographic entries")]


def main():
    d = P.load()
    C = d["concentration_by_year"]
    yrs = sorted(int(y) for y in C["temperature"])
    ser = {k: {int(y): v["top1"] / v["recorded"] for y, v in C[k].items()} for k, _, _, _ in SERIES}
    nrec = {k: {int(y): v["recorded"] for y, v in C[k].items()} for k, _, _, _ in SERIES}
    # three-year means at each end; cryo-EM starts at 2013 because before that n is under 160
    WIN = {"temperature": (2005, 2007), "space_group": (2005, 2007), "em_method": (2013, 2015)}
    chg = {}
    for k in ser:
        a, b = WIN[k]
        s0 = sum(ser[k][y] for y in range(a, b + 1)) / 3
        s1 = sum(ser[k][y] for y in range(2023, 2026)) / 3
        chg[k] = (s0, s1, (s1 - s0) * 100, a, b)

    W, H = 1200, 790
    s = plate.open_svg(W, H, "Two of the three monocultures are practice. One is the crystals.")
    fr, _ = plate.frame(W, 62,
                        who="anyone treating a dominant value in the register as a fixed fact "
                            "about proteins",
                        decide="whether a correlated failure mode is one the field chose",
                        wrong="all three shares move together, or none of them move")
    s += fr

    AX, AY, AH, AW = 28, 160, 430, 690
    x0, pw = AX + 46, AW - 92
    px = lambda y: x0 + pw * ((y - yrs[0]) / (yrs[-1] - yrs[0]))
    py = lambda f: AY + AH - 56 - (AH - 90) * f
    for f in (0, .25, .5, .75, 1.0):
        s.append(f'<line x1="{x0:.1f}" y1="{py(f):.1f}" x2="{px(yrs[-1]):.1f}" '
                 f'y2="{py(f):.1f}" stroke="{GRID}"/>')
        s.append(txt(x0 - 8, py(f) + 3, f"{f:.0%}", size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, AY - 18, "share of that year's entries taking the single most common value",
                 size=11, fill=INK2))
    for y in range(2005, 2026, 5):
        s.append(f'<line x1="{px(y):.1f}" y1="{py(0):.1f}" x2="{px(y):.1f}" '
                 f'y2="{py(0)+5:.1f}" stroke="{MUTED}"/>')
        s.append(txt(px(y), py(0) + 18, str(y), size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, py(0) + 36, "year the structure was deposited", size=10, fill=MUTED))

    for k, col, lab, base in SERIES:
        ys = [y for y in yrs if y in ser[k]]
        pts = [(px(y), py(ser[k][y])) for y in ys]
        s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                        for i, (a, b) in enumerate(pts))
                 + f'" fill="none" stroke="{col}" stroke-width="2.6"/>')
        for (a, b), y in zip(pts, ys):
            thin = nrec[k][y] < 200
            s.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="{2.2 if thin else 3.2:.1f}" '
                     f'fill="{"#faf8f3" if thin else col}" stroke="{col}" '
                     f'stroke-width="{1.4 if thin else 0}"/>')
        s0, s1, dpts, a, b = chg[k]
        # the two rising series end within four points of each other, so their labels are
        # pushed apart rather than left to overlap
        off = {"em_method": -22, "temperature": 12, "space_group": 3}[k]
        s += halo(pts[-1][0] + 8, pts[-1][1] + off, lab, size=10.5, fill=col, weight="700")
        s += halo(pts[-1][0] + 8, pts[-1][1] + off + 13,
                  f"{dpts:+.1f} pts since {a}–{b}", size=9.5, fill=col)
        s += halo(pts[-1][0] + 8, pts[-1][1] + off + 25, base, size=9, fill=MUTED)
    s += halo(px(2011), py(0.36), "hollow marks are years with under 200 entries recording "
                                  "the field", size=9.5, fill=MUTED)

    BX, BY, BH, BW = 950, 160, 180, 222
    s.append(txt(BX, BY - 18, "what each line is computed from", size=11, fill=INK2))
    import math
    nlo, nhi = 20, 15000
    ny = lambda v: (BY + BH - 26 - (BH - 46)
                    * ((math.log10(max(v, nlo)) - math.log10(nlo))
                       / (math.log10(nhi) - math.log10(nlo))))
    nx = lambda y: BX + (BW - 16) * ((y - yrs[0]) / (yrs[-1] - yrs[0]))
    for v in (100, 10000):
        s.append(f'<line x1="{BX:.1f}" y1="{ny(v):.1f}" x2="{nx(yrs[-1]):.1f}" '
                 f'y2="{ny(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(BX - 5, ny(v) + 3, f"{v:,}", size=8.5, fill=MUTED, anchor="end"))
    s.append(f'<line x1="{BX:.1f}" y1="{ny(200):.1f}" x2="{nx(yrs[-1]):.1f}" '
             f'y2="{ny(200):.1f}" stroke="{INK2}" stroke-width="1" stroke-dasharray="3 2"/>')
    s += halo(nx(yrs[-1]), ny(200) - 6, "200", size=8.5, fill=INK2, anchor="end", weight="700")
    for k, col, _, _ in SERIES:
        pts = [(nx(y), ny(nrec[k][y])) for y in yrs if y in nrec[k]]
        s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                        for i, (a, b) in enumerate(pts))
                 + f'" fill="none" stroke="{col}" stroke-width="1.8"/>')
    s.append(txt(BX, BY + BH - 8, "entries a year recording the field (log)", size=9,
                 fill=MUTED))
    s += wrap(BX, BY + BH + 16,
              "Cryo-EM recorded 27 to 79 entries a year before 2012, so the left end of its "
              "line is three or four structures moving it several points. It is drawn hollow "
              "and should not be read.",
              size=10, fill=INK2, chars=32, leading=13)

    by = AY + AH + 6
    s.append(txt(AX, by, "two of them are practice; the third is the crystals",
                 size=12.5, fill=INK, weight="600"))
    s += wrap(AX, by + 20,
              "Cryo-cooling and single-particle reconstruction are choices that hardened into "
              "defaults, and a field could in principle choose differently — whatever they "
              "systematically hide is hidden across most of the record at once, and depositing "
              "more of the same does not find it. The space group did not move across twenty "
              "years of everything else changing, which is what a property of the objects looks "
              "like rather than a property of the field. Reading all three as one “the PDB "
              "is a monoculture” claim merges a fixable habit with a fact about proteins.",
              size=11, fill=INK2, chars=104, leading=15)

    fy = H - 24 - 14 * 3
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"RCSB PDB search API, fetched {d['fetched']}; one terms facet per field per "
              f"deposition year. Each share is over the entries that record that field in that "
              f"year, not over all depositions, and the three denominators differ — they are "
              f"drawn at the right for exactly that reason. Change is quoted as a three-year "
              f"mean at each end, 2005–2007 against 2023–2025, and 2013–2015 against 2023–2025 "
              f"for cryo-EM because before that it records under 160 entries a year. An earlier "
              f"version of this figure read 87% at 100 K from a *histogram* bucket, which is "
              f"everything in [100, 125) K; the exact value is used here.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for k, _, lab, _ in SERIES:
        s0, s1, dpts, a, b = chg[k]
        print(f"    {lab:<34} {s0:6.1%} ({a}–{b})  ->  {s1:6.1%} (2023–25)   {dpts:+5.1f} pts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
