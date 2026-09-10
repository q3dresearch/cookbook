"""When Title 12 was last touched, splitting out the genre that is never amended.

Two panels: the full distribution, then the pre-1990 tail magnified, because the
tail is the claim and it is invisible against a 1,065-section bar.
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
import sys
from collections import Counter
sys.path.insert(0, HERE)
from svgkit import *
import cfrlib

rows, live = cfrlib.load()
isint = lambda r: "nterpret" in r["subjgrp"] or "nterpret" in r["subpart"]
DECS = list(range(1940, 2030, 10))
TAIL = [1940, 1950, 1960, 1970, 1980]
op = Counter(r["d"][-1].year // 10 * 10 for r in live if not isint(r))
ip = Counter(r["d"][-1].year // 10 * 10 for r in live if isint(r))
tot = lambda d: op.get(d, 0) + ip.get(d, 0)
pre80 = sum(tot(d) for d in TAIL[:4])
pre80i = sum(ip.get(d, 0) for d in TAIL[:4])
old30 = [r for r in live if r["age"] >= 30]
old30i = [r for r in old30 if isint(r)]

ANN = [("220.101", 1940, "A 1946 Board ruling on prompt settlement by broker-dealer "
                         "customers. Interpretations are superseded, not amended — "
                         "age is not decay here."),
       ("333.1", 1950, "FDIC's five categories of bank business: commercial, trust, "
                       "savings, industrial, cash depository. Operative, and simply "
                       "never needed changing."),
       ("615.5130", 1970, "Farm Credit bond procedure, delegated to operating "
                          "instructions in 1972 — the substance moved outside the "
                          "CFR, so the section stopped ageing.")]

W, L, R = 1180, 92, 46
PW = W - L - R
T1, PH1 = 202, 190
B1 = T1 + PH1
T2, PH2 = B1 + 122, 188
B2 = T2 + PH2
H = B2 + 84 + 34 + 20 * len(ANN) + 40

b = []
b.append(txt(40, 44, "Title 12 is young, with an old tail that is mostly not law",
             21, INK, weight="600"))
b.append(txt(40, 70, "Every in-force section of CFR Title 12 by the decade it was last "
                     "amended. The deep tail looks alarming until you separate the "
                     "genre sitting in it.", 12.5, MUTE))
b.append(txt(40, 90, f"Of the {pre80} sections last touched before 1980, {pre80i} "
                     f"({100*pre80i/pre80:.0f}%) are published interpretations — Board "
                     f"and agency rulings that are superseded by new ones, never edited "
                     f"in place.", 12.5, MUTE))
b.append(txt(40, 110, f"Across the whole 30-years-and-older population the share is "
                      f"{100*len(old30i)/len(old30):.0f}% ({len(old30i)} of "
                      f"{len(old30)}). Ageing text is not the same as neglected rules.",
             12.5, MUTE))
lx = 40
for c, lab in [(BLUE, "operative regulation"), (ORANGE, "published interpretation")]:
    b.append(rect(lx, 133, 11, 11, c, op=0.9))
    b.append(txt(lx + 17, 142.5, lab, 11.5, MUTE))
    lx += 17 + len(lab) * 6.15 + 30


def panel(decs, top, ph, base, maxv, step, title, sub, marks, interp_lab=True):
    bw = PW / len(decs)
    Y = lambda v: base - ph * v / maxv
    b.append(txt(L, top - 34, title, 13, INK, weight="600"))
    b.append(txt(L, top - 17, sub, 11.5, MUTE))
    t = step
    while t <= maxv + 1e-6:
        b.append(line(L, Y(t), W - R, Y(t), GRID))
        b.append(txt(L - 10, Y(t) + 4, f"{int(t):,}", 10.5, MUTE, "end"))
        t += step
    for i, d in enumerate(decs):
        x = L + i * bw + bw * 0.17
        w = bw * 0.66
        o, p = op.get(d, 0), ip.get(d, 0)
        if o:
            b.append(rect(x, Y(o), w, base - Y(o), BLUE, op=0.9))
        if p:
            b.append(rect(x, Y(o + p), w, Y(o) - Y(o + p), ORANGE, op=0.9))
        if o + p:
            b.append(txt(x + w / 2, Y(o + p) - 9, f"{o+p:,}", 11, INK, "middle", "600"))
            # only worth calling out where the genre is a real share of the bar
            if p and (interp_lab or p / (o + p) >= 0.15):
                b.append(txt(x + w / 2, Y(o + p) - 25, f"{p} interpretation"
                             f"{'s' if p != 1 else ''}", 9.5, ORANGE, "middle", "600"))
        marks[d] = (x + w / 2, Y(o + p))
        b.append(txt(x + w / 2, base + 22, f"{d}s", 12, INK, "middle"))
    b.append(line(L, base, W - R, base, INK, 1.4))


m1, m2 = {}, {}
panel(DECS, T1, PH1, B1, 1500, 500,
      "All nine decades", "The modern code dominates: 1,853 sections were "
      "amended in the 2010s or later.", m1, interp_lab=False)
panel(TAIL, T2, PH2, B2, 70, 20,
      "The same tail, magnified about twenty times",
      "Only the five oldest decades, rescaled so the bars are legible. Note how "
      "much of each is orange.", m2)
b.append(txt(L + PW / 2, B2 + 48, "decade the section was last amended",
             12, MUTE, "middle"))

for n, (sec, dec, _) in enumerate(ANN, 1):
    x, y = m2[dec]
    col = ORANGE if n != 2 else BLUE
    b.append(circ(x, y - 46, 9.5, col, "#ffffff", 1.6))
    b.append(txt(x, y - 42.2, str(n), 11, "#ffffff", "middle", "700"))
    b.append(line(x, y - 36, x, y - 30, GRID, 1.2))

ny = B2 + 84
b.append(txt(40, ny, "Three sections from the tail", 13, INK, weight="600"))
for n, (sec, dec, note) in enumerate(ANN, 1):
    yy = ny + 24 + (n - 1) * 20
    b.append(circ(48, yy - 4, 8.5, ORANGE if n != 2 else BLUE))
    b.append(txt(48, yy - 0.4, str(n), 10, "#ffffff", "middle", "700"))
    b.append(txt(64, yy, f"§ {sec}", 11.5, INK, weight="600"))
    b.append(txt(168, yy, note, 11.5, MUTE))

b.append(txt(40, H - 18, "Source: eCFR full-text API, snapshot 2026-09-01. In-force "
             "sections carrying their own Federal Register source note. "
             "“Interpretation” is the publisher's own subject-group label.", 10.5, MUTE))
open(os.path.join(CHARTS, "cfr-staleness-title12.svg"), "w").write(doc(W, H, b))
print(f"pre-1980 {pre80}/{pre80i}; 30y+ {len(old30i)}/{len(old30)}; "
      f"2010s+{tot(2010)+tot(2020)}")
