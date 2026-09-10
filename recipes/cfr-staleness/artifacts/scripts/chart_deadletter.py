"""Rules that announce their own expiry, against the day they were last edited.

    CFR_WORK=./work python chart_deadletter.py <sunset12.csv> <sunset29.csv>

Both axes are dates on one scale, so the dashed 45-degree line is "last edited on
the day it expired". Above it means the agency was still editing text that
declares itself no longer in effect. Three of the ten are above it. The worst,
12 CFR 208.23, states "the terms of this section will no longer be in effect as
of January 1, 1999" and was amended in 2013 — fourteen years after its own death
date, and it is still printed today.
"""
import os, sys, csv, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import cfrlib

TODAY = dt.date(2026, 9, 10)
OUT = os.path.join(cfrlib.CHARTS, "cfr-dead-letter.svg")
TITLECOL = {"12": BLUE, "29": ORANGE}

pts = []
for path in sys.argv[1:]:
    t = "29" if "29" in os.path.basename(path) else "12"
    rows, live = cfrlib.load(os.path.join(cfrlib.DERIVED, f"cfr-title{t}-sections.csv"))
    by = {r["section"]: r for r in rows}
    for r in csv.DictReader(open(path)):
        if r["passed"] != "yes":
            continue
        sec = by.get(r["section"])
        if not sec or not sec["d"]:
            continue                       # cannot place it without an edit date
        pts.append({"t": t, "sec": r["section"], "exp": dt.date.fromisoformat(r["expiry"]),
                    "last": sec["d"][-1], "head": r["heading"]})
if len(pts) < 4:
    print("too few dead-letter sections to plot"); raise SystemExit(1)

LO, HI = dt.date(1988, 1, 1), dt.date(2028, 1, 1)
SPAN = (HI - LO).days
W, L, T, P, R = 1080, 92, 208, 520, 300
H = T + P + 228

def sx(d): return L + (d - LO).days / SPAN * P
def sy(d): return T + P - (d - LO).days / SPAN * P

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "Rules that say they are dead, and the edits made afterwards",
             20, INK, weight="600"))
b.append(txt(40, 70, "Every section of CFR Title 12 and Title 29 whose own text sets "
            "an expiry date that has passed \u2014 all of them are Title 12.",
            13, MUTE))
b.append(txt(40, 89, "Up: the day it was last amended. Both axes are the same scale, so "
            "the dashed line is “last edited on the day it expired”.", 13, MUTE))
b.append(txt(40, 115, "Above the line the agency was still editing text that declares "
            "itself no longer in effect. All of it is still printed in the code today.",
            12, MUTE))
for i, (t, lab) in enumerate((("12", "Title 12 — Banks and Banking"),
                              ("29", "Title 29 — Labor · none found"))):
    b.append(circ(44 + i * 250, 141, 6, TITLECOL[t]))
    b.append(txt(56 + i * 250, 145, lab, 11.5, MUTE))

for y in range(1990, 2028, 5):
    d = dt.date(y, 1, 1)
    b.append(line(L, sy(d), L + P, sy(d), GRID, 1))
    b.append(txt(L - 10, sy(d) + 4, str(y), 10.5, MUTE, "end"))
    b.append(line(sx(d), T, sx(d), T + P, GRID, 1))
    b.append(txt(sx(d), T + P + 20, str(y), 10.5, MUTE, "middle"))
b.append(txt(L - 10, T - 12, "last amended", 11.5, INK, "end", "600"))
b.append(txt(L + P, T + P + 44, "stated expiry date", 11.5, INK, "end", "600"))
b.append(f'<line x1="{sx(LO):.1f}" y1="{sy(LO):.1f}" x2="{sx(HI):.1f}" y2="{sy(HI):.1f}" '
         f'stroke="{MUTE}" stroke-width="1" stroke-dasharray="5 5"/>')
b.append(txt(sx(dt.date(1997, 1, 1)) + 8, sy(dt.date(1997, 1, 1)) + 16,
             "edited the day it expired", 10, MUTE))
b.append(txt(L + 10, T + 22, "still being edited after it expired", 11.5, MUTE,
             style="font-style:italic"))
