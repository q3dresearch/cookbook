"""When each audience was filed for, and how those notices ended.

    python chart_audience.py

A faceted density — one row per audience, read off FDA's own intended-species
field. Above each baseline is the density of notices that CLEARED, below it the
ones the company PULLED. Rows share one scale, so a tall row means more notices,
not a busier row: food-producing is 51 notices and "both at once" is 10, and the
chart should say so rather than normalising them to look alike.

A previous version drew one dot per notice. Ninety-four dots is a strip, not a
distribution, and the outcome rates only existed in the caption. Both are now in
the geometry: the mirror shows the balance, and the bar on the right prints it.

Gaussian kernel, bandwidth 1.1 years, on 94 notices across 16 years. Every row
is thin and the printed counts are the honest version of each curve.
"""
import os, sys, re, math
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import graslib

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(os.path.dirname(HERE), "charts")
PET = re.compile(r"\bdog|\bcat\b|\bcats\b|\bpet", re.I)
FOOD = re.compile(r"cattle|cow|swine|pig|poultry|chicken|turkey|sheep|goat|livestock|"
                  r"broiler|laying|fish|aqua|salmon|shrimp|calve", re.I)
BW = 1.1
Y0, Y1 = 2009.5, 2026.5

rows, src = graslib.load_animal()
def yr(r): return int(r["filed"].split("/")[-1]) if r["filed"] else None
def audience(r):
    sp = r["species"]
    if re.search(r"all animals", sp, re.I): return "All animals"
    p, f = bool(PET.search(sp)), bool(FOOD.search(sp))
    if p and f: return "Both at once"
    if p: return "Pets"
    if f: return "Food-producing"
    return "Unclear"

ORDER = ["Pets", "Food-producing", "Both at once", "All animals"]
SUB = {"Pets": "dogs and cats", "Food-producing": "cattle, swine, poultry, fish",
       "Both at once": "pets AND livestock in one notice", "All animals": "“all animals”"}
CLEAR, PULL, OTHER = "#2e7d5b", "#c2553e", "#b9b4a8"

def density(years, grid):
    """Gaussian KDE scaled so the area is the COUNT, not 1."""
    return [sum(math.exp(-0.5 * ((g - y) / BW) ** 2) / (BW * math.sqrt(2 * math.pi))
                for y in years) for g in grid]

GRID = [Y0 + i * (Y1 - Y0) / 220 for i in range(221)]
data = {}
peak = 0.0
for a in ORDER:
    g = [r for r in rows if audience(r) == a and yr(r)]
    cl = density([yr(r) for r in g if r["outcome"] == "no questions"], GRID)
    pu = density([yr(r) for r in g if r["outcome"] == "withdrawn"], GRID)
    data[a] = (g, cl, pu)
    peak = max(peak, max(cl + pu))

W, L, T, RH, R = 1120, 210, 236, 116, 300
AXIS_GAP = 34
H = T + len(ORDER) * RH + AXIS_GAP + 180
PW = W - L - R
def sx(y): return L + (y - Y0) / (Y1 - Y0) * PW
def hh(v): return v / peak * (RH * 0.40)

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "Corn-ethanol additives for livestock, then novel protein for pets",
             20, INK, weight="600"))
b.append(txt(40, 70, "Every notice to FDA's animal-food GRAS programme, grouped by who "
            "the ingredient is for. Above each line, notices FDA cleared; below,", 13, MUTE))
b.append(txt(40, 89, "notices the company pulled. Rows share one scale, so height is "
            "notices per year — a taller row really is a busier one.", 13, MUTE))
b.append(txt(40, 115, "The bar on the right is the same rows' outcomes as shares. Pets "
            "clear more and pull less than livestock; claiming both at once is the worst "
            "row on the chart.", 12, MUTE))
b.append(circ(46, 143, 6, CLEAR))
b.append(txt(57, 147, "FDA had no questions", 11.5, MUTE))
b.append(circ(226, 143, 6, PULL))
b.append(txt(237, 147, "pulled by the company", 11.5, MUTE))
b.append(circ(406, 143, 6, OTHER))
b.append(txt(417, 147, "refused or still pending", 11.5, MUTE))

