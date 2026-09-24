#!/usr/bin/env python3
"""Nothing observable at deposit forecasts reuse, so cost per download cannot be a funding test.

    python3 chart-6-forecast.py

Cost per download spans a thousand-fold on this archive, from $340 to $4.85m. The obvious
policy reading is to stop funding the expensive end. This plate is why that is not
implementable.

**Two thirds of the spread is the denominator.** `log(award/downloads)` splits exactly into
`log(award) - log(downloads)`, and the two are uncorrelated, so the variances add: the award
contributes **31%** and the download count **69%**. A dataset is not expensive per download
because it was expensive. It is expensive per download because nobody took it.

**And the download count is very nearly unforecastable.** Every model on this plate is scored
twice -- once on the data it was fitted to, once on data held out by ten-fold
cross-validation. The gap between the two positions **is** the finding. On 86 funded datasets
"everything observable" reaches 0.193 in sample and **-0.069 held out**: worse than predicting
the mean. That is not a weak model, it is no model, and the in-sample figure was counting
columns.

**The honest ceiling is 0.107**, on the full 1,429-dataset archive where there are enough rows
to fit anything. So at the moment of the funding decision, **39% of the eventual cost per
download is knowable** -- the 31% that is the award, plus about a tenth of the rest -- and
**61% is a coin flip**.

**Which leaves one real lever and it is not a budget lever.** Holding subject count fixed,
every modality beats MRI, from MEG at 1.18x to PET at 2.53x, and MRI is 66% of the archive.
Scale is nearly worthless: the slope of downloads on subjects is +0.22, so doubling a cohort
returns about 16% more downloads. A lab does not choose its modality for reuse reasons, so
this describes a crowded market rather than prescribing an escape from it.
"""
import math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import modality, plate, roi                                              # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "6-forecast.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
XLO, XHI = -0.12, 0.26


