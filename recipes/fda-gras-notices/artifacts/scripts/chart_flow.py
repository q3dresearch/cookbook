"""Where 1,336 GRAS filings ended up, as a flow.

    python chart_flow.py

A company that wants to sell a new food ingredient can tell FDA it has decided
the ingredient is safe. FDA reads the file and replies. The best reply available
is not "approved" — it is "we have no questions".

This is every reply since 1998, and then what happened to the ones the company
pulled before FDA finished. Three stages, drawn as a flow because that is what it
is: the previous version was three stacked bars, which is a table with rounded
corners and hides that the third stage is a subset of the second.

Deliberately plain wording. The file says "at the notifier's request, FDA ceased
to evaluate this notice"; this chart says "the company pulled it". It says
"Resubmitted"; this says "filed again". A reader who does not already work in
food regulation should be able to read the chart without a glossary.
"""
import os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import graslib

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(os.path.dirname(HERE), "charts")
by, src = graslib.load()

n_total = len(by)
out = Counter(r["outcome"] for r in by.values())
wd = [r for r in by.values() if r["outcome"] == "withdrawn"]
again = [r for r in wd if r["next"] and str(r["next"]) != "None"]
ends = Counter(graslib.chain(r, by)[-1]["outcome"] for r in again)

GREEN, GREY, RED, AMBER = "#2e9e6b", "#8a8f98", "#d1495b", "#e8963c"

# stage -> [(label, sub, count, colour)] , drawn top to bottom within a column
S1 = [("FDA had no questions", "its version of a yes", out["no questions"], GREEN),
      ("The company pulled it", "before FDA finished reading", out["withdrawn"], AMBER),
      ("Still being read", "filed, no reply yet", out["pending"], GREY),
      ("FDA said the file was not enough", "the only outright no", out["rejected"], RED)]
S2 = [("Filed again later", "same ingredient, new number", len(again), AMBER),
      ("Never seen again", "FDA's records end here", len(wd) - len(again), GREY)]
S3 = [("FDA had no questions", "cleared on a later try", ends["no questions"], GREEN),
      ("Pulled again", "", ends["withdrawn"], AMBER),
      ("File was not enough", "", ends["rejected"], RED)]

W, T, H = 1120, 230, 730
COLX = [300, 620, 900]
COLW = 26
GAP = 30
SCALE = 250 / max(n_total, 1)          # pixels per notice, one scale everywhere


def column(items, x, y0, scale):
    """Stack boxes down from y0, returning (label, y, height, colour, count)."""
    out, y = [], y0
    for lab, sub, n, col in items:
        h = max(n * scale, 2.5)
        out.append((lab, sub, y, h, col, n))
        y += h + GAP
    return out


def ribbon(x1, y1, h1, x2, y2, h2, col, op=0.28):
    c = (x1 + x2) / 2
    return (f'<path d="M{x1},{y1} C{c},{y1} {c},{y2} {x2},{y2} '
            f'L{x2},{y2+h2} C{c},{y2+h2} {c},{y1+h1} {x1},{y1+h1} Z" '
            f'fill="{col}" fill-opacity="{op}"/>')


b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "What happens to a new food ingredient after a company tells FDA "
             "about it", 20, INK, weight="600"))
b.append(txt(40, 70, f"All {n_total:,} filings FDA has closed since 1998. Companies "
            f"decide for themselves that an ingredient is safe and notify FDA; FDA "
            f"reads the file and replies.", 13, MUTE))
b.append(txt(40, 89, "Band height is the number of filings, on one scale throughout. "
            "The second and third columns follow only the filings the company pulled.",
            13, MUTE))
b.append(txt(40, 115, "The best reply available is “we have no questions”. FDA "
            "does not approve these; it declines to object.", 12, MUTE))

c1 = column(S1, COLX[0], T, SCALE)
pulled = next(x for x in c1 if x[0].startswith("The company pulled"))
c2 = column(S2, COLX[1], pulled[2], SCALE)
filed = next(x for x in c2 if x[0].startswith("Filed again"))
c3 = column(S3, COLX[2], filed[2], SCALE)

for lab, sub, y, h, col, n in c1:
    if lab.startswith("The company pulled"):
        b.append(ribbon(COLX[0] + COLW, y, h, COLX[1], c2[0][2],
                        sum(x[3] for x in c2) + GAP * (len(c2) - 1), col))
for lab, sub, y, h, col, n in c2:
    if lab.startswith("Filed again"):
        b.append(ribbon(COLX[1] + COLW, y, h, COLX[2], c3[0][2],
                        sum(x[3] for x in c3) + GAP * (len(c3) - 1), col))

for ci, colm in enumerate((c1, c2, c3)):
    for lab, sub, y, h, col, n in colm:
        b.append(rect(COLX[ci], y, COLW, h, col, rx=3))
        ty = y + h / 2
        if ci == 0:
            b.append(txt(COLX[ci] - 14, ty - (2 if not sub else 6), lab, 12.5, INK, "end",
                         "600"))
            if sub:
                b.append(txt(COLX[ci] - 14, ty + 11, sub, 10.5, MUTE, "end"))
            b.append(txt(COLX[ci] + COLW + 9, ty + 4, f"{n:,}", 12.5, INK, weight="600"))
        else:
            b.append(txt(COLX[ci] + COLW + 10, ty - (2 if not sub else 6), lab, 12.5, INK,
                         weight="600"))
            if sub:
                b.append(txt(COLX[ci] + COLW + 10, ty + 11, sub, 10.5, MUTE))
            b.append(txt(COLX[ci] - 9, ty + 4, f"{n:,}", 12.5, INK, "end", "600"))

for ci, head in enumerate(("FDA's reply", "of the ones pulled…", "…and then")):
    b.append(txt(COLX[ci] + COLW / 2, T - 26, head, 11.5, MUTE, "middle",
                 style="font-style:italic"))

yb = H - 108
b.append(line(40, yb - 24, W - 40, yb - 24, GRID, 1))
b.append(txt(40, yb, f"{out['withdrawn']} filings were pulled by the company — "
             f"{out['withdrawn']/n_total:.0%} of everything closed, and "
             f"{out['withdrawn']/max(out['rejected'],1):.0f} times more often than FDA "
             f"said no.", 13, INK, weight="600"))
b.append(txt(40, yb + 22, f"{len(wd)-len(again):,} of them were never seen again. FDA "
             f"links a later filing only when it knows the two are related, so that "
             f"number is an upper bound on “abandoned” — a company can also "
             f"refile by", 12, MUTE))
b.append(txt(40, yb + 39, "another route, or sell the ingredient without telling FDA at "
             "all, which the law allows and this file cannot see.", 12, MUTE))
b.append(txt(40, yb + 62, f"Source: FDA GRAS Notice Inventory, {os.path.basename(src)}. "
             f"Chains followed through FDA's own Resubmitted / Resubmission fields, "
             f"cycle-guarded.", 11, MUTE))
open(os.path.join(CHARTS, "gras-flow.svg"), "w").write(doc(W, H, b))
print(f"  gras-flow.svg — {n_total:,} filings, {out['withdrawn']} pulled, "
      f"{len(again)} filed again, {ends['no questions']} of those cleared")
