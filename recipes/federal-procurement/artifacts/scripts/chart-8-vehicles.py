#!/usr/bin/env python3
"""Competition is a property of the vehicle, not of the department or the product.

    python3 chart-8-vehicles.py

`parent_award_id_piid` names the actual parent contract an order was placed against. It is
populated on **67.9%** of competed FY2016 awards and identifies **35,346** distinct vehicles;
688 carry fifty or more awards.

**Their single-bid rates run the whole range.** p10 **0%**, median 47%, p90 **99%**, against a
pooled 49.9%. 132 of the 688 never draw a second bid and 63 always do.

**The tails are not thin samples.** Raise the floor tenfold and they survive: at 500 or more
awards each, six vehicles still sit at exactly 0% single-bid. A contract that has been ordered
against five hundred times and has never once drawn a second bidder is not a small sample.

**And it is not what they buy.** Scoring each vehicle against the national rate of the product
families it actually carries leaves the spread almost intact -- **sd 38.2 points falls only to
34.7**, so the product mix accounts for about 17%.

**Which reframes the recipe's headline.** Eight figures explained single bids with categories
an award belongs to: department 23-34%, vehicle *procedure* 18%, product family 17%, public
advertisement about 4 points, supplier concentration about 2%. None is the right size for the
effect. The instrument itself is, and an instrument is a management choice rather than a market
fact -- which matters because management is changeable.

**What this cannot show.** Why any particular vehicle behaves as it does. The register names
the parent contract but not its terms, its ceiling, how many holders it has, or whether its
competition was real. It also cannot see the 32.1% of competed awards that name no parent at
all, which are a different population and are excluded rather than assumed away.
"""
import collections, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate, veh                                                        # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "8-vehicles.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"


def sd(v):
    m = sum(v) / len(v)
    return (sum((x - m) ** 2 for x in v) / len(v)) ** 0.5


