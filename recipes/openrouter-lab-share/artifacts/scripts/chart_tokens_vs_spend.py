"""Share of tokens against share of spend. The word "share" picks the winner.

    OR_WORK=./work python chart_tokens_vs_spend.py

Both axes are shares of the same population on the same scale, so the dashed 45
degree line is parity: a lab sitting on it earns exactly in proportion to the
traffic it serves. Above it a lab is paid more than it serves; below it, less.

DeepSeek serves a third of the tokens and takes a tenth of the spend. Anthropic
serves 8% and takes 41%. Both statements are true of the same month, and any
headline of the form "lab X is winning" has quietly chosen which one to mean.

WHAT THIS IS NOT. Input-token list price only: completion tokens cost several
times more and are not counted, and nobody large pays list. It covers the 57% of
August tokens that join to a price. And it is spend routed through OpenRouter,
which is not lab revenue — OpenRouter sees everyone who routes and nobody who
calls a lab directly. A direction, not an invoice.
"""
import os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import orlib

START = "2026-08-01"
rows = orlib.window(orlib.rankings(), START)
pr = orlib.prices()
tok, rev = collections.Counter(), collections.Counter()
for r in rows:
    s = r["model_permaslug"]
    if s in pr:
        tok[orlib.lab(s)] += r["tok"]
        rev[orlib.lab(s)] += r["tok"] * pr[s]
TT, TR = sum(tok.values()), sum(rev.values())
cover = TT / sum(r["tok"] for r in rows)
pts = [{"lab": l, "t": tok[l] / TT, "r": rev[l] / TR, "abs": tok[l]}
       for l in tok if tok[l] / TT >= 0.002 or rev[l] / TR >= 0.002]
MAX = max(max(p["t"] for p in pts), max(p["r"] for p in pts)) * 1.12

W, L, T, P, R = 1020, 132, 250, 560, 200
H = T + P + 220
def sx(v): return L + v / MAX * P
def sy(v): return T + P - v / MAX * P
def sr(a): return 5 + (a / max(x["abs"] for x in pts)) ** 0.5 * 16

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "Whoever picks the denominator picks the winner", 20, INK, weight="600"))
b.append(txt(40, 70, "Every lab routed through OpenRouter in August 2026. Across: its share "
            "of tokens served. Up: its share of what those tokens cost at", 13, MUTE))
b.append(txt(40, 89, "list price. Both axes are shares of the same population on the same "
            "scale, so the dashed line is parity — paid exactly in proportion", 13, MUTE))
b.append(txt(40, 108, "to what you serve. Area is absolute tokens.", 13, MUTE))
b.append(txt(40, 134, "DeepSeek serves a third of the tokens and takes a tenth of the "
            "spend. Anthropic serves 8% and takes 41%. Both are true of the same month.",
            12, MUTE))

for v in (0, .1, .2, .3, .4):
    if v > MAX: break
    b.append(line(L, sy(v), L + P, sy(v), GRID, 1))
    b.append(txt(L - 10, sy(v) + 4, f"{v:.0%}", 10.5, MUTE, "end"))
    b.append(line(sx(v), T, sx(v), T + P, GRID, 1))
    b.append(txt(sx(v), T + P + 20, f"{v:.0%}", 10.5, MUTE, "middle"))
b.append(txt(L - 10, T - 28, "share of SPEND", 12, INK, "end", "600"))
b.append(txt(L - 10, T - 12, "tokens × input list price", 10.5, MUTE, "end"))
b.append(txt(L + P, T + P + 44, "share of TOKENS served", 12, INK, "end", "600"))
b.append(f'<line x1="{sx(0):.1f}" y1="{sy(0):.1f}" x2="{sx(MAX):.1f}" y2="{sy(MAX):.1f}" '
         f'stroke="{MUTE}" stroke-width="1" stroke-dasharray="5 5"/>')
b.append(txt(sx(MAX * .74), sy(MAX * .74) - 10, "paid in proportion to what you serve",
             10.5, MUTE, "middle"))
