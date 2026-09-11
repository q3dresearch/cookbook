"""Does being better make you used? No.

    OR_WORK=./work python chart_capability.py

Across: Artificial Analysis's intelligence index, an independent composite. Up:
the share of August 2026 tokens that model actually served on OpenRouter. If
capability drove demand these would slope upward. The correlation is +0.02.

Colour is price per million input tokens, which is what DOES move with usage:
corr(log price, share) = -0.33. The cheap models are the used ones. The most
capable model on the chart serves under 2% of tokens.

Which is not a claim that capability is worthless — it is a claim that a
benchmark table is not a demand forecast, and that anyone reading leaderboard
position as market position has the wrong variable.
"""
import os, sys, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import orlib

START = "2026-08-01"
rows = orlib.window(orlib.rankings(), START)
TOT = sum(r["tok"] for r in rows)
use = collections.Counter()
for r in rows:
    use[r["model_permaslug"]] += r["tok"]
sc, pr = orlib.scores(), orlib.prices()
pts = []
for s, v in use.items():
    if s in sc and "intelligence_index" in sc[s]:
        pts.append({"slug": s, "i": sc[s]["intelligence_index"], "sh": v / TOT,
                    "p": pr.get(s, 0) * 1e6})
cover = sum(p["sh"] for p in pts)

def corr(a, b):
    n = len(a); ma, mb = sum(a)/n, sum(b)/n
    num = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    d = math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))
    return num/d if d else 0
R_I = corr([p["i"] for p in pts], [p["sh"] for p in pts])
priced = [p for p in pts if p["p"]]
R_P = corr([math.log10(max(p["p"], .01)) for p in priced], [p["sh"] for p in priced])

XMAX = max(p["i"] for p in pts) * 1.08
YMAX = max(p["sh"] for p in pts) * 1.12
RAMP = ["#bfe0f2", "#79b7dd", "#3d86bf", "#20599a", "#12336b"]
def shade(p):
    if not p: return "#cfcac0"
    for i, t in enumerate((0.3, 1, 3, 10)):
        if p <= t: return RAMP[i]
    return RAMP[4]

W, L, T, PH, R = 1020, 196, 244, 400, 250
H = T + PH + 206
def sx(v): return L + v / XMAX * (W - L - R)
def sy(v): return T + PH - v / YMAX * PH

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "Being better does not make you used", 20, INK, weight="600"))
b.append(txt(40, 70, "Each dot is one model. Across: an independent intelligence index. "
            "Up: the share of August 2026 tokens it actually served on", 13, MUTE))
b.append(txt(40, 89, "OpenRouter. Colour is price per million input tokens. If capability "
            "drove demand this would slope upward.", 13, MUTE))
b.append(txt(40, 115, f"It does not: correlation is {R_I:+.2f}. What moves with usage is "
            f"price, and it moves the wrong way — corr(log price, share) = {R_P:+.2f}.",
            12, MUTE))

for v in (0, .02, .04, .06, .08, .10, .12):
    if v > YMAX: break
    b.append(line(L, sy(v), W - R, sy(v), GRID, 1))
    b.append(txt(L - 10, sy(v) + 4, f"{v:.0%}", 10.5, MUTE, "end"))
for v in range(0, int(XMAX) + 1, 10):
    if v == 0: continue
    b.append(line(sx(v), T, sx(v), T + PH, GRID, 1))
    b.append(txt(sx(v), T + PH + 20, str(v), 10.5, MUTE, "middle"))
b.append(txt(L - 10, T - 28, "share of tokens served", 12, INK, "end", "600"))
b.append(txt(W - R, T + PH + 44, "intelligence index  ·  higher is more capable",
             12, INK, "end", "600"))

for p in sorted(pts, key=lambda p: -p["sh"]):
    b.append(circ(sx(p["i"]), sy(p["sh"]), 7, shade(p["p"])))
for p in sorted(pts, key=lambda p: -p["sh"])[:6]:
    b.append(txt(sx(p["i"]) + 11, sy(p["sh"]) + 4,
                 f"{p['slug'].split('/')[-1][:26]}  {p['sh']:.1%}", 11, INK))
# The most capable model sits on the floor with everything else, so its label
# goes ABOVE with a leader rather than into the pile.
best = max(pts, key=lambda p: p["i"])
bx, by = sx(best["i"]), sy(best["sh"])
ax, ay = W - R - 24, T + PH * 0.46   # empty: nothing sits right of 50 above 3%
b.append(f'<path d="M{ax:.1f},{ay+6:.1f} L{ax:.1f},{by-16:.1f} L{bx:.1f},{by-9:.1f}" '
         f'fill="none" stroke="{MUTE}" stroke-width="1" stroke-dasharray="3 3"/>')
b.append(txt(ax, ay - 8, "most capable model here", 11, INK, "end", "600"))
b.append(txt(ax, ay + 7, f"{best['slug'].split('/')[-1][:24]}", 10.5, MUTE, "end"))
b.append(txt(ax, ay + 21, f"{best['sh']:.1%} of tokens", 10.5, MUTE, "end"))

lx = W - R + 30
b.append(txt(lx, T + 6, "input price", 11.5, MUTE))
b.append(txt(lx, T + 21, "per Mtok", 11.5, MUTE))
for i, (c, lab) in enumerate(zip(RAMP, ("under $0.30", "$0.30-1", "$1-3", "$3-10", "over $10"))):
    b.append(rect(lx, T + 36 + i * 22, 18, 16, c))
    b.append(txt(lx + 26, T + 49 + i * 22, lab, 11, MUTE))

yb = T + PH + 84
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
b.append(txt(40, yb, f"Capability and usage are uncorrelated ({R_I:+.2f}). Price and usage "
             f"are, negatively ({R_P:+.2f}). The market buys cheap, not smart.", 13, INK,
             weight="600"))
b.append(txt(40, yb + 24, "A benchmark table is not a demand forecast. Anyone reading "
             "leaderboard position as market position has the wrong variable — which is "
             "most coverage of this industry.", 12, MUTE))
b.append(txt(40, yb + 48, f"{len(pts)} models join the benchmark feed on model_permaslug, "
             f"covering {cover:.0%} of August tokens. Intelligence index from Artificial "
             f"Analysis; price is input list price.", 11, MUTE))
b.append(txt(40, yb + 65, "OpenRouter is a router: it sees everyone who routes through it "
             "and nobody who calls a lab directly. Source: OpenRouter, Artificial Analysis.",
             11, MUTE))
open(os.path.join(orlib.CHARTS, "or-capability-vs-usage.svg"), "w").write(doc(W, H, b))
print(f"  or-capability-vs-usage.svg — {len(pts)} models, r(intel)={R_I:+.2f}, "
      f"r(log price)={R_P:+.2f}")
