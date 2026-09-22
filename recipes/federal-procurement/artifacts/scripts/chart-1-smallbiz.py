#!/usr/bin/env python3
"""Small business takes half the federal civilian awards and a quarter of the dollars.

    python3 chart-1-smallbiz.py

52.4% of awards and 26.1% of the dollars, on 554,171 civilian FY2016 awards. The sentence is
true on both bases and it misleads by a factor of two.

**The gap is not that small-business work is small.** The median small-business award is
$8,555 against $7,314 for everything else -- larger at the middle. Small business holds
50-57% of awards in every half-decade size band from $300 to $1m, which is 97.6% of all
awards. It collapses only above that, and there is **no tail at all**: 0 of the 35 awards
above $316m, and those 35 hold 23.7% of all the money.

**Checked against the continuous variable, not the bins.** Bands invite a curve, so the fall
was fitted on the 68,027 awards of $100,000 or more: the odds of a small-business win fall by
a factor of 0.652 per tenfold rise in award size. Below $100,000 the relation is flat to
rising, so the pooled fit over all positive awards is 1.034 and would read as no effect --
the range is stated rather than the pooled number.

**Who it lands on, and whether it is a programme effect, is figure 2.** This plate carried
four blocks until a reader said it was crowded; one chart per plate is the rule now.

**What this cannot show.** Business size is the contracting officer's determination on the
base action, not an audited status, and it disagrees between transactions of one award on 241
of 746,960 rows. The money curve uses the $128.9bn gross positive obligation as its base
because a cumulative share of the $125.8bn net exceeds 100% at the left edge; every other
percentage here is against the net.
"""
import bisect, collections, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate, sbiz                                                       # noqa: E402
from sbiz import (read_awards, logistic, med, SRC, SMALL, NONE_SA, SHORT, SA_SHORT,
                  RED, AMBER, GREEN, BLUE, SLATE)                     # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "1-smallbiz.svg")


