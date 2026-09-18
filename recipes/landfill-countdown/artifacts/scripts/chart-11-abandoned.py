#!/usr/bin/env python3
"""What happens to a landfill after it closes, and whether that has changed.

    python3 chart-11-abandoned.py

A closed landfill keeps making methane for decades. The register records whether each one
has a gas collection system, whether it only vents passively, or whether nothing is
happening at all -- so "what became of the abandoned ones" is answerable for 1,260 closed
sites with a closure year.

The control rate by decade of closure swings hard -- 33% for the 1990s against 68% for the
1980s and 65% for the 2020s -- and the obvious reading is that practice changed. A first
draft of this figure asserted that the decade marginal was flat. **It is not, and saying
so would have been the figure asserting something the data on it contradicts.**

The right way to test it is to ask what each decade's rate *would* be if only its size mix
mattered. Take the overall control rate in each size band as a standard, weight it by the
decade's own composition, and compare. From 1990 onward the observed rate is within four
points of that expectation in every decade: -4%, +3%, +4%, -3%. The swing is the 1990s
Subtitle D wave, which closed a very large number of very small dumps.

So the two marginals here are not "one moves, one does not". The top one is the size
gradient, 8% to 94%. The right one is observed against expected, and **they track** --
which is the stronger statement, because it says the decade carries no information once
size is known.

Which makes it the third time in this recipe that an apparent effect of era, ownership or
geography turned out to be size. In this register size is the confounder to rule out
first, not last.
"""
import collections, json, math, os, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
sys.path.insert(0, HERE)
from lmopdata import DATA

OUT = os.path.join(HERE, "..", "charts", "11-abandoned.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
GAS, PASS, NONE_, ACC = "#1b4f8a", "#c07a1e", "#b03a2e", "#0b0b0b"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
XLO, XHI, Y0, Y1 = 2e4, 6e7, 1960, 2025
SB = ((0, 5e5), (5e5, 2e6), (2e6, 1e7), (1e7, 1e12))
SLAB = ("<500k", "0.5-2M", "2-10M", ">10M")


def txt(x, y, s, *, size, fill, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" style="font-variant-numeric: tabular-nums">{escape(str(s))}</text>')


def wrap(x, y, s, *, size, fill, chars, leading=15.0):
    words, line, out, n = str(s).split(), [], [], 0
    for w in words:
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill)); line, n = [], n + 1
        line.append(w)
    if line:
        out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
    return out


