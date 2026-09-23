#!/usr/bin/env python3
"""PJM's flat-load signature is ordinary once you only compare it to grids its own size.

    python3 chart-4-size.py

Figure 3 found PJM's overnight trough growing **3.2 points faster than its afternoon peak**
between 2019 and 2025 -- the signature a flat 24/7 data centre load has to leave, and worth
about 10 GW of implied load. This figure asks the only question that matters next: **is 3.2
points unusual?**

**No. Among the eight US grids peaking above 20 GW the same number runs from -5.1 to +5.8**,
and PJM's +3.2 is the fourth largest in absolute value, behind California's +5.8, Southern's
-5.1 and Florida Power & Light's +5.0. Handed the number without the name of the grid, nobody
picks PJM out of that row.

**And the largest values in the country belong to grids nobody is siting compute in.** WALC at
-27.2 points and Tucson at +23.0 are 1.4 GW and 1.9 GW -- small enough for one industrial
customer or one metering change to move the entire figure.

**One row per size band, because that is the comparison.** The spread collapses from **28.9
points across the smallest band to 11.0 across the largest**, and a chart that mixed the bands
together would let a 1.4 GW grid argue about a 105 GW one. It is not a clean "small is noisy"
story either -- the 6-to-20 GW band is tighter than the band above it, at 7.3 points -- which
is why the bands are drawn rather than a trend line through them.

**What this closes.** Neither PeeringDB facility counts (r = +0.03 against state electricity
growth) nor hourly load shape isolates where compute load has landed. What predicted growth
was electricity per head at Pearson +0.64: how electrified a place already was, not what it
attracted. Compute does turn up later, in figure 8, and only as a predictor of how hard a grid
is to forecast.
"""
import math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate, shape                                                      # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "4-size.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
BANDS = [(20.0, 1e9, "above 20 GW", "the grids where the compute actually is"),
         (6.0, 20.0, "6 to 20 GW", ""),
         (2.5, 6.0, "2.5 to 6 GW", ""),
         (1.0, 2.5, "1 to 2.5 GW", "one customer moves the whole number")]
NAME = {"PJM": ("PJM", False), "CISO": ("California", True), "SOCO": ("Southern", True),
        "TEPC": ("Tucson", True), "WALC": ("WALC", False), "WACM": ("WACM", True),
        "AZPS": ("Phoenix", False)}
XLO, XHI = -0.30, 0.26


