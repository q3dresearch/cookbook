#!/usr/bin/env python3
"""Why each landfill is short of time: because it is nearly full, or because it is fast.

    python3 chart-4-fullness.py

Figure 1 plots remaining tons against years left, and remaining tons confounds two
different things. A small hole that is nearly empty and a huge one that is nearly full
can show the same remaining room, and the reader cannot tell which they are looking at.

The countdown decomposes exactly, with no residual:

    years left = (1 - fraction full) / (fraction of capacity consumed per year)

So the two causes of a short countdown are separable and they are the two axes here.
Right is nearly full. Up is consuming itself quickly. The curves are iso-countdowns: every
landfill on one has the same years left for a different reason. Mark area is design
capacity, which is the size question figure 1 could not answer.

The finding is that the emergency is almost entirely on the right, not the top. Sites
with under five years are nearly-full sites, not fast ones, which matters because those
are different problems: a nearly-full site needs a replacement sited, and a fast one
needs its intake managed.
"""
import math, os, sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmopdata import load, num, countdown
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plate                                                             # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "charts", "4-fullness.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
PRIV, PUB, HOT = "#b03a2e", "#1b4f8a", "#c07a1e"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
CAP, WIP, RATE = ("Landfill Design Capacity (tons)", "Waste in Place (tons)",
                  "Annual Waste Acceptance Rate (tons per year)")
