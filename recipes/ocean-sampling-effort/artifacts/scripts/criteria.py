#!/usr/bin/env python3
"""Criterion B is ruled out for four in five Critically Endangered species.

    python3 chart-13-criterionb.py

IUCN lists a species under any one of five criteria, and the thresholds are published. Four of
them -- A population reduction, C small declining population, D very small population, E modelled
extinction probability -- are counts of mature individuals or their rate of change. A
presence-only register with uncontrolled effort cannot supply any of them. **B, geographic
range, is the only criterion with a spatial threshold and therefore the only one this data can
be compared against at all.**

**And the comparison only runs one way.** Occupied geohash cells at precision 5 measure about
23 km2, larger than the 2 x 2 km grid IUCN recommends for area of occupancy, so every occupied
cell holds at least one occupied 4 km2 square and `cells x 4` is a strict lower bound. A lower
bound above the B2 threshold **rules the criterion out**. A lower bound below it proves nothing,
because nobody may have looked.

**Ruled out for 81% of CR, 34% of EN and 20% of VU.** The gradient is mostly the thresholds
themselves: B2 for CR is under 10 km2, which is two and a half occupied cells, and almost any
species with a handful of scattered records exceeds it. Those listings rest on A, C, D or E, and
this register cannot see which.

**The remainder do not rescue it.** Of the 48 CR species whose measured area stays under the
threshold, the median record count is **one**. Their small measured range is ignorance, not
endemism, and the right-hand panel is that check: the species where criterion B survives are
precisely the ones nobody has looked for. Between the two panels there is no Critically
Endangered species in this sample whose listing OBIS can explain.

**A cap worth recording.** `occurrence/grid` returns at most 100,000 features. One species hit
it exactly -- Diomedea exulans, the wandering albatross, on 159,138 records spread over the
Southern Ocean. Because every claim here is "at least this large", a truncated count only makes
the bound more conservative and changes no conclusion.
"""
import json, math, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "criteria.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
CAT = [("CR", "Critically Endangered", RED), ("EN", "Endangered", AMBER),
       ("VU", "Vulnerable", BLUE)]


def sup(x, y, mant, exp, *, size, fill, anchor="start"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}">{mant}<tspan font-size="{size*0.72:.1f}" '
            f'dy="{-size*0.40:.1f}">{exp}</tspan></text>')


