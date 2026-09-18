"""Withdrawal did not change. What a withdrawal MEANS did.

    python chart_meaning.py

Two rates, four-year cohorts, one axis because both are percentages. They are
percentages of different bases — withdrawals as a share of closures, comebacks as
a share of withdrawals — so read each line's SHAPE, not the gap between them.

The withdrawal rate is flat: 10-21% across 28 years, mean 17.2%, no trend. The
share of withdrawals that come back under a new GRN is not. It runs 40-67%
through 2007 and 22-36% after, and the break is sharp rather than gradual.

Two controls, because the obvious explanations are compositional:

  * It is not who files. One-time filers were 35% of withdrawals before 2008 and
    38% after — barely moved.
  * It is not a mix of filer types. The drop holds INSIDE each type: repeat
    filers 75% -> 39%, one-time filers 27% -> 15%. Both roughly halved.
  * It is not censoring. Comebacks take a median 1 year and 94% arrive within 3,
    so every cohort through 2022 has had time. The last cohort is shaded because
    it has not.

Two-proportion z on the censoring-free split (51% before 2010 against 29% for
2010-2022) is 2.78, so this is not noise. What caused the break is not in this
file — see the recipe's open questions.
"""
import os, sys, math
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import graslib

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(os.path.dirname(HERE), "charts")
B = 4
CENSORED_FROM = 2024

by, src = graslib.load()
rows = [r for r in by.values() if r["closed_year"]]
wr, rr = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
for r in rows:
    b = (int(r["closed_year"]) // B) * B
    wr[b][1] += 1
    if r["outcome"] == "withdrawn":
        wr[b][0] += 1
        rr[b][1] += 1
        if r["next"] and str(r["next"]) != "None":
            rr[b][0] += 1
cohorts = [b for b in sorted(wr) if wr[b][1] >= 8]

W, L, T, PH, R = 1060, 92, 214, 360, 250
H = T + PH + 190
def sx(i): return L + (i + 0.5) / len(cohorts) * (W - L - R)
def sy(v): return T + PH - v * PH
def sr(n): return 4.5 + math.sqrt(n) * 1.5

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "The same share pull out. Far fewer come back.",
             20, INK, weight="600"))
b.append(txt(40, 70, "Four-year groups of GRAS filings FDA has closed. Orange: the share "
            "the company pulled before FDA finished reading. Blue: the share of",
            13, MUTE))
b.append(txt(40, 89, "those pulled filings that the company later filed again for the "
            "same ingredient.", 13, MUTE))
b.append(txt(40, 108, "Both are percentages but of different bases, so read each line's "
            "shape, not the gap between them.", 13, MUTE))
b.append(txt(40, 134, "Pulling out is as common as it ever was. Coming back is not: that "
            "line falls off a cliff after 2007 and never recovers. It is not who "
            "files, and it is not censoring.", 12, MUTE))

for v in (0, .2, .4, .6, .8):
    b.append(line(L, sy(v), W - R, sy(v), GRID, 1))
    b.append(txt(L - 10, sy(v) + 4, f"{v:.0%}", 10.5, MUTE, "end"))
# The last cohort has not had time to come back; say so with the shading.
ci = [i for i, c in enumerate(cohorts) if c >= CENSORED_FROM]
if ci:
    x0 = sx(ci[0]) - (W - L - R) / len(cohorts) / 2
    b.append(rect(x0, T, W - R - x0, PH, "#f2f2f0"))
    b.append(txt((x0 + W - R) / 2, T + 18, "too recent", 10.5, MUTE, "middle"))
    b.append(txt((x0 + W - R) / 2, T + 33, "to have come back", 10.5, MUTE, "middle"))

for i, c in enumerate(cohorts):
    b.append(txt(sx(i), T + PH + 22, f"{c}–{str(c+B-1)[2:]}", 10.5, MUTE, "middle"))

for key, col, lab in ((wr, ORANGE, "withdrawn, share of closures"),
                      (rr, BLUE, "came back, share of withdrawals")):
    pts = [(sx(i), sy(key[c][0] / key[c][1])) for i, c in enumerate(cohorts) if key[c][1]]
    b.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) +
             f'" fill="none" stroke="{col}" stroke-width="2.4"/>')
for i, c in enumerate(cohorts):
    n = wr[c][1]
    b.append(circ(sx(i), sy(wr[c][0] / wr[c][1]), sr(n) * 0.55, ORANGE))
    if rr[c][1]:
        b.append(circ(sx(i), sy(rr[c][0] / rr[c][1]), sr(rr[c][1]), BLUE))
        b.append(txt(sx(i), sy(rr[c][0] / rr[c][1]) - sr(rr[c][1]) - 7,
                     f"n={rr[c][1]}", 9.5, MUTE, "middle"))

b.append(circ(L + 8, T - 30, 6, ORANGE))
b.append(txt(L + 20, T - 26, "pulled by the company · share of everything closed", 11.5, MUTE))
b.append(circ(L + 340, T - 30, 6, BLUE))
b.append(txt(L + 352, T - 26, "filed again later · share of those pulled "
             "(area = how many)", 11.5, MUTE))

yb = T + PH + 74
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
b.append(txt(40, yb, "Before 2010, 51% of pulled filings were filed again. From 2010 to "
             "2022, 29%. Two-proportion z = 2.78, so this is not noise.", 13, INK,
             weight="600"))
b.append(txt(40, yb + 22, "It is not composition. One-time filers were 35% of "
             "pulled filings before 2008 and 38% after. And the drop holds inside each "
             "type: repeat filers 75% to 39%, one-time", 12, MUTE))
b.append(txt(40, yb + 39, "filers 27% to 15%. Both roughly halved. Those pre-2008 "
             "strata are thin — 20 and 11 notices — so read them as consistent with "
             "the whole, not as separate evidence.", 12, MUTE))
b.append(txt(40, yb + 63, "Comebacks are fast: median 1 year, 94% within 3. So every "
             "cohort through 2022 has had time and only the shaded one is censored.",
             11, MUTE))
b.append(txt(40, yb + 80, "A comeback is counted only where FDA records a resubmission "
             "link. A substance refiled by another route, or marketed without any "
             "notice at all, is invisible here.", 11, MUTE))
b.append(txt(40, yb + 97, "Source: FDA GRAS Notice Inventory, "
             f"{os.path.basename(src)}.", 11, MUTE))
open(os.path.join(CHARTS, "gras-meaning.svg"), "w").write(doc(W, H, b))
print("  gras-meaning.svg")
for c in cohorts:
    w, n = wr[c]; cb, wn = rr[c]
    print(f"    {c}-{c+B-1}  closed {n:4d}  withdrew {w/n:4.0%}  "
          f"of {wn:3d} withdrawals {cb/wn if wn else 0:4.0%} came back")
