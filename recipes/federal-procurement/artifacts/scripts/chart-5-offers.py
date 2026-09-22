#!/usr/bin/env python3
"""A third of awards are labelled competed and drew exactly one bid.

    python3 chart-5-offers.py

The register carries two measures of competition on the same row: `extent_competed`, which is
the procedure the contracting officer recorded, and `number_of_offers_received`, which is how
many firms actually answered. They do not agree.

**180,868 awards -- 32.8% of the file -- carry a competed label and one bid.** That is 45% of
everything labelled competed.

**The label is near-deterministic in one direction only.** When it says NOT COMPETED, 99.8% of
awards drew one bid, which is what the label means. When it says COMPETED, 45% did, which is
close to a coin toss. A ranking built on the competed label is therefore ranking paperwork in
the half of the register where it matters.

**Which department the award belongs to is figure 6, and what procedure was actually run is
figure 7.** This plate carried five chart blocks until a reader said it was crowded; two is
the ceiling here.

**What this cannot show.** Whether a single bid was avoidable. One responsive offer to a
genuinely open solicitation is legal, common, and not by itself a defect, and nothing here
measures how many firms saw the notice and chose not to answer. It also cannot say the label
is wrong on its own terms: an order placed under a competed vehicle *was* competed, once, at
the vehicle.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import offers, plate                                                     # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "5-offers.svg")
RED, AMBER, GREEN, BLUE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8"
BANDS = [("1", "1 offer", RED), ("2", "2", AMBER), ("3-5", "3 to 5", GREEN),
         ("6+", "6 or more", BLUE)]


def main():
    S = offers.stats()
    c, counted, total = S["c"], S["counted"], S["total"]
    cells = c["cells"]
    W, H = 1240, 748
    s = plate.open_svg(
        W, H, "A third of awards are labelled competed and drew exactly one bid",
        subtitle=f"The two measures of competition that sit on the same row: the procedure "
                 f"the officer recorded, and how many firms answered. On "
                 f"{counted:,} FY2016 awards that record a bid count.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone ranking agencies on a competition rate, or screening awards on the "
            "competed label",
        decide="whether to measure competition with extent_competed or with the bid count "
               "on the same row",
        wrong="the label splits the bid count the same way in both directions, or one bid "
              "is rare inside the competed label")
    s += fr

    # ---- panel A: the cross-tab, drawn to area -----------------------------
    AX, AY, AW, AH = 64, y0 + 62, 540, 330
    nC, nU = cells["C|1"] + cells["C|2+"], cells["U|1"] + cells["U|2+"]
    wC = AW * nC / (nC + nU)
    s.append(txt(AX - 36, AY - 36, "the label against the count", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(AX - 36, AY - 19, "block area is awards; width is how many carry each "
                                   "label", size=10, fill=MUTED))
    for x0, wd, one, two, lab, sh in (
            (AX, wC, cells["C|1"], cells["C|2+"], "labelled competed", nC / counted),
            (AX + wC + 6, AW - wC - 6, cells["U|1"], cells["U|2+"], "labelled NOT competed",
             nU / counted)):
        tot = one + two
        h1 = AH * one / tot
        s.append(f'<rect x="{x0:.1f}" y="{AY:.1f}" width="{wd:.1f}" height="{h1:.1f}" '
                 f'fill="{RED}" fill-opacity="0.80"/>')
        s.append(f'<rect x="{x0:.1f}" y="{AY+h1:.1f}" width="{wd:.1f}" '
                 f'height="{AH-h1:.1f}" fill="{BLUE}" fill-opacity="0.55"/>')
        share = one / tot
        fmt = f"{share:.1%}" if share > 0.995 or share < 0.005 else f"{share:.0%}"
        s.append(txt(x0 + wd / 2, AY + h1 / 2 + 4, f"one bid {fmt}", size=12,
                     fill="#ffffff", anchor="middle", weight="700"))
        if AH - h1 > 26:
            s.append(txt(x0 + wd / 2, AY + h1 + (AH - h1) / 2 + 4,
                         f"more than one {1-one/tot:.0%}", size=12, fill="#ffffff",
                         anchor="middle", weight="700"))
        s.append(txt(x0 + wd / 2, AY + AH + 18, lab, size=10, fill=INK, anchor="middle"))
        s.append(txt(x0 + wd / 2, AY + AH + 32, f"{sh:.1%} of awards", size=9.5,
                     fill=MUTED, anchor="middle"))
    s += halo(AX, AY + AH + 56, f"the red block on the left is {cells['C|1']:,} awards, "
              f"{cells['C|1']/total:.0%} of the file", size=10.5, fill=RED, weight="700")
    s += halo(AX, AY + AH + 70, "the label is a real signal only when it says NOT competed",
              size=10.5, fill=INK2)

    # ---- panel B: the bid count itself -------------------------------------
    BX, BY, BW = 676, AY, 500
    band = c["band"]
    nb = sum(band.values())
    s.append(txt(BX - 30, AY - 36, "and the count on its own", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(BX - 30, AY - 19, f"how many offers the {nb:,} scored awards drew",
                 size=10, fill=MUTED))
    BH = 64
    x0 = BX
    for key, lab, col in BANDS:
        v = band.get(key, 0)
        wd = BW * v / nb
        s.append(f'<rect x="{x0:.1f}" y="{AY:.1f}" width="{max(wd-2,1):.1f}" '
                 f'height="{BH:.1f}" fill="{col}" fill-opacity="0.85"/>')
        s.append(txt(x0 + wd / 2, AY + BH + 18, lab, size=10, fill=INK, anchor="middle"))
        s.append(txt(x0 + wd / 2, AY + BH + 33, f"{v/nb:.1%}", size=11, fill=col,
                     anchor="middle", weight="700"))
        x0 += wd
    s += halo(BX, AY + BH + 62, "a single bid is the modal outcome of federal competition",
              size=10.5, fill=INK2, weight="700")
    s += halo(BX, AY + BH + 76, f"and {(band.get('1',0)+band.get('2',0))/nb:.0%} of awards "
              f"drew two firms or fewer", size=10.5, fill=INK2)
    # the same awards, by what they cost, because awards and dollars are different bases
    dY = AY + 206
    d1, dall = c["dollars"]["1"], S["dollars"]
    s.append(txt(BX - 30, dY - 14, "the same split counted in dollars, not awards",
                 size=11.5, fill=INK, weight="600"))
    w1 = BW * d1 / dall
    s.append(f'<rect x="{BX:.1f}" y="{dY+6:.1f}" width="{w1:.1f}" height="{BH:.1f}" '
             f'fill="{RED}" fill-opacity="0.80"/>')
    s.append(f'<rect x="{BX+w1+2:.1f}" y="{dY+6:.1f}" width="{BW-w1-2:.1f}" '
             f'height="{BH:.1f}" fill="{BLUE}" fill-opacity="0.55"/>')
    s.append(txt(BX + w1 / 2, dY + 6 + BH / 2 + 4, f"{d1/dall:.0%} of the dollars",
                 size=12, fill="#ffffff", anchor="middle", weight="700"))
    s.append(txt(BX + w1 + 2 + (BW - w1) / 2, dY + 6 + BH / 2 + 4,
                 f"{1-d1/dall:.0%}", size=12, fill="#ffffff", anchor="middle",
                 weight="700"))
    s.append(txt(BX, dY + BH + 38, f"single-bid awards are {band.get('1',0)/nb:.0%} of the "
                                   f"awards and {d1/dall:.0%} of the "
                                   f"${dall/1e9:.0f}bn obligated,", size=10.5, fill=INK2))
    s.append(txt(BX, dY + BH + 52, "because a single-bid award is a smaller award",
                 size=10.5, fill=INK2))

    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2016, eleven civilian "
        "departments, 554,171 awards. Rates use the 550,977 with a usable bid count, where "
        "a recorded 0 offers is not a count. CAVEAT: a single bid is legal and often "
        "unavoidable, and nothing here identifies an award as improperly competed. These "
        "eleven civilian departments are 8.5% of federal contract awards; Defense (68.6%) "
        "is absent, so this is not federal procurement as a whole.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=186, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=186, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    competed and one bid {cells['C|1']:,} = {cells['C|1']/total:.1%} of awards, "
          f"{cells['C|1']/(cells['C|1']+cells['C|2+']):.1%} of the competed label")
    print(f"    uncompeted and one bid {cells['U|1']/(cells['U|1']+cells['U|2+']):.1%}")
    print(f"    bands " + "  ".join(f"{k}:{c['band'].get(k,0)/nb:.1%}" for k, _, _ in BANDS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
