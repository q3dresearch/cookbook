#!/usr/bin/env python3
"""One instrument change, and which of this recipe's findings it destroys.

A regime search over the generated fields (`gmmlib`, 21-day calendar bins, five
model-written shape features, the declared `ai_summary_model` held out of the fit)
finds two boundaries: **2026-07-23**, which is a declared extractor swap, and
**2025-12-25**, which is not declared anywhere.

Of the five features clustered on, only two carry the December break at any size --
multi-word share at 8.3 within-regime SD and keyword length at 4.4. The other three
move 0.4 to 1.4 SD, less than an author-written control. **So the regime is one
thing:** from 2025-12-25 the extractor stops emitting single-word keywords. Their
share of every keyword list drops from 0.25 to 0.14 and partly returns, to 0.21, when
the extractor is swapped again in July.

That is a narrow mechanical change with a sharp consequence, and the consequence is the
point of the chart: **it decides which keyword findings in this recipe survive and
which do not.**

**Survives: the reinforcement-learning rise.** Q27's headline goes 2.1% to 11.5%, and
the whole climb happens *inside* the first regime -- 2.84% in 2023Q2 to 10.33% in
2025Q4, +1.0pp per quarter across eleven quarters, with the steep part in 2025Q2, six
months before the boundary. No instrument change is involved. Keep it.

**Does not survive: every single-word term said to have died.** Q29 reads `llms`
(-7.2pp), `gpt-4` (4.4% -> 0.1%) and `NeRF` (2.2% -> 0.0%) as topics fading or becoming
ambient. All three are one word long, all three are flat for ten quarters and collapse
in the single quarter that contains the boundary, and they do not recover. `llms` runs
8.3, 8.0, 4.5, then **0.8**. That is the extractor's vocabulary changing, not the
field's.

**Partly survives: the multi-word risers.** `vision-language models` climbs 1.9% to
2.9% inside the first regime, jumps to 4.8% across the boundary, then falls back to
2.7% when the extractor changes again. The trend is real; the size is inflated and the
round trip is the giveaway.

**So the rule this chart exists to give:** a keyword's share may be compared across
2025-12-25 only if the keyword is multi-word, and even then the level shifts. Single-word
series must be cut at the boundary and read within a regime or not at all.

**Why the declared model is drawn but not relied on.** `ai_summary_model` is the only
provenance the archive has, and `paperlib.feed(one_extractor=True)` filters on it. It
says nothing at the boundary that does the damage. The name of the model is not the
point; the point is that the field you would use to guard against this is silent
exactly where you need it.
"""
import sys, collections, statistics
sys.path.insert(0, ".")
import paperlib as P
import gmmlib as G

B1, B2 = "2025-12-25", "2026-07-23"
TERMS = [("llms", 1), ("gpt-4", 1), ("nerf", 1),
         ("reinforcement learning", 2), ("vision-language models", 2)]
LABEL = {"llms": "llms", "gpt-4": "gpt-4", "nerf": "NeRF",
         "reinforcement learning": "reinforcement learning",
         "vision-language models": "vision-language models"}


