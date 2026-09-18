"""Which kinds of ingredient are most likely to vanish from the record.

Encoding decisions, all of which are corrections to an earlier version:

  * Area WAS the number dropped. It correlated -0.38 with the x position, so
    area and position pulled against each other and the chart read as noisier
    than the data. Markers are now uniform.
  * The labels WERE "18 of 47". Both halves are already on the axes, so it was
    the same fact printed three times. Only the name survives.
  * Colour is the share of a kind's filings that come from a company appearing
    exactly once in the whole inventory. It correlates +0.48 with the dropout
    rate, which on eleven categories is suggestive and not a finding - it is
    drawn as a lead for the notifier question, and captioned as one.

The story is a slope, not a quadrant: dropout rate against filings correlates
-0.65. The more filings a kind of ingredient has behind it, the less likely any
one of them is to be dropped. Nothing here was banned - FDA has refused 20
filings ever. Dropped means the company stopped.

    python chart_kinds.py

The previous version ranked the 155 never-refiled notices by substance kind. That
is one axis: it says "there are more of these" and nothing about whether a kind is
unusually AT RISK. Twenty-three microbial biomass notices vanishing means one
thing if the category has 30 notices and another if it has 300.

So: across, how many of a kind were filed at all; up, what share of them ended
with the company pulling the notice and never coming back. The horizontal line is
the rate across everything. A kind above it fails more often than the average
ingredient, whatever its size.

Categories are inferred from the notice's own substance name, and are ours rather
than FDA's. 95% match a rule; the residue is shown as Other and greyed.
"""
import os, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import graslib

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(os.path.dirname(HERE), "charts")
MIN_N = 12

by, src = graslib.load()
rows = list(by.values())
def _norm(n): return " ".join((n or "").lower().replace(",", "").split())
filings_by_notifier = Counter(_norm(r["notifier"]) for r in rows)
tot, gone = Counter(), Counter()
example = {}
for r in rows:
    c = graslib.category(r["substance"])
    tot[c] += 1
    if r["outcome"] == "withdrawn" and not (r["next"] and str(r["next"]) != "None"):
        gone[c] += 1
        example.setdefault(c, r)
base = sum(gone.values()) / len(rows)
once = Counter()
for r in rows:
    if filings_by_notifier[_norm(r["notifier"])] == 1:
        once[graslib.category(r["substance"])] += 1
pts = [{"cat": c, "n": tot[c], "g": gone[c], "rate": gone[c] / tot[c],
        "one": once[c] / tot[c]} for c in tot if tot[c] >= MIN_N]
XMAX = max(p["n"] for p in pts) * 1.10
YMAX = max(max(p["rate"] for p in pts) * 1.18, base * 2)

W, L, T, PH, R = 1130, 150, 236, 400, 300
H = T + PH + 300
def sx(v): return L + v / XMAX * (W - L - R)
def sy(v): return T + PH - v / YMAX * PH
R_MARK = 9.5

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "Which kinds of ingredient get abandoned before FDA finishes",
             20, INK, weight="600"))
b.append(txt(40, 70, "One filing = one company telling FDA about one new ingredient. "
            "Across: how many ingredients OF THIS KIND have ever been put to FDA.",
            13, MUTE))
b.append(txt(40, 89, "Up: the share of those that the company pulled and never filed "
            "again. Colour: how much of that kind comes from companies that file once "
            "and never appear again.", 13, MUTE))
b.append(txt(40, 115, "A filing is almost always ONE substance, not a recipe with "
            "components: only 20 of 1,336 cover several at once, and those behave no "
            "differently (10% dropped against 12%).", 12, MUTE))
b.append(txt(40, 133, f"The flat line is the rate across everything ({base:.0%}); the "
            f"sloping one is the fit. Nothing here was banned — FDA has refused 20 "
            f"filings ever. Dropped means the company stopped.", 12, MUTE))

for v in (0, .05, .10, .15, .20, .25, .30, .35, .40):
    if v > YMAX: break
    b.append(line(L, sy(v), W - R, sy(v), GRID, 1))
    b.append(txt(L - 10, sy(v) + 4, f"{v:.0%}", 10.5, MUTE, "end"))
for v in range(0, int(XMAX) + 1, 50):
    if v == 0: continue
    b.append(line(sx(v), T, sx(v), T + PH, GRID, 1))
    b.append(txt(sx(v), T + PH + 20, str(v), 10.5, MUTE, "middle"))
b.append(txt(L - 10, T - 28, "abandoned for good", 11.5, INK, "end", "600"))
b.append(txt(L - 10, T - 12, "share of this kind's filings", 10.5, MUTE, "end"))
b.append(txt(W - R, T + PH + 44, "ingredients of this kind ever put to FDA", 11.5, INK, "end", "600"))
b.append(f'<line x1="{L}" y1="{sy(base):.1f}" x2="{W-R}" y2="{sy(base):.1f}" '
         f'stroke="{VIOLET}" stroke-width="1.3" stroke-dasharray="5 4"/>')
b.append(txt(W - R - 6, sy(base) - 8, f"all filings · {base:.0%}", 10.5, VIOLET, "end"))

RAMP = ["#cfe0f2", "#93b9e0", "#5a90cc", "#2f6cb0", "#1a4b85"]
def shade(o): return RAMP[min(int((o - 0.24) / 0.09), len(RAMP) - 1)]

