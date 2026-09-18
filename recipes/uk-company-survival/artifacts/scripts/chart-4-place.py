#!/usr/bin/env python3
"""How much of a place's dormant-company share is its industries, and how much is the place.

    python3 chart-4-place.py

ONS publishes company survival by local authority, so this recipe does not draw that. What
nobody publishes is the **denominator**: ONS counts enterprises, meaning things that trade
or employ, while Companies House counts companies, including those that exist only to hold
something. The share of a place's mature companies filing as DORMANT is that gap measured
on one side.

**The first version of this figure put dormancy against survival on zoomed axes and was
wrong twice.** The two are nearly independent (r = +0.12), so the vertical axis carried no
information; and the frame, 8 to 24% by 78 to 92%, made a modest spread look dramatic.

It is redrawn the way figure 5 is, and for the same reason. A raw dormancy share confounds
the place with what the place is made of: professional services file dormant at 15.7% and
extraterritorial households at 36.9%, so an area thick with consultancies will look
different without anything about the area differing. The horizontal axis is what each
area's dormancy **would** be if every one of its sector-by-vintage cells filed dormant at
the national rate for that cell. The vertical is how far from that it landed.

Composition explains **29%** of the variation and leaves 71%. Edinburgh files 12.0% dormant
where its mix predicts 20.1%, and it is not alone -- Dundee, Kilmarnock and Inverness sit
with it. London and Harrogate sit as far the other way. **How a country uses the limited
company differs by region**, and that is not a fact about its industries.
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
OUT = os.path.join(HERE, "..", "charts", "4-place.svg")
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
XLO, XHI, YLO, YHI = 0.115, 0.21, -0.09, 0.055


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
    rows = list(read(os.path.join(DATA, "geo-2024-09-01.csv.gz")))
    pc = collections.Counter(r["postcode"] for r in rows if r["postcode"])
    agents = {p for p, _ in pc.most_common(AGENT_TOP)}
    cells = collections.defaultdict(lambda: [0, 0])
    recs, secdorm = [], collections.defaultdict(lambda: [0, 0])
    for r in rows:
        y = (r["incorp"] or "")[:4]
        if not r["area"] or r["postcode"] in agents or not y.isdigit() or int(y) > MATURE_BY:
            continue
        sec = section(r["sic"]) or "?"
        key = (sec, min(max((2024 - int(y)) // 5, 0), 5))
        dorm = (r["accounts"] or "").strip().upper() == "DORMANT"
        cells[key][0] += 1
        cells[key][1] += dorm
        secdorm[sec][0] += 1
        secdorm[sec][1] += dorm
        recs.append((r["area"], key, dorm))
    agg = collections.defaultdict(lambda: [0, 0, 0.0])
    for a, key, dorm in recs:
        v = agg[a]
        v[0] += 1
        v[1] += dorm
        n, d = cells[key]
        v[2] += d / n
    pts = [{"a": a, "n": v[0], "obs": v[1] / v[0], "exp": v[2] / v[0], "reg": AREA_REGION.get(a)}
           for a, v in agg.items() if v[0] >= MIN_AREA]
    o = [p["obs"] for p in pts]
    res = [p["obs"] - p["exp"] for p in pts]
    explained = 1 - st.pvariance(res) / st.pvariance(o)

    W, H, L, T, PW, PH = 1020, 796, 128, 208, 494, 408
    lx = lambda v: L + PW * (min(max(v, XLO), XHI) - XLO) / (XHI - XLO)
    ly = lambda v: T + PH - PH * (min(max(v, YLO), YHI) - YLO) / (YHI - YLO)
    body = []
    for t in (0.12, 0.14, 0.16, 0.18, 0.20):
        body.append(f'<line x1="{lx(t):.1f}" y1="{T}" x2="{lx(t):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
        body.append(txt(lx(t), T + PH + 20, f"{t:.0%}", size=11, fill=MUTED, anchor="middle"))
    for t in (-0.08, -0.06, -0.04, -0.02, 0.0, 0.02, 0.04):
        body.append(f'<line x1="{L}" y1="{ly(t):.1f}" x2="{L+PW}" y2="{ly(t):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ly(t) + 4, f"{t:+.0%}" if t else "0", size=11, fill=MUTED, anchor="end"))
    body.append(txt(L + PW / 2, T + PH + 46, "dormant share its own mix of companies predicts",
                    size=12, fill=INK2, anchor="middle"))
    body.append(txt(L - 10, T - 50, "percentage points", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - 36, "more dormant", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - 22, "than predicted", size=11, fill=INK2, anchor="end"))
    body.append(f'<line x1="{L}" y1="{ly(0):.1f}" x2="{L+PW}" y2="{ly(0):.1f}" '
                f'stroke="{INK}" stroke-width="1.5"/>')
    body += halo(L + 6, ly(0) - 8, "exactly what its mix of companies predicts", size=10.5, fill=INK)

    nmax = max(p["n"] for p in pts)
    for p in sorted(pts, key=lambda p: -p["n"]):
        col = GROUP.get(p["reg"], "#9a988f")
        r = 2.4 + 9.5 * (p["n"] / nmax) ** 0.5
        body.append(f'<circle cx="{lx(p["exp"]):.1f}" cy="{ly(p["obs"]-p["exp"]):.1f}" r="{r:.1f}" '
                    f'fill="{col}" fill-opacity="0.34" stroke="{col}" stroke-opacity="0.8" '
                    f'stroke-width="0.9"/>')
    ranked = sorted(pts, key=lambda p: p["obs"] - p["exp"])
    placed = []
    for p in ranked[:5] + ranked[-5:]:
        col = GROUP.get(p["reg"], "#9a988f")
        d = p["obs"] - p["exp"]
        up = d < 0
        tx_, ty_ = lx(p["exp"]) + 10, ly(d) + (-8 if up else 4)
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
                 "A dormant company is one that told Companies House it did not trade. Where a place "
                 "sits above this line, more of its companies say that than its industries can "
                 "account for.", size=11, fill=INK2, chars=30, leading=14)
    body += wrap(L + PW + 26, T + 104,
                 f"Sector and vintage explain {explained:.0%} of the variation. The other "
                 f"{1-explained:.0%} is how a place uses the company form — and the Scottish cities "
                 f"sit together at one end, London and Harrogate at the other.",
                 size=11, fill=INK, chars=30, leading=14)
    top = sorted(secdorm.items(), key=lambda kv: -kv[1][1] / kv[1][0])
    top = [(k, v) for k, v in top if v[0] > 50000 and k != "?"][:3]
    body += wrap(L + PW + 26, T + 232,
                 "Dormancy by sector nationally: " +
                 ", ".join(f"{k.lower()} {v[1]/v[0]:.0%}" for k, v in top) +
                 " — which is what the horizontal axis is holding fixed.",
                 size=10.5, fill=MUTED, chars=32, leading=13)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Scotland's companies trade. London's and Harrogate's hold things.",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="a regional development body comparing company bases",
                        decide="whether a high local company count means real local activity",
                        wrong="holding-company share stops separating the regions")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    worst, best = ranked[-1], ranked[0]
    foot = [f"{best['a']} files {best['obs']:.1%} dormant against the {best['exp']:.1%} its mix "
            f"predicts; {worst['a']} files {worst['obs']:.1%} against {worst['exp']:.1%}. Before "
            f"repeating a company-formation figure for a place, that is what 'a company' means there.",
            "ONS already publishes survival by local authority, so this recipe does not. It publishes "
            "the denominator instead: how much of a place's company count is a company at all.",
            f"{len(pts)} areas, {sum(p['n'] for p in pts):,} companies incorporated by {MATURE_BY}. "
            f"Dormancy is a filing status, not an audit: it records what a company told the registrar."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}  ({len(pts)} areas)")
    print(f"  sector/vintage explains {explained:.0%}; {best['a']} {best['obs']-best['exp']:+.1%} "
          f"to {worst['a']} {worst['obs']-worst['exp']:+.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
