"""How animal notices end, against human food, and how that has moved.

    python chart_outcomes.py

Animal notices clear 51% against human food's 79%, and the gap is not one
failure mode. Every one is elevated: withdrawn 34% against 16.8%, refused 6.4%
against 1.5%, still pending 8.5% against 2.6%. Two to four times worse on each.

The lower panel is the same outcomes by era, which answers two more questions at
once. The withdrawal rate has no trend — 33%, 24%, 47%, 19% — and the last block
is likely censored because eight notices are still pending, all filed 2025 or
later. But "FDA declined to assess whether it works" goes 0%, 0%, 23%, 24%: FDA
now clears roughly a quarter of animal notices on safety while explicitly saying
nothing about utility.

Wilson intervals on the animal shares, because 94 notices is small enough that a
point estimate invites more confidence than it has earned.
"""
import os, sys, math
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import graslib

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(os.path.dirname(HERE), "charts")
UT = "Utility information not evaluated"
CL, WD, RJ, PD = "#2e7d5b", "#c2553e", "#7a2f22", "#b9b4a8"
ORDER = [("no questions", "FDA had no questions", CL), ("withdrawn", "pulled by the company", WD),
         ("rejected", "refused", RJ), ("pending", "still pending", PD)]

arows, src = graslib.load_animal()
hby, _ = graslib.load()
A, Hm = Counter(r["outcome"] for r in arows), Counter(r["outcome"] for r in hby.values())
NA, NH = len(arows), len(hby)
def wilson(k, n):
    z = 1.96; p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - m, c + m
def yr(r): return int(r["filed"].split("/")[-1]) if r["filed"] else None

W, L, T, R = 1080, 260, 244, 250
RH, PH2, GAP = 52, 176, 130
H = T + len(ORDER) * RH + GAP + PH2 + 240
BARW = W - L - R
def sx(v): return L + v * BARW

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "Every way an animal notice can fail is more likely than for human food",
             20, INK, weight="600"))
b.append(txt(40, 70, "How notices end, animal against human. The animal bars carry a 95% "
            "interval, because 94 notices is small enough that a bare", 13, MUTE))
b.append(txt(40, 89, "percentage invites more confidence than it has earned. Human food is "
            "1,336 notices and its intervals are about two points wide.", 13, MUTE))
b.append(txt(40, 115, "It is not one failure mode: withdrawal is twice as likely, outright "
            "refusal four times, and still-pending three times.", 12, MUTE))

for i, (k, lab, c) in enumerate(ORDER):
    y = T + i * RH
    a, h = A[k] / NA, Hm[k] / NH
    lo, hi = wilson(A[k], NA)
    b.append(txt(L - 18, y + 5, lab, 13, INK, "end", "600"))
    b.append(rect(L, y - 11, sx(a) - L, 24, c, rx=3))
    b.append(f'<line x1="{sx(lo):.1f}" y1="{y+1}" x2="{sx(hi):.1f}" y2="{y+1}" '
             f'stroke="{INK}" stroke-width="1.5"/>')
    for e in (lo, hi):
        b.append(f'<line x1="{sx(e):.1f}" y1="{y-6}" x2="{sx(e):.1f}" y2="{y+8}" '
                 f'stroke="{INK}" stroke-width="1.5"/>')
    b.append(txt(sx(hi) + 12, y + 5, f"{a:.0%}", 13, INK, weight="700"))
    b.append(f'<line x1="{sx(h):.1f}" y1="{y-14}" x2="{sx(h):.1f}" y2="{y+16}" '
             f'stroke="#2361b0" stroke-width="2.5"/>')
    b.append(txt(sx(h), y - 20, f"{h:.0%}", 11, "#2361b0", "middle", "700"))
b.append(txt(L, T - 30, "animal bar, with its 95% interval", 11, MUTE))
b.append(f'<line x1="{W-R+14}" y1="{T-42}" x2="{W-R+14}" y2="{T-26}" stroke="#2361b0" stroke-width="2.5"/>')
b.append(txt(W - R + 24, T - 30, "human food", 11, "#2361b0"))

