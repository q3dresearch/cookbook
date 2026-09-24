#!/usr/bin/env python3
"""Neuroimaging studies did not get bigger. A few got enormous.

    python3 chart-8-samplesize.py

One dot is one MRI dataset. The three lines are the 10th, 50th and 90th percentile of its
year.

**The median went from 23 subjects to 31 in a decade** -- a real trend, 1.84x per decade at
t = +4.42 -- and almost none of it is in the middle of the distribution. Ranked by percentile,
the decade's growth is **perfectly monotone**: p10 1.25x, p25 **1.00x**, p50 1.35x, p75 1.67x,
p90 2.02x, p99 3.56x. The floor did not move. The ceiling tripled.

**So this is not a field that scaled up. It is a field that grew a tail.** A handful of
consortium deposits carry the whole trend while the typical lab collects the same thirty people
it collected in 2016.

**The benchmark is the field's own.** Marek et al. (Nature, 2022) argued that reproducible
brain-wide association studies need thousands of participants. **0.9% of 2025-26 deposits
clear a thousand.** 13% clear a hundred.

**What this does not claim.** Not every study needs scale: task fMRI asking a within-subject
question is properly powered at thirty, and the benchmark applies to brain-behaviour
correlations specifically. The line is drawn so a reader can see where it sits, not to mark
every mark below it as a failure.

**And the sample is generous, not harsh.** These are studies whose authors chose to deposit,
and consortium projects share at a higher rate than single labs -- which inflates the upper
tail. The flat floor is if anything an understatement.
"""
import hashlib, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate, samplesize                                                 # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "8-samplesize.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
YLO, YHI = 0.8, 14000.0


def jx(did, span):
    h = int(hashlib.md5(did.encode()).hexdigest()[:8], 16)
    return ((h % 10000) / 10000.0 - 0.5) * span


