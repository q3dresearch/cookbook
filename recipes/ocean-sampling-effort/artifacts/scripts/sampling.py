#!/usr/bin/env python3
"""The world map of marine life is about five monitoring programmes.

    python3 chart-1-sampling.py

This replaces two figures that made the same argument twice. The first drew the concentration
of records across grid cells and named the busiest ones; the second drew how much of a cell is
one dataset and named the busiest ones again. The named cells were the same cells -- Sydney,
Santa Barbara, the Belgian coast, Monterey, the Dutch coast -- and only one of the two panels
said what was actually in them, which is the part that matters. The scatter of cells against
top-dataset share is gone: it was a blob, and the banded medians beside it carry the same claim
legibly.

**229 million records sounds like 229 million independent looks at the sea.** 27,168 cells hold
them, 27 cells hold a third, and 42% of cells hold fewer than a hundred records between them.

**The median cell takes 45% of its records from a single dataset**, 46% are more than half one
dataset, and 13% are more than 90%. It is worst where the data is thinnest, which is where a map
is read most confidently: in cells holding 100 to 1,000 records the median top dataset is 67%
and 82% of cells are majority-one. A remote cell is not thinly sampled by many people; it is one
survey that went there once.

**And the busy cells are not what "biodiversity hotspot" suggests.** They carry 120 to 290
datasets each and still take 30-65% of their volume from one: Australian Microbiome 16S
sequencing at Sydney, PISCO kelp forest surveys at Santa Barbara, herring gull telemetry off
Belgium, ANEMOON beach-washup monitoring off the Netherlands. A genomics programme, a kelp
survey, a bird study and people walking a beach. **A cell filled by 16S sequencing contains
bacteria; a cell filled by beach washup contains what floats.**

The records-per-species panel from the first of the two figures is not here. It said a seabird
species carries thirty-eight times the records of an average invertebrate, which is true and is
the same observation figure 15 makes better -- 52.7% of seabird records carry OBIS's ON_LAND
flag, because that is where people stand to count them. Four panels made this a portmanteau and
pushed it past the essay threshold; the number is in the README.
"""
import json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import obis, plate                                                       # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "sampling.svg")
RED, AMBER, GREEN, BLUE, PLUM = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#7a4a8a"
BANDS = ["over 1M", "100k-1M", "10k-100k", "1k-10k", "100-1k"]
# Cell centroids matched to a coastline by hand. The register carries no place names, and
# these were inlined rather than imported from the figure this one replaces -- a merged figure
# that still reads its predecessor's source is not a merge.
PLACES = [(-34.6, 151.0, "Sydney"), (34.3, -120.4, "Santa Barbara"), (51.2, 3.4, "Belgian coast"),
          (-43.0, 148.2, "Tasmania"), (35.7, -121.8, "Monterey Bay"), (-31.8, 115.9, "Perth"),
          (52.6, 4.8, "Dutch coast"), (-19.1, 146.8, "Townsville"), (37.1, -121.8, "N Monterey"),
          (34.3, -119.0, "Santa Barbara"), (-27.6, 153.8, "Brisbane")]


def place(lat, lon):
    for la, lo, nm in PLACES:
        if abs(la - lat) < 1.2 and abs(lo - lon) < 1.8:
            return nm
    return f"{lat:.0f}, {lon:.0f}"


