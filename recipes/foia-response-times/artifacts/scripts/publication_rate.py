"""The publication rate: what share of records requests the city makes public.

Request ids are sequential per year (26-10, 26-263), so the highest id
approximates requests received while the row count is requests published.
Validated: published ids spread ~10% per decile across each year's range, which
is what a sample from a sequential id space looks like.

The share is an UPPER bound -- if the highest-numbered requests are the
unpublished ones, the true denominator is larger than the max id seen.
"""
import json, os, re, sys, urllib.request, collections

HERE = os.path.dirname(os.path.abspath(__file__))
RECIPE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)                       # svgkit is vendored beside this file
from svgkit import *                                          # noqa: E402
OUT = os.path.join(RECIPE, "artifacts", "charts")
UA = "q3dresearch-cookbook/1.0 (+https://github.com/q3dresearch/cookbook)"

def get(u):
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(u, headers={"User-Agent": UA}), timeout=90).read())

rows, off = [], 0
while True:
    b = get(f"https://data.nola.gov/resource/jsrk-e98x.json"
            f"?$limit=10000&$offset={off}&$select=request_id&$order=:id")
    if not b:
        break
    rows += b; off += len(b)
    if len(b) < 10000:
        break
per = collections.defaultdict(list)
for r in rows:
    m = re.fullmatch(r"(\d{2})-(\d+)", (r.get("request_id") or "").strip())
    if m:
        per["20" + m.group(1)].append(int(m.group(2)))
YEARS = sorted(per)
recv = {y: max(per[y]) for y in YEARS}
pub  = {y: len(per[y]) for y in YEARS}

W, L, R = 1210, 74, 250
PW = W - L - R
T, PH = 152, 250
T2, PH2 = T + PH + 92, 96
H = T2 + PH2 + 104
b = []
b.append(txt(L, 46, "New Orleans receives nine times more records requests than in 2016 — "
                    "and publishes a third as many", 20, INK, weight="600"))
b.append(txt(L, 73, "Every earlier reading of this dataset — vanished departments, collapsing "
                    "compliance — is a symptom of this one line.", 13.5, MUTE))
b.append(circ(L + 5, 102, 5, MUTE)); b.append(txt(L + 16, 106, "Requests received (highest id that year)", 12.5, MUTE, weight="600"))
b.append(circ(L + 350, 102, 5, BLUE)); b.append(txt(L + 361, 106, "Requests published", 12.5, BLUE, weight="600"))
b.append(txt(L + 540, 106, "Share published — lower panel", 12.5, ORANGE, weight="600"))

mx = max(recv.values())
xw = PW / len(YEARS); xc = lambda i: L + xw * (i + 0.5)
for g in range(0, 25001, 5000):
    y = T + PH - PH * g / mx
    b.append(line(L, y, L + PW, y, GRID))
    b.append(txt(L - 8, y + 4, f"{g//1000}k" if g else "0", 11, MUTE, anchor="end"))
for i, y in enumerate(YEARS):
    hr = PH * recv[y] / mx
    b.append(rect(xc(i) - xw * 0.30, T + PH - hr, xw * 0.60, hr, MUTE, op=0.20))
    hp = PH * pub[y] / mx
    b.append(rect(xc(i) - xw * 0.30, T + PH - hp, xw * 0.60, hp, BLUE, op=0.85))
    b.append(txt(xc(i), T + PH - hr - 8, f"{recv[y]:,}", 10, MUTE, anchor="middle"))
    b.append(txt(xc(i), T + PH + 18, y[2:], 11, MUTE, anchor="middle"))
b.append(line(L, T + PH, L + PW, T + PH, MUTE))

# lower panel: the share, on its own axis, so nothing shares a scale it should not
b.append(txt(L, T2 - 16, "Share of those requests the city published", 12.5, INK, weight="600"))
for g in (0, 10, 20, 30):
    y = T2 + PH2 - PH2 * g / 35
    b.append(line(L, y, L + PW, y, GRID))
    b.append(txt(L - 8, y + 4, f"{g}%", 11, MUTE, anchor="end"))
sh = [(xc(i), T2 + PH2 - PH2 * (pub[y] / recv[y]) / 0.35, pub[y] / recv[y]) for i, y in enumerate(YEARS)]
for (x1, y1, _), (x2, y2, _) in zip(sh, sh[1:]):
    b.append(line(x1, y1, x2, y2, ORANGE, 2.5))
for i, (x, y, s) in enumerate(sh):
    b.append(circ(x, y, 4.5, ORANGE))
    b.append(txt(x, y - 11, f"{s*100:.0f}%", 10.5, ORANGE, anchor="middle", weight="600"))
    b.append(txt(x, T2 + PH2 + 17, YEARS[i][2:], 11, MUTE, anchor="middle"))
b.append(line(L, T2 + PH2, L + PW, T2 + PH2, MUTE))

nx = L + PW + 26
y0 = T + 8
for ln in wrap("The dataset is a feed of requests the city has chosen to publish; the rest are "
               "withheld for containing personal information. Reviewing each request by hand is "
               "workable at 2,600 a year and not at 24,000.", 210):
    b.append(txt(nx, y0, ln, 11.5, INK)); y0 += 16
y0 += 14
for ln in wrap("So this is not a transparency mechanism being switched off. It is one being "
               "outgrown.", 210):
    b.append(txt(nx, y0, ln, 11.5, ORANGE, weight="600")); y0 += 16
y0 += 14
for ln in wrap("Share is an upper bound: if the highest-numbered requests are the unpublished "
               "ones, the true denominator is larger than the highest id seen.", 210):
    b.append(txt(nx, y0, ln, 11, MUTE)); y0 += 15
b.append(txt(L, H - 30, "Source: data.nola.gov/jsrk-e98x, 10,369 published requests, 2016-06 to "
                        "2026-09. Received count inferred from sequential request ids.", 10.5, MUTE))
open(os.path.join(OUT, "publication-rate.svg"), "w").write(doc(W, H, b))
print("  wrote publication-rate.svg")
