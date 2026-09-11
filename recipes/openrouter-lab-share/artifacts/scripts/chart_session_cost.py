"""What a coding session costs, by model. The spread is 130x.

    OR_WORK=./work python chart_session_cost.py

OpenRouter publishes the median USD per session for four agent apps, split by how
many turns the session ran. That turns "cheap models win" from a correlation into
a mechanism: agents run long sessions, and at fifty turns the model choice is a
two-orders-of-magnitude cost decision.

Each line is one model inside one app, from a 1-turn session to its longest
published turn range. The vertical distance at the right edge is the whole
argument.

This is median session cost at list price, for the models each app actually
serves. It is not a benchmark of the models and not a claim about quality.
"""
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import orlib

APPS = [("kilo-code", "Kilo Code"), ("codex", "Codex"),
        ("claude-code", "Claude Code"), ("hermes-agent", "Hermes Agent")]
ORDER = ["1-turn", "2-9-turns", "10-49-turns", "50-plus-turns"]
LABEL = {"1-turn": "1 turn", "2-9-turns": "2–9", "10-49-turns": "10–49",
         "50-plus-turns": "50+"}

data = {}
for slug, name in APPS:
    f = os.path.join(orlib.RAW, f"session-cost-{slug}.json")
    if not os.path.exists(f):
        continue
    g = collections.defaultdict(dict)
    for r in json.load(open(f))["data"]:
        g[r["model_permaslug"]][r["turn_range"]] = float(r["median_session_cost_usd"])
    data[slug] = (name, g)

import math
LO, HI = 0.001, 20.0
def ly(v): return math.log10(max(v, LO))
W, PW, T, PH, GAP = 1260, 218, 262, 300, 52
L = 96
H = T + PH + 236

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "At fifty turns, the model you pick is a 130× cost decision",
             20, INK, weight="600"))
b.append(txt(40, 70, "Median cost of one session, by how many turns it ran. Each line is "
            "one model inside one agent. Log scale — each gridline is ten times", 13, MUTE))
b.append(txt(40, 89, "the one below. Agents run long sessions, so the right-hand edge is "
            "where the money actually is.", 13, MUTE))
b.append(txt(40, 115, "This is the mechanism behind every “cheap wins” result in this "
            "recipe: it is not that developers dislike good models, it is that a long "
            "session on one costs two", 12, MUTE))
b.append(txt(40, 133, "orders of magnitude more.", 12, MUTE))

for i, (slug, (name, g)) in enumerate(data.items()):
    x0 = L + i * (PW + GAP)
    ranges = [t for t in ORDER if any(t in m for m in g.values())]
    if len(ranges) < 2:
        continue
    def px(t): return x0 + ranges.index(t) / (len(ranges) - 1) * PW
    def py(v): return T + PH - (ly(v) - ly(LO)) / (ly(HI) - ly(LO)) * PH
    for dec in (0.001, 0.01, 0.1, 1, 10):
        b.append(line(x0, py(dec), x0 + PW, py(dec), GRID, 1))
        if i == 0:
            b.append(txt(L - 10, py(dec) + 4,
                         ("$%g" % dec) if dec >= 1 else f"${dec:g}", 10.5, MUTE, "end"))
    b.append(txt(x0 + PW / 2, T - 28, name, 13, INK, "middle", "600"))
    b.append(txt(x0 + PW / 2, T - 12, f"{len(g)} models", 10.5, MUTE, "middle"))
    for t in ranges:
        b.append(txt(px(t), T + PH + 20, LABEL[t], 10.5, MUTE, "middle"))
    ends = []
    for m, series in g.items():
        pts = [(px(t), py(series[t])) for t in ranges if t in series and series[t] > 0]
        if len(pts) < 2:
            continue
        col = ORANGE if orlib.lab(m) in orlib.CN else BLUE
        b.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) +
                 f'" fill="none" stroke="{col}" stroke-width="1.6" stroke-opacity="0.6"/>')
        ends.append((series[ranges[-1]] if ranges[-1] in series else pts[-1][1], m, pts[-1]))
    real = [(series[ranges[-1]], m) for m, series in g.items() if ranges[-1] in series]
    if real:
        hi = max(real); lo = min(real)
        for v, m in (hi, lo):
            yy = py(v)
            b.append(circ(px(ranges[-1]), yy, 5,
                          ORANGE if orlib.lab(m) in orlib.CN else BLUE))
            b.append(txt(px(ranges[-1]) + 9, yy + 4,
                         f"${v:,.2f}", 10.5, INK, "start", "700"))
            b.append(txt(px(ranges[-1]) + 9, yy + 17,
                         m.split("/")[-1][:18], 9.5, MUTE))
        b.append(txt(x0 + PW / 2, T + PH + 40, f"{hi[0]/max(lo[0],1e-9):,.0f}× spread",
                     11, INK, "middle", "700"))

yb = T + PH + 96
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
b.append(txt(40, yb, "A 50-turn Kilo Code session costs $0.10 on MiMo-v2.5 and $13.24 on "
             "Claude Opus 5. In Codex it is $0.03 against $5.31.", 13, INK, weight="600"))
b.append(txt(40, yb + 24, "Orange is a Chinese lab. They are at the bottom of every panel, "
             "which is the same fact as their 66%-of-tokens and 31%-of-spend split seen "
             "from the buyer's side.", 12, MUTE))
b.append(txt(40, yb + 48, "Median session cost at list price, for the models each app "
             "actually serves — not a benchmark of the models and not a claim about "
             "quality. Apps publish different turn", 11, MUTE))
b.append(txt(40, yb + 65, "ranges; Claude Code and Hermes Agent stop short of 50+, so "
             "their spreads are measured over a shorter session than the other two.",
             11, MUTE))
b.append(txt(40, yb + 82, "Source: OpenRouter session-cost dataset, 30-day window.",
             11, MUTE))
open(os.path.join(orlib.CHARTS, "or-session-cost.svg"), "w").write(doc(W, H, b))
print(f"  or-session-cost.svg — {len(data)} apps")
