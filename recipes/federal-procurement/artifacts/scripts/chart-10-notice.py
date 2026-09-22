#!/usr/bin/env python3
"""Both notice columns were read at the wrong level: the pooled numbers are the family.

    python3 chart-10-notice.py

`fed_biz_opps` records whether an opportunity was posted publicly. Pooled across the 402,070
competed FY2016 awards carrying a usable bid count, posting is worth **-4.3 points** of
single-bid rate, which reads as an architecture of public notice that produces almost no
bidders.

**It is not.** Posted awards are concentrated in the families that are most single-bid to begin
with -- 30% of them are medical and laboratory equipment, figure 9's worst family at 64.8%.
Hold the product family as well as the award size and the gap goes to **-7.4 points**, nearly
double the pooled number.

**And the commercial-item flag runs the other way until it is controlled.** Pooled it is
**+8.4 points**, which reads as commercial items drawing fewer bidders. Within family and size
band it is **+0.7** -- the eight points were composition, and a 0.6 point effect would have
been visible.

**So the two columns fail in opposite directions for the same reason**, and the reason is the
product family. One pooled number was too small and the other was entirely spurious.

**Where each column lands family by family is figure 11**, which is the same two columns drawn
as distributions rather than as one pooled mark each.

**Method, since it is not on the plate.** Marks are Cochran-Mantel-Haenszel risk differences
with 95% intervals. Award size is the award's net FY2016 obligation in thirteen bands and a
stratum needs 25 awards on both sides to count. Three robustness checks, all reported here
rather than drawn: banding on `base_and_all_options_value` instead of the obligation moves the
two third marks to -7.5 and +0.6 points, so the control is not a choice of column; product
family alone with size free gives -9.0 and +2.4, so the family is the active ingredient rather
than the size; and adding figure 5's solicitation procedure as a fourth stratum gives -16.0 and
-2.7 on the 71% and 86% of awards that still share a stratum. Within one procedure, family and
size fixed, notice is -11.6 points on vehicle orders, -14.5 on simplified acquisitions and
-24.5 on negotiated proposals.

**What this cannot show.** Causation. Posting is required above a dollar line, so posted and
unposted awards differ in kind as well as in size, and the controls here are composition
controls. The caveat that matters: on the UNCOMPETED base, where 99.9% of awards draw one bid
and there is almost no room to move, posting still reads -1.6 points, so some part of this
separates the officers who post from those who were going to draw bidders anyway.
"""
import collections, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import notice, plate
from notice import stats, mh, MIN_FAM, MIN_CELL                                                     # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "10-notice.svg")
BLUE, ORANGE, RED, SLATE = "#2e6f9e", "#b3681a", "#8c2318", "#9aa4ad"
MIN_FAM = 2000        # families below this many competed awards are not drawn
MIN_CELL = 25         # a stratum needs this many on BOTH sides to be used
C, FB, CI, FA, OB, SP, AW = range(7)


# ------------------------------------------------------------------ the estimator



# ------------------------------------------------------------------ the plate
LO, HI = -0.45, 0.38
TICKS = (-0.40, -0.30, -0.20, -0.10, 0.0, 0.10, 0.20, 0.30)
PX0, GUT = 278, 12

LAD = [("as reported, no control", lambda r: r[0]),
       ("within award-size band", lambda r: r[1]),
       ("within size band and product family", lambda r: r[2])]
#                                                     note anchor: (side, row it sits on)
# side -1 puts the note left of the last mark, +1 right of it; side 0 parks it against the
# left edge of the plot, which is the only empty space in a group whose marks are all at
# the far right.
GROUPS = [("post", BLUE, "public notice: posted against not posted",
           "fed_biz_opps YES, 196,281 awards, against NO, 47,330", -1),
          ("comm", ORANGE, "commercial item: procedures used against not used",
           "commercial_item_acquisition_procedures, 289,406 against 95,768", +1),
          ("bpa", RED, "the blank group: BPA calls against posted awards",
           "fed_biz_opps blank, 42,262 awards, 93.5% of them BPA calls", 0)]


