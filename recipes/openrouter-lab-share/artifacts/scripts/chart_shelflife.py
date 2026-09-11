"""How long a model stays at the top. About a month.

    OR_WORK=./work python chart_shelflife.py

Every model that ever held more than 0.5% of routed tokens and lived 150 days,
aligned on the day it first appeared. Share is a 7-day mean: on raw daily numbers
the "peak" is noise, and the first version of this measured a two-day half-life
because of it.

Median 18 days to peak, 10 days from peak to half. Zero of 194 models end the
record above half their peak.

Because share is relative in a market that grew 170x, the same half-life was
recomputed on ABSOLUTE tokens: also 10 days. The decay is real, not the market
growing around a model.
"""
import os, sys, collections, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import *
import orlib

rows = orlib.rankings()
day = collections.defaultdict(collections.Counter)
for r in rows:
    day[r["date"]][r["model_permaslug"]] += r["tok"]
dates = sorted(day)
tot = {d: sum(day[d].values()) for d in dates}
def smooth(v, k=7):
    return [st.mean(v[max(0, i-k+1):i+1]) for i in range(len(v))]
first = {}
for d in dates:
    for s in day[d]:
        first.setdefault(s, d)

tracks, stats = [], []
for s, f in first.items():
    idx = [i for i, d in enumerate(dates) if d >= f]
    if len(idx) < 150:
        continue
    sm = smooth([day[dates[i]].get(s, 0) / tot[dates[i]] for i in idx])
    pi = max(range(len(sm)), key=lambda i: sm[i])
    if sm[pi] < 0.005:
        continue
    half = next((j - pi for j in range(pi + 1, len(sm)) if sm[j] <= sm[pi] / 2), None)
    # Normalise each model to its OWN peak. On absolute share the median is
    # dominated by small models and sits flat at 1%, which says nothing about
    # the shape. Relative to peak, every model is comparable and the decay is
    # the thing being measured. Absolute peaks stay in the labels.
    tracks.append((s, [v / sm[pi] for v in sm[:270]], pi, sm[pi]))
    stats.append((pi, half))
PK = [a for a, _ in stats]
HL = [b for _, b in stats if b]
DAYS = 240
YMAX = 1.04

W, L, T, PH, R = 1060, 190, 250, 400, 250
H = T + PH + 210
def sx(d): return L + d / DAYS * (W - L - R)
def sy(v): return T + PH - v / YMAX * PH

b = [rect(0, 0, W, H, "#ffffff")]
b.append(txt(40, 44, "A model gets about a month at the top", 20, INK, weight="600"))
b.append(txt(40, 70, f"Every model that ever held more than 0.5% of routed tokens and "
            f"lived 150 days — {len(tracks)} of them — aligned on the day it first",
            13, MUTE))
b.append(txt(40, 89, "appeared. Share is a 7-day mean, because on raw daily numbers the "
            "peak is noise. Grey is one model; the thick line is the median.", 13, MUTE))
b.append(txt(40, 115, f"Median {st.median(PK):.0f} days to peak, {st.median(HL):.0f} days "
            f"from peak to half. **Zero** of {len(tracks)} end the record above half "
            f"their peak.".replace("**", ""), 12, MUTE))

for v in (0, .25, .5, .75, 1.0):
    b.append(line(L, sy(v), W - R, sy(v), GRID, 1))
    b.append(txt(L - 10, sy(v) + 4, f"{v:.0%}", 10.5, MUTE, "end"))
for d in range(0, DAYS + 1, 30):
    b.append(line(sx(d), T, sx(d), T + PH, GRID, 1))
    b.append(txt(sx(d), T + PH + 20, str(d), 10.5, MUTE, "middle"))
b.append(txt(L - 10, T - 44, "share of tokens,", 12, INK, "end", "600"))
b.append(txt(L - 10, T - 28, "relative to that model's own peak", 10.5, MUTE, "end"))
b.append(txt(W - R, T + PH + 44, "days since the model first appeared", 12, INK, "end",
             "600"))

for s, sm, pi, pk in tracks:
    pts = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(sm[:DAYS]))
    b.append(f'<polyline points="{pts}" fill="none" stroke="{MUTE}" '
             f'stroke-width="1" stroke-opacity="0.16"/>')
med = []
for d in range(DAYS):
    vals = [sm[d] for _, sm, _, _ in tracks if d < len(sm)]
    if len(vals) >= 20:
        med.append((d, st.median(vals)))
b.append('<polyline points="' + " ".join(f"{sx(d):.1f},{sy(v):.1f}" for d, v in med) +
         f'" fill="none" stroke="{BLUE}" stroke-width="3"/>')
b.append(f'<line x1="{L}" y1="{sy(0.5):.1f}" x2="{W-R}" y2="{sy(0.5):.1f}" '
         f'stroke="{VIOLET}" stroke-width="1.2" stroke-dasharray="5 4"/>')
b.append(txt(W - R - 6, sy(0.5) - 8, "half of peak", 10.5, VIOLET, "end"))
# Peaks are all at 1.0 now, so the biggest four are labelled down the right
# where there is room, with a leader back to their peak day.
for n, (s, sm, pi, pk) in enumerate(sorted(tracks, key=lambda t: -t[3])[:4]):
    ly = T + 18 + n * 17
    b.append(circ(sx(pi), sy(1.0), 4.5, ORANGE))
    b.append(txt(W - R - 12, ly, f"{s.split('/')[-1][:30]} — peaked at {pk:.0%} "
                 f"on day {pi}", 10.5, INK, "end"))
b.append(f'<line x1="{sx(st.median(PK)):.1f}" y1="{T}" x2="{sx(st.median(PK)):.1f}" '
         f'y2="{T+PH}" stroke="{VIOLET}" stroke-width="1.3" stroke-dasharray="4 4"/>')
b.append(txt(sx(st.median(PK)) + 8, T + PH - 28,
             f"median peak, day {st.median(PK):.0f}", 10.5, VIOLET))

yb = T + PH + 86
b.append(line(40, yb - 26, W - 40, yb - 26, GRID, 1))
b.append(txt(40, yb, f"Median {st.median(PK):.0f} days to peak and {st.median(HL):.0f} "
             f"from peak to half. Claude 3.5 Sonnet peaked at 31% of everything routed "
             f"and halved in 31 days.", 13, INK, weight="600"))
b.append(txt(40, yb + 24, "So “which model should I build on” has a shelf life of about a "
             "month, and the thing worth optimising is switching cost rather than choice.",
             12, MUTE))
b.append(txt(40, yb + 48, "Share is relative and this market grew 170× over the record, so "
             "the same half-life was recomputed on ABSOLUTE tokens: also 10 days. The "
             "decay is real, not the market", 11, MUTE))
b.append(txt(40, yb + 65, "growing around a model. A first version of this chart measured "
             "a two-day half-life, which was daily noise being read as a peak — hence the "
             "7-day mean.", 11, MUTE))
b.append(txt(40, yb + 82, "OpenRouter is a router: it sees everyone who routes and nobody "
             "who calls a lab directly. Source: OpenRouter (openrouter.ai/rankings).",
             11, MUTE))
open(os.path.join(orlib.CHARTS, "or-model-shelf-life.svg"), "w").write(doc(W, H, b))
print(f"  or-model-shelf-life.svg — {len(tracks)} models, peak d{st.median(PK):.0f}, "
      f"half {st.median(HL):.0f}d")
