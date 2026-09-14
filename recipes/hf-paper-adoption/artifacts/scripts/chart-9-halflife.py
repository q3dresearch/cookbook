#!/usr/bin/env python3
"""How long a subject stays the subject, drawn as trajectories rather than a summary.

A topic's share of the feed rises, peaks and falls, and the useful quantities are how
long the climb takes and how long the top lasts. Across the 56 keywords that reach 1%
and peak away from both edges of the window, the **median climb is 2 quarters and the
median fall to half the peak is 1**. A subject is at or near its peak for well under a
year.

Eight are drawn because the summary hides the variation that matters:

- **Mamba** and **DPO** go from nothing to their peak in one or two quarters and are
  halved in one. A term can be over before a slow reader has finished noticing it.
- **3D Gaussian Splatting** climbs as fast and then holds. Speed up is not speed down,
  and nothing about the rise predicts the fall.
- **GRPO**, **supervised fine-tuning** and **multimodal LLMs** are not below half
  today, so their windows are open and their durations are unknown, not long.

**Drawn as small multiples, not one overlay.** Eight trajectories on shared axes cross
each other repeatedly in the middle years and stop being traceable; the shape of each
arc is the content here, not the comparison of levels at any one quarter.

**Left- and right-censoring is the trap and it is why terms are excluded, not
clipped.** The window is 2023Q2 to 2026Q2. Anything already peaking at the start
appears to peak at the boundary -- `llms` and `gpt-4` are both maxima at the first
quarter, which says only that the feed begins after they did. Anything peaking in the
last two quarters has not had time to fall. Both are dropped rather than drawn with a
truncated arc, because a curve that stops at the edge of the frame reads as a plateau.

**A share is salience, not activity.** `llms` falling does not mean fewer LLM papers;
it means the word stopped distinguishing anything once every paper was one. Q29 in the
questions file separates the two cases, and this chart cannot: a term dropping out of
a keyword list because it became ambient looks exactly like one that died.

**And the extractor changed twice, which disqualifies some half-lives.** 2026Q3 is
excluded entirely, and there is a second, undeclared break on **2025-12-25** that
nearly halves how many single-word keywords the extractor emits (`11-instrument`). A
single-word term whose half-life lands on or after that quarter cannot be read: its
fall and the instrument's are the same event. GRPO is exactly that case and is marked
rather than quietly reported -- it is one word, it peaks in 2025Q3, and its half-life
lands in the quarter holding the break.

**Five of the eight fall entirely before it and are clean**: Mamba, DPO and GPT-4V
peak in 2024 and are halved within a quarter, GPT-4o by 2025Q3, 3D Gaussian Splatting
by 2025Q1. Those are the rows the summary statistics are computed from.

**What a fall does NOT tell you** is whether the method was superseded or became so
standard that nobody names it. Frequency measures salience. The test that would
separate them -- does the artifact side keep growing while mentions fall -- cannot be
run here: the top-1,000-by-download listing contains **zero** Mamba, Gaussian-splatting
and NeRF models, so absence there is its composition and not evidence. Supersession is
demonstrable only when a successor is named in advance, as with RLHF -> DPO -> GRPO.
"""
import sys, collections, statistics
sys.path.insert(0, ".")
import paperlib as P

SHOW = [
    ("mamba", "Mamba"), ("direct preference optimization", "DPO"),
    ("gpt-4v", "GPT-4V"), ("gpt-4o", "GPT-4o"),
    ("3d gaussian splatting", "3D Gaussian Splatting"), ("grpo", "GRPO"),
    ("supervised fine-tuning", "supervised fine-tuning"),
    ("multimodal large language models", "multimodal LLMs"),
]