def main():
    S = stats()
    W = 1240
    PW = W - 28 - PX0
    x = lambda v: PX0 + PW * (v - LO) / (HI - LO)

    fr, y0 = plate.frame(
        W, 86,
        who="anyone proposing to raise bidder counts by widening public notice, or reading "
            "the commercial-item flag as a competition signal",
        decide="whether either column survives holding the product family fixed",
        wrong="the marks do not move as the controls are added, or they move the same way "
              "in both groups")

    AY = y0 + 60
    GH, AR, AGAP = 20, 21, 36
    GRP = GH + len(LAD) * AR + AGAP
    A_END = AY + len(GROUPS) * GRP

    e, lad = S["extra"], S["ladders"]
    pf, cf = lad["post"][2], lad["comm"][2]
    # counted here and drawn in figure 11, which splits each pooled mark below into the 26
    # per-family differences behind it
    npos = sum(1 for r in S["fams"] if r["post"]["hi"] < 0)
    ppos = sum(1 for r in S["fams"] if r["post"]["lo"] > 0)
    ncom = sum(1 for r in S["fams"] if r["comm"]["hi"] < 0)
    pcom = sum(1 for r in S["fams"] if r["comm"]["lo"] > 0)
    med = lambda t: sorted(abs(r[t]["diff"]) for r in S["fams"])[len(S["fams"]) // 2]

    # Trimmed from the plate per doctrine/what-a-footnote-carries.md; kept here because it is method: f
    # oot = ( USAspending API v2 bulk download, fetched 2026-09-22; FY2016 contract
    # transactions for eleven civilian departments, collapsed to {S['d']['meta']['awards']:,}
    # awards. Rates use the {S['n_comp']:,} carrying a competed label and a usable bid count,
    # where a recorded 0 offers is a filing artefact and not a count. CAVEAT: on the
    # uncompeted base, where 99.9% of awards draw one bid and there is almost no room to move,
    # posting still reads {e['uncompeted']['diff']*100:+.1f} points -- so some part of this
    # separates the officers who post from the awards that were going to draw bidders anyway.
    # Nothing here is causal; posting is required above a dollar line, so the two groups
    # differ in kind. These eleven departments are 8.5% of federal contract awards and Defense
    # is 68.6%, so none of it describes federal procurement as a whole.)
    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2016, 554,171 awards. "
        "Rates use the 402,070 with a competed label and a usable bid count. CAVEAT: on the "
        "uncompeted base, where 99.9% of awards draw one bid, posting still reads -1.6 "
        "points, so part of this separates the officer from the bidders. Not causal. These "
        "eleven civilian departments are 8.5% of federal contract awards; Defense (68.6%) "
        "is absent, so this is not federal procurement as a whole.")
    fl = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=186, leading=14))
    H = int(A_END + 46 + 14 * fl + 22)

    s = plate.open_svg(
        W, H,
        "Hold the product family fixed and public notice nearly doubles; "
        "the commercial-item reversal was composition",
        subtitle=f"Both headline numbers are the product family showing through. "
                 f"{S['n_comp']:,} FY2016 civilian awards their own department labelled "
                 f"competed, carrying a usable bid count. Left of zero is fewer single-bid "
                 f"awards.")
    s += fr

    def axis(top, bot, labels_at):
        out = []
        for t in TICKS:
            col = INK2 if t == 0 else GRID
            wdt = 1.2 if t == 0 else 1
            out.append(f'<line x1="{x(t):.1f}" y1="{top:.1f}" x2="{x(t):.1f}" '
                       f'y2="{bot:.1f}" stroke="{col}" stroke-width="{wdt}"/>')
            out.append(txt(x(t), labels_at, f"{t*100:+.0f}" if t else "0",
                           size=9, fill=MUTED, anchor="middle"))
        return out

    def mark(v, yy, col, r=4.0):
        out = [f'<line x1="{x(v["lo"]):.1f}" y1="{yy:.1f}" x2="{x(v["hi"]):.1f}" '
               f'y2="{yy:.1f}" stroke="{col}" stroke-width="1.4" stroke-opacity="0.75"/>']
        for e2 in ("lo", "hi"):
            out.append(f'<line x1="{x(v[e2]):.1f}" y1="{yy-3.2:.1f}" x2="{x(v[e2]):.1f}" '
                       f'y2="{yy+3.2:.1f}" stroke="{col}" stroke-width="1.4" '
                       f'stroke-opacity="0.75"/>')
        out.append(f'<circle cx="{x(v["diff"]):.1f}" cy="{yy:.1f}" r="{r}" fill="{col}"/>')
        return out

    # -------------------------------------------------------- A: the control ladder
    s.append(txt(28, AY - 38, "the pooled comparison, as the controls are added",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(28, AY - 21, "each mark is the difference in single-bid rate with its 95% "
                              "interval; the strata are cumulative down each group",
                 size=10, fill=MUTED))
    s += axis(AY - 8, A_END - 22, A_END - 6)
    s.append(txt(x(0), A_END + 9, "difference in the share of competed awards that drew "
                                  "exactly one offer, percentage points",
                 size=9.5, fill=MUTED, anchor="middle"))
    NOTE = {"post": ("holding the family nearly doubles it",
                     f"and it is negative in {npos} of {len(S['fams'])} families"),
            "comm": ("the eight points were composition;",
                     f"a {cf['mde']*100:.1f} pt effect would have been visible"),
            "bpa": ("the biggest gap on this plate belongs to neither column.",
                    f"It is the {S['bpa_n']/S['n_comp']:.1%} of competed awards that are",
                    "calls placed on a blanket purchase agreement")}
    yy = AY
    for tag, col, head, sub, side in GROUPS:
        s.append(txt(28, yy + 10, head, size=11, fill=col, weight="700"))
        s.append(txt(W - 28, yy + 10, sub, size=9, fill=MUTED, anchor="end"))
        yy += GH
        # the connector first, so the marks sit on top of it. It asserts a sequence, and
        # the sequence is real: each stratification contains the one above it.
        pts = [(x(pick(lad[tag])["diff"]), yy + AR * i + AR / 2)
               for i, (_, pick) in enumerate(LAD)]
        s.append('<path d="M' + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts) +
                 f'" fill="none" stroke="{col}" stroke-width="1.3" stroke-opacity="0.45"/>')
        for i, (lab, pick) in enumerate(LAD):
            v = pick(lad[tag])
            ry = yy + AR * i + AR / 2
            s.append(txt(PX0 - GUT, ry + 3.4, lab, size=10,
                         fill=INK if i == len(LAD) - 1 else INK2,
                         anchor="end", weight="600" if i == len(LAD) - 1 else "normal"))
            s += mark(v, ry, col, r=4.6 if i == len(LAD) - 1 else 3.4)
            s += halo(x(v["diff"]) + (13 if v["diff"] >= 0 else -13), ry + 3.6,
                      f"{v['diff']*100:+.1f}", size=10, fill=col,
                      anchor="start" if v["diff"] >= 0 else "end",
                      weight="700" if i == len(LAD) - 1 else "600")
        last = pick(lad[tag])["diff"]
        if side:
            ax, an = x(last) + side * 18, "start" if side > 0 else "end"
            ny = yy + len(LAD) * AR - AR / 2 + 17
        else:
            ax, an = x(-0.435), "start"
            ny = yy + AR / 2 + 3.4
        for j, line in enumerate(NOTE[tag]):
            s += halo(ax, ny + 13 * j, line, size=9.5, fill=col, anchor=an,
                      weight="700" if j else "600")
        yy += len(LAD) * AR + AGAP

    # -------------------------------------------------------- footer
    # -------------------------------------------------------- footer
    fy = H - 20 - 14 * fl
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=186, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))

    print(f"  wrote {os.path.abspath(OUT)}  ({W}x{H})")
    print(f"  competed and usable {S['n_comp']:,}, single-bid "
          f"{S['k_comp']/S['n_comp']:.1%} ({S['k_comp']:,})")
    for tag, col, head, _, _side in GROUPS:
        print(f"  {head}")
        for (lab, pick) in LAD:
            v = pick(lad[tag])
            print(f"      {lab:<38}{v['diff']*100:+7.2f} pt "
                  f"[{v['lo']*100:+.2f},{v['hi']*100:+.2f}]  MDE80 {v['mde']*100:5.2f}  "
                  f"strata {v['strata']:>4}  dropped {v['drop']:.1%}")
    print(f"  per family: notice negative in {npos}, positive in {ppos}, "
          f"indistinguishable in {len(S['fams'])-npos-ppos}")
    print(f"              commercial negative in {ncom}, positive in {pcom}, "
          f"indistinguishable in {len(S['fams'])-ncom-pcom}")
    print(f"  median |gap| notice {med('post')*100:.1f} pt, commercial {med('comm')*100:.1f} pt")
    print(f"  blank fed_biz_opps {S['blank_tot']:,} competed awards, BPA calls are "
          f"{S['bpa_share_of_blank']:.1%} of them; {S['bpa_blank']/S['bpa_n']:.1%} of "
          f"competed BPA calls have it blank")
    return 0


if __name__ == "__main__":
    sys.exit(main())