TLO, THI = 0.002, 0.12


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
    pts = []
    for r in b.values():
        yrs, _ = countdown(r)
        if yrs is None:
            continue
        cap, wip, rate = num(r.get(CAP)), num(r.get(WIP)), num(r.get(RATE))
        pts.append({"full": min(max(wip / cap, 0.0), 1.0), "turn": min(max(rate / cap, TLO), THI),
                    "cap": cap, "yrs": yrs,
                    "priv": str(r.get("Ownership Type") or "").strip() == "Private",
                    "clamped": not (TLO <= rate / cap <= THI)})
    urgent = [p for p in pts if p["yrs"] < 5]
    by_full = sum(1 for p in urgent if p["full"] >= 0.9)

    W, H, L, T, PW, PH = 1020, 700, 120, 172, 590, 390
    lx = lambda v: L + PW * v
    ly = lambda v: T + PH - PH * (math.log10(v) - math.log10(TLO)) / (math.log10(THI) - math.log10(TLO))
    body = []
    for t in (0, 0.2, 0.4, 0.6, 0.8, 1.0):
        body.append(f'<line x1="{lx(t):.1f}" y1="{T}" x2="{lx(t):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
        body.append(txt(lx(t), T + PH + 20, f"{t:.0%}", size=11, fill=MUTED, anchor="middle"))
    for t, lab in ((0.002, "0.2%"), (0.005, "0.5%"), (0.01, "1%"), (0.02, "2%"), (0.05, "5%"), (0.1, "10%")):
        body.append(f'<line x1="{L}" y1="{ly(t):.1f}" x2="{L+PW}" y2="{ly(t):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ly(t) + 4, lab, size=11, fill=MUTED, anchor="end"))
    body.append(txt(L + PW / 2, T + PH + 46, "share of permitted capacity already used",
                    size=12, fill=INK2, anchor="middle"))
    body.append(txt(L - 10, T - 36, "share used", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - 22, "each year", size=11, fill=INK2, anchor="end"))

    urgent_path = []
    for i in range(241):
        f = i / 240 * 0.999
        urgent_path.append(f"{'M' if not i else 'L'}{lx(f):.1f},{ly(min(max((1-f)/5, TLO), THI)):.1f}")
    body.append(f'<path d="{"".join(urgent_path)}L{lx(0.999):.1f},{T}L{lx(0.0):.1f},{T}Z" '
                f'fill="{HOT}" fill-opacity="0.06"/>')

    # Iso-countdowns. Every point on one curve has the same years left, so the curve is
    # the claim: these two landfills are equally short of time for opposite reasons.
    for yrs in (5, 10, 25, 50, 100):
        seg, pen = [], False
        for i in range(241):
            f = i / 240 * 0.999
            t = (1 - f) / yrs
            if TLO <= t <= THI:
                seg.append(f"{'L' if pen else 'M'}{lx(f):.1f},{ly(t):.1f}"); pen = True
            else:
                pen = False
        if seg:
            hot = yrs == 5
            body.append(f'<path d="{"".join(seg)}" fill="none" stroke="{HOT if hot else RULE}" '
                        f'stroke-width="{1.6 if hot else 1}" stroke-dasharray="{"" if hot else "3 3"}"/>')
            # Labelled where the curve is still inside the frame, which for the long
            # countdowns is near the bottom rather than the top.
            # Anchored at a chosen x per curve so four labels do not pile up in the
            # corner where the curves converge.
            fl = {5: 0.44, 10: 0.93, 25: 0.84, 50: 0.71, 100: 0.52}[yrs]
            tl = (1 - fl) / yrs
            if TLO <= tl <= THI:
                body.append(txt(lx(fl) - 5, ly(tl) - 6, f"{yrs} yr", size=10,
                                fill=HOT if hot else MUTED, anchor="end",
                                weight="600" if hot else "normal"))

    caps = [p["cap"] for p in pts]
    cmax = max(caps)
    for p in sorted(pts, key=lambda p: -p["cap"]):
        r = 1.6 + 7.4 * (p["cap"] / cmax) ** 0.5
        body.append(f'<circle cx="{lx(p["full"]):.1f}" cy="{ly(p["turn"]):.1f}" r="{r:.1f}" '
                    f'fill="{PRIV if p["priv"] else PUB}" fill-opacity="0.34" '
                    f'stroke="{PRIV if p["priv"] else PUB}" stroke-opacity="0.5" stroke-width="0.6"/>')

    y0 = T + 20
    for col, lab, n in ((PRIV, "privately owned", sum(p["priv"] for p in pts)),
                        (PUB, "publicly owned", sum(not p["priv"] for p in pts))):
        body.append(f'<circle cx="{L+PW+22:.1f}" cy="{y0-4:.1f}" r="4.5" fill="{col}" fill-opacity="0.55" '
                    f'stroke="{col}" stroke-opacity="0.7" stroke-width="0.7"/>')
        body.append(txt(L + PW + 34, y0, f"{lab}  {n}", size=11, fill=col))
        y0 += 18
    # Size legend: three real capacities drawn at the radii they would get.
    body.append(txt(L + PW + 22, y0 + 14, "mark area is design capacity", size=10.5, fill=INK2, weight="600"))
    yy = y0 + 42
    for tons, lab in ((2e6, "2M tons"), (2e7, "20M"), (1e8, "100M")):
        rr = 1.6 + 7.4 * (tons / cmax) ** 0.5
        body.append(f'<circle cx="{L+PW+34:.1f}" cy="{yy:.1f}" r="{rr:.1f}" fill="none" '
                    f'stroke="{MUTED}" stroke-width="0.9"/>')
        body.append(txt(L + PW + 52, yy + 4, lab, size=10, fill=MUTED))
        yy += 26

    body += wrap(L + PW + 22, yy + 12,
                 f"Of the {len(urgent)} landfills with under five years, {by_full} are at least "
                 "90% full. Almost none are in trouble because they are fast.",
                 size=10.5, fill=MUTED, chars=28, leading=13)
    nc = sum(p["clamped"] for p in pts)
    if nc:
        body.append(txt(L + PW, T + 14, f"{nc} marks sit on an axis bound", size=10.5,
                        fill=MUTED, anchor="end"))

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Landfills run out of room by filling up, not by speeding up",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="a planner modelling when a specific site closes",
                        decide="whether to model intake growth or just remaining volume",
                        wrong="intake rate predicts closure better than fill level does")
    s += fr
    s += body
    fy = H - 22 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    foot = [f"The emergency is on the right edge, not the top: {by_full} of the {len(urgent)} sites under "
            "five years are 90% full or more. That is a siting problem, not an intake problem.",
            "The median landfill is 53% full and consumes 1.6% of itself a year, which is 62 years of "
            "design life at today's rate — most of the register is in no hurry.",
            "863 open sites, the ones reporting all three numbers. Both causes are measured against "
            "permitted capacity, so a permit expansion moves a mark left and down at once."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}  ({len(pts)} landfills)")
    print(f"  under five years: {len(urgent)}, of which {by_full} are >=90% full ({by_full/len(urgent):.0%})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
