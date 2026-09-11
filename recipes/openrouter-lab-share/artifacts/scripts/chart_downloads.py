"""Downloads are not use. Rank by each and the lines cross.

    OR_WORK=./work HF_RAW=<path> python chart_downloads.py

Hugging Face download counts are the most-cited popularity number in AI
coverage. They measure how often a weights file was pulled — an intent to
self-host, or to evaluate, or simply to have. Tokens served through a router
measure something else entirely: what people actually ran, repeatedly, and paid
for.

On the models where both are observable the two ranks barely relate: Spearman
+0.12 across 15 models holding 39% of August traffic.

The clearest case is gpt-oss-20b — 6.55 million downloads, 0.22% of tokens.
DeepSeek-v4-flash has four times fewer downloads and seventy-eight times more
tokens.

SCOPE. This join can only see OPEN-WEIGHT models: a closed model has no Hugging
Face presence, so Claude and the GPT-5 series are absent by construction. It is
a statement about how open-weight popularity metrics relate to open-weight use,
not about the market.
"""
import os, sys, json, gzip, csv, re, collections, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import orlib

HF_GLOB = os.environ.get("HF_RAW") or os.path.join(
    os.path.dirname(orlib.RECIPE), "..", "..", "wss", "wss-hugging-face",
    "raw", "hf.models.text-generation", "**", "*")
files = sorted(f for f in glob.glob(HF_GLOB, recursive=True) if os.path.isfile(f))
if not files:
    raise SystemExit("no wss-hugging-face capture found; set HF_RAW")
raw = open(files[-1], "rb").read()
if raw[:2] == b"\x1f\x8b":
    raw = gzip.decompress(raw)
hf = {m["id"]: m for m in json.loads(raw)}

cat = json.load(open(os.path.join(orlib.RAW, "models-catalog.json")))["data"]
hfid = {m["id"]: m["hugging_face_id"] for m in cat if m.get("hugging_face_id")}
rows = orlib.window(orlib.rankings(), "2026-08-01")
TOT = sum(r["tok"] for r in rows)
use = collections.Counter()
for r in rows:
    use[re.sub(r"-20\d{6}$", "", r["model_permaslug"].split(":")[0])] += r["tok"]
pts = []
for orid, h in hfid.items():
    if h in hf and orid in use:
        d = int(hf[h].get("downloads") or 0)
        if d:
            pts.append({"id": orid, "dl": d, "sh": use[orid] / TOT})
cover = sum(p["sh"] for p in pts)

def ranks(key, rev=True):
    order = sorted(pts, key=lambda p: -p[key] if rev else p[key])
    return {p["id"]: i + 1 for i, p in enumerate(order)}
RD, RT = ranks("dl"), ranks("sh")
n = len(pts)
rho = 1 - 6 * sum((RD[p["id"]] - RT[p["id"]]) ** 2 for p in pts) / (n * (n * n - 1))

W, T, RH = 1060, 246, 40
LX, RX = 430, 690
H = T + n * RH + 214

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "Downloads are not use", 20, INK, weight="600"))
b.append(txt(40, 70, "The same open-weight models ranked two ways. Left: Hugging Face "
            "downloads in the last 30 days — the most-cited popularity number", 13, MUTE))
b.append(txt(40, 89, "in AI coverage. Right: share of tokens actually served through "
            "OpenRouter in August 2026. A line that stays flat means the two", 13, MUTE))
b.append(txt(40, 108, "agree about a model. Almost none of them do.", 13, MUTE))
b.append(txt(40, 134, f"Spearman rank correlation {rho:+.2f} across {n} models holding "
            f"{cover:.0%} of August traffic. Downloads measure an intent to self-host; "
            f"tokens measure use.", 12, MUTE))

b.append(txt(LX, T - 26, "ranked by DOWNLOADS", 12, INK, "end", "600"))
b.append(txt(RX, T - 26, "ranked by TOKENS SERVED", 12, INK, "start", "600"))
for p in sorted(pts, key=lambda p: RD[p["id"]]):
    y1 = T + (RD[p["id"]] - 1) * RH
    y2 = T + (RT[p["id"]] - 1) * RH
    move = RD[p["id"]] - RT[p["id"]]
    col = "#2e7d5b" if move > 2 else ("#c2553e" if move < -2 else MUTE)
    b.append(f'<path d="M{LX+10},{y1} C{(LX+RX)/2},{y1} {(LX+RX)/2},{y2} {RX-10},{y2}" '
             f'fill="none" stroke="{col}" stroke-width="2" stroke-opacity="0.75"/>')
    b.append(circ(LX + 10, y1, 5, col))
    b.append(circ(RX - 10, y2, 5, col))
    b.append(txt(LX - 4, y1 + 4, f"{p['id'][:36]}", 11.5, INK, "end"))
    b.append(txt(LX - 4, y1 + 17, f"{p['dl']:,} downloads", 10, MUTE, "end"))
    b.append(txt(RX + 6, y2 + 4, f"{p['sh']:.2%} of tokens", 11.5, INK))

yb = T + n * RH + 44
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
top_dl = min(pts, key=lambda p: RD[p["id"]])
top_tk = min(pts, key=lambda p: RT[p["id"]])
b.append(txt(40, yb, f"{top_dl['id']} is the most downloaded and serves "
             f"{top_dl['sh']:.2%} of tokens. {top_tk['id']} serves {top_tk['sh']:.1%} "
             f"with {top_dl['dl']/top_tk['dl']:.0f}x fewer downloads.", 13, INK,
             weight="600"))
b.append(txt(40, yb + 24, "Green means a model is used more than its downloads suggest; "
             "red, less. If download counts were a usage proxy these lines would be "
             "flat, and they are not.", 12, MUTE))
b.append(txt(40, yb + 48, "SCOPE: this join can only see OPEN-WEIGHT models. A closed "
             "model has no Hugging Face presence, so Claude and the GPT-5 series are "
             "absent by construction — it says how", 11, MUTE))
b.append(txt(40, yb + 65, f"open-weight popularity relates to open-weight use, not how "
             f"the market works. {n} models is small; the ranks are shown rather than a "
             f"fitted line for that reason.", 11, MUTE))
b.append(txt(40, yb + 82, "Sources: OpenRouter rankings and models catalog; Hugging Face "
             "model index via the wss-hugging-face archive.", 11, MUTE))
open(os.path.join(orlib.CHARTS, "or-downloads-vs-use.svg"), "w").write(doc(W, H, b))
print(f"  or-downloads-vs-use.svg — {n} models, Spearman {rho:+.2f}, {cover:.0%} of tokens")
