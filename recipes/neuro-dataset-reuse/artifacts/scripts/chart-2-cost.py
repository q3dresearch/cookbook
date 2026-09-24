#!/usr/bin/env python3
"""The median NIH-funded dataset on OpenNeuro cost $3.1m and has been downloaded 43 times.

    python3 chart-2-cost.py

86 OpenNeuro datasets name an NIH project number that resolves in RePORTER to a
single-project research grant. That makes the money visible: what the grant behind a shared
dataset was awarded, against how often anyone has taken the data.

**Median award $3.06m. Median $57,010 per download.** The spread is four orders of magnitude,
from **$340** a download to **$4.85m**, which is the point: the question is not what sharing
costs, it is why identical spending produces a thousand-fold difference in reuse.

**Per subject scanned, the median is $92,431** -- and iEEG runs to **$719,129** because
intracranial recording needs a neurosurgical patient and the median dataset has four of them.

**This is an upper bound and nothing here pretends otherwise.** An R01 funds staff, analysis,
publication and students; the deposited dataset is one output among many. The same
overstatement applies to every mark, so the comparison between them holds while the absolute
level does not. A first pass that included CTSAs, program projects and core facilities reached
$1,017.7m -- one of them a $112m award to an entire Clinical and Translational Science
Institute -- and those are excluded because attributing a building to a dataset is not a loose
bound, it is the wrong object.

**Downloads are cumulative and ages differ**, so a 2018 dataset has had longer to earn them.
The diagonals are lines of constant cost per download and are read as position, not as a
model; the age of each dataset is not encoded and that is a real limit of this plate.

**A download is not a citation.** It counts anyone taking the data, including the depositor
and crawlers OpenNeuro's analytics did not filter. As a denominator it flatters the cost.
"""
import math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import costjoin, modality, plate, roi                                         # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "2-cost.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
COL = {"mri": BLUE, "eeg": RED, "ieeg": AMBER, "meg": GREEN, "pet": GREEN,
       "nirs": GREEN, "unknown": SLATE}
XLO, XHI = 1.5e5, 1.6e7          # award
YLO, YHI = 0.7, 2500.0           # cumulative downloads
ISO = (1e3, 1e4, 1e5, 1e6)       # dollars per download


