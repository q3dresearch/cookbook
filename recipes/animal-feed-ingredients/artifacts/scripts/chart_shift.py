"""What the animal feed programme is FOR, and how that changed.

    python chart_shift.py

This recipe's original headline was "animal feed innovation is mostly about
wasting less" — efficiency rather than new inputs. Measured across all years that
is 34%. Measured by era it is a pooled number averaging two different programmes:

    2010-14   72% efficiency     mostly corn-ethanol processing aids
    2015-19   53%
    2020-24   21%
    2025-29   10%     mostly protein sources

So the claim was true of the programme's first five years and is no longer. What
replaced it is alternative protein: krill, methanotroph single-cell protein,
crickets, algal residue, yeast expressing an ovine protein, black soldier fly
larvae — nine of the thirteen protein notices were filed from 2019 on.

Stacked shares on one axis because the categories partition each cohort, and
counts are printed on the bars because a share of eighteen notices is not the
same evidence as a share of thirty-eight.
"""
import os, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import graslib

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(os.path.dirname(HERE), "charts")
EFF = {"Phosphorus availability (phytase)", "Synthetic amino acid",
       "Ethanol co-product", "Viscosity / NSP enzyme"}
UT = "Utility information not evaluated"

rows, src = graslib.load_animal()
def pur(r):
    return graslib.purpose(r["use"] + " " + r["substance"])

def band(r):
    if UT in r["use"]:
        return "FDA did not say what it is for"
    p = pur(r)
    if p in EFF:
        return "Efficiency — get more from the same feed"
    if p == "Protein source":
        return "New protein source"
    return "Everything else"

ORDER = ["Efficiency — get more from the same feed", "New protein source",
         "Everything else", "FDA did not say what it is for"]
COL = {ORDER[0]: "#2e7d5b", ORDER[1]: "#2361b0", ORDER[2]: "#b9b4a8",
       ORDER[3]: "#c2553e"}

g = defaultdict(Counter)
for r in rows:
    y = r["filed"].split("/")[-1] if r["filed"] else None
    if y:
        g[(int(y) // 5) * 5][band(r)] += 1
cohorts = [b for b in sorted(g) if sum(g[b].values()) >= 8]

W, L, T, PH, R = 1040, 96, 230, 330, 280
H = T + PH + 214
BW = (W - L - R) / len(cohorts)

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "The feed programme stopped being about waste and started being "
             "about protein", 20, INK, weight="600"))
b.append(txt(40, 70, "Every notice to FDA's animal-food GRAS programme, by what the "
            "ingredient is for. One notice = one company telling FDA about one", 13, MUTE))
b.append(txt(40, 89, "feed or pet-food ingredient. Bars are shares of each five-year "
            "group; the count is printed because eighteen notices and thirty-eight "
            "are not", 13, MUTE))
b.append(txt(40, 108, "the same evidence.", 13, MUTE))
b.append(txt(40, 134, "This corrects the recipe's own earlier headline. Pooled across all "
            "years, efficiency is 34% — which is the average of 72% and 10%.", 12, MUTE))

lx = 40
for k in ORDER:
    b.append(rect(lx, 158, 11, 11, COL[k]))
    b.append(txt(lx + 17, 167.5, k, 11.5, MUTE))
    lx += 17 + len(k) * 6.1 + 26

for v in (0, .25, .5, .75, 1.0):
    y = T + PH - v * PH
    b.append(line(L, y, W - R, y, GRID, 1))
    b.append(txt(L - 10, y + 4, f"{v:.0%}", 10.5, MUTE, "end"))

for i, c in enumerate(cohorts):
    n = sum(g[c].values())
    x = L + i * BW + BW * 0.16
    w = BW * 0.68
    acc = 0.0
    for k in ORDER:
        v = g[c][k] / n
        if not v:
            continue
        h = v * PH
        b.append(rect(x, T + PH - acc - h, w, h, COL[k]))
        if v >= 0.10:
            b.append(txt(x + w / 2, T + PH - acc - h / 2 + 4, str(g[c][k]), 11,
                         "#ffffff", "middle", "700"))
        acc += h
    b.append(txt(x + w / 2, T + PH + 22, f"{c}–{str(c+4)[2:]}", 11.5, MUTE, "middle"))
    b.append(txt(x + w / 2, T + PH + 38, f"n={n}", 10.5, MUTE, "middle"))

yb = T + PH + 90
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
b.append(txt(40, yb, "Efficiency ran 72% of the programme's first five years and 10% of "
             "its last. It was never a claim about animal feed — it was a claim about "
             "2010–14.", 13, INK, weight="600"))
b.append(txt(40, yb + 24, "What replaced it is alternative protein: krill meal, "
             "methanotroph and methylotroph single-cell protein, crickets, algal residue, "
             "yeast expressing an ovine protein, black", 12, MUTE))
b.append(txt(40, yb + 41, "soldier fly larvae. Nine of the thirteen protein notices were "
             "filed from 2019 on, and five of the thirteen were withdrawn.", 12, MUTE))
b.append(txt(40, yb + 65, "The red band is not a category of ingredient. It is notices "
             "whose stated use reads “Utility information not evaluated for GRAS, see "
             "FDA's letter” — FDA clearing on safety", 11, MUTE))
b.append(txt(40, yb + 82, "while explicitly declining to say whether the thing works. That "
             "went from 0% before 2016 to a quarter of recent notices, and it is why the "
             "purpose of a notice is now often unreadable.", 11, MUTE))
b.append(txt(40, yb + 106, f"94 notices, 2010 to date. Purpose categories are ours, read "
             f"off each notice's stated use. Source: FDA animal food GRAS inventory, "
             f"{os.path.basename(src)}.", 11, MUTE))
open(os.path.join(CHARTS, "animal-purpose-shift.svg"), "w").write(doc(W, H, b))
print("  animal-purpose-shift.svg")
for c in cohorts:
    n = sum(g[c].values())
    print(f"    {c}-{c+4}  n={n:2d}  " +
          "  ".join(f"{k.split(' —')[0][:14]}={g[c][k]}" for k in ORDER if g[c][k]))
