#!/usr/bin/env python3
"""What an Australian drug shortage lasts, against what the register appears to say.

Two curves on one pair of axes. The faint one is the register read naively: the
share of RESOLVED shortages that lasted longer than t, which reaches 50% at about
two months. The bold one is the Kaplan-Meier estimate over every shortage observed in
the last twelve months, current ones included and censored at capture, which reaches
50% at about a year. The gap between the curves is the bias, drawn: the resolved rows
are the short shortages, because the long ones that resolved are already purged and
the long ones still running are not resolved.

See survival.py for why the twelve-month purge window makes this a valid
left-truncated design rather than a hopeless one.
"""
import math
import statistics as st
import sys
sys.path.insert(0, ".")
import shortagelib as S
import survival as V

NAIVE, KM, BAND = "#b9b6ad", "#1b4f8a", "#1b4f8a"


def main():
    subs = V.subjects()
    curve = V.km(subs)
    naive = V.naive_curve(subs)
    med_n = V.median_of_resolved(subs)
    med_k, q25_k = V.quantile(curve, 0.5), V.quantile(curve, 0.25)
    n_ev = sum(1 for s in subs if s["event"])

    # segmentation, stated rather than drawn: injectables against oral solids
    def form(s):
        f = (s["rec"].get("dose_form") or "").lower()
        return "injection" if "injection" in f else ("oral solid" if ("tablet" in f or "capsule" in f) else None)
    seg = {}
    for g in ("injection", "oral solid"):
        gs = [s for s in subs if form(s) == g]
        seg[g] = (V.quantile(V.km(gs), 0.5), len(gs), sum(1 for s in gs if s["event"]))

    XMAX = 4 * 365
    W, L, T, PW, PH = 960, 90, 178, 600, 330
    xs = lambda d: L + PW * min(d, XMAX) / XMAX
    ys = lambda p: T + PH - PH * p
    body = []
    for g in range(0, 101, 25):
        body.append(f'<line x1="{L}" y1="{ys(g/100):.1f}" x2="{L+PW}" y2="{ys(g/100):.1f}" '
                    f'stroke="{S.RULE}" stroke-width="1"/>')
        body.append(S.txt(L - 10, ys(g / 100) + 4, f"{g}%", size=11, fill=S.MUTED, anchor="end", tab=True))
    for yr in range(0, 5):
        body.append(S.txt(xs(yr * 365), T + PH + 20, f"{yr} y" if yr else "start", size=11,
                          fill=S.MUTED, anchor="middle"))
    body.append(S.txt(L - 10, T - 22, "still short", size=11, fill=S.INK2, anchor="end"))
    body.append(S.txt(L + PW, T + PH + 40, "time since the shortage began", size=12,
                      fill=S.INK2, anchor="end"))

    # Greenwood band on the KM curve
    up, lo = [], []
    for t, s_, _r, _e, var in curve:
        se = math.sqrt(var)
        up.append(f"{xs(t):.1f},{ys(min(1, s_ + 1.96 * se)):.1f}")
        lo.append(f"{xs(t):.1f},{ys(max(0, s_ - 1.96 * se)):.1f}")
    body.append(f'<polygon points="{" ".join(up + lo[::-1])}" fill="{BAND}" fill-opacity="0.10"/>')

    def step(points, stroke, width, dash=""):
        d, prev = [], None
        for x, y in points:
            if prev is None:
                d.append(f"M{x:.1f},{y:.1f}")
            else:
                d.append(f"H{x:.1f} V{y:.1f}")
            prev = (x, y)
        return (f'<path d="{" ".join(d)}" fill="none" stroke="{stroke}" stroke-width="{width}" '
                f'{"stroke-dasharray=" + chr(34) + dash + chr(34) if dash else ""}/>')
    body.append(step([(xs(t), ys(p)) for t, p in naive if t <= XMAX], NAIVE, 2, "5,4"))
    body.append(step([(xs(t), ys(s_)) for t, s_, *_ in curve if t <= XMAX], KM, 2.6))

    # medians, drawn as drops to the axis
    for med, col, lab, dy in ((med_n, "#7a776e", f"resolved rows alone: {med_n} days", 0),
                              (med_k, KM, f"every shortage observed: {med_k} days", 0)):
        body.append(f'<line x1="{xs(med):.1f}" y1="{ys(0.5):.1f}" x2="{xs(med):.1f}" y2="{ys(0):.1f}" '
                    f'stroke="{col}" stroke-width="1.2" stroke-dasharray="2,3"/>')
        body.append(f'<circle cx="{xs(med):.1f}" cy="{ys(0.5):.1f}" r="4.5" fill="{col}"/>')
    body.append(S.txt(xs(med_n) + 10, ys(0.5) + 44, "the register's apparent median:", size=11, fill="#7a776e"))
    body.append(S.txt(xs(med_n) + 10, ys(0.5) + 58, f"{med_n} days, from the {n_ev} resolved rows alone",
                      size=11, fill="#7a776e"))
    body.append(S.txt(xs(med_k) + 12, ys(0.5) - 34, f"corrected median: {med_k} days", size=12.5,
                      fill=KM, weight="600"))
    body.append(S.txt(xs(med_k) + 12, ys(0.5) - 19, f"{len(subs)} shortages observed, {n_ev} resolutions",
                      size=11, fill=KM))
    if q25_k:
        body.append(S.txt(xs(q25_k) - 8, ys(0.25) + 18, f"one in four still short at {q25_k/365:.1f} years",
                          size=11, fill=KM, anchor="end"))
    body.append(S.txt(L + PW + 14, ys(0.62), "band: 95% Greenwood", size=10, fill=S.MUTED))
    body.append(S.txt(L + PW + 14, ys(0.62) + 14, "axis cut at four years;", size=10, fill=S.MUTED))
    body.append(S.txt(L + PW + 14, ys(0.62) + 28, "the longest ran 6,538 days", size=10, fill=S.MUTED))

    svg = S.frame(
        W, T + PH + 190,
        "A resolved Australian shortage lasted two months. A shortage lasts about a year.",
        "Share of TGA-listed shortages still unresolved, by time since they began. The dashed "
        "curve is the register read naively — resolved rows only. The solid one counts every "
        "shortage open in the last twelve months, the 409 still running included, censored at "
        "capture. The gap is the purge: long shortages that ended are gone, long ones still "
        "running are not yet resolved.",
        body,
        footer=[
            f"Size a bridge for a year, not two months: half of shortages are still open at "
            f"{med_k} days, and one in four at {q25_k} days.",
            f"Injectables resolve faster here than oral solids — KM medians {seg['injection'][0]} "
            f"against {seg['oral solid'][0]} days ({seg['injection'][2]} and {seg['oral solid'][2]} "
            f"resolutions). TGA's own severity class does not order durations at all.",
            "Australia is the only one of the three registers that can support this: FDA kept "
            "seven resolved rows and France records no start date.",
            "Kaplan-Meier, left-truncated at the window start and right-censored at capture; "
            "discontinuations and anticipated shortages excluded. See survival.py.",
        ])
    print(S.write("3-duration.svg", svg))
    print(f"  naive median {med_n} d | KM median {med_k} d | q25 {q25_k} d | n {len(subs)} events {n_ev} | "
          f"injection {seg['injection']} oral solid {seg['oral solid']}")


if __name__ == "__main__":
    main()
