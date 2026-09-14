#!/usr/bin/env python3
"""The deadline spike is real in some years and absent in others.

**Corrected 2026-09-14.** The first version pooled every year's papers by week of the
year and reported that deadline weeks carry **1.8x** the volume at **0.69x** the
uptake. Pooling is what produced those numbers. The feed grew from about 110 papers a
month in late 2023 to over 900 in mid-2026, so a pooled week-of-year profile is
dominated by the most recent years, and two of the four years in the archive are
partial -- 2023 begins at week 7 and 2026 stops at week 31 -- so their empty weeks
deflate the off-peak average and inflate the ratio further.

Normalised within each year, the effect does not hold up as a law:

| year | deadline weeks vs the rest | complete? |
| --- | --- | --- |
| 2024 | **0.92x** -- deadline weeks are *quieter* | yes |
| 2025 | 1.43x | yes |
| 2023 | 2.18x | no, starts week 7 |
| 2026 | 1.82x | no, stops week 31 |

**On the two complete years the mean is 1.18x, not 1.8x**, and in 2024 the sign
reverses. The busiest weeks of 2024 are 40, 41 and 42 -- October, outside the deadline
set entirely -- and they are among the busiest weeks of 2025 too. Whatever drives that
autumn cluster is not in `DEAD`.

**The uptake half reverses as well.** Pooled, deadline-week papers carry 0.69x the
median stars. Split by year: 2024 runs **1.70x** -- deadline papers did *better* -- and
2025 runs 0.75x. A permutation test on the two complete years pooled puts the upvote
difference at p = 0.32, a null.

**So the prescription changes shape.** It is not "a count-based signal fires every
February and May". It is that **the seasonal profile is itself unstable**, which is
worse for anyone building on it: a fixed deadline adjustment fitted on one year is
wrong in the next, and the pooled average that looks like a stable correction is an
artifact of a growing feed.

Partial years are drawn dashed rather than dropped, because their shape is real even
where their ratio is not comparable.
"""
import sys, collections, statistics, datetime as dt
sys.path.insert(0, ".")
import paperlib as P

DEAD = {5, 6, 20, 21, 22, 23, 24}
AUTUMN = {40, 41, 42}


