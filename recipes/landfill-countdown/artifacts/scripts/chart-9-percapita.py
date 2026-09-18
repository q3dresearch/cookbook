#!/usr/bin/env python3
"""How much landfill room each state has per resident, against how fast it uses it.

    python3 chart-9-percapita.py

A state's total remaining capacity says nothing on its own: Nevada's 1.2 billion tons and
New Jersey's 55 million are not comparable until both are divided by the people who fill
them. Per resident the gap is **385 tons against 6**, a factor of sixty-four, which is the
largest spread of any measure in this recipe.

The second axis is how fast each state buries, also per resident. Dividing one by the
other gives years of room left at the current rate, and because both axes are logarithmic
those are the straight diagonals. A state below a diagonal has less time than it.

**The caveat is the whole reason this is not a simple ranking.** The numerator counts
waste buried *in* a state and the denominator counts people *living* in it, and waste
crosses state lines. Pennsylvania and Ohio import heavily, which inflates their disposal
per resident and understates their years, while New Jersey exports, which flatters it. So
read the vertical position as a hard fact about stock and the horizontal position as
"disposal happening here", not "waste generated here".

Population is the Census 2023 county estimate summed to state, which is why the count is
45 states: the rest have fewer than five open landfills reporting both capacity numbers,
and a per-capita figure over three sites is an accident rather than a measure.
"""
import collections, json, math, os, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
sys.path.insert(0, HERE)
from lmopdata import DATA
import geo

