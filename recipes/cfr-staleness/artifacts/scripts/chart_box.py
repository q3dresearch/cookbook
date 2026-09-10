"""Age distribution by agency or by functional category, with a churn column."""
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
import json, os, sys
sys.path.insert(0, HERE)
from svgkit import *
import cfrlib

MODE = sys.argv[1] if len(sys.argv) > 1 else "agency"
CFG = {
 "agency": dict(
   key=lambda r: r["agency"], minn=25, out="cfr-age-by-agency.svg",
   title="How old is the law you are reading?",
   sub="Years since last amendment, for every in-force section of CFR Title 12 "
       "(Banks and Banking) that carries its own source note.",
   lab="agency", annot="annot.json"),
 "category": dict(
   key=cfrlib.category, minn=40, out="cfr-age-by-category.svg",
   title="What is sticky, and what is fluid",
   sub="The same sections grouped by what the rule does rather than who wrote it. "
       "Age separates the categories sharply. Amendment counts barely differ, so "
       "how often a rule is revised says much less than how long ago it last was.",
   lab="category", annot="annot_cat.json"),
}[MODE]

rows, live = cfrlib.load()
by = {}
for r in live:
    by.setdefault(CFG["key"](r), []).append(r)
groups = [(k, sorted(v, key=lambda r: r["age"]))
          for k, v in by.items() if len(v) >= CFG["minn"]]
groups.sort(key=lambda kv: -quantiles([r["age"] for r in kv[1]], [0.5])[0])
if MODE == "category":     # keep the residual bucket last, it is not a finding
    groups.sort(key=lambda kv: (kv[0] == "Other",))

ANNOT = json.load(open(os.path.join(HERE, CFG["annot"]))) if os.path.exists(os.path.join(HERE, CFG["annot"])) else []

W, L, CH, R = 1200, 262, 168, 40
ROWH, TOP = 42, 150
PW = W - L - CH - R
XMAX = max(r["age"] for r in live) * 1.02
NOTE_H = 34 + 20 * len(ANNOT) if ANNOT else 0
BOT = TOP + ROWH * len(groups)
H = BOT + 96 + NOTE_H
X = lambda v: L + PW * v / XMAX
CX = L + PW + 46

b = []
b.append(txt(40, 44, CFG["title"], 21, INK, weight="600"))
for i, ln in enumerate(wrap(CFG["sub"], 1090)):
    b.append(txt(40, 68 + i * 18, ln, 12.5, MUTE))
b.append(txt(40, 110, "Box spans the middle half, line inside is the median, "
                      "whiskers reach the 10th and 90th percentile. Every section "
                      "past the 90th is drawn.", 12.5, MUTE))

for v in range(0, int(XMAX) + 1, 10):
    b.append(line(X(v), TOP - 10, X(v), BOT - 6, GRID))
    b.append(txt(X(v), TOP - 16, str(v), 11, MUTE, "middle"))
b.append(txt(L + PW / 2, BOT + 44, "years since last amendment", 12, MUTE, "middle"))
b.append(txt(CX + 46, TOP - 30, "mean amendments", 11, MUTE, "middle"))
b.append(txt(CX + 46, TOP - 16, "per section", 11, MUTE, "middle"))

gmed = quantiles(sorted(r["age"] for r in live), [0.5])[0]
b.append(line(X(gmed), TOP - 10, X(gmed), BOT - 6, VIOLET, 1.2, "4 3"))
b.append(txt(X(gmed) + 7, BOT + 15, f"title median {gmed:.1f}y", 10.5, VIOLET))

marks = {}
FOUNDED = {"CFPB": 2011, "FHFA": 2008, "NCUA": 1970}
SNAP = 2026.67
capped = []

