#!/usr/bin/env python3
"""The field that would give you biomass exists, and cannot be added up.

    python3 chart-4-units.py

Occurrence registers record presence. OBIS also carries `organismQuantity` — how many, how
heavy, how much cover — on a substantial minority of records, which is what anyone wanting
density or biomass would reach for.

**It cannot be summed, and the reason is the unit field beside it.** A 6,000-record sample
across twelve phyla and classes returns **44 distinct strings** in `organismQuantityType`.
They are not variants of one measure. They are at least five incompatible kinds of thing:

- **counts** — individuals, individual, Individuals, individual count, SpecimensInContainer
- **densities on different geometries** — number of individuals per 60 m², number of
  individuals per 120 m³, Quantity per cubic metre, cells/L. **Area and volume are not the
  same dimension** and nothing marks which is which
- **masses** — tonnes, biomass in kilograms (kg), wet weight of all fish in row
- **an ordinal letter scale** — SACFORN, the British marine abundance scale running
  Superabundant, Abundant, Common, Frequent, Occasional, Rare, Not-seen. It has no numeric
  meaning at all
- **sequencing output** — DNA sequence reads, DNA Sequence reads. These are not organisms.
  A read count scales with PCR amplification, not with how much of a thing is present

**The first version of this figure drew the wrong number.** Each string was a bar whose width
was the LENGTH OF THE STRING, with the record count in the fill opacity: the strongest visual
channel carrying a quantity nobody cares about and the weakest carrying the real one. Width is
the record count now. The granularity was right all along -- one mark per string, because the
forty-four strings ARE the finding and eight grouped bars hide it.

**And one is not an abundance in any sense.** `Length of longest arm in millimeters` appears in
the quantity-type field. That is a morphometric measurement filed where a count belongs, and it
has been through the publishing pipeline into the register.

**Lowercasing and depluralising takes 44 strings to 39.** So this is not a tidying job with a
clean answer underneath. Two records reading "12" mean twelve fish, twelve grams per square
metre, or twelve thousand sequencing reads, and the register does not say which without parsing
prose.

**What this means for the obvious question.** "Biomass density by latitude and longitude" is
not answerable here, and the blocker is not coverage — it is that the quantities recorded are
incommensurable by construction. A project that needed it would have to restrict to one unit
string, which throws away most of the data and reintroduces exactly the sampling bias the
quantity was supposed to escape.
"""
import collections, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import obis, plate                                                       # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "quantity.svg")
RED, AMBER, GREEN, BLUE, PLUM, TEAL = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#7a4a8a", "#2a6f7f"
# Order matters and is the point: "number of individuals per 60 m2" contains the word
# individuals, so a matcher that tests counts first files a density as a count — which is the
# same mistake anyone aggregating this field would make, one layer down.
KIND = [
    ("density — per AREA", BLUE,
     ["per 60 m2", " m2", "per m2", "% cover", "percent cover", "sample area"]),
    ("density — per VOLUME", TEAL,
     ["per 120 m3", " m3", "cubic metre", "cells/l", "per m3", "per litre"]),
    ("counts of individuals", GREEN,
     ["individual", "individuals", "specimensincontainer", "individual count", "abundance",
      "number of individuals", "count", "colonias", "colonies"]),
    ("mass", AMBER, ["tonne", "kilogram", "weight", "kg", "biomass"]),
    ("an ordinal letter scale", PLUM, ["sacforn"]),
    ("sequencing output", RED, ["dna sequence read", "reads"]),
    ("not an abundance at all", "#000000", ["length of longest arm"]),
]


def classify(t):
    low = t.lower()
    for name, col, pats in KIND:
        if any(p in low for p in pats):
            return name, col
    return "everything else", MUTED