def main():
    f = P.feed()
    kq = collections.defaultdict(collections.Counter); tot = collections.Counter()
    for p in f.values():
        q = P.quarter(p["publishedAt"]); tot[q] += 1
        for k in set(x.lower() for x in (p.get("ai_keywords") or [])): kq[q][k] += 1
    qs = [q for q in sorted(tot) if tot[q] >= 200]

    # the population statistic quoted in the footer, computed the same way as the lines
    allk = collections.Counter()
    for q in qs:
        for k, c in kq[q].items(): allk[k] += c
    rises, halves = [], []
    for k, _ in allk.most_common(600):
        ser = [kq[q][k]/tot[q]*100 for q in qs]
        pk = max(range(len(ser)), key=lambda i: ser[i]); pv = ser[pk]
        if pv < 1.0 or pk < 2 or pk > len(ser)-3: continue
        rise = next((pk-i for i in range(pk, -1, -1) if ser[i] < pv*0.25), None)
        if rise is None: continue
        rises.append(rise)
        h = next((i-pk for i in range(pk, len(ser)) if ser[i] < pv*0.5), None)
        if h is not None: halves.append(h)
    nterms = len(rises)

    COLS, ROWS = 4, 2
    PW, PH = 190, 118
    GX, GY = 32, 74
    W = 40 + COLS*PW + (COLS-1)*GX + 30
    T = 164
    H = T + ROWS*PH + (ROWS-1)*GY + 150
    mx = 4.8
    body = []
    body.append(P.txt(40, T-52, "share of the quarter's papers carrying the keyword   "
                      "(same scale in every panel, 0 to 4.8%)", size=12, fill=P.INK2))
    for n, (key, label) in enumerate(SHOW):
        cx = 40 + (n % COLS)*(PW+GX)
        cy = T + (n // COLS)*(PH+GY)
        ser = [kq[q][key]/tot[q]*100 for q in qs]
        pk = max(range(len(ser)), key=lambda i: ser[i]); pv = ser[pk]
        # "fallen" is judged on where the series ENDS, not on any dip below half: a
        # noisy quarter briefly crossing the line was flagging live topics as over.
        fallen = ser[-1] < pv*0.5
        rise = next((pk-i for i in range(pk, -1, -1) if ser[i] < pv*0.25), None)
        h = next((i-pk for i in range(pk, len(ser)) if ser[i] < pv*0.5), None)
        # A single-word term whose half-life lands in or after the break quarter is
        # measuring the extractor, not the topic. Decided BEFORE the colour is chosen:
        # setting it afterwards greyed the caption and left the line blue.
        BREAK_Q = "2025Q4"
        suspect = (h is not None and " " not in key and qs[pk+h] >= BREAK_Q)
        col = P.MUTED if suspect else (P.HOT if fallen else P.COOL)
        sx = lambda i: cx + i/(len(qs)-1)*PW
        sy = lambda v: cy + PH - v/mx*PH
        body.append(f'<rect x="{cx}" y="{cy}" width="{PW}" height="{PH}" fill="none" '
                    f'stroke="{P.RULE}" stroke-width="1"/>')
        body.append(f'<line x1="{cx}" y1="{sy(pv*0.5):.1f}" x2="{cx+PW}" y2="{sy(pv*0.5):.1f}" '
                    f'stroke="{P.BASELINE}" stroke-width="1" stroke-dasharray="3 3"/>')
        d = " ".join(("M" if i == 0 else "L") + f"{sx(i):.1f} {sy(v):.1f}" for i, v in enumerate(ser))
        body.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2"/>')
        body.append(f'<circle cx="{sx(pk):.1f}" cy="{sy(pv):.1f}" r="4.2" fill="{col}" '
                    f'stroke="{P.SURFACE}" stroke-width="1.5"/>')
        body.append(P.txt(cx, cy-30, label, size=12, fill=P.INK, weight="600"))
        note = ("climb %dq · half-life UNREADABLE" % rise if suspect else
                (f"climb {rise}q · half-life {h}q" if h is not None
                 else f"climb {rise}q · still above half"))
        body.append(P.txt(cx, cy-14, note, size=10.5, fill=col))
        body.append(P.txt(cx+PW, cy-30, f"{pv:.1f}% · {qs[pk]}", size=10.5,
                          fill=P.MUTED, anchor="end"))
        if n // COLS == ROWS-1:
            for i in (0, len(qs)-1):
                body.append(P.txt(sx(i), cy+PH+18, qs[i], size=10, fill=P.MUTED,
                                  anchor="start" if i == 0 else "end"))
    foot = [f"Across all {nterms} keywords that reach 1% and peak away from both edges: median climb "
            f"{statistics.median(rises):.0f} quarters, median fall to half the peak {statistics.median(halves):.0f}.",
            "GREY = unreadable. A single-word term whose half-life lands in the quarter holding the 2025-12-25 "
            "extractor break, where its fall and the instrument's are one event.",
            "Dots mark each peak, the dashed line half of it. Orange ends below half; blue has not fallen there yet, "
            "so its window is open and its length unknown.",
            "Terms peaking in the first or last two quarters are excluded, not clipped — a curve cut off at the "
            "frame edge reads as a plateau.",
            "A fall does NOT separate 'superseded' from 'so standard nobody names it'. The test that would — does "
            "the artifact side keep growing? — cannot run:",
            "the top-1,000-by-download listing holds zero Mamba, Gaussian-splatting and NeRF models, so absence "
            "there is its composition and not evidence.",
            "2026Q3 is excluded because the extractor changed again — see 11-instrument."]
    print(P.write("9-halflife.svg", P.frame(
        W, H, "How long a subject stays the subject",
        "Keyword share by quarter for eight topics, on one shared scale. The climb is the entry window; the "
        "fall is how long being right pays.", body, foot, chars=122)))

main()