T2 = T + len(ORDER) * RH + GAP
BLOCKS = [(2010, "2010–14"), (2015, "2015–19"), (2020, "2020–24"), (2025, "2025–29")]
BW = BARW / len(BLOCKS)
b.append(txt(40, T2 - 40, "The same outcomes by era, plus the notices FDA declined to "
             "assess", 14, INK, weight="600"))
UTS = []
for _b0, _lab in BLOCKS:
    _g = [r for r in arows if yr(r) and _b0 <= yr(r) < _b0 + 5]
    UTS.append(sum(1 for r in _g if UT in r["use"]) / len(_g) if _g else 0)
b.append(txt(40, T2 - 22, "Withdrawal has no trend. “FDA did not say whether it works” "
             "went " + ", ".join(f"{v:.0%}" for v in UTS) + ".", 12, MUTE))
for i, (b0, lab) in enumerate(BLOCKS):
    g = [r for r in arows if yr(r) and b0 <= yr(r) < b0 + 5]
    if not g: continue
    x = L + i * BW + BW * 0.18
    w = BW * 0.64
    acc = 0.0
    for k, _, c in ORDER:
        v = sum(1 for r in g if r["outcome"] == k) / len(g)
        if not v: continue
        hgt = v * PH2
        b.append(rect(x, T2 + PH2 - acc - hgt, w, hgt, c))
        acc += hgt
    ut = sum(1 for r in g if UT in r["use"]) / len(g)
    b.append(f'<line x1="{x:.1f}" y1="{T2+PH2-ut*PH2:.1f}" x2="{x+w:.1f}" '
             f'y2="{T2+PH2-ut*PH2:.1f}" stroke="#f0b44a" stroke-width="3"/>')
    b.append(txt(x + w + 8, T2 + PH2 - ut * PH2 + 4, f"{ut:.0%}", 11, "#b8860b", "start",
                 "700"))
    b.append(txt(x + w / 2, T2 + PH2 + 22, lab, 12, MUTE, "middle"))
    b.append(txt(x + w / 2, T2 + PH2 + 38, f"n={len(g)}", 10.5, MUTE, "middle"))
b.append(rect(W - R + 14, T2 + 4, 22, 3, "#f0b44a"))
b.append(txt(W - R + 44, T2 + 9, "share FDA declined", 11, MUTE))
b.append(txt(W - R + 44, T2 + 25, "to assess for utility", 11, MUTE))

yb = T2 + PH2 + 88
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
b.append(txt(40, yb, "Animal notices clear 51% (95% CI 41–61%) against human food's 79% "
             "(77–81%). The intervals do not touch, so this is not a small-sample artefact.",
             13, INK, weight="600"))
b.append(txt(40, yb + 24, "The withdrawal rate itself has no trend and the final block is "
             "probably censored — all eight pending notices were filed in 2025 or later, "
             "so some will yet be pulled.", 12, MUTE))
b.append(txt(40, yb + 41, "The yellow line is the one that moved: nothing before 2015, "
             "then FDA clearing a sixth to a third of animal notices while stating it did "
             "not evaluate whether the ingredient works.", 12, MUTE))
b.append(txt(40, yb + 58, "Where exactly that sits depends on the block boundaries — "
             "five-year blocks give " + ", ".join(f"{v:.0%}" for v in UTS) + " and "
             "four-year blocks give 0%, 0%, 23%, 24%. The rise is the finding, not "
             "the last figure.", 12, MUTE))
b.append(txt(40, yb + 84, f"94 animal notices against 1,336 human ones. Wilson intervals. "
             f"Sources: FDA animal and human food GRAS inventories, "
             f"{os.path.basename(src)}.", 11, MUTE))
open(os.path.join(CHARTS, "animal-outcomes.svg"), "w").write(doc(W, H, b))
print("  animal-outcomes.svg")
for k, lab, _ in ORDER:
    lo, hi = wilson(A[k], NA)
    print(f"    {lab:24s} animal {A[k]/NA:5.1%} (CI {lo:.0%}-{hi:.0%})  human {Hm[k]/NH:5.1%}")