def main():
    f = P.feed()
    byy = collections.defaultdict(collections.Counter)
    stars = collections.defaultdict(lambda: collections.defaultdict(list))
    for pa in f.values():
        d = dt.date.fromisoformat(pa["publishedAt"][:10])
        y, w = d.isocalendar()[0], d.isocalendar()[1]
        if w > 52: continue
        byy[y][w] += 1
        if pa.get("githubStars") is not None: stars[y][w].append(pa["githubStars"])
    years = [y for y in sorted(byy) if sum(byy[y].values()) >= 1000]
    cover = {y: (min(w for w in byy[y] if byy[y][w]), max(w for w in byy[y] if byy[y][w])) for y in years}
    complete = [y for y in years if cover[y] == (1, 52)]

    W, H, L, R, T, B = 940, 540, 84, 178, 168, 132
    pw, ph = W-L-R, H-T-B
    sx = lambda w: L + (w-1)/51*pw
    mx = 2.6
    sy = lambda v: T + ph - v/mx*ph
    body = []
    for ws, lab, col in ((DEAD, "ICML / NeurIPS deadline weeks", P.HOT),
                         (AUTUMN, "weeks 40-42", P.MUTED)):
        for w in sorted(ws):
            body.append(f'<rect x="{sx(w)-pw/104:.1f}" y="{T}" width="{pw/52:.1f}" height="{ph:.1f}" '
                        f'fill="{col}" fill-opacity="0.09"/>')
    body.append(P.txt(sx(22), T-20, "ICML / NeurIPS deadline weeks", size=11, fill=P.HOT,
                      anchor="middle", weight="600"))
    body.append(P.txt(sx(41), T-20, "weeks 40-42", size=11, fill=P.MUTED, anchor="middle", weight="600"))
    for g in (0, 0.5, 1.0, 1.5, 2.0, 2.5):
        em = (g == 1.0)
        body.append(f'<line x1="{L}" y1="{sy(g):.1f}" x2="{L+pw:.1f}" y2="{sy(g):.1f}" '
                    f'stroke="{P.INK if g == 0 else (P.BASELINE if em else P.GRID)}" '
                    f'stroke-width="{1.3 if g == 0 else (1.4 if em else 1)}" '
                    f'{"stroke-dasharray=\'5 4\'" if em else ""}/>')
        body.append(P.txt(L-10, sy(g)+4, f"{g:.1f}x", size=11, fill=P.INK2 if em else P.MUTED,
                          anchor="end", tab=True))
    body.append(P.txt(L+6, sy(1.0)-6, "that year's average week", size=10, fill=P.INK2))
    for w in (1, 10, 20, 30, 40, 50):
        body.append(P.txt(sx(w), T+ph+20, f"wk {w}", size=11, fill=P.MUTED, anchor="middle", tab=True))
    body.append(P.txt(L+pw/2, T+ph+44, "ISO week of the year", size=12, fill=P.INK2, anchor="middle"))
    body.append(P.txt(L-10, T-60, "papers that week, indexed to THAT YEAR's own average week", size=12, fill=P.INK2))
    body.append(P.txt(L-10, T-44, "so a year with 31 weeks of coverage is comparable to one with 52", size=10.5, fill=P.MUTED))

    # Fixed legend slots on the right: deriving label y from each line's last point
    # stacked 2024 on 2025 and pushed 2026 into the footer.
    slot = {y: T + 6 + i*46 for i, y in enumerate(sorted(years))}
    for y in sorted(years):
        tot = sum(byy[y].values())
        lo, hi = cover[y]
        ws = [w for w in range(lo, hi+1)]
        base = tot/len(ws)          # that year's own average covered week
        v = [byy[y][w]/base for w in ws]
        full = y in complete
        col = (P.COOL if y == 2025 else P.HOT) if full else P.MUTED
        d = " ".join(("M" if i == 0 else "L") + f"{sx(w):.1f} {sy(x):.1f}" for i, (w, x) in enumerate(zip(ws, v)))
        body.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{2.2 if full else 1.4}" '
                    f'stroke-opacity="{1 if full else 0.7}" '
                    f'{"" if full else "stroke-dasharray=\'5 3\'"}/>')
        dr = statistics.mean(byy[y][w] for w in ws if w in DEAD)/statistics.mean(byy[y][w] for w in ws if w not in DEAD)
        ly = slot[y]
        body.append(f'<line x1="{L+pw+10:.1f}" y1="{ly-4:.1f}" x2="{L+pw+26:.1f}" y2="{ly-4:.1f}" '
                    f'stroke="{col}" stroke-width="{2.2 if full else 1.4}" '
                    f'{"" if full else "stroke-dasharray=\'5 3\'"}/>')
        body.append(P.txt(L+pw+32, ly, f"{y}", size=12.5, fill=col, weight="600"))
        body.append(P.txt(L+pw+10, ly+15, f"{dr:.2f}x in deadline weeks", size=10, fill=P.MUTED))
        body.append(P.txt(L+pw+10, ly+27, "complete year" if full else f"wks {lo}-{hi} only",
                          size=9.5, fill=P.MUTED))

    cd = statistics.mean(statistics.mean(byy[y][w] for w in DEAD)/statistics.mean(byy[y][w] for w in range(1, 53) if w not in DEAD) for y in complete)
    sr = {}
    for y in complete:
        dsm = statistics.median([x for w in DEAD for x in stars[y][w]])
        osm = statistics.median([x for w in range(1, 53) if w not in DEAD for x in stars[y][w]])
        sr[y] = dsm/osm
    foot = [f"Mean over the two COMPLETE years is {cd:.2f}x, not the 1.8x that pooling gives. In {min(complete)} the "
            f"sign reverses — deadline weeks are quieter than the rest of the year.",
            f"Uptake reverses too: median stars in deadline weeks run {sr[2024]:.2f}x in 2024 and {sr[2025]:.2f}x in "
            f"2025. On both complete years the upvote difference is a null at p = 0.32.",
            "Pooling produced the original 1.8x because the feed grew from ~110 papers a month to over 900, so "
            "recent years dominate, and two of four years are partial.",
            "The usable prescription is not 'volume follows the calendar' but 'the seasonal profile is unstable' — "
            "a deadline adjustment fitted on one year is wrong in the next."]
    print(P.write("3-calendar.svg", P.frame(
        W, H, "The deadline spike is real in some years and absent in others",
        "Each year's papers by ISO week, indexed to that year's own average week — so a feed that grew "
        "eightfold cannot drive the shape.", body, foot, chars=124)))


main()
