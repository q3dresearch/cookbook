"""What the code keeps adding, against what it stops touching.

    CFR_WORK=./work python chart_lifecycle.py

Across: the share of a category's sections first published in 2010 or later —
what the agency is still writing. Up: the share older than its title's median —
what it has stopped touching. Area is how many sections. Colour is the title.

Capital & risk in banking is the outlier on both axes: 84% written since 2010 and
only 24% stale. That is Dodd-Frank and Basel III arriving as text. Consumer
disclosure is its mirror — 53% new but 62% stale, a category being added to and
abandoned at the same time, because new products get new rules while the old
disclosure regime is never reopened.

Labour law barely rewrites itself at all: its most-renewed category is Procedure
& appeals at 40%, against banking's 84%. What changes in Title 29 is how you
file, not what the rule says.
"""
import os, sys, collections, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import cfrlib

OUT = os.path.join(cfrlib.CHARTS, "cfr-lifecycle.svg")
TITLES = [("12", "Title 12 — Banks and Banking", BLUE),
          ("29", "Title 29 — Labor", ORANGE)]
MIN_N = 40

pts = []
for t, name, col in TITLES:
    rows, live = cfrlib.load(os.path.join(cfrlib.DERIVED, f"cfr-title{t}-sections.csv"))
    cut = st.median([r["age"] for r in live])
    g = collections.defaultdict(list)
    for r in live:
        g[cfrlib.category(r)].append(r)
    for c, v in g.items():
        if len(v) < MIN_N or c == "Other":
            continue
        pts.append({"t": t, "col": col, "cat": c, "n": len(v),
                    "new": sum(1 for r in v if r["born"] and r["born"] >= 2010) / len(v),
                    "old": sum(1 for r in v if r["age"] >= cut) / len(v)})

nmax = max(p["n"] for p in pts)
W, L, T, P, R = 1120, 168, 196, 470, 320
H = T + P + 196
def sx(v): return L + v * P
def sy(v): return T + P - v * P
def sr(n): return 6 + (n / nmax) ** 0.5 * 16

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "What the code keeps writing, and what it stops touching",
             20, INK, weight="600"))
b.append(txt(40, 70, "Each dot is one functional category within a title. Across: share "
            "of its sections first published in 2010 or later. Up: share older than",
            13, MUTE))
b.append(txt(40, 89, "that title's median age. Area is how many sections. Both axes are "
            "shares of the same population, so the diagonal is a fair reference.",
            13, MUTE))
b.append(txt(40, 115, "Top-left is abandoned; bottom-right is actively rewritten. "
            "Top-right is both at once — new rules piling up beside old ones nobody "
            "reopens.", 12, MUTE))
for i, (t, name, col) in enumerate(TITLES):
    b.append(circ(44 + i * 260, 141, 6, col))
    b.append(txt(56 + i * 260, 145, name, 11.5, MUTE))

for v in (0, .25, .5, .75, 1.0):
    b.append(line(L, sy(v), L + P, sy(v), GRID, 1))
    b.append(txt(L - 10, sy(v) + 4, f"{v:.0%}", 10.5, MUTE, "end"))
    b.append(line(sx(v), T, sx(v), T + P, GRID, 1))
    b.append(txt(sx(v), T + P + 20, f"{v:.0%}", 10.5, MUTE, "middle"))
b.append(txt(L - 12, T - 26, "stopped touching", 11.5, INK, "end", "600"))
b.append(txt(L - 12, T - 10, "older than the title median", 10.5, MUTE, "end"))
b.append(txt(L + P, T + P + 44, "still writing  ·  share born 2010 or later",
             11.5, INK, "end", "600"))
b.append(f'<line x1="{sx(0):.1f}" y1="{sy(0):.1f}" x2="{sx(1):.1f}" y2="{sy(1):.1f}" '
         f'stroke="{GRID}" stroke-width="1" stroke-dasharray="5 5"/>')
