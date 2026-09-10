"""Withdrawal rate over time, on two stacked panels rather than two y-axes."""
import os, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import graslib

HERE = os.path.dirname(os.path.abspath(__file__))
# HERE is artifacts/scripts, so the charts live one level up, beside it.
CHARTS = os.path.join(os.path.dirname(HERE), "charts")
by, src = graslib.load()
per = defaultdict(Counter)
for v in by.values():
    if v["closed_year"]:
        per[v["closed_year"]][v["outcome"]] += 1
YEARS = [y for y in sorted(per) if sum(per[y].values()) >= 8]
LAST = YEARS[-1]

W, L, R = 1180, 88, 46
PW = W - L - R
BW = PW / len(YEARS)
T1, PH1 = 176, 132          # rate panel
T2, PH2 = 380, 250          # count panel
H = T2 + PH2 + 148
CMAX, RMAX = 100, 40

b = []
b.append(txt(40, 44, "Withdrawal is normal, and it is not increasing", 21, INK, weight="600"))
b.append(txt(40, 70, "Every GRAS notice FDA closed in each year, by outcome. A notice is "
                     "“withdrawn” when FDA records that, at the notifier’s "
                     "request, it ceased to evaluate.", 12.5, MUTE))
b.append(txt(40, 88, f"Source: FDA GRAS Notice Inventory, {src}. {len(by):,} notices, "
                     f"GRN 1–1336. {LAST} is a partial year.", 12.5, MUTE))

lx = 40
for c, lab in [(BLUE, "FDA has no questions"), (ORANGE, "withdrawn at notifier's request"),
               (VIOLET, "no basis for a GRAS determination"), (MUTE, "pending")]:
    b.append(rect(lx, 111, 11, 11, c, op=0.9))
    b.append(txt(lx + 17, 120.5, lab, 11.5, MUTE))
    lx += 17 + len(lab) * 6.15 + 26

# --- panel 1: withdrawal rate
RY = lambda p: T1 + PH1 - PH1 * p / RMAX
b.append(txt(L, T1 - 16, "withdrawn, % of that year's closures", 12, INK, weight="600"))
for g in (0, 10, 20, 30, 40):
    b.append(line(L, RY(g), W - R, RY(g), GRID))
    b.append(txt(L - 10, RY(g) + 4, f"{g}%", 10.5, MUTE, "end"))
rates = []
for i, y in enumerate(YEARS):
    t = sum(per[y].values())
    rates.append((L + i * BW + BW / 2, 100 * per[y]["withdrawn"] / t))
allw = sum(per[y]["withdrawn"] for y in YEARS)
allt = sum(sum(per[y].values()) for y in YEARS)
mean = 100 * allw / allt
b.append(line(L, RY(mean), W - R, RY(mean), VIOLET, 1.3, "5 4"))
b.append(txt(W - R - 4, RY(mean) - 7, f"mean {mean:.1f}%", 10.5, VIOLET, "end"))
b.append('<polyline fill="none" stroke="%s" stroke-width="2" points="%s"/>' %
         (ORANGE, " ".join(f"{x:.1f},{RY(p):.1f}" for x, p in rates)))
for x, p in rates:
    b.append(circ(x, RY(p), 3, ORANGE))

# --- panel 2: counts
CY = lambda v: T2 + PH2 - PH2 * v / CMAX
b.append(txt(L, T2 - 16, "notices closed", 12, INK, weight="600"))
for g in (0, 25, 50, 75, 100):
    b.append(line(L, CY(g), W - R, CY(g), GRID))
    b.append(txt(L - 10, CY(g) + 4, str(g), 10.5, MUTE, "end"))
for i, y in enumerate(YEARS):
    x = L + i * BW + BW * 0.16
    w = BW * 0.68
    base = T2 + PH2
    for key, col in (("no questions", BLUE), ("withdrawn", ORANGE),
                     ("rejected", VIOLET), ("pending", MUTE)):
        v = per[y][key]
        if not v:
            continue
        h = PH2 * v / CMAX
        b.append(rect(x, base - h, w, h, col, op=0.9))
        base -= h
    if y % 2 == 1 or y == LAST:
        b.append(f'<text x="{x + w/2:.1f}" y="{T2 + PH2 + 16:.1f}" font-family="{FONT}" '
                 f'font-size="10.5" fill="{MUTE}" text-anchor="end" '
                 f'transform="rotate(-45 {x + w/2:.1f} {T2 + PH2 + 16:.1f})">{y}</text>')

b.append(line(L, T2 + PH2, W - R, T2 + PH2, INK, 1.4))
ny = T2 + PH2 + 76
lo = min(p for _, p in rates); hi = max(p for _, p in rates)
b.append(txt(40, ny, f"The rate ranges from {lo:.0f}% to {hi:.0f}% with no trend across "
                     f"{len(YEARS)} years, on a mean of {mean:.1f}%. Reading any single "
                     f"year as a signal is reading noise.", 12, MUTE))
b.append(txt(40, H - 18, "Years with fewer than 8 closures "
             "omitted. Outcome is FDA's own letter text, classified verbatim.",
             10.5, MUTE))
open(os.path.join(CHARTS, "gras-withdrawal-rate.svg"), "w").write(doc(W, H, b))
print(f"years {YEARS[0]}-{YEARS[-1]}  mean withdrawal {mean:.1f}%  "
      f"min {min(p for _,p in rates):.1f}%  max {max(p for _,p in rates):.1f}%")
