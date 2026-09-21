#!/usr/bin/env python3
"""A sixth of the Protein Data Bank was never written up, and the recent rise is not real.

    python3 chart-1-unpublished.py

`rcsb_primary_citation.rcsb_journal_abbrev` reads **"To be published"** for 41,156 of 260,089
entries -- **15.8%**. A structure deposited into the permanent record with no paper behind it.

**Plotted by deposition year it makes a U, and both arms have a mechanism.**

*The left arm is structural genomics.* The share climbs from 1.2% in 1995 to **26.2% in 2007**
and falls back to 11.5% by 2018. That bulge is the structural genomics era, when consortia
deposited at volume against a target list rather than a paper: the four most prolific depositing
names in the whole register are SGC people, and two of the top ten "authors" are consortia
filing under their own name.

*The right arm is not a finding at all.* The share rises to 21.7% in 2024, 30.6% in 2025 and
42.1% in 2026 -- and a structure deposited in 2026 cannot have a 2026 paper yet. **That is
right-censoring, not a collapse in publishing.** The naive read is "the literature is breaking
down"; the figure marks the censored years so nobody has to arrive at it.

**What survives both arms.** Over 1990-2010 the share is 15.1% and over 2016-2024 it is 14.1%.
Mature cohorts settle near a seventh, and they do **not** decay toward zero with age -- a 2007
deposition is more likely to still say "To be published" than a 1998 one. The field records the
state at deposition and nobody goes back when the paper appears.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdb as P, plate                                                   # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "1-unpublished.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
CENSORED_FROM = 2023        # a deposition this recent has not had time to acquire a paper


def main():
    d = P.load()
    dep = {int(k): v for k, v in d["deposit_by_year"].items()}
    unp = {int(k): v for k, v in d["unpublished_by_year"].items()}
    yrs = [y for y in sorted(dep) if 1992 <= y <= 2026 and dep[y] >= 200]

    W, H = 1200, 850
    s = plate.open_svg(W, H, "A sixth of the Protein Data Bank was never written up")
    fr, _ = plate.frame(W, 62,
                        who="anyone counting PDB entries as a proxy for published structural work",
                        decide="whether an unpublished share is a filing convention or a real gap",
                        wrong="mature cohorts decay toward zero as their papers eventually appear")
    s += fr

    AX, AY, AH, AW = 28, 268, 320, 470
    s.append(txt(AX, AY - 56, "share of each year's depositions citing “To be published”",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(AX, AY - 40, "by deposition date; release date differs by up to 2,203 a year",
                 size=10.5, fill=MUTED))
    x0, pw = AX + 44, AW - 74
    px = lambda y: x0 + pw * ((y - yrs[0]) / (yrs[-1] - yrs[0]))
    py = lambda f: AY + AH - 46 - (AH - 76) * (f / .45)
    for f in (0, .1, .2, .3, .4):
        s.append(f'<line x1="{x0:.1f}" y1="{py(f):.1f}" x2="{px(yrs[-1]):.1f}" '
                 f'y2="{py(f):.1f}" stroke="{GRID}"/>')
        s.append(txt(x0 - 7, py(f) + 3, f"{f*100:.0f}%", size=9, fill=MUTED, anchor="end"))
    for y in range(1995, 2026, 5):
        s.append(txt(px(y), AY + AH - 30, str(y), size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, AY + AH - 14, "year the structure was deposited", size=9.5, fill=MUTED))
    cx = px(CENSORED_FROM)
    s.append(f'<rect x="{cx:.1f}" y="{AY-10:.1f}" width="{px(yrs[-1])-cx:.1f}" '
             f'height="{AH-36:.1f}" fill="{AMBER}" fill-opacity="0.12"/>')
    s += halo((cx + px(yrs[-1])) / 2, AY - 16, "no time to publish yet", size=9,
              fill=AMBER, anchor="middle", weight="700")
    pts = {y: (px(y), py(unp.get(y, 0) / dep[y])) for y in yrs}
    solid = [pts[y] for y in yrs if y <= CENSORED_FROM]
    dashed = [pts[y] for y in yrs if y >= CENSORED_FROM]
    for seq, col, dash in ((solid, RED, ""), (dashed, AMBER, ' stroke-dasharray="4 3"')):
        s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                        for i, (a, b) in enumerate(seq))
                 + f'" fill="none" stroke="{col}" stroke-width="2.2"{dash}/>')
    for y in (2007, 2018):
        s.append(f'<circle cx="{pts[y][0]:.1f}" cy="{pts[y][1]:.1f}" r="4" fill="{RED}"/>')
        s += halo(pts[y][0], pts[y][1] - 9, f"{unp[y]/dep[y]:.0%}", size=10, fill=RED,
                  anchor="middle", weight="700")
    mature = (sum(unp.get(y, 0) for y in range(1990, 2011))
              / sum(dep.get(y, 0) for y in range(1990, 2011)))
    s.append(f'<line x1="{x0:.1f}" y1="{py(mature):.1f}" x2="{px(2022):.1f}" '
             f'y2="{py(mature):.1f}" stroke="{INK2}" stroke-width="1.2" '
             f'stroke-dasharray="2 3"/>')
    s += halo(px(1996), py(mature) + 14, f"mature cohorts settle near {mature:.0%}", size=9,
              fill=INK2)
    s += wrap(AX, AY + AH + 10,
              f"The 2007 peak is structural genomics — consortia depositing at volume against a "
              f"target list rather than a paper. The rise after {CENSORED_FROM} is "
              f"right-censoring, and is dashed so the obvious reading, that publishing is "
              f"collapsing, is not available.",
              size=10.5, fill=INK2, chars=76)

    BX, BY, BH, BW = 590, 268, 320, 470
    s.append(txt(BX, BY - 56, "and waiting does not clear it", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(BX, BY - 40, "the same share, against how long the cohort has had",
                 size=10.5, fill=MUTED))
    bx0, bpw = BX + 44, BW - 74
    ages = [(2026 - y, unp.get(y, 0) / dep[y], y) for y in yrs if y <= CENSORED_FROM]
    mxa = max(a for a, _, _ in ages)
    bpx = lambda a_: bx0 + bpw * (a_ / mxa)
    bpy = lambda f: BY + BH - 46 - (BH - 76) * (f / .30)
    for f in (0, .1, .2, .3):
        s.append(f'<line x1="{bx0:.1f}" y1="{bpy(f):.1f}" x2="{bpx(mxa):.1f}" '
                 f'y2="{bpy(f):.1f}" stroke="{GRID}"/>')
        s.append(txt(bx0 - 7, bpy(f) + 3, f"{f*100:.0f}%", size=9, fill=MUTED, anchor="end"))
    for a_ in (5, 10, 15, 20, 25, 30):
        if a_ <= mxa:
            s.append(txt(bpx(a_), BY + BH - 30, str(a_), size=9, fill=MUTED, anchor="middle"))
    s.append(txt(BX, BY + BH - 14, "years since deposition", size=9.5, fill=MUTED))
    for a_, f, y in ages:
        col = RED if 2004 <= y <= 2011 else SLATE
        s.append(f'<circle cx="{bpx(a_):.1f}" cy="{bpy(f):.1f}" r="3.6" fill="{col}" '
                 f'fill-opacity="0.85"/>')
    for y, side in ((2007, 1), (1998, -1)):
        a_ = 2026 - y
        s += halo(bpx(a_) + 9 * side, bpy(unp[y] / dep[y]) + 3, f"deposited {y}", size=9,
                  fill=RED if y == 2007 else SLATE,
                  anchor="start" if side > 0 else "end")
    lx, ly = bx0 + 8, BY + 4
    for lab, col in (("deposited 2004–2011, the structural genomics years", RED),
                     ("every other cohort", SLATE)):
        s.append(f'<circle cx="{lx+4:.1f}" cy="{ly-3.5:.1f}" r="3.6" fill="{col}" '
                 f'fill-opacity="0.85"/>')
        s.append(txt(lx + 13, ly, lab, size=9.5, fill=INK2))
        ly += 14
    s += wrap(BX, BY + BH + 10,
              "If the citation were corrected when the paper appeared this would slope down to "
              "the right and the oldest cohorts would be clean. It does not: a 28-year-old "
              "cohort sits near 2% and a 19-year-old one near 26%. The driver is which era the "
              "work was done in, not how long it has had — the field records the state at "
              "deposition and nobody revisits it.",
              size=10.5, fill=INK2, chars=76)

    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"RCSB PDB search API, faceted server-side, fetched {d['fetched']}: "
              f"{d['total']:,} experimentally determined entries of which "
              f"{d['unpublished_total']:,} cite “To be published”. Deposition date, "
              f"not release date — they differ by up to 2,203 entries in a year and release "
              f"date measures the embargo as much as the science. The register grows weekly, so "
              f"this is one fetch, snapshotted beside the cache. Years before 1992 and cohorts "
              f"under 200 depositions are dropped as too small to carry a share.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    mature 1990-2010 {mature:.1%}; 2007 peak {unp[2007]/dep[2007]:.1%}; "
          f"2026 {unp.get(2026,0)/dep[2026]:.1%} (censored)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
