"""NYC FOIL: the compliance measure that hides its own decline.

The usual statistic divides on-time closures by *closed* requests. That drops
every request still sitting open — and the ones still open are the late ones.
As a backlog grows the measure improves while service worsens.

Counting a request that is open past its due date as missed (and excluding only
those not yet due) removes the bias. On ~640k NYC requests the two measures
diverge by 23 points in 2025.
"""
import csv, os, sys, collections, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
RECIPE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)                       # svgkit is vendored beside this file
from svgkit import *                                          # noqa: E402
OUT = os.path.join(RECIPE, "artifacts", "charts")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.getcwd(), "foia", "requests.csv")
D = lambda s: dt.date.fromisoformat(s) if s else None

rows = [r for r in csv.DictReader(open(SRC, encoding="utf-8"))
        if r["jurisdiction"] == "new-york-city" and r["received"] and r["due"]]

# "Open past due" is measured against a reference date, and that date was once
# written into this file as a literal. A frozen reference silently drifts: rerun
# a year later and requests that came due in the meantime are still counted as
# not-yet-due. Taking it from the corpus makes the chart both deterministic and
# correct — it is as of the data, which is what the caption claims.
TODAY = max(d for d in (D(r["received"]) for r in rows) if d)
by = collections.defaultdict(list)
for r in rows:
    by[r["received"][:4]].append(r)
YEARS = [y for y in sorted(by) if len(by[y]) >= 2000]          # skip the one-agency era

def naive(v):
    cl = [r for r in v if r["closed"]]
    return sum(1 for r in cl if D(r["closed"]) <= D(r["due"])) / len(cl)
def honest(v):
    hits = sum(1 for r in v if r["closed"] and D(r["closed"]) <= D(r["due"]))
    undecided = sum(1 for r in v if not r["closed"] and D(r["due"]) >= TODAY)
    return hits / (len(v) - undecided)
def openshare(v):
    return sum(1 for r in v if not r["closed"]) / len(v)

W, L, R = 1210, 74, 258
PW = W - L - R
T, PH = 158, 292
H = T + PH + 108
b = []
b.append(txt(L, 46, "New York's records compliance improved on paper while it fell in fact",
             21, INK, weight="600"))
AGENCIES = len({r["agency"] for r in rows if r.get("agency")})
b.append(txt(L, 73, f"{len(rows):,} FOIL requests, {AGENCIES} agencies, as of "
                    f"{TODAY:%B %Y}. The difference is whether requests "
                    "still sitting unanswered are counted at all.", 13.5, MUTE))
b.append(circ(L + 5, 104, 5, MUTE))
b.append(txt(L + 16, 108, "The usual measure — on-time share of CLOSED requests", 12.5, MUTE, weight="600"))
b.append(circ(L + 396, 104, 5, ORANGE))
b.append(txt(L + 407, 108, "Counting requests open past their deadline as missed", 12.5, ORANGE, weight="600"))

xw = PW / len(YEARS); xc = lambda i: L + xw * (i + 0.5)
for g in range(0, 101, 25):
    y = T + PH - PH * g / 100
    b.append(line(L, y, L + PW, y, GRID))
    b.append(txt(L - 8, y + 4, f"{g}%", 11, MUTE, anchor="end"))
na = [(xc(i), T + PH - PH * naive(by[y]), naive(by[y])) for i, y in enumerate(YEARS)]
ho = [(xc(i), T + PH - PH * honest(by[y]), honest(by[y])) for i, y in enumerate(YEARS)]
for (x1, y1, _), (x2, y2, _) in zip(na, na[1:]):
    b.append(line(x1, y1, x2, y2, MUTE, 2, dash="5,4"))
for (x1, y1, _), (x2, y2, _) in zip(ho, ho[1:]):
    b.append(line(x1, y1, x2, y2, ORANGE, 2.6))
for i, y in enumerate(YEARS):
    b.append(line(xc(i), na[i][1], xc(i), ho[i][1], GRID, 1))
for x, y, v in na:
    b.append(circ(x, y, 4, MUTE)); b.append(txt(x, y - 11, f"{v*100:.0f}%", 10, MUTE, anchor="middle"))
for x, y, v in ho:
    b.append(circ(x, y, 5, ORANGE))
    b.append(txt(x, y + 19, f"{v*100:.0f}%", 11, ORANGE, anchor="middle", weight="600"))
for i, y in enumerate(YEARS):
    b.append(txt(xc(i), T + PH + 18, y, 11, MUTE, anchor="middle"))
    b.append(txt(xc(i), T + PH + 32, f"{openshare(by[y])*100:.0f}% open", 9,
                 ORANGE if openshare(by[y]) > 0.15 else MUTE, anchor="middle"))
b.append(line(L, T + PH, L + PW, T + PH, MUTE))
nx = L + PW + 26; y0 = T + 6
for ln in wrap("The usual statistic divides on-time closures by closed requests — so every "
               "request still waiting is dropped, and the ones still waiting are the late "
               "ones.", 218):
    b.append(txt(nx, y0, ln, 11.5, INK)); y0 += 16
y0 += 12
for ln in wrap("As a backlog builds, that measure rises while service falls. In 2025 it "
               "reports 79% against a true 56%.", 218):
    b.append(txt(nx, y0, ln, 11.5, ORANGE, weight="600")); y0 += 16
y0 += 12
for ln in wrap("Requests not yet past their due date are excluded from both measures rather "
               "than counted as failures. 2026 is a partial year.", 218):
    b.append(txt(nx, y0, ln, 11, MUTE)); y0 += 15
b.append(txt(L, H - 30, "Source: data.cityofnewyork.us/kegn-anvq (OpenRecords FOIL), requests "
                        "submitted 2016-2026 carrying a due date.", 10.5, MUTE))
open(os.path.join(OUT, "nyc-hidden-decline.svg"), "w").write(doc(W, H, b))
print("  wrote nyc-hidden-decline.svg")
