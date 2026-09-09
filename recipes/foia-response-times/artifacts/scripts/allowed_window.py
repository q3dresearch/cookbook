#!/usr/bin/env python3
"""The fifth trap: an agency can raise its on-time rate by moving its own deadline.

    python allowed_window.py <requests.csv>

Every compliance measure in this recipe, including the corrected one, is a
comparison against a due date. That date is not fixed by nature. New York City's
median allowed window went from 53 days in 2018 to 136 in 2025 while its median
days-to-close barely moved, so the on-time rate rose without a single request
being answered faster.

Two panels rather than two y-axes. Days and percentages do not share a scale, and
putting them on one chart with two axes would let the scale choice manufacture
whatever relationship suited the argument. Stacking them on a shared x-axis shows
the same thing and cannot be tuned.

Years under MIN_N are dropped: New York's pre-2016 rows are a few hundred a year
from a system that predates OpenRecords, and their medians swing by decades.
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
MIN_N = 1000
D = lambda s: dt.date.fromisoformat(s) if s else None          # noqa: E731

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getcwd(), "foia", "requests.csv")
rows = [r for r in csv.DictReader(open(SRC, encoding="utf-8"))
        if r["jurisdiction"] == "new-york-city" and r["received"] and r["due"]]

by = collections.defaultdict(lambda: ([], [], [0, 0]))
for r in rows:
    y = D(r["received"]).year
    allowed = (D(r["due"]) - D(r["received"])).days
    if not 0 <= allowed <= 400:
        continue
    by[y][0].append(allowed)
    if r["closed"]:
        took = (D(r["closed"]) - D(r["received"])).days
        if -5 <= took <= 2000:
            by[y][1].append(took)
            by[y][2][1] += 1
            if D(r["closed"]) <= D(r["due"]):
                by[y][2][0] += 1

YEARS = [y for y in sorted(by) if len(by[y][0]) >= MIN_N]
# Every comparison is anchored to the last COMPLETE year. The current year holds
# only the requests closed so far, which are the quick ones, so its days-to-close
# is the least trustworthy number here and would flatter the story.
THIS_YEAR = dt.date.today().year
LAST = max(i for i, y in enumerate(YEARS) if y < THIS_YEAR)
# Baseline is the first year OpenRecords was fully adopted. 2016 and 2017 carry
# 1,783 and 9,067 requests against 2018's 40,190 — the system was still rolling
# out — and the direction of the on-time rate depends on which of them you start
# from. Every year is still drawn; only the comparison is anchored.
BASE = next(i for i, y in enumerate(YEARS) if len(by[y][0]) >= 30000)
allow = [statistics.median(by[y][0]) for y in YEARS]
took = [statistics.median(by[y][1]) for y in YEARS]
ont = [by[y][2][0] / by[y][2][1] for y in YEARS]

W, L, R = 1180, 74, 250
PW = W - L - R
T1, PH1 = 168, 236
T2, PH2 = T1 + PH1 + 92, 128
H = T2 + PH2 + 92
mx = max(max(allow), max(took)) * 1.15
X = lambda i: L + (i / max(len(YEARS) - 1, 1)) * PW                    # noqa: E731
Y1 = lambda v: T1 + PH1 - (v / mx) * PH1                               # noqa: E731
Y2 = lambda v: T2 + PH2 - v * PH2                                      # noqa: E731

ORANGE, GREY = "#c9541f", "#5b5f66"
b = []
b.append(txt(L, 46, "New York almost tripled its own deadline and did not get any faster",
             21, INK, weight="600"))
b.append(txt(L, 114, "This citywide median is mostly one agency: see agency-backlog.svg. "
                     "The police department went 55 days to 139; the fire department, "
                     "holding a third of the backlog, never moved.", 12, MUTE))
b.append(txt(L, 73, f"Median days a request was ALLOWED, against median days it actually TOOK. "
                    f"{len(rows):,} FOIL requests carrying both dates.", 13.5, MUTE))
b.append(txt(L, 95, "The deadline is set by the agency. Raising it raises the on-time rate "
                    "without answering anything faster.", 13.5, MUTE))
b.append(circ(L + 5, 126, 5, ORANGE))
b.append(txt(L + 16, 130, "Days allowed — the agency's own deadline", 12.5, ORANGE, weight="600"))
b.append(circ(L + 330, 126, 5, GREY))
b.append(txt(L + 341, 130, "Days actually taken to close", 12.5, GREY, weight="600"))

for g in range(0, int(mx), 40):
    if g == 0:
        continue
    b.append(line(L, Y1(g), L + PW, Y1(g), GRID))
    b.append(txt(L - 10, Y1(g) + 4, str(g), 11.5, MUTE, anchor="end"))
b.append(txt(L - 10, T1 - 14, "days", 11.5, MUTE, anchor="end"))

for vals, colour in ((allow, ORANGE), (took, GREY)):
    for i in range(len(YEARS) - 1):
        b.append(line(X(i), Y1(vals[i]), X(i + 1), Y1(vals[i + 1]), colour, 2.6))
    for i, v in enumerate(vals):
        b.append(circ(X(i), Y1(v), 4.6, colour))
for i, v in enumerate(allow):
    if i in (BASE, LAST):
        b.append(txt(X(i), Y1(v) - 13, f"{v:.0f}", 12.5, ORANGE, anchor="middle", weight="600"))
for i, v in enumerate(took):
    if i in (BASE, LAST):
        b.append(txt(X(i), Y1(v) + 20, f"{v:.0f}", 12.5, GREY, anchor="middle", weight="600"))

b.append(txt(L, T2 - 26, "On-time rate against that moving deadline", 13, INK, weight="600"))
for g in (0.5, 0.75, 1.0):
    b.append(line(L, Y2(g), L + PW, Y2(g), GRID))
    b.append(txt(L - 10, Y2(g) + 4, f"{g:.0%}", 11.5, MUTE, anchor="end"))
for i in range(len(YEARS) - 1):
    b.append(line(X(i), Y2(ont[i]), X(i + 1), Y2(ont[i + 1]), INK, 2.2))
for i, v in enumerate(ont):
    b.append(circ(X(i), Y2(v), 4.2, INK))
    if i in (BASE, LAST):
        b.append(txt(X(i), Y2(v) - 12, f"{v:.0%}", 12, INK, anchor="middle", weight="600"))
for i, y in enumerate(YEARS):
    lbl = f"{y} (partial)" if y >= THIS_YEAR else str(y)
    b.append(txt(X(i), T2 + PH2 + 22, lbl, 11.5, MUTE, anchor="middle"))
    b.append(txt(X(i), T2 + PH2 + 37, f"n={len(by[y][0]):,}", 9.5, MUTE, anchor="middle"))

RX = L + PW + 26
b.append(txt(RX, T1 + 6, f"{YEARS[BASE]} to {YEARS[LAST]}, once", 12.5, INK, weight="600"))
b.append(txt(RX, T1 + 24, "OpenRecords was adopted:", 12.5, INK, weight="600"))
# wrap() takes a string and a PIXEL width, and str()s whatever it is given
# rather than complaining — passing a list of words renders the list repr.
COLW = W - RX - 20
for j, ln in enumerate(wrap(f"The window grew from {allow[BASE]:.0f} days to "
                            f"{allow[LAST]:.0f}. Days actually taken did not move: "
                            f"{took[BASE]:.0f} to {took[LAST]:.0f}. The on-time rate "
                            f"went {ont[BASE]:.0%} to {ont[LAST]:.0%} on the back of "
                            f"the deadline alone.", COLW)):
    b.append(txt(RX, T1 + 52 + j * 17, ln, 12, MUTE))
for j, ln in enumerate(wrap("So track the allowed window beside any compliance rate. An "
                            "agency that extends its own deadline buys the number without "
                            "changing the service.", COLW)):
    b.append(txt(RX, T1 + 146 + j * 17, ln, 12, ORANGE,
                 weight="600" if j == 0 else "normal"))

b.append(txt(L, H - 30, f"Source: data.cityofnewyork.us/kegn-anvq (OpenRecords FOIL). "
                        f"Years with fewer than {MIN_N:,} requests are omitted; the "
                        f"pre-2016 system predates OpenRecords.", 11.5, MUTE))
b.append(txt(L, H - 13, f"Comparisons run {YEARS[BASE]}-{YEARS[LAST]}: earlier years "
                        f"predate full adoption and the last is partial, holding only "
                        f"the requests closed so far, which are the quick ones.",
             11.5, MUTE))

open(os.path.join(OUT, "allowed-window.svg"), "w").write(doc(W, H, b))
print("  wrote allowed-window.svg")
for y, a, t, o in zip(YEARS, allow, took, ont):
    print(f"    {y}  allowed {a:>5.0f}d   took {t:>5.0f}d   on-time {o:>5.0%}")
