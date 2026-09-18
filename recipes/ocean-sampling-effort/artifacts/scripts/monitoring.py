#!/usr/bin/env python3
"""Threat status buys a little monitoring. Record count buys all of it.

    python3 chart-11-redlist.py

`checklist/redlist` is the only join in the API carrying an outside judgement -- the IUCN threat
category -- so it is the one place this register can be turned on a named decision: given that
someone has decided a species is threatened, can OBIS tell you how it is doing?

**For about a third, no.** 508 of 1,617 threatened species have no record at all since 2016, on
a median of 48 records in the whole file. **The comparison reverses the obvious story**, though.
Against non-threatened species from the same families, matched on log10(total records), the
threatened ones are *better* monitored in every stratum that matters: 72% unseen against 85% at
1-9 records, 27% against 44% at 10-99, 4% against 8% at 100-999. Concern follows attention.

**What actually decides it is record count, and nothing else comes close.** A species with fewer
than ten records has a 72% chance of not appearing in a decade; one with over a thousand has a
1% chance. That is a seventy-fold swing across the axis that threat status moves by a fifth.
525 of the 1,617 threatened species sit in the bottom bracket.

**EX is the positive control.** Fourteen species are listed Extinct, and 85.7% of them have no
record since 2016, median record count 0, median last sighting 1982. If the measure could not
find the extinct ones it would not be measuring anything.

**The gap is where the charisma is not.** Seabirds lose 6% of their threatened species from the
last decade and marine mammals 10%; sea snails lose **67%** and seagrasses 52%. Teleost fish
contribute the largest absolute number, 160 species.

**The caveat is the recipe's oldest.** An absent record is not an absent animal. This measures
whether the register saw the species, and a thin-record species may be unwatched, unreachable or
genuinely gone, which this cannot separate.
"""
import json, math, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "monitoring.svg")

# The register stores Latin class names and every other figure in this recipe says "seabirds"
# and "sea snails". The first version of the right-hand panel printed Aves and Gastropoda
# while its own caption beneath said seabirds and sea snails, so the reader had to translate
# the chart into the words explaining it.
COMMON = {
    "Aves": "seabirds", "Mammalia": "marine mammals", "Elasmobranchii": "sharks and rays",
    "Hexacorallia": "corals", "Teleostei": "ray-finned fish", "Magnoliopsida": "seagrasses",
    "Bivalvia": "clams and mussels", "Gastropoda": "sea snails", "Anthozoa": "corals",
    "Actinopterygii": "ray-finned fish", "Demospongiae": "sponges",
    "Malacostraca": "crabs and shrimp", "Polychaeta": "bristle worms",
    "Holothuroidea": "sea cucumbers", "Echinoidea": "sea urchins", "Asteroidea": "sea stars",
}
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#7d8a96"


