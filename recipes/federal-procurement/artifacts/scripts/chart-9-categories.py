#!/usr/bin/env python3
"""What is bought predicts competition better than who buys it.

    python3 chart-9-categories.py

Every award carries a product or service code, and its first character is the register's
own top-level family. Scoring each family on how often its *competed* awards drew exactly
one bid gives a spread of **50 points**, from construction at 14.6% to medical and
laboratory equipment at 64.8%.

**Neither obvious explanation carries it.** Scoring each family at the national rate of the
departments that happen to buy it predicts a spread of about 17 points and accounts for
**29%** of the variance between families. Extrapolating figure 5's mechanism -- orders
against an already-competed vehicle draw one bid 59.9% of the time against 32.5% for other
procedures -- accounts for **19%**. Construction lands **26 points** below what the
departments buying it would predict, clothing and subsistence 18 below, social services 18
above.

**The base matters here more than anywhere else in this recipe.** Across all awards,
vehicle orders are 60.0% single-bid and everything else 59.6%, which looks like the
mechanism evaporating. It is not: the uncompeted awards are 99%+ single-bid whatever
procedure is recorded, and they swamp the comparison. Inside the competed label the gap is
27 points. Every rate on this plate is on the competed base, and the all-award figure is
given in the footer so the two cannot be confused.

**What this cannot show.** Why a category competes. The register encodes what was bought
and how it was solicited, not whether the thing has a catalogue price or has to be designed,
which is the distinction the residuals look like. Naming that would need a source this
recipe does not have, so it is left as an unexplained effect rather than dressed as one.

**A warning for anyone building a screen.** Supplier count is not the variable it looks
like. Facility operation has 340 suppliers and 26.4% single bids across all its awards;
medical and laboratory equipment has 10,101 and 77.0%. A concentrated market here competes
harder than a crowded one, so a screen ranking categories on supplier counts ranks them
close to backwards.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cats, plate                                                       # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "9-categories.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
MIN_C = 1000          # families below this many competed awards are not scored


def sd(v):
    m = sum(v) / len(v)
    return (sum((x - m) ** 2 for x in v) / len(v)) ** 0.5


def main():
    d = cats.load()
    F = {k: v for k, v in d["families"].items() if v["cn"] and v["cn"] >= MIN_C}
    ks = sorted(F, key=lambda k: -F[k]["crate"])
    act = [F[k]["crate"] for k in ks]
    exp = [F[k]["cexp"] for k in ks]
    vr, orr = d["veh_rate"], d["other_rate"]
    vp = {k: orr + F[k]["cveh"] * (vr - orr) for k in ks}
    ex_dep = 1 - sd([F[k]["crate"] - F[k]["cexp"] for k in ks]) ** 2 / sd(act) ** 2
    ex_veh = 1 - sd([F[k]["crate"] - vp[k] for k in ks]) ** 2 / sd(act) ** 2

    W, H = 1240, 966
    s = plate.open_svg(
        W, H, "What is bought predicts competition better than who buys it",
        subtitle=f"Among awards their own department labelled competed, the single-bid rate "
                 f"runs from {min(act):.1%} to {max(act):.1%} across product families — and "
                 f"neither the buying department nor the contract vehicle accounts for it.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone screening categories for weak competition, or explaining a single bid "
            "with market structure",
        decide="whether to screen on what is being bought or on who is buying it",
        wrong="the two columns on the left line up, or the families sit on the vehicle "
              "line on the right")
    s += fr

    # ---------------------------------------------------------------- A: the dumbbells
    AX, AY, AW = 28, y0 + 58, 556
    ROW = 16.4
    AH = ROW * len(ks)
    ax = lambda r: AX + 214 + (AW - 250) * (r - 0.05) / 0.65
    ay = lambda i: AY + ROW * i + ROW / 2
    s.append(txt(AX, AY - 36, "each family, against the rate its buyers' own habits predict",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(AX, AY - 19, f"{len(ks)} product families with {MIN_C:,} or more competed "
                              f"awards; hollow mark is the department-mix prediction",
                 size=10, fill=MUTED))
    for g in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6):
        s.append(f'<line x1="{ax(g):.1f}" y1="{AY-4:.1f}" x2="{ax(g):.1f}" '
                 f'y2="{AY+AH+2:.1f}" stroke="{GRID}"/>')
        s.append(txt(ax(g), AY + AH + 16, f"{g:.0%}", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX + 214, AY + AH + 32, "share of the family's competed awards that drew "
                                         "exactly one offer", size=9.5, fill=MUTED))
    for i, k in enumerate(ks):
        v = F[k]
        yy = ay(i)
        col = GREEN if v["crate"] < v["cexp"] else RED
        s.append(f'<line x1="{ax(v["cexp"]):.1f}" y1="{yy:.1f}" x2="{ax(v["crate"]):.1f}" '
                 f'y2="{yy:.1f}" stroke="{col}" stroke-width="1.7" stroke-opacity="0.65"/>')
        s.append(f'<circle cx="{ax(v["cexp"]):.1f}" cy="{yy:.1f}" r="3.1" fill="none" '
                 f'stroke="{SLATE}" stroke-width="1.3"/>')
        s.append(f'<circle cx="{ax(v["crate"]):.1f}" cy="{yy:.1f}" r="3.6" fill="{col}"/>')
        s.append(txt(AX + 206, yy + 3.4, v["name"][:30], size=9.5,
                     fill=INK if abs(v["crate"] - v["cexp"]) >= 0.1 else INK2, anchor="end"))
        s.append(txt(AX + 2, yy + 3.4, f"{v['cn']:,}", size=8.5, fill=MUTED))
    big = max(ks, key=lambda k: F[k]["cexp"] - F[k]["crate"])
    s += halo(ax(0.075), ay(1), f"{F[big]['name']} lands", size=9.5, fill=GREEN)
    s += halo(ax(0.075), ay(1) + 13,
              f"{(F[big]['cexp']-F[big]['crate'])*100:.0f} points below what its",
              size=9.5, fill=GREEN)
    s += halo(ax(0.075), ay(1) + 26, "buyers' own habits predict", size=9.5, fill=GREEN,
              weight="700")

    # ---------------------------------------------------------------- B: the mechanism
    BX, BY, BS = 700, AY, 452
    bx = lambda v: BX + 56 + (BS - 74) * (v - 0.0) / 0.80
    by = lambda v: BY + BS - 44 - (BS - 78) * (v - 0.05) / 0.65
    s.append(txt(BX - 28, AY - 36, "and against figure 5's mechanism, extrapolated",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(BX - 28, AY - 19, "one mark per family, area is its competed awards",
                 size=10, fill=MUTED))
    for g in (0.1, 0.3, 0.5, 0.7):
        s.append(f'<line x1="{bx(g):.1f}" y1="{by(0.05):.1f}" x2="{bx(g):.1f}" '
                 f'y2="{by(0.70):.1f}" stroke="{GRID}"/>')
        s.append(txt(bx(g), by(0.05) + 16, f"{g:.0%}", size=9, fill=MUTED, anchor="middle"))
    for g in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6):
        s.append(f'<line x1="{bx(0):.1f}" y1="{by(g):.1f}" x2="{bx(0.80):.1f}" '
                 f'y2="{by(g):.1f}" stroke="{GRID}"/>')
        s.append(txt(bx(0) - 8, by(g) + 3, f"{g:.0%}", size=9, fill=MUTED, anchor="end"))
    s.append(txt(BX - 28, by(0.05) + 32, "share of the family's competed awards placed "
                                         "against a vehicle", size=9.5, fill=MUTED))
    s.append(f'<text x="{BX+18}" y="{by(0.05):.1f}" font-size="9.5" fill="{MUTED}" '
             f'transform="rotate(-90 {BX+18} {by(0.05):.1f})">'
             f'share that drew exactly one offer</text>')
    # the award-level mechanism, drawn as the line it would imply
    s.append(f'<path d="M{bx(0):.1f},{by(orr):.1f} L{bx(0.80):.1f},'
             f'{by(orr + 0.80*(vr-orr)):.1f}" fill="none" stroke="{INK2}" '
             f'stroke-width="1.5" stroke-dasharray="5 3"/>')
    s += halo(bx(0.015), by(0.655), "if only the vehicle mattered, the families",
              size=9.5, fill=INK2)
    s += halo(bx(0.015), by(0.655) + 13,
              f"would sit on this line: {orr:.0%} rising to {vr:.0%}",
              size=9.5, fill=INK2, weight="700")
    LAB = {"6": (1, 4), "Y": (1, 4), "8": (1, 4), "G": (1, 4), "D": (1, -7),
           "Q": (1, 4), "R": (1, 4), "Z": (-1, 4), "A": (1, 4)}
    for k in sorted(ks, key=lambda z: -F[z]["cn"]):
        v = F[k]
        r = max(3.0, math.sqrt(v["cn"]) / 42)
        col = GREEN if v["crate"] < vp[k] else RED
        s.append(f'<circle cx="{bx(v["cveh"]):.1f}" cy="{by(v["crate"]):.1f}" r="{r:.1f}" '
                 f'fill="{col}" fill-opacity="0.2" stroke="{col}" stroke-width="1.3"/>')
        if k in LAB:
            sx, dy = LAB[k]
            s += halo(bx(v["cveh"]) + sx * (r + 5), by(v["crate"]) + dy, v["name"][:32],
                      size=9, fill=col, anchor="start" if sx > 0 else "end", weight="700")
    s += halo(bx(0.78), by(0.115), f"the line accounts for {ex_veh:.0%} of the spread;",
              size=9.5, fill=INK2, anchor="end")
    s += halo(bx(0.78), by(0.115) + 13, f"the departments for {ex_dep:.0%}",
              size=9.5, fill=INK2, anchor="end", weight="700")

    # ---------------------------------------------------------------- caption
    cy0 = AY + AH + 62
    s.append(txt(28, cy0, "a screen on supplier counts would rank these close to backwards",
                 size=12, fill=INK, weight="600"))
    m6, mm = d["families"]["6"], d["families"]["M"]
    s += wrap(28, cy0 + 20,
              f"Facility operation has {mm['suppliers']:,} distinct parent suppliers across "
              f"{mm['n']:,} awards and draws one bid {mm['rate']:.1%} of the time; medical "
              f"and laboratory equipment has {m6['suppliers']:,} across {m6['n']:,} and "
              f"draws one {m6['rate']:.1%} of the time. Across the {len(ks)} families the "
              f"correlation between how concentrated the suppliers are and how often one bid "
              f"arrives is slightly negative, so the crowded markets are the quiet ones. "
              f"Whatever decides this, it is a property of the thing being bought rather than "
              f"of the number of firms able to sell it — and that is the variable an "
              f"oversight screen would most naturally reach for first.",
              size=10.5, fill=INK2, chars=186, leading=14.5)

    # Trimmed from the plate per doctrine/what-a-footnote-carries.md; kept here because it is method: f
    # oot = (USAspending API v2 bulk download, fetched 2026-09-22; contract transactions with
    # an action date in FY2016, eleven civilian departments, collapsed to {d['n_awards']:,}
    # awards on contract_award_unique_key. Families are the first character of
    # product_or_service_code, the register's own taxonomy, present on 99.8% of awards. Rates
    # use the {d['n_comp']:,} awards that carry a competed label AND a usable bid count, where
    # a recorded 0 offers is not a count (1,876 awards). On that base vehicle orders are
    # {vr:.1%} single-bid against {orr:.1%} for other procedures; across ALL awards the same
    # two figures are 60.0% and 59.6%, because uncompeted awards are 99%+ single-bid whatever
    # the procedure and swamp the comparison — the all-award reading is the confounded one.
    # The department-mix prediction scores each family at the national single-bid rate of the
    # departments that bought it, so it is a composition control and not a causal claim.
    # Families below {MIN_C:,} competed awards are not drawn. These eleven departments are
    # 8.5% of federal contract awards, Defense is 68.6% and its product mix is distinctive, so
    # nothing here describes federal procurement as a whole.)
    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2016. Rates use the awards "
        "carrying a competed label and a usable bid count. CAVEAT: across ALL awards "
        "vehicle orders are 60.0% single-bid and everything else 59.6% -- uncompeted awards "
        "are 99%+ single-bid whatever the procedure and swamp that comparison. These eleven "
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
    print(f"    {len(ks)} families; competed single-bid {min(act):.1%} to {max(act):.1%}")
    print(f"    department mix explains {ex_dep:.1%}; the vehicle line {ex_veh:.1%}")
    for k in ks[:3] + ks[-3:]:
        v = F[k]
        print(f"      {k} {v['name'][:30]:<32}n={v['cn']:>7,} act {v['crate']:>6.1%} "
              f"dept {v['cexp']:>6.1%} veh-line {vp[k]:>6.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
