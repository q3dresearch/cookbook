#!/usr/bin/env python3
"""The field fixed sex balance and left age alone.

    python3 chart-12-sex.py

One bar is one dataset's female share, at 2.5-point resolution. **716 datasets with at least
ten classifiable subjects; the median is 53.8% female and 68% sit inside a 35-65% band.**
Pooled across 50,437 records it is 54.4%, and it holds in every modality -- MRI 54.8%, EEG
53.8%, MEG 54.5%, PET 50.0%, iEEG 49.3%.

**The point is the comparison with plate 11.** There, 18-25 year olds are 4.4 times their
population share and over-65s 0.4 times. Here the same community is balanced to within four
points. This is not general carelessness about who gets scanned: it is one demographic critique
answered and another left alone, which is a more useful thing to know than either number.

**32% of studies are still outside 35-65**, and that is not automatically a fault -- a study of
prostate cancer or of pregnancy has a reason. The distribution matters more than any one
dataset.

**Half the field is blank, which is a different problem from being wrong.** Of 101,536 subject
records, 50,437 are usable, **44,309 are simply empty**, 2,333 say n/a, and 3,980 are bare
numbers -- `1`, `0`, `2`, `-1` -- with no key in the record, because the convention is
per-dataset. An earlier draft of this module called that "half unusable", conflating a field
nobody filled in with one filled in badly.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import modality, plate, sexbalance                                       # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "12-sex.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
STEP = 0.025


def main():
    rs = sexbalance.rows()
    v = sexbalance.vocabulary()
    d = sexbalance.distribution(rs)
    mods = sexbalance.by_modality(rs)
    g = [r for r in rs if r["n_ok"] >= sexbalance.MIN_SUBJ]
    nb = int(1 / STEP) + 1
    hist = [0] * nb
    for r in g:
        hist[min(nb - 1, int(r["female"] / STEP))] += 1
    mx = max(hist)

    W, H = 1180, 710
    s = plate.open_svg(
        W, H, "The field fixed sex balance and left age alone",
        subtitle=f"{len(g):,} OpenNeuro datasets with at least {sexbalance.MIN_SUBJ} "
                 f"classifiable subjects. One bar is a 2.5-point slice of female share. "
                 f"Compare plate 11, where 18-25s are 4.4x their population share.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone auditing a pooled corpus for representativeness, or deciding which "
            "demographic gap is worth funding next",
        decide="whether neuroimaging's demographic problem is general or specific to age",
        wrong="this distribution is as skewed as the age one, in which case the field is "
              "careless about demographics generally")
    s += fr

    AX, AY, AW, AH = 250, y0 + 56, 600, 286
    bx = lambda f: AX + AW * f
    by = lambda v_: AY + AH - AH * v_ / mx
    for f in (0, .25, .35, .5, .65, .75, 1.0):
        col = INK2 if f == .5 else GRID
        s.append(f'<line x1="{bx(f):.1f}" y1="{AY:.1f}" x2="{bx(f):.1f}" '
                 f'y2="{AY+AH:.1f}" stroke="{col}" '
                 f'stroke-width="{1.4 if f == .5 else 1}"/>')
        s.append(txt(bx(f), AY + AH + 18, f"{f*100:.0f}%", size=9.5, fill=MUTED,
                     anchor="middle"))
    tick = 10 ** int(math.log10(mx))
    while mx / tick > 5:
        tick *= 2
    t = tick
    while t <= mx:
        s.append(f'<line x1="{AX:.1f}" y1="{by(t):.1f}" x2="{AX+AW:.1f}" '
                 f'y2="{by(t):.1f}" stroke="{GRID}"/>')
        s.append(txt(AX - 8, by(t) + 3, f"{t:,}", size=9, fill=MUTED, anchor="end"))
        t += tick
    s.append(txt(AX, AY + AH + 36, "share of that dataset's subjects recorded as female",
                 size=10, fill=INK2))
    s.append(txt(AX - 8, AY - 14, "datasets", size=10, fill=INK2))

    s.append(f'<rect x="{bx(.35):.1f}" y="{AY:.1f}" width="{bx(.65)-bx(.35):.1f}" '
             f'height="{AH:.1f}" fill="{GREEN}" fill-opacity="0.06"/>')
    w = AW * STEP
    for i, n in enumerate(hist):
        if not n:
            continue
        f = i * STEP
        col = GREEN if .35 <= f < .65 else AMBER
        s.append(f'<rect x="{bx(f):.1f}" y="{by(n):.1f}" width="{max(w-1,1):.1f}" '
                 f'height="{AH-(by(n)-AY):.1f}" fill="{col}" fill-opacity="0.65"/>')
    s += halo(bx(.5), AY - 30, f"median {d['median']:.0%} female", size=12, fill=INK,
              anchor="middle", weight="700")
    s += halo(bx(.5), AY + 16,
              f"{d['bands'][2]['share']:.0%} of datasets sit between 35% and 65%",
              size=10.5, fill=GREEN, anchor="middle", weight="700")

    RY = AY + AH + 74
    s.append(txt(AX - 8, RY - 12, "and what the sex field actually contains, "
                                  f"across {v['total']:,} subject records", size=10.5,
                 fill=INK, weight="700"))
    segs = (("usable", v["classifiable"], GREEN), ("blank", v["blank"], RED),
            ("bare numbers, no key", v["numeric"], AMBER),
            ("n/a", v["na"], SLATE), ("other", v["other"], SLATE))
    x = AX
    for lab, n, col in segs:
        wseg = AW * n / v["total"]
        s.append(f'<rect x="{x:.1f}" y="{RY:.1f}" width="{wseg:.1f}" height="30" '
                 f'fill="{col}" fill-opacity="0.5" stroke="{col}"/>')
        if wseg > 40:
            s += halo(x + wseg / 2, RY + 21, f"{n/v['total']:.0%}", size=13, fill=col,
                      anchor="middle", weight="700")
            s.append(txt(x + wseg / 2, RY + 46, lab, size=9.5, fill=MUTED,
                         anchor="middle"))
        x += wseg

    TX, ty = AX + AW + 42, AY - 16
    for head, body, col in (
            ("one critique answered, one not",
             f"Median {d['median']:.0%} female here, against 18-25s at 4.4x their "
             f"population share on plate 11. The same community did one and not the "
             f"other.", INK),
            ("it is not an averaging artifact",
             f"The median WITHIN a dataset is {d['median']:.0%}, not just the pool. "
             f"It holds in every modality, from iEEG at "
             f"{[m['median'] for m in mods if m['mod']=='ieeg'][0]:.0%} to MRI at "
             f"{[m['median'] for m in mods if m['mod']=='mri'][0]:.0%}.", GREEN),
            ("a third are still outside the band",
             f"{d['skewed']:.0%} sit beyond 35-65, which is not automatically a fault — a "
             f"study of pregnancy has a reason.", AMBER),
            ("the gap is blank, not wrong",
             f"{v['blank']:,} records have no sex at all. A further {v['numeric']:,} are "
             f"bare numbers whose meaning lives in a per-dataset convention that is not in "
             f"the record.", RED)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        wl = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=30, leading=12.5)
        s += wl
        ty += 12.5 * len(wl) + 14

    foot = (
        f"OpenNeuro GraphQL API, no key, fetched 2026-09-24; "
        f"latestSnapshot.summary.subjectMetadata.sex, a field never requested until now. "
        f"Classifiable means f/female/m/male in any case; {v['distinct']} distinct raw values "
        f"appear in total. Datasets need at least {sexbalance.MIN_SUBJ} classifiable subjects "
        f"to be drawn. CAVEAT: recorded sex, not gender, and a participant in two datasets is "
        f"counted twice.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {len(g):,} datasets, median {d['median']:.1%} female, "
          f"{d['bands'][2]['share']:.0%} in 35-65 band")
    print(f"    records: usable {v['classifiable']:,}, blank {v['blank']:,}, "
          f"numeric {v['numeric']:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