def main():
    d = veh.load()
    R = sorted(d["vehicles"], key=lambda r: -r["n"])
    pooled = d["pooled_rate"]
    scored = [r for r in R if r["exp"] is not None]
    A = [r["rate"] for r in scored]
    Rs = [r["rate"] - r["exp"] for r in scored]
    explained = max(0.0, 1 - sd(Rs) ** 2 / sd(A) ** 2)

    W, H = 1240, 790
    s = plate.open_svg(
        W, H,
        "Whether anyone competes is a property of the vehicle, not of the buyer or the "
        "product",
        subtitle=f"{len(R)} contract vehicles carrying {d['floor']} or more competed FY2016 "
                 f"awards. The pooled single-bid rate is {pooled:.1%}; the vehicles behind it "
                 f"run from 0% to 100%.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone screening for weak competition, or explaining a single bid with the "
            "agency, the market or the product",
        decide="whether to screen on the contract vehicle or on a category the award "
               "belongs to",
        wrong="the extremes disappear as the award floor rises, or the product mix a "
              "vehicle carries accounts for its rate")
    s += fr

    # ---- panel A: rate against how many awards produced it ------------------
    AX, AY, AW, AH = 64, y0 + 58, 556, 430
    nlo, nhi = d["floor"], max(r["n"] for r in R)
    lg = lambda v: math.log10(max(v, nlo))
    ax = lambda v: AX + 56 + (AW - 74) * (lg(v) - lg(nlo)) / (lg(nhi) - lg(nlo))
    ay = lambda v: AY + AH - 44 - (AH - 60) * v
    s.append(txt(AX - 36, AY - 34, "every vehicle, against the awards behind its rate",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(AX - 36, AY - 17, "if the extremes were small samples they would close as "
                                   "the count grows", size=10, fill=MUTED))
    for g in (0.0, 0.25, 0.50, 0.75, 1.0):
        s.append(f'<line x1="{ax(nlo):.1f}" y1="{ay(g):.1f}" x2="{ax(nhi):.1f}" '
                 f'y2="{ay(g):.1f}" stroke="{GRID}"/>')
        s.append(txt(ax(nlo) - 8, ay(g) + 3, f"{g:.0%}", size=9, fill=MUTED, anchor="end"))
    for v in (50, 100, 250, 500, 1000, 3000):
        if v <= nhi:
            s.append(txt(ax(v), ay(0) + 16, f"{v:,}", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX - 36, ay(0) + 34, "competed awards placed against that vehicle (log)",
                 size=9.5, fill=MUTED))
    s.append(f'<text x="{AX-14}" y="{ay(0):.1f}" font-size="9.5" fill="{INK2}" '
             f'transform="rotate(-90 {AX-14} {ay(0):.1f})">'
             f'share of them that drew exactly one offer</text>')
    s.append(f'<line x1="{ax(nlo):.1f}" y1="{ay(pooled):.1f}" x2="{ax(nhi):.1f}" '
             f'y2="{ay(pooled):.1f}" stroke="{INK2}" stroke-width="1.3" '
             f'stroke-dasharray="5 3"/>')
    s += halo(ax(nhi), ay(pooled) - 7, f"pooled rate across all of them, {pooled:.1%}",
              size=9.5, fill=INK2, anchor="end", weight="700")
    for r in R:
        col = RED if r["rate"] >= 0.995 else (GREEN if r["rate"] <= 0.005 else SLATE)
        rad = 2.6 if col == SLATE else 3.4
        s.append(f'<circle cx="{ax(r["n"]):.1f}" cy="{ay(r["rate"]):.1f}" r="{rad:.1f}" '
                 f'fill="{col}" fill-opacity="{0.45 if col == SLATE else 0.8}"/>')
    for lo in (100, 250, 500):
        s.append(f'<line x1="{ax(lo):.1f}" y1="{ay(1.0):.1f}" x2="{ax(lo):.1f}" '
                 f'y2="{ay(0.0):.1f}" stroke="{FAINT}" stroke-dasharray="2 4"/>')
        s += halo(ax(lo) + 3, ay(1.0) - 6, f"{lo}+", size=8.5, fill=MUTED)
    # the floor counts stack in the sparse upper right rather than sitting on the marks
    s += halo(ax(900), ay(0.46), "raising the floor keeps both tails", size=9,
              fill=INK2, weight="700")
    for i, lo in enumerate((100, 250, 500)):
        g = [r for r in R if r["n"] >= lo]
        z = sum(1 for r in g if r["rate"] == 0.0)
        h = sum(1 for r in g if r["rate"] == 1.0)
        s += halo(ax(900), ay(0.46) + 13 + i * 12,
                  f"{lo}+ awards: {z} never, {h} always", size=8.5, fill=MUTED)
    s += halo(ax(nlo) + 6, ay(0.045), f"{sum(1 for r in R if r["rate"] == 0.0)} vehicles "
              f"never draw a second bid", size=9.5, fill=GREEN, weight="700")
    s += halo(ax(nlo) + 6, ay(0.955), f"{sum(1 for r in R if r["rate"] == 1.0)} always do",
              size=9.5, fill=RED, weight="700")

    # ---- panel B: against what the vehicle actually buys ---------------------
    BX, BY, BS = 700, AY, 430
    bx = lambda v: BX + 56 + (BS - 74) * v
    by = lambda v: BY + BS - 44 - (BS - 60) * v
    s.append(txt(BX - 30, AY - 34, "and against the mix of things it carries",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(BX - 30, AY - 17, f"each vehicle scored at the national rate of its own "
                                   f"product families ({len(scored)} with enough to score)",
                 size=10, fill=MUTED))
    for g in (0.0, 0.25, 0.50, 0.75, 1.0):
        s.append(f'<line x1="{bx(g):.1f}" y1="{by(0):.1f}" x2="{bx(g):.1f}" '
                 f'y2="{by(1):.1f}" stroke="{GRID}"/>')
        s.append(f'<line x1="{bx(0):.1f}" y1="{by(g):.1f}" x2="{bx(1):.1f}" '
                 f'y2="{by(g):.1f}" stroke="{GRID}"/>')
        s.append(txt(bx(g), by(0) + 16, f"{g:.0%}", size=9, fill=MUTED, anchor="middle"))
        s.append(txt(bx(0) - 8, by(g) + 3, f"{g:.0%}", size=9, fill=MUTED, anchor="end"))
    s.append(txt(BX - 30, by(0) + 34, "rate its product mix predicts", size=9.5, fill=MUTED))
    s.append(f'<text x="{BX-12}" y="{by(0):.1f}" font-size="9.5" fill="{INK2}" '
             f'transform="rotate(-90 {BX-12} {by(0):.1f})">'
             f'rate it actually had</text>')
    s.append(f'<path d="M{bx(0):.1f},{by(0):.1f} L{bx(1):.1f},{by(1):.1f}" fill="none" '
             f'stroke="{INK2}" stroke-width="1.4" stroke-dasharray="5 3"/>')
    s += halo(bx(0.02), by(0.86), "on this line what a vehicle buys", size=9.5, fill=INK2)
    s += halo(bx(0.02), by(0.86) + 12, "would account for how it behaves", size=9.5,
              fill=INK2)
    for r in sorted(scored, key=lambda z: -z["n"]):
        col = RED if r["rate"] >= 0.995 else (GREEN if r["rate"] <= 0.005 else SLATE)
        rad = max(2.4, math.sqrt(r["n"]) / 11)
        s.append(f'<circle cx="{bx(r["exp"]):.1f}" cy="{by(r["rate"]):.1f}" r="{rad:.1f}" '
                 f'fill="{col}" fill-opacity="0.22" stroke="{col}" stroke-width="1.1"/>')
    s += halo(bx(0.97), by(0.20), f"spread of the actual rates: sd {sd(A)*100:.1f} points",
              size=9.5, fill=INK2, anchor="end")
    s += halo(bx(0.97), by(0.20) + 13, f"left after the product mix: sd {sd(Rs)*100:.1f}",
              size=9.5, fill=INK2, anchor="end", weight="700")
    s += halo(bx(0.97), by(0.20) + 26, f"so the mix accounts for {explained:.0%}",
              size=9.5, fill=INK2, anchor="end", weight="700")

    # Trimmed from the plate per doctrine/what-a-footnote-carries.md; kept here because it is method: f
    # oot = (USAspending API v2 bulk download, fetched 2026-09-22; FY2016 contract
    # transactions for eleven civilian departments, collapsed to awards on
    # contract_award_unique_key. Restricted to the {d['n_named']:,} awards that carry a
    # competed label, a usable bid count and a parent_award_id_piid --
    # {d['n_named']/d['n_competed']:.1%} of competed awards; the rest name no parent and are a
    # different population, excluded rather than assumed. A recorded 0 offers is not a bid
    # count. {d['n_distinct']:,} distinct vehicles appear; {len(R)} carry {d['floor']} or more
    # competed awards and only those are drawn, because a rate on fewer is not worth a mark.
    # The product-mix score gives each vehicle the national single-bid rate of the product
    # families it actually carries, and is computed only where at least 40 of its awards fall
    # in a family with 500 or more awards nationally ({len(scored)} vehicles qualify); it is a
    # composition control, not a causal claim. Vehicle identity is the PIID as filed and is
    # not normalised, so a vehicle recorded under two spellings appears twice and would split
    # its awards -- which would understate, not manufacture, the extremes. These eleven
    # departments are 8.5% of federal contract awards and Defense is 68.6%, so nothing here
    # describes federal procurement as a whole.)
    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2016. The 273,026 competed "
        "awards carrying a usable bid count and a parent_award_id_piid, 67.9% of competed "
        "awards; the rest name no parent and are excluded. CAVEAT: vehicle identity is the "
        "PIID as filed and is not normalised, which understates the extremes rather than "
        "creating them. These eleven civilian departments are 8.5% of federal contract "
        "awards; Defense (68.6%) is absent, so this is not federal procurement as a whole.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=186, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=186, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {len(R)} vehicles at {d['floor']}+ awards; pooled {pooled:.1%}")
    print(f"    actual sd {sd(A)*100:.2f} pts; residual sd {sd(Rs)*100:.2f}; "
          f"mix explains {explained:.1%}")
    for lo in (50, 100, 250, 500):
        g = sorted(r["rate"] for r in R if r["n"] >= lo)
        print(f"      {lo:>4}+: {len(g):>4} vehicles  p10 {g[len(g)//10]:.0%} "
              f"median {g[len(g)//2]:.0%} p90 {g[9*len(g)//10]:.0%}  "
              f"at 0% {sum(1 for x in g if x == 0)}  at 100% {sum(1 for x in g if x == 1)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
