#!/usr/bin/env python3
"""One column is consistently negative; the other is a cancellation, not a null.

    python3 chart-11-noticefam.py

Figure 10 holds the product family fixed and gets **-7.4 points** for public notice and
**+0.7** for the commercial-item flag. A single pooled mark cannot tell a genuinely small
effect from two large ones that cancel, so this draws the distribution behind each.

**They are not the same shape.** Public notice is negative in **15 of 26** families and
positive in 3, with a median absolute gap of 7.9 points. The commercial-item flag is negative
in 14 and positive in **9**, with a *larger* median absolute gap of 9.5 points. Its pooled
+0.7 is 23 of 26 families being distinguishable from zero and pointing both ways.

**Which is the difference between a finding and an artefact.** "Commercial items make no
difference" would be wrong: they make a large difference whose sign depends on what is being
bought. "Public notice makes little difference" is also wrong: it makes a consistent one.

**Why a violin and not 26 rows of intervals.** The earlier version of this drew every family as
a labelled dot with its confidence interval, and at 26 rows by two series it was unreadable --
the shape of each distribution, which is the whole claim, was the thing hardest to see. Each
family is still drawn as its own mark; the outline is only there to make the two shapes
comparable.

**What this cannot show.** Which families. The names are in figure 10's underlying fold and in
the recipe; putting 26 labels back on this plate is what made the last one unreadable. The
density outline is a kernel estimate over 26 points and should be read as a shape, not as a
probability.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
import notice                                                             # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "11-noticefam.svg")
BLUE, ORANGE = "#2e6f9e", "#b3681a"


def density(vals, grid, bw):
    """Gaussian kernel over the family effects. 26 points is a shape, not a distribution."""
    out = []
    for g in grid:
        t = sum(math.exp(-0.5 * ((g - v) / bw) ** 2) for v in vals)
        out.append(t / (len(vals) * bw * math.sqrt(2 * math.pi)))
    return out


def main():
    S = notice.stats()
    fams = S["fams"]
    series = (("post", "public notice", BLUE, "posted against not posted"),
              ("comm", "commercial item", ORANGE, "procedures used against not used"))
    vals = {t: [r[t]["diff"] * 100 for r in fams] for t, *_ in series}
    lo = min(min(v) for v in vals.values()) - 6
    hi = max(max(v) for v in vals.values()) + 6

    W, H = 1080, 858
    s = plate.open_svg(
        W, H,
        "One column is consistently negative; the other is two large effects cancelling",
        subtitle=f"The same {len(fams)} product families behind figure 10's two pooled marks, "
                 f"each family's own difference in single-bid rate with award size held "
                 f"fixed.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone reading a pooled near-zero as evidence that a column does not matter",
        decide="whether to act on a column everywhere, or only where its sign is the one "
               "you want",
        wrong="the two shapes match, or either one is symmetric about zero")
    s += fr

    AX, AY, AW, AH = 246, y0 + 66, W - 300, 386
    cy = AY + AH / 2
    ax = lambda v: AX + AW * (v - lo) / (hi - lo)
    s.append(txt(28, AY - 44, "each family's own effect, as a distribution",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(28, AY - 27, "one mark per family; the outline is a kernel density over "
                              "them and is a shape, not a probability", size=10, fill=MUTED))
    for g in range(-40, 41, 10):
        if not lo <= g <= hi:
            continue
        s.append(f'<line x1="{ax(g):.1f}" y1="{AY:.1f}" x2="{ax(g):.1f}" '
                 f'y2="{AY+AH:.1f}" stroke="{RULE if g == 0 else GRID}"/>')
        s.append(txt(ax(g), AY + AH + 18, f"{g:+d}" if g else "0", size=9, fill=MUTED,
                     anchor="middle"))
    s.append(txt(AX, AY + AH + 38, "difference in the share of competed awards that drew "
                                   "exactly one offer, percentage points",
                 size=9.5, fill=MUTED))
    s += halo(ax(0) - 8, AY + 14, "fewer single bids", size=9, fill=MUTED, anchor="end")
    s += halo(ax(0) + 8, AY + 14, "more single bids", size=9, fill=MUTED)

    grid = [lo + (hi - lo) * i / 240 for i in range(241)]
    bw = 5.0
    HALF = AH / 2 - 16
    for k, (tag, name, col, sub) in enumerate(series):
        up = -1 if k == 0 else 1          # notice above the axis, commercial below
        d = density(vals[tag], grid, bw)
        dmax = max(max(density(v, grid, bw)) for v in vals.values())
        pts = [(ax(g), cy + up * HALF * (y / dmax)) for g, y in zip(grid, d)]
        s.append('<path d="' + f"M{pts[0][0]:.1f},{cy:.1f} "
                 + " ".join(f"L{a:.1f},{b:.1f}" for a, b in pts)
                 + f' L{pts[-1][0]:.1f},{cy:.1f} Z" fill="{col}" fill-opacity="0.15" '
                   f'stroke="{col}" stroke-width="1.6"/>')
        # every family still gets its own mark, jittered only away from the axis
        for i, v in enumerate(sorted(vals[tag])):
            off = 9 + (i % 5) * 7.5
            s.append(f'<circle cx="{ax(v):.1f}" cy="{cy + up * off:.1f}" r="3.0" '
                     f'fill="{col}" fill-opacity="0.75"/>')
        med = sorted(vals[tag])[len(vals[tag]) // 2]
        s.append(f'<line x1="{ax(med):.1f}" y1="{cy + up * 4:.1f}" x2="{ax(med):.1f}" '
                 f'y2="{cy + up * (HALF + 6):.1f}" stroke="{col}" stroke-width="2.0"/>')
        s += halo(ax(med), cy + up * (HALF + 16) + (0 if up < 0 else 10),
                  f"median {med:+.1f}", size=9.5, fill=col, anchor="middle", weight="700")
        neg = sum(1 for r in fams if r[tag]["hi"] < 0)
        pos = sum(1 for r in fams if r[tag]["lo"] > 0)
        s.append(txt(AX - 18, cy + up * (HALF * 0.55), name, size=11.5, fill=col,
                     weight="700", anchor="end"))
        s.append(txt(AX - 18, cy + up * (HALF * 0.55) + 15, sub, size=9, fill=MUTED,
                     anchor="end"))
        s.append(txt(AX - 18, cy + up * (HALF * 0.55) + 30,
                     f"{neg} below zero, {pos} above", size=9, fill=INK2, anchor="end"))
    s.append(f'<line x1="{AX:.1f}" y1="{cy:.1f}" x2="{AX+AW:.1f}" y2="{cy:.1f}" '
             f'stroke="{INK2}" stroke-width="1.1"/>')
    nb = sum(1 for r in fams if r["comm"]["hi"] < 0 or r["comm"]["lo"] > 0)
    s += halo(ax(hi) - 6, cy + HALF * 0.86,
              f"pooled this is +0.7 points, and {nb} of {len(fams)} families",
              size=9.5, fill=ORANGE, anchor="end", weight="700")
    s += halo(ax(hi) - 6, cy + HALF * 0.86 + 13,
              "are distinguishable from zero, in both directions",
              size=9.5, fill=ORANGE, anchor="end", weight="700")

    # Trimmed from the plate per doctrine/what-a-footnote-carries.md; kept here because it is method: f
    # oot = (USAspending API v2 bulk download, fetched 2026-09-22; FY2016 contract
    # transactions for eleven civilian departments. The {len(fams)} product families with
    # {notice.MIN_FAM:,} or more competed awards carrying a usable bid count, where a recorded 0
    # offers is a filing artefact and not a count. Each family's mark is a Cochran-Mantel-
    # Haenszel risk difference with award size held fixed in thirteen bands, the same
    # estimator as figure 10's third rung; 'below zero' and 'above zero' count families whose
    # 95% interval clears zero. The outline is a Gaussian kernel density with a {bw:.0f}-point
    # bandwidth over {len(fams)} values -- it is drawn to make the two shapes comparable and
    # should not be read as a probability; every family is also drawn as its own mark. Family
    # names are deliberately not labelled here: the previous version of this panel carried 26
    # labelled rows with intervals and the shape, which is the claim, was the hardest thing in
    # it to see. Posting is required above a dollar line, so this is a composition control and
    # not a causal estimate. These eleven departments are 8.5% of federal contract awards and
    # Defense is 68.6%, so nothing here describes federal procurement as a whole.)
    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2016. The 26 product "
        "families with 2,000 or more competed awards carrying a usable bid count. CAVEAT: "
        "the outline is a kernel density over 26 values and is a shape, not a probability. "
        "Posting is required above a dollar line, so this is a composition control. These "
        "eleven civilian departments are 8.5% of federal contract awards; Defense (68.6%) "
        "is absent, so this is not federal procurement as a whole.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=160, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=160, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for tag, name, _, _ in series:
        v = sorted(vals[tag])
        neg = sum(1 for r in fams if r[tag]["hi"] < 0)
        pos = sum(1 for r in fams if r[tag]["lo"] > 0)
        print(f"    {name:<16} median {v[len(v)//2]:+6.1f}  range {v[0]:+.1f} to {v[-1]:+.1f}"
              f"  below zero {neg}  above {pos}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
