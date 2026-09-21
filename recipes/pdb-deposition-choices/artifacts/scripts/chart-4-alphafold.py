#!/usr/bin/env python3
"""AlphaFold did not dent experimental deposition, and here is the size of dent it could see.

    python3 chart-4-alphafold.py

AlphaFold DB released in July 2021 and expanded to 214 million predictions in July 2022. The
obvious question is whether people stopped solving structures. The obvious method -- compare
deposition before and after -- answers yes-or-no whichever is true, because the series has
grown for thirty years.

**So the trend comes out first.** Depositions fit a log-linear +5.3% a year over 2005-2020 with
R² 0.96. Extrapolating that fit past 2020 and reading the residuals:

    2021  -4.2%      2023  +0.2%      2025  -10.9%
    2022  +1.4%      2024  +7.3%

**The post-period is the pre-period.** Residuals over 2018-2020 average -1.5% and over
2022-2025 average -0.5%. The series wanders by several per cent either side of its own trend in
both windows, so there is no step to find.

**The null is only worth anything with a size attached.** Pre-AlphaFold residuals span -7.2% to
+5.4%, so a real effect smaller than roughly a tenth of annual deposition would be invisible
here. **This rules out a collapse. It does not rule out a dent.**

**And a second event lands in the same window.** SARS-CoV-2 targets are 7.6% of 2020
depositions, 8.3% of 2022 and 5.1% of 2024. A pandemic added several per cent to exactly the
years AlphaFold is supposed to have subtracted from, so even the raw comparison has two
mechanisms in it pointing opposite ways. Figure 4 is that story on its own.

**One year to watch rather than explain.** 2025 sits 10.9% below trend, the largest miss in the
series. One year is one year; it is drawn and not interpreted.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdb as P, plate                                                   # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "4-alphafold.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
FIT = range(2005, 2021)


def main():
    d = P.load()
    dep = {int(k): v for k, v in d["deposit_by_year"].items()}
    xs = [y for y in FIT]
    ys = [math.log(dep[y]) for y in xs]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    a = my - b * mx
    pred = lambda y: math.exp(a + b * y)
    resid = {y: (dep[y] - pred(y)) / pred(y) for y in range(2005, 2026)}
    pre = [resid[y] for y in FIT]
    band = max(abs(min(pre)), abs(max(pre)))

    W, H = 1200, 850
    s = plate.open_svg(W, H, "AlphaFold did not dent experimental deposition")
    fr, _ = plate.frame(W, 62,
                        who="anyone asking whether prediction displaced experiment",
                        decide="whether to read a post-2021 change as an AlphaFold effect",
                        wrong="post-2021 residuals leave the band the pre-period already "
                              "wandered in")
    s += fr

    # ---- left: the series and its own trend, on a log axis so a constant rate is a line
    AX, AY, AH, AW = 28, 268, 330, 470
    s.append(txt(AX, AY - 56, "depositions per year against their own pre-2021 trend",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(AX, AY - 40, "log scale, so a constant growth rate is a straight line",
                 size=10.5, fill=MUTED))
    yrs = list(range(2005, 2026))
    x0, pw = AX + 46, AW - 76
    px = lambda y: x0 + pw * ((y - yrs[0]) / (yrs[-1] - yrs[0]))
    lo, hi = 4000, 22000
    py = lambda v: (AY + AH - 46 - (AH - 76)
                    * ((math.log10(max(v, lo)) - math.log10(lo))
                       / (math.log10(hi) - math.log10(lo))))
    for v in (5000, 10000, 20000):
        s.append(f'<line x1="{x0:.1f}" y1="{py(v):.1f}" x2="{px(yrs[-1]):.1f}" '
                 f'y2="{py(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(x0 - 7, py(v) + 3, f"{v//1000}k", size=9, fill=MUTED, anchor="end"))
    for y in range(2005, 2026, 5):
        s.append(txt(px(y), AY + AH - 30, str(y), size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, AY + AH - 14, "year the structure was deposited", size=9.5, fill=MUTED))
    for y, lab in ((2021, "AlphaFold DB"), (2022, "214M expansion")):
        s.append(f'<line x1="{px(y):.1f}" y1="{AY-6:.1f}" x2="{px(y):.1f}" '
                 f'y2="{AY+AH-52:.1f}" stroke="{AMBER}" stroke-width="1.4"/>')
        s += halo(px(y) + 4, AY + (0 if y == 2021 else 16), lab, size=8.5, fill=AMBER,
                  weight="700")
    s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{px(y):.1f},{py(pred(y)):.1f}"
                                    for i, y in enumerate(yrs))
             + f'" fill="none" stroke="{INK2}" stroke-width="1.4" stroke-dasharray="4 3"/>')
    s += halo(px(2009), py(pred(2009)) - 10, "+5.3% a year, R² 0.96", size=9, fill=INK2)
    s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{px(y):.1f},{py(dep[y]):.1f}"
                                    for i, y in enumerate(yrs))
             + f'" fill="none" stroke="{BLUE}" stroke-width="2.3"/>')
    s += wrap(AX, AY + AH + 10,
              "The fit is on 2005–2020 only and extended past it as a dashed line. Deposition "
              "keeps to it: 2024 is the busiest year the register has ever had, three years "
              "after the release that was supposed to end the need.",
              size=10.5, fill=INK2, chars=76)

    # ---- right: the residuals, and the size of effect they could have shown
    BX, BY, BH, BW = 590, 268, 330, 470
    s.append(txt(BX, BY - 56, "and the residuals do not move", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(BX, BY - 40, "actual minus trend, as a share of trend", size=10.5, fill=MUTED))
    bx0, bpw = BX + 46, BW - 76
    bpx = lambda y: bx0 + bpw * ((y - yrs[0]) / (yrs[-1] - yrs[0]))
    mid = BY + BH / 2 - 26
    bpy = lambda f: mid - (BH - 90) / 2 * (f / .16)
    s.append(f'<rect x="{bx0:.1f}" y="{bpy(band):.1f}" width="{bpx(yrs[-1])-bx0:.1f}" '
             f'height="{bpy(-band)-bpy(band):.1f}" fill="{SLATE}" fill-opacity="0.14"/>')
    s += halo(bx0 + 6, bpy(band) - 5, f"the band the pre-period already wandered in, ±{band:.0%}",
              size=8.5, fill=INK2, weight="700")
    for f in (-.10, -.05, 0, .05, .10):
        s.append(f'<line x1="{bx0:.1f}" y1="{bpy(f):.1f}" x2="{bpx(yrs[-1]):.1f}" '
                 f'y2="{bpy(f):.1f}" stroke="{INK2 if f == 0 else GRID}" '
                 f'stroke-width="{1.4 if f == 0 else 1}"/>')
        s.append(txt(bx0 - 7, bpy(f) + 3, f"{f*100:+.0f}%" if f else "0", size=9, fill=MUTED,
                     anchor="end"))
    for y in range(2005, 2026, 5):
        s.append(txt(bpx(y), bpy(-.16) + 16, str(y), size=9, fill=MUTED, anchor="middle"))
    s.append(f'<line x1="{bpx(2021):.1f}" y1="{bpy(.16):.1f}" x2="{bpx(2021):.1f}" '
             f'y2="{bpy(-.16):.1f}" stroke="{AMBER}" stroke-width="1.4"/>')
    for y in yrs:
        col = AMBER if y >= 2021 else BLUE
        s.append(f'<line x1="{bpx(y):.1f}" y1="{bpy(0):.1f}" x2="{bpx(y):.1f}" '
                 f'y2="{bpy(resid[y]):.1f}" stroke="{col}" stroke-width="2.4" '
                 f'stroke-opacity="0.6"/>')
        s.append(f'<circle cx="{bpx(y):.1f}" cy="{bpy(resid[y]):.1f}" r="3.4" fill="{col}"/>')
    s += halo(bpx(2025), bpy(resid[2025]) + 14, f"{resid[2025]:+.0%}, one year", size=9,
              fill=AMBER, anchor="middle")
    post = [resid[y] for y in (2022, 2023, 2024, 2025)]
    s += wrap(BX, BY + BH + 10,
              f"Residuals average {sum(resid[y] for y in (2018,2019,2020))/3:+.1%} over "
              f"2018–2020 and {sum(post)/len(post):+.1%} over 2022–2025. The shaded band is the "
              f"range the series already wandered in before AlphaFold existed, ±{band:.0%}. "
              f"An effect smaller than that is invisible here: this rules out a "
              f"collapse, not a dent.",
              size=10.5, fill=INK2, chars=76)

    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"RCSB PDB search API, fetched {d['fetched']}, deposition date. The fit is "
              f"log-linear on 2005–2020 and every point after is out of sample. A second event "
              f"lands in the same window: SARS-CoV-2 targets are 7.6% of 2020 depositions, 8.3% "
              f"of 2022 and 5.1% of 2024, so a pandemic added to exactly the years prediction "
              f"was supposed to subtract from — two mechanisms pointing opposite ways, which is "
              f"why the raw before-and-after comparison is worthless and the detrended one is "
              f"reported with a detectable-effect size instead of a p-value.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    trend {math.exp(b)-1:+.1%}/yr, band ±{band:.1%}, "
          f"post-period mean {sum(post)/len(post):+.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
