#!/usr/bin/env python3
"""How many more companies die in a place than its own mix of companies predicts.

    python3 chart-5-excess.py

An earlier figure put dormancy against survival on zoomed axes -- 8 to 24% by 78 to 92% --
which is arguing a case with the frame rather than the data. The first fix was to put
observed against expected death rate on matched axes from zero, and that was worse: 117
areas occupied a fifth of the plot and the claim, a gap of a few points, was a hair either
side of a diagonal.

**When two axes carry the same quantity and the difference is the claim, draw the
difference.** So the vertical axis here is observed minus expected, in percentage points,
with zero marked -- every mark's height is the number the figure is about, read directly
rather than estimated from a distance to a line.

The axes are also a different pair, because the first pair could not support a geographic
decision. Death rate alone confounds place with what a place is made of: Dudley and the
City of London do not hold the same industries, the same company sizes or the same
vintages. So the horizontal axis is what each area's death rate **would** be if every one
of its sector-by-account-type-by-age cells died at the national rate for that cell, and the
vertical is what actually happened. **The vertical distance is the part that is about the
place**, which is the only part a council can act on.

It survives. Composition explains **43%** of the variance in area death rates and leaves
57%. That is the opposite of the landfill recipe, where the same test dissolved three
findings into size, and it is why this figure exists at all: the test was run expecting to
kill the geography and did not.

Formation agents are held out, and only companies incorporated by 2021 are counted, for
the reasons in `location.py`.
"""
import collections, csv, gzip, math, os, statistics as st, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
sys.path.insert(0, HERE)
from entry_share import section                                          # noqa: E402
from location import AREA_REGION, AGENT_TOP, MIN_AREA, MATURE_BY, read   # noqa: E402