def main():
    if not os.path.exists(SRC):
        raise SystemExit("  civilian-fy2016.zip missing -- run usa2.py")
    print("  reading transactions...", flush=True)
    aw, M = read_awards(SRC)
    ntx, disagree = M["tx"], M["disagree"]
    n = len(aw)
    tot = sum(a["ob"] for a in aw)
    sm = [a for a in aw if a["size"] == SMALL]
    ot = [a for a in aw if a["size"] and a["size"] != SMALL]
    aw_share = len(sm) / n
    dol_share = sum(a["ob"] for a in sm) / tot
    med_sm, med_ot = med([a["ob"] for a in sm]), med([a["ob"] for a in ot])
    topsmall = max(a["ob"] for a in sm) / sum(a["ob"] for a in sm)
    topother = max(a["ob"] for a in ot) / sum(a["ob"] for a in ot)

    # --- A: small-business share of awards by award size, half-decade bands
    pos = [a for a in aw if a["ob"] > 0]
    gross = sum(a["ob"] for a in pos)
    nonpos = [a for a in aw if a["ob"] <= 0]
    edges = [10 ** (e / 2) for e in range(4, 20)]           # $100 .. $10bn
    bands = []
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        g = [a for a in pos if lo <= a["ob"] < hi]
        if len(g) < 25:
            continue
        bands.append({"lo": lo, "hi": hi, "n": len(g),
                      "s": sum(1 for a in g if a["size"] == SMALL) / len(g),
                      "d": sum(a["ob"] for a in g) / gross})
    # merge the sparse top so the last drawn band is not a single award
    while len(bands) > 1 and bands[-1]["n"] < 60:
        b, p = bands.pop(), bands[-1]
        p.update(hi=b["hi"], n=p["n"] + b["n"],
                 s=(p["s"] * p["n"] + b["s"] * b["n"]) / (p["n"] + b["n"]),
                 d=p["d"] + b["d"])
    asc = sorted(a["ob"] for a in pos)
    cum = [0.0]
    for x in asc:
        cum.append(cum[-1] + x)
    below = lambda x: cum[bisect.bisect_left(asc, x)] / gross     # $ share under x
    half = asc[bisect.bisect_left(cum, 0.5 * gross) - 1]           # size holding the median $
    big = [a for a in pos if a["ob"] >= 10 ** 8.5]
    fit = [(math.log10(a["ob"]), 1.0 if a["size"] == SMALL else 0.0)
           for a in pos if a["ob"] >= 1e5]
    b0, b1 = logistic(fit)


    # ------------------------------------------------------------------- draw
    W, H = 1280, 812
    s = plate.open_svg(W, H, "Small business takes half the federal civilian awards and a "
                             "quarter of the dollars")
    fr, _ = plate.frame(W, 62,
                        who="anyone about to repeat the half-of-contracts figure",
                        decide="whether the claim being made needs the count base or the "
                               "dollar base",
                        wrong="the two bases agree, or the dollar shortfall disappears "
                              "inside departments")
    s += fr

    # ---- panel A: where the two bases part company ------------------------
    AX, AY, AH = 28, 222, 330
    GUT, x0, x1 = 118, 28 + 44, W - 124
    lo, hi = 2.0, 9.6                                  # log10 dollars
    px = lambda v: x0 + GUT + (x1 - x0 - GUT) * (math.log10(v) - lo) / (hi - lo)
    py = lambda f: AY + AH - AH * f
    s.append(txt(AX, 176, "where the two bases part company", size=13, fill=INK,
                 weight="600"))
    s.append(txt(AX, 194, "horizontal axis is what the award was actually obligated; both "
                          "curves are percentages of a stated base", size=10.5, fill=MUTED))
    for f in (0, .25, .5, .75, 1.0):
        s.append(f'<line x1="{x0:.1f}" y1="{py(f):.1f}" x2="{x1:.1f}" y2="{py(f):.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(x0 - 9, py(f) + 3.5, f"{f:.0%}", size=9.5, fill=MUTED, anchor="end"))
    for v, lab in ((1e2, "$100"), (1e3, "$1k"), (1e4, "$10k"), (1e5, "$100k"),
                   (1e6, "$1m"), (1e7, "$10m"), (1e8, "$100m"), (1e9, "$1bn")):
        s.append(f'<line x1="{px(v):.1f}" y1="{py(0):.1f}" x2="{px(v):.1f}" '
                 f'y2="{py(0)+5:.1f}" stroke="{MUTED}"/>')
        s.append(txt(px(v), py(0) + 18, lab, size=9.5, fill=MUTED, anchor="middle"))
    s.append(txt((x0 + GUT + x1) / 2, py(0) + 38, "obligation on the award", size=10.5,
                 fill=INK2, anchor="middle"))
    # money: share of positive dollars sitting in awards below x
    pts = [f"{px(10 ** (lo + (hi - lo) * i / 240)):.1f},"
           f"{py(below(10 ** (lo + (hi - lo) * i / 240))):.1f}" for i in range(241)]
    s.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{SLATE}" '
             f'stroke-width="2.4"/>')
    # small-business share of awards, one step per half-decade of award size
    step = []
    for b in bands:
        step.append(f"{max(px(b['lo']), px(10 ** lo)):.1f},{py(b['s']):.1f}")
        step.append(f"{min(px(b['hi']), x1):.1f},{py(b['s']):.1f}")
    s.append(f'<polyline points="{" ".join(step)}" fill="none" stroke="{GREEN}" '
             f'stroke-width="2.8" stroke-linejoin="round"/>')
    nmax = max(b["n"] for b in bands)
    for b in bands:
        cx = (max(px(b["lo"]), px(10 ** lo)) + min(px(b["hi"]), x1)) / 2
        s.append(f'<circle cx="{cx:.1f}" cy="{py(b["s"]):.1f}" '
                 f'r="{2.6 + 4.6 * (b["n"] / nmax) ** 0.5:.1f}" fill="{GREEN}" '
                 f'fill-opacity="0.5" stroke="{GREEN}" stroke-width="1.2"/>')
    for val, col, lab in ((aw_share, GREEN, "counting awards"),
                          (dol_share, INK2, "counting dollars")):
        s.append(f'<line x1="{x0:.1f}" y1="{py(val):.1f}" x2="{x1 + 6:.1f}" '
                 f'y2="{py(val):.1f}" stroke="{col}" stroke-width="1.3" '
                 f'stroke-dasharray="6 4"/>')
        s += halo(x1 + 11, py(val) - 2, f"{val:.1%}", size=12.5, fill=col, weight="700")
        s += halo(x1 + 11, py(val) + 12, lab, size=9.5, fill=col, weight="600")
    # the awards that net to zero or below have no place on a logarithmic axis
    gx = x0 + 50
    s.append(f'<line x1="{x0 + GUT - 34:.1f}" y1="{py(0):.1f}" x2="{x0 + GUT - 34:.1f}" '
             f'y2="{py(1.0):.1f}" stroke="{MUTED}" stroke-dasharray="3 3"/>')
    nz = sum(1 for a in nonpos if a["size"] == SMALL) / len(nonpos)
    s.append(f'<circle cx="{gx:.1f}" cy="{py(nz):.1f}" r="7.5" fill="{GREEN}" '
             f'fill-opacity="0.35" stroke="{GREEN}" stroke-width="1.5"/>')
    s += halo(gx, py(nz) - 13, f"{nz:.0%} small", size=10, fill=GREEN, anchor="middle",
              weight="700")
    for i, ln in enumerate((f"{len(nonpos):,} awards", f"({len(nonpos) / n:.0%}) net to",
                            "zero or below")):
        s.append(txt(gx, py(0) + 18 + i * 11, ln, size=9, fill=MUTED, anchor="middle"))
    # inline series labels
    s += halo(px(2.6e3), py(bands[3]["s"]) + 20,
              "share of the awards in each size band won by a small business",
              size=10.5, fill=GREEN, weight="700")
    s += halo(px(1.3e5), py(below(1.3e5)) - 24, "share of all obligated dollars sitting",
              size=10.5, fill=SLATE, weight="700")
    s += halo(px(1.3e5), py(below(1.3e5)) - 11, "in awards smaller than this", size=10.5,
              fill=SLATE, weight="700")
    ax, ay = px(1.6e7), py(0.82)
    n_half = sum(1 for x in asc if x >= half)
    s += halo(ax, ay, f"half of all the money is in the {n_half:,} awards above", size=10.5,
              fill=INK, weight="700")
    s += halo(ax, ay + 14, f"${half / 1e6:.1f}m -- {n_half / n:.2%} of the awards. None of",
              size=10.5, fill=INK, weight="700")
    s += halo(ax, ay + 28, f"the {len(big)} awards above $316m went to a small business.",
              size=10.5, fill=INK, weight="700")
    s.append(f'<line x1="{px(half):.1f}" y1="{py(0.50):.1f}" x2="{px(half):.1f}" '
             f'y2="{py(0.0):.1f}" stroke="{INK2}" stroke-width="1" stroke-dasharray="2 3"/>')
    s.append(f'<circle cx="{px(half):.1f}" cy="{py(0.50):.1f}" r="3.4" fill="{INK2}"/>')
    s += wrap(px(1.5e3), py(0.38),
              f"the steps are bins, so the fall was checked against the continuous variable: "
              f"fitted on the {len(fit):,} awards of $100,000 or more, the odds of a "
              f"small-business win fall by a factor of {math.exp(b1):.2f} per tenfold rise "
              f"in award size", size=9.5, fill=MUTED, chars=74, leading=13, weight="600")


    # ---- footer -----------------------------------------------------------
    # FOOTNOTE BEFORE TRIMMING, kept because it is method and method belongs in the script: f
    # oot = (USAspending API v2 bulk download, fetched 2026-09-22; {ntx:,} FY2016 prime
    # contract transactions for eleven civilian departments, collapsed to {n:,} awards on
    # contract_award_unique_key. Dollars are federal_action_obligation summed per award, de-
    # obligations included; keeping only positive rows would overstate the total by
    # {M['pos'] / tot - 1:.1%}. Business size is the contracting officer's determination on
    # the base action, not an audited status. The money curve is drawn against the ${gross /
    # 1e9:.1f}bn gross positive obligation because a cumulative share of the ${tot /
    # 1e9:.1f}bn net exceeds 100% at the left edge; every other percentage is against the
    # net. These departments are 8.5% of federal contract awards and Defense is 68.6%, so
    # this is not a claim about federal procurement as a whole. Where the gap lands is
    # figure 2; the fetch, the fold and the failed documentation control are in the recipe.)
    # Trimmed from the plate per doctrine/what-a-footnote-carries.md; kept here because it is method: f
    # oot = ( USAspending API v2 bulk download, fetched 2026-09-22; FY2016, 554,171 awards.
    # Dollars are federal_action_obligation per award with de-obligations kept. CAVEAT:
    # business size is the contracting officer's determination, not an audited status, and the
    # money curve uses the $128.9bn gross-positive base while every other share is against the
    # $125.8bn net. These eleven civilian departments are 8.5% of federal contract awards;
    # Defense (68.6%) is absent, so this is not federal procurement as a whole.)
    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2016, 554,171 awards. "
        "Dollars are federal_action_obligation per award with de-obligations kept. CAVEAT: "
        "business size is the contracting officer's determination, not an audited status, "
        "and the money curve uses the gross-positive base while every other share is "
        "against the net. These eleven civilian departments are 8.5% of federal contract "
        "awards; Defense (68.6%) is absent, so this is not federal procurement as a whole.")
    nl = len(wrap(28, 0, foot, size=10.5, fill=MUTED, chars=184))
    fy2 = H - 26 - 14 * (nl - 1)
    s.append(f'<line x1="28" y1="{fy2 - 18:.1f}" x2="{W - 28}" y2="{fy2 - 18:.1f}" '
             f'stroke="{RULE}"/>')
    s += wrap(28, fy2, foot, size=10.5, fill=MUTED, chars=184, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {n:,} awards, ${tot / 1e9:.1f}bn net")
    print(f"    small business: {aw_share:.1%} of awards, {dol_share:.1%} of dollars")
    print(f"    medians: small ${med_sm:,.0f}  other ${med_ot:,.0f}")
    print(f"    logistic on awards >= $100k (n={len(fit):,}): "
          f"odds x{math.exp(b1):.3f} per decade of award size")
    print(f"    half the money is above ${half:,.0f} "
          f"({sum(1 for x in asc if x >= half):,} awards)")
    print(f"    awards above $316m: {sum(1 for a in aw if a['ob'] > 316e6)}, "
          f"of which small business: "
          f"{sum(1 for a in aw if a['ob'] > 316e6 and a['size'] == SMALL)}")
    print(f"    largest single award is {topsmall:.2%} of the small-business total, "
          f"{topother:.2%} of the other-than-small total")
    return 0


if __name__ == "__main__":
    sys.exit(main())