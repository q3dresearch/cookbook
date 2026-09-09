"""Two charts for the FOIA recipe.

1. coverage-trap  — the city-wide compliance rate next to the number of
   departments it is computed over. The denominator is the whole point: the
   rate falls because the dataset shrinks, not because the city slows down.
2. reversal       — the same years read per department. The largest department
   moves opposite to the aggregate.
"""
import csv, os, sys, collections, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
RECIPE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)                       # svgkit is vendored beside this file
from svgkit import *                                          # noqa: E402

OUT = os.path.join(RECIPE, "artifacts", "charts")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.getcwd(), "foia", "requests.csv")
D = lambda s: dt.date.fromisoformat(s)

rows = [r for r in csv.DictReader(open(SRC, encoding="utf-8"))
        if r["jurisdiction"] == "new-orleans" and r["received"] and r["due"] and r["closed"]]
YEARS = [str(y) for y in range(2016, 2027)]
allrows = [r for r in csv.DictReader(open(SRC, encoding="utf-8"))
           if r["jurisdiction"] == "new-orleans" and r["received"]]

ontime = lambda rs: sum(1 for r in rs if D(r["closed"]) <= D(r["due"])) / len(rs)
byyear = {y: [r for r in rows if r["received"][:4] == y] for y in YEARS}
def _deps(r):
    """A request can name several departments in one field, separated by ';'.
    Counting the raw strings inflated the total to 705; splitting gives 81."""
    return [p.strip() for p in (r["agency"] or "?").split(";") if p.strip()]
depts  = {y: len({d for r in allrows if r["received"][:4] == y for d in _deps(r)}) for y in YEARS}

def top_share(y):
    """Share of the year's requests sitting in its single largest department.
    Department *count* misses the real problem: 2020 has 86 departments but 63%
    of requests in one of them, so the rate is that department's rate."""
    v = [d for r in allrows if r["received"][:4] == y for d in _deps(r)]
    if not v: return 0.0
    return collections.Counter(v).most_common(1)[0][1] / len(v)
conc = {y: top_share(y) for y in YEARS}
THIN = lambda y: conc[y] >= 0.30

# ---------------------------------------------------------------- chart 1
W, L, R = 1210, 74, 250
PW = W - L - R
T1, PH1 = 118, 200
T2, PH2 = T1 + PH1 + 96, 132
H = T2 + PH2 + 96
b = []
b.append(txt(L, 46, "The compliance rate falls as the dataset narrows", 21, INK, weight="600"))
b.append(txt(L, 73, "Each year's rate is computed over a different New Orleans. "
                    "The denominator is the finding.", 13.5, MUTE))

xw = PW / len(YEARS)
xc = lambda i: L + xw * (i + 0.5)

# panel 1 — compliance
b.append(txt(L, T1 - 16, "Share of requests answered by the city's own legal deadline",
             12.5, INK, weight="600"))
for g in range(0, 101, 25):
    y = T1 + PH1 - PH1 * g / 100
    b.append(line(L, y, L + PW, y, GRID))
    b.append(txt(L - 8, y + 4, f"{g}%", 11, MUTE, anchor="end"))
pts = []
for i, y in enumerate(YEARS):
    v = byyear[y]
    if not v:
        continue
    rate = ontime(v)
    px, py = xc(i), T1 + PH1 - PH1 * rate
    pts.append((px, py, y, rate, len(v)))
for (x1, y1, *_), (x2, y2, *_) in zip(pts, pts[1:]):
    b.append(line(x1, y1, x2, y2, BLUE, 2.5))
for x, y, yr, rate, n in pts:
    thin = THIN(yr)
    b.append(circ(x, y, 5, ORANGE if thin else BLUE))
    b.append(txt(x, y - 13, f"{rate*100:.0f}%", 11.5, ORANGE if thin else BLUE,
                 anchor="middle", weight="600"))
    b.append(txt(x, T1 + PH1 + 17, yr[2:], 11, MUTE, anchor="middle"))
    b.append(txt(x, T1 + PH1 + 31, f"n={n:,}", 9.5, MUTE, anchor="middle"))

# panel 2 — the denominator
b.append(txt(L, T2 - 16, "Distinct city departments in that year's data — and the share held "
                         "by the single largest", 12.5, INK, weight="600"))
mx = max(depts.values())
for i, y in enumerate(YEARS):
    n = depts[y]
    hgt = PH2 * n / mx
    thin = THIN(y)
    b.append(rect(xc(i) - xw * 0.3, T2 + PH2 - hgt, xw * 0.6, hgt,
                  ORANGE if thin else BLUE, op=0.9 if thin else 0.55))
    b.append(txt(xc(i), T2 + PH2 - hgt - 7, str(n), 11, INK, anchor="middle", weight="600"))
    b.append(txt(xc(i), T2 + PH2 + 17, y[2:], 11, MUTE, anchor="middle"))
    b.append(txt(xc(i), T2 + PH2 + 32, f"{int(conc[y]*100)}%", 9.5,
                 ORANGE if thin else MUTE, anchor="middle",
                 weight="600" if thin else "normal"))
