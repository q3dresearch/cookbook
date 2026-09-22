#!/usr/bin/env python3
"""The register lost a fifth of a million awards, and 78% of them were under $10,000.

    python3 chart-20-comparability.py

FY2016 and FY2025 come from the same eleven departments under the same collapse rule, and
they do not describe the same population. FY2016: **444,495** positive awards, $125.8bn,
median $12,423. FY2025: **232,751**, $231.8bn, median **$39,000**. Awards down 41%, dollars up
84%, and the typical award three times larger.

**It is a reporting change, not a behaviour change.** The loss is not spread across the
distribution: **78% of it sits below $10,000**, and the largest single band is $3,500 to
$10,000, which lost **124,219** awards on its own. The micro-purchase threshold was $3,500
through FY2017 and **$10,000 from FY2018**. Below that line a purchase goes on a government
card and is not reported as a contract action at all. The awards did not stop happening; they
stopped being filed.

**Everything above $316,000 grew.** Every band from $316k up has more awards in FY2025 than in
FY2016, so the big end is a real increase sitting underneath a reporting cut at the small end.
Transactions per award moved only 1.35 to 1.51, so the collapse rule is not what changed --
which was the one candidate that would have invalidated the comparison rather than explained
it.

**What this licenses and forbids, which is the reason to draw it.** Any figure in this recipe
that counts awards, takes a median, or lives at the small end -- the size curve, the
small-business share, the set-aside programmes -- **cannot be compared across FY2018** without
first cutting both years at $10,000. Figure 12 is unaffected: it measures the shape of the
distribution around $150,000 and $250,000, far above the line that moved.

**What this cannot show.** Where the card purchases went. They are absent from this register by
design, so their volume, their suppliers and their competition are all invisible here, and no
amount of care with the remaining rows recovers them.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cmp2, plate                                                       # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "20-comparability.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"


def main():
    d = cmp2.load()
    names, A, B = d["names"], d["years"]["2016"], d["years"]["2025"]
    c16, c25 = A["counts"], B["counts"]
    loss = A["positive"] - B["positive"]
    under = sum(c16[:3]) - sum(c25[:3])

    W, H = 1240, 754
    s = plate.open_svg(
        W, H,
        "The register lost a fifth of a million awards, and 78% of them were under $10,000",
        subtitle=f"FY2016 and FY2025, same eleven departments, same collapse rule: "
                 f"{A['positive']:,} positive awards against {B['positive']:,}, and "
                 f"${A['net']/1e9:.1f}bn against ${B['net']/1e9:.1f}bn.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone about to compare a count, a median or a small-award share across "
            "these two years",
        decide="whether the two years describe the same population, and at what value "
               "they start to",
        wrong="the loss is spread evenly across the bands, or the bands above $316,000 "
              "shrank too")
    s += fr

    # ---- one chart: every band, both years -----------------------------------
    AX, AY, AW = 64, y0 + 62, 1112
    ROW = 30.0
    AH = ROW * len(names)
    lo, hi = 100, 200000
    lg = lambda v: math.log10(max(v, lo))
    ax = lambda v: AX + 232 + (AW - 300) * (lg(v) - lg(lo)) / (lg(hi) - lg(lo))
    ay = lambda i: AY + ROW * i + ROW / 2
    s.append(txt(AX - 36, AY - 38, "awards in each value band, FY2016 against FY2025",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(AX - 36, AY - 21, "positive-value awards only; the bar is the change, and "
                                   "the count axis is logarithmic", size=10, fill=MUTED))
    for g in (100, 1000, 10000, 100000):
        s.append(f'<line x1="{ax(g):.1f}" y1="{AY-6:.1f}" x2="{ax(g):.1f}" '
                 f'y2="{AY+AH+2:.1f}" stroke="{GRID}"/>')
        s.append(txt(ax(g), AY + AH + 17, f"{g:,}", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX + 232, AY + AH + 34, "awards in the band (log scale)", size=9.5,
                 fill=MUTED))
    for i, nm in enumerate(names):
        yy = ay(i)
        a, b = c16[i], c25[i]
        grew = b >= a
        col = GREEN if grew else RED
        if a and b:
            s.append(f'<line x1="{ax(a):.1f}" y1="{yy:.1f}" x2="{ax(b):.1f}" '
                     f'y2="{yy:.1f}" stroke="{col}" stroke-width="2.2" '
                     f'stroke-opacity="0.6"/>')
        if a:
            s.append(f'<circle cx="{ax(a):.1f}" cy="{yy:.1f}" r="3.2" fill="none" '
                     f'stroke="{SLATE}" stroke-width="1.4"/>')
        if b:
            s.append(f'<circle cx="{ax(b):.1f}" cy="{yy:.1f}" r="3.8" fill="{col}"/>')
        s.append(txt(AX + 224, yy + 3.6, nm, size=10, fill=INK, anchor="end"))
        dd = b - a
        s += halo(ax(max(a, b)) + 10, yy + 3.6,
                  f"{dd:+,}" + (f"   {-dd/loss:.0%} of the loss" if dd < -3000 else ""),
                  size=9.5, fill=col, weight="700")
    # the two micro-purchase lines are the explanation, so they are drawn on the bands
    for i, (lab, col) in enumerate((("$3,500: the line through FY2017", SLATE),
                                    ("$10,000: the line from FY2018", INK))):
        yb = ay(2 + i) - ROW / 2
        s.append(f'<line x1="{AX+236:.1f}" y1="{yb:.1f}" x2="{AX+AW-56:.1f}" '
                 f'y2="{yb:.1f}" stroke="{col}" stroke-width="1.3" '
                 f'stroke-dasharray="4 3"/>')
        s += halo(AX + 240, yb - 5, lab, size=9, fill=col, weight="700")
    s += halo(ax(hi) - 4, ay(0) - 8,
              f"below the newer line: {under:,} fewer awards, {under/loss:.0%} of the "
              f"whole loss", size=9.5, fill=RED, anchor="end", weight="700")
    s += halo(ax(hi) - 4, ay(len(names) - 1) + 12,
              "every band above $316,000 grew", size=9.5, fill=GREEN, anchor="end",
              weight="700")
    lx, ly = AX + 620, AY + AH + 34
    s.append(f'<circle cx="{lx:.1f}" cy="{ly-3.5:.1f}" r="3.2" fill="none" '
             f'stroke="{SLATE}" stroke-width="1.4"/>')
    s.append(txt(lx + 10, ly, "FY2016", size=9.5, fill=MUTED))
    s.append(f'<circle cx="{lx+70:.1f}" cy="{ly-3.5:.1f}" r="3.8" fill="{SLATE}"/>')
    s.append(txt(lx + 80, ly, "FY2025", size=9.5, fill=MUTED))

    # Trimmed from the plate per doctrine/what-a-footnote-carries.md; kept here because it is method: f
    # oot = (USAspending API v2 bulk download; contract transactions for the same eleven
    # civilian departments in FY2016 and FY2025, collapsed to awards on
    # contract_award_unique_key and summed to a net obligation. Positive-value awards only:
    # {A['positive']:,} and {B['positive']:,}. Transactions per award moved
    # {A['tx_per_award']:.2f} to {B['tx_per_award']:.2f} and the share naming a parent vehicle
    # {A['with_parent']:.1%} to {B['with_parent']:.1%}, so the collapse rule and the vehicle
    # structure are not what changed -- a change in what counts as a distinct award was the
    # one candidate that would have invalidated this comparison rather than explained it, and
    # it is ruled out. The micro-purchase threshold history is the FAR's, not inferred from
    # the data. Median positive award ${A['median_positive']:,.0f} to
    # ${B['median_positive']:,.0f}. Dollar figures are nominal and not deflated, so part of
    # the upward drift in every band is inflation and none of the 78% below $10,000 is. Card
    # purchases below the threshold are absent from this register by design and nothing here
    # recovers them. These eleven departments are 8.5% of federal contract awards and Defense
    # is 68.6%, so nothing here describes federal procurement as a whole.)
    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2016 and FY2025, the same "
        "departments, positive awards only. The micro-purchase threshold history is the "
        "FAR's. CAVEAT: dollars are nominal and not deflated, so part of the upward drift "
        "in every band is inflation and none of the 78% below $10,000 is. These eleven "
        "civilian departments are 8.5% of federal contract awards; Defense (68.6%) is "
        "absent, so this is not federal procurement as a whole.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=186, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=186, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    net loss {loss:,}; under $10,000 accounts for {under:,} = {under/loss:.1%}")
    for i, nm in enumerate(names):
        print(f"      {nm:<16}{c16[i]:>9,}{c25[i]:>9,}{c25[i]-c16[i]:>+10,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
