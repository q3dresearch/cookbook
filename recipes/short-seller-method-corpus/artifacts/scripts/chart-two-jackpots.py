#!/usr/bin/env python3
"""Crime does not slope with size. Broken economics is almost entirely size.

    python chart-two-jackpots.py

Two things are worth proving about a company: that a crime is happening, or that its
unit economics do not work. Both are checkable from SEC filings alone. Plotted against
market cap, with every company shown and a logistic fit through them, the two behave
in opposite ways -- and that contrast is the finding.

    outcome ~ log10(public float)        slope per 10x        verdict
    crime, targets                       +0.06  +/- 0.31      flat
    crime, controls                      +0.48  +/- 0.27      flat
    broken economics, targets            -2.21  +/- 0.61      resolved, steep
    broken economics, controls           -0.95  +/- 0.41      resolved

**Crime is flat in size for both groups.** A company's chance of disclosing a Wells
notice, grand jury, subpoena or formal order does not move measurably across a
thousandfold range of market value -- but the target curve sits above the control
curve across that whole range. Being targeted raises it; being large does not.

**Broken economics is a size curve.** Both groups fall steeply and the two curves run
close together. A small company fails to cover its overhead or burns cash almost
always, whether or not anybody shorted it.

**This replaced a three-band version, and the bands were inviting a wrong reading.**
Grouped into non-accelerated / accelerated / large accelerated, the target crime rate
read 21%, 9%, 28% -- a U-shape a reader will see and believe. The middle band was
eleven companies. The fitted slope says there is no shape there at all: +0.06 with a
standard error of 0.31. Bands turn sampling noise into a picture of a mechanism.

**Why no spline.** The honest limit is the event count, not the axis. Ten crime events
among targets and five among controls; at the usual ten-events-per-parameter this
supports about one parameter, and the chart already spends two. A three-knot spline
would be fitting four parameters to five events, and it would draw a confident wiggle
every time.

**Why public float and not total assets.** Assets covers more companies and is unusable
for this. It is reported in the filer's own currency -- Nomura enters the data at 62.6
trillion, which is yen -- and for a bank it is the loan book, so Bank of America
outweighs every industrial in the corpus by two orders of magnitude. `EntityPublicFloat`
is a US regulatory disclosure, always USD, always market value. It costs coverage:
foreign private issuers do not file it, which is 21 of 76 targets. The same fits run on
assets give the same signs and the same verdicts, so the conclusion survives the swap
even though the axis does not.

**One caution on the crime panel that does not go away.** A short report can cause the
investigation it appears to predict -- regulators read these, and a public allegation
is itself a reason to open a file. Nothing here separates "found a company already
under investigation" from "caused one". That needs the date a file was opened, which
is not public.
"""
import json, math, random, sys
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import palette
from jackpot import broken, enforced, enforced_at
from selection import logistic

RAW = HERE.parent / "raw"
OUT = HERE.parent / "charts" / "two-jackpots.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
RULE = "#ebeae3"
HOT, COOL = "#b03a2e", "#1b4f8a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
W, H = 960, 660
LO, HI = 6.0, 11.5          # $1m to $316bn of public float
TICKS = [(6, "$1m"), (7, "$10m"), (8, "$100m"), (9, "$1bn"), (10, "$10bn"), (11, "$100bn")]


def txt(x, y, s, *, size, fill, anchor="start", weight="normal", tab=False):
    st = "font-variant-numeric: tabular-nums;" if tab else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family=\'{FONT}\' font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
            f'style="{st}">{escape(s)}</text>')


def para(x, y, s, *, size, fill, chars, leading=17.0):
    words, line, out, n = s.split(), [], [], 0
    for w in words:
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
            line, n = [], n + 1
        line.append(w)
    if line:
        out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
        n += 1
    return out, n * leading


def observations(items, floats, outcome):
    out = []
    for k, v in items.items():
        f = floats.get(k, {})
        o = outcome(v)
        if f.get("status") == "ok" and f["float"] > 0 and o is not None:
            out.append((math.log10(f["float"]), int(o)))
    return out


