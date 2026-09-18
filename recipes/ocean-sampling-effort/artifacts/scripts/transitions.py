#!/usr/bin/env python3
"""The label moves mostly because knowledge moves. Except for the corals.

    python3 chart-14-transitions.py

OBIS's redlist endpoint has no temporal field, so species entering or leaving threatened status
looked unanswerable. It is not: GBIF mirrors the IUCN Red List as Darwin Core archives under
CC-BY, and the directory holds nine dated files covering Red List versions **2020-3 to 2026-1**.
Diffing them gives 7,517 category changes across eight distinct states.

**One of the nine files is an exact republication.** 2022-1 and 2022-1_2022-08-12 differ in
bytes and agree on every category, so the series is eight distinct states rather than nine. A
second pair very nearly is: 2024-2 and 2025-1 differ by a **single species**. An earlier draft
called both republications and said seven states; correcting the join key -- from
`scientificName`, which carries the authorship, to genus plus epithet -- moved that pair from
zero changes to one, and `verify.py` caught the stale sentence rather than a reader.

**The largest single flow is not a decline.** 548 species entered threatened status **from Data
Deficient** -- a first real assessment, not a fall -- and 186 left threatened *to* Data
Deficient, which is not safety. Against that, 938 left to Least Concern and 653 to Near
Threatened. IUCN separates a genuine status change from one caused by better knowledge or
revised taxonomy, and publishes that distinction as the Red List Index; **the flag is not in the
Darwin Core archive**, so nothing here can make that split. This measures the label moving, and
the label moves for reasons that are not the animal.

**The marine subset runs the other way, and one order explains it.** Of 510 changes matching a
name OBIS holds, 68 improved and 351 worsened. But **233 of the 351 are Hexacorallia** and 273
of them landed in the single 2024-2 release: the Atlantic coral reassessment after disease and
bleaching, arriving as one event. Drop the corals and marine goes from 5:1 worse to 1.7:1.
A category moving for 233 species on one day is one decision, not 233 observations.

**What survives.** Sharks and rays are the second block, 60 worsening and spread across
releases. The green turtle, Chelonia mydas, moved EN to LC -- three steps, the largest marine
improvement in the file.
"""
import collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "transitions.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
ORDER = ["LC", "NT", "VU", "EN", "CR", "EW", "EX", "DD"]
RANK = {c: i for i, c in enumerate(["LC", "NT", "VU", "EN", "CR", "EW", "EX"])}


