#!/usr/bin/env python3
"""Survival curves for UK companies, by sector, from the register's own snapshots.

    python3 chart.py

One line per sector, four named because sixteen labels is a legend nobody reads. The
quantity is position on both axes, so the reader compares lengths rather than digits.

The axis is age, not calendar time, and that is the whole design: the register publishes
only survivors, so a death is a company missing from a later snapshot, and the estimate
is a discrete-time hazard by age over a two-year observation window. See survive.py.
"""
import json, os, sys
from xml.sax.saxutils import escape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plate                                                             # noqa: E402

DATA = os.environ.get("FSB_DATA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "charts", "1-survival.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
HOT, COOL, WARM, GREY = "#b03a2e", "#1b4f8a", "#c07a1e", "#c9c7bf"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
NAMED = {"Retail & wholesale": HOT, "Information & communication": WARM,
         "Professional & scientific": "#4a7a3a", "Real estate": COOL}


def txt(x, y, s, *, size, fill, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" '
            f'style="font-variant-numeric: tabular-nums">{escape(str(s))}</text>')


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
    d = json.load(open(os.path.join(DATA, "survival.json")))
    curves, allc = d["curves"], d["survival"]
    W, H, L, T, PW, PH = 1020, 660, 92, 150, 620, 360
    xs = lambda a: L + PW * min(a, 25) / 25
    ys = lambda p: T + PH - PH * p
    body = []
    for g in range(0, 101, 20):
        body.append(f'<line x1="{L}" y1="{ys(g/100):.1f}" x2="{L+PW}" y2="{ys(g/100):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ys(g / 100) + 4, f"{g}%", size=11, fill=MUTED, anchor="end"))
    for a in (0, 1, 2, 3, 5, 8, 12, 20, 25):
        body.append(f'<line x1="{xs(a):.1f}" y1="{T}" x2="{xs(a):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
        body.append(txt(xs(a), T + PH + 20, a if a else 0, size=11, fill=MUTED, anchor="middle"))
    body.append(txt(L + PW / 2, T + PH + 44, "years since incorporation", size=12, fill=INK2, anchor="middle"))
    body.append(txt(L - 10, T - 34, "still on the", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - 20, "register", size=11, fill=INK2, anchor="end"))

    def path(pts, col, w, op=1.0):
        pieces = [f"M{xs(0):.1f},{ys(1.0):.1f}"] + [f"L{xs(p['age']):.1f},{ys(p['survival']):.1f}" for p in pts]
        return (f'<path d="{" ".join(pieces)}" fill="none" stroke="{col}" stroke-width="{w}" '
                f'stroke-opacity="{op}" stroke-linejoin="round"/>')

    for name, pts in curves.items():
        if name not in NAMED:
            body.append(path(pts, GREY, 1.4, 0.9))
    body.append(path([{"age": s["band"], "survival": s["survival_to_end"]} for s in []], GREY, 1))
    ally = [{"age": a, "survival": s["survival_to_end"]}
            for a, s in zip((1, 2, 3, 5, 8, 12, 20, 25), allc)]
    body.append(path(ally, INK, 2.6))
    for name, col in NAMED.items():
        if name in curves:
            body.append(path(curves[name], col, 2.4))
    # end labels, spread so they do not collide
    ends = sorted([(curves[n][-1]["survival"], n, c) for n, c in NAMED.items() if n in curves]
                  + [(allc[-1]["survival_to_end"], "All companies", INK)], reverse=True)
    y_prev = -99
    for surv, name, col in ends:
        y = max(ys(surv), y_prev + 16)
        y_prev = y
        body.append(f'<line x1="{L+PW+3:.1f}" y1="{ys(surv):.1f}" x2="{L+PW+14:.1f}" y2="{y:.1f}" '
                    f'stroke="{col}" stroke-width="1"/>')
        body.append(txt(L + PW + 18, y + 4, f"{name}  {surv:.0%}", size=11.5, fill=col,
                        weight="600" if name == "All companies" else "normal"))
    # The median life, interpolated rather than rounded to a band edge. A first version
    # snapped it to the first band whose END was under half and captioned it "within two
    # years", which the numbers do not say: survival is 52.7% at two and 43.8% at three.
    ages = (1, 2, 3, 5, 8, 12, 20, 25)
    sv = [s["survival_to_end"] for s in allc]
    i = next(k for k in range(len(sv)) if sv[k] <= 0.5)
    a0, a1, s0, s1 = ages[i - 1], ages[i], sv[i - 1], sv[i]
    half = a0 + (s0 - 0.5) * (a1 - a0) / (s0 - s1)
    body.append(f'<line x1="{xs(half):.1f}" y1="{ys(0.5):.1f}" x2="{xs(half):.1f}" y2="{T+PH:.1f}" '
                f'stroke="{INK}" stroke-width="1.1" stroke-dasharray="3,3"/>')
    body.append(f'<line x1="{L}" y1="{ys(0.5):.1f}" x2="{xs(half):.1f}" y2="{ys(0.5):.1f}" '
                f'stroke="{INK}" stroke-width="1.1" stroke-dasharray="3,3"/>')
    body.append(f'<circle cx="{xs(half):.1f}" cy="{ys(0.5):.1f}" r="4.5" fill="{INK}"/>')
    # the annotation goes in the empty upper right, never over the curves
    body += wrap(xs(9), ys(0.93),
                 f"Half of all UK companies are off the register by age {half:.1f}. The yearly risk "
                 f"PEAKS in the second year rather than the first, because a company cannot be struck "
                 f"off for not filing until its first accounts are overdue.",
                 size=11.5, fill=INK2, chars=52)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Two-thirds of UK companies are gone within five years", size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="anyone quoting a company survival or failure rate for the UK",
                        decide="which baseline an individual company is being judged against",
                        wrong="five-year survival moves outside the band its cohorts have held")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    foot = ["Sector changes the answer more than anything else here: 17% of retail and wholesale companies reach five "
            "years against 59% of real estate ones.",
            "Leaving the register is not the same as failing. Only 4.5% of departures were in liquidation or "
            "administration a year earlier; the rest were dissolved.",
            "Ages 0-1 disagree between the two measurement years by 6 points, so the first year is the least "
            "trustworthy part of this curve. Every other band agrees within 2."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