def main():
    d = json.load(open(os.path.join(HERE, "..", "data", "redlist.json")))
    t, c = d["threatened"], d["control"]
    YR = d["recent_from"]

    def strat(rows):
        b = defaultdict(list)
        for x in rows:
            b[int(math.log10(max(x["dated"], 1)))].append(x)
        return b
    bt, bc = strat(t), strat(c)
    ks = [k for k in sorted(set(bt) | set(bc)) if len(bt.get(k, [])) >= 20]

    W, H = 1200, 900
    s = plate.open_svg(W, H, "Threat status buys a little monitoring. "
                             "Record count buys all of it.")
    fr, _ = plate.frame(W, 62,
                        who="anyone planning to monitor threatened marine species from "
                            "occurrence data",
                        decide="whether this register can track a named species at all",
                        wrong="the thin-record species are absent from the sea rather than "
                              "absent from the register")
    s += fr

    # ---- left: the matched comparison, inside strata, because the raw contrast is rarity.
    # One ROW per record bracket, not a connected line. Drawn as a line it read as a survival
    # curve over time -- the horizontal axis is record count, not years, and a descending
    # series on a log axis says "decay" to every reader. Bands are not a sequence.
    AX, AY, AH, AW = 28, 258, 330, 470
    s.append(txt(AX, AY - 56, f"share with no record since {YR}", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(AX, AY - 40, "one row per bracket of total records — the rows are groups of "
                              "species, not a sequence", size=10.5, fill=MUTED))
    x0, pw = AX + 116, AW - 176
    px = lambda f: x0 + pw * f
    rh = (AH - 40) / len(ks)
    for f in (0, .25, .5, .75, 1.0):
        s.append(f'<line x1="{px(f):.1f}" y1="{AY-4:.1f}" x2="{px(f):.1f}" '
                 f'y2="{AY+len(ks)*rh:.1f}" stroke="{GRID}"/>')
        s.append(txt(px(f), AY + len(ks) * rh + 16, f"{f*100:.0f}%", size=9, fill=MUTED,
                     anchor="middle"))
    s.append(txt(AX, AY + len(ks) * rh + 32,
                 f"share of the bracket's species with no record since {YR}",
                 size=9.5, fill=MUTED))
    for i, k in enumerate(ks):
        y = AY + i * rh + rh / 2
        tv, cv = bt.get(k, []), bc.get(k, [])
        ft = sum(1 for x in tv if x["recent"] == 0) / len(tv)
        fc = sum(1 for x in cv if x["recent"] == 0) / len(cv) if cv else None
        lab = (f"{10**k:,}–{10**(k+1)-1:,}" if k < 4
               else f"{10**k//1000:,}k–{(10**(k+1)-1)//1000:,}k")
        s.append(txt(AX + 108, y - 1, lab, size=9.5, fill=INK2, anchor="end"))
        s.append(txt(AX + 108, y + 11, f"n={len(tv)}", size=8.5, fill=MUTED, anchor="end"))
        if fc is not None:
            s.append(f'<line x1="{px(min(ft,fc)):.1f}" y1="{y:.1f}" x2="{px(max(ft,fc)):.1f}" '
                     f'y2="{y:.1f}" stroke="{MUTED}" stroke-width="1.2"/>')
            s.append(f'<circle cx="{px(fc):.1f}" cy="{y:.1f}" r="4.6" fill="none" '
                     f'stroke="{SLATE}" stroke-width="1.8"/>')
        s.append(f'<circle cx="{px(ft):.1f}" cy="{y:.1f}" r="4.6" fill="{RED}"/>')
        s += halo(px(max(ft, fc or 0)) + 10, y + 3, f"{ft:.0%} vs {fc:.0%}" if fc is not None
                  else f"{ft:.0%}", size=9, fill=INK2)
    ly = AY + len(ks) * rh + 52
    s.append(f'<circle cx="{x0+5:.1f}" cy="{ly-3.5:.1f}" r="4.6" fill="{RED}"/>')
    s.append(txt(x0 + 16, ly, "IUCN-threatened", size=9.5, fill=INK2))
    s.append(f'<circle cx="{x0+135:.1f}" cy="{ly-3.5:.1f}" r="4.6" fill="none" '
             f'stroke="{SLATE}" stroke-width="1.8"/>')
    s.append(txt(x0 + 146, ly, "matched control, same families", size=9.5, fill=INK2))
    s += wrap(AX, ly + 22,
              f"Read down, not across: each row is a different group of species, sorted by how "
              f"many records they hold. The threatened dot is left of its control in every row "
              f"that matters, but the rows themselves span 72% to 1% — so how many records a "
              f"species already had decides this, and being listed shifts it a little. "
              f"{sum(1 for x in t if x['dated'] < 10):,} of {len(t):,} threatened species are "
              f"in the top row.",
              size=10.5, fill=INK2, chars=76)

    # ---- right: where the gap is, with the extinct listing as the anchor
    BX, BY, BH, BW = 560, 252, 330, 470
    s.append(txt(BX, BY - 50, "and which groups it falls on", size=12.5, fill=INK, weight="600"))
    s.append(txt(BX, BY - 34, "area is the number of threatened species in the class",
                 size=10.5, fill=MUTED))
    by = defaultdict(list)
    for x in t:
        by[x["class"] or "unknown"].append(x)
    rows = sorted(((k, v) for k, v in by.items() if len(v) >= 15 and k != "unknown"),
                  key=lambda kv: sum(1 for x in kv[1] if x["recent"] == 0) / len(kv[1]))
    bx0, bpw = BX + 130, BW - 176
    bpx = lambda f: bx0 + bpw * f
    rh = BH / (len(rows) + 1)
    for f in (0, .25, .5, .75):
        s.append(f'<line x1="{bpx(f):.1f}" y1="{BY-4:.1f}" x2="{bpx(f):.1f}" '
                 f'y2="{BY+len(rows)*rh:.1f}" stroke="{GRID}"/>')
        s.append(txt(bpx(f), BY + len(rows) * rh + 16, f"{f*100:.0f}%", size=9, fill=MUTED,
                     anchor="middle"))
    mxn = max(len(v) for _, v in rows)
    for i, (k, v) in enumerate(rows):
        y = BY + i * rh + rh / 2
        sh = sum(1 for x in v if x["recent"] == 0) / len(v)
        rad = 4 + 13 * (len(v) / mxn) ** .5
        col = GREEN if sh < .2 else (BLUE if sh < .45 else RED)
        s.append(f'<line x1="{bpx(0):.1f}" y1="{y:.1f}" x2="{bpx(sh):.1f}" y2="{y:.1f}" '
                 f'stroke="{col}" stroke-width="1.2" stroke-opacity="0.5"/>')
        s.append(f'<circle cx="{bpx(sh):.1f}" cy="{y:.1f}" r="{rad:.1f}" fill="{col}" '
                 f'fill-opacity="0.35" stroke="{col}" stroke-width="1.4"/>')
        s.append(txt(BX + 122, y + 3, COMMON.get(k, k), size=9.5, fill=INK2, anchor="end"))
        s += halo(bpx(sh) + rad + 6, y + 3,
                  f"{sum(1 for x in v if x['recent'] == 0)} of {len(v)}", size=9, fill=col)
    ex = [x for x in t if x["category"] == "EX"]
    exs = sum(1 for x in ex if x["recent"] == 0) / len(ex)
    y = BY + len(rows) * rh + rh / 2
    s.append(f'<line x1="{bpx(0):.1f}" y1="{y:.1f}" x2="{bpx(exs):.1f}" y2="{y:.1f}" '
             f'stroke="{INK2}" stroke-width="1.2" stroke-dasharray="3 3"/>')
    s.append(f'<circle cx="{bpx(exs):.1f}" cy="{y:.1f}" r="5" fill="none" stroke="{INK2}" '
             f'stroke-width="1.6"/>')
    s.append(txt(BX + 122, y + 3, "listed Extinct", size=9.5, fill=INK2, anchor="end",
                 weight="600"))
    s += halo(bpx(exs) + 11, y + 3, f"{sum(1 for x in ex if x['recent'] == 0)} of {len(ex)}",
              size=9, fill=INK2)
    s.append(txt(BX, BY + len(rows) * rh + 32,
                 f"share of the class's threatened species with no record since {YR}",
                 size=9.5, fill=MUTED))
    s += wrap(BX, BY + BH + 54,
              "Seabirds lose 6% of their threatened species from the last decade and marine "
              "mammals 10%; sea snails lose 67% and seagrasses 52%. Teleost fish contribute the "
              "largest absolute number at 160. The dashed row is the fourteen species IUCN "
              "lists as Extinct, at 85.7% — the control that shows the measure can find an "
              "animal that is actually gone, median last sighting 1982.",
              size=10.5, fill=INK2, chars=76)

    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              "OBIS v3 checklist/redlist and statistics/years, fetched 2026-09-18. IUCN does not "
              "assess from OBIS — assessments draw on literature, targeted survey and expert "
              "judgement — so a Critically Endangered species with two records here is not an "
              "assessment resting on two observations; the question runs the other way. OBIS "
              "stamps `category` only for CR, EN, VU and EX: Least Concern, Near Threatened and "
              "never-assessed all return null, so the controls are drawn from same-family "
              "species with no category and matched on log10 records, not from 'unassessed' "
              "species, which this field cannot identify.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    threatened {sum(1 for x in t if x['recent']==0)/len(t):.1%} unseen, "
          f"control {sum(1 for x in c if x['recent']==0)/len(c):.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
