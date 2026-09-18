#!/usr/bin/env python3
"""You cannot map invasion from this register, and the reason is one word in a schema.

    python3 chart-3-invasive.py

OBIS carries a `wrims` flag from the World Register of Introduced Marine Species, and
`?wrims=true` filters occurrences and every aggregation endpoint. 44.5 million records — 19.4%
of the register — come back. It looks like exactly the tool for mapping marine invasion.

**Effort-normalised, the map produces an immediate finding, and it is wrong.** Taking
introduced records as a share of all records per cell — which controls for the survey bias the
first figure in this recipe found — the most invaded waters on Earth are off south-west
Greenland, at **100%**, followed by Arctic Norway at 99% and 95%, and British Columbia at 95%.

**Opening the Greenland cell explains it.** 299 of 300 sampled records are *Salvelinus alpinus*,
Arctic char, from a single dataset. **Arctic char is native to Greenland.**

**WRiMS lists a species if it is introduced somewhere. The filter then marks every record of
that species everywhere, including throughout its native range.** The flag is a property of the
species and is being read as a property of the record.

| species | flagged | records | native range includes |
| --- | --- | --- | --- |
| *Salvelinus alpinus* | yes | 325,563 | Greenland, Scandinavia, Arctic Canada |
| *Mytilus edulis* | yes | 163,774 | the whole North Atlantic |
| *Carcinus maenas* | yes | 187,794 | European Atlantic coast |
| *Crassostrea gigas* | yes | 43,714 | Japan and north-east Asia |
| *Gadus morhua* | no | 3,116,403 | — |

So a cell reading 100% introduced can mean the water is entirely non-native, or that one
widely-moved species lives there naturally and somebody surveyed it. **Nothing in the register
distinguishes those**, because the introduced-ness is not recorded against the occurrence.

**What would actually work.** WRiMS publishes introduced status per species *per region*, which
is the join that would fix this — it is simply not what the OBIS filter applies. Failing that,
first-record dates by region are robust to the problem, because a species' first appearance
somewhere is an event even when the surrounding volume is unreliable.

**And a second trap on the way in.** `wrims=false` returns zero records and so does
`wrims=banana`. The complement is not reachable and a garbage value is indistinguishable from
an empty result, so every non-introduced count here is computed as total minus introduced and
never asked for.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import obis, plate                                                       # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "invasion.svg")
RED, AMBER, GREEN, BLUE, PLUM = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#7a4a8a"
PLACES = [(61.0, -47.2, "SW Greenland"), (61.0, -45.8, "SW Greenland"),
          (66.7, 16.0, "Arctic Norway"), (51.2, -124.6, "British Columbia"),
          (66.7, 14.6, "Arctic Norway"), (63.8, 10.4, "Trondheim"),
          (69.5, -104.9, "Nunavut"), (34.3, 139.8, "Tokyo Bay"),
          (47.0, -59.9, "Gulf of St Lawrence"), (45.6, -61.3, "Nova Scotia")]
SPECIES = [("Salvelinus alpinus", "Arctic char", True, 325563,
            "Greenland, Scandinavia, Arctic Canada"),
           ("Carcinus maenas", "green crab", True, 187794, "European Atlantic coast"),
           ("Mytilus edulis", "blue mussel", True, 163774, "the whole North Atlantic"),
           ("Crassostrea gigas", "Pacific oyster", True, 43714, "Japan, north-east Asia"),
           ("Gadus morhua", "Atlantic cod", False, 3116403, "not flagged")]


def place(lat, lon):
    for la, lo, nm in PLACES:
        if abs(la - lat) < 1 and abs(lo - lon) < 1.6:
            return nm
    return f"{lat:.0f}, {lon:.0f}"


def main():
    def cells(name):
        out = {}
        for f in obis.load(name)["features"]:
            c = f["geometry"]["coordinates"][0]
            lon = round(sum(p[0] for p in c) / len(c), 3)
            lat = round(sum(p[1] for p in c) / len(c), 3)
            out[(lat, lon)] = f["properties"].get("n", 0)
        return out
    a, w = cells("grid3.json"), cells("grid3-wrims.json")
    ca, cw = obis.load("composition.json"), obis.load("composition-wrims.json")
    joined = [(k, a[k], w.get(k, 0)) for k in a if a[k] >= 5000]
    joined.sort(key=lambda t: -(t[2] / t[1]))

    W, H = 1200, 800
    s = plate.open_svg(W, H, "You cannot map invasion from this register, and the reason is "
                             "one word in a schema")
    fr, _ = plate.frame(W, 62,
                        who="anyone computing invasion pressure from an occurrence register",
                        decide="whether the introduced flag can be read at record level at all",
                        wrong="WRiMS status turns out to be recorded per region rather than per species")
    s += fr


    # ---- left: the distribution the claim would have to live in. The first version of this
    # panel was ten ranked bars reading 84%, 86%, 88%, 89%, 93%, 95%, 95%, 99%, 100%, 100% --
    # ten bars of near-identical length, which is a list of numbers wearing a chart's clothes,
    # and two of the ten were the same place name twice. What matters is the SHAPE: a real
    # invasion map is crushed against zero with a thin tail. This one has a shoulder at the top.
    import math
    AX, AY, AW, AH = 28, 256, 500, 330
    s.append(txt(AX, AY - 44, "introduced share of every well-sampled cell", size=12.5,
                 fill=INK, weight="600"))
    s.append(txt(AX, AY - 28, f"{len(joined):,} cells holding 5,000 records or more",
                 size=10.5, fill=MUTED))
    x0 = AX + 46
    px = lambda f: x0 + (AW - 66) * f
    py = lambda n: AY + AH - 40 - (AH - 70) * (math.log10(max(n, 5000)) - 3.7) / 3.2
    for f in (0, .25, .5, .75, 1.0):
        s.append(f'<line x1="{px(f):.1f}" y1="{AY:.1f}" x2="{px(f):.1f}" y2="{AY+AH-40:.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(px(f), AY + AH - 24, f"{f*100:.0f}%", size=9, fill=MUTED, anchor="middle"))
    for n, lab in ((1e4, "10k"), (1e5, "100k"), (1e6, "1M")):
        s.append(txt(x0 - 8, py(n) + 3, lab, size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, AY + AH - 8, "share of the cell's records flagged introduced",
                 size=9.5, fill=MUTED))
    s.append(f'<text transform="translate({AX+10},{AY+(AH-40)/2}) rotate(-90)" font-size="9.5" '
             f'fill="{MUTED}" text-anchor="middle">records in the cell</text>')
    for (lat, lon), tot, wn in joined:
        f = wn / tot
        col = RED if f > .8 else (AMBER if f > .4 else BLUE)
        s.append(f'<circle cx="{px(f):.1f}" cy="{py(tot):.1f}" r="3" fill="{col}" '
                 f'fill-opacity="0.55"/>')
    hi = [t for t in joined if t[2] / t[1] > .8]
    placed = []
    for (lat, lon), tot, wn in sorted(hi, key=lambda t: -t[1])[:4]:
        cx, cy = px(wn / tot), py(tot)
        ly = cy + 3
        while any(abs(ly - q) < 12 and abs(cx - qx) < 150 for qx, q in placed):
            ly -= 12
        placed.append((cx, ly))
        if abs(ly - (cy + 3)) > 8:
            s.append(f'<line x1="{cx-5:.1f}" y1="{cy:.1f}" x2="{cx-9:.1f}" y2="{ly-3:.1f}" '
                     f'stroke="{RED}" stroke-width="0.8" stroke-opacity="0.5"/>')
        s += halo(cx - 10, ly, place(lat, lon), size=9, fill=RED, anchor="end")
    s += wrap(AX, AY + AH + 14,
              f"{len(hi)} of {len(joined):,} cells are over 80% introduced, and they are not "
              f"small: the most invaded water on Earth is off south-west Greenland and in "
              f"Arctic Norway, not in a busy port. That is the first sign something is wrong.",
              size=10.5, fill=INK2, chars=80)

    # ---- right: why. The flag is binary per species, so every species sits at 0% or 100%
    # and nothing lands between. That is the schema fact, drawn instead of asserted -- it
    # replaces a list of five species with the word "flagged" typed beside each.
    BX, BY, BH, BW = 590, 256, 330, 500
    s.append(txt(BX, BY - 44, "and the flag has only two values", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(BX, BY - 28, "share of a species' own records carrying the introduced flag",
                 size=10.5, fill=MUTED))
    bx0 = BX + 46
    bpx = lambda f: bx0 + (BW - 150) * f
    bpy = lambda n: BY + BH - 40 - (BH - 70) * (math.log10(max(n, 1e4)) - 4) / 2.6
    for f in (0, .25, .5, .75, 1.0):
        s.append(f'<line x1="{bpx(f):.1f}" y1="{BY:.1f}" x2="{bpx(f):.1f}" '
                 f'y2="{BY+BH-40:.1f}" stroke="{GRID}"/>')
        s.append(txt(bpx(f), BY + BH - 24, f"{f*100:.0f}%", size=9, fill=MUTED, anchor="middle"))
    for n, lab in ((1e4, "10k"), (1e5, "100k"), (1e6, "1M")):
        s.append(txt(bx0 - 8, bpy(n) + 3, lab, size=9, fill=MUTED, anchor="end"))
    s.append(txt(BX, BY + BH - 8, "share of that species' records flagged introduced",
                 size=9.5, fill=MUTED))
    s.append(f'<text transform="translate({BX+10},{BY+(BH-40)/2}) rotate(-90)" font-size="9.5" '
             f'fill="{MUTED}" text-anchor="middle">records for the species</text>')
    placed2 = []
    for sci, common, flagged, recs, native in sorted(SPECIES, key=lambda x: -x[3]):
        f = 1.0 if flagged else 0.0
        col = RED if flagged else GREEN
        cy = bpy(recs)
        s.append(f'<circle cx="{bpx(f):.1f}" cy="{cy:.1f}" r="5.5" fill="{col}" '
                 f'fill-opacity="0.85"/>')
        right = not flagged
        # blue mussel and green crab are 24k apart on a log axis; without this they overprint
        ly = cy + 3
        while any(abs(ly - q) < 13 for q in placed2):
            ly += 13
        placed2.append(ly)
        if abs(ly - (cy + 3)) > 8:
            s.append(f'<line x1="{bpx(f) + (7 if right else -7):.1f}" y1="{cy:.1f}" '
                     f'x2="{bpx(f) + (11 if right else -11):.1f}" y2="{ly-3:.1f}" '
                     f'stroke="{col}" stroke-width="0.8" stroke-opacity="0.5"/>')
        s += halo(bpx(f) + (11 if right else -11), ly,
                  f"{common} · native to {native}" if flagged else common,
                  size=9.5, fill=col, anchor="start" if right else "end")
    s += wrap(BX, BY + BH + 14,
              "Nothing sits between the two edges, because WRiMS lists a SPECIES if it is "
              "introduced somewhere and the filter then marks every one of its records, native "
              "range included. Arctic char is native to Greenland and 325,549 of its 325,563 "
              "records are flagged. A cell at 100% can mean the water is non-native, or that "
              "one widely-moved species lives there naturally. Nothing separates those.",
              size=10.5, fill=INK2, chars=80)

    fy = H - 20 - 14 * 3
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              "OBIS v3, fetched 2026-09-18. A second trap: wrims=false returns zero and so does "
              "wrims=banana, so the complement is unreachable — non-introduced counts here are "
              "total minus introduced. WRiMS publishes status per species PER REGION, which is "
              "the join the filter does not apply. Method in the recipe.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for (lat, lon), n, iv in joined[:5]:
        print(f"    {place(lat,lon):<22}{n:>10,}{iv/n:>8.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
