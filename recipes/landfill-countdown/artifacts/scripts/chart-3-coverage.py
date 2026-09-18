#!/usr/bin/env python3
"""What the countdown cannot see, and whether it is worth anything.

    python3 chart-3-coverage.py

Figures 1, 2 and 4 are computed on the 863 open sites that report design capacity, a dated
stock and an acceptance rate. 403 do not, and this figure bounds what that costs.

Two earlier versions were wrong in instructive ways.

**The first** plotted tons accepted per year against tons already in the ground, coloured
by whether a countdown was computable. Those axes are 60% the same variable in logs
(r = 0.78), so the scatter was a fat diagonal that spent its second dimension on nothing.
It also invited the reading that ownership drives reporting, when ownership is riding
along with size.

**The second** put coverage on a continuous size axis as a running line with the banded
rates as dots on top of it. That is the grammar of a price series with buy and sell
markers, and it read as one: a trend with signals fired against it. A rate compared across
strata is not a series, and drawing it as one tells the reader to look for momentum and
crossings that do not exist.

So this is laid out as what it is — one row per size band, smallest at the top. The left
column is who reports, with the distance between the two dots being the whole ownership
effect. The right column is how many landfills that band holds against how much waste, on
one shared scale so the two bars can be compared directly. The top three rows are the
answer: 41% of the landfills, 5% of the waste.

The bands do not manufacture the gradient. A sliding window of 121 sites over the size
rank reproduces the same curve; the script prints it.
"""
import math, os, sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmopdata import load, num, countdown
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plate                                                             # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "charts", "3-coverage.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
PRIV, PUB, HOT, SITE = "#b03a2e", "#1b4f8a", "#c07a1e", "#9a988f"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
RATE = "Annual Waste Acceptance Rate (tons per year)"
BANDS = ((0, 1e4, "under 10k"), (1e4, 3e4, "10k - 30k"), (3e4, 1e5, "30k - 100k"),
         (1e5, 3e5, "100k - 300k"), (3e5, 1e6, "300k - 1M"), (1e6, 1e12, "over 1M"))
