#!/usr/bin/env python3
"""Taxonomy has two golden ages and two world wars in it.

    python3 chart-10-described.py

Figure 9 runs on the date carried by a record, which is when a specimen was collected.
`scientificNameAuthorship` carries when the species became known to science, and it is
populated for essentially every species row: 116,098 species across nineteen classes.

**The pooled curve is a history of expeditions and interruptions.** It starts from nothing and
jumps to 1,144 species in the 1755-59 bin, which is Linnaeus and the tenth edition of Systema
Naturae -- a naming system, not a voyage. It climbs through the nineteenth century of survey
ships and peaks at **4,320 species in 1905-09**, the tail of the Challenger era, whose fifty
volumes of reports came out between 1880 and 1895. Then it breaks twice: **1915-19 falls 30%
below what its neighbours imply and 1945-49 falls 31%**. Descriptions are done by a few hundred
specialists in a handful of institutions, and both wars closed them.

**The second golden age is the bigger one.** After 1950 the curve climbs again and reaches
**4,341 species in 2005-09**, above the Challenger peak. More marine species were described in
the 2000s than in any decade of the age of sail.

**The classes are on completely different clocks.** Seabirds have a median description year of
**1811** and 0.2% of their species described since 2000: that work finished before photography.
Bristle worms have a median of **1972** and 28.7% since 2000, and crabs and shrimp 1966 and
21.4%. Two centuries separate the midpoints, and the split is body size and charisma.

**It connects to figure 9 loosely, not tightly.** Rank correlation between a class's share
described since 2000 and the cost of its next hundred species is **-0.54** -- real, but with
loud exceptions. Sharks and rays are 22.3% post-2000 and still cost 6.7M records per hundred
species, because a shark is easy to notice and hard to find.

**Paging is load-bearing here.** The checklist caps at 10,000 rows, returns HTTP 500 above it,
and is sorted by record count descending. Taking only the first page would have put the
gastropod median at 1864 instead of 1911 and the crab median at 1903 instead of 1966 -- a bias
of half a century, in the direction of the story being told.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "taxonomy.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#7d8a96"
WAR = "#c9a294"                      # 2.01:1 on the grid track. The first try, #d9c4bd,
                                     # was 1.45:1 and plateaudit rejected it -- the same
                                     # defect as a bar drawn in the track colour.


def main():
    d = json.load(open(os.path.join(HERE, "..", "data", "described.json")))
    cl, B = d["classes"], d["bin"]
    # The 2025 bin spans 2025-2029 and only one year of it has happened, so it is not a fall
    # in taxonomy, it is a bin that has not finished. Drawn, it would put a cliff on the right
    # edge of all nineteen curves. Every bin kept here is fully elapsed as of the fetch date.
    LAST_FULL = 2024
    LO = 1750
    bins = [b for b in range(LO, LAST_FULL + 1, B) if b + B - 1 <= LAST_FULL]
    HI = bins[-1]
    agg = {b: 0 for b in bins}
    for v in cl.values():
        for k, n in v["hist"].items():
            if int(k) in agg:
                agg[int(k)] += n

    W, H = 1200, 1054
    s = plate.open_svg(W, H, "Taxonomy has two golden ages and two world wars in it.")
    fr, _ = plate.frame(W, 62,
                        who="anyone asking which marine groups are still being described",
                        decide="whether a class's taxonomy is finished or still open",
                        wrong="the recent rise is names being revised rather than species "
                              "being described")
    s += fr

    # ---- left: everything pooled, so the eras are one curve rather than nineteen
    AX, AY, AH, AW = 28, 250, 300, 470
    s.append(txt(AX, AY - 50, "marine species described, all nineteen classes pooled",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(AX, AY - 34, f"{sum(agg.values()):,} species, in {B}-year bins to {HI+B-1}",
                 size=10.5, fill=MUTED))
    x0, pw = AX + 44, AW - 62
    px = lambda y: x0 + pw * ((y - LO) / (HI - LO))
    mx = max(agg.values()) or 1
    py = lambda n: AY + AH - AH * (n / mx)
    for lo, hi in ((1914, 1918), (1939, 1945)):
        s.append(f'<rect x="{px(lo):.1f}" y="{AY:.1f}" width="{px(hi)-px(lo):.1f}" '
                 f'height="{AH:.1f}" fill="{WAR}"/>')
    for n in (0, 1000, 2000, 3000, 4000):
        s.append(f'<line x1="{x0:.1f}" y1="{py(n):.1f}" x2="{px(HI):.1f}" y2="{py(n):.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(x0 - 7, py(n) + 3, f"{n:,}" if n else "0", size=9, fill=MUTED,
                     anchor="end"))
    for y in range(1750, HI + 1, 50):
        s.append(txt(px(y), AY + AH + 16, str(y), size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, AY + AH + 32, "year the species was described", size=9.5, fill=MUTED))
    s.append(f'<text transform="translate({AX+10},{AY+AH/2}) rotate(-90)" font-size="9.5" '
             f'fill="{MUTED}" text-anchor="middle">species described in the bin</text>')
    pts = " ".join(("M" if i == 0 else "L") + f"{px(b):.1f},{py(agg[b]):.1f}"
                   for i, b in enumerate(bins))
    s.append(f'<path d="{pts}" fill="none" stroke="{BLUE}" stroke-width="2.1"/>')
    for b, col in ((1755, AMBER), (1905, BLUE), (2005, BLUE)):
        s.append(f'<circle cx="{px(b):.1f}" cy="{py(agg[b]):.1f}" r="4" fill="{col}"/>')
        s += halo(px(b), py(agg[b]) - 9, f"{agg[b]:,}", size=9, fill=col, anchor="middle")
    lx, ly = x0 + 8, AY + 16
    for lab, col, box in (("Linnaeus, Systema Naturae 1758", AMBER, False),
                          ("peak 1905–09, the Challenger reports", BLUE, False),
                          ("peak 2005–09, the larger of the two", BLUE, False),
                          ("the two world wars", WAR, True)):
        if box:
            s.append(f'<rect x="{lx:.1f}" y="{ly-8:.1f}" width="10" height="9" fill="{col}"/>')
        else:
            s.append(f'<circle cx="{lx+5:.1f}" cy="{ly-3.5:.1f}" r="4" fill="{col}"/>')
        s.append(txt(lx + 16, ly, lab, size=9.5, fill=INK2))
        ly += 14
    s += wrap(AX, AY + AH + 54,
              "1915–19 sits 30% below what its neighbours imply and 1945–49 sits 31% below. "
              "Description is done by a few hundred specialists in a handful of institutions, "
              "and both wars closed them. The recovery overshoots: more marine species were "
              "described in the 2000s than in any decade of the age of sail.",
              size=10.5, fill=INK2, chars=76)

    # ---- right: the same curve per class, ordered by when each class had its midpoint
    BX, BY, BW_ = 560, 250, 420
    s.append(txt(BX, BY - 50, "and which taxonomies are still open", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(BX, BY - 34, "each curve scaled to its own peak; ordered by the rate on the right",
                 size=10.5, fill=MUTED))
    # The number is new species per year per 1,000 already known, over the last complete
    # decade. The raw rate was tried first and discarded: it correlates with class size at
    # rho +0.96, so it says only that large classes contain more undescribed species. The
    # median description year was tried before that and is worse still -- it is a location on
    # the horizontal axis, which the curve already shows, so it spends the slot on nothing.
    def growth(v):
        h = {int(k): n for k, n in v["hist"].items()}
        return (h.get(2010, 0) + h.get(2015, 0)) / 10 / max(v["dated"], 1) * 1000
    rows = sorted(cl.values(), key=growth)
    rw = (BW_ - 40) / (len(bins) - 1)
    RH, STEP = 32, 28
    bpx = lambda i: BX + 150 + i * rw
    for i, v in enumerate(rows):
        y = BY + i * STEP
        h = {int(k): n for k, n in v["hist"].items()}
        vals = [h.get(b, 0) for b in bins]
        m = max(vals) or 1
        gr = growth(v)
        col = RED if gr < 3 else (GREEN if gr >= 8 else BLUE)
        p = [(bpx(k), y + RH - RH * (n / m) * 0.95) for k, n in enumerate(vals)]
        s.append(f'<path d="M{p[0][0]:.1f},{y+RH:.1f} '
                 + " ".join(f"L{a:.1f},{b2:.1f}" for a, b2 in p)
                 + f' L{p[-1][0]:.1f},{y+RH:.1f} Z" fill="{col}" fill-opacity="0.28"/>')
        s.append('<path d="' + " ".join(("M" if k == 0 else "L") + f"{a:.1f},{b2:.1f}"
                                        for k, (a, b2) in enumerate(p))
                 + f'" fill="none" stroke="{col}" stroke-width="1.5"/>')
        s.append(txt(BX + 142, y + RH - 1, v["common"], size=9.5, fill=INK2, anchor="end"))
        s += halo(bpx(len(bins) - 1) + 7, y + RH - 1, f"{gr:.1f}", size=9, fill=col)
    base = BY + len(rows) * STEP + RH
    # The decade the number is measured over, marked so the number can be checked against
    # the curve. Drawn as two rules, not a band: a fill light enough to sit behind nineteen
    # curves would be under the contrast floor, and the warm band already means "world war"
    # in the panel to the left.
    for wy in (2010, 2020):
        s.append(f'<line x1="{bpx((wy-LO)/B):.1f}" y1="{BY-8:.1f}" '
                 f'x2="{bpx((wy-LO)/B):.1f}" y2="{base-2:.1f}" stroke="{INK2}" '
                 f'stroke-width="1" stroke-opacity="0.45"/>')
    for y in range(1750, HI + 1, 50):
        s.append(txt(bpx((y - LO) / B), base + 4, str(y), size=9, fill=MUTED, anchor="middle"))
    s.append(txt(BX + 150, base + 20, "number is new species per year per 1,000 already "
                 "known, measured between the two rules", size=9, fill=MUTED))
    lx2, ly2 = BX, base + 40
    for lab, col in (("under 3 per 1,000 — closed", RED),
                     ("3 to 8", BLUE), ("8 and over — still open", GREEN)):
        s.append(f'<line x1="{lx2:.1f}" y1="{ly2-3.5:.1f}" x2="{lx2+14:.1f}" '
                 f'y2="{ly2-3.5:.1f}" stroke="{col}" stroke-width="2.4"/>')
        s.append(txt(lx2 + 20, ly2, lab, size=9.5, fill=INK2))
        lx2 += 175 if col != BLUE else 66
    s += wrap(BX, base + 62,
              "Bristle worms gain 11.9 species a year per thousand they already have and "
              "seabirds gain none at all. Sharks and rays are the surprise at 8.2, as open as "
              "the worms and sponges despite being large, conspicuous and only 1,164 species — "
              "so being noticed is not the same as being described. The raw count of new species "
              "would have ranked crabs first and said nothing: it tracks class size at rank "
              "correlation +0.96.",
              size=10.5, fill=INK2, chars=76)

    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              "OBIS v3 checklist, fetched 2026-09-18, year parsed from scientificNameAuthorship "
              "— the FIRST year in the string, which is the original description, so "
              "\"(Pallas, 1766)\" is 1766. Only taxonRank Species rows are counted, because a "
              "checklist also carries genera and the class itself with their own authorships. "
              "The checklist caps at 10,000 rows, 500s above that, and is sorted by record count "
              "descending, so it is paged with skip — from, offset and after are accepted and "
              "silently ignored. Page one alone would have given a gastropod median of 1864 "
              "against 1911, and a crab median of 1903 against 1966. Bins run to 2024: the "
              "2025–29 bin is one year old and is dropped rather than drawn as a fall.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for v in rows:
        print(f"    {v['common']:<20}median {v['median']}  since 2000 {v['since2000']:6.1%}  "
              f"n={v['dated']:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
