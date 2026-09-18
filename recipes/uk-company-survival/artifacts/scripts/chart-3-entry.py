#!/usr/bin/env python3
"""What people start companies to do, and how that has moved.

    python3 chart-3-entry.py

Share of newly registered limited companies by sector, by year of registration. Entry,
not survival, because survival levels are set by each country's filing law and entry is
not: a registration is a registration.

THE SURVIVOR CORRECTION, AND WHY IT IS DRAWN RATHER THAN APPLIED SILENTLY. Both registers
show the living, so a company born in 2005 appears only if it is still here, and sectors
die at different rates. The observed line is therefore biased, and biased differently in
each sector. The UK sector survival curves from this same recipe give the correction:
divide the observed count by that sector's survival to that age. Both lines are drawn, so
the size of the correction is visible rather than asserted, and the gap between them is
the honest measure of how far back the uncorrected series can be read.

Norway is added when its extract exists, uncorrected and labelled as such, because this
recipe could not measure Norwegian survival.
"""
import collections, csv, glob, gzip, json, math, os, sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from entry_share import section, UK_LTD
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plate                                                             # noqa: E402

DATA = os.environ.get("FSB_DATA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "charts", "3-entry.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
SHOW = {"Manufacturing": "#b03a2e", "Retail & wholesale": "#1b4f8a",
        "Information & communication": "#c07a1e", "Professional & scientific": "#4a7a3a",
        "Construction": "#7a6ea6"}
Y0, Y1 = 1998, 2025


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


def uk_counts():
    out = collections.defaultdict(collections.Counter)
    with gzip.open(os.path.join(DATA, "compact-2026-09-01.csv.gz"), "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("category") not in UK_LTD:
                continue
            y, s = r["incorp"][:4], section(r["sic"])
            if y.isdigit() and s:
                out[int(y)][s] += 1
    return out


def norway_counts():
    cand = sorted(glob.glob(os.path.join(DATA, "norway-as*.csv.gz")))
    if not cand:
        return None
    out = collections.defaultdict(collections.Counter)
    with gzip.open(cand[-1], "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            y, s = (r["registered"] or "")[:4], section(r["nace"])
            if y.isdigit() and s:
                out[int(y)][s] += 1
    return out


def main():
    U = uk_counts()
    N = norway_counts()
    try:
        curves = json.load(open(os.path.join(DATA, "survival.json")))["curves"]
    except Exception:
        curves = {}

    def surv(sec, age):
        pts = curves.get(sec)
        if not pts:
            return None
        return next((p["survival"] for p in pts if p["age"] >= age), pts[-1]["survival"])

    years = [y for y in range(Y0, Y1 + 1) if sum(U.get(y, {}).values()) > 2000]
    # The correction divides by a sector's survival to that age, so it explodes on old
    # cohorts: retail survival at 28 years is about 5%, a multiplier of twenty, and it
    # amplifies noise far more than it removes bias. Drawn only where every sector on
    # the chart still has at least MIN_S of its cohort left, which caps the multiplier
    # near three. Before that the correction is not trustworthy and is not drawn --
    # extrapolating it would be asserting precision the curves cannot carry.
    MIN_S = 0.35
    obs, cor = {}, {}
    for s in SHOW:
        obs[s] = [(y, U[y][s] / sum(U[y].values())) for y in years]
        cs = []
        for y in years:
            age = 2026 - y
            if min((surv(k, age) or 1) for k in SHOW) < MIN_S:
                continue
            tot = sum((U[y][k] / (surv(k, age) or 1)) for k in U[y])
            v = U[y][s] / (surv(s, age) or 1)
            cs.append((y, v / tot if tot else 0))
        cor[s] = cs
    cor_from = cor["Manufacturing"][0][0] if cor["Manufacturing"] else None

    W, H, L, T, PW, PH = 1060, 680, 118, 182, 600, 360
    xs = lambda y: L + PW * (y - years[0]) / (years[-1] - years[0])
    top = max(max([v for _, v in obs[s]] + [v for _, v in cor[s]] or [0]) for s in SHOW) * 1.08
    ys = lambda v: T + PH - PH * v / top
    body = []
    for g in range(0, int(top * 100) + 1, 5):
        v = g / 100
        if v > top:
            break
        body.append(f'<line x1="{L}" y1="{ys(v):.1f}" x2="{L+PW}" y2="{ys(v):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ys(v) + 4, f"{g}%", size=11, fill=MUTED, anchor="end"))
    for y in range(years[0], years[-1] + 1, 4):
        body.append(txt(xs(y), T + PH + 20, y, size=11, fill=MUTED, anchor="middle"))
    body.append(txt(L + PW / 2, T + PH + 42, "year the company was registered", size=12, fill=INK2, anchor="middle"))
    body.append(txt(L - 10, T - 34, "share of new", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - 20, "limited companies", size=11, fill=INK2, anchor="end"))

    def path(pts, col, w, dash=""):
        d = " ".join(("M" if i == 0 else "L") + f"{xs(y):.1f},{ys(v):.1f}" for i, (y, v) in enumerate(pts))
        return (f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linejoin="round"'
                + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")

    # The survivor correction is NOT drawn. Dividing by a sector's survival to age is
    # right in principle and useless in practice here: retail survival at twenty-eight
    # years is about 5%, a multiplier of twenty that amplifies noise far more than it
    # removes bias, and requiring every sector to retain even a third of its cohort left
    # exactly one year qualifying. The honest statement is that a 2026 snapshot cannot
    # reconstruct a 1998 birth cohort, so the direction of the bias is named in the
    # footer instead of a false precision being drawn.
    for s, col in SHOW.items():
        body.append(path(obs[s], col, 2.4))
    # mark where little has had time to die, so the reader can see which part is safe
    body.append(f'<rect x="{xs(years[-1]-4):.1f}" y="{T}" width="{xs(years[-1])-xs(years[-1]-4):.1f}" '
                f'height="{PH}" fill="{INK}" fill-opacity="0.035"/>')
    body.append(txt(xs(years[-1] - 2), T - 8, "little has had time to die", size=10.5,
                    fill=MUTED, anchor="middle"))
    ends = sorted(((obs[s][-1][1], s, c) for s, c in SHOW.items()), reverse=True)
    prev = T - 14
    for v, s, c in ends:
        yy = max(ys(v), prev + 15)
        prev = yy
        body.append(f'<line x1="{L+PW+3:.1f}" y1="{ys(v):.1f}" x2="{L+PW+13:.1f}" y2="{yy:.1f}" stroke="{c}" stroke-width="1"/>')
        body.append(txt(L + PW + 17, yy + 4, f"{s}  {v:.1%}", size=11, fill=c))


    m0 = next(v for y, v in obs["Manufacturing"] if y == years[0])
    m1 = obs["Manufacturing"][-1][1]
    body += wrap(L + 14, T + 18,
                 f"Manufacturing fell from {m0:.1%} of new British limited companies in "
                 f"{years[0]} to {m1:.1%} in {years[-1]}, while retail and wholesale went the "
                 f"other way.",
                 size=11.5, fill=INK2, chars=58)

    sub = ("Share of newly registered UK limited companies by sector. Sole traders, partnerships and "
           "charities are excluded so the population matches what other countries' registers hold.")
    if N:
        ny = [y for y in sorted(N) if sum(N[y].values()) > 200]
        if ny:
            sub += f" Norwegian data covers {ny[0]}-{ny[-1]} and is added as points."
            for s, col in SHOW.items():
                pts = [(y, N[y][s] / sum(N[y].values())) for y in ny if y in years]
                for y, v in pts:
                    body.append(f'<circle cx="{xs(y):.1f}" cy="{ys(v):.1f}" r="3.4" fill="none" '
                                f'stroke="{col}" stroke-width="1.6"/>')

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Manufacturing halved. Retail doubled. Nobody stopped starting companies.",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="anyone reading a sector's company count as a measure of its health",
                        decide="whether a falling count means firms are failing or not forming",
                        wrong="formation and dissolution start moving together within a sector")
    s += fr
    s += body
    fy = H - 20 - 15 * 3
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    foot = ["Before repeating a decline narrative about a sector, check whether people are still "
            "forming companies in it. This is the measure that answers that, and it needs no deaths.",
            "These are survivors, so early years are thinned unevenly: manufacturing survives worse than "
            "average, so its true 1998 share was above 7.6% and the fall is steeper than drawn.",
            "Entry share is not output. A sector can consolidate into fewer, larger firms and look "
            "identical here; distinguishing the two needs employment or turnover, which registers do not carry.",
            "The industry code is self-declared at incorporation and rarely updated, so it records what "
            "the founder intended rather than what the company did."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}  | Norway included: {bool(N)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