b.append(txt(L + 8, T + 72, "abandoned", 11.5, MUTE, style="font-style:italic"))
b.append(txt(L + P - 8, T + P - 10, "actively rewritten", 11.5, MUTE, "end",
             style="font-style:italic"))

# 23 labels do not fit. Label only what carries the argument — the extremes on
# each axis plus the largest categories — and let area and colour do the rest.
# A first version pushed every label down until they ran off the bottom.
def extremes(key, n=3, rev=False):
    return [q["cat"] + q["t"] for q in sorted(pts, key=lambda q: q[key], reverse=not rev)[:n]]
keep = set(extremes("new") + extremes("new", rev=True)
           + extremes("old") + extremes("old", rev=True)
           + extremes("n", 2))
for q in pts:
    if q["cat"] == "Disclosure & consumer":
        keep.add(q["cat"] + q["t"])

for q in sorted(pts, key=lambda q: -q["n"]):
    b.append(circ(sx(q["new"]), sy(q["old"]), sr(q["n"]), q["col"]))

marks = [(sx(q["new"]), sy(q["old"]), sr(q["n"])) for q in pts]
taken = []
def free(bx):
    return not (any(bx[0] < o[2] and o[0] < bx[2] and bx[1] < o[3] and o[1] < bx[3]
                    for o in taken)
                or any(bx[0] < cx + r and cx - r < bx[2] and bx[1] < cy + r and cy - r < bx[3]
                       for cx, cy, r in marks))
for q in sorted(pts, key=lambda q: -q["n"]):
    if q["cat"] + q["t"] not in keep:
        continue
    lab = f"{q['cat']} ({q['n']})"
    x, y, r = sx(q["new"]), sy(q["old"]), sr(q["n"])
    w = len(lab) * 6.1 + 8
    for dy in (0, -15, 15, -30, 30, -45, 45):
        for anc in ("start", "end"):
            x0 = x + r + 7 if anc == "start" else x - r - 7 - w
            bx = (x0, y + dy - 8, x0 + w, y + dy + 6)
            if bx[0] < L - 46 or bx[2] > L + P + R - 30 or not free(bx):
                continue
            taken.append(bx)
            b.append(txt(x + (r + 7 if anc == "start" else -r - 7), y + dy + 4, lab,
                         11, INK, anc))
            break
        else:
            continue
        break

yb = T + P + 84
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
b.append(txt(40, yb, "Banking rewrites itself where the statute told it to, and nowhere "
             "else. Labour law barely rewrites itself at all.", 13, INK, weight="600"))
b.append(txt(40, yb + 22, "Capital & risk is 84% written since 2010 and only 24% stale — "
             "Dodd-Frank and Basel III arriving as text. Consumer disclosure is 53% new "
             "AND 62% stale: new products get new", 12, MUTE))
b.append(txt(40, yb + 39, "rules while the old disclosure regime is never reopened. "
             "Title 29's most-renewed category is Procedure & appeals at 40% — what "
             "changes there is how you file, not what the rule says.", 12, MUTE))
b.append(txt(40, yb + 63, f"Categories are inferred from section headings by keyword and "
             f"are ours, not the publisher's; “Other” (688 and 1,078 sections) is "
             f"excluded, as is any category under {MIN_N}.", 11, MUTE))
b.append(txt(40, yb + 80, "Shares are of the dated subset (35% and 33%). “Born” is the "
             "earliest surviving citation, so a wholly rewritten section reads as new. "
             "Source: eCFR full-text API, snapshot 2026-09-01.", 11, MUTE))
open(OUT, "w").write(doc(W, H, b))
print(f"  cfr-lifecycle.svg — {len(pts)} categories")
for p in sorted(pts, key=lambda p: -p["new"]):
    print(f"    T{p['t']} {p['cat'][:24]:24s} n={p['n']:4d}  new {p['new']:4.0%}  stale {p['old']:4.0%}")
