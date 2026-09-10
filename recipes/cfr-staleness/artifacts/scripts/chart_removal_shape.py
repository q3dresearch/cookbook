"""Is removal attrition, or an event? Sections lost per part against days taken.

    CFR_WORK=./work python chart_removal_shape.py

If parts shed sections gradually, a part that lost twenty sections should have
lost them across many separate days. It did not. Of the 55 parts that lost three
or more sections, 43 lost every one of them on a single day, and only 20% of
parts with any removal ever had another one later.

That is the mechanism behind "pruning is one event, not a habit", measured at the
level the event actually happens: a rulemaking opens a part, deletes what it came
for, and closes it. Nothing decays on its own.

It also explains the dead-letter list. Expired text does not survive because
nobody visits the part — 12 CFR 208.23 expired in 1999 and the Federal Reserve
deleted eight OTHER sections from part 208 in 2019. It survives because "does any
section here say it expired" is not on the checklist when the part is opened.

The 836 sections removed on 2018-10-11 (the Office of Thrift Supervision's
rulebook) are excluded: one abolished agency is not evidence about maintenance.
"""
import os, sys, csv, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import cfrlib

OUT = os.path.join(cfrlib.CHARTS, "cfr-removal-shape.svg")
OTS = "2018-10-11"

ev = list(csv.DictReader(open(os.path.join(cfrlib.DERIVED,
                                           "cfr-title12-version-events.csv"))))
rem = [e for e in ev if e["removed"] == "True" and e["amendment_date"]
       and not e["amendment_date"].startswith(OTS)]
lost = collections.Counter(e["part"] for e in rem)
days = collections.defaultdict(set)
for e in rem:
    days[e["part"]].add(e["amendment_date"][:10])
rows, live = cfrlib.load()
size = collections.Counter(r["part"] for r in rows if not r["reserved"])

pts = [{"part": p, "n": n, "d": len(days[p]), "size": size.get(p, 0)}
       for p, n in lost.items()]
XMAX = max(p["n"] for p in pts) * 1.08
YMAX = max(p["d"] for p in pts) + 1
smax = max(p["size"] for p in pts) or 1

W, L, T, P, R = 1080, 148, 208, 460, 300
H = T + P + 208
def sx(v): return L + v / XMAX * P
def sy(v): return T + P - v / YMAX * P
def sr(s): return 5 + (s / smax) ** 0.5 * 13

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "Parts are not pruned. They are opened once and closed.",
             20, INK, weight="600"))
b.append(txt(40, 70, "Each dot is one part of CFR Title 12 that lost sections. Across: "
            "how many it lost. Up: how many separate days it took.", 13, MUTE))
b.append(txt(40, 89, "If removal were attrition, dots would climb with the axis. They sit "
            "on the floor: whatever a part loses, it loses in one action.", 13, MUTE))
b.append(txt(40, 115, "Area is how many sections the part still holds. The 836 removed on "
            "11 October 2018 — the Office of Thrift Supervision's whole rulebook — are "
            "excluded.", 12, MUTE))

for v in range(0, int(YMAX) + 1, 2):
    b.append(line(L, sy(v), L + P, sy(v), GRID, 1))
    b.append(txt(L - 10, sy(v) + 4, str(v), 10.5, MUTE, "end"))
for v in range(0, int(XMAX) + 1, 25):
    b.append(line(sx(v), T, sx(v), T + P, GRID, 1))
    b.append(txt(sx(v), T + P + 20, str(v), 10.5, MUTE, "middle"))
b.append(txt(L - 10, T - 26, "separate days", 11.5, INK, "end", "600"))
b.append(txt(L - 10, T - 10, "it took to lose them", 10.5, MUTE, "end"))
b.append(txt(L + P, T + P + 44, "sections the part lost", 11.5, INK, "end", "600"))

# If removal were attrition, a part losing n sections would take roughly n days.
b.append(txt(L + P - 6, T + 18, "attrition would put dots up here, and to the right",
             10.5, MUTE, "end", style="font-style:italic"))
b.append(f'<line x1="{L}" y1="{sy(1):.1f}" x2="{L+P}" y2="{sy(1):.1f}" '
         f'stroke="{VIOLET}" stroke-width="1.4"/>')
b.append(txt(L + P - 6, sy(1) + 16, "everything lost in one action", 10.5, VIOLET, "end"))

for p in sorted(pts, key=lambda p: -p["size"]):
    b.append(circ(sx(p["n"]), sy(p["d"]), sr(p["size"]), BLUE))
for i, p in enumerate(sorted(pts, key=lambda p: -p["n"])[:4]):
    dy = 4 if p["d"] > 1 else -sr(p["size"]) - 8
    b.append(txt(sx(p["n"]) + sr(p["size"]) + 7 if p["d"] > 1 else sx(p["n"]),
                 sy(p["d"]) + dy, f"part {p['part']} · {p['n']} lost", 11, INK,
                 "start" if p["d"] > 1 else "middle"))

multi = [p for p in pts if p["n"] >= 3]
one = [p for p in multi if p["d"] == 1]
yb = T + P + 88
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
b.append(txt(40, yb, f"Of the {len(multi)} parts that lost three or more sections, "
             f"{len(one)} lost every one of them on a single day.", 13, INK, weight="600"))
b.append(txt(40, yb + 22, "So there is no attrition to predict and no decay curve to fit. "
             "The question “which section will be removed next” has no answer; the "
             "question “which part is about to be", 12, MUTE))
b.append(txt(40, yb + 39, "opened” has one, and it is a rulemaking calendar, not this "
             "dataset. What this dataset can do is hand that rulemaking a list of what to "
             "delete while the part is open.", 12, MUTE))
b.append(txt(40, yb + 63, "Which is the point of the dead-letter scan: 12 CFR 208.23 "
             "expired in 1999, and part 208 lost eight OTHER sections in 2019 without "
             "anyone noticing that one.", 11, MUTE))
b.append(txt(40, yb + 80, "Removals are only recorded from 2017, when the eCFR version "
             "record opens. Source: eCFR versions API, snapshot 2026-09-01.", 11, MUTE))
open(OUT, "w").write(doc(W, H, b))
print(f"  cfr-removal-shape.svg — {len(pts)} parts, {len(one)}/{len(multi)} one-shot")