def main():
    d = obis.load("units-sample.json")
    types = d["types"]
    total = sum(types.values())
    groups = collections.defaultdict(lambda: [0, 0, []])
    for t, c in types.items():
        nm, col = classify(t)
        g = groups[nm]
        g[0] += c
        g[1] += 1
        g[2].append((c, t))
    order = [k for k, _, _ in KIND] + ["everything else"]
    order = [k for k in order if k in groups]

    W, H = 1200, 740
    s = plate.open_svg(W, H, "The field that would give you biomass exists, and cannot be "
                             "added up")
    fr, _ = plate.frame(W, 62,
                        who="anyone planning to compute density or biomass from occurrence data",
                        decide="whether to build on organismQuantity or go to a survey source",
                        wrong="a controlled vocabulary appears and the strings collapse to a few units")
    s += fr

    AX, AY, AW = 28, 250, 430
    s.append(txt(AX, AY - 44, "what the quantity field is actually measuring", size=12.5,
                 fill=INK, weight="600"))
    s.append(txt(AX, AY - 28, "one mark per distinct string; width is how many records "
                 "carry it, square-root scale", size=10.5, fill=MUTED))
    # Bar width is RECORDS. The first version sized each mark by the LENGTH OF THE STRING and
    # put the record count in the fill opacity -- the strongest visual channel carrying a
    # number nobody cares about, and the real quantity in the weakest. The strings still need
    # to be visible, because the variety is the finding, but they are text, not geometry.
    # One mark per string, because 44 distinct strings IS the finding and eight bars hide it.
    # Width is that string's RECORD COUNT on a square-root scale so the small ones stay
    # visible. The first version sized each mark by the LENGTH OF THE STRING and put the
    # record count in the fill opacity -- the strongest visual channel carrying a number
    # nobody cares about and the weakest carrying the real one. The second version collapsed
    # to eight bars with the strings as a paragraph, which made the figure a table with bars.
    import math
    mxc = max(c for k in order for c, _ in groups[k][2]) or 1
    scale = lambda c: max(11.0, 168 * (c / mxc) ** .5)
    y = AY
    for k in order:
        n, nstr, items = groups[k]
        col = dict((a, b) for a, b, _ in KIND).get(k, MUTED)
        s.append(txt(AX, y, k, size=11, fill=INK, weight="600" if col != MUTED else "normal"))
        s.append(txt(AX + AW, y, f"{n:,} records · {nstr} string{'s' if nstr > 1 else ''}",
                     size=9, fill=MUTED, anchor="end"))
        x, rowy = AX, y + 9
        for c, t in sorted(items, reverse=True):
            w = scale(c)
            if x + w > AX + AW:
                x, rowy = AX, rowy + 19
            s.append(f'<rect x="{x:.1f}" y="{rowy:.1f}" width="{w:.1f}" height="15" '
                     f'fill="{col}"/>')
            fits = int((w - 7) / 4.6)
            if fits >= 4:
                s.append(txt(x + 4, rowy + 11, t[:fits], size=7.5, fill="#ffffff"))
            x += w + 3
        y = rowy + 34
    s += wrap(AX, y + 4,
              "Area and volume are not the same dimension and nothing marks which is which. "
              "SACFORN is the British ordinal abundance scale and has no numeric meaning at "
              "all. DNA sequence reads are not organisms — a read count scales with PCR "
              "amplification. And the single widest mark in the file is DNA sequence reads.",
              size=10.5, fill=INK2, chars=96)

    BX, BY, BW_ = 530, 250, 320
    s.append(txt(BX, BY - 44, "it is not a tidying problem", size=12.5, fill=INK, weight="600"))
    s.append(txt(BX, BY - 28, "distinct strings, before and after normalising", size=10.5, fill=MUTED))
    low = {t.lower().rstrip("s").strip() for t in types}
    for i, (lab, n, col) in enumerate((("as published", len(types), RED),
                                       ("lowercased, depluralised", len(low), AMBER),
                                       ("genuinely distinct kinds", len(order), GREEN))):
        yy = BY + i * 74
        s.append(txt(BX, yy, lab, size=11, fill=INK))
        s.append(f'<rect x="{BX}" y="{yy+8:.1f}" width="{max(BW_*n/len(types),2):.1f}" '
                 f'height="26" fill="{col}"/>')
        s += halo(BX + max(BW_ * n / len(types), 2) + 8, yy + 26, str(n), size=14, fill=col,
                  weight="700")
    s += wrap(BX, BY + 3 * 74 + 4,
              "Five strings disappear to case and plurals. The rest are real differences in what "
              "was measured, so there is no clean number underneath waiting to be recovered.",
              size=10.5, fill=INK2, chars=52)
    s += wrap(BX, BY + 3 * 74 + 56,
              "Two records reading 12 mean twelve fish, twelve grams per square metre, or twelve "
              "thousand sequencing reads.", size=11, fill=INK, chars=50)

    # The third panel was a grey box containing the sentence "Length of longest arm in
    # millimeters" and two paragraphs about it. A box with prose in it is not a chart, and the
    # string it was built around is already a labelled row in panel A. The consequence it
    # argued for now sits under panel B, where the collapse it follows from is drawn.
    s += wrap(BX, BY + 3 * 74 + 104,
              "So biomass by latitude and longitude is not answerable here, and the blocker is "
              "not coverage — the quantities are incommensurable by construction. Restricting "
              "to one unit string would make them addable and throw away most of the data.",
              size=10.5, fill=INK2, chars=52)

    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"OBIS v3, fetched 2026-09-18. {d['sampled']:,} records sampled {d['per']} at a "
              f"time across {len(d['taxa'])} taxa, not from the head of the index, so no single "
              f"dataset's convention dominates. It supports a claim about the VARIETY of units, "
              f"not about the share of 229 million records carrying any one. Method in the recipe.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {len(types)} strings -> {len(low)} normalised -> {len(order)} kinds")
    for k in order:
        print(f"    {k:<26}{groups[k][1]:>3} strings, {groups[k][0]:>5} records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
