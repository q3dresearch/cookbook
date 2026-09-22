#!/usr/bin/env python3
"""What predicts a single bid is the procedure actually run, not the label on the award.

    python3 chart-7-procedure.py

Figure 5 shows the competed label splitting the bid count close to a coin toss. This asks what
does predict it, inside that same label.

**`solicitation_procedures` does.** Among the 402,070 competed-labelled awards, orders placed
against an already-competed vehicle draw one bid **59.9%** of the time; a sealed bid or
two-step draws one **6.5%** of the time. That is a nine-fold range inside a single label.

**Which is the mechanism behind figure 5's headline.** 75% of the awards carrying the
strongest label, FULL AND OPEN COMPETITION, are orders against a vehicle that was competed
once, earlier, by someone else. The label is inherited from the vehicle rather than earned by
the order, and 17% of them carry in the same row a recorded reason why only one source could
be solicited -- 98% of those drew one bid.

**What this cannot show.** Whether the vehicle's own competition was real. The register names
the parent contract but not its terms or how many holders it has, so "competed once, earlier"
is a description of the paperwork and not a verdict on it. Figure 8 measures how differently
individual vehicles behave.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import offers, plate                                                     # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "7-procedure.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
COL = {"order against a vehicle": RED, "simplified acquisition": AMBER,
       "proposal or quote solicited": GREEN, "sealed bid or two-step": BLUE,
       "architect-engineer": SLATE, "other or not recorded": SLATE}


def main():
    S = offers.stats()
    procs, nproc, fo = S["procs"], S["nproc"], S["fo"]
    W, H = 1240, 812
    s = plate.open_svg(
        W, H,
        "Inside the competed label, the procedure actually run decides the bid count",
        subtitle=f"The {nproc:,} competed-labelled FY2016 awards, split by "
                 f"solicitation_procedures. Width is awards; height is the share that drew "
                 f"a single bid.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone screening on the competed label, or deciding which lever raises "
            "bidder counts",
        decide="whether to read competition off the label or off the procedure recorded "
               "beside it",
        wrong="the blocks are the same height, or the widest one is not the tallest")
    s += fr

    AX, AY, AW, AH = 64, y0 + 74, W - 120, 340
    s.append(txt(AX, AY - 44, "each procedure, sized by how much work runs through it",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(AX, AY - 27, "block width is awards, block height is the single-bid share, "
                              "so area is single-bid awards", size=10, fill=MUTED))
    hi = 0.70
    by = lambda v: AY + AH - AH * (v / hi)
    for g in (0.0, 0.2, 0.4, 0.6):
        s.append(f'<line x1="{AX-6:.1f}" y1="{by(g):.1f}" x2="{AX+AW:.1f}" '
                 f'y2="{by(g):.1f}" stroke="{GRID}"/>')
        s.append(txt(AX - 12, by(g) + 3, f"{g:.0%}", size=9, fill=MUTED, anchor="end"))
    s.append(f'<text x="{AX-40}" y="{by(0):.1f}" font-size="9.5" fill="{INK2}" '
             f'transform="rotate(-90 {AX-40} {by(0):.1f})">'
             f"share of the block's awards that drew a single bid</text>")
    x0 = AX
    for p in procs:
        wd = AW * p["n"] / nproc
        col = COL.get(p["lab"], SLATE)
        s.append(f'<rect x="{x0:.1f}" y="{by(p["one"]):.1f}" width="{max(wd-2,1.2):.1f}" '
                 f'height="{by(0)-by(p["one"]):.1f}" fill="{col}" fill-opacity="0.80"/>')
        if wd > 120:
            s += halo(x0 + wd / 2, by(p["one"]) - 22, p["lab"], size=11, fill=col,
                      anchor="middle", weight="700")
            s += halo(x0 + wd / 2, by(p["one"]) - 8, f"{p['one']:.0%} single-bid", size=11,
                      fill=col, anchor="middle", weight="700")
            s.append(txt(x0 + wd / 2, by(0) + 17, f"{p['n']:,} awards", size=9.5,
                         fill=MUTED, anchor="middle"))
        x0 += wd
    # the narrow blocks get a stacked key rather than labels that would not fit
    small = [p for p in procs if AW * p["n"] / nproc <= 120]
    ky = AY + 6
    for i, p in enumerate(small):
        s += halo(AX + AW, ky + i * 14, f"{p['lab']}: {p['n']:,} awards, "
                  f"{p['one']:.0%} single-bid", size=9.5, fill=COL.get(p["lab"], SLATE),
                  anchor="end", weight="700")
    s.append(txt(AX, by(0) + 36, "the widest block is also the tallest, which is the whole "
                                 "finding", size=10.5, fill=INK2))

    cy = AY + AH + 66
    s.append(txt(28, cy, "and that is where figure 5's headline comes from",
                 size=12, fill=INK, weight="600"))
    s += wrap(28, cy + 20,
              f"Of the {fo['all']:,} awards carrying the strongest label, FULL AND OPEN "
              f"COMPETITION, {fo['vehicle']/fo['all']:.0%} are orders placed against a "
              f"vehicle that was competed once, earlier, by someone else, and "
              f"{fo['exception']/fo['all']:.0%} carry in the same row a recorded reason why "
              f"only one source could be solicited -- {fo['exception_1']/fo['exception']:.0%} "
              f"of those drew one bid. The label is inherited from the vehicle rather than "
              f"earned by the order.",
              size=10.5, fill=INK2, chars=186, leading=14.5)

    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2016, eleven civilian "
        "departments. The 402,070 awards carrying a competed label and a usable bid count, "
        "where a recorded 0 offers is not a count. CAVEAT: an order under a competed vehicle "
        "was competed once, at the vehicle, so this is not a claim that the label is false. "
        "Defense (68.6% of federal contract awards) is absent.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=186, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=186, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for p in procs:
        print(f"    {p['lab']:<30}{p['n']:>8,}  {p['n']/nproc:>6.1%}  "
              f"single-bid {p['one']:>6.1%}")
    print(f"    FULL AND OPEN: {fo['vehicle']/fo['all']:.1%} vehicle orders, "
          f"{fo['exception']/fo['all']:.1%} only-one-source, "
          f"{fo['exception_1']/fo['exception']:.1%} of those single-bid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