b.append(txt(L + 12, T + 22, "paid MORE than it serves", 11.5, MUTE,
             style="font-style:italic"))
b.append(txt(L + P - 12, T + P - 12, "serves MORE than it is paid", 11.5, MUTE, "end",
             style="font-style:italic"))

for p in sorted(pts, key=lambda p: -p["abs"]):
    c = ORANGE if p["lab"] in orlib.CN else BLUE
    b.append(circ(sx(p["t"]), sy(p["r"]), sr(p["abs"]), c))
marks = [(sx(p["t"]), sy(p["r"]), sr(p["abs"])) for p in pts]
taken = []
def free(bx):
    return not (any(bx[0] < o[2] and o[0] < bx[2] and bx[1] < o[3] and o[1] < bx[3] for o in taken)
                or any(bx[0] < cx+rr and cx-rr < bx[2] and bx[1] < cy+rr and cy-rr < bx[3]
                       for cx, cy, rr in marks))
for p in sorted(pts, key=lambda p: -max(p["t"], p["r"])):
    if max(p["t"], p["r"]) < 0.012:
        continue
    lab_s = f"{p['lab']}  {p['t']:.0%} / {p['r']:.0%}"
    x, y, rr = sx(p["t"]), sy(p["r"]), sr(p["abs"])
    w = len(lab_s) * 6.2 + 10
    for dy in (0, -15, 15, -30, 30, -45, 45):
        for anc in ("start", "end"):
            x0 = x + rr + 7 if anc == "start" else x - rr - 7 - w
            bx = (x0, y + dy - 8, x0 + w, y + dy + 6)
            if bx[0] < 44 or bx[2] > W - 30 or not free(bx):
                continue
            taken.append(bx)
            b.append(txt(x + (rr + 7 if anc == "start" else -rr - 7), y + dy + 4,
                         lab_s, 11, INK, anc))
            break
        else:
            continue
        break
b.append(circ(W - R + 44, T + 10, 7, ORANGE))
b.append(txt(W - R + 58, T + 14, "Chinese lab", 11.5, MUTE))
b.append(circ(W - R + 44, T + 34, 7, BLUE))
b.append(txt(W - R + 58, T + 38, "everyone else", 11.5, MUTE))

cn_t = sum(p["t"] for p in pts if p["lab"] in orlib.CN)
cn_r = sum(p["r"] for p in pts if p["lab"] in orlib.CN)
yb = T + P + 92
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
b.append(txt(40, yb, f"Chinese labs serve {cn_t:.0%} of the tokens and take {cn_r:.0%} of "
             f"the spend. Anthropic serves 8% and takes 41%.", 13, INK, weight="600"))
b.append(txt(40, yb + 24, "Both numbers are real. The word “share” is doing the lying, and "
             "which one a headline means is usually whichever supports it.", 12, MUTE))
b.append(txt(40, yb + 48, f"Input-token LIST price only — completion tokens cost several "
             f"times more and are not counted, and nobody large pays list. Covers the "
             f"{cover:.0%} of August tokens that join", 11, MUTE))
b.append(txt(40, yb + 65, "to a price, keyed on model_permaslug. And this is spend routed "
             "through OpenRouter, which is not lab revenue: OpenRouter sees everyone who "
             "routes and nobody who calls a lab", 11, MUTE))
b.append(txt(40, yb + 82, "directly. A direction, not an invoice. "
             "Source: OpenRouter (openrouter.ai/rankings).", 11, MUTE))
open(os.path.join(orlib.CHARTS, "or-tokens-vs-spend.svg"), "w").write(doc(W, H, b))
print(f"  or-tokens-vs-spend.svg — {len(pts)} labs, {cover:.0%} of tokens priced")
for p in sorted(pts, key=lambda p: -p["r"])[:6]:
    print(f"    {p['lab'][:14]:14s} tokens {p['t']:5.1%}  spend {p['r']:5.1%}  "
          f"{p['r']/p['t']:.1f}x")