def main():
    T = json.loads((RAW / "jackpot_targets.json").read_text())
    C = json.loads((RAW / "jackpot_controls.json").read_text())
    FT = json.loads((RAW / "float_targets.json").read_text())
    FC = json.loads((RAW / "float_controls.json").read_text())
    dates = sorted(v["as_of"] for v in T.values())

    def build(axis):
        rnd = random.Random(20260912)
        if axis == "crime":
            t = observations(T, FT, lambda v: enforced(v))
            c = observations(C, FC, lambda v: enforced_at(v, rnd.choice(dates)))
        else:
            t = observations(T, FT, lambda v: broken(v["economics"]))
            c = observations(C, FC, lambda v: broken(v["economics"]))
        return t, c

    panels = [("A crime is being investigated",
               "disclosed a Wells notice, grand jury, subpoena or formal order within 3 years",
               *build("crime")),
              ("The business does not work",
               "does not cover its overhead, or burns cash, at the last annual before the report",
               *build("economics"))]

    L, R, GAP, TOP = 78, 30, 50, 196
    pw = (W - L - R - GAP) / 2
    ph = 250
    RUG = 13

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    s.append(txt(L, 44, "Crime does not slope with size. Broken economics is almost entirely size.",
                 size=20, fill=INK, weight="600"))
    body, _ = para(L, 72, "Every company plotted at its public float, with a logistic fit and its 95% "
                   "band. Ticks along the top are companies where it happened, along the bottom where "
                   "it did not.", size=13, fill=INK2, chars=112)
    s += body
    for i, (lab, col) in enumerate((("targets", HOT), ("controls", COOL))):
        lx = W - R - 200 + i * 104
        s.append(f'<circle cx="{lx + 5:.1f}" cy="68" r="5.5" fill="{col}"/>')
        s.append(txt(lx + 16, 72, lab, size=12, fill=INK2))

    for pi, (title, sub, tobs, cobs) in enumerate(panels):
        x0 = L + pi * (pw + GAP)
        sx = lambda v: x0 + (v - LO) / (HI - LO) * pw
        sy = lambda v: TOP + ph - v * ph
        s.append(txt(x0, TOP - 66, title, size=14, fill=INK, weight="600"))
        sw, _ = para(x0, TOP - 48, sub, size=11, fill=MUTED, chars=int(pw / 5.6), leading=13)
        s += sw
        for g in (0, 0.25, 0.5, 0.75, 1.0):
            y = sy(g)
            s.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + pw:.1f}" y2="{y:.1f}" '
                     f'stroke="{RULE}" stroke-width="1"/>')
            if pi == 0:
                s.append(txt(x0 - 10, y + 4, f"{g:.0%}", size=11, fill=MUTED, anchor="end", tab=True))
        # The rug's two rows ARE the y-value: a company sits at the top if the thing
        # happened to it and at the bottom if it did not. Clustered into one row they
        # would show only which sizes exist, and the fitted curve would be the sole
        # evidence on screen. Labelled at the edge because a caption alone let a reader
        # take them for decoration.
        if pi == 0:
            s.append(txt(x0 - 12, TOP - 9, "happened", size=9.5, fill=MUTED, anchor="end"))
            s.append(txt(x0 - 12, TOP + ph + 21, "did not", size=9.5, fill=MUTED, anchor="end"))
        for v, lab in TICKS:
            s.append(txt(sx(v), TOP + ph + RUG + 34, lab, size=11, fill=MUTED,
                         anchor="middle", tab=True))
        s.append(txt(x0 + pw / 2, TOP + ph + RUG + 56, "public float at the report",
                     size=11.5, fill=INK2, anchor="middle"))

        for obs, col, lane in ((cobs, COOL, 1), (tobs, HOT, 0)):
            # Rug: each company as a tick, events above the plot and non-events below,
            # one lane per series so the two groups never sit on the same pixel row.
            for xv, yv in obs:
                yy = (TOP - 8 - lane * 6) if yv else (TOP + ph + 8 + lane * 6)
                # Two control shells sit at $127k and $265k of float, below the axis
                # floor. Drawn at their true x they landed on the row label outside the
                # panel. They clamp to the edge at half opacity rather than extending
                # the axis a whole decade for two points -- the FIT still uses their
                # real values, only the tick moves.
                off = xv < LO or xv > HI
                px = sx(min(HI, max(LO, xv)))
                s.append(f'<line x1="{px:.1f}" y1="{yy:.1f}" x2="{px:.1f}" '
                         f'y2="{yy + (-5 if yv else 5):.1f}" stroke="{col}" stroke-width="1.6" '
                         f'stroke-opacity="{0.35 if off else 0.75}"/>')

            fit = logistic([a for a, _ in obs], [b for _, b in obs])
            if fit is None:
                continue
            b, cov = fit
            xs = np.linspace(LO, HI, 120)
            X = np.column_stack([np.ones(len(xs)), xs])
            eta = X @ b
            se = np.sqrt(np.einsum("ij,jk,ik->i", X, cov, X))
            mid = 1 / (1 + np.exp(-eta))
            lo = 1 / (1 + np.exp(-(eta - 1.96 * se)))
            hi = 1 / (1 + np.exp(-(eta + 1.96 * se)))
            band = ([f"{sx(x):.1f},{sy(v):.1f}" for x, v in zip(xs, hi)] +
                    [f"{sx(x):.1f},{sy(v):.1f}" for x, v in zip(xs[::-1], lo[::-1])])
            n, ev = len(obs), sum(v for _, v in obs)
            slope = b[1]
            se_s = math.sqrt(cov[1, 1])
            resolved = abs(slope / se_s) >= 1.96
            verdict = "slopes" if resolved else "no resolvable slope"
            s.append(f'<polygon points="{" ".join(band)}" fill="{col}" fill-opacity="0.11"/>')
            # A solid line asserts a trend. Where the slope cannot be told from zero the
            # line is dashed, because the fit still bends -- the control crime curve
            # climbs to 60% on five events that all sit between $800m and $16bn, with
            # none above or below -- and a reader reads the line, not the band.
            s.append(f'<polyline points="{" ".join(f"{sx(x):.1f},{sy(v):.1f}" for x, v in zip(xs, mid))}" '
                     f'fill="none" stroke="{col}" stroke-width="2.2"'
                     f'{"" if resolved else chr(32) + chr(115) + "troke-dasharray=\"6 4\" stroke-opacity=\"0.75\""}/>')
            # Below the axis, not inside the plot: at the top-left of the economics
            # panel this text landed directly on the curve, which is at 100% there.
            s.append(txt(x0, TOP + ph + RUG + 76 + lane * 16,
                         f"{'targets ' if lane == 0 else 'controls'}  n={n}, {ev} events   "
                         f"slope {slope:+.2f} ±{se_s:.2f}   {verdict}",
                         size=11, fill=col, tab=True))

    fy = TOP + ph + RUG + 138
    s.append(f'<line x1="{L}" y1="{fy - 22}" x2="{W - R}" y2="{fy - 22}" stroke="{RULE}" stroke-width="1"/>')
    foot, _ = para(L, fy, "Slope is the change in log-odds per 10× of market value; dashed means it "
                   "cannot be told from zero, so read the ticks rather than the line. On crime neither "
                   "slope resolves and targets carry 10 events in 39 against 5 in 45 — and every "
                   "control event sits between $800m and $16bn while target events span the whole "
                   "range. Both economics slopes are steeply negative and the curves run together: "
                   "that axis is measuring size.",
                   size=12, fill=INK2, chars=116)
    s += foot
    s.append("</svg>")
    OUT.write_text("\n".join(s))
    for title, _, tobs, cobs in panels:
        print(f"  {title}")
        for lab, obs in (("targets", tobs), ("controls", cobs)):
            fit = logistic([a for a, _ in obs], [b for _, b in obs])
            if not fit:
                print(f"    {lab:<10} n={len(obs)} will not fit"); continue
            b, cov = fit
            print(f"    {lab:<10} n={len(obs):<4} events={sum(v for _, v in obs):<3} "
                  f"slope={b[1]:+.2f} ±{math.sqrt(cov[1,1]):.2f}")


if __name__ == "__main__":
    main()