b.append(line(L, T2 + PH2, L + PW, T2 + PH2, MUTE))

# right-hand note
nx = L + PW + 22
y0 = T1 + 4
for j, ln in enumerate(wrap("Orange marks a year where one department holds 30% or more of "
                           "all requests — the rate is then that department's rate, not "
                           "the city's.", 200)):
    b.append(txt(nx, y0 + j * 16, ln, 11.5, INK)); y0 += 0
y0 += 16 * 5 + 14
for j, ln in enumerate(wrap("From August 2024 the log drops from 81 departments to 21. "
                           "Finance-Treasury, which answered 291 of 295 requests on time in "
                           "2018, publishes nothing after 2023.", 200)):
    b.append(txt(nx, y0 + j * 16, ln, 11.5, MUTE))
b.append(txt(L, H - 30, "Source: data.nola.gov/jsrk-e98x, 10,290 requests carrying both a due date "
                        "and a closed date, 2016-06 to 2026-09.", 10.5, MUTE))
open(os.path.join(OUT, "coverage-trap.svg"), "w").write(doc(W, H, b))

# ---------------------------------------------------------------- chart 2
SHOW = [("Fire Department (NOFD)", "Fire Department", ORANGE),
        ("Finance - Treasury", "Finance – Treasury", BLUE),
        ("Media Request - NOPD", "Police media requests", VIOLET)]
by = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    by[r["agency"]][r["received"][:4]].append(r)

W2, L2, R2 = 1210, 74, 250
PW2 = W2 - L2 - R2
T, PH = 152, 300
H2 = T + PH + 104
b = []
b.append(txt(L2, 46, "Read by department, the biggest records desk moved the opposite way",
             21, INK, weight="600"))
b.append(txt(L2, 73, "Same data, same years. The aggregate fell because the mix changed, "
                     "not because departments got slower.", 13.5, MUTE))
lx = L2
for _k, _lab, _c in SHOW:
    b.append(circ(lx + 5, 102, 5, _c))
    b.append(txt(lx + 16, 106, _lab, 12.5, _c, weight="600"))
    lx += 26 + len(_lab) * 7.4
xw2 = PW2 / len(YEARS)
xc2 = lambda i: L2 + xw2 * (i + 0.5)
for g in range(0, 101, 25):
    y = T + PH - PH * g / 100
    b.append(line(L2, y, L2 + PW2, y, GRID))
    b.append(txt(L2 - 8, y + 4, f"{g}%", 11, MUTE, anchor="end"))
for i, yv in enumerate(YEARS):
    b.append(txt(xc2(i), T + PH + 18, yv[2:], 11, MUTE, anchor="middle"))
placed = {}
for key, label, col in SHOW:
    seq = []
    for i, yv in enumerate(YEARS):
        v = by[key].get(yv, [])
        if len(v) < 25:
            continue
        seq.append((xc2(i), T + PH - PH * ontime(v), ontime(v), len(v)))
    for (x1, y1, *_), (x2, y2, *_) in zip(seq, seq[1:]):
        b.append(line(x1, y1, x2, y2, col, 2.5))
    for j, (x, y, rate, n) in enumerate(seq):
        b.append(circ(x, y, 4.5, col))
        # Side-step only against another series at the same x. Counts appear at
        # the ends of each line rather than on every point: thirty n-labels on a
        # three-series chart is noise, and the endpoints carry the scale.
        near = [oy for ok, _l, _c in SHOW if ok != key
                for ox, oy, *_ in placed.get(ok, []) if abs(ox - x) < 1 and abs(oy - y) < 34]
        below = bool(near) and min(near) < y
        b.append(txt(x, y + (19 if below else -13), f"{rate*100:.0f}%", 10.5, col,
                     anchor="middle", weight="600"))
        if j in (0, len(seq) - 1):
            b.append(txt(x, y + (31 if below else -25), f"n={n:,}", 9, MUTE, anchor="middle"))
    placed[key] = seq
b.append(line(L2, T + PH, L2 + PW2, T + PH, MUTE))
nx = L2 + PW2 + 26
for j, ln in enumerate(wrap("Fire Department, like for like: 18.9% on time across 2017–19 "
                           "(n=222), 51.9% across 2022–26 (n=1,702). It nearly tripled while "
                           "the city-wide rate fell.", 210)):
    b.append(txt(nx, T + 14 + j * 16, ln, 11.5, INK))
for j, ln in enumerate(wrap("Counts are shown at each line's first and last year. A year is "
                           "plotted only where that department had at least 25 requests.", 210)):
    b.append(txt(nx, T + 150 + j * 16, ln, 11, MUTE))
b.append(txt(L2, H2 - 30, "Source: data.nola.gov/jsrk-e98x. On time = closed on or before the "
                          "due date the city itself records.", 10.5, MUTE))
open(os.path.join(OUT, "reversal.svg"), "w").write(doc(W2, H2, b))
print("  wrote coverage-trap.svg and reversal.svg")