def main():
    g = obis.load("grid3.json")["features"]
    st = obis.load("statistics.json")
    cells = []
    for f in g:
        c = f["geometry"]["coordinates"][0]
        cells.append((f["properties"].get("n", 0),
                      sum(p[1] for p in c) / len(c), sum(p[0] for p in c) / len(c)))
    cells.sort(reverse=True)
    tot = sum(c[0] for c in cells)
    sampled = [c for c in json.load(open(os.path.join(HERE, "..", "data", "map-depth.json")))
               ["cells"] if c["top_share"] is not None]

    W, H = 1200, 800
    s = plate.open_svg(W, H, "The world map of marine life is about five monitoring programmes")
    fr, _ = plate.frame(W, 62,
                        who="anyone treating a dense cell as a well-characterised one, or a gap "
                            "as an empty sea",
                        decide="whether a cell's contents describe the ocean or one project's "
                               "method",
                        wrong="the median top-dataset share falls below a quarter in a later "
                              "sample")
    s += fr

    # ---- top left: how concentrated the whole register is
    AX, AY, AW, AH = 28, 250, 330, 230
    s.append(txt(AX, AY - 44, "twenty-seven cells hold a third of it", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(AX, AY - 28, f"cumulative share of {tot:,} records", size=10.5, fill=MUTED))
    px = lambda q: AX + AW * (math.log10(max(q, 1e-4)) + 4) / 4
    py = lambda v: AY + AH - AH * v
    pts, run = [], 0
    for i, (n, _, _) in enumerate(cells):
        run += n
        if i < 40 or i % 37 == 0:
            pts.append((px((i + 1) / len(cells)), py(run / tot)))
    s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                    for i, (a, b) in enumerate(pts))
             + f'" fill="none" stroke="{BLUE}" stroke-width="2.6"/>')
    for q, lab in ((0.001, "0.1%"), (0.01, "1%"), (0.1, "10%"), (1.0, "100%")):
        s.append(f'<line x1="{px(q):.1f}" y1="{AY}" x2="{px(q):.1f}" y2="{AY+AH}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(px(q), AY + AH + 16, lab, size=9.5, fill=MUTED, anchor="middle"))
    for v in (0.25, 0.5, 0.75, 1.0):
        s.append(f'<line x1="{AX}" y1="{py(v):.1f}" x2="{AX+AW}" y2="{py(v):.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(AX - 6, py(v) + 4, f"{v:.0%}", size=9.5, fill=MUTED, anchor="end"))
    for q in (0.001, 0.01):
        k = max(1, int(len(cells) * q))
        v = sum(c[0] for c in cells[:k]) / tot
        s.append(f'<circle cx="{px(q):.1f}" cy="{py(v):.1f}" r="4" fill="{BLUE}"/>')
        s += halo(px(q) + 8, py(v) + 4, f"{v:.0%}", size=11, fill=BLUE)
    s.append(txt(AX, AY + AH + 32, "share of cells, largest first (log)", size=9.5, fill=MUTED))
    under = sum(1 for c in cells if c[0] < 100)
    s += wrap(AX, AY + AH + 54,
              f"{under:,} of {len(cells):,} cells hold under a hundred records. The emptiest "
              f"half hold 0.3% between them.",
              size=10.5, fill=INK2, chars=54)

    # ---- top right: and how much of any one cell is a single contributor
    BX, BY, BW_ = 400, 250, 330
    s.append(txt(BX, BY - 44, "and how much of a cell is one dataset", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(BX, BY - 28, "median share held by the largest contributor",
                 size=10.5, fill=MUTED))
    for i, b in enumerate(BANDS):
        v = [c for c in sampled if c["band"] == b]
        if not v:
            continue
        m = statistics.median(c["top_share"] for c in v)
        nd = statistics.median(c["datasets"] for c in v)
        dom = sum(1 for c in v if c["top_share"] > .5) / len(v)
        y = BY + i * 66
        s.append(txt(BX, y, f"cells with {b} records", size=11, fill=INK))
        s.append(txt(BX + BW_, y, f"{nd:,.0f} datasets", size=9, fill=MUTED, anchor="end"))
        col = RED if m > .6 else (AMBER if m > .4 else GREEN)
        s.append(f'<rect x="{BX}" y="{y+8:.1f}" width="{BW_}" height="18" fill="{GRID}"/>')
        s.append(f'<rect x="{BX}" y="{y+8:.1f}" width="{max(BW_*m,1.5):.1f}" height="18" '
                 f'fill="{col}"/>')
        s += halo(BX + BW_ * m + 7, y + 22, f"{m:.0%}", size=11, fill=col)
        s.append(txt(BX, y + 42, f"{dom:.0%} of these cells are majority one dataset",
                     size=9, fill=MUTED))
    s += wrap(BX, BY + len(BANDS) * 66 + 4,
              "Worst where the data is thinnest — which is where a map is read most "
              "confidently.",
              size=10.5, fill=INK2, chars=54)

    # ---- right: what is actually in the busy cells. The one panel the merge kept whole.
    CX, CY, CW = 770, 250, 400
    s.append(txt(CX, CY - 44, "and what actually fills the busiest cells", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(CX, CY - 28, "largest contributing dataset, by name", size=10.5, fill=MUTED))
    for i, c in enumerate(sorted(sampled, key=lambda c: -c["cell_records"])[:10]):
        y = CY + i * 50
        s.append(txt(CX, y, place(c["lat"], c["lon"]), size=10.5, fill=INK, weight="600"))
        s.append(txt(CX + 118, y, f"{c['cell_records']:,}", size=9, fill=MUTED, anchor="end"))
        s.append(txt(CX + 132, y, f"{c['datasets']} datasets", size=9, fill=MUTED))
        w = 120 * c["top_share"]
        s.append(f'<rect x="{CX+218}" y="{y-9:.1f}" width="{max(w,1.5):.1f}" height="11" '
                 f'fill="{PLUM}"/>')
        s += halo(CX + 218 + w + 6, y, f"{c['top_share']:.0%}", size=9.5, fill=PLUM)
        s.append(txt(CX, y + 16, c["top_title"][:54], size=9, fill=INK2))
    s += wrap(CX, CY + 10 * 50 + 6,
              "None is a biodiversity survey of the ocean, and together they are the global "
              "picture. A cell filled by 16S sequencing contains bacteria; one filled by beach "
              "washup contains what floats.", size=10.5, fill=INK, chars=62)

    # The records-per-species panel that lived here is gone. It said a seabird species
    # carries 38x the records of an average invertebrate — true, and the same observation
    # figure 15 makes better with the ON_LAND flag, where 52.7% of seabird records carry it.
    # Four panels made this a portmanteau and pushed it past the essay threshold; the number
    # is in the recipe README instead.

    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"OBIS v3, fetched 2026-09-18: {st['records']:,} records across "
              f"{st['datasets']:,} datasets, live and additive, so this is one fetch. Cells are "
              f"the API's precision-3 grid and are not equal-area. Sampling, scoping and the two "
              f"panels this figure replaced are in the recipe.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {len(cells):,} cells, top 27 hold {sum(c[0] for c in cells[:27])/tot:.1%}")
    print(f"    median top-dataset share {statistics.median(c['top_share'] for c in sampled):.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