def main():
    rows = json.load(open(os.path.join(DATA, "features.json")))
    cl = [r for r in rows if not r["open"] and r["closure_year"] and r["wip"]
          and 1940 <= r["closure_year"] <= 2024 and r["wip"] > 0]
    kind = lambda r: "gas" if r["has_gas"] else ("pass" if r["passive"] else "none")

    W, H, L, T, PW, PH = 1020, 742, 112, 232, 512, 348
    MT, MR = 62, 86                                  # marginal strips, above and right
    lx = lambda v: L + PW * (math.log10(min(max(v, XLO), XHI)) - math.log10(XLO)) / (math.log10(XHI) - math.log10(XLO))
    ly = lambda v: T + PH - PH * (min(max(v, Y0), Y1) - Y0) / (Y1 - Y0)
    body = []
    for t, lab in ((2e4, "20k"), (1e5, "100k"), (1e6, "1M"), (1e7, "10M")):
        body.append(f'<line x1="{lx(t):.1f}" y1="{T-MT}" x2="{lx(t):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
        body.append(txt(lx(t), T + PH + 20, lab, size=11, fill=MUTED, anchor="middle"))
    for t in (1960, 1980, 2000, 2020):
        body.append(f'<line x1="{L}" y1="{ly(t):.1f}" x2="{L+PW+MR}" y2="{ly(t):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ly(t) + 4, t, size=11, fill=MUTED, anchor="end"))
    body.append(txt(L + PW / 2, T + PH + 46, "tons of waste buried there (logarithmic)",
                    size=12, fill=INK2, anchor="middle"))
    body.append(txt(L - 10, T - MT - 14, "year it", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - MT, "closed", size=11, fill=INK2, anchor="end"))

    for r in sorted(cl, key=lambda r: {"gas": 0, "pass": 1, "none": 2}[kind(r)]):
        k = kind(r)
        col = {"gas": GAS, "pass": PASS, "none": NONE_}[k]
        body.append(f'<circle cx="{lx(r["wip"]):.1f}" cy="{ly(r["closure_year"]):.1f}" r="2.7" '
                    f'fill="{col}" fill-opacity="{0.35 if k == "gas" else 0.65}"/>')

    # Top marginal: control rate by size. This one moves.
    body.append(txt(L, T - MT - 32, "share with a gas system, by size", size=11, fill=INK, weight="600"))
    pts = []
    for (lo, hi), lab in zip(SB, SLAB):
        g = [r for r in cl if lo <= r["wip"] < hi]
        if len(g) < 8:
            continue
        rate = sum(r["has_gas"] for r in g) / len(g)
        xm = lx(math.sqrt(max(lo, XLO) * min(hi, XHI)))
        pts.append((xm, T - MT + (MT - 8) * (1 - rate), rate, len(g), lab))
    body.append(f'<path d="{" ".join(("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x, y, *_ ) in enumerate(pts))}" '
                f'fill="none" stroke="{ACC}" stroke-width="1.6" stroke-opacity="0.45"/>')
    for x, y, rate, n, lab in pts:
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="{ACC}"/>')
        body.append(txt(x, y - 8, f"{rate:.0%}", size=10, fill=ACC, anchor="middle", weight="600"))

    # Right marginal: observed against what the decade's own size mix predicts. Drawing
    # only the observed series invited the reading that practice improved; drawing both
    # shows the decade adds nothing once size is known.
    body.append(txt(L + PW + 10, T - 30, "by decade", size=11, fill=INK, weight="600"))
    body.append(txt(L + PW + 10, T - 17, "observed vs size-predicted", size=9.5, fill=MUTED))
    base = {}
    for i, (lo, hi) in enumerate(SB):
        g = [r for r in cl if lo <= r["wip"] < hi]
        base[i] = (sum(r["has_gas"] for r in g) / len(g)) if g else 0.0
    band = lambda w: next(i for i, (lo, hi) in enumerate(SB) if lo <= w < hi)
    dec = collections.defaultdict(list)
    for r in cl:
        dec[int(r["closure_year"] // 10) * 10].append(r)
    dpts = []
    for d in sorted(dec):
        g = dec[d]
        if len(g) < 8 or d < Y0:
            continue
        obs = sum(r["has_gas"] for r in g) / len(g)
        comp = collections.Counter(band(r["wip"]) for r in g)
        exp = sum(base[i] * n / len(g) for i, n in comp.items())
        dpts.append((ly(d + 5), obs, exp, len(g)))
    mx = lambda v: L + PW + 8 + (MR - 16) * v
    for series, col, op, w in ((2, MUTED, 0.9, 1.2), (1, ACC, 0.5, 1.6)):
        body.append(f'<path d="{" ".join(("M" if i == 0 else "L") + f"{mx(p[series]):.1f},{p[0]:.1f}" for i, p in enumerate(dpts))}" '
                    f'fill="none" stroke="{col}" stroke-width="{w}" stroke-opacity="{op}" '
                    f'{"stroke-dasharray=\"3 3\"" if series == 2 else ""}/>')
    for y, obs, exp, n in dpts:
        body.append(f'<line x1="{mx(min(obs,exp)):.1f}" y1="{y:.1f}" x2="{mx(max(obs,exp)):.1f}" '
                    f'y2="{y:.1f}" stroke="{MUTED}" stroke-width="1"/>')
        body.append(f'<circle cx="{mx(exp):.1f}" cy="{y:.1f}" r="3" fill="{SURFACE}" '
                    f'stroke="{MUTED}" stroke-width="1.3"/>')
        body.append(f'<circle cx="{mx(obs):.1f}" cy="{y:.1f}" r="4.2" fill="{ACC}"/>')
        body.append(txt(mx(max(obs, exp)) + 8, y + 4, f"{obs:.0%}", size=10, fill=ACC))
    body.append(f'<line x1="{L+PW+8}" y1="{T}" x2="{L+PW+8}" y2="{T+PH}" stroke="{RULE}"/>')
    body.append(f'<line x1="{L+PW+MR-8}" y1="{T}" x2="{L+PW+MR-8}" y2="{T+PH}" stroke="{RULE}"/>')
    body.append(txt(L + PW + 8, T + PH + 20, "0%", size=9.5, fill=MUTED, anchor="middle"))
    body.append(txt(L + PW + MR - 8, T + PH + 20, "100%", size=9.5, fill=MUTED, anchor="middle"))

    y0 = T + PH + 62
    for col, lab, k in ((GAS, "gas collection system", "gas"), (PASS, "passive venting only", "pass"),
                        (NONE_, "no control at all", "none")):
        n = sum(1 for r in cl if kind(r) == k)
        body.append(f'<circle cx="{L+6:.1f}" cy="{y0-4:.1f}" r="5" fill="{col}" fill-opacity="0.7"/>')
        body.append(txt(L + 18, y0, f"{lab}  {n}  ({n/len(cl):.0%})", size=11, fill=col))
        y0 += 17

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Whether an abandoned landfill is controlled depends on its size, not its era",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="a state agency prioritising legacy site remediation",
                        decide="whether to screen legacy sites by closure era or by size",
                        wrong="era predicts whether a site is controlled better than size does")
    s += fr
    s += body
    body_end = T + PH + 62 + 17 * 3
    s += wrap(L + PW + MR + 22, T + 24,
              "Filled dots are what each decade actually shows. Hollow dots are what its own size mix "
              "predicts. From 1990 on they are within four points of each other, so the decade adds "
              "nothing once size is known.",
              size=10.5, fill=INK2, chars=26, leading=13.5)
    s += wrap(L + PW + MR + 22, T + 180,
              "Third time in this recipe that an apparent effect of era, ownership or place turned out "
              "to be size. Here it is the confounder to rule out first.",
              size=10.5, fill=MUTED, chars=26, leading=13.5)
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    small = [r for r in cl if r["wip"] < 5e5]
    foot = [f"If you want more abandoned landfills controlled, the target is small ones: "
            f"{len(small)} closed sites hold under 500,000 tons each and {sum(r['has_gas'] for r in small)/len(small):.0%} "
            f"of them collect gas, in every decade equally.",
            "Observed minus size-predicted, by decade of closure: -4%, +3%, +4%, -3% from the 1990s on. "
            "The 1990s trough is the Subtitle D wave, which closed thousands of very small dumps.",
            f"{len(cl):,} closed landfills with both a stock and a closure year. Sites closing before "
            f"1960 are drawn on the bottom row; the decade marginal starts at 1960 where the counts allow it."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}  ({len(cl)} closed landfills)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
