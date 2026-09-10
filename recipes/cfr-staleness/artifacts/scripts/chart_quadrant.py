"""Settled vs fossil: section age against the age of its neighbourhood.

Square plot on a shared range, so the y=x diagonal is a true 45 degrees:
distance from it is how far a section has drifted from its own part.
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
RECIPE = os.path.dirname(os.path.dirname(HERE))          # recipes/cfr-staleness
CHARTS = os.path.join(RECIPE, "artifacts", "charts")
# This recipe commits no data. capture.py writes into a work directory and every
# other script reads from the same one: set CFR_WORK, or accept ./work in the
# current directory. Nothing here reaches outside the recipe except that dir.
WORK = os.environ.get("CFR_WORK") or os.path.join(os.getcwd(), "work")
DERIVED = os.path.join(WORK, "derived")
RAW = os.path.join(WORK, "raw")
os.makedirs(DERIVED, exist_ok=True)
import json, os, sys
from collections import Counter
sys.path.insert(0, HERE)
from svgkit import *
import cfrlib

rows, live = cfrlib.load()
med, _ = cfrlib.part_activity(live)
# Sections that are the only dated one in their part have no neighbourhood to be
# compared to, so they are dropped rather than plotted against themselves.
solo = [r for r in live if (r["part"], r["section"]) not in med]
live = [r for r in live if (r["part"], r["section"]) in med]
for r in live:
    r["pmed"] = med[(r["part"], r["section"])]
CUT = quantiles(sorted(r["age"] for r in live), [0.5])[0]

ANN = json.load(open(os.path.join(HERE, "quad_annot.json"))) if os.path.exists(os.path.join(HERE, "quad_annot.json")) else []
L, R, T, P = 96, 372, 138, 556                  # square plot of side P
B = 180 + (34 + 19 * len(ANN) if ANN else 0)
W, H = L + P + R, T + P + B
MAX = max(max(r["age"] for r in live), max(r["pmed"] for r in live)) * 1.02
X = lambda v: L + P * v / MAX
Y = lambda v: T + P - P * v / MAX

cell = lambda r: ("frozen" if r["age"] >= CUT else "live",
                  "quiet" if r["pmed"] >= CUT else "active")
cnt = Counter(cell(r) for r in live)
N = len(live)

b = []
b.append(txt(40, 44, "Settled, or simply forgotten?", 21, INK, weight="600"))
b.append(txt(40, 68, "A section nobody has amended looks the same whether it was "
                     "deliberately left alone or never reopened. Its neighbours tell "
                     "you which.", 12.5, MUTE))
b.append(txt(40, 86, f"Each dot is one in-force section of CFR Title 12, plotted against "
                     f"the median age of the rest of its part. Axes split at the title "
                     f"median, {CUT:.1f} years.", 12.5, MUTE))
b.append(txt(40, 104, "Both axes share one range, so the diagonal is a true 45°: on it, "
                      "a section is exactly as stale as its neighbourhood.", 12.5, MUTE))

b.append(rect(X(CUT), Y(CUT), P - (X(CUT) - L), T + P - Y(CUT), VIOLET, op=0.07))
b.append(rect(X(CUT), T, P - (X(CUT) - L), Y(CUT) - T, MUTE, op=0.075))
b.append(rect(L, T, X(CUT) - L, Y(CUT) - T, AQUA, op=0.06))
b.append(rect(L, Y(CUT), X(CUT) - L, T + P - Y(CUT), BLUE, op=0.045))

for v in range(0, int(MAX) + 1, 10):
    b.append(line(X(v), T, X(v), T + P, GRID))
    b.append(line(L, Y(v), L + P, Y(v), GRID))
    b.append(txt(X(v), T + P + 20, str(v), 11, MUTE, "middle"))
    b.append(txt(L - 10, Y(v) + 4, str(v), 11, MUTE, "end"))

for r in live:
    col = {("frozen", "active"): VIOLET, ("frozen", "quiet"): MUTE,
           ("live", "quiet"): AQUA}.get(cell(r), BLUE)
    b.append(f'<circle cx="{X(r["age"]):.1f}" cy="{Y(r["pmed"]):.1f}" r="1.9" '
             f'fill="{col}" fill-opacity="0.45"/>')

b.append(line(X(0), Y(0), X(MAX), Y(MAX), INK, 1.4, "2 4"))
b.append(line(X(CUT), T, X(CUT), T + P, INK, 1.2, "5 4"))
b.append(line(L, Y(CUT), L + P, Y(CUT), INK, 1.2, "5 4"))
# diagonal label, set along the line near its upper end
dl = MAX * 0.82
b.append(f'<text x="{X(dl):.1f}" y="{Y(dl)-9:.1f}" font-family="{FONT}" '
         f'font-size="11" fill="{INK}" text-anchor="middle" '
         f'transform="rotate(-45 {X(dl):.1f} {Y(dl)-9:.1f})">'
         f'as stale as its neighbours</text>')
b.append(txt(X(MAX * 0.30), Y(MAX * 0.62), "section fresher than its part",
             10.5, MUTE, "middle", style="italic"))
b.append(txt(X(MAX * 0.72), Y(MAX * 0.15), "section staler than its part",
             10.5, MUTE, "middle", style="italic"))

b.append(txt(L + P / 2, T + P + 44, "years since this section was amended",
             12, MUTE, "middle"))
b.append(f'<text x="30" y="{T+P/2:.0f}" font-family="{FONT}" font-size="12" '
         f'fill="{MUTE}" text-anchor="middle" transform="rotate(-90 30 {T+P/2:.0f})">'
         f'median age of the rest of its part</text>')

QT = [(("frozen", "active"), VIOLET, "SETTLED", "frozen section, active part",
       "they reopened the part and left this alone"),
      (("frozen", "quiet"), MUTE, "FOSSIL", "frozen section, frozen part",
       "nobody has looked at this neighbourhood"),
      (("live", "quiet"), AQUA, "PROBLEM CHILD", "recent section, otherwise quiet part",
       "the one rule here they keep having to re-fix"),
      (("live", "active"), BLUE, "LIVE", "recent section, active part",
       "ordinary maintained regulation")]
lx, ly = L + P + 26, T + 6
b.append(txt(lx, ly, "Four populations", 13.5, INK, weight="600"))
for k, (key, col, name, sub, why) in enumerate(QT):
    yy = ly + 32 + k * 74
    n = cnt.get(key, 0)
    b.append(rect(lx, yy - 12, 4, 52, col))
    b.append(txt(lx + 14, yy, name, 12.5, col, weight="700"))
    b.append(txt(lx + 14, yy + 18, f"{n:,} sections · {100*n/N:.0f}%", 11.5, INK))
    b.append(txt(lx + 14, yy + 35, sub, 10.8, MUTE))
    for j, ln in enumerate(wrap(why, 300)):
        b.append(txt(lx + 14, yy + 51 + j * 13, ln, 10.8, MUTE, style="italic"))

idx = {r["section"]: r for r in live}
if ANN:
    ay = T + P + 74
    b.append(txt(40, ay, "Four sections, one from each population", 13, INK, weight="600"))
    for n, a in enumerate(ANN, 1):
        r = idx.get(a["section"])
        if not r:
            continue
        col = {("frozen", "active"): VIOLET, ("frozen", "quiet"): MUTE,
               ("live", "quiet"): AQUA}.get(cell(r), BLUE)
        b.append(circ(X(r["age"]), Y(r["pmed"]), 8.5, col, "#ffffff", 1.6))
        b.append(txt(X(r["age"]), Y(r["pmed"]) + 3.6, str(n), 10, "#ffffff", "middle", "700"))
        yy = ay + 22 + (n - 1) * 19
        b.append(circ(48, yy - 4, 8.5, col))
        b.append(txt(48, yy - 0.4, str(n), 10, "#ffffff", "middle", "700"))
        b.append(txt(64, yy, f"§ {a['section']}", 11.5, INK, weight="600"))
        b.append(txt(168, yy, a["note"], 11.5, MUTE))

# A third of sections were amended in the same action as their whole part, so
# they land on the diagonal carrying no within-part signal at all. That does not
# touch SETTLED or PROBLEM CHILD, which are off-diagonal by definition, but it
# does mean FOSSIL and LIVE include blocks nobody ever chose section by section.
on_diag = sum(1 for r in live if abs(r["age"] - r["pmed"]) < 0.05)
b.append(txt(40, H - 54, f"{on_diag:,} sections ({on_diag/N:.0%}) sit exactly on the "
             "diagonal because their whole part was amended in one action. They carry "
             "no within-part signal; this inflates", 10.5, MUTE))
b.append(txt(40, H - 38, "FOSSIL and LIVE, and cannot affect SETTLED or PROBLEM CHILD, "
             "which are off-diagonal by definition.", 10.5, MUTE))
b.append(txt(40, H - 22, f"Compared to the median of the OTHER dated sections in the "
             f"part; {len(solo)} sole dated sections are excluded for having no "
             "neighbourhood.", 10.5, MUTE))
b.append(txt(40, H - 6, "Source: eCFR full-text API, snapshot 2026-09-01. In-force "
             "sections carrying their own source note.", 10.5, MUTE))
open(os.path.join(CHARTS, "cfr-settled-vs-fossil.svg"), "w").write(doc(W, H, b))
print("cut", round(CUT, 1), "N", N, "max", round(MAX, 1))
for k, v in cnt.most_common():
    print(" ", k, v, f"{100*v/N:.1f}%")
