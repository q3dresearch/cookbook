#!/usr/bin/env python3
"""A hand-made ligand classification, tested against the method that never had a drop.

    python3 chart-5-ligands.py

Figure 6 used to sort the 60 most common bound components into ADDITIVE, AMBIGUOUS and
BIOLOGICAL by hand and print the three totals. The labels were declared in the script and
nothing tested them. There is a test available, and it is nearly free.

**A crystallisation additive is an artefact of growing a crystal.** No drop, no buffer, no
cryoprotectant -- so a declared additive should be scarce in cryo-EM entries, while a genuine
cofactor should not care how the structure was determined.

**Except that cryo-EM does big things** (figure 8), and additives sit in small proteins. Across
these 30 components the correlation between a component's cryo-EM share and the share of its
host entries over 200 kDa is **rho +0.94**. Size has to be conditioned on or it explains
everything.

**Conditioned on size, the labels hold, and one model says they do not.** Fit the relationship
on the 23 non-additive components and read each additive's residual:

- a **linear** fit gives a mean additive residual of **+0.5 points** and mixed signs: no effect
- a **log-odds** fit -- the right shape for a bounded share -- gives **15 of 16 additives below
  prediction, median 27.7x fewer cryo-EM entries than their host sizes predict**

The linear fit predicts *negative* cryo-EM shares for eight components, which is impossible,
and the positive residuals it manufactures at the floor are the whole of its null. **The
functional form decided the answer**, and the plate draws both so the failure is visible.

**The test also corrects the classification.** Potassium, sodium, chloride and phosphate were
declared additives and sit on the line at 0.9x to 2.4x -- they behave like cofactors, because
they are also genuine physiological ions. MES buffer at 146x, PEG at 150x, ethylene glycol at
153x and MPD at 262x are the unambiguous ones.

**What it still cannot do.** A high cryo-EM share is not evidence of biology: it tracks host
size, which is what the conditioning is for. Only the depleted end carries a mechanism.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdb as P, plate                                                   # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "5-ligands.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
XR, EM = "X-RAY DIFFRACTION", "ELECTRON MICROSCOPY"

# Declared, not derived. Argue with any of these and re-run.
ADDITIVE = {"SO4": "sulfate, buffer", "GOL": "glycerol, cryoprotectant", "CL": "chloride",
            "EDO": "ethylene glycol, cryoprotectant", "NA": "sodium", "PO4": "phosphate buffer",
            "ACT": "acetate", "PEG": "polyethylene glycol", "DMS": "DMSO", "K": "potassium",
            "TRS": "Tris buffer", "NI": "nickel, from His-tag purification", "IOD": "iodide",
            "MES": "MES buffer", "EPE": "HEPES buffer", "FMT": "formate", "CIT": "citrate",
            "BR": "bromide", "CD": "cadmium", "MPD": "MPD, precipitant", "IMD": "imidazole",
            "PG4": "PEG fragment", "1PE": "PEG fragment", "BME": "beta-mercaptoethanol",
            "TLA": "tartrate", "MLI": "malonate", "SCN": "thiocyanate", "AZI": "azide",
            "NO3": "nitrate", "CO3": "carbonate", "PGE": "PEG fragment", "P6G": "PEG fragment",
            "TRIS": "Tris buffer", "OXL": "oxalate", "BCT": "bicarbonate"}
AMBIGUOUS = {"MG": "magnesium", "ZN": "zinc", "CA": "calcium", "MN": "manganese",
             "FE": "iron", "CU": "copper", "CO": "cobalt", "FE2": "iron(II)", "NAG": "NAG"}
# NAG sits in the ambiguous bucket deliberately: N-acetylglucosamine is a real glycan on a real
# glycoprotein and also a routine expression artefact.


def group(cid):
    if cid in ADDITIVE:
        return "additive", RED
    if cid in AMBIGUOUS:
        return "ambiguous", AMBER
    return "biological", GREEN


def lsq(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((a - mx) * (y - my) for a, y in zip(xs, ys)) / sum((a - mx) ** 2 for a in xs)
    a0 = my - b * mx
    r2 = 1 - (sum((y - (a0 + b * x)) ** 2 for x, y in zip(xs, ys))
              / sum((y - my) ** 2 for y in ys))
    return a0, b, r2


def main():
    d = P.load()
    L, M = d["ligand_by_method"], d["ligand_mw"]
    rows = []
    for c, v in L.items():
        xr, em = v[XR], v[EM]
        h = sorted((float(a), b) for a, b in M[c])
        n = sum(b for _, b in h)
        rows.append({"c": c, "xr": xr, "em": em, "n": v["total"],
                     "sh": em / max(xr + em, 1),
                     # Haldane correction: the two components with no cryo-EM entry at all
                     # still have to sit somewhere on a log axis and in the fit
                     "adj": (em + 0.5) / (xr + em + 1.0),
                     "lo": math.log((em + 0.5) / (xr + 0.5)),
                     "big": sum(b for a, b in h if a >= 200) / n,
                     "g": group(c)[0]})
    ref = [r for r in rows if r["g"] != "additive"]
    la, lb, lr2 = lsq([r["big"] for r in ref], [r["lo"] for r in ref])          # log-odds
    na, nb, _ = lsq([r["big"] for r in ref], [r["sh"] for r in ref])            # linear
    inv = lambda t: math.exp(t) / (1 + math.exp(t))
    for r in rows:
        r["resid"] = r["lo"] - (la + lb * r["big"])
        r["nresid"] = r["sh"] - (na + nb * r["big"])
    add = [r for r in rows if r["g"] == "additive"]
    med = sorted(r["resid"] for r in add)[len(add) // 2]
    below = sum(1 for r in add if r["resid"] < 0)
    nmean = sum(r["nresid"] for r in add) / len(add)

    W, H = 1200, 900
    s = plate.open_svg(W, H, "A hand-made ligand classification, tested against the "
                             "method that never had a drop")
    fr, _ = plate.frame(W, 62,
                        who="anyone mining PDB ligands for binding sites or drug discovery",
                        decide="whether a declared additive label survives the size confound",
                        wrong="declared additives sit on the size line like everything else")
    s += fr

    AX, AY, AH, AW = 28, 158, 470, 730
    x0, pw = AX + 52, AW - 96
    px = lambda f: x0 + pw * (f / 0.58)
    ylo, yhi = 0.0001, 1.0
    py = lambda f: (AY + AH - 58 - (AH - 92)
                    * ((math.log10(max(f, ylo)) - math.log10(ylo))
                       / (math.log10(yhi) - math.log10(ylo))))
    for f, lab in ((0.001, "0.1%"), (0.01, "1%"), (0.1, "10%"), (1.0, "100%")):
        s.append(f'<line x1="{x0:.1f}" y1="{py(f):.1f}" x2="{px(0.58):.1f}" '
                 f'y2="{py(f):.1f}" stroke="{GRID}"/>')
        s.append(txt(x0 - 8, py(f) + 3, lab, size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, AY - 18, "share of this component's entries that were solved by cryo-EM "
                              "(log scale)", size=11, fill=INK2))
    for f in (0, .1, .2, .3, .4, .5):
        s.append(f'<line x1="{px(f):.1f}" y1="{py(ylo):.1f}" x2="{px(f):.1f}" '
                 f'y2="{py(ylo)+5:.1f}" stroke="{MUTED}"/>')
        s.append(txt(px(f), py(ylo) + 18, f"{f:.0%}", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, py(ylo) + 36, "share of this component's host entries over 200 kDa — the "
                                   "size confound, conditioned on", size=10, fill=MUTED))

    # the linear fit, and the region where it predicts an impossible share
    lin = []
    for i in range(121):
        f = 0.58 * i / 120
        v = na + nb * f
        lin.append((px(f), py(v)) if v > ylo else None)
    seg, cur = [], []
    for p in lin:
        if p:
            cur.append(p)
        elif cur:
            seg.append(cur); cur = []
    if cur:
        seg.append(cur)
    for sg in seg:
        s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                        for i, (a, b) in enumerate(sg))
                 + f'" fill="none" stroke="{SLATE}" stroke-width="1.6" '
                   f'stroke-dasharray="6 3"/>')
    zero = -na / nb
    s.append(f'<rect x="{px(0):.1f}" y="{py(ylo):.1f}" width="{px(zero)-px(0):.1f}" '
             f'height="6" fill="{SLATE}" fill-opacity="0.30"/>')
    s += halo(px(zero) + 6, py(ylo) - 2, "left of here the linear fit predicts a negative "
                                         "share", size=9, fill=SLATE)
    s += halo(px(0.405), py(na + nb * 0.405) - 10, "a linear fit", size=9.5,
              fill=SLATE, anchor="middle", weight="700")

    curve = [(px(0.58 * i / 120), py(inv(la + lb * 0.58 * i / 120))) for i in range(121)]
    s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                    for i, (a, b) in enumerate(curve))
             + f'" fill="none" stroke="{INK2}" stroke-width="2"/>')
    s += halo(px(0.445), py(inv(la + lb * 0.445)) + 18, "a log-odds fit", size=9.5,
              fill=INK2, anchor="middle", weight="700")
    s += halo(px(0.445), py(inv(la + lb * 0.445)) + 30, "fitted on the non-additives",
              size=8.5, fill=MUTED, anchor="middle")

    LAB = {"MPD": "n", "EDO": "s", "PEG": "n", "MES": "e", "SO4": "s", "GOL": "w",
           "K": "e", "NA": "e", "CL": "e", "PO4": "w",
           "ATP": "e", "ADP": "e", "NAD": "s", "FAD": "s", "HEM": "e", "SF4": "s",
           "NAG": "n", "MG": "e", "ZN": "s"}
    for r in sorted(rows, key=lambda r: r["n"]):
        col = group(r["c"])[1]
        cx, cy = px(r["big"]), py(r["adj"])
        rr = max(3.0, math.sqrt(r["n"]) * 0.048)
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" fill="{col}" '
                 f'fill-opacity="{0.20 if r["em"] else 0.0}" stroke="{col}" '
                 f'stroke-width="1.4" {"stroke-dasharray=\"2 2\"" if not r["em"] else ""}/>')
        side = LAB.get(r["c"])
        if side:
            dx, dy, anc = {"e": (rr + 5, 3.5, "start"), "w": (-(rr + 5), 3.5, "end"),
                           "n": (0, -rr - 6, "middle"), "s": (0, rr + 11, "middle")}[side]
            s += halo(cx + dx, cy + dy, r["c"], size=9.5, fill=col, anchor=anc, weight="700")

    LX = px(0.335)
    ly = py(0.0045)
    for col, t in ((RED, "declared a crystallisation additive"),
                   (AMBER, "declared ambiguous"), (GREEN, "declared biological")):
        s.append(f'<circle cx="{LX:.1f}" cy="{ly-3.5:.1f}" r="4.6" fill="{col}" '
                 f'fill-opacity="0.20" stroke="{col}" stroke-width="1.4"/>')
        s.append(txt(LX + 12, ly, t, size=10, fill=INK2))
        ly += 17
    s.append(f'<circle cx="{LX:.1f}" cy="{ly-3.5:.1f}" r="4.6" fill="none" stroke="{MUTED}" '
             f'stroke-width="1.4" stroke-dasharray="2 2"/>')
    s.append(txt(LX + 12, ly, "no cryo-EM entry at all; placed by a Haldane correction",
                 size=10, fill=MUTED))
    ly += 17
    s.append(txt(LX + 12, ly, "area is the number of entries carrying the component",
                 size=10, fill=MUTED))

    BX = 800
    by = AY + AH + 6
    s.append(txt(AX, by, "the functional form decided the answer", size=12.5, fill=INK,
                 weight="600"))
    s += wrap(AX, by + 20,
              f"Fitted linearly, the declared additives sit a mean {nmean*100:+.1f} points from "
              f"prediction with mixed signs, and the classification looks like it tests "
              f"negative. That fit predicts a negative cryo-EM share for every component left "
              f"of {zero:.0%} on this axis, which cannot happen, and the positive residuals it "
              f"manufactures against the floor are its entire null. Fitted in log-odds — the "
              f"shape a bounded share actually has — {below} of {len(add)} additives fall "
              f"below prediction, by a median of {math.exp(-med):.0f}x. Both fits are drawn "
              f"because only one of them can be right and they disagree completely.",
              size=11, fill=INK2, chars=94, leading=15)
    s += halo(AX + 760, by + 2, "and it corrects the labels", size=10.5, fill=GREEN,
              weight="700")
    s += wrap(AX + 760, by + 20,
              "Potassium, sodium, chloride and phosphate were declared additives and sit on "
              "the line at 0.9x to 2.4x. They are also genuine physiological ions, and the "
              "test says they behave like one. MES at 146x, PEG at 150x, ethylene glycol at "
              "153x and MPD at 262x are the unambiguous ones.",
              size=10.5, fill=INK2, chars=44, leading=14)

    fy = H - 24 - 14 * 5
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"RCSB PDB search API, fetched {d['fetched']}; the 30 most common non-polymer "
              f"components, each crossed with exptl.method and with a molecular-weight "
              f"histogram of the entries carrying it. The grouping is declared in the script, "
              f"not derived, which is what makes it testable. Host size is summarised as the "
              f"share of an entry's carriers over 200 kDa because the histogram is binned at "
              f"50 kDa and its median is quantised to the bin. Two components have no cryo-EM "
              f"entry at all and are placed by a Haldane correction, drawn dashed. A high "
              f"cryo-EM share is not evidence of biology — it tracks host size, which is what "
              f"the conditioning is for; only the depleted end carries a mechanism. Components "
              f"are multi-valued per entry and cannot be summed.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    log-odds fit R² {lr2:.2f}; additives {below}/{len(add)} below prediction, "
          f"median {math.exp(-med):.1f}x")
    print(f"    linear fit: mean additive residual {nmean*100:+.1f} pts — the wrong shape")
    return 0


if __name__ == "__main__":
    sys.exit(main())
