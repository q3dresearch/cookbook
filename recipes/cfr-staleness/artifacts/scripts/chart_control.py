"""Does the Title 12 finding travel? The same measurement on Title 29 (Labor).

    python chart_control.py

Title 12's headline is that its old tail is mostly a publishing genre rather than
neglected regulation: 39% of everything 30 years or older sits in a subject group
the publisher labels `Interpretations`. That correction is what makes the title
look young once applied.

It does not travel, in two separate ways, and the chart shows both:

  * The LABEL is a Title 12 convention. `Interpretations` as a subject-group
    exists 12 times in Title 12 and once in Title 29. Run the shipped detector on
    Labor and it returns 6% where Title 12 returns 39% — silently, because a
    field that is empty everywhere looks exactly like a genre that is absent.
  * The GENRE really is smaller there too. Labor does carry interpretive
    bulletins — 29 CFR 775.1 "Advisory interpretations announced by the
    Administrator" is 79.8 years old and structurally unlabelled — but even a
    generous detector that reads section headings reaches only 8% of the tail.

So Labor's 626 sections at 30 years or older are, in the main, real un-updated
regulation: OSHA construction and maritime standards, Wage and Hour overtime
rules, EEOC recordkeeping. In banking the oldest text is not regulation. In
labour law it is. The two titles hold a comparable number of dated sections
(2,493 and 2,386), so the bars are directly comparable without rescaling.
"""
import os, sys, collections, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import cfrlib

TITLES = [(12, "Title 12 — Banks and Banking"), (29, "Title 29 — Labor")]
DECADES = [1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]

data = {}
for t, _ in TITLES:
    rows, live = cfrlib.load(os.path.join(cfrlib.DERIVED, f"cfr-title{t}-sections.csv"))
    d = collections.defaultdict(lambda: [0, 0])       # decade -> [other, interpretation]
    for r in live:
        dec = min(max((r["d"][-1].year // 10) * 10, 1940), 2020)
        lab = "nterpret" in ((r.get("subjgrp") or "") + (r.get("subpart") or ""))
        d[dec][1 if lab else 0] += 1
    old = [r for r in live if r["age"] >= 30]
    data[t] = dict(dec=d, n=len(live), old=len(old),
                   old_lab=sum(1 for r in old
                               if "nterpret" in ((r.get("subjgrp") or "")
                                                 + (r.get("subpart") or ""))),
                   med=st.median([r["age"] for r in live]))

MAXV = max(sum(v) for t, _ in TITLES for v in data[t]["dec"].values())
W, L, R, TOP, PH, GAP = 1040, 78, 40, 196, 200, 92
H = TOP + 2 * PH + GAP + 186
BW = (W - L - R) / len(DECADES)

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "The genre correction is a Title 12 convention, not a CFR one",
             20, INK, weight="600"))
b.append(txt(40, 70, "Every dated in-force section by the decade it was last amended. "
            "Orange is the publisher's own “Interpretations” label — the "
            "correction that makes", 13, MUTE))
b.append(txt(40, 89, "Title 12's old tail read as genre rather than neglect. The same "
            "detector on Labor returns 6% where banking returns 39%.", 13, MUTE))
b.append(txt(40, 116, "Labor holds 626 sections at 30 years or older against banking's "
            "194, and almost none are the genre. In banking the oldest text is not "
            "regulation; in labour law it is.", 12, MUTE))

b.append(rect(40, 138, 11, 11, BLUE))
b.append(txt(58, 148, "operative regulation", 12, MUTE))
b.append(rect(210, 138, 11, 11, ORANGE))
b.append(txt(228, 148, "labelled “Interpretations”", 12, MUTE))

for pi, (t, name) in enumerate(TITLES):
    y0 = TOP + pi * (PH + GAP)
    d = data[t]
    b.append(txt(L, y0 - 26, name, 13.5, INK, weight="600"))
    b.append(txt(L, y0 - 9, f"{d['n']:,} dated sections · median {d['med']:.1f}y · "
                 f"{d['old']} at 30y+, {d['old_lab']} of them labelled "
                 f"({d['old_lab']/d['old']:.0%})", 11.5, MUTE))
    for gv in (0, 250, 500, 750, 1000):
        if gv > MAXV: break
        gy = y0 + PH - gv / MAXV * PH
        b.append(line(L, gy, W - R, gy, GRID, 1))
        b.append(txt(L - 10, gy + 4, f"{gv:,}", 10.5, MUTE, "end"))
    for i, dec in enumerate(DECADES):
        other, lab = d["dec"].get(dec, [0, 0])
        x = L + i * BW + BW * 0.18
        w = BW * 0.64
        hb = other / MAXV * PH
        hl = lab / MAXV * PH
        if hb: b.append(rect(x, y0 + PH - hb, w, hb, BLUE, "none", 1, 0.85))
        if hl: b.append(rect(x, y0 + PH - hb - hl, w, hl, ORANGE, "none", 1, 0.9))
        tot = other + lab
        if tot:
            b.append(txt(x + w / 2, y0 + PH - hb - hl - 6, f"{tot:,}", 10.5, INK,
                         "middle", "600"))
            if lab:
                b.append(txt(x + w / 2, y0 + PH - hb - hl - 19, f"{lab} interp",
                             9.5, ORANGE, "middle"))
        b.append(txt(x + w / 2, y0 + PH + 17, f"{dec}s", 11, MUTE, "middle"))

yb = TOP + 2 * PH + GAP + 70
b.append(line(40, yb - 24, W - 40, yb - 24, GRID, 1))
b.append(txt(40, yb, "A detector keyed on a label that only one title uses fails "
             "silently: an empty field reads exactly like an absent genre.", 13, INK,
             weight="600"))
b.append(txt(40, yb + 21, "Labor does carry interpretive bulletins — § 775.1 "
             "“Advisory interpretations announced by the Administrator” is 79.8 "
             "years old and structurally unlabelled — but widening the", 12, MUTE))
b.append(txt(40, yb + 38, "detector to read section headings only reaches 8% of its "
             "tail. The genre is genuinely smaller there; the label is genuinely "
             "absent. Both are true and they are separate problems.", 12, MUTE))
b.append(txt(40, yb + 62, "Source: eCFR full-text API, snapshot 2026-09-01. In-force "
             "sections carrying their own Federal Register source note (35% of "
             "Title 12, 33% of Title 29).", 10.5, MUTE))

open(os.path.join(CHARTS := cfrlib.CHARTS, "cfr-control-title29.svg"), "w").write(
    doc(W, H, b))
print("cfr-control-title29.svg")
for t, _ in TITLES:
    d = data[t]
    print(f"  title {t}: {d['n']:,} dated, median {d['med']:.1f}y, "
          f"{d['old']} at 30y+ of which {d['old_lab']} labelled "
          f"({d['old_lab']/d['old']:.0%})")
