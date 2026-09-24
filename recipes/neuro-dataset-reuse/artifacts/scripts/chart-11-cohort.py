#!/usr/bin/env python3
"""A brain model trained on this archive would represent a 24-year-old.

    python3 chart-11-cohort.py

One bar is one year of age, which is the granularity the data arrives in -- there is no bin
choice here to carry a story. **52,970 individual people across 945 datasets**, the largest
measurement in this recipe, from a field that had sat unused since the first fetch because it
was assumed to be a [min, max] pair.

**Median age 24. The 18-25 band is 41.9% of everyone ever scanned against roughly 9.5% of the
population: 4.4 times over-represented.** The 41-64 and 65-plus bands each sit at 0.4x. The
people who carry almost all of the neurodegeneration are the ones the archive has least of.

**Not a few big cohorts.** Removing the five largest datasets -- 12% of all people -- moves the
median from 24 to 23 and pushes the 18-30 share *up* to 55.9%. The skew is the archive, not its
outliers.

**It is turning, and recently.** Over-65s are 3.7% of 2024's people, 7.0% of 2025's and
**20.3% of 2026's**. The 2025 jump was 44% a single dataset and collapses to 4.9% without it;
2026's is spread across stroke outcomes, the Precision Aging Network, Michigan Neural
Distinctiveness and two Parkinson's EEG sets, and still reads 16.6% with the largest removed.

**The population line is context, not a matched comparison.** A research corpus owes nobody a
census, and a study of adolescent development should be full of adolescents. The claim is about
what a model trained on the *whole* archive would have seen, which is a fair question to ask of
a whole archive.
"""
import json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cohort, plate                                                     # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "11-cohort.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
AGEHI = 90


