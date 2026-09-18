#!/usr/bin/env python3
"""For plants and single cells, recorded depth is the instrument, not the organism.

    python3 chart-7-producers.py

Figure 6 did this for animals, where depth separated classes by three orders of magnitude and
most of that was real: sea cucumbers dominate abyssal sediment and seabirds do not. Running the
same pull over plants, algae, phytoplankton and bacteria gives the opposite result, and the
opposite result is the finding.

**Depth collapses.** Eleven of the fourteen classes have a median recorded depth of 0 m. What
varies is the tail, and the tail is bought entirely by method: the rank correlation between a
class's DNA-sequencing share and the share of its records below 50 m is **+0.97 across the
thirteen classes sampled from water**. Alphaproteobacteria is 96% sequencing and 44% below
50 m; kelp is 0.8% sequencing and 0.3% below 50 m. A CTD rosette fires bottles down the water
column and a diver does not, so the depth profile is a picture of the gear.

**Forams are the control that names the mechanism.** They break the correlation -- 2.2%
sequencing but 39.6% below 50 m -- and they break it because their largest dataset is the Deep
Sea Drilling Project. That is a third instrument, a sediment core, and it reaches depths no
water sampler does. Drop forams and rho goes from +0.73 to +0.97. The exception is not noise;
it is the same claim arriving by a different route.

**Temperature still works.** Mean recorded SST spans 10.7C for cryptophytes to 21.5C for
seagrasses, a wider range than the animals' 6.7 to 17.2 and shifted warm, which is what a group
containing tropical seagrass beds and reef algae should look like. The ridgeline is sorted by
mean rather than mode for the reason figure 6 records: modes tie, six classes at 10C and six
more at 20C.

**A synonym trap, recorded because it nearly went in.** OBIS resolves unaccepted names silently.
`Fragilariophyceae` and `Bacillariophyceae` both return 6,389,742 records; `Prymnesiophyceae`
and `Coccolithophyceae` both return 1,252,644. Every class here is checked against /v3/taxon for
`taxonRank` Class and `taxonomicStatus` accepted before it is drawn.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "producers.svg")
RED, AMBER, GREEN, BLUE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8"
KCOL = {"Plantae": GREEN, "Chromista": BLUE, "Bacteria": AMBER}
CORE = "Globothalamea"          # drill core, not water column -- excluded from rho


def pct(bins, q):
    tot = sum(r["records"] for r in bins) or 1
    run = 0
    for r in bins:
        run += r["records"]
        if run >= tot * q:
            return r["from"]
    return bins[-1]["from"] if bins else 0


def spearman(a, b):
    def rk(xs):
        order = sorted(range(len(xs)), key=lambda i: xs[i])
        out = [0] * len(xs)
        for p, i in enumerate(order):
            out[i] = p
        return out
    ra, rb, n = rk(a), rk(b), len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** .5
    return num / den if den else 0.0


def main():
    d = json.load(open(os.path.join(HERE, "..", "data", "producers.json")))
    rows = []
    for k, v in d.items():
        b = v["depth"]
        if not b:
            continue
        tot = sum(r["records"] for r in b) or 1
        st = sum(x["records"] for x in v["sst"]) or 1
        rows.append({"k": k, **v, "med": pct(b, .5),
                     "deep": sum(r["records"] for r in b if r["from"] >= 50) / tot,
                     "mean_t": sum(x["sst"] * x["records"] for x in v["sst"]) / st})
    water = [r for r in rows if r["k"] != CORE]
    rho_all = spearman([r["dna_share"] for r in rows], [r["deep"] for r in rows])
    rho_w = spearman([r["dna_share"] for r in water], [r["deep"] for r in water])

    W, H = 1200, 1000
    s = plate.open_svg(W, H, "For plants and single cells, depth is the instrument.")
    fr, _ = plate.frame(W, 62,
                        who="anyone reading a plankton or algal depth range out of OBIS",
                        decide="whether a class's depth profile is the organism or the sampling gear",
                        wrong="a class sampled both ways gives the same depth profile by each method")
    s += fr

    # ---- left: does sequencing buy the depth? one mark per class, no fitted line, because
    # the statistic is a rank correlation and a straight line would assert linearity instead.
    AX, AY, AH = 28, 238, 430
    s.append(txt(AX, AY - 46, "how deep a class is recorded, against how often it was sequenced",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(AX, AY - 30, "each mark is one class; both axes are shares of that class's records",
                 size=10.5, fill=MUTED))
    x0, pw = AX + 52, 400
    px = lambda f: x0 + pw * f
    py = lambda f: AY + AH - AH * (min(f, .50) / .50)
    for g_ in (0, .25, .50, .75, 1.0):
        s.append(f'<line x1="{px(g_):.1f}" y1="{AY:.1f}" x2="{px(g_):.1f}" y2="{AY+AH:.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(px(g_), AY + AH + 16, f"{g_*100:.0f}%", size=9, fill=MUTED, anchor="middle"))
    for g_ in (0, .10, .20, .30, .40, .50):
        s.append(f'<line x1="{x0:.1f}" y1="{py(g_):.1f}" x2="{px(1.0):.1f}" y2="{py(g_):.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(x0 - 8, py(g_) + 3, f"{g_*100:.0f}%", size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, AY + AH + 32, "share of the class's records that are DNA sequencing runs",
                 size=9.5, fill=MUTED))
    s.append(f'<text transform="translate({AX+10},{AY+AH/2}) rotate(-90)" font-size="9.5" '
             f'fill="{MUTED}" text-anchor="middle">share of records below 50 m</text>')
    placed = []
    for r in sorted(rows, key=lambda r: -r["deep"]):
        cx, cy = px(r["dna_share"]), py(r["deep"])
        core = r["k"] == CORE
        col = KCOL.get(r["kingdom"], BLUE)
        if core:
            s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="8.5" fill="none" '
                     f'stroke="{RED}" stroke-width="1.6"/>')
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.4" fill="{col}" '
                 f'fill-opacity="0.85"/>')
        right = r["dna_share"] < .62
        # Points near the floor must have their labels nudged UP, not down: the bottom-left
        # cluster is five classes inside four percentage points and pushing down walks them
        # off the plot and through the axis title.
        step = -11 if cy > AY + AH * .72 else 11
        ly = cy + 3.5
        while any(abs(ly - q) < 11 and abs(cx - qx) < 130 for qx, q in placed):
            ly += step
        ly = min(max(ly, AY + 10), AY + AH - 3)
        placed.append((cx, ly))
        lx_ = cx + (10 if right else -10)
        # Six of the fourteen classes sit inside four percentage points of the floor, so some
        # labels end up well away from their mark. A leader claims only "this name belongs to
        # this dot", which is exactly what is needed and nothing more.
        if abs(ly - (cy + 3.5)) > 13:
            s.append(f'<line x1="{cx + (6 if right else -6):.1f}" y1="{cy:.1f}" '
                     f'x2="{lx_:.1f}" y2="{ly-3:.1f}" stroke="{col}" stroke-width="0.8" '
                     f'stroke-opacity="0.55"/>')
        s += halo(lx_, ly, r["common"], size=9.5,
                  fill=RED if core else INK2, anchor="start" if right else "end")
    lx, ly = px(0.0) + 6, AY + 14
    for name, col in (("Plantae", GREEN), ("Chromista", BLUE), ("Bacteria", AMBER)):
        s.append(f'<circle cx="{lx+4:.1f}" cy="{ly-3.5:.1f}" r="4.4" fill="{col}" '
                 f'fill-opacity="0.85"/>')
        s.append(txt(lx + 14, ly, name, size=9.5, fill=INK2))
        ly += 14
    s.append(f'<circle cx="{lx+4:.1f}" cy="{ly-3.5:.1f}" r="7" fill="none" stroke="{RED}" '
             f'stroke-width="1.5"/>')
    s.append(txt(lx + 14, ly, "sediment core, not water", size=9.5, fill=RED))
    s += wrap(AX, AY + AH + 56,
              f"Rank correlation between the two axes is {rho_w:+.2f} across the thirteen classes "
              f"sampled from water, and {rho_all:+.2f} with forams added back. Forams are the "
              f"exception that names the mechanism: 2.2% sequencing but 39.6% below 50 m, because "
              f"their largest dataset is the Deep Sea Drilling Project. No line is fitted — the "
              f"statistic is a rank correlation and a straight line would claim more than that.",
              size=10.5, fill=INK2, chars=76)

    # ---- right: the same ridgeline as figure 6, sorted by mean temperature
    BX, BY, BW_ = 560, 238, 400
    s.append(txt(BX, BY - 46, "and in what water", size=12.5, fill=INK, weight="600"))
    s.append(txt(BX, BY - 30, "each class's records across sea surface temperature, "
                              "coldest-centred first", size=10.5, fill=MUTED))
    sstb = [b["sst"] for b in rows[0]["sst"]]
    ridge = sorted(rows, key=lambda r: r["mean_t"])
    rw = (BW_ - 20) / (len(sstb) - 1)
    RH, STEP = 40, 31
    px2 = lambda i: BX + 150 + i * rw
    for i, r in enumerate(ridge):
        y = BY + i * STEP
        tot = sum(x["records"] for x in r["sst"]) or 1
        vals = [x["records"] / tot for x in r["sst"]]
        mx = max(vals) or 1
        col = KCOL.get(r["kingdom"], BLUE)
        pts = [(px2(k), y + RH - RH * (v / mx) * 0.95) for k, v in enumerate(vals)]
        s.append(f'<path d="M{pts[0][0]:.1f},{y+RH:.1f} '
                 + " ".join(f"L{a:.1f},{b:.1f}" for a, b in pts)
                 + f' L{pts[-1][0]:.1f},{y+RH:.1f} Z" fill="{col}" fill-opacity="0.28"/>')
        s.append('<path d="' + " ".join(("M" if k == 0 else "L") + f"{a:.1f},{b:.1f}"
                                        for k, (a, b) in enumerate(pts))
                 + f'" fill="none" stroke="{col}" stroke-width="1.7"/>')
        mxp = px2((r["mean_t"] + 5) / 5)
        s.append(f'<line x1="{mxp:.1f}" y1="{y+RH-4:.1f}" x2="{mxp:.1f}" y2="{y+RH+3:.1f}" '
                 f'stroke="{col}" stroke-width="1.6"/>')
        s.append(txt(BX + 142, y + RH - 1, r["common"], size=9.5, fill=INK2, anchor="end"))
        s += halo(px2(len(sstb) - 1) + 8, y + RH - 1, f"{r['mean_t']:.1f}°", size=9, fill=col)
    base = BY + len(ridge) * STEP + RH
    for k, t in enumerate(sstb):
        s.append(txt(px2(k), base + 4, f"{t}", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(BX + 150, base + 20, "°C at the surface · tick is each class's mean",
                 size=9, fill=MUTED))
    s += wrap(BX, base + 44,
              "Sorted by mean, not mode: six classes peak at 10° and six more at 20°, so a modal "
              "ordering would tie them. Seagrasses are the warmest class in the file at 21.5° and "
              "the only one with no weight at all below 5°, which is a tropical and subtropical "
              "plant showing through a register that is otherwise North Atlantic. Cryptophytes are "
              "the coldest at 10.7°.",
              size=10.5, fill=INK2, chars=68)

    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              "OBIS v3 statistics/env and /dataset with a taxon filter, fetched 2026-09-18. "
              "Sequencing share is a keyword match on the titles of each class's 100 largest "
              "datasets (16S, 18S, metagenome, amplicon, eDNA, metabarcoding, Tara Oceans, "
              "Australian Microbiome), which cover 93–99% of every class's records; it is a "
              "method label read off a title, not a field OBIS publishes. Every class was checked "
              "against /v3/taxon for rank Class and status accepted, because OBIS resolves "
              "unaccepted synonyms silently — Fragilariophyceae and Bacillariophyceae return an "
              "identical 6,389,742 records.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"  rho(DNA share, below 50 m) = {rho_w:+.2f} over {len(water)} water-sampled "
          f"classes, {rho_all:+.2f} including forams")
    for r in sorted(rows, key=lambda r: -r["dna_share"]):
        print(f"    {r['common']:<22}DNA {r['dna_share']:>5.1%}  below 50 m {r['deep']:>5.1%}  "
              f"median {r['med']:>5,} m  mean {r['mean_t']:>4.1f}°C")
    return 0


if __name__ == "__main__":
    sys.exit(main())
