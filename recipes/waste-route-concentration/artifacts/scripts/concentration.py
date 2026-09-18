#!/usr/bin/env python3
"""Ten lines on a form are half of America's hazardous waste.

    python3 chart-3-concentration.py

This began as an attempt to answer the question the landfill recipe had to abandon: **what
is actually in it.** The municipal register records how much waste is in a hole and never
what; this one carries EPA waste codes and a free-text description on every record, so the
composition should be readable.

It is, and then it is not, because of the shape of the file.

**The ten largest records are about two fifths of all managed tonnage** — not the ten
largest facilities, the ten largest *rows*. One row can carry tens of millions of tons and
a dozen waste codes, and a single 2019 record, Watervliet Arsenal's 55.4 million tons of
"industrial wastewater", is larger than the entire national total for 2023.

**An earlier version of this figure said the file had become more concentrated over time.
It had not.** That claim came from a six-category basket; across all twelve the top ten go
from 40.2% in 2001 to 38.9% in 2023 — flat, with a spike to 41% in 2019 caused by that one
record. The concentration is severe and roughly constant, which is a different statement
and a less exciting one.

So "what is in America's hazardous waste" is mostly "what a handful of Gulf Coast chemical
plants inject underground", and a national composition statistic is a statement about them.

**It also breaks the obvious way of measuring composition.** Counting tonnage once per
waste code a record carries — which is what any "how much plating waste" figure does —
inflates by the number of codes, and that inflation is not stable: **tonnage-weighted codes
per record went from 22.3 in 2001 to 28.2 in 2023**, while unweighted codes per record
*fell*. The largest records carry many codes each, so weighting by tonnage multiplies any
family total by more than twenty — and by a different amount in each cycle.

A family total computed that way showed plating waste up 401% and refinery waste up 194%
over the same span that every management category *fell* in tons. Both were the code count
moving, not the waste.
"""
import csv, glob, gzip, math, os, re, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
CACHE = os.environ.get("HWF_CACHE") or os.path.join(DATA, "br-cache")
sys.path.insert(0, HERE)
import plate
import brdata, plate                                                            # noqa: E402

# Declared, not discovered. An earlier version globbed the cache and summed whatever a
# background pull had finished writing, so the same code gave 30.8M tons for 2001 one hour
# and 226M the next. The basket now travels with the number.
BASKET = brdata.REQUIRED

