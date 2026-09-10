"""Creation vs removal on one calendar axis and ONE linear scale.

Up and down share a baseline, so they must share pixels-per-section: the whole
claim of a diverging bar chart is that the two directions are comparable.
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
import csv, sys
from collections import Counter
sys.path.insert(0, HERE)
from svgkit import *
VIOLET2 = "#8c3b17"   # a darker orange: same family, so the split reads as one series
import cfrlib

rows, live = cfrlib.load()
DECS = list(range(1940, 2030, 10))
born = Counter(r["born"] // 10 * 10 for r in live)
frozen = Counter(r["born"] // 10 * 10 for r in live if r["n_amend"] == 0)
vr = list(csv.DictReader(open(os.path.join(DERIVED, "cfr-title12-version-events.csv"))))
OTS_DAY = "2018-10-11"          # Office of Thrift Supervision's entire rulebook
_r = [r for r in vr if r["removed"] == "True" and r["amendment_date"]]
rem = Counter(int(r["amendment_date"][:4]) // 10 * 10
              for r in _r if not r["amendment_date"].startswith(OTS_DAY))
ots = Counter(int(r["amendment_date"][:4]) // 10 * 10
              for r in _r if r["amendment_date"].startswith(OTS_DAY))
ROUTINE = sum(rem.values())
ONEDAY = sum(ots.values())

W, L, R, TOPP = 1180, 96, 40, 176
SPAN = 560                      # total pixels shared by both directions
PW = W - L - R
BW = PW / len(DECS)
# The down-scale must span the FULL bar, clean-up included, or the
# 2010s column runs off the plot.
_tot = {d: rem.get(d, 0) + ots.get(d, 0) for d in set(rem) | set(ots)}
umax, dmax = max(born.values()), max(_tot.values())


def nice(v):
    import math
    e = 10 ** int(math.log10(v))
    for m in (1, 2, 2.5, 5, 10):
        if m * e >= v:
            return m * e
    return 10 * e


STEP = nice(max(umax, dmax) / 4.0)
UTOP = -(-umax // STEP) * STEP          # round each side up to a whole tick
DBOT = -(-dmax // STEP) * STEP
UNIT = SPAN / (UTOP + DBOT)             # one pixels-per-section for both halves
UPH, DNH = UTOP * UNIT, DBOT * UNIT
BASE = TOPP + UPH
H = BASE + DNH + 176
Y = lambda v: BASE - v * UNIT           # v>0 up, v<0 down

b = []
b.append(txt(40, 44, "Pruning is one event, not a habit", 21, INK, weight="600"))
b.append(txt(40, 68, "Sections of CFR Title 12 first published in each decade and still "
                     "in force today (up), against sections removed (down). One linear "
                     "scale both ways.", 12.5, MUTE))
b.append(txt(40, 86, f"{ONEDAY:,} of the {ONEDAY+ROUTINE:,} removals ever recorded went "
                     f"on a single day. Strip that and removal runs at about "
                     f"{ROUTINE/9.7:.0f} sections a year.", 12.5, MUTE))
b.append(txt(40, 104, "These are NOT two halves of a balance. Up counts survivors by "
                      "birth decade; down counts deaths by death decade, and only from "
                      "2017. A section born in 1995 and removed in 2018", 11.5, MUTE))
b.append(txt(40, 120, "appears below and not above. The eCFR version record begins with "
                      "a 2016–17 baseline load, so a true additions series is not "
                      "recoverable and no net figure is drawn here.", 11.5, MUTE))

lx = 40
for c, lab in [(BLUE, "amended at least once since"),
               (VIOLET, "never amended since first published"),
               (ORANGE, "removed, routine"), (VIOLET2, "removed, the 2018 clean-up")]:
    b.append(rect(lx, 137, 11, 11, c, op=0.9))
    b.append(txt(lx + 17, 146.5, lab, 11.5, MUTE))
    lx += 17 + len(lab) * 6.15 + 30

t = STEP
while t <= UTOP + 1:
    b.append(line(L, Y(t), W - R, Y(t), GRID))
    b.append(txt(L - 10, Y(t) + 4, f"{int(t):,}", 10.5, MUTE, "end"))
    t += STEP
t = STEP
while t <= DBOT + 1:
    b.append(line(L, Y(-t), W - R, Y(-t), GRID))
    b.append(txt(L - 10, Y(-t) + 4, f"{int(t):,}", 10.5, MUTE, "end"))
    t += STEP
b.append(txt(L - 10, TOPP - 14, "sections", 10.5, MUTE, "end"))

xcut = L + BW * DECS.index(2010)
b.append(rect(L, BASE + 2, xcut - L, DNH - 2, MUTE, op=0.055))
b.append(txt((L + xcut) / 2, BASE + DNH / 2 - 4, "no removal record before 2017",
             11.5, MUTE, "middle"))
b.append(txt((L + xcut) / 2, BASE + DNH / 2 + 13, "(eCFR version history starts here)",
             10.5, MUTE, "middle"))

for i, d in enumerate(DECS):
    x = L + i * BW + BW * 0.16
    w = BW * 0.68
    tot, fz = born.get(d, 0), frozen.get(d, 0)
    if tot:
        b.append(rect(x, Y(tot), w, BASE - Y(tot), BLUE, op=0.90))
        if fz:
            b.append(rect(x, Y(fz), w, BASE - Y(fz), VIOLET, op=0.95))
        b.append(txt(x + w / 2, Y(tot) - 8, f"{tot:,}", 10.5, INK, "middle", "600"))
        if fz and (BASE - Y(fz)) > 17:
            b.append(txt(x + w / 2, Y(fz) + 14, f"{100*fz/tot:.0f}%", 9.5,
                         "#ffffff", "middle", "700"))
    rm, ot = rem.get(d, 0), ots.get(d, 0)
    if rm:
        b.append(rect(x, BASE + 2, w, Y(-rm) - BASE, ORANGE, op=0.90))
    if ot:
        b.append(rect(x, Y(-rm), w, Y(-rm - ot) - Y(-rm), VIOLET2, op=0.90))
        b.append(txt(x + w / 2, (Y(-rm) + Y(-rm - ot)) / 2 + 4,
                     f"{ot:,} in one day", 10.5, "#ffffff", "middle", "600"))
    if rm + ot:
        b.append(txt(x + w / 2, Y(-rm - ot) + 15, f"{rm + ot:,}", 10.5, ORANGE,
                     "middle", "600"))
    b.append(txt(x + w / 2, BASE + DNH + 30, f"{d}s", 12, INK, "middle"))

b.append(line(L, BASE, W - R, BASE, INK, 1.6))

i10 = DECS.index(2010)
ax = L + i10 * BW + BW * 0.5
b.append(circ(ax, (BASE + Y(-rem.get(2010, 0))) / 2, 9.5, "#ffffff", ORANGE, 1.8))
b.append(txt(ax, (BASE + Y(-rem.get(2010, 0))) / 2 + 3.8, "1", 11, ORANGE, "middle", "700"))
ny = BASE + DNH + 66
b.append(circ(48, ny - 4, 9.5, ORANGE))
b.append(txt(48, ny - 0.2, "1", 11, "#ffffff", "middle", "700"))
b.append(txt(65, ny, "836 of the 2010s removals went on a single day, 11 October 2018:",
             12, INK, weight="600"))
b.append(txt(65, ny + 18, "the Office of Thrift Supervision's entire rulebook, deleted "
             "seven years after Dodd-Frank abolished the agency in 2011. Pruning here is "
             "not maintenance — it is one clean-up.", 12, MUTE))

b.append(txt(40, H - 34, "Source: eCFR full-text API (source notes) and versions API, "
             "snapshot 2026-09-01. Creation dates are the earliest surviving Federal "
             "Register citation.", 10.5, MUTE))
b.append(txt(40, H - 18, "A wholly rewritten section reads as new and loses its "
             "amendment history, so “never amended” means never amended since "
             "last republished.", 10.5, MUTE))
open(os.path.join(CHARTS, "cfr-growth-vs-removal.svg"), "w").write(doc(W, H, b))
print(f"scale: {UNIT:.4f} px/section both ways; step {STEP}; up->{UTOP} down->{DBOT}")
print("born:", sorted(born.items()))
print("never amended:", sorted(frozen.items()))
print("removed:", sorted(rem.items()))
