#!/usr/bin/env python3
"""Which landfills need attention first: short of room, and serving a lot of people.

    python3 chart-10-triage.py

Figures 1 and 4 say how many landfills are nearly full. Neither says which ones matter,
because a hole with three years left in an empty county is a different problem from one
with three years left beside a city. This puts time against people and names the corner.

No composite score. Two measured quantities on two axes and the reader picks their own
threshold, because a weighted index would bury the thing it claims to rank -- multiply two
signals together and you have built an AND, and the sites that are extreme on one and
ordinary on the other vanish.

**The population measure undercounts and it is worth knowing how.** Census urban areas are
polygons but the gazetteer publishes one interior point each, so this counts the
population of every urban area whose *centre* is within 25 km. A landfill ten kilometres
outside a large sprawling city, but forty from its middle, scores zero from that city.
Marks along the bottom of this chart are therefore "no urban centre nearby", not
"nobody there".
"""
import json, math, os, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
sys.path.insert(0, HERE)
from lmopdata import DATA

OUT = os.path.join(HERE, "..", "charts", "10-triage.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
GAS, NOGAS, HOT = "#1b4f8a", "#b03a2e", "#8c2318"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
XLO, XHI, YLO, YHI = 0.3, 200.0, 1000.0, 8e6
URGENT = 5.0


def txt(x, y, s, *, size, fill, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" style="font-variant-numeric: tabular-nums">{escape(str(s))}</text>')


def halo(x, y, s, *, size, fill, weight="normal"):
    """Text with a page-coloured outline, drawn as two elements rather than one.

    `paint-order="stroke"` is the one-element way and browsers honour it, but the renderer
    used to check these figures does not: it paints the stroke over the fill and the label
    comes out solid white. Two elements look identical everywhere."""
    common = (f'font-size="{size}" text-anchor="start" font-weight="{weight}" '
              f'style="font-variant-numeric: tabular-nums"')
    e = escape(str(s))
    return [f'<text x="{x:.1f}" y="{y:.1f}" fill="none" stroke="{SURFACE}" stroke-width="3.2" '
            f'stroke-linejoin="round" {common}>{e}</text>',
            f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" {common}>{e}</text>']


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
    pts = []
    for r in rows:
        if not r["open"] or r["countdown"] is None or r["people_25km"] is None:
            continue
        rem = max((r["cap"] or 0) - (r["wip"] or 0), 1e4)
        pts.append({"x": min(max(r["countdown"], XLO), XHI), "y": min(max(r["people_25km"], YLO), YHI),
                    "rem": rem, "gas": r["has_gas"], "name": r["name"], "st": r["state"],
                    "raw_x": r["countdown"], "raw_y": r["people_25km"],
                    "floor": r["people_25km"] < YLO})
    urgent = [p for p in pts if p["raw_x"] < URGENT]
    named = sorted(urgent, key=lambda p: -p["raw_y"])[:8]

    W, H, L, T, PW, PH = 1020, 726, 132, 176, 542, 404
    lx = lambda v: L + PW * (math.log10(v) - math.log10(XLO)) / (math.log10(XHI) - math.log10(XLO))
    ly = lambda v: T + PH - PH * (math.log10(v) - math.log10(YLO)) / (math.log10(YHI) - math.log10(YLO))
    body = []
    for t, lab in ((0.3, "0.3"), (1, "1"), (5, "5"), (20, "20"), (50, "50"), (200, "200")):
        body.append(f'<line x1="{lx(t):.1f}" y1="{T}" x2="{lx(t):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
        body.append(txt(lx(t), T + PH + 20, lab, size=11, fill=MUTED, anchor="middle"))
    for t, lab in ((1e3, "none"), (1e4, "10k"), (1e5, "100k"), (1e6, "1M"), (8e6, "8M")):
        body.append(f'<line x1="{L}" y1="{ly(t):.1f}" x2="{L+PW}" y2="{ly(t):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ly(t) + 4, lab, size=11, fill=MUTED, anchor="end"))
    body.append(txt(L + PW / 2, T + PH + 46, "years of room left, at the current acceptance rate",
                    size=12, fill=INK2, anchor="middle"))
    body.append(txt(L - 10, T - 36, "people within", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - 22, "25 km", size=11, fill=INK2, anchor="end"))

    body.append(f'<rect x="{lx(XLO):.1f}" y="{T}" width="{lx(URGENT)-lx(XLO):.1f}" height="{PH}" '
                f'fill="{HOT}" fill-opacity="0.06"/>')
    body.append(txt(lx(URGENT) - 8, T + PH - 34, f"{len(urgent)} landfills with under five years",
                    size=11.5, fill=HOT, anchor="end", weight="600"))
    body.append(txt(lx(URGENT) - 8, T + PH - 20,
                    f"{sum(1 for p in urgent if p['raw_y'] >= 1e5)} of them near 100,000 people or more",
                    size=10.5, fill=MUTED, anchor="end"))

    rmax = max(p["rem"] for p in pts)
    for p in sorted(pts, key=lambda p: -p["rem"]):
        r = 1.8 + 6.2 * (p["rem"] / rmax) ** 0.5
        body.append(f'<circle cx="{lx(p["x"]):.1f}" cy="{ly(p["y"]):.1f}" r="{r:.1f}" '
                    f'fill="{GAS if p["gas"] else NOGAS}" fill-opacity="0.45"/>')

    placed = []
    for p in named:
        tx_, ty_ = lx(p["x"]) + 10, ly(p["y"]) + 4
        while any(abs(ty_ - q) < 14 for _, q in placed):
            ty_ += 14
        placed.append((tx_, ty_))
        body += halo(tx_, ty_, f"{p['name'][:26]} ({p['st']})  {p['raw_x']:.1f} yr",
                     size=10, fill=INK, weight="600" if p["raw_y"] > 1e6 else "normal")
        body.append(f'<line x1="{lx(p["x"])+3:.1f}" y1="{ly(p["y"]):.1f}" x2="{tx_-3:.1f}" '
                    f'y2="{ty_-4:.1f}" stroke="{MUTED}" stroke-width="0.7"/>')

    y0 = T + PH - 74
    for col, lab, n in ((GAS, "collects its gas", sum(p["gas"] for p in pts)),
                        (NOGAS, "does not", sum(not p["gas"] for p in pts))):
        body.append(f'<circle cx="{L+PW+30:.1f}" cy="{y0-4:.1f}" r="5" fill="{col}" fill-opacity="0.6"/>')
        body.append(txt(L + PW + 42, y0, f"{lab}  {n}", size=11, fill=col))
        y0 += 18
    body.append(txt(L + PW + 30, y0 + 12, "mark area is the room left", size=10, fill=MUTED))
    body += wrap(L + PW + 30, T + 24,
                 "Top left is the triage corner: little time and a lot of people. Siting a "
                 "replacement takes longer than five years, so every mark in the shaded band is a "
                 "decision somebody is already late for.",
                 size=10.5, fill=INK2, chars=30, leading=13.5)
    nf = sum(p["floor"] for p in pts)
    if nf:
        body.append(txt(L + PW - 4, ly(YLO) - 8, f"{nf} sites have no urban centre within 25 km",
                        size=10, fill=MUTED, anchor="end"))

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "The landfills that need attention first, named", size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="a regulator with a finite inspection budget",
                        decide="which named sites to visit this year",
                        wrong="a named site restates its remaining capacity")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    top = named[0]
    foot = [f"{top['name']} ({top['st']}) has {top['raw_x']:.1f} years and {top['raw_y']/1e6:.1f} million "
            f"people within 25 km. Of the {len(urgent)} sites under five years, "
            f"{sum(1 for p in urgent if not p['gas'])} do not collect their gas either.",
            "No index, no weighting. A composite would rank a site that is extreme on one axis and "
            "ordinary on the other below one that is mediocre on both, which is the opposite of triage.",
            "Population is counted from urban-area centroids, so it undercounts a landfill on the edge "
            "of a large city. Read the bottom row as \"no urban centre nearby\", not as \"nobody there\"."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}  ({len(pts)} landfills, {len(urgent)} urgent)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