def main():
    rs = cohort.rows()
    ppl = cohort.people(rs)
    bd = cohort.bands(ppl)
    rb = cohort.robustness(rs)
    yr = cohort.by_year(rs)
    hist = [sum(1 for a in ppl if int(a) == k) for k in range(AGEHI + 1)]
    mx = max(hist)

    W, H = 1180, 750
    s = plate.open_svg(
        W, H, "A brain model trained on this archive would represent a 24-year-old",
        subtitle=f"{len(ppl):,} individual participants across {len(rs):,} OpenNeuro "
                 f"datasets. One bar is one year of age. The step line is roughly what the "
                 f"population looks like, for scale.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone training or evaluating a model on pooled neuroimaging, or choosing "
            "which population to collect next",
        decide="which ages a model built on this corpus can be expected to know anything "
               "about",
        wrong="the bars follow the population line, so the archive is a fair cross-section")
    s += fr

    AX, AY, AW, AH = 250, y0 + 54, 620, 300
    bx = lambda a: AX + AW * a / AGEHI
    by = lambda v: AY + AH - AH * v / mx
    for a in (0, 18, 25, 40, 65, 90):
        s.append(f'<line x1="{bx(a):.1f}" y1="{AY:.1f}" x2="{bx(a):.1f}" '
                 f'y2="{AY+AH:.1f}" stroke="{GRID}"/>')
        s.append(txt(bx(a), AY + AH + 18, str(a), size=9.5, fill=MUTED, anchor="middle"))
    s.append(txt(AX, AY + AH + 36, "age of the participant, in years", size=10, fill=INK2))
    s.append(txt(AX - 8, AY - 14, "people in the archive at that age", size=10, fill=INK2))
    # a quantitative axis with no ticks is unreadable; label it in round counts
    tick = 10 ** int(math.log10(mx))
    while mx / tick > 5:
        tick *= 2
    v = tick
    while v <= mx:
        s.append(f'<line x1="{AX:.1f}" y1="{by(v):.1f}" x2="{AX+AW:.1f}" '
                 f'y2="{by(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(AX - 8, by(v) + 3, f"{v:,}", size=9, fill=MUTED, anchor="end"))
        v += tick

    w = AW / (AGEHI + 1)
    for k, v in enumerate(hist):
        if not v:
            continue
        col = RED if k >= 65 else (BLUE if 18 <= k <= 30 else SLATE)
        s.append(f'<rect x="{bx(k):.1f}" y="{by(v):.1f}" width="{max(w-0.6,0.8):.1f}" '
                 f'height="{AH - (by(v)-AY):.1f}" fill="{col}" fill-opacity="0.6"/>')

    # the population, as a step over the same bands, scaled to the same head-count
    pts = []
    for lo, hi, lab in cohort.BANDS:
        hi2 = min(hi, AGEHI)
        per = len(ppl) * cohort.POP[lab] / (hi2 - lo + 1)
        pts += [(bx(lo), by(per)), (bx(hi2 + 1), by(per))]
    s.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
             + f'" fill="none" stroke="{INK}" stroke-width="2" stroke-dasharray="5 3"/>')
    s += halo(bx(52), by(len(ppl) * cohort.POP["41-64"] / 24) - 10,
              "what the population looks like", size=10, fill=INK, weight="700")
    peak = max(range(AGEHI + 1), key=lambda k: hist[k])
    s += halo(bx(peak) + 8, by(mx) + 4, f"peak at {peak}: {mx:,} people", size=10,
              fill=BLUE, weight="700")

    RY = AY + AH + 72
    s.append(txt(AX - 8, RY - 12, "how far each band is from the population, and how many "
                                  "people that is", size=10.5, fill=INK, weight="700"))
    cw = AW / len(bd)
    for i, b in enumerate(bd):
        x = AX + i * cw
        rat = b["share"] / b["pop"]
        col = BLUE if rat >= 1.3 else (RED if rat <= 0.6 else SLATE)
        s.append(f'<rect x="{x+8:.1f}" y="{RY:.1f}" width="{cw-16:.1f}" height="30" '
                 f'fill="{col}" fill-opacity="{min(0.55, 0.12+abs(math.log10(rat))*0.5):.2f}" '
                 f'stroke="{col}"/>')
        s += halo(x + cw / 2, RY + 21, f"{rat:.1f}x", size=14, fill=col, anchor="middle",
                  weight="700")
        s.append(txt(x + cw / 2, RY + 46, b["label"], size=9.5, fill=MUTED, anchor="middle"))
        s.append(txt(x + cw / 2, RY + 59, f"{b['n']:,}", size=8.5, fill=FAINT,
                     anchor="middle"))

    TX, ty = AX + AW + 42, AY - 12
    for head, body, col in (
            ("what a pooled model would know",
             f"Ages 18-25 are {bd[2]['share']:.0%} of everyone scanned and about "
             f"{bd[2]['pop']:.0%} of people. Over-65s are {bd[5]['share']:.1%} against "
             f"{bd[5]['pop']:.0%}, and they carry the neurodegeneration.", RED),
            ("not a few big cohorts",
             f"Dropping the five largest datasets, {rb['share_of_people']:.0%} of all "
             f"people, moves the median {rb['with']['median']:.0f} to "
             f"{rb['without']['median']:.0f} and pushes 18-30 up to "
             f"{rb['without']['young']:.0%}.", INK2),
            ("and it is turning",
             f"Over-65s are {yr[-3]['old']:.1%} of 2024's people, {yr[-2]['old']:.1%} of "
             f"2025's and {yr[-1]['old']:.1%} of 2026's — {yr[-1]['old_ex_top']:.1%} even "
             f"without that year's largest.", GREEN),
            ("the line is context, not a target",
             "A corpus owes nobody a census, and a study of adolescent development should "
             "be full of adolescents. The question is what the whole archive represents.",
             MUTED)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        wl = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=30, leading=12.5)
        s += wl
        ty += 12.5 * len(wl) + 14

    foot = (
        f"OpenNeuro GraphQL API, no key, fetched 2026-09-24; metadata.ages, which holds one "
        f"entry per participant rather than a range — {len(rs):,} of 1,891 datasets carry it. "
        f"Population shares are rough OECD figures used for scale only and are not a matched "
        f"comparison. CAVEAT: a participant appearing in two datasets is counted twice, and "
        f"self-reported ages are not verified.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {len(ppl):,} people, median {statistics.median(ppl):.0f}, peak at {peak}")
    for b in bd:
        print(f"    {b['label']:<10}{b['share']:>7.1%}{b['share']/b['pop']:>7.1f}x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
