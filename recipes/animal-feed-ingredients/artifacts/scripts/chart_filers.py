"""Who files, how many, and whether experience helps.

    python chart_filers.py

Three questions that are all about the notifier rather than the ingredient:

  * Is the programme growing? Yes — 15, 10, 29 and 34 notices per four-year
    block. It roughly doubled.
  * Is it concentrating? No, the opposite. On the four-year blocks this chart
    draws, the top three firms were 60% of 2010-13 filings and 24% of 2022-25,
    and the number of distinct firms per block went 8, 9, 16, 24. (The questions
    file quotes 56% to 29% because it cuts five-year blocks; same direction,
    different boundaries.)
  * Does filing repeatedly help? Yes, and in the same direction as human food:
    a firm's first-and-only notice clears 38%, a firm that files two or three
    clears 57%, four or more 54%.

The growth and the deconcentration are the same fact seen twice: more firms are
trying, so the programme is broadening rather than being worked by a few
incumbents.
"""
import os, sys, re
from collections import Counter
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
    while p != n: p = n; n = TR.sub("", n).strip()
    return n

rows, src = graslib.load_animal()
def yr(r): return int(r["filed"].split("/")[-1]) if r["filed"] else None
def ok(rs): return sum(1 for r in rs if r["outcome"] == "no questions") / len(rs)
BLOCKS = [(2010, "2010–13"), (2014, "2014–17"), (2018, "2018–21"), (2022, "2022–25")]
tot = Counter(norm(r["notifier"]) for r in rows)

W, L, T, R = 1060, 108, 250, 300
PH, GAP = 190, 118
H = T + PH * 2 + GAP + 190
BW = (W - L - R) / len(BLOCKS)

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "More firms are trying, and the ones that keep trying do better",
             20, INK, weight="600"))
b.append(txt(40, 70, "The animal-food GRAS programme has roughly doubled in notices and "
            "spread across more companies at the same time. Top: notices filed", 13, MUTE))
b.append(txt(40, 89, "per four-year block, split by how many distinct firms filed them. "
            "Bottom: how often a notice clears, by how many times its firm has filed.",
            13, MUTE))
b.append(txt(40, 115, "94 notices and 49 firms in total. Every bar here is small — the "
            "counts are printed for that reason.", 12, MUTE))

mx = max(sum(1 for r in rows if yr(r) and b0 <= yr(r) < b0 + 4) for b0, _ in BLOCKS)
b.append(txt(L - 12, T - 26, "notices filed", 12, INK, "end", "600"))
for i, (b0, lab) in enumerate(BLOCKS):
    g = [r for r in rows if yr(r) and b0 <= yr(r) < b0 + 4]
    firms = Counter(norm(r["notifier"]) for r in g)
    top3 = sum(n for _, n in firms.most_common(3))
    x = L + i * BW + BW * 0.20
    w = BW * 0.60
    h = len(g) / mx * PH
    b.append(rect(x, T + PH - h, w, h, "#b9c9dd", rx=3))
    ht = top3 / mx * PH
    b.append(rect(x, T + PH - ht, w, ht, "#2361b0", rx=3))
    b.append(txt(x + w / 2, T + PH - h - 10, f"{len(g)}", 13, INK, "middle", "700"))
    b.append(txt(x + w / 2, T + PH - ht / 2 + 4, f"{top3/len(g):.0%}", 11.5,
                 "#ffffff", "middle", "700"))
    b.append(txt(x + w / 2, T + PH + 22, lab, 12, MUTE, "middle"))
    b.append(txt(x + w / 2, T + PH + 39, f"{len(firms)} firms", 10.5, MUTE, "middle"))
b.append(rect(W - R + 40, T + 6, 12, 12, "#2361b0"))
b.append(txt(W - R + 58, T + 16, "the three biggest filers", 11.5, MUTE))
b.append(rect(W - R + 40, T + 30, 12, 12, "#b9c9dd"))
b.append(txt(W - R + 58, T + 40, "everyone else", 11.5, MUTE))
first3 = None
b.append(txt(W - R + 40, T + 74, "Top-3 share falls 60% to 24%.", 11.5, INK))
b.append(txt(W - R + 40, T + 91, "The programme is broadening,", 11.5, MUTE))
b.append(txt(W - R + 40, T + 108, "not consolidating.", 11.5, MUTE))

T2 = T + PH + GAP
L2 = 250
b.append(txt(L2 - 12, T2 - 26, "share of notices cleared", 12, INK, "end", "600"))
BANDS = [("its first and only notice", 1, 1), ("a firm filing 2–3", 2, 3),
         ("a firm filing 4 or more", 4, 99)]
for i, (lab, lo, hi) in enumerate(BANDS):
    g = [r for r in rows if lo <= tot[norm(r["notifier"])] <= hi]
    yy = T2 + i * 46
    b.append(txt(L2 - 12, yy + 5, lab, 12.5, INK, "end"))
    wdt = ok(g) * (W - L2 - R)
    b.append(rect(L2, yy - 10, wdt, 22, "#2e7d5b", rx=3))
    b.append(txt(L2 + wdt + 10, yy + 5, f"{ok(g):.0%}", 12.5, INK, weight="600"))
    b.append(txt(L2 + wdt + 52, yy + 5, f"n={len(g)}", 11, MUTE))

yb = T2 + 3 * 46 + 58
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
b.append(txt(40, yb, "Filing once and never again clears 38%. Filing repeatedly clears "
             "54–57% — the same direction as human food, where it is 76% against 86%.",
             13, INK, weight="600"))
b.append(txt(40, yb + 24, "Which is not necessarily a lesson about persistence. A firm "
             "that files four times is a firm that had four ingredients worth filing, "
             "and that is a different kind of company", 12, MUTE))
b.append(txt(40, yb + 41, "from one with a single product. The data cannot separate "
             "learning from selection, and this chart should not be read as saying "
             "it can.", 12, MUTE))
b.append(txt(40, yb + 65, f"Firm names matched after stripping trailing legal suffixes. "
             f"49 distinct firms across 94 notices. Source: FDA animal food GRAS "
             f"inventory, {os.path.basename(src)}.", 11, MUTE))
open(os.path.join(CHARTS, "animal-filers.svg"), "w").write(doc(W, H, b))
print("  animal-filers.svg")
for b0, lab in BLOCKS:
    g = [r for r in rows if yr(r) and b0 <= yr(r) < b0 + 4]
    f = Counter(norm(r["notifier"]) for r in g)
    print(f"    {lab}  {len(g):2d} notices, {len(f):2d} firms, "
          f"top3 {sum(n for _,n in f.most_common(3))/len(g):.0%}")
