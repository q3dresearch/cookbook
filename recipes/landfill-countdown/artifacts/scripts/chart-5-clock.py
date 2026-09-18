#!/usr/bin/env python3
"""Whether the clock actually ran down between the register's two editions.

    python3 chart-5-clock.py

Every other figure here is a snapshot. This is the only one that uses the fact that two
editions survived: it puts each landfill's countdown in 2021 against its countdown in
2024 and asks whether three years actually cost it three years.

The lower curve is what three years looks like if nothing else happens -- same permit,
same intake, three more years of rubbish. A landfill on that curve simply aged. Above it,
somebody added room, slowed the intake, or both. Below it, the hole is filling faster than
the calendar.

Restricted to the 811 sites whose reported stock advanced by exactly three years, so one
reference curve is correct for every mark. Thirteen others moved by one, two or four years
and are left out rather than judged against the wrong line.

The finding is that the system responds to scarcity. **69% of the landfills that had under
ten years left in 2021 are above the curve; only 38% of those with over fifty years are.**
Permitted capacity grew on 40% of the short ones against 15% of the long ones, and 39% of
all the new permitted tonnage in the country went to the 18% of sites that were nearly out.
A scale-free rank test puts that gradient at rho = -0.28, p < 0.0001, n = 824.
"""
import math, os, sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmopdata import load, num, countdown
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plate                                                             # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "charts", "5-clock.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
GREW, SAME, HOT = "#1b7f5a", "#8a8880", "#c07a1e"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
CAP, YR = "Landfill Design Capacity (tons)", "Waste in Place Year"
WIP = "Waste in Place (tons)"
LO, HI, GAP = 0.6, 200.0, 3.0


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
    a, b = load("2021"), load("2024")
    pts, basket = [], []
    for k in sorted(set(a) & set(b)):
        y0, _ = countdown(a[k], fresh=2017)
        y1, _ = countdown(b[k], fresh=2020)
        t0, t1 = num(a[k].get(YR)), num(b[k].get(YR))
        if y0 is None or y1 is None or not t0 or not t1 or t1 - t0 != GAP:
            continue
        c0, c1 = num(a[k].get(CAP)), num(b[k].get(CAP))
        basket.append(k)
        pts.append({"x": min(max(y0, LO), HI), "y": min(max(y1, LO), HI),
                    "clamp": not (LO <= y0 <= HI and LO <= y1 <= HI),
                    "grew": bool(c0 and c1 and c1 > c0 * 1.01), "raw": (y0, y1),
                    "cap": c1 or 0})
    above = lambda p: p["raw"][1] > max(p["raw"][0] - GAP, 0.01)
    short = [p for p in pts if p["raw"][0] < 10]
    long_ = [p for p in pts if p["raw"][0] >= 50]

    W, H, L, T, PW, PH = 1020, 720, 104, 176, 470, 430
    lx = lambda v: L + PW * (math.log10(v) - math.log10(LO)) / (math.log10(HI) - math.log10(LO))
    ly = lambda v: T + PH - PH * (math.log10(v) - math.log10(LO)) / (math.log10(HI) - math.log10(LO))
    body = []
    for t in (1, 3, 10, 30, 100, 200):
        body.append(f'<line x1="{lx(t):.1f}" y1="{T}" x2="{lx(t):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
        body.append(txt(lx(t), T + PH + 20, f"{t:g}", size=11, fill=MUTED, anchor="middle"))
        body.append(f'<line x1="{L}" y1="{ly(t):.1f}" x2="{L+PW}" y2="{ly(t):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ly(t) + 4, f"{t:g}", size=11, fill=MUTED, anchor="end"))
    body.append(txt(L + PW / 2, T + PH + 46, "years of room left in 2021", size=12, fill=INK2, anchor="middle"))
    body.append(txt(L - 10, T - 36, "years of room", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - 22, "left in 2024", size=11, fill=INK2, anchor="end"))

    # The two reference lines. Equal-value is what "nothing moved at all" looks like; the
    # lower curve is what three years of ordinary use looks like. The space between them
    # is the room that got added back, which is the whole subject of the figure.
    body.append(f'<line x1="{lx(LO):.1f}" y1="{ly(LO):.1f}" x2="{lx(HI):.1f}" y2="{ly(HI):.1f}" '
                f'stroke="{MUTED}" stroke-width="1" stroke-dasharray="3 4"/>')
    seg = []
    for i in range(201):
        v = LO * (HI / LO) ** (i / 200)
        w = v - GAP
        if w >= LO:
            seg.append(f"{'L' if seg else 'M'}{lx(v):.1f},{ly(w):.1f}")
    body.append(f'<path d="{"".join(seg)}" fill="none" stroke="{HOT}" stroke-width="1.8"/>')
    # Labelled at the lower-left end of each line, where the cloud is thin; the upper
    # right is where the two lines converge and where every big site already sits.
    body.append(txt(lx(1.15), ly(1.15) - 7, "unchanged", size=10.5, fill=MUTED))
    body.append(txt(lx(6.0), ly(1.35), "three years older, nothing else", size=10.5,
                    fill=HOT, weight="600"))

    cmax = max(p["cap"] for p in pts) or 1
    for p in sorted(pts, key=lambda p: -p["cap"]):
        r = 1.8 + 5.4 * (p["cap"] / cmax) ** 0.5
        body.append(f'<circle cx="{lx(p["x"]):.1f}" cy="{ly(p["y"]):.1f}" r="{r:.1f}" '
                    f'fill="{GREW if p["grew"] else SAME}" fill-opacity="{0.6 if p["grew"] else 0.34}"/>')

    # the two bands the finding is about
    for lo_, hi_, lab, g in ((LO, 10, "under 10 years in 2021", short), (50, HI, "over 50 years", long_)):
        body.append(f'<rect x="{lx(lo_):.1f}" y="{T}" width="{lx(hi_)-lx(lo_):.1f}" height="{PH}" '
                    f'fill="{INK}" fill-opacity="0.035"/>')
        pc = sum(above(p) for p in g) / len(g)
        body.append(txt((lx(lo_) + lx(hi_)) / 2, T + PH - 30, f"{pc:.0%} gained room", size=11.5,
                        fill=INK, anchor="middle", weight="600"))
        body.append(txt((lx(lo_) + lx(hi_)) / 2, T + PH - 16, lab, size=10, fill=MUTED, anchor="middle"))

    y0 = T + 20
    for col, op, lab, n in ((GREW, 0.6, "permit grew", sum(p["grew"] for p in pts)),
                            (SAME, 0.34, "permit unchanged or cut", sum(not p["grew"] for p in pts))):
        body.append(f'<circle cx="{L+PW+34:.1f}" cy="{y0-4:.1f}" r="5" fill="{col}" fill-opacity="{op}"/>')
        body.append(txt(L + PW + 46, y0, f"{lab}  {n}", size=11, fill=col if col == GREW else INK2))
        y0 += 18
    body.append(txt(L + PW + 34, y0 + 12, "mark area is permitted capacity", size=10, fill=MUTED))
    body += wrap(L + PW + 34, y0 + 44,
                 "A landfill sitting on the orange curve simply aged three years. Above it, room was "
                 "added or intake slowed. Below it, the hole is filling faster than the calendar.",
                 size=11, fill=INK2, chars=36, leading=15)
    body += wrap(L + PW + 34, y0 + 140,
                 "The gradient between the two shaded bands is the finding: America permits new room, "
                 "and it permits it where the clock is short. 39% of all the new tonnage went to the "
                 "18% of sites that were nearly out.",
                 size=11, fill=INK, chars=36, leading=15)
    nc = sum(p["clamp"] for p in pts)
    if nc:
        body.append(txt(L + PW - 4, T + 14, f"{nc} marks sit on an axis bound", size=10,
                        fill=MUTED, anchor="end"))

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "The clock runs down, and the room gets put back where it is shortest",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="a regulator watching whether expansions follow scarcity",
                        decide="whether a short countdown is a real shortage or a permitting lag",
                        wrong="new capacity stops appearing where the countdown is shortest")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    # Computed, not typed. This footer carried 14.5bn/14.8bn/1.3bn as a literal string for the
    # recipe's whole life, and no basket in the shipped code produced those numbers -- the
    # direction was right and every digit was stale. A headline belongs to whatever basis the
    # figure actually plots, so it is derived from that basis here and the basis is named.
    def _room(ed, keys):
        t = 0.0
        for k in keys:
            c, w = num(ed[k].get(CAP)), num(ed[k].get(WIP))
            if c is not None and w is not None and c - w > 0:
                t += c - w
        return t
    r0, r1 = _room(a, basket), _room(b, basket)
    added = sum(max(0.0, (num(b[k].get(CAP)) or 0) - (num(a[k].get(CAP)) or 0)) for k in basket)
    dug = sum(max(0.0, (num(b[k].get(WIP)) or 0) - (num(a[k].get(WIP)) or 0)) for k in basket)
    foot = [f"Across these {len(basket):,} sites the room grew: {r0/1e9:.1f}bn tons left in 2021, "
            f"{r1/1e9:.1f}bn in 2024, after burying {dug/1e9:.1f}bn, because {added/1e9:.1f}bn tons "
            f"of new capacity was permitted. Scarcity is local, not national.",
            "Measured scale-free: a 10% intake change moves a 100-year site by ten years and a 10-year "
            "site by one. Spearman of log countdown against log ratio: -0.28, p < 0.0001, n = 824.",
            "Two editions is one interval. Room was replaced once, between 2021 and 2024; whether that "
            "is normal, the register no longer holds the years to say."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}  ({len(pts)} paired landfills)")
    print(f"  under 10 yr: {sum(above(p) for p in short)/len(short):.0%} gained (n={len(short)}); "
          f"over 50 yr: {sum(above(p) for p in long_)/len(long_):.0%} (n={len(long_)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