BMAX = 0.45


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
    b = load("2024")
    rows = []
    for r in b.values():
        if str(r.get("Current Landfill Status") or "").strip() != "Open":
            continue
        rate = num(r.get(RATE))
        if rate and rate > 0:
            rows.append((rate, countdown(r)[0] is not None,
                         str(r.get("Ownership Type") or "").strip() == "Private"))
    rows.sort()
    n_all = sum(1 for r in b.values() if str(r.get("Current Landfill Status") or "").strip() == "Open")
    tot = sum(x for x, _, _ in rows)
    cov_all = sum(c for _, c, _ in rows) / n_all

    band = []
    for lo, hi, lab in BANDS:
        g = [(x, c, p) for x, c, p in rows if lo <= x < hi]
        pub = [c for _, c, p in g if not p]
        pri = [c for _, c, p in g if p]
        band.append({"lab": lab, "n": len(g), "cov": sum(c for _, c, _ in g) / len(g),
                     "pub": (sum(pub) / len(pub), len(pub)) if pub else None,
                     "pri": (sum(pri) / len(pri), len(pri)) if pri else None,
                     "tons": sum(x for x, _, _ in g) / tot, "sites": len(g) / len(rows)})

    W, H = 1020, 648
    LBL, AX, AW = 28, 196, 292          # left column: coverage
    BX, BW = 610, 330                   # right column: share of the country
    R0, RH = 216, 54
    ax = lambda v: AX + AW * v
    bx = lambda v: BX + BW * min(v, BMAX) / BMAX
    body = []

    body.append(txt(LBL, R0 - 52, "tons accepted", size=11, fill=INK2))
    body.append(txt(LBL, R0 - 38, "per year", size=11, fill=INK2))
    body.append(txt(AX, R0 - 52, "share of the band with a computable countdown",
                    size=12, fill=INK, weight="600"))
    body.append(txt(AX, R0 - 36, "the gap between the dots is the entire ownership effect",
                    size=10.5, fill=MUTED))
    body.append(txt(BX, R0 - 52, "what the band is worth", size=12, fill=INK, weight="600"))
    body.append(txt(BX, R0 - 36, "share of all open landfills, and of all waste accepted",
                    size=10.5, fill=MUTED))

    for v in (0, 0.25, 0.5, 0.75, 1.0):
        body.append(f'<line x1="{ax(v):.1f}" y1="{R0-24}" x2="{ax(v):.1f}" y2="{R0+RH*len(band)-16}" '
                    f'stroke="{GRID}"/>')
        body.append(txt(ax(v), R0 - 12, f"{v:.0%}", size=10, fill=MUTED, anchor="middle"))
    for v in (0, 0.1, 0.2, 0.3, 0.4):
        body.append(f'<line x1="{bx(v):.1f}" y1="{R0-24}" x2="{bx(v):.1f}" y2="{R0+RH*len(band)-16}" '
                    f'stroke="{GRID}"/>')
        body.append(txt(bx(v), R0 - 12, f"{v:.0%}", size=10, fill=MUTED, anchor="middle"))

    for i, d in enumerate(band):
        y = R0 + i * RH + 16
        if i % 2 == 0:
            body.append(f'<rect x="{LBL-6}" y="{y-20:.1f}" width="{W-2*LBL+12}" height="{RH-6}" '
                        f'fill="{GRID}" fill-opacity="0.5"/>')
        body.append(txt(LBL, y + 1, d["lab"], size=12, fill=INK, weight="600"))
        body.append(txt(LBL, y + 16, f"{d['n']} landfills", size=10, fill=MUTED))

        # The dumbbell. Distance between the dots IS the ownership effect, which is the
        # comparison the figure exists to make, so it is a length and not two positions
        # the reader has to difference by eye.
        if d["pub"] and d["pri"]:
            body.append(f'<line x1="{ax(d["pub"][0]):.1f}" y1="{y:.1f}" x2="{ax(d["pri"][0]):.1f}" '
                        f'y2="{y:.1f}" stroke="{MUTED}" stroke-width="1.6" stroke-opacity="0.75"/>')
        for col, key in ((PUB, "pub"), (PRIV, "pri")):
            if not d[key]:
                continue
            rate_, n_ = d[key]
            r = 3.0 + 6.0 * (n_ / 340) ** 0.5
            body.append(f'<circle cx="{ax(rate_):.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{col}" '
                        f'fill-opacity="0.85"/>')
        body.append(txt(ax(d["cov"]), y + 27, f"{d['cov']:.0%} overall", size=10,
                        fill=INK2, anchor="middle"))

        for j, (val, col, lab) in enumerate(((d["sites"], SITE, "landfills"), (d["tons"], HOT, "waste"))):
            yy = y - 11 + j * 13
            body.append(f'<rect x="{BX}" y="{yy:.1f}" width="{max(bx(val)-BX, 0.8):.1f}" height="10" '
                        f'fill="{col}"/>')
            body.append(txt(bx(val) + 6, yy + 9, f"{val:.1%} of {lab}", size=9.5, fill=INK2))

    s3 = sum(d["sites"] for d in band[:3])
    t3 = sum(d["tons"] for d in band[:3])

    y0 = R0 + len(band) * RH + 4
    for col, lab in ((PUB, "publicly owned"), (PRIV, "privately owned")):
        body.append(f'<circle cx="{AX+6:.1f}" cy="{y0-4:.1f}" r="5" fill="{col}" fill-opacity="0.85"/>')
        body.append(txt(AX + 18, y0, lab, size=11, fill=col))
        y0 += 17
    body.append(txt(AX + 130, R0 + len(band) * RH + 4, "dot area is how many sites it averages",
                    size=10, fill=MUTED))
    body += wrap(BX, R0 + len(band) * RH + 4,
                 f"The top three rows are {s3:.0%} of America's open landfills and {t3:.1%} of the "
                 f"waste it buries. That is why missing them costs the site count and not the tonnage.",
                 size=11, fill=INK, chars=64, leading=15)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "The countdown misses small landfills, and small landfills barely matter",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="anyone worried the countdown's sample is unrepresentative",
                        decide="whether to chase the missing small sites before using the figure",
                        wrong="the uncovered sites turn out to hold a meaningful share of national room")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    foot = [f"Read figures 1, 2 and 4 as claims about national capacity, which they cover at 94%, not "
            f"about the typical landfill, which they cover at {cov_all:.0%}.",
            "Above 10k tons a year the private-public gap is 3 to 15 points, against a 36-point raw gap "
            "between counted and uncounted sites. The top row's 44-point gap rests on 15 private sites.",
            f"{len(rows):,} of {n_all:,} open sites report a rate and can be banded; the other "
            f"{n_all-len(rows)} count as uncovered. A sliding window over size rank gives the same gradient."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"  top three bands: {s3:.1%} of sites, {t3:.1%} of tonnage")
    # the continuous check the bands replaced
    win = 121
    pts = [(rows[i + win // 2][0], sum(c for _, c, _ in rows[i:i + win]) / win)
           for i in range(0, len(rows) - win, max(1, (len(rows) - win) // 8))]
    print("  sliding window of 121 sites over size rank (the bands are not making the gradient):")
    for x, v in pts:
        print(f"    at {x:>10,.0f} tons/yr   {v:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