def main():
    rs = samplesize.rows()
    ser = samplesize.by_year(rs)
    er = samplesize.eras(rs)
    tr = samplesize.trend(rs)
    a, b = er[0], er[-1]
    years = [c["year"] for c in ser]

    W, H = 1180, 830
    s = plate.open_svg(
        W, H, "Neuroimaging studies did not get bigger — a few got enormous",
        subtitle=f"{len(rs):,} OpenNeuro MRI datasets by publication year. One dot is one "
                 f"study. The lines are that year's 10th, 50th and 90th percentile.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone judging whether the field answered its own power crisis, or sizing a "
            "study they are about to run",
        decide="whether a typical neuroimaging study is any larger than it was a decade ago",
        wrong="the three percentile lines rise together, which would mean the whole "
              "distribution shifted rather than stretched")
    s += fr

    AX, AY, AW, AH = 250, y0 + 40, 560, 452
    px = lambda i: AX + AW * i / (len(years) - 1)
    ly = lambda v: (AY + AH - AH * (math.log10(min(max(v, YLO), YHI)) - math.log10(YLO))
                    / (math.log10(YHI) - math.log10(YLO)))
    for g in (1, 10, 100, 1000, 10000):
        s.append(f'<line x1="{AX-14:.1f}" y1="{ly(g):.1f}" x2="{AX+AW+14:.1f}" '
                 f'y2="{ly(g):.1f}" stroke="{GRID}"/>')
        s.append(txt(AX - 22, ly(g) + 3, f"{g:,}", size=9.5, fill=MUTED, anchor="end"))
    s.append(f'<text x="{AX-58}" y="{ly(YLO):.1f}" font-size="10" fill="{INK2}" '
             f'transform="rotate(-90 {AX-58} {ly(YLO):.1f})">'
             f'participants in the dataset (log scale)</text>')
    for i, y in enumerate(years):
        s.append(txt(px(i), ly(YLO) + 20, str(y), size=9.5, fill=MUTED, anchor="middle"))
        s.append(txt(px(i), ly(YLO) + 33, str(ser[i]["n"]), size=8.5, fill=FAINT,
                     anchor="middle"))

    # the field's own benchmark, drawn so a reader can see where it sits
    s.append(f'<line x1="{AX-14:.1f}" y1="{ly(samplesize.BENCH):.1f}" '
             f'x2="{AX+AW+14:.1f}" y2="{ly(samplesize.BENCH):.1f}" stroke="{RED}" '
             f'stroke-width="1.4" stroke-dasharray="6 4"/>')
    s += halo(AX - 20, ly(samplesize.BENCH) - 8,
              "brain-wide association studies need thousands (Marek 2022)",
              size=9.5, fill=RED, weight="700")

    sp = AW / len(years) * 0.72
    for r in rs:
        i = years.index(r["yr"]) if r["yr"] in years else None
        if i is None:
            continue
        s.append(f'<circle cx="{px(i) + jx(r["id"], sp):.1f}" cy="{ly(r["subjects"]):.1f}" '
                 f'r="2.6" fill="{SLATE}" fill-opacity="0.34" stroke="{SLATE}" '
                 f'stroke-width="0.5" stroke-opacity="0.4"/>')
    for key, col, lab in (("p90", BLUE, "90th percentile"), ("p50", INK, "median"),
                          ("p10", AMBER, "10th percentile")):
        pts = [(i, c[key]) for i, c in enumerate(ser)]
        s.append('<polyline points="' + " ".join(f"{px(i):.1f},{ly(v):.1f}" for i, v in pts)
                 + f'" fill="none" stroke="{col}" stroke-width="2.6"/>')
        s += halo(px(len(pts) - 1) + 12, ly(pts[-1][1]) + 4, lab, size=10, fill=col,
                  weight="700")

    TX, ty = AX + AW + 124, AY - 12
    fan = [("p10", a["p10"], b["p10"]), ("p25", a["p25"], b["p25"]),
           ("median", a["p50"], b["p50"]), ("p75", a["p75"], b["p75"]),
           ("p90", a["p90"], b["p90"]), ("p99", a["p99"], b["p99"])]
    s.append(txt(TX, ty, f"growth over the decade, by percentile", size=10.5, fill=INK,
                 weight="700"))
    ty += 17
    for lab, v0, v1 in fan:
        col = AMBER if v1 / v0 < 1.3 else (INK if v1 / v0 < 1.8 else BLUE)
        s.append(txt(TX, ty, lab, size=9.5, fill=MUTED))
        s.append(txt(TX + 54, ty, f"{v0} to {v1}", size=9.5, fill=MUTED))
        s += halo(TX + 152, ty, f"{v1/v0:.2f}x", size=10.5, fill=col, anchor="end",
                  weight="700")
        ty += 15
    ty += 10
    for head, body, col in (
            ("it stretched, it did not shift",
             "The growth is monotone in percentile. Whatever changed, it did not reach the "
             "labs at the bottom of this distribution.", INK2),
            ("against the field's own benchmark",
             f"{b['over']:.1%} of {b['era']} deposits clear a thousand participants. "
             f"13% clear a hundred.", RED),
            ("the line is not a pass mark",
             "A within-subject task question is properly powered at thirty. The benchmark "
             "is for brain-behaviour correlations.", MUTED),
            ("the sample flatters the tail",
             "These are studies whose authors chose to share, and consortia share more "
             "readily than single labs.", SLATE)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        w = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=30, leading=12.5)
        s += w
        ty += 12.5 * len(w) + 14

    foot = (
        f"OpenNeuro GraphQL API, no key, fetched 2026-09-24; latestSnapshot.summary.subjects, "
        f"restricted to datasets whose modality resolves to MRI. A year is drawn only where it "
        f"holds at least {samplesize.MIN_N} datasets. Log-linear trend "
        f"{tr['per_decade']:.2f}x per decade, t = {tr['t']:+.2f} on {tr['n']:,} datasets. "
        f"CAVEAT: a deposit archive is not a census of the field, and the 1,000-participant "
        f"benchmark applies to brain-wide association studies rather than to all imaging.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {len(rs):,} MRI datasets, {tr['per_decade']:.2f}x/decade t={tr['t']:+.2f}")
    for lab, v0, v1 in fan:
        print(f"    {lab:<8}{v0:>5} -> {v1:>5}   {v1/v0:.2f}x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
