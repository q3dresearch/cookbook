#!/usr/bin/env python3
"""The two most-solved proteins on Earth are both from one virus.

    python3 chart-3-targets.py

Grouping every entry by the UniProt accession of its polymer gives the field's actual target
list. The top of it is not what a textbook would predict.

**`P0DTD1`, the SARS-CoV-2 replicase polyprotein, has 3,722 entries. `P0DTC2`, its spike, has
2,267.** Third is beta-2-microglobulin at 1,401 and fourth is lysozyme at 1,393 -- the classics
are still there, and a virus first sequenced in January 2020 is now ahead of both.

**It is not a 2020 spike.** The replicase is still drawing 582 depositions in 2024, four years
on, because that polyprotein contains the main protease and the field is doing antiviral
chemistry against it. The spike peaked in 2022 and fell away; the replicase did not.

**Which makes deposition volume over 2020-2024 a statement about subject, not capacity.** Any
reading of those years as the field getting faster has to subtract a pandemic first.

**But the list is not unusually steep.** Ranked against entry count on log scales it is an
ordinary power law, R² 0.88 fitted on ranks 10-200, and the replicase sits only **1.6x above
that line**.

*A defect found while rebuilding this panel:* the terms facet returns the top 200 accessions by
count but **not in count order** -- 35 of the 200 positions come back out of sequence. The
earlier version of this figure plotted facet order on an axis labelled "rank". Sorting first
moves the fit from R² 0.77 to 0.88, so the shape being described was partly the API's ordering. The notable thing about the head is *which* proteins are in it, not how far they
stand out -- which is the opposite of what the sorted bar this panel used to be implied.

200 accessions carry 95,377 entity-entries. A count of PDB entries is a count of *attention* --
the same protein re-solved with a different ligand is two entries -- so "we have 260,089
structures" and "we know 260,089 proteins" are very different statements, and only the first is
true.

**One thing this cannot do.** An accession is one polymer; an entry with several distinct
chains appears under each. The per-accession counts are therefore entity-entries and cannot be
added across accessions to recover an entry count, for the same reason the author facet could
not be summed in figure 2.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdb as P, plate                                                   # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "3-targets.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
COVID = {"P0DTD1", "P0DTC2", "P0DTC9"}


def main():
    d = P.load()
    # the terms facet returns the top 200 by count but does NOT return them in
    # count order — 35 of 200 positions come back out of sequence. An axis
    # labelled "rank" has to be sorted here or it is not rank.
    acc = sorted(d["accessions"], key=lambda t: -t[1])
    tgt = d["target_by_year"]

    W, H = 1200, 770
    s = plate.open_svg(W, H, "The two most-solved proteins on Earth are both from one virus")
    fr, _ = plate.frame(W, 62,
                        who="anyone reading deposition volume as the field's capacity",
                        decide="whether a busy year is more structural biology or one subject",
                        wrong="the SARS-CoV-2 targets fall away after 2021 like a news cycle")
    s += fr

    # ---- left: rank against count, both logged, so the shape of the head is readable
    AX, AY, AH, AW = 28, 268, 340, 470
    s.append(txt(AX, AY - 56, "the target list is an ordinary power law", size=12.5,
                 fill=INK, weight="600"))
    s.append(txt(AX, AY - 40, "rank against entries, both on log scales — a straight line "
                              "means a power law", size=10.5, fill=MUTED))
    x0, pw = AX + 44, AW - 74
    rx = lambda i: x0 + pw * (math.log10(i + 1) / math.log10(len(acc)))
    vlo, vhi = 150, 5000
    ry = lambda v: (AY + AH - 46 - (AH - 76)
                    * ((math.log10(max(v, vlo)) - math.log10(vlo))
                       / (math.log10(vhi) - math.log10(vlo))))
    for v in (200, 500, 1000, 2000, 5000):
        s.append(f'<line x1="{x0:.1f}" y1="{ry(v):.1f}" x2="{rx(len(acc)-1):.1f}" '
                 f'y2="{ry(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(x0 - 7, ry(v) + 3, f"{v:,}", size=9, fill=MUTED, anchor="end"))
    for i_ in (0, 4, 19, 99, 199):
        s.append(f'<line x1="{rx(i_):.1f}" y1="{ry(vlo):.1f}" x2="{rx(i_):.1f}" '
                 f'y2="{ry(vlo)+5:.1f}" stroke="{MUTED}"/>')
        s.append(txt(rx(i_), AY + AH - 30, str(i_ + 1), size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, AY + AH - 14, "rank among the 200 most-solved proteins (log scale)",
                 size=9.5, fill=MUTED))

    # fitted away from the head, so the head can be measured against it
    lx = [math.log10(i_ + 1) for i_ in range(len(acc))]
    ly_ = [math.log10(c) for _, c in acc]
    X, Y = lx[9:], ly_[9:]
    nn = len(X)
    mxx, myy = sum(X) / nn, sum(Y) / nn
    bb = sum((a - mxx) * (y - myy) for a, y in zip(X, Y)) / sum((a - mxx) ** 2 for a in X)
    aa = myy - bb * mxx
    r2 = 1 - (sum((y - (aa + bb * x)) ** 2 for x, y in zip(X, Y))
              / sum((y - myy) ** 2 for y in Y))
    fitpts = [(rx(i_), ry(10 ** (aa + bb * math.log10(i_ + 1)))) for i_ in range(len(acc))]
    s.append('<path d="' + " ".join(("M" if i_ == 0 else "L") + f"{a:.1f},{b:.1f}"
                                    for i_, (a, b) in enumerate(fitpts))
             + f'" fill="none" stroke="{INK2}" stroke-width="1.6" stroke-dasharray="5 3"/>')
    s += halo(rx(40), ry(10 ** (aa + bb * math.log10(41))) + 17,
              f"fitted on ranks 10–200, R² {r2:.2f}", size=9, fill=INK2, anchor="middle")

    for i_, (a, c) in enumerate(acc):
        col = RED if a in COVID else SLATE
        s.append(f'<circle cx="{rx(i_):.1f}" cy="{ry(c):.1f}" r="{3.4 if a in COVID else 2.1:.1f}" '
                 f'fill="{col}" fill-opacity="{1.0 if a in COVID else 0.55}"/>')
    LAB = {"P0DTD1": "SARS-CoV-2 replicase", "P0DTC2": "SARS-CoV-2 spike",
           "P61769": "β2-microglobulin", "P00698": "lysozyme"}
    for i_, (a, c) in enumerate(acc[:4]):
        pred = 10 ** (aa + bb * math.log10(i_ + 1))
        extra = f" · {c/pred:.1f}x the fit" if i_ < 2 else ""
        s += halo(rx(i_) + 9, ry(c) + 3.5 + (0 if i_ % 2 == 0 else 11),
                  f"{LAB.get(a, a)} · {c:,}{extra}", size=9.5,
                  fill=RED if a in COVID else INK2, weight="700" if a in COVID else "400")
    s += wrap(AX, AY + AH + 10,
              f"The 200 most-solved proteins carry {sum(c for _, c in acc):,} entity-entries. "
              f"The distribution is an unremarkable power law and the replicase sits only "
              f"{acc[0][1] / 10 ** (aa + bb * 0):.1f}x above it — so the notable thing about "
              f"the head of this list is which proteins are in it, not how far they stand out. "
              f"A count of entries is a count of attention: the same protein re-solved with a "
              f"different ligand is two entries.",
              size=10.5, fill=INK2, chars=76)

    # ---- right: and it is not a news cycle
    BX, BY, BH, BW = 590, 268, 340, 470
    s.append(txt(BX, BY - 56, "and the virus did not go away", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(BX, BY - 40, "depositions per year for the top targets", size=10.5,
                 fill=MUTED))
    yrs = list(range(2015, 2026))
    bx0, bpw = BX + 44, BW - 90
    bpx = lambda y: bx0 + bpw * ((y - yrs[0]) / (yrs[-1] - yrs[0]))
    mx2 = 800
    bpy = lambda v: BY + BH - 46 - (BH - 76) * (min(v, mx2) / mx2)
    for v in (0, 200, 400, 600, 800):
        s.append(f'<line x1="{bx0:.1f}" y1="{bpy(v):.1f}" x2="{bpx(yrs[-1]):.1f}" '
                 f'y2="{bpy(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(bx0 - 7, bpy(v) + 3, f"{v:,}", size=9, fill=MUTED, anchor="end"))
    for y in range(2016, 2026, 2):
        s.append(txt(bpx(y), BY + BH - 30, str(y), size=9, fill=MUTED, anchor="middle"))
    s.append(txt(BX, BY + BH - 14, "year the structure was deposited", size=9.5, fill=MUTED))
    placed2 = []
    for a, v in sorted(tgt.items(), key=lambda kv: -kv[1]["total"]):
        by = {int(k): n for k, n in v["by_year"].items()}
        if v["total"] < 340:
            continue
        col = RED if a in COVID else SLATE
        pts = [(bpx(y), bpy(by.get(y, 0))) for y in yrs]
        s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{p:.1f},{q:.1f}"
                                        for i, (p, q) in enumerate(pts))
                 + f'" fill="none" stroke="{col}" stroke-width="2.1" '
                 f'stroke-opacity="{1 if a in COVID else 0.5}"/>')
        ly = pts[-1][1]
        while any(abs(ly - q) < 12 for q in placed2):
            ly -= 12
        placed2.append(ly)
        if a in COVID or v["total"] > 1200:
            s += halo(bpx(yrs[-1]) + 6, ly + 3, v["label"], size=9,
                      fill=col, )
    s += wrap(BX, BY + BH + 10,
              "The spike peaked in 2022 and fell away. The replicase polyprotein did not — it "
              "was still drawing 582 depositions in 2024, because that polyprotein contains "
              "the main protease and the field is doing antiviral chemistry against it. Every "
              "grey line is a classic target running flat underneath.",
              size=10.5, fill=INK2, chars=76)

    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"RCSB PDB search API, fetched {d['fetched']}, grouped on the UniProt accession "
              f"of the polymer entity. An accession is one polymer and an entry with several "
              f"distinct chains appears under each, so these are entity-entries and cannot be "
              f"added across accessions to recover an entry count — the same multi-valued trap "
              f"as the author facet in figure 2. Deposition date throughout. The facet returns "
              f"the 200 largest, so the tail beyond rank 200 is not drawn and no Gini or "
              f"cumulative share is computed from a truncated list. It also returns them "
              f"— 35 of the 200 — out of count order, so they are sorted here before "
              f"anything is called a rank; the earlier version of this figure did not, which "
              f"moved the fit from R² 0.77 to 0.88.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for a, c in acc[:4]:
        print(f"    {a}  {LAB.get(a, ''):<22}{c:>6,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
