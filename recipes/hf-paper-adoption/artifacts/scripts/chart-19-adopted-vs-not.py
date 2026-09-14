#!/usr/bin/env python3
"""Adopted papers do look different. Only one half of that is usable.

Split the feed by whether any top-1,000 model ever named the paper, and both signals
separate cleanly. **Median upvotes run 51 against 13. Median GitHub stars run 3,140
against 55.** A 57-fold gap on stars is the largest separation anywhere in this recipe.

(The star medians read 2,975 and 52 elsewhere in the recipe. A log axis cannot show a
zero, so this panel is restricted to papers with at least one star; the README quotes
the figure over all papers carrying a repo. Both are correct and the difference is the
27 repos sitting at exactly zero.)

**And the star half must not be read as prediction**, which is why the two panels are
drawn differently. Stars are counted *today*, after adoption has already happened, and
for most of these papers **the repository IS the model release** -- DeepSeek-R1 shows
91,991 stars because that repo is the thing people adopted. Stars and adoption are
partly the same event seen twice, not a predictor and an outcome.

The upvote half is cleaner: an upvote is cast in the week of publication, before any
model exists, so the ordering at least runs the right way. It is still weak --
`1-no-predictor` shows the best single feature reaching 7% against a 0.8% base -- but
it is a signal you could actually have acted on, and `7-budget` is where that is
turned into a rule.

**The separation is not evidence that attention causes adoption.** Both are downstream
of the same thing: a lab that ships a widely-downloaded model also writes a paper people
upvote and a repository people star. Establishing direction needs the star count as it
stood *before* the model existed, which is the one quantity a backfill cannot return
(Q14, `18-backfill`).

Drawn on a log scale because both distributions span four orders of magnitude, and as
quantile boxes rather than means because both are heavily skewed.
"""
import sys, collections, math, statistics
sys.path.insert(0, ".")
import paperlib as P


def main():
    ms, f = P.models(), P.feed()
    cited = set()
    for m in ms: cited |= P.arxiv_ids(m)
    groups = {"named by a top-1,000 model": [], "never named": []}
    for k, v in f.items():
        groups["named by a top-1,000 model" if k in cited else "never named"].append(v)

    panels = [("upvotes", lambda v: v["upvotes"], P.COOL,
               "cast the week of publication, before any model exists"),
              ("GitHub stars", lambda v: v.get("githubStars"), P.HOT,
               "counted TODAY, after adoption — often the model release itself")]
    W, L, R, T = 940, 210, 96, 196
    PH, GAP = 150, 132
    H = T + PH*2 + GAP + 156
    pw = W - L - R
    body = []
    for pi, (name, get, col, note) in enumerate(panels):
        y0 = T + pi*(PH+GAP)
        series = {g: sorted(x for x in (get(v) for v in vs) if x is not None and x > 0)
                  for g, vs in groups.items()}
        lo, hi = 1, max(max(s) for s in series.values())
        sx = lambda v: L + (math.log10(max(v, 1)))/math.log10(hi)*pw
        for g in (1, 10, 100, 1000, 10000, 100000):
            if g > hi: continue
            body.append(f'<line x1="{sx(g):.1f}" y1="{y0-10:.1f}" x2="{sx(g):.1f}" y2="{y0+PH:.1f}" '
                        f'stroke="{P.GRID}" stroke-width="1"/>')
            body.append(P.txt(sx(g), y0+PH+18, f"{g:,}", size=10.5, fill=P.MUTED, anchor="middle", tab=True))
        body.append(P.txt(L-16, y0-38, name.upper(), size=12.5, fill=P.INK, anchor="end", weight="600"))
        body.append(P.txt(L+pw, y0-38, note, size=10.5, fill=P.MUTED, anchor="end"))
        for gi, (g, s) in enumerate(series.items()):
            yy = y0 + 34 + gi*62
            q = statistics.quantiles(s, n=10)
            p10, p50, p90 = q[0], statistics.median(s), q[8]
            fill = col if gi == 0 else P.MUTED
            body.append(f'<line x1="{sx(p10):.1f}" y1="{yy:.1f}" x2="{sx(p90):.1f}" y2="{yy:.1f}" '
                        f'stroke="{fill}" stroke-width="9" stroke-opacity="0.28" stroke-linecap="round"/>')
            for e in (p10, p90):
                body.append(f'<line x1="{sx(e):.1f}" y1="{yy-9:.1f}" x2="{sx(e):.1f}" y2="{yy+9:.1f}" '
                            f'stroke="{fill}" stroke-width="1.6"/>')
            body.append(f'<circle cx="{sx(p50):.1f}" cy="{yy:.1f}" r="6" fill="{fill}"/>')
            body.append(P.txt(L-16, yy+4, g, size=11.5, fill=P.INK if gi == 0 else P.INK2, anchor="end"))
            body.append(P.txt(L-16, yy+18, f"n={len(s):,}", size=9.5, fill=P.MUTED, anchor="end"))
            body.append(P.txt(sx(p50), yy-14, f"{p50:,.0f}", size=11.5, fill=fill,
                              anchor="middle", weight="600", tab=True))
        a, b = list(series.values())
        body.append(P.txt(L+pw, y0-20, f"{statistics.median(a)/max(statistics.median(b),1):.0f}x on the median",
                          size=11.5, fill=col, anchor="end", weight="600"))

    foot = ["Bars span the 10th to 90th percentile, dots are medians — both distributions are heavily skewed, so "
            "means would be meaningless.",
            "The UPVOTE panel is usable: an upvote is cast before any model exists, so the ordering runs the right "
            "way. 7-budget turns it into a rule.",
            "The STAR panel is not. Stars are counted after adoption, and for most of these the repository IS the "
            "model release.",
            "Neither shows attention CAUSING adoption — both are downstream of the same thing: a lab that ships a "
            "downloaded model also writes an upvoted paper.",
            "Log axis, so papers with zero stars are excluded here; the README quotes the median over all papers "
            "with a repo, which is 2,975 against 52."]
    print(P.write("19-adopted-vs-not.svg", P.frame(
        W, H, "Adopted papers look different, and only one half of that is usable",
        "Every feed paper split by whether a top-1,000 model ever named it, on the two attention signals available "
        "at publication.", body, foot, chars=124)))


main()