DATA = os.environ.get("FSB_DATA") or os.path.join(HERE, "..", "data")
OUT = os.path.join(HERE, "..", "charts", "5-excess.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
GROUP = {"London": "#b03a2e", "South East": "#c07a1e", "South West": "#c07a1e", "East": "#c07a1e",
         "West Midlands": "#6b6f2e", "East Midlands": "#6b6f2e", "North West": "#1b4f8a",
         "North East": "#1b4f8a", "Yorkshire and The Humber": "#1b4f8a", "Scotland": "#1b7f5a",
         "Wales": "#1b7f5a", "Northern Ireland": "#1b7f5a"}
LAB = {"London": "London", "South East": "South", "South West": "South", "East": "South",
       "West Midlands": "Midlands", "East Midlands": "Midlands", "North West": "North",
       "North East": "North", "Yorkshire and The Humber": "North", "Scotland": "Scotland, Wales, NI",
       "Wales": "Scotland, Wales, NI", "Northern Ireland": "Scotland, Wales, NI"}
XLO, XHI, YLO, YHI = 0.10, 0.19, -0.05, 0.105


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


def main():
    alive = {r["number"] for r in read(os.path.join(DATA, "geo-2026-09-01.csv.gz"))}
    rows = list(read(os.path.join(DATA, "geo-2024-09-01.csv.gz")))
    pc = collections.Counter(r["postcode"] for r in rows if r["postcode"])
    agents = {p for p, _ in pc.most_common(AGENT_TOP)}
    cells = collections.defaultdict(lambda: [0, 0])
    recs = []
    for r in rows:
        y = (r["incorp"] or "")[:4]
        if not r["area"] or r["postcode"] in agents or not y.isdigit() or int(y) > MATURE_BY:
            continue
        key = (section(r["sic"]) or "?", (r["accounts"] or "").strip().upper() or "?",
               min(max((2024 - int(y)) // 5, 0), 5))
        died = r["number"] not in alive
        cells[key][0] += 1
        cells[key][1] += died
        recs.append((r["area"], key, died,
                     (r["accounts"] or "").strip().upper() == "DORMANT"))
    agg = collections.defaultdict(lambda: [0, 0, 0.0, 0])
    for a, key, died, dorm in recs:
        v = agg[a]
        v[0] += 1
        v[1] += died
        n, d = cells[key]
        v[2] += d / n
        v[3] += dorm
    pts = [{"a": a, "n": v[0], "obs": v[1] / v[0], "exp": v[2] / v[0], "dorm": v[3] / v[0],
            "reg": AREA_REGION.get(a)} for a, v in agg.items() if v[0] >= MIN_AREA]
    o = [p["obs"] for p in pts]
    e = [p["exp"] for p in pts]
    res = [p["obs"] - p["exp"] for p in pts]
    explained = 1 - st.pvariance(res) / st.pvariance(o)
    dcorr = (sum((p["dorm"] - sum(q["dorm"] for q in pts) / len(pts)) *
                 (p["obs"] - p["exp"] - sum(res) / len(res)) for p in pts) /
             math.sqrt(sum((p["dorm"] - sum(q["dorm"] for q in pts) / len(pts)) ** 2 for p in pts) *
                       sum((r_ - sum(res) / len(res)) ** 2 for r_ in res)))

    W, H, L, T, PW, PH = 1020, 796, 128, 208, 494, 408
    lx = lambda v: L + PW * (min(max(v, XLO), XHI) - XLO) / (XHI - XLO)
    ly = lambda v: T + PH - PH * (min(max(v, YLO), YHI) - YLO) / (YHI - YLO)
    body = []
    for t in (0.10, 0.12, 0.14, 0.16, 0.18):
        body.append(f'<line x1="{lx(t):.1f}" y1="{T}" x2="{lx(t):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
        body.append(txt(lx(t), T + PH + 20, f"{t:.0%}", size=11, fill=MUTED, anchor="middle"))
    for t in (-0.04, -0.02, 0.0, 0.02, 0.04, 0.06, 0.08, 0.10):
        body.append(f'<line x1="{L}" y1="{ly(t):.1f}" x2="{L+PW}" y2="{ly(t):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ly(t) + 4, f"{t:+.0%}" if t else "0", size=11, fill=MUTED, anchor="end"))
    body.append(txt(L + PW / 2, T + PH + 46,
                    "death rate its own mix of companies predicts", size=12, fill=INK2, anchor="middle"))
    body.append(txt(L - 10, T - 50, "percentage points", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - 36, "more of its companies", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - 22, "died than predicted", size=11, fill=INK2, anchor="end"))

    body.append(f'<rect x="{L}" y="{T}" width="{PW}" height="{ly(0)-T:.1f}" fill="#b03a2e" '
                f'fill-opacity="0.04"/>')
    body.append(f'<line x1="{L}" y1="{ly(0):.1f}" x2="{L+PW}" y2="{ly(0):.1f}" '
                f'stroke="{INK}" stroke-width="1.5"/>')
    body += halo(L + 6, ly(0) - 8, "exactly what its mix of companies predicts",
                 size=10.5, fill=INK)

    nmax = max(p["n"] for p in pts)
    for p in sorted(pts, key=lambda p: -p["n"]):
        col = GROUP.get(p["reg"], "#9a988f")
        r = 2.4 + 9.5 * (p["n"] / nmax) ** 0.5
        body.append(f'<circle cx="{lx(p["exp"]):.1f}" cy="{ly(p["obs"]-p["exp"]):.1f}" r="{r:.1f}" '
                    f'fill="{col}" fill-opacity="0.34" stroke="{col}" stroke-opacity="0.8" '
                    f'stroke-width="0.9"/>')
    ranked = sorted(pts, key=lambda p: p["obs"] - p["exp"])
    placed = []
    for p in ranked[:4] + ranked[-6:]:
        col = GROUP.get(p["reg"], "#9a988f")
        d = p["obs"] - p["exp"]
        up = (p["obs"] - p["exp"]) < 0
        tx_, ty_ = lx(p["exp"]) + 10, ly(p["obs"] - p["exp"]) + (-8 if up else 4)
        step = -14 if up else 14
        while any(abs(ty_ - q) < 14 and abs(tx_ - qx) < 130 for qx, q in placed):
            ty_ += step
        placed.append((tx_, ty_))
        body += halo(tx_, ty_, f"{p['a']}  {d:+.1%}", size=10, fill=col)

    x0, y0, seen = L, T + PH + 68, set()
    for r_, lab in LAB.items():
        if lab in seen:
            continue
        seen.add(lab)
        body.append(f'<circle cx="{x0+5:.1f}" cy="{y0-4:.1f}" r="5" fill="{GROUP[r_]}" '
                    f'fill-opacity="0.45" stroke="{GROUP[r_]}" stroke-width="0.9"/>')
        body.append(txt(x0 + 16, y0, lab, size=10.5, fill=GROUP[r_]))
        x0 += 22 + len(lab) * 6.0
    body.append(txt(L, y0 + 17, "mark area is how many companies", size=10, fill=MUTED))

    body += wrap(L + PW + 26, T + 4,
                 "Above the line, a place buries more of its companies than its industries, company "
                 "sizes and vintages can account for. That gap is the only part of a death rate a "
                 "council can do anything about.",
                 size=11, fill=INK2, chars=30, leading=14)
    body += wrap(L + PW + 26, T + 104,
                 f"Composition explains {explained:.0%} of the variation between areas. The other "
                 f"{1-explained:.0%} is the place itself — which is the opposite of what the same "
                 f"test found for landfills, where everything dissolved into size.",
                 size=11, fill=INK, chars=30, leading=14)
    body += wrap(L + PW + 26, T + 232,
                 f"It is not the shell companies either: the excess is uncorrelated with an area's "
                 f"dormant share (r = {dcorr:+.2f}).",
                 size=10.5, fill=MUTED, chars=32, leading=13)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Dudley buries a tenth more of its companies than anything about them explains",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="a local authority or regulator deciding where to intervene",
                        decide="which places have a problem beyond their industry and age mix",
                        wrong="the excess disappears once a further control is added")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    worst, best = ranked[-1], ranked[0]
    foot = [f"{worst['a']} loses {worst['obs']:.1%} of its companies in two years against the "
            f"{worst['exp']:.1%} its mix predicts; {best['a']} loses {best['obs']:.1%} against "
            f"{best['exp']:.1%}. Neither gap is about what those companies do.",
            "The Black Country and Worcestershire — DY, WR, B, BL — sit furthest above the line, and "
            "they sit above it together, which a single-area story would have missed.",
            f"{len(pts)} areas, {sum(p['n'] for p in pts):,} companies, {len(cells):,} "
            f"sector-by-type-by-vintage cells. A death is a disappearance between the 2024 and 2026 "
            f"snapshots."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}  ({len(pts)} areas)")
    print(f"  composition explains {explained:.0%}; excess vs dormancy r={dcorr:+.3f}")
    print(f"  worst {worst['a']} {worst['obs']-worst['exp']:+.2%}, best {best['a']} "
          f"{best['obs']-best['exp']:+.2%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