def main():
    _d = roi.decompose()                      # the price/popularity split, computed once
    dec, rr = _d["award_share"], _d["corr"]
    joined = costjoin.rows()
    rs = [r for r in joined if r["downloads"] > 0]
    # A log axis has no room for a zero, and on a cost-per-download plate the zeros are the
    # most expensive marks on it. They get a gutter rather than a silent drop.
    never = sorted((r for r in joined if r["downloads"] == 0), key=lambda r: -r["award"])
    per = sorted(r["per_dl"] for r in rs)
    med_award = statistics.median(r["award"] for r in rs)
    med_dl = statistics.median(r["downloads"] for r in rs)
    med_subj = statistics.median(r["per_subj"] for r in rs if r["per_subj"])

    W, H = 1180, 900
    s = plate.open_svg(
        W, H, f"Reuse does not track spending: across a thousand-fold spread in cost per "
              f"download, the award explains none of it",
        subtitle=f"{len(joined)} datasets naming an NIH project number that resolves to a "
                 f"single-project research grant. Median award ${med_award/1e6:,.1f}m, "
                 f"median {med_dl:,.0f} downloads, median ${statistics.median(per):,.0f} "
                 f"each. {len(never)} zeros sit in the gutter.")
    fr, y0 = plate.frame(
        W, 86,
        who="a programme officer asking what a data-sharing mandate returns, or a PI "
            "deciding how much to spend collecting something they intend to share",
        decide="whether a dataset's cost per download says anything about the money that "
               "made it",
        wrong="the cloud tilts up the page, so bigger grants do buy more reuse")
    s += fr

    AX, AY, AW, AH = 250, y0 + 48, W - 560, 520
    lx = lambda v: AX + AW * (math.log10(min(max(v, XLO), XHI)) - math.log10(XLO)) / (
        math.log10(XHI) - math.log10(XLO))
    ay = lambda v: (AY + AH - 44 - (AH - 70)
                    * (math.log10(min(max(v, YLO), YHI)) - math.log10(YLO))
                    / (math.log10(YHI) - math.log10(YLO)))

    for g, lab in ((2e5, "$200k"), (1e6, "$1m"), (5e6, "$5m"), (1.5e7, "$15m")):
        s.append(f'<line x1="{lx(g):.1f}" y1="{ay(YHI):.1f}" x2="{lx(g):.1f}" '
                 f'y2="{ay(YLO):.1f}" stroke="{GRID}"/>')
        s.append(txt(lx(g), ay(YLO) + 17, lab, size=9, fill=MUTED, anchor="middle"))
    for v in (1, 10, 100, 1000):
        s.append(f'<line x1="{lx(XLO):.1f}" y1="{ay(v):.1f}" x2="{lx(XHI):.1f}" '
                 f'y2="{ay(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(lx(XLO) - 8, ay(v) + 3, f"{v:,}", size=9, fill=MUTED, anchor="end"))
    # iso-cost diagonals: constant award/download is a straight line on log-log
    for c in ISO:
        pts = [(x, x / c) for x in (XLO, XHI) if YLO <= x / c <= YHI * 3]
        if len(pts) < 2:
            xs = [x for x in (XLO * 1.001, XHI * 0.999)]
            pts = [(x, min(max(x / c, YLO), YHI)) for x in xs]
        s.append(f'<line x1="{lx(pts[0][0]):.1f}" y1="{ay(pts[0][1]):.1f}" '
                 f'x2="{lx(pts[1][0]):.1f}" y2="{ay(pts[1][1]):.1f}" stroke="{FAINT}" '
                 f'stroke-width="1" stroke-dasharray="4 4"/>')
        lab = f"${c:,.0f}".replace(",000,000", "m").replace(",000", "k")
        xi = min(XHI * 0.96, max(XLO * 1.1, c * YHI * 0.55))
        s.append(txt(lx(xi), ay(xi / c) - 5, f"{lab} per download", size=8.5, fill=MUTED,
                     anchor="end"))
    # the diagonals are a reference grid, not a model, and a reader has to be told which way
    # is expensive or they read four lines with no meaning
    s += halo(lx(XLO) + 8, ay(YHI * 0.88),
              "each dashed line is one constant cost per download", size=9.5, fill=MUTED,
              weight="700")
    s += halo(lx(XLO) + 8, ay(YHI * 0.88) + 14,
              "further down and right = more money per download", size=9.5, fill=MUTED,
              weight="700")
    # the gutter: zero downloads, drawn at their award but off the vertical scale entirely
    if never:
        gy = ay(YLO) + 52                       # clear of the x tick labels
        s.append(f'<line x1="{AX:.1f}" y1="{gy-15:.1f}" x2="{AX+AW:.1f}" y2="{gy-15:.1f}" '
                 f'stroke="{RED}" stroke-width="1" stroke-dasharray="4 4" '
                 f'stroke-opacity="0.55"/>')
        for r in never:
            c = COL.get(r["mod"], SLATE)
            rad = min(max(3.4, math.sqrt(max(r["subjects"], 1)) * 0.9), 14)
            s.append(f'<circle cx="{lx(r["award"]):.1f}" cy="{gy+4:.1f}" r="{rad:.1f}" '
                     f'fill="{c}" fill-opacity="0.22" stroke="{c}" stroke-width="1.4"/>')
        s += halo(AX - 8, gy + 8, "downloaded 0 times", size=9.5, fill=RED,
                  anchor="end", weight="700")
        s += halo(lx(max(r["award"] for r in never)) + 22, gy + 8,
                  f"${sum(r['award'] for r in never)/1e6:,.1f}m awarded, never taken",
                  size=9.5, fill=RED, weight="700")
        s.append(txt(AX, gy + 40, "total NIH award to the grant named by the dataset  "
                                  "(log scale)", size=10, fill=INK2))
    else:
        s.append(txt(AX, ay(YLO) + 36, "total NIH award to the grant named by the dataset  "
                                       "(log scale)", size=10, fill=INK2))
    s.append(f'<text x="{AX-44}" y="{ay(YLO):.1f}" font-size="10" fill="{INK2}" '
             f'transform="rotate(-90 {AX-44} {ay(YLO):.1f})">'
             f'downloads to date (log scale)</text>')

    for r in sorted(rs, key=lambda r: -r["award"]):
        c = COL.get(r["mod"], SLATE)
        rad = max(3.4, math.sqrt(max(r["subjects"], 1)) * 0.9)
        s.append(f'<circle cx="{lx(r["award"]):.1f}" cy="{ay(r["downloads"]):.1f}" '
                 f'r="{min(rad,14):.1f}" fill="{c}" fill-opacity="0.22" stroke="{c}" '
                 f'stroke-width="1.4"/>')
    best = min(rs, key=lambda r: r["per_dl"])
    worst = max(rs, key=lambda r: r["per_dl"])
    for r, lab, col in ((best, f"{best['id']}  ${best['per_dl']:,.0f} a download", GREEN),
                        (worst, f"{worst['id']}  ${worst['per_dl']/1e6:,.1f}m a download",
                         RED)):
        # flip the label inward past the plot's midpoint, or it runs into the side panel
        right = lx(r["award"]) > AX + AW * 0.55
        s += halo(lx(r["award"]) + (-12 if right else 10), ay(r["downloads"]) + 4, lab,
                  size=9.5, fill=col, weight="700",
                  anchor="end" if right else "start")

    for v, body, col, wt in (
            (3.1, f"median ${statistics.median(per):,.0f} per download", INK, "700"),
            (2.2, f"p10 ${per[len(per)//10]:,.0f}   p90 ${per[-len(per)//10]:,.0f}   "
                  f"-- a thousand-fold spread on similar money", INK2, "normal"),
            (1.55, f"median ${med_subj:,.0f} per subject scanned", INK2, "normal")):
        s.append(txt(lx(1.7e5), ay(v), body, size=9.5, fill=col, weight=wt))

    TX, ty = W - 240, AY + 26
    for head, body, col in (
            ("an upper bound, always",
             "An R01 funds staff, analysis, papers and students; the dataset is one output, "
             "so every mark is overstated by the same kind of amount. Downloads are "
             "cumulative and ages differ, which the diagonals do not know about.", MUTED),
            ("colour", "EEG red, MRI blue, iEEG amber. Circle area is subjects scanned.",
             INK2),
            ("read the diagonals, not the cloud",
             "Each dashed line is a fixed cost per download. The marks cross all four, so "
             "there is no going rate to budget against and an average would be "
             "meaningless.", INK2),
            ("so which axis makes a dataset expensive",
             f"Two thirds of it is the vertical one. The spread splits {dec:.0%} award and "
             f"{1-dec:.0%} downloads, and the two are uncorrelated at r = {rr:+.2f}. A "
             f"dataset is not dear per download because it cost a lot -- it is dear "
             f"because nobody took it.", AMBER),
            ("and you cannot pick the winners",
             "Plate 6 scores every observable predictor of reuse out of sample and the "
             "ceiling is 0.107. Do not read this plate as a ranking a funder could have "
             "applied in advance.", RED),):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        w = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=32, leading=12.5)
        s += w
        ty += 12.5 * len(w) + 16

    fn = costjoin.funnel()
    foot = (
        f"OpenNeuro GraphQL and NIH RePORTER v2, both keyless, fetched 2026-09-24. "
        f"{fn['named']} of {fn['total']:,} datasets name a grant; {fn['parsed']} carry a "
        f"parseable NIH core project number; {fn['joined']} resolve to a "
        f"single-project research grant, {len(rs)} of them with at least one download. "
        "CAVEAT: the award "
        "funds a project, not a dataset, so every figure here is an upper bound -- and three "
        "datasets spell the activity code with a letter O, which the parser rewrites.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {len(rs)} datasets; median award ${med_award:,.0f}, "
          f"median ${statistics.median(per):,.0f} per download")
    print(f"    best {best['id']} ${best['per_dl']:,.0f}   "
          f"worst {worst['id']} ${worst['per_dl']:,.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