def main():
    d = json.load(open(os.path.join(HERE, "..", "data", "redlisthistory.json")))
    rl = json.load(open(os.path.join(HERE, "..", "data", "redlist.json")))
    cls = {x["name"]: x.get("class") for x in rl["threatened"]}
    cls.update({x["name"]: x.get("class") for x in rl["control"]})
    moves = [(m, t["to_version"]) for t in d["transitions"] for m in t["moves"]]

    W, H = 1200, 830
    s = plate.open_svg(W, H, "The label moves mostly because knowledge moves. "
                             "Except for the corals.")
    fr, _ = plate.frame(W, 62,
                        who="anyone reading a Red List change as a change in the animal",
                        decide="whether a category move is a new assessment or a new condition",
                        wrong="the coral block is 233 separate declines rather than one "
                              "reassessment")
    s += fr

    # ---- left: every flow, as area. Counts typed into boxes would be a spreadsheet.
    AX, AY, AH, AW = 28, 270, 340, 470
    s.append(txt(AX, AY - 62, "where the category moves, all taxa", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(AX, AY - 46, f"{len(moves):,} changes across eight distinct Red List states, "
                              "2020-3 to 2026-1", size=10.5, fill=MUTED))
    cnt = collections.Counter((m["from"], m["to"]) for m, _ in moves)
    x0 = AX + 40
    cw = (AW - 62) / len(ORDER)
    rhh = (AH - 54) / len(ORDER)
    mx = max(cnt.values())
    for j, c in enumerate(ORDER):
        s.append(txt(x0 + j * cw + cw / 2, AY - 14, c, size=9.5, fill=MUTED, anchor="middle"))
    s.append(txt(x0 + (AW - 62) / 2, AY - 28, "to", size=9.5, fill=INK2, anchor="middle"))
    for i, a in enumerate(ORDER):
        y = AY + i * rhh + rhh / 2
        s.append(txt(AX + 32, y + 3, a, size=9.5, fill=MUTED, anchor="end"))
        for j, b in enumerate(ORDER):
            n = cnt.get((a, b), 0)
            if not n:
                continue
            r = 2 + 15 * (n / mx) ** .5
            ra, rb = RANK.get(a), RANK.get(b)
            col = (SLATE if a == "DD" or b == "DD"
                   else RED if (ra is not None and rb is not None and rb > ra)
                   else GREEN)
            s.append(f'<circle cx="{x0 + j*cw + cw/2:.1f}" cy="{y:.1f}" r="{r:.1f}" '
                     f'fill="{col}" fill-opacity="0.45" stroke="{col}" stroke-width="1.1"/>')
            if n >= 300:
                s += halo(x0 + j * cw + cw / 2, y + 3, f"{n}", size=8.5, fill=INK,
                          anchor="middle")
    s.append(f'<text transform="translate({AX+10},{AY+AH/2-20}) rotate(-90)" font-size="9.5" '
             f'fill="{INK2}" text-anchor="middle">from</text>')
    lx, ly = AX, AY + AH - 36
    for lab, col in (("to a worse category", RED), ("to a better one", GREEN),
                     ("Data Deficient at one end", SLATE)):
        s.append(f'<circle cx="{lx+5:.1f}" cy="{ly-3.5:.1f}" r="5" fill="{col}" '
                 f'fill-opacity="0.45" stroke="{col}" stroke-width="1.1"/>')
        s.append(txt(lx + 15, ly, lab, size=9.5, fill=INK2))
        lx += 150 if col != GREEN else 125
    s += wrap(AX, AY + AH + 4,
              "The single biggest flow is Data Deficient into Vulnerable and Endangered: 548 "
              "species entered threatened status from DD, which is a first real assessment and "
              "not a fall, and 186 left threatened to DD, which is not safety. IUCN publishes "
              "whether a change is genuine or a knowledge correction — that flag is not in this "
              "archive, so this figure cannot make the split and does not claim to.",
              size=10.5, fill=INK2, chars=76)

    # ---- right: the marine subset, by release, so one event cannot pass as a trend
    BX, BY, BH, BW = 560, 270, 340, 470
    s.append(txt(BX, BY - 62, "and the marine subset, by release", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(BX, BY - 46, "one mark per species; vertical position is how many categories "
                              "it moved", size=10.5, fill=MUTED))
    mar = [(m, v) for m, v in moves if m["name"] in cls
           and m["from"] in RANK and m["to"] in RANK]
    vers = [t["to_version"] for t in d["transitions"]]
    bx0, bpw = BX + 40, BW - 70
    # Releases are NOT evenly spaced and the first version drew them as if they were: the
    # mirror holds nothing between 2022-1 and 2024-2, so a two-and-a-half year hole was the
    # same width as a six-month step, and the biggest block of change sat right beside it.
    # Slots are weighted by the real interval and the hole is marked on the axis.
    def _yr(v):
        a, b = v.split("_")[0].split("-")[:2]
        return int(a) + (int(b) - 1) / 3.0
    prev, slots, acc = _yr(vers[0]) - 0.34, [], 0.0
    for v in vers:
        acc += min(max(_yr(v) - prev, 0.34), 1.3)      # capped so the hole widens without
        slots.append(acc)                              # squeezing every other release to a line
        prev = _yr(v)
    span = slots[-1] or 1
    vpx = {v: bx0 + bpw * (slots[i] / span) for i, v in enumerate(vers)}
    gap = max(range(1, len(vers)), key=lambda i: slots[i] - slots[i - 1])
    gx0, gx1 = vpx[vers[gap - 1]], vpx[vers[gap]]
    s.append(f'<rect x="{gx0+4:.1f}" y="{BY-6:.1f}" width="{gx1-gx0-8:.1f}" '
             f'height="{BH-50:.1f}" fill="{AMBER}" fill-opacity="0.07"/>')
    s += halo((gx0 + gx1) / 2, BY - 12, "no release on the mirror", size=8.5, fill=AMBER,
              anchor="middle")
    LOV, HIV = -4.4, 3.4
    py = lambda v: BY + BH - 60 - (BH - 90) * ((v - LOV) / (HIV - LOV))
    for g_ in range(-4, 4):
        s.append(f'<line x1="{bx0-14:.1f}" y1="{py(g_):.1f}" x2="{bx0+bpw+14:.1f}" '
                 f'y2="{py(g_):.1f}" stroke="{GRID if g_ else INK2}" '
                 f'stroke-width="{1.4 if g_ == 0 else 1}"/>')
        s.append(txt(bx0 - 18, py(g_) + 3, f"{g_:+d}" if g_ else "0", size=9, fill=MUTED,
                     anchor="end"))
    for v, x in vpx.items():
        # a republication carries the same version string as its predecessor; saying so beats
        # printing "2022-1" twice and looking like a mistake
        dup = sum(1 for w in vers if w.split("_")[0] == v.split("_")[0]) > 1
        s.append(txt(x, BY + BH - 44, v.split("_")[0], size=8.5, fill=MUTED, anchor="middle"))
        if dup and "_" in v:
            s.append(txt(x, BY + BH - 34, "republished", size=7.5, fill=MUTED,
                         anchor="middle"))
    buck = collections.defaultdict(int)
    for m, v in mar:
        delta = RANK[m["from"]] - RANK[m["to"]]
        k = (v, delta)
        buck[k] += 1
        i = buck[k] - 1
        coral = (cls.get(m["name"]) or "") == "Hexacorallia"
        shark = (cls.get(m["name"]) or "") == "Elasmobranchii"
        col = AMBER if coral else (BLUE if shark else (GREEN if delta > 0 else SLATE))
        s.append(f'<circle cx="{vpx[v] + ((i % 12) - 5.5) * 3.0:.1f}" '
                 f'cy="{py(delta) + (i // 12) * 3.0:.1f}" r="2.1" fill="{col}" '
                 f'fill-opacity="0.7"/>')
    lx2, ly2 = BX, BY + BH - 26
    for lab, col in (("hard corals", AMBER), ("sharks and rays", BLUE),
                     ("improved", GREEN), ("everything else", SLATE)):
        s.append(f'<circle cx="{lx2+4:.1f}" cy="{ly2-3.5:.1f}" r="3.4" fill="{col}" '
                 f'fill-opacity="0.8"/>')
        s.append(txt(lx2 + 12, ly2, lab, size=9.5, fill=INK2))
        lx2 += 104 if col in (AMBER, GREEN) else 132
    s.append(txt(BX, BY - 30, "categories gained above the line, lost below", size=9,
                 fill=MUTED))
    s += wrap(BX, BY + BH + 4,
              "233 of the 351 marine worsenings are hard corals and 273 of them land in the "
              "2024-2 release alone — the Atlantic reassessment after disease and bleaching, "
              "arriving as one decision on one day. Drop the corals and marine goes from 5:1 "
              "worse to 1.7:1. Sharks and rays are the second block, 60 species and spread "
              "across releases. The largest marine improvement is the green turtle, Chelonia "
              "mydas, Endangered to Least Concern.",
              size=10.5, fill=INK2, chars=76)

    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              "IUCN Red List Darwin Core archives mirrored by GBIF at "
              "hosted-datasets.gbif.org/datasets/iucn/, CC-BY, fetched 2026-09-19; nine dated "
              "files, of which two are republications of an earlier version. Fields are located "
              "by term from each archive's own meta.xml because threatStatus sits at index 4 in "
              "2020-3 and index 5 in 2026-1. The join key is genus plus specificEpithet: IUCN "
              "writes authorship into scientificName and OBIS does not, and joining on that "
              "matched 0 of 7,517 changes. The mirror has no release between 2022-1 and 2024-2, "
              "so that pair spans several real releases and no change in it can be dated to one.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {len(moves):,} changes, {len(mar):,} marine; "
          f"{sum(1 for m,_ in mar if RANK[m['from']]>RANK[m['to']])} improved, "
          f"{sum(1 for m,_ in mar if RANK[m['from']]<RANK[m['to']])} worsened")
    return 0


if __name__ == "__main__":
    sys.exit(main())