# The slope IS the story, so draw it. Least squares on the eleven categories.
xs = [p["n"] for p in pts]; ys = [p["rate"] for p in pts]
mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
den = sum((x - mx) ** 2 for x in xs)
m = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0
c0 = my - m * mx
b.append(f'<line x1="{sx(0):.1f}" y1="{sy(c0):.1f}" x2="{sx(XMAX):.1f}" '
         f'y2="{sy(max(c0 + m * XMAX, 0)):.1f}" stroke="{MUTE}" stroke-width="1.2" '
         f'stroke-dasharray="6 4"/>')
b.append(txt(sx(XMAX * 0.60), sy(max(c0 + m * XMAX * 0.60, 0)) - 12,
             "fewer dropped as a category fills out", 10.5, MUTE, "middle"))

for p in sorted(pts, key=lambda p: -p["n"]):
    b.append(circ(sx(p["n"]), sy(p["rate"]), R_MARK, shade(p["one"])))

marks = [(sx(p["n"]), sy(p["rate"]), R_MARK) for p in pts]
taken = []
def free(bx):
    return not (any(bx[0] < o[2] and o[0] < bx[2] and bx[1] < o[3] and o[1] < bx[3]
                    for o in taken)
                or any(bx[0] < cx + r and cx - r < bx[2] and bx[1] < cy + r and cy - r < bx[3]
                       for cx, cy, r in marks))
for p in sorted(pts, key=lambda p: -p["rate"]):
    lab = p["cat"]
    x, y, r = sx(p["n"]), sy(p["rate"]), R_MARK
    w = len(lab) * 6.1 + 8
    for dy in (0, -15, 15, -30, 30, -45, 45):
        for anc in ("start", "end"):
            x0 = x + r + 7 if anc == "start" else x - r - 7 - w
            bx = (x0, y + dy - 8, x0 + w, y + dy + 6)
            if bx[0] < L + 2 or bx[2] > W - R - 20 or not free(bx):
                continue
            taken.append(bx)
            b.append(txt(x + (r + 7 if anc == "start" else -r - 7), y + dy + 4, lab,
                         11, INK, anc))
            break
        else:
            continue
        break

lx, ly = W - R + 30, T + 20
b.append(txt(lx, ly, "filed by a company that", 11, MUTE))
b.append(txt(lx, ly + 15, "appears once, and never again", 11, MUTE))
for i, c in enumerate(RAMP):
    b.append(rect(lx + i * 26, ly + 26, 24, 14, c))
b.append(txt(lx, ly + 56, "25%", 10.5, MUTE))
b.append(txt(lx + 5 * 26 - 2, ly + 56, "60%", 10.5, MUTE, "end"))
b.append(txt(lx, ly + 82, "Suggestive only: r = +0.48", 10.5, MUTE))
b.append(txt(lx, ly + 97, "across eleven categories.", 10.5, MUTE))

hi = max(pts, key=lambda p: p["rate"])
yb = T + PH + 76
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
b.append(txt(40, yb, "The more filings a kind of ingredient has behind it, the less "
             "often any one of them is dropped — r = -0.65.", 13, INK, weight="600"))
b.append(txt(40, yb + 21, f"{hi['cat']} sits worst at {hi['rate']:.0%}, "
             f"{hi['rate']/base:.1f}× the overall rate.", 13, INK, weight="600"))
b.append(txt(40, yb + 45, "These are overwhelmingly novel ingredients from B2B suppliers "
             "and start-ups — precision fermentation, algal oils, enzymes, "
             "oligosaccharides — not established additives in", 12, MUTE))
b.append(txt(40, yb + 62, "consumer products. Which is what you would expect if the "
             "binding constraint is a small company's ability to fund a dossier, "
             "rather than the ingredient being unsafe.", 12, MUTE))
b.append(txt(40, yb + 86, "“Other” is not a leftover — it is the largest "
             "group (454) and it is the conventional additives: sodium bisulfate, "
             "transglutaminase, pectin esterase, tasteless smoke. Established", 11, MUTE))
b.append(txt(40, yb + 103, "chemistry with a known dossier, which is why it sits at the "
             "bottom. Read it as the baseline the novel categories are being compared "
             "against, not as a leftover.", 11, MUTE))
b.append(txt(40, yb + 127, "Each notice is filed under the FIRST category rule its "
             "substance name matches; 14% match more than one, usually because the name "
             "describes an enzyme by its source organism.", 11, MUTE))
b.append(txt(40, yb + 144, "That moves the category SIZES a lot — recombinant protein "
             "runs 85 or 18 depending on rule order — but not the slope: across 200 "
             "random rule orders r stays between -0.68 and -0.53.", 11, MUTE))
b.append(txt(40, yb + 168, "Categories are inferred from the substance name and are ours, "
             f"not FDA's. Kinds under {MIN_N} filings are omitted. "
             f"Source: {os.path.basename(src)}.", 11, MUTE))
open(os.path.join(CHARTS, "gras-withdrawn-kinds.svg"), "w").write(doc(W, H, b))
print(f"  gras-withdrawn-kinds.svg — {len(pts)} kinds, base rate {base:.1%}")
for p in sorted(pts, key=lambda p: -p["rate"]):
    print(f"    {p['cat'][:32]:32s} {p['g']:3d}/{p['n']:3d} = {p['rate']:5.1%}")