def main():
    rows = []
    for p in P.feed(one_extractor=False).values():
        d = (p.get("submittedOnDailyAt") or p["publishedAt"])[:10]
        rows.append((d, P.quarter(p["publishedAt"]),
                     [x.strip().lower() for x in (p.get("ai_keywords") or []) if x.strip()]))
    rows.sort()

    # panel A: the instrument, in 21-day bins
    import datetime as dt
    d0 = dt.date.fromisoformat(rows[0][0])
    bins = collections.defaultdict(list)
    for d, _, ks in rows:
        bins[(dt.date.fromisoformat(d) - d0).days // 21].append((d, ks))
    keys = [b for b in sorted(bins) if len(bins[b]) >= 120]
    sing, bdate = [], []
    for b in keys:
        ks = [k for _, kk in bins[b] for k in kk]
        sing.append(sum(1 for k in ks if " " not in k)/len(ks))
        bdate.append(bins[b][len(bins[b])//2][0])

    # panel B: the consequence, by quarter
    q = collections.defaultdict(list)
    for d, qq, ks in rows: q[qq].append((d, ks))
    qs = [x for x in sorted(q) if len(q[x]) >= 150]
    qdate = {x: q[x][len(q[x])//2][0] for x in qs}
    series = {t: [sum(1 for _, kk in q[x] if t in kk)/len(q[x])*100 for x in qs] for t, _ in TERMS}

    W, L, R, T = 940, 190, 210, 168
    PA, GAPv, PB = 132, 76, 210
    H = T + PA + GAPv + PB + 206
    pw = W - L - R
    ax = lambda i: L + i/(len(keys)-1)*pw
    bx = lambda i: L + i/(len(qs)-1)*pw
    body = []

    def shade(x0f, x1f, y0, y1):
        body.append(f'<rect x="{x0f:.1f}" y="{y0:.1f}" width="{x1f-x0f:.1f}" height="{y1-y0:.1f}" '
                    f'fill="{P.HOT}" fill-opacity="0.07"/>')

    a0, a1 = T, T+PA
    b0, b1 = T+PA+GAPv, T+PA+GAPv+PB
    for xs, dates, y0, y1 in ((ax, bdate, a0, a1), (bx, [qdate[x] for x in qs], b0, b1)):
        i0 = next(i for i, d in enumerate(dates) if d >= B1)
        i1 = next(i for i, d in enumerate(dates) if d >= B2)
        shade(xs(i0-0.5), xs(i1-0.5), y0-16, y1)
        for i in (i0, i1):
            body.append(f'<line x1="{xs(i-0.5):.1f}" y1="{y0-16:.1f}" x2="{xs(i-0.5):.1f}" '
                        f'y2="{y1:.1f}" stroke="{P.INK}" stroke-width="1.4" stroke-dasharray="5 3"/>')
        if y0 == a0:
            body.append(P.txt(xs(i0-0.5)-8, y0-44, B1, size=12, fill=P.HOT, anchor="end", weight="600"))
            body.append(P.txt(xs(i0-0.5)-8, y0-28, "no declared change", size=11, fill=P.HOT, anchor="end", weight="600"))
            body.append(P.txt(xs(i1-0.5)+8, y0-44, B2, size=12, fill=P.INK2, weight="600"))
            body.append(P.txt(xs(i1-0.5)+8, y0-28, "extractor swapped", size=11, fill=P.INK2))

    # --- panel A
    lo, hi = 0.10, 0.30
    sy = lambda v: a1 - (v-lo)/(hi-lo)*(PA-20)
    for g in (0.10, 0.15, 0.20, 0.25, 0.30):
        body.append(f'<line x1="{L}" y1="{sy(g):.1f}" x2="{L+pw:.1f}" y2="{sy(g):.1f}" stroke="{P.GRID}" stroke-width="1"/>')
        body.append(P.txt(L-10, sy(g)+4, f"{g:.2f}", size=10.5, fill=P.MUTED, anchor="end", tab=True))
    d = " ".join(("M" if i == 0 else "L") + f"{ax(i):.1f} {sy(v):.1f}" for i, v in enumerate(sing))
    body.append(f'<path d="{d}" fill="none" stroke="{P.COOL}" stroke-width="2.2"/>')
    body.append(P.txt(L-10, a0-44, "THE INSTRUMENT", size=11, fill=P.INK, weight="600", anchor="end"))
    body.append(P.txt(L-10, a0-28, "share of emitted keywords", size=10.5, fill=P.MUTED, anchor="end"))
    body.append(P.txt(L-10, a0-14, "that are a single word", size=10.5, fill=P.MUTED, anchor="end"))
    # Computed, not typed: hardcoded regime labels are exactly how a number drifts
    # away from the data it describes.
    pre = [v for v, d in zip(sing, bdate) if d < B1]
    mid = [v for v, d in zip(sing, bdate) if B1 <= d < B2]
    body.append(P.txt(L+pw+12, sy(statistics.mean(pre)), f"{statistics.mean(pre):.2f}",
                      size=11, fill=P.COOL, weight="600", tab=True))
    body.append(P.txt(L+pw+12, sy(statistics.mean(mid)), f"{statistics.mean(mid):.2f}",
                      size=11, fill=P.COOL, weight="600", tab=True))
    body.append(P.txt(L+pw+12, sy(statistics.mean(mid))+14, "single-word keywords", size=10, fill=P.MUTED))
    body.append(P.txt(L+pw+12, sy(statistics.mean(mid))+26, "nearly halve", size=10, fill=P.MUTED))

    # --- panel B
    mx = 16.0
    sy2 = lambda v: b1 - v/mx*(PB-16)
    for g in (0, 4, 8, 12, 16):
        body.append(f'<line x1="{L}" y1="{sy2(g):.1f}" x2="{L+pw:.1f}" y2="{sy2(g):.1f}" '
                    f'stroke="{P.INK if g == 0 else P.GRID}" stroke-width="{1.3 if g == 0 else 1}"/>')
        body.append(P.txt(L-10, sy2(g)+4, f"{g}%", size=10.5, fill=P.MUTED, anchor="end", tab=True))
    body.append(P.txt(L-10, b0-44, "THE CONSEQUENCE", size=11, fill=P.INK, weight="600", anchor="end"))
    body.append(P.txt(L-10, b0-28, "share of the quarter's papers", size=10.5, fill=P.MUTED, anchor="end"))
    body.append(P.txt(L-10, b0-14, "carrying the keyword", size=10.5, fill=P.MUTED, anchor="end"))
    # Labels placed from the highest ending value down, each pushed below the last.
    # Dodging in TERMS order scrambled them: vision-language models ended up labelling
    # a line three rows above its own.
    placed = []
    for t, nw in sorted(TERMS, key=lambda x: -series[x[0]][-1]):
        v = series[t]
        col = P.HOT if nw == 1 else P.COOL
        d = " ".join(("M" if i == 0 else "L") + f"{bx(i):.1f} {sy2(x):.1f}" for i, x in enumerate(v))
        body.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.1" '
                    f'{"stroke-dasharray=\'6 3\'" if nw == 1 else ""}/>')
        ly = sy2(v[-1])
        if placed: ly = max(ly, placed[-1] + 25)
        placed.append(ly)
        body.append(f'<line x1="{L+pw:.1f}" y1="{sy2(v[-1]):.1f}" x2="{L+pw+8:.1f}" y2="{ly:.1f}" '
                    f'stroke="{col}" stroke-width="0.9" stroke-opacity="0.5"/>')
        body.append(P.txt(L+pw+12, ly+4, LABEL[t], size=11, fill=col, weight="600"))
        body.append(P.txt(L+pw+12, ly+16, "one word — dies at the break" if nw == 1
                          else "multi-word — survives", size=9.5, fill=P.MUTED))
    for i, x in enumerate(qs):
        if i % 2 == 0:
            body.append(P.txt(bx(i), b1+20, x, size=10, fill=P.MUTED, anchor="middle"))
    i_rl = qs.index("2025Q2")
    body.append(f'<line x1="{bx(i_rl):.1f}" y1="{sy2(11.57)-6:.1f}" x2="{bx(i_rl):.1f}" '
                f'y2="{sy2(16)+4:.1f}" stroke="{P.COOL}" stroke-width="1" stroke-dasharray="3 3"/>')
    body.append(P.txt(bx(i_rl)-7, sy2(14.6), "RL climbs HERE — inside one regime,", size=10.5,
                      fill=P.COOL, weight="600", anchor="end"))
    body.append(P.txt(bx(i_rl)-7, sy2(14.6)+13, "six months before the break. It survives.",
                      size=10.5, fill=P.COOL, anchor="end"))

    foot = ["The rule: a keyword share may be compared across 2025-12-25 only if the keyword is multi-word — and "
            "even then the level is inflated between the two breaks.",
            "KEEP Q27's reinforcement-learning rise: 2.84% to 10.33% entirely inside the first regime, +1.0pp per "
            "quarter over eleven quarters.",
            "RETRACT Q29's dead topics: llms, gpt-4 and NeRF are all one word, flat for ten quarters, and collapse "
            "in the quarter holding the boundary.",
            "HAIRCUT the multi-word risers: vision-language models goes 1.9 -> 2.9 inside the regime, jumps to 4.8 "
            "across it, falls back to 2.7 at the next change.",
            "Boundaries located by GMM on five shape features in 21-day bins, declared model held out of the fit. "
            "Both reproduce at 21-, 28- and 35-day bins."]
    print(P.write("11-instrument.svg", P.frame(
        W, H, "An undeclared extractor change, and the findings it decides",
        "From 2025-12-25 the extractor nearly halves how many single-word keywords it emits. Every 'dead topic' in "
        "this recipe is a single word.", body, foot, chars=126)))


main()
