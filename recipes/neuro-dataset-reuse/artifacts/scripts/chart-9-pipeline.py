#!/usr/bin/env python3
"""Four in five datasets never publish, and the survivors take either two days or six months.

    python3 chart-9-pipeline.py

Every other plate in this recipe measures what happens to a dataset after it is published.
This one measures what happens before, which is where the losses are.

**OpenNeuro has issued 8,851 accessions and 1,891 are public.** An accession is assigned when
a dataset is *created*, so the missing 79% are abandoned drafts rather than deletions -- the
same fact that closed the capture question. It is by an order of magnitude the largest loss
anywhere in this pipeline: nothing downstream of publication removes more than a third.

**For the survivors the draft is bimodal.** 30% publish the same day and 60% inside a week,
which is a pipeline working as intended. Then the curve flattens hard: **p90 is 193 days and
p99 is 887**. One deposit in twenty takes more than a year.

**And the long draft buys nothing.** Datasets published the same day are downloaded 14.7 times
a year; those that took over six months, 12.7. The delay produces no better dataset, no larger
cohort worth the wait, and no fewer validator errors. It is friction with no yield.

**Pre-2019 is excluded from the curve and kept in the count.** OpenNeuro absorbed OpenfMRI, and
migrated datasets were created and published the same day in bulk, which would put a spike at
zero that means nothing about anybody's pipeline.

**What this cannot see.** Why a draft is abandoned. The 6,960 missing accessions could be
withdrawn consent, a project that died, a duplicate, or someone who clicked create to look
around. Nothing in the public API distinguishes them, and their absence from the Wayback record
says only that they were never public pages.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lifecycle, plate                                                  # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "9-pipeline.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
XHI = 1100.0            # days in draft, log axis


def main():
    rs = lifecycle.rows()
    fn = lifecycle.funnel(rs)
    d = lifecycle.draft(rs)
    lags = lifecycle.drafts(rs)
    spans = lifecycle.spans(rs)

    W, H = 1180, 770
    s = plate.open_svg(
        W, H, "A dataset ships in days and then keeps changing for years",
        subtitle=f"{fn['issued']:,} accessions issued, {fn['published']:,} public. Two "
                 f"durations in one dataset's life, on the same axis: {len(lags):,} draft "
                 f"times and {len(spans):,} revision spans.")
    fr, y0 = plate.frame(
        W, 86,
        who="a repository looking for where deposits are lost, or a lab budgeting the time "
            "between finishing a study and sharing it",
        decide="whether a published dataset is a finished one, and where deposits are lost",
        wrong="the two curves lie on top of each other, so publishing and finishing are "
              "the same event")
    s += fr

    # the one nested step, drawn as area because it is a ratio of counts
    BX, BY, BW, BH = 34, y0 + 40, 300, 176
    s.append(txt(BX, BY - 12, "the only real funnel step", size=11, fill=INK, weight="700"))
    s.append(f'<rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" fill="{GRID}"/>')
    h = BH * fn["published"] / fn["issued"]
    s.append(f'<rect x="{BX}" y="{BY + BH - h:.1f}" width="{BW}" height="{h:.1f}" '
             f'fill="{GREEN}" fill-opacity="0.45" stroke="{GREEN}"/>')
    s += halo(BX + BW / 2, BY + 38, f"{fn['issued'] - fn['published']:,}", size=26,
              fill=RED, anchor="middle", weight="700")
    s += halo(BX + BW / 2, BY + 56, "accessions never published", size=10, fill=RED,
              anchor="middle", weight="700")
    s += halo(BX + BW / 2, BY + BH - h / 2 + 4, f"{fn['published']:,} public  "
              f"({fn['published']/fn['issued']:.0%})", size=11, fill=INK, anchor="middle",
              weight="700")
    s += wrap(BX, BY + BH + 20,
              "An accession is issued when a dataset is created, so these are abandoned "
              "drafts, not deletions. Nothing after publication loses more than a third.",
              size=9.5, fill=MUTED, chars=46, leading=12.5)

    AX, AY, AW, AH = 430, y0 + 56, 430, 380
    lx = lambda v: AX + AW * math.log10(max(v, 0) + 1) / math.log10(XHI + 1)
    ay = lambda p: AY + AH - AH * p
    for g in (0, 1, 7, 30, 180, 365, 1000):
        s.append(f'<line x1="{lx(g):.1f}" y1="{AY:.1f}" x2="{lx(g):.1f}" '
                 f'y2="{AY+AH:.1f}" stroke="{GRID}"/>')
        s.append(txt(lx(g), AY + AH + 18, f"{g:,}", size=9, fill=MUTED, anchor="middle"))
    for p in (0, .25, .5, .75, 1.0):
        s.append(f'<line x1="{AX:.1f}" y1="{ay(p):.1f}" x2="{AX+AW:.1f}" '
                 f'y2="{ay(p):.1f}" stroke="{GRID}"/>')
        s.append(txt(AX - 8, ay(p) + 3, f"{p*100:.0f}%", size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, AY + AH + 36, "days since the dataset was created (log scale)",
                 size=10, fill=INK2))
    s.append(txt(AX - 8, AY - 14, "share that had finished the step by then", size=10,
                 fill=INK2))

    # both durations on one axis, because they are the same kind of quantity and the gap
    # between them is the whole finding
    for vals, col, lab in ((lags, BLUE, "published"), (spans, AMBER, "finished revising")):
        pts = [(lx(v), ay((i + 1) / len(vals))) for i, v in enumerate(vals)]
        step = max(1, len(pts) // 600)
        s.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts[::step])
                 + f' {pts[-1][0]:.1f},{pts[-1][1]:.1f}" fill="none" stroke="{col}" '
                 f'stroke-width="2.6"/>')
        half = vals[len(vals) // 2]
        s += halo(lx(half) + 10, ay(0.5) - 9, lab, size=10.5, fill=col, weight="700")
        s.append(f'<circle cx="{lx(half):.1f}" cy="{ay(0.5):.1f}" r="4.2" fill="{col}"/>')
        s += halo(lx(half) + 10, ay(0.5) + 12, f"median {half:,} days", size=9.5, fill=col,
                  weight="700")
    for day in (7, 365):
        a = sum(1 for v in lags if v <= day) / len(lags)
        b_ = sum(1 for v in spans if v <= day) / len(spans)
        s.append(f'<line x1="{lx(day):.1f}" y1="{ay(b_):.1f}" x2="{lx(day):.1f}" '
                 f'y2="{ay(a):.1f}" stroke="{INK}" stroke-width="1.4" '
                 f'stroke-dasharray="3 3"/>')
        far = lx(day) > AX + AW * 0.6
        s += halo(lx(day) + (-6 if far else 0), ay(a) - 10,
                  f"day {day}: {a:.0%} vs {b_:.0%}", size=9.5, fill=INK,
                  anchor="end" if far else "middle", weight="700")

    TX, ty = AX + AW + 44, AY - 16
    for head, body, col in (
            ("if you run the repository",
             f"The loss is upstream. {fn['issued']-fn['published']:,} accessions never "
             f"shipped, against {fn['published']:,} that did. Chasing download counts "
             f"optimises the wrong end.", RED),
            ("publishing is not finishing",
             f"By day 7, {sum(1 for v in lags if v<=7)/len(lags):.0%} have published but "
             f"only {sum(1 for v in spans if v<=7)/len(spans):.0%} have stopped changing. "
             f"Cite the snapshot tag, not the accession.", INK2),
            ("what an earlier version got wrong",
             "This revision curve was drawn as five bars and read as bimodal — two "
             "populations. Bin-free, its slope rises monotonically. One skewed mode. The "
             "bins made the story.", AMBER),
            ("what it cannot see",
             "Why a draft dies. Withdrawn consent, a dead project, a duplicate and idle "
             "curiosity are indistinguishable from outside.", MUTED)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        w = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=30, leading=12.5)
        s += w
        ty += 12.5 * len(w) + 15

    foot = (
        f"OpenNeuro GraphQL API, no key, fetched 2026-09-24; dataset.created and "
        f"dataset.publishDate. Accession range read from the published ids. Datasets "
        f"published before {lifecycle.MIGRATION_END + 1} are excluded from the curve because "
        f"OpenNeuro absorbed OpenfMRI and migrated records were created and published the "
        f"same day in bulk. CAVEAT: unpublished drafts are invisible to the public API, so "
        f"the 79% is inferred from the accession range and not observed directly.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {fn['issued']:,} issued, {fn['published']:,} published "
          f"({fn['published']/fn['issued']:.0%})")
    print(f"    draft n={d['n']:,}  median {d['p50']}d  p75 {d['p75']}  p90 {d['p90']}  "
          f"p99 {d['p99']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
