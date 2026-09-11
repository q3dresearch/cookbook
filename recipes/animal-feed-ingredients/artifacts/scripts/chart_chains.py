"""Substances filed more than once — refiling FDA does not publish.

    python chart_chains.py

The human-food inventory has `Resubmitted` and `Resubmission` columns linking a
notice to its successor. The animal table has neither. Normalising substance
names recovers the links anyway: 18 substances were filed more than once, 41 of
the 94 notices.

The rate that falls out is 31% of pulled notices come back, and 8 of those 10
eventually cleared — the same comeback rate as human food's 31%. So the animal
programme's FIRST attempt fails far more often (51% cleared against 79%) while
the retry behaviour is identical. What differs is the first pass, not persistence.

Matching is on a normalised substance name, so it will miss a refiling under a
renamed substance and could in principle merge two firms' identical ingredient —
the chart marks which chains stay inside one company.
"""
import os, sys, re
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import graslib

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(os.path.dirname(HERE), "charts")
COL = {"no questions": "#2e7d5b", "withdrawn": "#c2553e",
       "rejected": "#7a2f22", "pending": "#b9b4a8"}
LAB = {"no questions": "cleared", "withdrawn": "pulled",
       "rejected": "refused", "pending": "pending"}

rows, src = graslib.load_animal()
def yr(r): return int(r["filed"].split("/")[-1]) if r["filed"] else None
def norm_sub(s):
    s = re.sub(r"\(.*?\)", " ", (s or "").lower())
    s = re.sub(r"\b(dried|inactivated|preparation|product|from|derived|biomass|"
               r"potassium|meal|solubles|condensed)\b", " ", s)
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())
def firm(r): return (r["notifier"] or "").split(",")[0].split(" doing")[0].strip()

g = defaultdict(list)
for r in rows:
    if yr(r): g[norm_sub(r["substance"])].append(r)
chains = [(k, sorted(v, key=yr)) for k, v in g.items() if len(v) > 1]
chains.sort(key=lambda kv: (yr(kv[1][0]), -len(kv[1])))

Y0, Y1 = 2009.6, 2026.6
W, L, RH, R = 1120, 330, 34, 230
T = 250
H = T + len(chains) * RH + 208
def sx(y): return L + (y - Y0) / (Y1 - Y0) * (W - L - R)

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "Companies do come back — FDA just does not say so here",
             20, INK, weight="600"))
b.append(txt(40, 70, "Every substance filed to the animal-food programme more than once. "
            "The human-food inventory links a notice to its successor with a", 13, MUTE))
b.append(txt(40, 89, "`Resubmitted` field; the animal table has no such column, so these "
            "chains were recovered by matching normalised substance names.", 13, MUTE))
b.append(txt(40, 115, "31% of pulled notices come back and 8 of those 10 eventually clear "
            "— the same comeback rate as human food. The first attempt is what differs, "
            "not the persistence.", 12, MUTE))
lx = 40
for k in ("no questions", "withdrawn", "rejected", "pending"):
    b.append(circ(lx + 6, 145, 6, COL[k]))
    b.append(txt(lx + 17, 149, LAB[k], 11.5, MUTE))
    lx += 17 + len(LAB[k]) * 6.4 + 26

for y in range(2010, 2027, 2):
    b.append(line(sx(y), T - 16, sx(y), T + len(chains) * RH - 14, GRID, 1))
    b.append(txt(sx(y), T - 24, str(y), 10.5, MUTE, "middle"))

for i, (k, v) in enumerate(chains):
    y = T + i * RH
    one_firm = len({firm(r).lower() for r in v}) == 1
    b.append(line(sx(yr(v[0])), y, sx(yr(v[-1])), y, MUTE if one_firm else GRID,
                  1.8 if one_firm else 1.8, None if one_firm else "4 3"))
    for r in v:
        b.append(circ(sx(yr(r)), y, 6.5, COL[r["outcome"]]))
    name = v[0]["substance"]
    b.append(txt(L - 16, y + 4, name[:42] + ("…" if len(name) > 42 else ""), 11.5,
                 INK, "end"))
    tail = firm(v[-1])
    b.append(txt(W - R + 14, y + 4,
                 f"{tail[:24]}{'' if one_firm else '  (two firms)'}", 10.5, MUTE))

n_pull = sum(1 for r in rows if r["outcome"] == "withdrawn")
came = sum(1 for r in rows if r["outcome"] == "withdrawn"
           and any(yr(x) > yr(r) for x in g[norm_sub(r["substance"])] if yr(x) and yr(r)))
yb = T + len(chains) * RH + 42
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
b.append(txt(40, yb, f"{len(chains)} substances, {sum(len(v) for _,v in chains)} of the 94 "
             f"notices. {came} of the {n_pull} pulled notices have a later filing — "
             f"{came/n_pull:.0%}, against human food's 31%.", 13, INK, weight="600"))
b.append(txt(40, yb + 24, "Some chains are long. Methylococcus capsulatus was pulled, then "
             "cleared, then pulled again across five years and one company. Alpha-lipoic acid was "
             "refused in 2011 and cleared in 2022,", 12, MUTE))
b.append(txt(40, yb + 41, "eleven years later. Serine endopeptidase was pulled in 2024 and "
             "pulled again in 2025. A solid line is one company; a dashed line means two "
             "different firms filed the same substance.", 12, MUTE))
b.append(txt(40, yb + 65, "Matching is on a normalised substance name, so a refiling under "
             "a renamed substance is missed and the 31% is a floor. Source: FDA animal "
             f"food GRAS inventory, {os.path.basename(src)}.", 11, MUTE))
open(os.path.join(CHARTS, "animal-refiling-chains.svg"), "w").write(doc(W, H, b))
print(f"  animal-refiling-chains.svg — {len(chains)} chains, "
      f"{came}/{n_pull} pulled notices came back = {came/n_pull:.0%}")