for i, a in enumerate(ORDER):
    base = T + i * RH + RH * 0.46
    g, cl, pu = data[a]
    n = len(g)
    nc = sum(1 for r in g if r["outcome"] == "no questions")
    nw = sum(1 for r in g if r["outcome"] == "withdrawn")
    b.append(line(L, base, L + PW, base, GRID, 1))
    up = " ".join(f"{sx(x):.1f},{base - hh(v):.1f}" for x, v in zip(GRID, cl))
    dn = " ".join(f"{sx(x):.1f},{base + hh(v):.1f}" for x, v in zip(GRID, pu))
    b.append(f'<polygon points="{sx(Y0):.1f},{base:.1f} {up} {sx(Y1):.1f},{base:.1f}" '
             f'fill="{CLEAR}" fill-opacity="0.72"/>')
    b.append(f'<polygon points="{sx(Y0):.1f},{base:.1f} {dn} {sx(Y1):.1f},{base:.1f}" '
             f'fill="{PULL}" fill-opacity="0.72"/>')
    b.append(txt(L - 18, base - 4, a, 13, INK, "end", "600"))
    b.append(txt(L - 18, base + 13, SUB[a], 10.5, MUTE, "end"))
    b.append(txt(L - 18, base + 30, f"{n} notices", 10.5, MUTE, "end"))

    # the numbers, printed rather than described
    bx, bw = L + PW + 40, 150
    seg = [(nc, CLEAR, "cleared"), (nw, PULL, "pulled"), (n - nc - nw, OTHER, "")]
    x = bx
    for v, c, lab in seg:
        if not v:
            continue
        w = v / n * bw
        b.append(rect(x, base - 13, w, 26, c))
        if v / n >= 0.16:
            b.append(txt(x + w / 2, base + 4, f"{v/n:.0%}", 11.5, "#ffffff", "middle", "700"))
        x += w
    b.append(txt(bx + bw + 10, base - 1, f"{nc/n:.0%} cleared", 11, INK))
    b.append(txt(bx + bw + 10, base + 14, f"{nw/n:.0%} pulled", 11, MUTE))

b.append(line(L, T + len(ORDER) * RH - 12, L + PW, T + len(ORDER) * RH - 12, GRID, 1))
for y in range(2010, 2027, 2):
    b.append(txt(sx(y), T + len(ORDER) * RH + 4, str(y), 10.5, MUTE, "middle"))

yb = T + len(ORDER) * RH + AXIS_GAP + 14
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
b.append(txt(40, yb, "Pets clear 60% and pull 15%. Food-producing clears 53% and pulls "
             "35%. Claiming pets AND livestock in one notice clears 20% and pulls 70%.",
             13, INK, weight="600"))
b.append(txt(40, yb + 24, "That last row is 10 notices, so read it as a warning rather "
             "than a rate — but it points the same way as the species count does: notices "
             "naming 1–3 species clear 54%,", 12, MUTE))
b.append(txt(40, yb + 41, "those naming four or more clear 41%, and that gap survives "
             "dropping the ethanol cohort (55/45) and everything before 2018 (55/43).",
             12, MUTE))
b.append(txt(40, yb + 65, f"Gaussian kernel, bandwidth 1.1 years, area scaled to counts "
             f"rather than normalised. 94 notices over 16 years — every row is thin, and "
             f"the printed counts are the honest version", 11, MUTE))
b.append(txt(40, yb + 82, f"of each curve. Species groups are read off FDA's intended-"
             f"species text. Source: FDA animal food GRAS inventory, "
             f"{os.path.basename(src)}.", 11, MUTE))
open(os.path.join(CHARTS, "animal-audience.svg"), "w").write(doc(W, H, b))
print("  animal-audience.svg")
for a in ORDER:
    g = data[a][0]
    nc = sum(1 for r in g if r["outcome"] == "no questions")
    nw = sum(1 for r in g if r["outcome"] == "withdrawn")
    print(f"    {a:16s} n={len(g):3d}  cleared {nc/len(g):4.0%}  pulled {nw/len(g):4.0%}")