def main():
    rows = shape.rows()
    bands = []
    for lo, hi, lab, note in BANDS:
        g = sorted((r for r in rows if lo <= r["peak_gw"] < hi), key=lambda r: r["gap"])
        if g:
            bands.append((lab, note, g))
    big = [r for r in rows if r["peak_gw"] >= 20]
    blo, bhi = min(r["gap"] for r in big), max(r["gap"] for r in big)
    pjm = next(r for r in rows if r["ba"] == "PJM")
    rank = sorted(big, key=lambda r: -abs(r["gap"])).index(pjm) + 1

    W = 1150
    H = 268 + 108 * len(bands) + 118
    s = plate.open_svg(
        W, H, "PJM's flat-load signature is ordinary next to grids its own size",
        subtitle=f"The figure 3 gap -- how much faster the overnight trough grew than the "
                 f"afternoon peak, 2019 to 2025 -- with one row per size band. Each mark is "
                 f"one of the {len(rows)} US grids above 1 GW.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone about to read a trough-versus-peak gap as evidence of data centre load",
        decide="whether PJM's +3.2 points is distinctive enough to act on",
        wrong="the big grids sit outside the range the smaller ones occupy")
    s += fr

    AX, AW = 236, W - 420
    lx = lambda v: AX + AW * (min(max(v, XLO), XHI) - XLO) / (XHI - XLO)
    top = y0 + 76
    bot = top + 108 * len(bands) - 34
    for g in (-0.30, -0.20, -0.10, 0.0, 0.10, 0.20):
        zero = abs(g) < 1e-9
        s.append(f'<line x1="{lx(g):.1f}" y1="{top-30:.1f}" x2="{lx(g):.1f}" '
                 f'y2="{bot:.1f}" stroke="{RULE if zero else GRID}" '
                 f'stroke-width="{1.5 if zero else 1}"/>')
        s.append(txt(lx(g), top - 38, f"{g*100:+.0f}" if not zero else "0", size=9,
                     fill=MUTED, anchor="middle"))
    s.append(txt(AX - 4, top - 56, "trough grew FASTER than peak, in percentage points  "
                                   "-- a data centre pushes a grid to the right",
                 size=10, fill=INK2))

    for i, (lab, note, g) in enumerate(bands):
        y = top + 108 * i + 24
        vals = [r["gap"] for r in g]
        span = (max(vals) - min(vals)) * 100
        med = statistics.median(vals)
        s.append(txt(AX - 20, y - 2, lab, size=11.5, fill=INK, anchor="end", weight="600"))
        s.append(txt(AX - 20, y + 13, f"{len(g)} grids", size=9.5, fill=MUTED,
                     anchor="end"))
        if note:
            s.append(txt(AX - 20, y + 27, note, size=9, fill=MUTED, anchor="end"))
        # the band's own span, drawn as the thing that shrinks
        s.append(f'<line x1="{lx(min(vals)):.1f}" y1="{y:.1f}" x2="{lx(max(vals)):.1f}" '
                 f'y2="{y:.1f}" stroke="{FAINT}" stroke-width="7" stroke-opacity="0.35"/>')
        s.append(f'<line x1="{lx(med):.1f}" y1="{y-11:.1f}" x2="{lx(med):.1f}" '
                 f'y2="{y+11:.1f}" stroke="{INK2}" stroke-width="2"/>')
        for r in g:
            subject = r["ba"] == "PJM"
            col = RED if subject else (BLUE if r["peak_gw"] >= 20 else SLATE)
            s.append(f'<circle cx="{lx(r["gap"]):.1f}" cy="{y:.1f}" '
                     f'r="{7.4 if subject else 5.2:.1f}" fill="{col}" '
                     f'fill-opacity="{0.42 if subject else 0.26}" stroke="{col}" '
                     f'stroke-width="{2.2 if subject else 1.4}"/>')
            if r["ba"] in NAME:
                nm, up = NAME[r["ba"]]
                s += halo(lx(r["gap"]), y + (-13 if up else 21), nm, size=9.5,
                          fill=col, anchor="middle", weight="700")
        s.append(txt(W - 166, y - 2, f"{span:.0f} pts", size=11, fill=INK2, weight="700"))
        s.append(txt(W - 166, y + 13, "wide", size=9, fill=MUTED))

    s += halo(AX - 20 - 190, bot + 30,
              f"the eight largest grids all sit between {blo*100:+.1f} and {bhi*100:+.1f} "
              f"points, and PJM is the {rank}th largest of them in absolute value",
              size=10.5, fill=BLUE, weight="700")
    s += halo(AX - 20 - 190, bot + 45,
              "so the signature is real and it is not distinctive -- which is what closes "
              "the question rather than answering it", size=10.5, fill=INK2)

    foot = (
        "EIA Hourly Electric Grid Monitor (EBA) bulk file, no key, fetched 2026-09-23. "
        "Trough and peak are the median daily minimum and maximum of local-time hourly "
        "demand; the grey bar is each band's full span and the tick its median. CAVEAT: the "
        "fourteen EIA region codes are aggregates of the balancing authorities beside them "
        "and are excluded, or CAL would be drawn against CISO, which it contains.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=172, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=172, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for lab, _, g in bands:
        v = [r["gap"] for r in g]
        print(f"    {lab:<14}n={len(g):>3}  span {(max(v)-min(v))*100:>5.1f} pts  "
              f"median {statistics.median(v)*100:>+5.1f}")
    print(f"    the {len(big)} above 20 GW span {blo:+.1%} to {bhi:+.1%}; "
          f"PJM is {rank} of {len(big)} by absolute value")
    return 0


if __name__ == "__main__":
    sys.exit(main())