OUT = os.path.join(HERE, "..", "charts", "9-percapita.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
HOT, COOL, MID = "#8c2318", "#1b4f8a", "#c07a1e"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
XLO, XHI, YLO, YHI = 0.15, 2.5, 3.0, 600.0
MIN_SITES = 5


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
    agg = collections.defaultdict(lambda: [0.0, 0.0, 0])
    for r in rows:
        if not r["open"] or not r["cap"] or not r["wip"]:
            continue
        a = agg[r["state"]]
        a[0] += max(r["cap"] - r["wip"], 0)
        a[1] += r["rate"] or 0
        a[2] += 1
    pops = collections.defaultdict(int)
    rev = {v: k for k, v in geo.STATES.items()}
    for (stn, _), (p, _) in geo.counties().items():
        if stn in rev:
            pops[rev[stn]] += p
    pts = []
    for s, (room, rate, n) in agg.items():
        pop = pops.get(s, 0)
        if n < MIN_SITES or pop < 200000 or rate <= 0:
            continue
        pts.append({"s": s, "n": n, "room": room, "pop": pop,
                    "y": room / pop, "x": rate / pop, "yr": room / rate})

    W, H, L, T, PW, PH = 1020, 726, 104, 178, 572, 402
    lx = lambda v: L + PW * (math.log10(min(max(v, XLO), XHI)) - math.log10(XLO)) / (math.log10(XHI) - math.log10(XLO))
    ly = lambda v: T + PH - PH * (math.log10(min(max(v, YLO), YHI)) - math.log10(YLO)) / (math.log10(YHI) - math.log10(YLO))
    body = []
    for t, lab in ((0.15, "0.15"), (0.25, "0.25"), (0.5, "0.5"), (1.0, "1.0"), (2.5, "2.5")):
        body.append(f'<line x1="{lx(t):.1f}" y1="{T}" x2="{lx(t):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
        body.append(txt(lx(t), T + PH + 20, lab, size=11, fill=MUTED, anchor="middle"))
    for t, lab in ((3, "3"), (10, "10"), (30, "30"), (100, "100"), (300, "300"), (600, "600")):
        body.append(f'<line x1="{L}" y1="{ly(t):.1f}" x2="{L+PW}" y2="{ly(t):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ly(t) + 4, lab, size=11, fill=MUTED, anchor="end"))
    body.append(txt(L + PW / 2, T + PH + 46, "tons buried per resident per year", size=12,
                    fill=INK2, anchor="middle"))
    body.append(txt(L - 10, T - 36, "tons of room", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - 22, "per resident", size=11, fill=INK2, anchor="end"))

    # Iso-year diagonals. Both axes are per-resident and logarithmic, so years = y / x is
    # a straight line and the population cancels: the diagonal is the state's countdown.
    for yrs, hot in ((20, True), (50, False), (100, False), (300, False)):
        p0, p1 = (XLO, XLO * yrs), (XHI, XHI * yrs)
        if p0[1] > YHI or p1[1] < YLO:
            continue
        body.append(f'<line x1="{lx(p0[0]):.1f}" y1="{ly(p0[1]):.1f}" x2="{lx(p1[0]):.1f}" '
                    f'y2="{ly(p1[1]):.1f}" stroke="{HOT if hot else RULE}" '
                    f'stroke-width="{1.5 if hot else 1}" stroke-dasharray="{"" if hot else "3 4"}"/>')
        # Labelled at the left end: the right end is where 45 states converge and where
        # the legend sits.
        body.append(txt(lx(0.19) + 4, ly(0.19 * yrs) - 5, f"{yrs} years", size=10,
                        fill=HOT if hot else MUTED, weight="600" if hot else "normal"))

    # Two passes: every circle, then every label. Drawing each label with its own circle
    # let the next state's disc print over the previous state's name.
    rmax = max(p["room"] for p in pts)
    colour = lambda p: HOT if p["yr"] < 20 else (MID if p["yr"] < 60 else COOL)
    for p in sorted(pts, key=lambda p: -p["room"]):
        r = 3.0 + 9.0 * (p["room"] / rmax) ** 0.5
        body.append(f'<circle cx="{lx(p["x"]):.1f}" cy="{ly(p["y"]):.1f}" r="{r:.1f}" '
                    f'fill="{colour(p)}" fill-opacity="0.28" stroke="{colour(p)}" '
                    f'stroke-opacity="0.8" stroke-width="0.9"/>')
    for p in sorted(pts, key=lambda p: -p["room"]):
        body.append(txt(lx(p["x"]), ly(p["y"]) + 3.6, p["s"], size=9.5,
                        fill=colour(p), anchor="middle", weight="700"))

    y0 = T + 20
    for col, lab in ((HOT, "under 20 years"), (MID, "20 to 60"), (COOL, "over 60")):
        n = sum(1 for p in pts if (p["yr"] < 20 if col == HOT else
                                   (20 <= p["yr"] < 60 if col == MID else p["yr"] >= 60)))
        body.append(f'<circle cx="{L+PW+30:.1f}" cy="{y0-4:.1f}" r="5" fill="{col}" fill-opacity="0.45" '
                    f'stroke="{col}" stroke-width="0.9"/>')
        body.append(txt(L + PW + 42, y0, f"{lab}  {n}", size=11, fill=col))
        y0 += 18
    body.append(txt(L + PW + 30, y0 + 12, "mark area is the state's total room", size=10, fill=MUTED))
    lo = min(pts, key=lambda p: p["y"]); hi = max(pts, key=lambda p: p["y"])
    body += wrap(L + PW + 30, y0 + 44,
                 f"{hi['s']} holds {hi['y']:,.0f} tons of room per resident and {lo['s']} holds "
                 f"{lo['y']:,.0f}. Both bury about the same amount each year.",
                 size=11, fill=INK, chars=30, leading=14)
    body += wrap(L + PW + 30, y0 + 134,
                 "Waste crosses state lines. The numerator is buried here, the denominator lives "
                 "here, so importers sit further right than their own residents put there.",
                 size=10.5, fill=MUTED, chars=32, leading=13)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "New Jersey has six tons of landfill room per resident. Nevada has 385.",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="a state planner, or anyone siting new capacity",
                        decide="whether your state is importing or exporting its disposal problem",
                        wrong="per-capita room stops predicting interstate waste flow")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    med = sorted(p["y"] for p in pts)[len(pts) // 2]
    foot = [f"The national median state holds {med:,.0f} tons of room per resident. Below the orange "
            f"diagonal a state has under twenty years at its current rate, whoever is generating the waste.",
            "Per-resident normalisation is what makes states comparable at all, and it is also what "
            "exposes the import problem: a state can look profligate because it is taking someone else's rubbish.",
            f"{len(pts)} states qualify. Population is the Census 2023 county estimate summed to state; "
            f"capacity and rate are the register's own reported figures for open sites."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}  ({len(pts)} states)")
    print(f"  {hi['s']} {hi['y']:,.0f} t/person; {lo['s']} {lo['y']:,.0f}; median {med:,.0f}")
    print(f"  under 20 years: {', '.join(sorted(p['s'] for p in pts if p['yr'] < 20))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
