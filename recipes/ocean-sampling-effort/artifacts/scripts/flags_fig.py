#!/usr/bin/env python3
"""A fifth of this register is flagged on land. Removing it would delete the shore.

    python3 chart-15-flags.py

`statistics/qc` publishes OBIS's own error signature and nothing in the previous fourteen
figures had opened it. It reports **43.2M records flagged ON_LAND** against 229.7M, 44.0M
NO_MATCH, 8.5M deeper than the sea floor beneath them, and half a million coordinates outside
the possible range. Nineteen percent of a marine register flagged as being on land is the sort
of number that stops an analysis.

**It should not, because the flags are a habitat map.** ON_LAND is 52.7% of seabirds, 31.7% of
seagrasses, 21.6% of clams and 19.7% of red algae -- birds are counted from the shore, seagrass
grows in estuaries, and clams are dug out of a beach. DEPTH_EXCEEDS_BATH picks out the opposite
set: sea urchins 10.1%, kelp 9.7%, corals 7.3%, sea cucumbers 6.1%. Those are benthic animals on
rugged bottom, where a coarse bathymetry raster disagrees with the record by a few metres. The
two flags select almost disjoint groups, and neither selects anything at random.

**So excluding them does not clean the data, it deletes a coastline.** The routine first step --
drop the flagged rows and get on with it -- would have removed more than half of all seabird
records and a third of all seagrass records from a recipe whose seventh figure is about where
seagrass lives.

**And it changes nothing, which is the other half of the point.** Re-running figure 8's statistic
on the cleaned subset moves not one of the seven crossings: seagrasses 20 m, kelp 30 m, red algae
50 m, green algae 70 m, and sponges, bristle worms and ray-finned fish still never reach a tenth.
The share of records in the top 200 m goes from 88.0% to 87.6%. The flags land roughly in
proportion to where each group already is, so a within-bin composition ratio divides them out --
which is the same reason figure 8 worked at all.

**The filter was verified before it was trusted.** `flags=ON_LAND` returns 34.6M and
`exclude=ON_LAND` returns 195.1M against 229.7M unfiltered, so both are honoured. `flags=BANANA`
returns 0 rather than the total; `banana=ON_LAND` returns the unfiltered total. The first is what
a working filter does with a value it does not know, the second is what an ignored parameter
looks like, and four parameters in this API behave the second way.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "flags.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"


def main():
    d = json.load(open(os.path.join(HERE, "..", "data", "flags.json")))
    cls = d["classes"]
    for c in cls:
        n = max(c["records"], 1)
        c["land"] = c["flags"]["ON_LAND"] / n
        c["deep"] = c["flags"]["DEPTH_EXCEEDS_BATH"] / n

    W, H = 1200, 850
    s = plate.open_svg(W, H, "A fifth of this register is flagged on land. "
                             "Removing it would delete the shore.")
    fr, _ = plate.frame(W, 62,
                        who="anyone about to exclude flagged records before analysing OBIS",
                        decide="whether a quality flag marks an error or a habitat",
                        wrong="dropping the flagged rows moves any finding in this recipe")
    s += fr

    # ---- left: the two flags against each other. If they were noise they would cluster.
    AX, AY, AH, AW = 28, 262, 380, 470
    s.append(txt(AX, AY - 56, "the two big flags select opposite animals", size=12.5,
                 fill=INK, weight="600"))
    s.append(txt(AX, AY - 40, "share of each class's records carrying each flag",
                 size=10.5, fill=MUTED))
    x0, pw = AX + 52, AW - 92
    px = lambda f: x0 + pw * (f / .60)
    py = lambda f: AY + AH - AH * (f / .12)
    for f in (0, .15, .30, .45, .60):
        s.append(f'<line x1="{px(f):.1f}" y1="{AY:.1f}" x2="{px(f):.1f}" y2="{AY+AH:.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(px(f), AY + AH + 16, f"{f*100:.0f}%", size=9, fill=MUTED, anchor="middle"))
    for f in (0, .03, .06, .09, .12):
        s.append(f'<line x1="{x0:.1f}" y1="{py(f):.1f}" x2="{px(.60):.1f}" y2="{py(f):.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(x0 - 7, py(f) + 3, f"{f*100:.0f}%", size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, AY + AH + 32, "flagged ON_LAND", size=9.5, fill=MUTED))
    s.append(f'<text transform="translate({AX+10},{AY+AH/2}) rotate(-90)" font-size="9.5" '
             f'fill="{MUTED}" text-anchor="middle">flagged DEPTH_EXCEEDS_BATH</text>')
    placed = []
    for c in sorted(cls, key=lambda c: -(c["land"] + c["deep"])):
        cx, cy = px(c["land"]), py(c["deep"])
        col = RED if c["land"] > .18 else (BLUE if c["deep"] > .04 else SLATE)
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.4" fill="{col}" '
                 f'fill-opacity="0.8"/>')
        right = c["land"] < .40
        # the bottom-left corner holds six classes inside three points of each other, so
        # labels there are pushed UP; pushing down walks them through the axis title
        step = -11 if cy > AY + AH * .72 else 11
        ly = cy + 3.5
        while any(abs(ly - q) < 11 and abs(cx - qx) < 120 for qx, q in placed):
            ly += step
        ly = min(max(ly, AY + 10), AY + AH - 3)
        placed.append((cx, ly))
        if abs(ly - (cy + 3.5)) > 13:
            s.append(f'<line x1="{cx + (6 if right else -6):.1f}" y1="{cy:.1f}" '
                     f'x2="{cx + (10 if right else -10):.1f}" y2="{ly-3:.1f}" '
                     f'stroke="{col}" stroke-width="0.8" stroke-opacity="0.55"/>')
        s += halo(cx + (10 if right else -10), ly, c["common"], size=9.5, fill=col,
                  anchor="start" if right else "end")
    lx, ly = px(.30), AY + 20
    for lab, col in (("over 18% on land — the shore", RED),
                     ("over 4% below the sea floor — rugged bottom", BLUE),
                     ("neither", SLATE)):
        s.append(f'<circle cx="{lx+5:.1f}" cy="{ly-3.5:.1f}" r="4.4" fill="{col}" '
                 f'fill-opacity="0.8"/>')
        s.append(txt(lx + 16, ly, lab, size=9.5, fill=INK2))
        ly += 14
    s += wrap(AX, AY + AH + 54,
              "Nothing sits in the top right. A class is either counted from the shore or found "
              "on broken ground, and almost never both. Seabirds are half on land because that "
              "is where people stand to count them; sea urchins are a tenth below the sea floor "
              "because the bathymetry raster is coarser than the rock they live on. Neither is "
              "a mistake in the record.",
              size=10.5, fill=INK2, chars=76)

    # ---- right: the null. A flat row of marks, because flat is the claim.
    BX, BY, BH, BW = 560, 262, 380, 470
    s.append(txt(BX, BY - 56, "and dropping them moves nothing", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(BX, BY - 40, "figure 8's crossing depth, re-measured with the flagged "
                              "records excluded", size=10.5, fill=MUTED))
    bx0, bpw = BX + 52, BW - 92
    ck = d["checks"]
    mxloss = max((1 - c["records_clean"] / max(c["records_raw"], 1)) for c in ck) or .01
    bpx = lambda f: bx0 + bpw * (f / (mxloss * 1.15))
    mid = BY + BH * 0.42
    s.append(f'<line x1="{bx0:.1f}" y1="{mid:.1f}" x2="{bx0+bpw:.1f}" y2="{mid:.1f}" '
             f'stroke="{INK2}" stroke-width="1.5"/>')
    for g_ in (0, .05, .10, .15, .20):
        if g_ > mxloss * 1.15:
            continue
        s.append(f'<line x1="{bpx(g_):.1f}" y1="{mid-60:.1f}" x2="{bpx(g_):.1f}" '
                 f'y2="{mid+60:.1f}" stroke="{GRID}"/>')
        s.append(txt(bpx(g_), mid + 78, f"{g_*100:.0f}%", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(BX, mid + 94, "share of the class's records removed by cleaning",
                 size=9.5, fill=MUTED))
    s.append(txt(bx0 - 8, mid + 3, "0", size=9, fill=MUTED, anchor="end"))
    s.append(f'<text transform="translate({BX+10},{mid}) rotate(-90)" font-size="9.5" '
             f'fill="{MUTED}" text-anchor="middle">change in the crossing depth, metres</text>')
    placed2 = []
    for c in sorted(ck, key=lambda c: -(1 - c["records_clean"] / max(c["records_raw"], 1))):
        loss = 1 - c["records_clean"] / max(c["records_raw"], 1)
        a, b = c["cross_raw"], c["cross_clean"]
        moved = (b - a) if (a is not None and b is not None) else 0
        cx, cy = bpx(loss), mid - moved * 4
        never = a is None
        col = SLATE if never else GREEN
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.6" fill="{col}" '
                 f'fill-opacity="0.85"/>')
        ly = cy - 9
        while any(abs(ly - q) < 12 for q in placed2):
            ly -= 12
        placed2.append(ly)
        lab = f"{c['common']} · {a} m" if not never else f"{c['common']} · never"
        s += halo(cx, ly, lab, size=9.5, fill=col, anchor="middle")
    ly2 = mid + 112
    for lab, col in (("has a crossing, unchanged", GREEN),
                     ("never reaches a tenth, before or after", SLATE)):
        s.append(f'<circle cx="{bx0+5:.1f}" cy="{ly2-3.5:.1f}" r="4.6" fill="{col}" '
                 f'fill-opacity="0.85"/>')
        s.append(txt(bx0 + 16, ly2, lab, size=9.5, fill=INK2))
        ly2 += 14
    s += wrap(BX, ly2 + 10,
              f"Every mark sits on the zero line. Cleaning removes up to "
              f"{mxloss*100:.0f}% of a class's records and moves not one of the seven crossings "
              f"— seagrasses 20 m, kelp 30 m, red algae 50 m, green algae 70 m, and the three "
              f"controls still never reach a tenth. The share of all records in the top 200 m "
              f"goes from {d['top200_raw']*100:.1f}% to {d['top200_clean']*100:.1f}%. The flags "
              f"fall roughly where each group already is, so a within-bin ratio divides them "
              f"out — the same reason figure 8 worked.",
              size=10.5, fill=INK2, chars=76)

    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"OBIS v3 statistics/qc and occurrence with flags/exclude, fetched 2026-09-19 "
              f"against {d['total']:,} records. statistics/qc and a filtered count disagree on "
              f"ON_LAND — 43,236,520 against 34,582,170 — because the qc table counts everything "
              f"ever ingested including rows dropped before indexing, while the filter counts "
              f"what a query returns; the filter count is used, being the population every other "
              f"figure drew from. Both parameters were verified: flags=BANANA returns 0 rather "
              f"than the total, and banana=ON_LAND returns the unfiltered total, which is what "
              f"four other parameters in this API do silently. Cleaning here means excluding "
              f"{d['clean_exclusions'].replace(',', ', ')}.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for c in sorted(cls, key=lambda c: -c["land"])[:5]:
        print(f"    {c['common']:<20}on land {c['land']:6.1%}   below the floor {c['deep']:5.1%}")
    print(f"    crossings unchanged: "
          f"{sum(1 for c in ck if c['cross_raw'] == c['cross_clean'])} of {len(ck)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
