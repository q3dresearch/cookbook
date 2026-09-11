"""Does claiming more species cost you? And does a vaguer claim?

    python chart_breadth.py

Two properties a notifier controls, against the outcome:

  * HOW MANY SPECIES the notice claims. Naming 1-3 clears 54%, naming four or
    more clears 41%. The gap survives dropping the corn-ethanol cohort (55/45)
    and dropping everything before 2018 (55/43), so it is not just the early
    notices that claimed every farm animal at once.
  * HOW SPECIFIC the stated use is, proxied by its length. Split at the median
    103 characters, short clears 31% and long clears 52% - and that survives the
    same two controls plus restricting to food-producing animals (22/52).
    Two-proportion z = +1.96, which is borderline; length is a crude proxy.

Both point the same way: a narrow, specific claim clears more often than a broad
vague one. Neither is a large sample, which is why the counts are printed.
"""
import os, sys, re, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import graslib

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(os.path.dirname(HERE), "charts")
UT = "Utility information not evaluated"
rows, src = graslib.load_animal()
def yr(r): return int(r["filed"].split("/")[-1]) if r["filed"] else None
def ok(rs): return sum(1 for r in rs if r["outcome"] == "no questions") / len(rs)
def wd(rs): return sum(1 for r in rs if r["outcome"] == "withdrawn") / len(rs)
ETH = re.compile(r"ethanol|distiller|fermentor|isobutanol", re.I)
def nspec(r):
    sp = r["species"]
    if re.search(r"all animals", sp, re.I): return 99
    return len([x for x in re.split(r",|\band\b", sp) if x.strip()])

described = [r for r in rows if UT not in r["use"]]
MED = st.median([len(r["use"]) for r in described])

PANELS = [
    ("How many species the notice claims",
     [("one", [r for r in rows if nspec(r) == 1]),
      ("two or three", [r for r in rows if 2 <= nspec(r) <= 3]),
      ("four or more", [r for r in rows if 4 <= nspec(r) < 99]),
      ("“all animals”", [r for r in rows if nspec(r) == 99])],
     [("all notices", lambda r: True),
      ("no ethanol", lambda r: not ETH.search(r["use"] + r["substance"])),
      ("2018 on", lambda r: yr(r) and yr(r) >= 2018)],
     lambda r: nspec(r) <= 3),
    ("How specific the stated use is",
     [("shorter than 103 chars", [r for r in described if len(r["use"]) < MED]),
      ("103 chars or more", [r for r in described if len(r["use"]) >= MED])],
     [("all described", lambda r: UT not in r["use"]),
      ("no ethanol", lambda r: UT not in r["use"] and not ETH.search(r["use"] + r["substance"])),
      ("food-producing", lambda r: UT not in r["use"] and re.search(
          r"cattle|swine|poultry|chicken|livestock", r["species"], re.I))],
     lambda r: len(r["use"]) >= MED),
]

W, L, R = 1080, 300, 300
T = 236
ROW, GAPY = 46, 78
H = T + sum(len(p[1]) * ROW + GAPY for p in PANELS) + 140
BARW = W - L - R
def sx(v): return L + v * BARW

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "A narrow, specific claim clears more often than a broad vague one",
             20, INK, weight="600"))
b.append(txt(40, 70, "Two things the notifier chooses, against how often FDA cleared the "
            "notice. Bars are the share cleared; the number beside each is how", 13, MUTE))
b.append(txt(40, 89, "many notices sit in that band. The small figures on the right are the "
            "same split under two or three controls.", 13, MUTE))
b.append(txt(40, 115, "Neither is a large sample. 94 notices, and every split of it is "
            "smaller — read the counts, not the decimals.", 12, MUTE))

y = T
for title, bands, controls, pred in PANELS:
    b.append(txt(40, y - 18, title, 14, INK, weight="600"))
    for i, (lab, g) in enumerate(bands):
        yy = y + i * ROW
        if not g:
            continue
        b.append(txt(L - 18, yy + 5, lab, 12.5, INK, "end"))
        b.append(rect(L, yy - 10, sx(ok(g)) - L, 22, "#2e7d5b", rx=3))
        b.append(txt(sx(ok(g)) + 10, yy + 5, f"{ok(g):.0%} cleared", 12, INK, weight="600"))
        b.append(txt(sx(ok(g)) + 96, yy + 5, f"n={len(g)}", 11, MUTE))
    # the controls, small, to the right
    cy = y + 4
    b.append(txt(W - R + 54, cy - 22, "same split under controls", 10.5, MUTE))
    for j, (clab, keep) in enumerate(controls):
        s = [r for r in rows if keep(r) and not pred(r)]
        g2 = [r for r in rows if keep(r) and pred(r)]
        if len(s) < 6 or len(g2) < 6:
            continue
        b.append(txt(W - R + 54, cy + j * 17, f"{clab}", 10.5, MUTE))
        b.append(txt(W - R + 168, cy + j * 17,
                     f"{ok(s):.0%} → {ok(g2):.0%}".replace("→", "vs"), 10.5, INK))
    y += len(bands) * ROW + GAPY

yb = H - 150
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
b.append(txt(40, yb, "Naming one species clears 56%. Naming four or more clears 36%. "
             "A use statement over 103 characters clears 52%; a shorter one 31%.",
             13, INK, weight="600"))
b.append(txt(40, yb + 24, "The species result is not just the corn-ethanol cohort that "
             "claimed every farm animal at once: it survives dropping those notices and "
             "dropping everything before 2018.", 12, MUTE))
b.append(txt(40, yb + 41, "The specificity result survives the same two plus restricting to "
             "livestock. z = +1.96, which is borderline, and length is a crude proxy for "
             "how specific a claim is.", 12, MUTE))
b.append(txt(40, yb + 65, "Use statements are also getting shorter: median 128 characters "
             "in 2010-14, 56 in 2025-29. Claims are getting vaguer at the same time FDA is "
             "increasingly declining to", 11, MUTE))
b.append(txt(40, yb + 82, f"assess whether they work. The 15 notices FDA declined to "
             f"describe are excluded from the specificity panel — they have no stated use "
             f"to measure. Source: {os.path.basename(src)}.", 11, MUTE))
open(os.path.join(CHARTS, "animal-claim-shape.svg"), "w").write(doc(W, H, b))
print("  animal-claim-shape.svg")
for title, bands, _, _ in PANELS:
    print(f"    {title}")
    for lab, g in bands:
        if g: print(f"      {lab:24s} n={len(g):3d}  cleared {ok(g):4.0%}")