def main():
    d = json.load(open(os.path.join(HERE, "..", "data", "criterionb.json")))
    sp, B2 = d["species"], d["b2"]

    W, H = 1200, 800
    s = plate.open_svg(W, H, "Criterion B is ruled out for four in five Critically "
                             "Endangered species.")
    fr, _ = plate.frame(W, 62,
                        who="anyone hoping to reconstruct or audit a Red List assessment "
                            "from occurrence data",
                        decide="whether this register can say why a species is listed",
                        wrong="the species under the threshold have small ranges rather than "
                              "few records")
    s += fr

    # ---- left: every species against ITS OWN threshold, so one rule serves all three rows.
    # The first version plotted absolute km2 with a separate faint vertical line per row --
    # three different boundaries, each drawn as the lightest thing on the page, for a figure
    # whose entire claim is "which side of the boundary is this on". Dividing by each
    # category's own B2 threshold puts every species on one axis with one line at 1.0, and
    # the ruled-out share can then sit on its own row instead of floating in a column.
    AX, AY, AH, AW = 28, 262, 320, 470
    s.append(txt(AX, AY - 56, "area of occupancy against that species' own B2 threshold",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(AX, AY - 40, "one mark per species; rows are categories, not a sequence",
                 size=10.5, fill=MUTED))
    x0, pw = AX + 96, AW - 126
    LO, HI = -3.2, 5.0
    px = lambda r: x0 + pw * ((min(max(math.log10(max(r, 1e-6)), LO), HI) - LO) / (HI - LO))
    rows_h = (AH - 54) / len(CAT)
    thr_x = px(1.0)
    s.append(f'<rect x="{thr_x:.1f}" y="{AY-14:.1f}" width="{px(10**HI)-thr_x:.1f}" '
             f'height="{AH-34:.1f}" fill="{RED}" fill-opacity="0.055"/>')
    s.append(f'<line x1="{thr_x:.1f}" y1="{AY-14:.1f}" x2="{thr_x:.1f}" '
             f'y2="{AY+AH-48:.1f}" stroke="{INK}" stroke-width="2"/>')
    # NOT an arrow. U+2192 renders as an empty box under cairosvg -- this recipe has shipped
    # that once already and plateaudit checks for it. Drawn as a path instead.
    s += halo(thr_x + 22, AY - 20, "ruled out from here", size=9.5, fill=INK, weight="700")
    s.append(f'<path d="M{thr_x+4:.1f},{AY-23.5:.1f} L{thr_x+16:.1f},{AY-23.5:.1f} '
             f'M{thr_x+12:.1f},{AY-27:.1f} L{thr_x+16:.1f},{AY-23.5:.1f} '
             f'L{thr_x+12:.1f},{AY-20:.1f}" fill="none" stroke="{INK}" stroke-width="1.4"/>')
    for e in (-3, -2, -1, 0, 1, 2, 3, 4, 5):
        if e:
            s.append(f'<line x1="{px(10**e):.1f}" y1="{AY-14:.1f}" x2="{px(10**e):.1f}" '
                     f'y2="{AY+AH-48:.1f}" stroke="{GRID}"/>')
        s.append(sup(px(10 ** e), AY + AH - 32, "10", str(e), size=9, fill=MUTED,
                     anchor="middle"))
    s.append(txt(AX, AY + AH - 14, "multiples of its category's own B2 threshold",
                 size=9.5, fill=MUTED))
    for i, (c, name, col) in enumerate(CAT):
        v = [x for x in sp if x["category"] == c]
        y = AY + i * rows_h + rows_h / 2 - 16
        over = sum(1 for x in v if x["over_b2"])
        for j, x in enumerate(v):
            s.append(f'<circle cx="{px(x["aoo_min_km2"] / B2[c]):.1f}" '
                     f'cy="{y + ((j % 7) - 3) * 3.4:.1f}" r="2.2" fill="{col}" '
                     f'fill-opacity="0.5"/>')
        s.append(txt(AX, y - 4, name, size=10.5, fill=col, weight="600"))
        s.append(txt(AX, y + 9, f"n={len(v)}, B2 < {B2[c]:,} km²", size=8.5, fill=MUTED))
        s += halo(px(10 ** HI) + 8, y + 4, f"{over/len(v):.0%}", size=13, fill=col,
                  weight="700")
        s.append(txt(px(10 ** HI) + 8, y + 17, "ruled out", size=8.5, fill=MUTED))
    s += wrap(AX, AY + AH + 10,
              "Everything right of the rule has a measured area already larger than the "
              "threshold, so criterion B2 cannot be what listed it and the listing rests on A, "
              "C, D or E — none of which a presence-only register can see. Dividing by each "
              "category's own threshold is what lets the three rows share one boundary: CR's "
              "is 10 km², two and a half occupied cells, so almost any scattered species "
              "clears it.",
              size=10.5, fill=INK2, chars=76)

    # ---- right: the species B2 could still explain, and what they are made of
    BX, BY, BH, BW = 560, 256, 330, 470
    s.append(txt(BX, BY - 56, "and the ones it could still explain have no data",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(BX, BY - 40, "records held by species under and over their own B2 threshold",
                 size=10.5, fill=MUTED))
    bx0, bpw = BX + 108, BW - 152
    LOR, HIR = -0.2, 6.2
    bpx = lambda v: bx0 + bpw * ((min(max(math.log10(max(v, 1)), LOR), HIR) - LOR) / (HIR - LOR))
    rh = (BH - 46) / len(CAT)
    for e in range(0, 7, 2):
        s.append(f'<line x1="{bpx(10**e):.1f}" y1="{BY-6:.1f}" x2="{bpx(10**e):.1f}" '
                 f'y2="{BY+BH-46:.1f}" stroke="{GRID}"/>')
        s.append(sup(bpx(10 ** e), BY + BH - 30, "10", str(e), size=9, fill=MUTED,
                     anchor="middle"))
    s.append(txt(BX, BY + BH - 14, "records the species holds in the register", size=9.5,
                 fill=MUTED))
    for i, (c, name, col) in enumerate(CAT):
        y = BY + i * rh + rh / 2 - 12
        under = [x for x in sp if x["category"] == c and not x["over_b2"]]
        over = [x for x in sp if x["category"] == c and x["over_b2"]]
        s.append(txt(BX, y - 8, c, size=10.5, fill=col, weight="600"))
        for grp, dy, fill, lab in ((under, -9, col, "B2 still possible"),
                                   (over, 11, None, "B2 ruled out")):
            if not grp:
                continue
            m = st.median([x["records"] for x in grp])
            s.append(f'<line x1="{bpx(min(x["records"] for x in grp)):.1f}" y1="{y+dy:.1f}" '
                     f'x2="{bpx(max(x["records"] for x in grp)):.1f}" y2="{y+dy:.1f}" '
                     f'stroke="{col}" stroke-width="1" stroke-opacity="0.4"/>')
            if fill:
                s.append(f'<circle cx="{bpx(m):.1f}" cy="{y+dy:.1f}" r="5" fill="{col}"/>')
            else:
                s.append(f'<circle cx="{bpx(m):.1f}" cy="{y+dy:.1f}" r="5" fill="none" '
                         f'stroke="{col}" stroke-width="1.8"/>')
            s += halo(bpx(m) + 10, y + dy + 3, f"median {m:,.0f}  (n={len(grp)})", size=9,
                      fill=col)
    ly = BY + BH - 46 + 42
    s.append(f'<circle cx="{bx0+5:.1f}" cy="{ly-3.5:.1f}" r="5" fill="{INK2}"/>')
    s.append(txt(bx0 + 16, ly, "B2 still possible", size=9.5, fill=INK2))
    s.append(f'<circle cx="{bx0+145:.1f}" cy="{ly-3.5:.1f}" r="5" fill="none" stroke="{INK2}" '
             f'stroke-width="1.8"/>')
    s.append(txt(bx0 + 156, ly, "B2 ruled out", size=9.5, fill=INK2))
    s += wrap(BX, ly + 22,
              "Of the 48 Critically Endangered species whose measured area stays under the "
              "threshold, the median record count is one. Their small range is ignorance, not "
              "endemism. Between the two panels there is no Critically Endangered species here "
              "whose listing this register can explain: either the range is already too large "
              "for B2, or there is nothing to measure.",
              size=10.5, fill=INK2, chars=76)

    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              "OBIS v3 occurrence/grid precision 5 and checklist/redlist, fetched 2026-09-19. "
              "Thresholds from IUCN Red List Categories and Criteria v3.1, second edition "
              "(portals.iucn.org, RL-2001-001-2nd.pdf). B is never satisfied by area alone: it "
              "also requires at least two of severe fragmentation or few locations, continuing "
              "decline, and extreme fluctuations — none readable from presence-only data — so "
              "this register can rule a species OUT of criterion B and can never rule one in. "
              "occurrence/grid caps at 100,000 features; one species reached it, and since every "
              "claim is a lower bound a truncated count only makes it more conservative.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for c, name, _ in CAT:
        v = [x for x in sp if x["category"] == c]
        u = [x for x in v if not x["over_b2"]]
        print(f"    {c}  n={len(v):<4} ruled out {sum(1 for x in v if x['over_b2'])/len(v):.0%}"
              f"   still possible n={len(u)}, median records "
              f"{st.median([x['records'] for x in u]):,.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