def main():
    dec = roi.decompose()
    sc = roi.scaling()
    fu = roi.score(roi.funded(), roi.SETS_FUNDED)
    ar = roi.score(roi.archive(), roi.SETS_ALL)
    ceiling = max(s["heldout"] for s in ar)
    known = dec["award_share"] + dec["download_share"] * ceiling

    W, H = 1180, 780
    s = plate.open_svg(
        W, H, "Nothing you can see at deposit forecasts reuse, so cost per download cannot "
              "be a funding test",
        subtitle="Each row is a set of things a depositor knows on the day they publish. "
                 "The hollow mark is how well it fits its own data; the solid mark is how "
                 "well it predicts data held out. The gap is the answer.")
    fr, y0 = plate.frame(
        W, 86,
        who="a programme officer asked to screen proposals on expected reuse, or anyone "
            "about to rank datasets by cost per download",
        decide="whether the expensive-per-download dataset can be identified in advance",
        wrong="a held-out score rises above about 0.15, or the hollow and solid marks "
              "sit on top of each other")
    s += fr

    AX, AY, AW = 372, y0 + 60, 470
    lx = lambda v: AX + AW * (v - XLO) / (XHI - XLO)
    rows = ([("FUNDED DATASETS   n = %d" % fu[0]["n"], None)]
            + [(f["label"], f) for f in fu]
            + [("THE WHOLE ARCHIVE   n = %d" % ar[0]["n"], None)]
            + [(a["label"], a) for a in ar])
    RH = 30
    for g in (-0.1, 0.0, 0.1, 0.2):
        x = lx(g)
        s.append(f'<line x1="{x:.1f}" y1="{AY-14:.1f}" x2="{x:.1f}" '
                 f'y2="{AY + len(rows)*RH - 6:.1f}" '
                 f'stroke="{INK2 if g == 0 else GRID}" '
                 f'stroke-width="{1.4 if g == 0 else 1}"/>')
        s.append(txt(x, AY - 22, f"{g:+.1f}" if g else "0", size=9, fill=MUTED,
                     anchor="middle"))
    s += halo(lx(0.0), AY + len(rows) * RH + 12, "predicts nothing", size=9.5, fill=INK2,
              anchor="middle", weight="700")
    s.append(txt(AX + AW, AY - 38, "share of the variation in reuse explained  (R2)",
                 size=10, fill=INK2, anchor="end"))

    y = AY
    for lab, r in rows:
        if r is None:
            s.append(txt(34, y + 4, lab, size=10, fill=INK, weight="700", spacing="0.08em"))
            y += RH
            continue
        col = RED if r["heldout"] < 0.02 else (AMBER if r["heldout"] < 0.09 else GREEN)
        s.append(txt(AX - 16, y + 4, lab, size=10.5, fill=INK2, anchor="end"))
        x1, x2 = lx(r["insample"]), lx(r["heldout"])
        s.append(f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" '
                 f'stroke="{col}" stroke-width="2" stroke-opacity="0.45"/>')
        s.append(f'<circle cx="{x1:.1f}" cy="{y:.1f}" r="5" fill="none" stroke="{col}" '
                 f'stroke-width="1.6"/>')
        s.append(f'<circle cx="{x2:.1f}" cy="{y:.1f}" r="5" fill="{col}"/>')
        s += halo(x2 + (-11 if r["heldout"] < r["insample"] else 11), y + 4,
                  f"{r['heldout']:+.3f}", size=9.5, fill=col,
                  anchor="end" if r["heldout"] < r["insample"] else "start", weight="700")
        y += RH
    s += halo(lx(fu[-1]["insample"]) + 10, AY + 4 * RH + 4,
              "fitted to its own data", size=9, fill=MUTED, weight="700")

    BY = AY + len(rows) * RH + 48
    s.append(f'<line x1="34" y1="{BY-16:.1f}" x2="{W-300:.1f}" y2="{BY-16:.1f}" '
             f'stroke="{RULE}"/>')
    s.append(txt(34, BY + 2, "so what is knowable on the day the money is committed",
                 size=11, fill=INK, weight="700"))
    BX, BW, BH = 34, W - 340, 30
    seg = ((dec["award_share"], GREEN, "the award, known exactly"),
           (dec["download_share"] * ceiling, AMBER, "forecastable reuse"),
           (dec["download_share"] * (1 - ceiling), RED, "a coin flip"))
    x = BX
    for frac, col, lab in seg:
        s.append(f'<rect x="{x:.1f}" y="{BY+14:.1f}" width="{BW*frac:.1f}" height="{BH}" '
                 f'fill="{col}" fill-opacity="0.5" stroke="{col}" stroke-width="1"/>')
        s += halo(x + BW * frac / 2, BY + 34, f"{frac:.0%}", size=12, fill=col,
                  anchor="middle", weight="700")
        s.append(txt(x + BW * frac / 2, BY + 60, lab, size=9.5, fill=MUTED,
                     anchor="middle"))
        x += BW * frac

    TX, ty = W - 268, AY - 30
    for head, body, col in (
            ("if you are told to fund on expected reuse",
             f"You cannot. At the decision, {1-known:.0%} of the eventual cost per download "
             f"is undetermined by anything on the application. The $340 dataset and the "
             f"$4.85m one look the same.", RED),
            ("if you are tempted by an in-sample fit",
             "Every hollow mark is a model flattering itself. On 86 rows, 'everything "
             "observable' explains 19% of its own data and less than nothing of anyone "
             "else's.", AMBER),
            ("what the money actually buys",
             f"Not reuse. Award against downloads is r = {dec['corr']:+.2f}, t = "
             f"{dec['t']:+.2f}. A bigger grant does not produce a more-taken dataset.",
             SLATE),
            ("the one lever, and it is not financial",
             f"Holding subject count fixed, every modality beats MRI -- "
             f"{modality.NICE.get(sc['mods'][0]['mod'], '')} by "
             f"{sc['mods'][0]['observed']/sc['mods'][0]['size_says']:.2f}x -- and MRI is "
             f"{sc['mods'][-1]['n']/sc['n']:.0%} of the archive. Scale is not a lever: "
             f"doubling a cohort returns {sc['per_2x']-1:.0%}.", BLUE),
            ("what would change this",
             "A predictor nobody has tried: the task or paradigm. It is the field most "
             "likely to carry demand and OpenNeuro does not record it in countable form.",
             MUTED)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        w = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=32, leading=12.5)
        s += w
        ty += 12.5 * len(w) + 14

    foot = (
        f"OpenNeuro GraphQL and NIH RePORTER v2, both keyless, fetched 2026-09-24. Target is "
        f"log10 downloads per year since publication, which removes the age confound in a "
        f"cumulative count. Held-out R2 from ten-fold cross-validation, seeded. The variance "
        f"split is exact in log units because award and downloads are uncorrelated. CAVEAT: "
        f"a download is not a citation, and 'everything observable' is only everything "
        f"OpenNeuro records.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    ceiling {ceiling:.3f}, knowable {known:.0%}, coin flip {1-known:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