for i, (name, secs) in enumerate(groups):
    y = TOP + i * ROWH + ROWH / 2 - 4
    ages = [r["age"] for r in secs]
    p10, p25, p50, p75, p90 = quantiles(ages, [.10, .25, .50, .75, .90])
    grey = (name == "Other")
    col = MUTE if grey else BLUE
    b.append(txt(L - 14, y - 1, name, 12.5, MUTE if grey else INK, "end"))
    b.append(txt(L - 14, y + 13, f"n={len(secs):,}", 10.5, MUTE, "end"))
    b.append(line(X(p10), y, X(p25), y, col, 1.3))
    b.append(line(X(p75), y, X(p90), y, col, 1.3))
    for v in (p10, p90):
        b.append(line(X(v), y - 5, X(v), y + 5, col, 1.3))
    b.append(rect(X(p25), y - 11, X(p75) - X(p25), 22, col, col, 1.3, 0.20))
    b.append(line(X(p50), y - 11, X(p50), y + 11, col, 2.6))
    born = FOUNDED.get(name)
    # A ceiling is only worth drawing where the data is pressed against it.
    # NCUA may not hold a rule older than 1970, but its oldest is 47y against a
    # 57y ceiling, so the limit is not what shapes its box. CFPB's oldest is
    # 14.7y against 15.6y: that box ends because the bureau does.
    if born is not None and 0.90 <= max(r["age"] for r in secs) / (SNAP - born) <= 1.0:
        ceil = SNAP - born
        capped.append((name, born, ceil))
        b.append(line(X(ceil), y - 15, X(ceil), y + 15, ORANGE, 1.4,
                      dash="3 3") if "dash" in line.__code__.co_varnames
                 else f'<line x1="{X(ceil):.1f}" y1="{y-15:.1f}" '
                      f'x2="{X(ceil):.1f}" y2="{y+15:.1f}" stroke="{ORANGE}" '
                      f'stroke-width="1.4" stroke-dasharray="3 3"/>')
        b.append(txt(X(ceil) + 7, y + 4, f"agency founded {born}", 10, ORANGE))

    for r in secs:
        if r["age"] > p90:
            b.append(f'<circle cx="{X(r["age"]):.1f}" cy="{y:.1f}" r="2.4" '
                     f'fill="{ORANGE}" fill-opacity="0.75"/>')
            marks[r["section"]] = (X(r["age"]), y)
    mean_ch = sum(r["n_amend"] for r in secs) / len(secs)
    b.append(rect(CX, y - 7, 62 * mean_ch / 2.2, 14, AQUA, op=0.75))
    b.append(txt(CX + 74, y + 4, f"{mean_ch:.1f}", 11.5, INK))

for n, a in enumerate(ANNOT, 1):
    xy = marks.get(a["section"])
    if not xy:
        print("  !! no outlier marker for", a["section"])
        continue
    x, y = xy
    b.append(circ(x, y, 8.5, ORANGE, "#ffffff", 1.6))
    b.append(txt(x, y + 3.6, str(n), 10, "#ffffff", "middle", "700"))

if ANNOT:
    ny = BOT + 74
    b.append(txt(40, ny, "What those outliers actually say", 13, INK, weight="600"))
    for n, a in enumerate(ANNOT, 1):
        yy = ny + 24 + (n - 1) * 20
        b.append(circ(48, yy - 4, 8.5, ORANGE))
        b.append(txt(48, yy - 0.4, str(n), 10, "#ffffff", "middle", "700"))
        b.append(txt(64, yy, f"§ {a['section']}", 11.5, INK, weight="600"))
        b.append(txt(176, yy, a["note"], 11.5, MUTE))

foot = ("Source: eCFR full-text API, snapshot 2026-09-01. Dates parsed from Federal "
        "Register source notes. An amendment count is the number of Federal Register "
        "citations after the first, so it undercounts any section since republished.")
if capped:
    who = ", ".join(f"{n} ({b})" for n, b, _ in capped)
    b.append(txt(40, H - 36, f"A young median can mean a diligent regulator or a new "
                 f"one. {who} cannot hold a rule older than itself, so its box is "
                 f"truncated, not tidy \u2014 do not read it as", 10.5, MUTE))
    b.append(txt(40, H - 22, "faster maintenance. FHFA is 19 years old and holds "
                 "26-year-old rules inherited from OFHEO and the FHFB, so it is not "
                 "capped and is not marked.", 10.5, MUTE))
    s_shift = True
if MODE == "category":
    foot = ("Source: eCFR full-text API, snapshot 2026-09-01. Interpretation is the "
            "publisher's own subject-group label; the other categories are inferred "
            "from section headings by keyword and 28% of sections match none of them.")
b.append(txt(40, H - 6 if capped else H - 18, foot, 10.5, MUTE))
open(os.path.join(CHARTS, CFG["out"]), "w").write(doc(W, H, b))
print(f"[{MODE}] {len(groups)} groups, {sum(len(v) for _,v in groups)} sections")
for k, v in groups:
    a = sorted(r["age"] for r in v)
    q = quantiles(a, [.5, .9])
    print(f"  {k:26s} n={len(v):5d} med={q[0]:5.1f} p90={q[1]:5.1f} "
          f"max={a[-1]:5.1f} mean_amend={sum(r['n_amend'] for r in v)/len(v):4.1f}")