b.append(txt(L + P - 10, T + P - 10, "left alone since", 11.5, MUTE, "end",
             style="font-style:italic"))
# Today's line: everything left of it is overdue.
b.append(f'<line x1="{sx(TODAY):.1f}" y1="{T}" x2="{sx(TODAY):.1f}" y2="{T+P}" '
         f'stroke="{VIOLET}" stroke-width="1.2"/>')
b.append(txt(sx(TODAY) - 6, T + 14, "today", 10.5, VIOLET, "end"))

# Sections sharing an expiry AND an edit date are one rule issued by several
# agencies — the 2021 leverage relief is Fed, OCC and FDIC saying the same thing.
# Draw them once, or three labels land on top of each other and the fact that
# they are one rule is lost.
groups = {}
for q in pts:
    groups.setdefault((q["exp"], q["last"]), []).append(q)

placed = []
for (exp, last), g in sorted(groups.items()):
    c = TITLECOL[g[0]["t"]]
    b.append(circ(sx(exp), sy(last), 7.5 if len(g) == 1 else 10, c))
    if len(g) > 1:
        b.append(txt(sx(exp), sy(last) + 4, str(len(g)), 10, "#ffffff", "middle", "700"))
    if last > exp:
        b.append(f'<line x1="{sx(exp):.1f}" y1="{sy(exp):.1f}" x2="{sx(exp):.1f}" '
                 f'y2="{sy(last):.1f}" stroke="{c}" stroke-width="1.2" '
                 f'stroke-dasharray="2 3"/>')
    yrs = (TODAY - exp).days / 365.25
    lab = (f"§ {g[0]['sec']}  ·  {yrs:.0f}y overdue" if len(g) == 1
           else f"§ {' / '.join(q['sec'] for q in g)}  ·  {yrs:.0f}y overdue")
    ly = sy(last) + 4
    while any(abs(ly - o) < 15 for o in placed):
        ly += 16
    placed.append(ly)
    b.append(txt(sx(exp) + 14, ly, lab, 11, INK))
    if len(g) > 1:
        b.append(txt(sx(exp) + 14, ly + 15, "one rule, three agencies", 10, MUTE,
                     style="font-style:italic"))
        placed.append(ly + 15)

n_after = sum(1 for p in pts if p["last"] > p["exp"])
yb = T + P + 92
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
b.append(txt(40, yb, f"{len(pts)} banking rules have passed their own stated expiry and "
             f"are still in the code. {n_after} were amended AFTER that date. Title 29 "
             f"has none at all.", 13, INK, weight="600"))
b.append(txt(40, yb + 22, "12 CFR 208.23 states “the terms of this section will no longer "
             "be in effect as of January 1, 1999” and was amended in 2013. The 2021 "
             "leverage-ratio relief appears three times —", 12, MUTE))
b.append(txt(40, yb + 39, "§ 217.303 (Federal Reserve), § 3.304 (OCC) and § 324.304 "
             "(FDIC) — all expired, all identical, none removed. Nobody is checking, and "
             "the check is one regular expression.", 12, MUTE))
b.append(txt(40, yb + 63, "Only self-referential expiry counts: “this section expires”, "
             "not “the borrower's option expires”. Source notes are stripped first — "
             "they are full of dates that are publication, not expiry.", 11, MUTE))
b.append(txt(40, yb + 80, "Expiry stated without a date cannot appear here: 26 in Title "
             "12, 18 in Title 29. One more, § 1815.115, prints an OMB control number that "
             "expired in 1998 and is excluded — it is a stale", 11, MUTE))
b.append(txt(40, yb + 97, "artefact, not a rule that sunset. Source: eCFR full-text API, "
             "snapshot 2026-09-01.", 11, MUTE))
b.append("</svg>" if False else "")
open(OUT, "w").write(doc(W, H, b))
print(f"  cfr-dead-letter.svg — {len(pts)} sections, {n_after} amended after expiry")
for p in sorted(pts, key=lambda p: p["exp"]):
    print(f"    § {p['sec']:<12s} expired {p['exp']}  last amended {p['last']}"
          f"{'  ← after' if p['last'] > p['exp'] else ''}")
