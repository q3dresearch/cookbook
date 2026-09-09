#!/usr/bin/env python3
"""Two ways an agency misses its deadline, and they need different remedies.

    python agency_backlog.py <requests.csv>

New York City's compliance figures are not New York City's. 61% of every request
sitting open past its deadline belongs to the police department and another 31%
to the fire department; 28 of 60 agencies have any at all. So does the deadline
extension behind the fifth trap — the median allowed window went from 53 days to
136 citywide, and that is almost entirely NYPD moving from 55 to 139 while the
fire department stayed at 38.

Which makes the citywide numbers an instance of this recipe's own third trap: an
aggregate moving because its composition moved. Both of the headline findings
here needed splitting by agency before they meant anything, and neither was.

Two panels, because the two failure modes need different responses. An agency
that extends its own deadline is buying the number and the fix is to cap the
window. An agency that leaves 87% of its requests open past a seven-day deadline
is not gaming anything; it has stopped answering.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RECIPE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from svgkit import *                                          # noqa: E402

OUT = os.path.join(RECIPE, "artifacts", "charts")
D = lambda s: dt.date.fromisoformat(s) if s else None          # noqa: E731
MIN_N = 200

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getcwd(), "foia", "requests.csv")
rows = [r for r in csv.DictReader(open(SRC, encoding="utf-8"))
        if r["jurisdiction"] == "new-york-city" and r["received"] and r["due"]]
TODAY = max(D(r["received"]) for r in rows)

win = collections.defaultdict(lambda: collections.defaultdict(list))
stat = collections.defaultdict(lambda: [0, 0])                 # open past due, total
for r in rows:
    a = r["agency"] or "?"
    w = (D(r["due"]) - D(r["received"])).days
    if 0 <= w <= 400:
        win[a][D(r["received"]).year].append(w)
    if D(r["received"]).year >= 2021:
        stat[a][1] += 1
        if not r["closed"] and D(r["due"]) < TODAY:
            stat[a][0] += 1

BACKLOG = sum(v[0] for v in stat.values())
agencies = []
for a, ys in win.items():
    if all(len(ys.get(y, [])) >= MIN_N for y in (2018, 2025)) and stat[a][1] >= 500:
        agencies.append((stat[a][0] / BACKLOG, a,
                         statistics.median(ys[2018]), statistics.median(ys[2025]),
                         stat[a][0], stat[a][0] / stat[a][1]))
agencies.sort(reverse=True)
agencies = agencies[:8]

W, L, R = 1200, 330, 60
P1 = 300                      # window panel
GAP = 76
P2 = 300                      # own-share panel
T, RH = 214, 46
H = T + len(agencies) * RH + 150
mxw = max(max(a[2], a[3]) for a in agencies) * 1.1
X1 = lambda v: L + v / mxw * P1                                # noqa: E731
X2 = lambda v: L + P1 + GAP + v * P2                           # noqa: E731

ORANGE, GREY, RED = "#c9541f", "#8a8880", "#b3261e"
b = []
b.append(txt(L - 256, 46, "Two agencies are the whole backlog, and only one of them "
                          "moved its deadline", 21, INK, weight="600"))
b.append(txt(L - 256, 74, f"Every New York City agency with at least {MIN_N} dated requests "
                          f"in both 2018 and 2025, ranked by its share of the "
                          f"{BACKLOG:,} requests", 13.5, MUTE))
b.append(txt(L - 256, 94, "sitting open past their deadline. The citywide figures in this "
                          "recipe are these agencies wearing a city's name.", 13.5, MUTE))
b.append(txt(L, T - 42, "Median days the agency allowed itself", 12.5, INK, weight="600"))
b.append(circ(L + 6, T - 22, 4.6, GREY))
b.append(txt(L + 16, T - 18, "2018", 11.5, MUTE))
b.append(circ(L + 66, T - 22, 5.4, ORANGE))
b.append(txt(L + 78, T - 18, "2025", 11.5, ORANGE, weight="600"))
b.append(txt(L + P1 + GAP, T - 42, "Share of its own requests open past due",
             12.5, INK, weight="600"))

for g in (0, 50, 100, 150):
    if g > mxw:
        continue
    b.append(line(X1(g), T - 8, X1(g), T + len(agencies) * RH - 24, GRID))
    b.append(txt(X1(g), T + len(agencies) * RH - 6, str(g), 11, MUTE, anchor="middle"))
for g in (0, 0.25, 0.5, 0.75, 1.0):
    b.append(line(X2(g), T - 8, X2(g), T + len(agencies) * RH - 24, GRID))
    b.append(txt(X2(g), T + len(agencies) * RH - 6, f"{g:.0%}", 11, MUTE, anchor="middle"))

for i, (share, a, w18, w25, nopen, ownshare) in enumerate(agencies):
    y = T + i * RH
    b.append(txt(L - 14, y + 4, a.replace("New York City ", "")[:34], 12.5, INK,
                 anchor="end", weight="600" if share > 0.1 else "normal"))
    b.append(txt(L - 14, y + 19, f"{nopen:,} open · {share:.0%} of the backlog", 10.5,
                 MUTE, anchor="end"))
    moved = w25 - w18
    b.append(line(X1(w18), y, X1(w25), y, ORANGE if moved > 20 else GREY, 2.4))
    b.append(circ(X1(w18), y, 4.6, GREY))
    b.append(circ(X1(w25), y, 5.4, ORANGE if moved > 20 else GREY))
    # Plain ASCII: the renderer has no glyph for an arrow and silently draws a box.
    lab = f"{w18:.0f} to {w25:.0f}" + (f"   +{moved:.0f}d" if moved > 20 else "")
    b.append(txt(X1(max(w18, w25)) + 11, y + 4, lab, 11.5,
                 ORANGE if moved > 20 else MUTE, weight="600" if moved > 20 else "normal"))
    b.append(rect(X2(0), y - 8, max(X2(ownshare) - X2(0), 2), 16,
                  RED if ownshare > 0.5 else GREY, rx=3))
    b.append(txt(X2(ownshare) + 9, y + 4, f"{ownshare:.0%}", 11.5,
                 RED if ownshare > 0.5 else MUTE, weight="600" if ownshare > 0.5 else "normal"))

yb = T + len(agencies) * RH + 34
b.append(line(L - 256, yb - 14, W - 40, yb - 14, GRID))
for j, ln in enumerate(wrap("Extending the window and abandoning the queue are different "
                            "failures. The police department did the first — 55 days to 139 "
                            "— and its on-time rate rose without answering anything faster. "
                            "The fire department did the second: it never moved its deadline "
                            "and simply stopped closing. Capping the allowed window would "
                            "reach one of them and not the other.", W - L - 20)):
    b.append(txt(L - 256, yb + 8 + j * 18, ln, 13, INK))
b.append(txt(L - 256, H - 30, f"Source: data.cityofnewyork.us/kegn-anvq. Backlog measured on "
                              f"requests received from 2021; window medians on requests "
                              f"received in 2018 and 2025.", 11.5, MUTE))
b.append(txt(L - 256, H - 13, f"Agencies with fewer than {MIN_N} dated requests in either "
                              f"year, or fewer than 500 since 2021, are omitted.", 11.5, MUTE))

open(os.path.join(OUT, "agency-backlog.svg"), "w").write(doc(W, H, b))
print("  wrote agency-backlog.svg")
for share, a, w18, w25, nopen, own in agencies:
    print(f"    {a[:40]:<42} window {w18:>4.0f}->{w25:>4.0f}   "
          f"{nopen:>7,} open ({share:>4.0%} of backlog, {own:>4.0%} of own)")
