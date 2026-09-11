#!/usr/bin/env python3
"""They find crimes. Broken businesses, not quite.

    python chart-two-jackpots.py

Two things are worth proving about a company: that a crime is happening, or that its
unit economics do not work. Both are checkable from SEC filings alone, which is what
makes them reachable without sources. Measured against 139 control filers, the firms
in this corpus are good at one and barely distinguishable at the other.

    disclosed an investigation in 3 years   22% vs 6%    4.0x   p = 0.002
    does not cover overhead or burns cash   49% vs 33%   1.5x   p = 0.09

**The intervals carry the argument, which is why they are drawn.** On the crime axis
they do not come close to touching. On the economics axis they overlap across most of
their range, and a reader who only saw the two dots would take a 1.5x lift for a
result.

**And the economics lean is mostly composition.** Split by filer size class it nearly
vanishes: 31% vs 20% among large accelerated filers, 85% vs 79% among everything
smaller. Small companies fail to cover their overhead about four times in five whether
or not anybody shorts them. Targets skew large, controls skew small, and most of the
pooled gap is that mix rather than any difference in how broken the companies are.

**Exposure is matched on the crime axis, because it decides the result.** A target
attacked in 2014 has twelve years in which to disclose an investigation; one attacked
in 2025 has months. Each control is given a report date drawn from the target
distribution, every company is scored on a fixed three-year window, and any company
whose window has not closed is dropped rather than counted as a no. Counting "ever
disclosed afterwards" instead inflates the target rate against controls that were all
measured from a single cutoff.

**One caution belongs with the 4.0x and does not go away.** A short report can cause
the investigation it appears to predict — regulators read these, and a public
allegation is itself a reason to open a file. Nothing here separates "found a company
already under investigation" from "caused one", and the two mean completely different
things for anyone trying to do the same work. Separating them needs the date a file
was opened, which is not public.
"""
import json, random, sys
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import palette
from jackpot import broken, enforced, enforced_at
from selection import fisher, wilson

RAW = HERE.parent / "raw"
OUT = HERE.parent / "charts" / "two-jackpots.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
RULE = "#ebeae3"
HOT, COOL = "#b03a2e", "#1b4f8a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
W, H = 940, 500
AXIS_MAX = 0.85


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


def main():
    T = json.loads((RAW / "jackpot_targets.json").read_text())
    C = json.loads((RAW / "jackpot_controls.json").read_text())

    dates = sorted(v["as_of"] for v in T.values())
    rnd = random.Random(20260912)
    te = [x for x in (enforced(v) for v in T.values()) if x is not None]
    ce = [x for x in (enforced_at(v, rnd.choice(dates)) for v in C.values()) if x is not None]
    tb = [x for x in (broken(v["economics"]) for v in T.values()) if x is not None]
    cb = [x for x in (broken(v["economics"]) for v in C.values()) if x is not None]

    axes = [
        ("A crime is being investigated",
         "disclosed a Wells notice, grand jury, subpoena or formal order within 3 years",
         sum(te), len(te), sum(ce), len(ce)),
        ("The business does not work",
         "does not cover its overhead, or burns cash, at the last annual before the report",
         sum(tb), len(tb), sum(cb), len(cb)),
    ]

    # The value label sits past the right end of the interval, so the axis needs headroom
    # beyond the widest upper bound (61%) or the label runs off the page. The verdict
    # goes in the left column for the same reason -- right-aligned at the edge it
    # collided with that label.
    L, R, TOP, COL = 46, 46, 168, 236
    pw = W - L - R - COL - 96
    sx = lambda v: L + COL + v / AXIS_MAX * pw

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    s.append(txt(L, 46, "They find crimes. Broken businesses, not quite.",
                 size=22, fill=INK, weight="600"))
    body, _ = para(L, 74, "Short-seller targets against 139 filers nobody attacked. Bars are 95% "
                   "intervals — where they overlap, the gap is not a finding.",
                   size=13, fill=INK2, chars=100)
    s += body

    # Legend: two series, so identity is never carried by colour alone.
    for i, (lab, col) in enumerate((("targets", HOT), ("controls", COOL))):
        lx = L + COL + i * 110
        s.append(f'<circle cx="{lx + 5:.1f}" cy="{TOP - 34}" r="5.5" fill="{col}"/>')
        s.append(txt(lx + 16, TOP - 30, lab, size=12, fill=INK2))

    for v in (0, 0.2, 0.4, 0.6, 0.8):
        x = sx(v)
        s.append(f'<line x1="{x:.1f}" y1="{TOP - 12}" x2="{x:.1f}" y2="{TOP + 176}" '
                 f'stroke="{RULE}" stroke-width="1"/>')
        s.append(txt(x, TOP + 196, f"{v:.0%}", size=11, fill=MUTED, anchor="middle", tab=True))

    for i, (title, sub, a, na, c, nc) in enumerate(axes):
        y = TOP + 30 + i * 96
        s.append(txt(L, y - 6, title, size=14, fill=INK, weight="600"))
        sw, sh = para(L, y + 13, sub, size=11, fill=MUTED, chars=32, leading=14)
        s += sw
        for k, n, col, dy in ((a, na, HOT, 0), (c, nc, COOL, 30)):
            lo, hi = wilson(k, n)
            yy = y + dy
            s.append(f'<line x1="{sx(lo):.1f}" y1="{yy:.1f}" x2="{sx(hi):.1f}" y2="{yy:.1f}" '
                     f'stroke="{col}" stroke-width="3" stroke-opacity="0.35" stroke-linecap="round"/>')
            s.append(f'<circle cx="{sx(k / n):.1f}" cy="{yy:.1f}" r="6.5" fill="{col}" '
                     f'stroke="{SURFACE}" stroke-width="2"/>')
            s.append(txt(sx(hi) + 14, yy + 4, f"{k/n:.0%}   {k}/{n}", size=12, fill=col,
                         weight="600", tab=True))
        p = fisher(a, na - a, c, nc - c)
        strong = p < 0.01
        verdict = "clear" if strong else ("not significant" if p > 0.05 else "borderline")
        s.append(txt(L, y + sh + 22, f"{(a/na)/(c/nc):.1f}x   p = {p:.3f}   {verdict}",
                     size=12, fill=INK if strong else MUTED,
                     weight="600" if strong else "normal", tab=True))

    fy = TOP + 236
    s.append(f'<line x1="{L}" y1="{fy - 22}" x2="{W - R}" y2="{fy - 22}" stroke="{RULE}" stroke-width="1"/>')
    foot, _ = para(L, fy, "And the economics lean is mostly composition: split by filer size class it "
                   "nearly vanishes — 31% vs 20% among large accelerated filers, 85% vs 79% among "
                   "everything smaller. Small companies fail to cover their overhead about four times "
                   "in five whether or not anybody shorts them.",
                   size=12, fill=INK2, chars=112)
    s += foot
    s.append("</svg>")
    OUT.write_text("\n".join(s))
    for title, _, a, na, c, nc in axes:
        print(f"  {title:<32}{a}/{na}={a/na:.0%} vs {c}/{nc}={c/nc:.0%}  "
              f"{(a/na)/(c/nc):.1f}x  p={fisher(a, na-a, c, nc-c):.4f}")


if __name__ == "__main__":
    main()
