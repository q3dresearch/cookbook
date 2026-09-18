"""The same companies, on both sides of FDA's wall.

    python chart_wall.py

Animal-food notices clear 51% against human food's 79%. The obvious objection is
that animal filers are different companies — smaller, newer, worse at dossiers.
Eight firms file on both sides, which lets the objection be tested directly
rather than argued about.

They clear 84% of their human-food notices and 57% of their animal ones. Holding
the company fixed, the animal side is 27 points worse. n is 21 animal notices, so
the magnitude is soft and the direction is not: seven of the eight firms do worse
on the animal side or the same, and none does better by more than one notice.

Each firm is a line between its two rates. The thick line is the pooled total.
"""
import os, sys, re, math
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import graslib

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(os.path.dirname(HERE), "charts")
SUF = r"(inc|incorporated|llc|ltd|limited|co|corp|corporation|company|gmbh|a/s|ab|bv|nv|sa|srl|plc|pty|aps|oy|sas|sl|spa)"
TR = re.compile(rf"(\s+{SUF}\b\.?)+$", re.I)
def norm(n):
    n = (n or "").split(",")[0].split(";")[0].split(" doing business")[0]
    n = re.sub(r"[.,]", " ", n.lower())
    n = " ".join(re.sub(r"[^a-z0-9& /]", " ", n).split())
    p = None
    while p != n:
        p = n; n = TR.sub("", n).strip()
    return n
PRETTY = {"cj cheiljedang": "CJ CheilJedang", "dsm nutritional products": "DSM Nutritional",
          "basf": "BASF", "ab enzymes": "AB Enzymes", "kemin industries": "Kemin",
          "danisco us": "Danisco US", "intralytix": "Intralytix", "kerry": "Kerry"}

arows, src = graslib.load_animal()
hby, _ = graslib.load()
ag, hg = defaultdict(list), defaultdict(list)
for r in arows: ag[norm(r["notifier"])].append(r)
for r in hby.values(): hg[norm(r["notifier"])].append(r)
def ok(rs): return sum(1 for r in rs if r["outcome"] == "no questions") / len(rs)
both = sorted(set(ag) & set(hg), key=lambda k: -len(ag[k]))
pts = [(PRETTY.get(k, k), ok(ag[k]), len(ag[k]), ok(hg[k]), len(hg[k])) for k in both]
TA = sum(1 for k in both for r in ag[k] if r["outcome"] == "no questions")
NA = sum(len(ag[k]) for k in both)
TH = sum(1 for k in both for r in hg[k] if r["outcome"] == "no questions")
NH = sum(len(hg[k]) for k in both)

ANIMAL, HUMAN = "#c2553e", "#2361b0"
W, L, T, RH, R = 1020, 250, 244, 46, 250
H = T + (len(pts) + 2) * RH + 176
def sx(v): return L + v * (W - L - R)

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "The same companies do worse on the animal side of FDA's wall",
             20, INK, weight="600"))
b.append(txt(40, 70, "Animal-food notices clear 51% against human food's 79%. The obvious "
            "objection is that animal filers are different, smaller companies.", 13, MUTE))
b.append(txt(40, 89, "Eight firms file on both sides, so the objection can be tested "
            "instead of argued. Each line joins one firm's two clearance rates.", 13, MUTE))
b.append(txt(40, 115, "Holding the company fixed, the animal side is 27 points worse. "
            "n is 21 animal notices — the direction is solid, the magnitude is not.",
            12, MUTE))
b.append(circ(46, 143, 6, HUMAN))
b.append(txt(57, 147, "human food", 11.5, MUTE))
b.append(circ(176, 143, 6, ANIMAL))
b.append(txt(187, 147, "animal food", 11.5, MUTE))

for v in (0, .25, .5, .75, 1.0):
    b.append(line(sx(v), T - 14, sx(v), T + (len(pts) + 1) * RH - 10, GRID, 1))
    b.append(txt(sx(v), T - 22, f"{v:.0%}", 10.5, MUTE, "middle"))
b.append(txt(L - 14, T - 40, "share of notices FDA cleared", 11, MUTE, "end"))

for i, (name, a, na, h, nh) in enumerate(pts):
    y = T + i * RH
    b.append(line(sx(min(a, h)), y, sx(max(a, h)), y, MUTE, 1.6))
    if abs(a - h) < 0.01:
        b.append(circ(sx(h), y - 7, 7, HUMAN))
        b.append(circ(sx(a), y + 7, 7, ANIMAL))
        b.append(txt(sx(a) - 14, y + 4, "both", 10, MUTE, "end"))
    else:
        b.append(circ(sx(h), y, 7, HUMAN))
        b.append(circ(sx(a), y, 7, ANIMAL))
    b.append(txt(L - 14, y + 4, name, 12.5, INK, "end", "600"))
    b.append(txt(W - R + 14, y + 4, f"{na} animal · {nh} human", 11, MUTE))

y = T + (len(pts) + 0.7) * RH
b.append(line(40, y - 16, W - 40, y - 16, GRID, 1))
b.append(line(sx(TA / NA), y + 8, sx(TH / NH), y + 8, INK, 3))
b.append(circ(sx(TH / NH), y + 8, 9, HUMAN))
b.append(circ(sx(TA / NA), y + 8, 9, ANIMAL))
b.append(txt(L - 14, y + 12, "all eight pooled", 13, INK, "end", "700"))
b.append(txt(W - R + 14, y + 12, f"{NA} animal · {NH} human", 11, MUTE))
b.append(txt(sx(TA / NA), y - 4, f"{TA/NA:.0%}", 12, ANIMAL, "middle", "700"))
b.append(txt(sx(TH / NH), y - 4, f"{TH/NH:.0%}", 12, HUMAN, "middle", "700"))

yb = y + 66
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
b.append(txt(40, yb, "It is the programme, not the companies. AB Enzymes clears 76% of "
             "its 25 human notices and 0% of its 2 animal ones.", 13, INK, weight="600"))
b.append(txt(40, yb + 24, "That does not make the animal programme stricter for no "
             "reason. Feed goes to animals people then eat, and a pet-food ingredient has "
             "no human-food twin to borrow", 12, MUTE))
b.append(txt(40, yb + 41, "safety data from. It says only that the gap is not explained "
             "by who is doing the filing.", 12, MUTE))
b.append(txt(40, yb + 65, f"Firm names matched after stripping trailing legal suffixes, so "
             f"\"AB Enzymes GmbH\" and \"AB Enzymes, Inc.\" are one firm. Sources: FDA "
             f"human and animal GRAS inventories.", 11, MUTE))
open(os.path.join(CHARTS, "animal-vs-human-wall.svg"), "w").write(doc(W, H, b))
print(f"  animal-vs-human-wall.svg — {len(pts)} firms, pooled {TA/NA:.0%} animal "
      f"vs {TH/NH:.0%} human")
