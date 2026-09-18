#!/usr/bin/env python3
"""The register sees fishing fleets, not fish farms.

    python3 chart-12-attention.py

OBIS carries no field for "farmed" or "commercially important". The question is whether either
falls out of the record profile anyway. Two numbers per species: total records, and how many
separate datasets report it. Datasets are breadth -- a species in 300 of them is genuinely met
by many programmes -- so regressing records on datasets gives an expected attention, and the
residual is a species counted more, or less, than its spread of sources warrants.

**Two lists were written down before the fetch**, from the FAO production tables: 28 major
farmed marine species and 33 major wild-capture species that are not farmed at scale. Whether
they separate is the test, and either answer is useful.

**They separate completely, and only one way.** Wild-capture species sit **+1.04 sd** above the
unlabelled background, p = 0.0001 on a 20,000-draw permutation test. Farmed species sit +0.18 sd
from it, p = 0.36 -- indistinguishable. A farmed oyster never enters a trawl survey, so
aquaculture is invisible here and no amount of modelling will recover it. What the residual
detects is **fishery survey effort**, which is a real and different thing.

**The top of the ranking is not the finding, and reading it would have misled.** The forty
largest residuals contain **none** of the declared commercial species: they have a median of 13
datasets, the same as the whole sample, and are one-survey species -- Falkland Islands trawl
material again, the same programme that distorted figure 6's cephalopods. The declared species
have a median of 105 datasets. The commercial signal is a **shift in the middle of the
distribution**, not an extreme tail, and only a declared list could tell the two apart.

**The other half of the question is the negative residual.** A species met by forty or more
datasets and still barely counted is under-observed relative to how widely it is encountered:
the giant manta is in 160 datasets with 4,642 records, the scalloped hammerhead in 156 with
8,840. Both are IUCN-threatened. That is a research-attention list that does not depend on
anyone's opinion of what matters.

**Where it cannot go.** Datasets are a crude breadth measure and a large one may cover a small
sea. Species were sampled stratified by log10(records) so the draw is not simply the famous end,
but 1,143 species of five classes is a sample, and the farmed null rests on 21 species.
"""
import json, math, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "attention.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"


def sup(x, y, mant, exp, *, size, fill, anchor="start"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}">{mant}<tspan font-size="{size*0.72:.1f}" '
            f'dy="{-size*0.40:.1f}">{exp}</tspan></text>')