OUT = os.path.join(HERE, "..", "charts", "concentration.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
OLD, NEW, HOT = "#7fa8c4", "#8c2318", "#c07a1e"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
num = lambda v: float(v) if v not in ("", "None", None) else 0.0


def txt(x, y, s, *, size, fill, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" style="font-variant-numeric: tabular-nums">{escape(str(s))}</text>')


def halo(x, y, s, *, size, fill, anchor="start", weight="600"):
    c = (f'font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" '
         f'style="font-variant-numeric: tabular-nums"')
    e = escape(str(s))
    return [f'<text x="{x:.1f}" y="{y:.1f}" fill="none" stroke="{SURFACE}" stroke-width="3" '
            f'stroke-linejoin="round" {c}>{e}</text>',
            f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" {c}>{e}</text>']


def wrap(x, y, s, *, size, fill, chars, leading=15.0):
    words, line, out, n = str(s).split(), [], [], 0
    for w in words:
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill)); line, n = [], n + 1
        line.append(w)
    if line:
        out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
    return out


def load(y):
    return [r for r in brdata.load(y, BASKET) if num(r["managed_tons"]) > 0]


def main():
    data = {}
    for y in (2001, 2023):
        g = sorted(load(y), key=lambda r: -num(r["managed_tons"]))
        tons = [num(r["managed_tons"]) for r in g]
        tot = sum(tons)
        cum, s = [], 0.0
        for t in tons:
            s += t
            cum.append(s / tot)
        wc = sum(t * max(len(set(re.findall(r"[A-Z]\d{3}", r["federal_waste_codes"] or ""))), 1)
                 for r, t in zip(g, tons)) / tot
        uc = sum(len(set(re.findall(r"[A-Z]\d{3}", r["federal_waste_codes"] or ""))) for r in g) / len(g)
        big = sum(t for r, t in zip(g, tons)
                  if len(set(re.findall(r"[A-Z]\d{3}", r["federal_waste_codes"] or ""))) >= 20) / tot
        data[y] = {"cum": cum, "tot": tot, "n": len(g), "wc": wc, "uc": uc, "big": big,
                   "top": [(r["handler_name"], t) for r, t in zip(g[:6], tons[:6])]}

    W, H, L, T, PW, PH = 1040, 730, 100, 206, 560, 394
    XHI = max(d["n"] for d in data.values())
    lx = lambda r: L + PW * math.log10(max(r, 1)) / math.log10(XHI)
    ly = lambda v: T + PH - PH * v
    body = []
    for t in (1, 10, 100, 1000, 10000, 100000):
        if t <= XHI:
            body.append(f'<line x1="{lx(t):.1f}" y1="{T}" x2="{lx(t):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
            body.append(txt(lx(t), T + PH + 20, f"{t:,}", size=10.5, fill=MUTED, anchor="middle"))
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        body.append(f'<line x1="{L}" y1="{ly(v):.1f}" x2="{L+PW}" y2="{ly(v):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ly(v) + 4, f"{v:.0%}", size=11, fill=MUTED, anchor="end"))
    body.append(txt(L + PW / 2, T + PH + 46, "number of records, largest first (logarithmic)",
                    size=12, fill=INK2, anchor="middle"))
    body.append(txt(L - 10, T - 36, "share of all", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - 22, "managed tonnage", size=11, fill=INK2, anchor="end"))

    for y, col in ((2001, OLD), (2023, NEW)):
        d = data[y]
        pts = []
        r = 1
        while r <= d["n"]:
            pts.append(f"{'M' if not pts else 'L'}{lx(r):.1f},{ly(d['cum'][r-1]):.1f}")
            r = max(r + 1, int(r * 1.12))
        body.append(f'<path d="{"".join(pts)}" fill="none" stroke="{col}" stroke-width="2.6"/>')
        body.append(f'<circle cx="{lx(10):.1f}" cy="{ly(d["cum"][9]):.1f}" r="4.5" fill="{col}"/>')
        body += halo(lx(10) + 9, ly(d["cum"][9]) + 4, f"{y}: ten records = {d['cum'][9]:.0%}",
                     size=11.5, fill=col)
    body.append(f'<line x1="{lx(10):.1f}" y1="{T}" x2="{lx(10):.1f}" y2="{T+PH}" '
                f'stroke="{INK}" stroke-width="1" stroke-dasharray="3 3"/>')

    d = data[2023]
    body += wrap(L + PW + 26, T + 4, "The ten largest records in 2023, all of them deep-well "
                                     "injection at a chemical plant:", size=11, fill=INK, chars=30, leading=14)
    yy = T + 48
    for nm, t in d["top"]:
        body.append(txt(L + PW + 26, yy, f"{t/1e6:.2f}M", size=10.5, fill=NEW, weight="600"))
        body.append(txt(L + PW + 70, yy, (nm or "")[:26], size=10, fill=INK2))
        yy += 15
    body += wrap(L + PW + 26, yy + 18,
                 f"Counting tonnage once per waste code a record carries inflates it by "
                 f"{data[2001]['wc']:.1f}x in 2001 and {d['wc']:.1f}x in 2023 — so any "
                 f"“how much plating waste” figure grows without waste being made.",
                 size=10.5, fill=MUTED, chars=32, leading=13)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Ten lines on a form are half of America's hazardous waste",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="anyone designing a sampling, audit or monitoring programme",
                        decide="how many form codes you must cover to reach half the mass",
                        wrong="the top ten's share drops below a third in a later cycle")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    foot = [f"A national statement about what is in American hazardous waste is a statement about a "
            f"handful of plants: {d['cum'][9]:.0%} of the tonnage is ten records, against "
            f"{data[2001]['cum'][9]:.0%} in 2001 — severe, and roughly constant.",
            f"Records with twenty or more waste codes were {data[2001]['big']:.1%} of tonnage in 2001 "
            f"and {d['big']:.1%} in 2023, while unweighted codes per record fell from "
            f"{data[2001]['uc']:.1f} to {d['uc']:.1f}. The giants got wordier; the rest did not.",
            f"{data[2001]['n']:,} records in 2001 and {d['n']:,} in 2023, across all twelve "
            f"management categories. This is a curve over records, not over facilities: it says "
            f"nothing about plants consolidating. Method in the recipe."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for y in (2001, 2023):
        print(f"    {y}: top10 {data[y]['cum'][9]:.1%}, weighted codes/row {data[y]['wc']:.1f}, "
              f"20+ code tonnage {data[y]['big']:.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
