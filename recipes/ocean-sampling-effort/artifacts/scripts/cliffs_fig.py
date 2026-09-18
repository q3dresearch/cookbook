#!/usr/bin/env python3
"""Light is the only cliff this register can prove.

    python3 chart-8-cliffs.py

Figure 7 established that a taxon's recorded depth is largely its sampling gear. Composition
survives that, because every taxon in a depth bin was reached by the same cruises: the share of
a bin's records belonging to a group cancels the effort that produced the bin.

**The cliff is real and it is sharp.** Benthic photosynthesisers must attach to the bottom and
be lit, and they vanish within tens of metres. Measured as a share of each bin's records and
scaled to each group's own peak, seagrasses fall under a tenth of peak by **20 m**, kelp by
**30 m**, red and green algae by **50 m**. Over the same range bristle worms, sponges and fish
never fall below half. This is not the cruises running out: 14.9M records sit in 50-100 m, from
1,189 datasets.

**The ordering is the mechanism.** Seagrass is the shallowest and is a flowering plant needing
soft lit sediment; red and green algae run twice as deep, which is what a group that includes
low-light crustose corallines should do. Stony corals are the designed intermediate -- they hold
photosynthetic symbionts in the shallows and lose them in the deep-water species -- and they
give exactly a partial cliff: under half of peak by 50 m, never under a tenth at all.

**What the right panel is for.** The same method fails below 4,000 m. A composition ratio only
cancels effort if the bin is many cruises: shallow bands run to 2,665 datasets with the largest
at 9-12%, while 5,000-6,000 m is **46.6% one cruise** and below 6,000 m is **52.8%**. The
carbonate compensation depth was the other cliff worth hunting -- calcite dissolves below about
4,500 m, so calcifiers should drop out -- and forams do fall from 2.04% of the 3-4 km band to
0.39% of the 4-5 km band. That is the right size in the right place and it cannot be claimed:
sea cucumbers hold 26.7% of the 4-5 km band on their own. The test is blocked, not negative.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "cliffs.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#7d8a96"
KIND = {"photo": GREEN, "mixed": AMBER, "control": SLATE}


def sup(x, y, mant, exp, *, size, fill, anchor="start"):
    """10 with a raised exponent, built from a tspan rather than a Unicode superscript."""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}">{mant}<tspan font-size="{size*0.72:.1f}" '
            f'dy="{-size*0.40:.1f}">{exp}</tspan></text>')


def main():
    d = json.load(open(os.path.join(HERE, "..", "data", "cliffs.json")))
    G = {x["from"]: x["records"] for x in d["global"]}
    edges = sorted(G)[:21]                                  # 0..200 m, the 10 m bins

    rows = []
    for sci, v in d["taxa"].items():
        t = {x["from"]: x["records"] for x in v["depth"]}
        comp = [(t.get(e, 0) / G[e] if G[e] else 0) for e in edges]
        # Baseline is the group's composition over 0-20 m, not its single best bin. Peak
        # normalisation puts the reference on whichever bin happened to be noisiest, which
        # made three flat controls zigzag between 20% and 100% and read as random. The top
        # two bins carry 64.1M records between them and every group here is benthic and
        # present in them, so the ratio is stable and means "share of its own shallow
        # prominence retained".
        base = (sum(t.get(e, 0) for e in edges[:2])
                / sum(G[e] for e in edges[:2])) or 1e-12
        rel = [c / base for c in comp]
        tenth = next((edges[i] for i in range(len(rel)) if all(r < .1 for r in rel[i:])), None)
        half = next((edges[i] for i in range(len(rel)) if all(r < .5 for r in rel[i:])), None)
        rows.append({"sci": sci, **v, "rel": rel, "tenth": tenth, "half": half})
    rows.sort(key=lambda r: (r["tenth"] is None, r["tenth"] or 999, r["half"] or 999))

    W, H = 1200, 968
    s = plate.open_svg(W, H, "Light is the only cliff this register can prove.")
    fr, _ = plate.frame(W, 62,
                        who="anyone about to read a community claim off a depth slice",
                        decide="whether a depth band's mix is biology or one ship's itinerary",
                        wrong="the deep bands keep their composition once the largest dataset is dropped")
    s += fr

    # ---- left: composition against depth, each group scaled to its own peak
    AX, AY, AH, AW = 28, 250, 380, 470
    s.append(txt(AX, AY - 50, "what share of each depth bin belongs to each group",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(AX, AY - 34, "ratio to the same group's share of the top 20 m, log scale",
                 size=10.5, fill=MUTED))
    x0, pw = AX + 46, AW - 74
    px = lambda m: x0 + pw * (m / 200)
    LO, HI = 3e-4, 6.0
    lg = lambda f: math.log10(min(max(f, LO), HI))
    py = lambda f: AY + AH - AH * ((lg(f) - lg(LO)) / (lg(HI) - lg(LO)))
    for m in (0, 50, 100, 150, 200):
        s.append(f'<line x1="{px(m):.1f}" y1="{AY:.1f}" x2="{px(m):.1f}" y2="{AY+AH:.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(px(m), AY + AH + 16, f"{m}", size=9, fill=MUTED, anchor="middle"))
    for f, e in ((1.0, "0"), (.1, "-1"), (.01, "-2"), (.001, "-3")):
        s.append(f'<line x1="{x0:.1f}" y1="{py(f):.1f}" x2="{px(200):.1f}" y2="{py(f):.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(sup(x0 - 7, py(f) + 3, "10", e, size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, AY + AH + 32, "metres below the surface", size=9.5, fill=MUTED))
    s.append(f'<text transform="translate({AX+12},{AY+AH/2}) rotate(-90)" font-size="9.5" '
             f'fill="{MUTED}" text-anchor="middle">its share of this bin '
             f'&#247; its share of 0-20 m</text>')
    placed = []
    for r in rows:
        col = KIND[r["kind"]]
        pts = " ".join(("M" if i == 0 else "L") + f"{px(e):.1f},{py(r['rel'][i]):.1f}"
                       for i, e in enumerate(edges))
        s.append(f'<path d="{pts}" fill="none" stroke="{col}" stroke-width="1.9" '
                 f'stroke-opacity="{0.95 if r["kind"] != "control" else 0.55}"/>')
        # the crossing itself gets a mark; it is the quantity the panel is about
        if r["tenth"] is not None:
            s.append(f'<circle cx="{px(r["tenth"]):.1f}" cy="{py(.1):.1f}" r="3.6" fill="{col}"/>')
        # label at the right edge for the flat lines, at the cliff for the steep ones
        if r["tenth"] is None:
            ly = py(r["rel"][-1])
            while any(abs(ly - q) < 12 for q in placed):
                ly -= 12
            placed.append(ly)
            s += halo(px(200) + 6, ly + 3, r["common"], size=9.5, fill=col)
        else:
            # four cliffs land inside 50 m of each other; stack their labels upward from
            # the crossing rather than writing them all on the same line
            ly = py(.1) - 9
            while any(abs(ly - q) < 12 for q in placed):
                ly -= 12
            placed.append(ly)
            s += halo(px(r["tenth"]) + 7, ly, f"{r['common']} · {r['tenth']} m",
                      size=9.5, fill=col)
    # the bottom-left quarter is the one empty region: every line is still near 1 across
    # the first 50 m, so a legend there covers nothing
    lx, ly = x0 + 10, py(.02)
    for lab, col in (("needs light to live", GREEN), ("symbionts in the shallows only", AMBER),
                     ("does not photosynthesise", SLATE)):
        s.append(f'<line x1="{lx:.1f}" y1="{ly-3.5:.1f}" x2="{lx+16:.1f}" y2="{ly-3.5:.1f}" '
                 f'stroke="{col}" stroke-width="2.4"/>')
        s.append(txt(lx + 22, ly, lab, size=9.5, fill=INK2))
        ly += 14
    s.append(f'<circle cx="{lx+8:.1f}" cy="{ly-3.5:.1f}" r="3.6" fill="{INK2}"/>')
    s.append(sup(lx + 22, ly, "crosses 10", "-1", size=9.5, fill=INK2))
    s += wrap(AX, AY + AH + 54,
              "Every line starts at 1.0 by construction. The photosynthesisers cross 0.1 within "
              "70 m and bottom out between 0.00043 and 0.0024 — three decades down. The controls "
              "never leave the 0.1 to 1.0 decade at any depth on this panel. Stony corals are the "
              "intermediate the panel was built to contain, with a floor of 0.092, because reef "
              "corals carry photosynthetic symbionts and deep-water corals do not.",
              size=10.5, fill=INK2, chars=76)

    # ---- right: where a composition ratio is a measurement at all
    BX, BY, BH, BW = 560, 250, 380, 470
    s.append(txt(BX, BY - 50, "and where that ratio stops meaning anything",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(BX, BY - 34, "largest dataset's share of each depth band; area is records in the band",
                 size=10.5, fill=MUTED))
    bx0, bpw = BX + 54, BW - 82
    lx_ = lambda m: bx0 + bpw * (math.log10(max(m, 10) / 10) / math.log10(11000 / 10))
    by = lambda f: BY + BH - BH * (f / .60)
    for m, lab in ((10, "10 m"), (100, "100"), (1000, "1,000"), (10000, "10,000")):
        s.append(f'<line x1="{lx_(m):.1f}" y1="{BY:.1f}" x2="{lx_(m):.1f}" y2="{BY+BH:.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(lx_(m), BY + BH + 16, lab, size=9, fill=MUTED, anchor="middle"))
    for f in (0, .20, .40, .60):
        s.append(f'<line x1="{bx0:.1f}" y1="{by(f):.1f}" x2="{lx_(11000):.1f}" y2="{by(f):.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(bx0 - 7, by(f) + 3, f"{f*100:.0f}%", size=9, fill=MUTED, anchor="end"))
    s.append(txt(BX, BY + BH + 32, "depth band, log scale", size=9.5, fill=MUTED))
    s.append(f'<text transform="translate({BX+10},{BY+BH/2}) rotate(-90)" font-size="9.5" '
             f'fill="{MUTED}" text-anchor="middle">biggest single dataset\'s share '
             f'of the band</text>')
    mxrec = max(b["records"] for b in d["bands"])
    pts = []
    for b in d["bands"]:
        mid = (b["lo"] + b["hi"]) / 2
        cx, cy = lx_(mid), by(b["top_share"] or 0)
        pts.append((cx, cy))
    s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{c:.1f}"
                                    for i, (a, c) in enumerate(pts))
             + f'" fill="none" stroke="{MUTED}" stroke-width="1.2" stroke-opacity="0.5"/>')
    for b, (cx, cy) in zip(d["bands"], pts):
        sh = b["top_share"] or 0
        rad = 4 + 15 * (b["records"] / mxrec) ** .5
        col = RED if sh >= .40 else (AMBER if sh >= .25 else GREEN)
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}" fill="{col}" '
                 f'fill-opacity="0.32" stroke="{col}" stroke-width="1.4"/>')
    for b, (cx, cy) in zip(d["bands"], pts):
        if b["lo"] in (0, 50, 5000, 6000):
            s += halo(cx, cy - (4 + 15 * (b["records"] / mxrec) ** .5) - 6,
                      f"{b['lo']:,}–{b['hi']:,} m", size=9, fill=INK2, anchor="middle")
    lx2, ly2 = bx0 + 12, BY + 16
    for lab, col in (("under 25% — a share here is a measurement", GREEN),
                     ("25–40% — one contributor is steering it", AMBER),
                     ("40% and over — not a measurement", RED)):
        s.append(f'<circle cx="{lx2+6:.1f}" cy="{ly2-3.5:.1f}" r="5" fill="{col}" '
                 f'fill-opacity="0.32" stroke="{col}" stroke-width="1.4"/>')
        s.append(txt(lx2 + 18, ly2, lab, size=9.5, fill=INK2))
        ly2 += 14
    kx, ky = lx_(11000) - 96, BY + BH - 30
    s.append(txt(kx, ky - 34, "records in the band", size=9, fill=MUTED))
    for rec, dx in ((max(b["records"] for b in d["bands"]), 0), (2_000_000, 52)):
        rr = 4 + 15 * (rec / mxrec) ** .5
        s.append(f'<circle cx="{kx+dx+19:.1f}" cy="{ky-rr:.1f}" r="{rr:.1f}" fill="none" '
                 f'stroke="{MUTED}" stroke-width="1.1"/>')
        lab = f"{rec/1e6:.0f}M" if rec >= 1e6 else f"{rec/1e3:.0f}k"
        s.append(txt(kx + dx + 19, ky + 12, lab, size=9, fill=MUTED, anchor="middle"))
    s += wrap(BX, BY + BH + 54,
              "The light cliff sits at 20–50 m, where 1,189–2,665 datasets contribute and the "
              "largest holds 9–12%. The other cliff worth hunting was the carbonate compensation "
              "depth near 4,500 m, and forams do fall from 2.04% of the 3–4 km band to 0.39% of "
              "the 4–5 km band — right size, right place. It cannot be claimed: sea cucumbers are "
              "26.7% of that band by themselves. Blocked, not negative.",
              size=10.5, fill=INK2, chars=76)

    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              "OBIS v3 statistics/env, /occurrence and /dataset, fetched 2026-09-18. The 38 depth "
              "bins are NOT equal width — 10 m to 200 m, then 100 m, then 1,000 m — so the raw "
              "histogram's steps at 200 m and 1,000 m are the bin widening, not a boundary: per "
              "metre, 190–200 m holds 67,390 records and 200–300 m holds 45,865, a fall drawn as "
              "a rise. Only the 10 m bins are used here. startdepth/enddepth match a record's "
              "depth RANGE, so abutting bands overlap and their counts must not be summed; every "
              "band figure is a ratio inside one query. Bathymetry, sst, sss and shoredistance "
              "are on every record but cannot be filtered on — those params return the "
              "unfiltered total, exactly as a nonsense param does.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for r in rows:
        print(f"    {r['common']:<20}{r['kind']:<8}half {str(r['half']):>5} m   "
              f"tenth {str(r['tenth']):>5} m")
    return 0


if __name__ == "__main__":
    sys.exit(main())