def main():
    d = json.load(open(os.path.join(HERE, "..", "data", "attention.json")))
    rl = json.load(open(os.path.join(HERE, "..", "data", "redlist.json")))
    thr = {x["name"] for x in rl["threatened"]}
    sp = [x for x in d["species"] if x["datasets"] and x["records"]]
    xs = [math.log10(x["datasets"]) for x in sp]
    ys = [math.log10(x["records"]) for x in sp]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((p - mx) * (q - my) for p, q in zip(xs, ys)) / sum((p - mx) ** 2 for p in xs)
    a = my - b * mx
    sd = st.pstdev([q - (a + b * p) for p, q in zip(xs, ys)])
    for x in sp:
        x["exp"] = 10 ** (a + b * math.log10(x["datasets"]))
        x["resid"] = (math.log10(x["records"]) - math.log10(x["exp"])) / sd

    W, H = 1200, 960
    s = plate.open_svg(W, H, "The register sees fishing fleets, not fish farms.")
    fr, _ = plate.frame(W, 62,
                        who="anyone using a record count as a proxy for how well a species "
                            "is known",
                        decide="whether a species is under-observed for how widely it is met",
                        wrong="a longer farmed list separates from the background, making the "
                              "null a sample-size result")
    s += fr

    # ---- left: the test. Background, then the two declared lists on top of it.
    AX, AY, AH, AW = 28, 250, 400, 470
    s.append(txt(AX, AY - 50, "records against the number of datasets reporting the species",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(AX, AY - 34, "1,143 species from five classes, sampled across the record range",
                 size=10.5, fill=MUTED))
    x0, pw = AX + 52, AW - 86
    LX, HX, LY, HY = 0, 2.8, 0, 7.0
    px = lambda v: x0 + pw * ((v - LX) / (HX - LX))
    py = lambda v: AY + AH - AH * ((v - LY) / (HY - LY))
    for e in range(0, 3):
        s.append(f'<line x1="{px(e):.1f}" y1="{AY:.1f}" x2="{px(e):.1f}" y2="{AY+AH:.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(sup(px(e), AY + AH + 16, "10", str(e), size=9, fill=MUTED, anchor="middle"))
    for e in range(0, 8, 2):
        s.append(f'<line x1="{x0:.1f}" y1="{py(e):.1f}" x2="{px(HX):.1f}" y2="{py(e):.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(sup(x0 - 7, py(e) + 3, "10", str(e), size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, AY + AH + 32, "datasets that report the species", size=9.5, fill=MUTED))
    s.append(f'<text transform="translate({AX+10},{AY+AH/2}) rotate(-90)" font-size="9.5" '
             f'fill="{MUTED}" text-anchor="middle">records</text>')
    for x in sp:
        if x["control"]:
            continue
        s.append(f'<circle cx="{px(math.log10(x["datasets"])):.1f}" '
                 f'cy="{py(math.log10(x["records"])):.1f}" r="2" fill="{SLATE}" '
                 f'fill-opacity="0.4"/>')
    s.append(f'<line x1="{px(LX):.1f}" y1="{py(a + b*LX):.1f}" x2="{px(HX):.1f}" '
             f'y2="{py(a + b*HX):.1f}" stroke="{INK2}" stroke-width="1.6"/>')
    for lbl, col in (("farmed", GREEN), ("wild", RED)):
        for x in sp:
            if x["control"] != lbl:
                continue
            s.append(f'<circle cx="{px(math.log10(x["datasets"])):.1f}" '
                     f'cy="{py(math.log10(x["records"])):.1f}" r="4.4" fill="{col}" '
                     f'fill-opacity="0.85"/>')
    lx, ly = x0 + 10, AY + 16
    for lab, col in ((f"wild-caught, declared (n=29) · +1.04 sd, p=0.0001", RED),
                     (f"farmed, declared (n=21) · +0.18 sd, p=0.36", GREEN),
                     ("everything else (n=1,093)", SLATE)):
        s.append(f'<circle cx="{lx+5:.1f}" cy="{ly-3.5:.1f}" r="4.4" fill="{col}" '
                 f'fill-opacity="0.85"/>')
        s.append(txt(lx + 16, ly, lab, size=9.5, fill=INK2))
        ly += 14
    s.append(txt(lx + 16, ly, "fitted line: records = datasets^2.09, R² 0.74", size=9.5,
                 fill=INK2))
    s += wrap(AX, AY + AH + 54,
              "Wild-capture species sit a full standard deviation above the line and farmed "
              "species sit on it. A farmed oyster never enters a trawl survey, so aquaculture "
              "is invisible here and no model will recover it. The forty largest residuals "
              "contain none of the declared species — they are one-survey species with a median "
              "of 13 datasets against the declared list's 105, so the commercial signal is a "
              "shift in the middle, not a tail. Only a list written down first separates them.",
              size=10.5, fill=INK2, chars=76)

    # ---- right: the other half. Widely met, barely counted, drawn as the gap itself.
    BX, BY, BH, BW = 560, 250, 400, 470
    s.append(txt(BX, BY - 50, "met everywhere, counted rarely", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(BX, BY - 34, "species in 40+ datasets with the largest shortfall against the "
                              "fit", size=10.5, fill=MUTED))
    wide = sorted((x for x in sp if x["datasets"] >= 40), key=lambda x: x["resid"])[:14]
    bx0, bpw = BX + 168, BW - 214
    LB, HB = 1.5, 5.5
    bpx = lambda v: bx0 + bpw * ((min(max(v, LB), HB) - LB) / (HB - LB))
    rh = (BH - 30) / len(wide)
    for e in range(2, 6):
        s.append(f'<line x1="{bpx(e):.1f}" y1="{BY-4:.1f}" x2="{bpx(e):.1f}" '
                 f'y2="{BY+len(wide)*rh:.1f}" stroke="{GRID}"/>')
        s.append(sup(bpx(e), BY + len(wide) * rh + 16, "10", str(e), size=9, fill=MUTED,
                     anchor="middle"))
    for i, x in enumerate(wide):
        y = BY + i * rh + rh / 2
        ax_, bx_ = bpx(math.log10(x["records"])), bpx(math.log10(x["exp"]))
        s.append(f'<line x1="{ax_:.1f}" y1="{y:.1f}" x2="{bx_:.1f}" y2="{y:.1f}" '
                 f'stroke="{AMBER}" stroke-width="1.6" stroke-opacity="0.75"/>')
        s.append(f'<circle cx="{bx_:.1f}" cy="{y:.1f}" r="3.6" fill="none" stroke="{INK2}" '
                 f'stroke-width="1.3"/>')
        s.append(f'<circle cx="{ax_:.1f}" cy="{y:.1f}" r="4" fill="{AMBER}"/>')
        red = x["name"] in thr
        s.append(txt(BX + 160, y + 3, x["name"], size=9.5, anchor="end",
                     fill=RED if red else INK2, weight="600" if red else "normal"))
        s += halo(bx_ + 9, y + 3, f"{x['datasets']} ds", size=8.5, fill=MUTED)
    lx2, ly2 = bx0, BY + len(wide) * rh + 34
    s.append(f'<circle cx="{lx2+5:.1f}" cy="{ly2-3.5:.1f}" r="4" fill="{AMBER}"/>')
    s.append(txt(lx2 + 16, ly2, "records it has", size=9.5, fill=INK2))
    s.append(f'<circle cx="{lx2+125:.1f}" cy="{ly2-3.5:.1f}" r="3.6" fill="none" '
             f'stroke="{INK2}" stroke-width="1.3"/>')
    s.append(txt(lx2 + 136, ly2, "records the fit expects", size=9.5, fill=INK2))
    s.append(txt(BX, ly2 + 15, "names in red are IUCN-threatened", size=9.5, fill=RED))
    s += wrap(BX, ly2 + 36,
              "These are met by forty or more separate programmes and counted a fraction of "
              "what that breadth implies. It is a research-attention list that needs nobody's "
              "opinion of what matters. Among species in 40+ datasets, the over-counted are "
              "more often IUCN-threatened than the under-counted, 21.4% against 8.1% — the same "
              "direction as figure 11, on nine species against five, so it is a hint and not a "
              "finding.",
              size=10.5, fill=INK2, chars=76)

    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              "OBIS v3 checklist and /dataset, fetched 2026-09-19. Breadth is the count of "
              "datasets reporting the species; /v3/node takes a scientificname and returns 39 "
              "for everything, which is the total node count, so it cannot be used. Species were "
              "drawn stratified by log10(records) from five classes, seed 20260919, with every "
              "declared control added regardless of the draw. Checklists are paged with skip "
              "because the endpoint caps at 10,000 and sorts by record count — the variable "
              "being modelled. p-values are two-sided permutation tests on the median, 20,000 "
              "draws, against the 1,093 unlabelled species.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for lbl in ("wild", "farmed"):
        v = [x["resid"] for x in sp if x["control"] == lbl]
        print(f"    {lbl:<8}n={len(v):<4} median residual {st.median(v):+.2f} sd")
    return 0


if __name__ == "__main__":
    sys.exit(main())
