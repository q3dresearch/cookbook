#!/usr/bin/env python3
"""What a screening rule buys someone who has to choose, and what it cannot buy.

`1-no-predictor` establishes that nothing available at publication picks a winner: the
base rate is 0.8% and the best feature reaches 7%. That is a **picking** claim, and it
is often read as "the signals are worthless". This chart is the **portfolio** claim,
which is the one an allocator actually faces, and it points the other way.

Rank the cohort by a rule, fund the top slice, and count how many of the eventually
adopted papers you caught. **Funding the top 10% by upvotes catches 56% of them against
the 10% a random draw gives** -- a 5.6x smaller haystack from a free, same-week field.
Both statements are true at once, and neither substitutes for the other.

(An earlier version of this file quoted 7% for the random baseline. That came from
sorting on a constant key, which Python's stable sort leaves in dictionary order rather
than shuffling. Random at a 10% budget is 10% by definition, which is what the diagonal
has always drawn.)

**Stars lag in the middle and upvotes do not.** Both rules reach everything eventually
-- fund 100% of the cohort and you have funded every adopted paper by definition -- but
at a half budget upvotes has caught 97% and stars 61%. **43% of this cohort carries no
repo at all**, and the star rule cannot rank a paper it cannot see, so those sit in one
undifferentiated block at the bottom. An earlier version of this file called that a
ceiling at 62%; it is not a ceiling, the curve climbs again once the budget reaches the
block. The cost is coverage, paid in the middle of the range.

**Exposure-matched**: papers published 2023-06-01 to 2025-03-31 only, so every one has
had at least eighteen months in which to be adopted. Without that window the recent
half of the feed enters as guaranteed misses and every curve is dragged toward the
diagonal.

**The outcome is "named by any top-1,000 model", which is mostly self-citation.**
`8-two-positives` is the companion: the independent-adoption outcome does not exist yet
for any paper in this cohort, so this chart cannot be rebuilt on it.
"""
import sys, collections
sys.path.insert(0, ".")
import paperlib as P

LO, HI = "2023-06-01", "2025-03-31"

def main():
    f = P.feed(); ms = P.models()
    cited = set()
    for m in ms: cited |= P.arxiv_ids(m)
    coh = [(k, v) for k, v in f.items() if LO <= v["publishedAt"][:10] <= HI]
    tot = sum(1 for k, _ in coh if k in cited)

    rules = [
        ("upvotes",      lambda kv: kv[1]["upvotes"],                P.COOL,  22, -14),
        ("GitHub stars", lambda kv: kv[1].get("githubStars") or -1,  P.HOT,   46,  16),
        ("team size",    lambda kv: len(kv[1].get("authors") or []), P.MUTED, 68,  16),
    ]
    curves = []
    for label, key, col, lx, dy in rules:
        s = sorted(coh, key=key, reverse=True)
        pts, hit = [(0.0, 0.0)], 0
        for i, (k, _) in enumerate(s, 1):
            if k in cited: hit += 1
            if i % 12 == 0 or i == len(s): pts.append((i/len(s)*100, hit/tot*100))
        curves.append((label, pts, col, lx, dy))

    W, H, L, R, T, B = 900, 560, 74, 96, 132, 136
    pw, ph = W-L-R, H-T-B
    sx = lambda v: L + v/100*pw
    sy = lambda v: T + ph - v/100*ph
    body = []
    for g in range(0, 101, 25):
        body.append(f'<line x1="{L}" y1="{sy(g):.1f}" x2="{L+pw:.1f}" y2="{sy(g):.1f}" '
                    f'stroke="{P.GRID}" stroke-width="1"/>')
        body.append(P.txt(L-10, sy(g)+4, f"{g}%", size=11, fill=P.MUTED, anchor="end", tab=True))
        body.append(f'<line x1="{sx(g):.1f}" y1="{T}" x2="{sx(g):.1f}" y2="{T+ph:.1f}" '
                    f'stroke="{P.GRID}" stroke-width="1"/>')
        body.append(P.txt(sx(g), T+ph+20, f"{g}%", size=11, fill=P.MUTED, anchor="middle", tab=True))
    body.append(f'<line x1="{sx(0):.1f}" y1="{sy(0):.1f}" x2="{sx(100):.1f}" y2="{sy(100):.1f}" '
                f'stroke="{P.BASELINE}" stroke-width="1.4" stroke-dasharray="5 4"/>')
    body.append(P.txt(sx(62)+6, sy(58), "fund at random", size=11, fill=P.MUTED))
    body.append(P.txt(L+pw/2, T+ph+42, "share of the cohort funded   (budget)", size=12, fill=P.INK2, anchor="middle"))
    body.append(P.txt(L-52, T-18, "share of the papers that get adopted, captured", size=12, fill=P.INK2))

    for label, pts, col, lx, dy in curves:
        d = " ".join(("M" if i == 0 else "L") + f"{sx(x):.1f} {sy(y):.1f}" for i, (x, y) in enumerate(pts))
        body.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.2"/>')
        # Labelled where the curves are far apart, not at the right edge: all three
        # finish within three points of each other and the end labels overprinted.
        ly = max(y for x, y in pts if x <= lx)
        body.append(P.txt(sx(lx), sy(ly)+dy, label, size=12, fill=col, weight="600", anchor="middle"))

    # the decision point, marked once
    for label, pts, col, lx, dy in curves:
        y10 = max(y for x, y in pts if x <= 10)
        body.append(f'<circle cx="{sx(10):.1f}" cy="{sy(y10):.1f}" r="4.5" fill="{col}" '
                    f'stroke="{P.SURFACE}" stroke-width="1.6"/>')
        if label == "upvotes":
            body.append(f'<line x1="{sx(10):.1f}" y1="{sy(y10):.1f}" x2="{sx(10):.1f}" y2="{T+ph:.1f}" '
                        f'stroke="{col}" stroke-width="1" stroke-dasharray="3 3"/>')
            body.append(P.txt(sx(10)+9, sy(y10)-26, f"{y10:.0f}% caught on a 10% budget", size=11.5,
                              fill=col, weight="600"))
            body.append(P.txt(sx(10)+9, sy(y10)-13, "random gives 10%", size=10.5, fill=P.MUTED))
    foot = [f"Cohort: {len(coh):,} papers published 2023-06 to 2025-03, of which {tot} are named by a top-1,000 model. "
            f"Every paper has had 18+ months of exposure.",
            "At a half budget upvotes has caught 97% and stars 61% — 43% of this cohort has no repo, so the "
            "star rule cannot rank them at all.",
            "This does NOT contradict 1-no-predictor. No rule picks a winner; a rule still shrinks the field "
            "5.6-fold at this budget. Picking and portfolio are different questions.",
            "The outcome counted here is 'named by any top-1,000 model', which is overwhelmingly a lab citing "
            "itself — see 8-two-positives."]
    print(P.write("7-budget.svg", P.frame(W, H, "What a screening rule buys an allocator",
        "Rank the cohort by one field available the week of publication, fund the top slice, and count the "
        "eventually-adopted papers captured.", body, foot, chars=118)))

main()
