#!/usr/bin/env python3
"""Whether a company's death is visible before it happens, and for how long.

    python3 chart-6-warning.py

Companies House publishes a status on every live company, and one value of it — "Active -
Proposal to Strike off" — is the registrar saying out loud that it intends to remove the
company. Three snapshots a year apart make it testable.

**A first version drew this as stacked bars: died in year one, died in year two, still
there.** The counts were right and the shape was invisible. Survival curves make the
finding, because the statuses do not differ only in how much risk they carry — they differ
in *when*.

**The strike-off flag is a one-year event.** 48.5% of flagged companies are gone within a
year. Of those that survive it, **12.6% die in the following year — against 11.8% for a
plainly Active company.** Survive a strike-off proposal and you are back to baseline; the
signal is entirely spent. That is why the right-hand panel exists: it puts the first year's
hazard against the second year's, conditional on having survived the first, and the
diagonal is what a constant risk would look like.

**Administration runs the other way**: 26.4% in year one, then **34.8%** among the
survivors. The risk builds. Liquidation is roughly flat. Three different processes, one of
which the stacked bars had drawn as if it were the same as the others.

The lower band is the other half of the story and neither half stands alone: flagged
companies are 8.6% of the register, so **81% of all departures carry no warning at all**.
"""
import collections, csv, gzip, math, os, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
DATA = os.environ.get("FSB_DATA") or os.path.join(HERE, "..", "data")
OUT = os.path.join(HERE, "..", "charts", "6-warning.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
FLAG, CALM = "#b03a2e", "#1b4f8a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
STYLE = {
    "Active - Proposal to Strike off": ("#8c2318", "strike-off proposed", 2.8),
    "Liquidation": ("#b03a2e", "liquidation", 2.0),
    "In Administration": ("#c07a1e", "in administration", 2.0),
    "Active": ("#1b4f8a", "Active, no warning", 2.8),
    "Live but Receiver Manager on at least one charge": ("#7fa8c4", "receiver on a charge", 1.6),
    "Voluntary Arrangement": ("#1b7f5a", "voluntary arrangement", 1.6),
}
FLAGGED = ("Proposal to Strike off", "Liquidation", "Administration", "Receiver", "Voluntary")


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


def read(f):
    with gzip.open(os.path.join(DATA, f), "rt", newline="") as fh:
        yield from csv.DictReader(fh)


def main():
    s24 = {r["number"]: r["status"] for r in read("geo-2024-09-01.csv.gz")}
    s25 = {r["number"] for r in read("geo-2025-09-01.csv.gz")}
    s26 = {r["number"] for r in read("geo-2026-09-01.csv.gz")}
    st = collections.defaultdict(lambda: [0, 0, 0])
    for num, status in s24.items():
        v = st[status]
        v[0] += 1
        v[1] += num in s25
        v[2] += num in s26
    series = []
    for k, (n, a1, a2) in st.items():
        if n < 500 or k not in STYLE:
            continue
        S1, S2 = a1 / n, a2 / n
        series.append({"k": k, "n": n, "S": [1.0, S1, S2], "h1": 1 - S1,
                       "h2": (S1 - S2) / S1 if S1 else 0,
                       "col": STYLE[k][0], "lab": STYLE[k][1], "w": STYLE[k][2]})
    total = sum(v[0] for v in st.values())
    deaths = sum(v[0] - v[2] for v in st.values())
    flag_d = sum(v[0] - v[2] for k, v in st.items() if any(f in k for f in FLAGGED))

    W, H = 1060, 830
    L, T, PW, PH = 92, 208, 296, 300
    RX, RW, RH = 610, 268, 300
    body = []

    # survival curves
    body.append(txt(L, T - 44, "share still on the register", size=12.5, fill=INK, weight="600"))
    body.append(txt(L, T - 28, "from the status it held in September 2024", size=10.5, fill=MUTED))
    lx = lambda t: L + PW * t / 2
    ly = lambda v: T + PH - PH * v
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        body.append(f'<line x1="{L}" y1="{ly(v):.1f}" x2="{L+PW}" y2="{ly(v):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ly(v) + 4, f"{v:.0%}", size=11, fill=MUTED, anchor="end"))
    for t, lab in ((0, "2024"), (1, "2025"), (2, "2026")):
        body.append(f'<line x1="{lx(t):.1f}" y1="{T}" x2="{lx(t):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
        body.append(txt(lx(t), T + PH + 20, lab, size=11, fill=MUTED, anchor="middle"))
    placed = []
    for d in sorted(series, key=lambda d: -d["S"][2]):
        p = " ".join(f"{'M' if i==0 else 'L'}{lx(i):.1f},{ly(v):.1f}" for i, v in enumerate(d["S"]))
        body.append(f'<path d="{p}" fill="none" stroke="{d["col"]}" stroke-width="{d["w"]}"/>')
        for i, v in enumerate(d["S"][1:], start=1):
            body.append(f'<circle cx="{lx(i):.1f}" cy="{ly(v):.1f}" r="3" fill="{d["col"]}"/>')
        ty = ly(d["S"][2]) + 4
        while any(abs(ty - q) < 14 for q in placed):
            ty += 14
        placed.append(ty)
        body += halo(lx(2) + 8, ty, f"{d['lab']}  {d['S'][2]:.0%}", size=10.5, fill=d["col"])

    # hazard panel
    body.append(txt(RX, T - 44, "when the risk actually falls", size=12.5, fill=INK, weight="600"))
    body.append(txt(RX, T - 28, "year one against year two, among those who survived year one",
                    size=10.5, fill=MUTED))
    HI = 0.55
    hx = lambda v: RX + RW * min(v, HI) / HI
    hy = lambda v: T + RH - RH * min(v, HI) / HI
    for t in (0, 0.1, 0.2, 0.3, 0.4, 0.5):
        body.append(f'<line x1="{hx(t):.1f}" y1="{T}" x2="{hx(t):.1f}" y2="{T+RH}" stroke="{GRID}"/>')
        body.append(txt(hx(t), T + RH + 20, f"{t:.0%}", size=10, fill=MUTED, anchor="middle"))
        body.append(f'<line x1="{RX}" y1="{hy(t):.1f}" x2="{RX+RW}" y2="{hy(t):.1f}" stroke="{GRID}"/>')
        body.append(txt(RX - 8, hy(t) + 4, f"{t:.0%}", size=10, fill=MUTED, anchor="end"))
    body.append(f'<line x1="{hx(0):.1f}" y1="{hy(0):.1f}" x2="{hx(HI):.1f}" y2="{hy(HI):.1f}" '
                f'stroke="{INK}" stroke-width="1.3"/>')
    body += halo(hx(0.30), hy(0.30) - 9, "same risk both years", size=10, fill=INK, anchor="end")
    nmax = max(d["n"] for d in series)
    for d in sorted(series, key=lambda d: -d["n"]):
        r = 3 + 9 * (d["n"] / nmax) ** 0.5
        body.append(f'<circle cx="{hx(d["h1"]):.1f}" cy="{hy(d["h2"]):.1f}" r="{r:.1f}" '
                    f'fill="{d["col"]}" fill-opacity="0.4" stroke="{d["col"]}" stroke-width="1.1"/>')
    hp = []
    for d in sorted(series, key=lambda d: -d["h1"]):
        ty = hy(d["h2"]) + 4
        while any(abs(ty - q) < 13 for q in hp):
            ty += 13
        hp.append(ty)
        body += halo(hx(d["h1"]) + 10, ty, d["lab"], size=10, fill=d["col"])
    body.append(txt(RX + RW / 2, T + RH + 44, "died in year one", size=11, fill=INK2, anchor="middle"))
    body.append(txt(RX - 8, T - 12, "died in year two,", size=10.5, fill=INK2, anchor="end"))
    body.append(txt(RX - 8, T + 2, "having survived year one", size=10.5, fill=INK2, anchor="end"))

    cy = T + PH + 96
    body.append(txt(92, cy, "and where the departures actually came from", size=12.5, fill=INK, weight="600"))
    body.append(txt(92, cy + 16, f"all {deaths/1e6:.2f} million of them, by the status held in 2024",
                    size=10.5, fill=MUTED))
    bx, by, bw = 92, cy + 32, W - 184
    x = bx
    for val, col, lab in ((1 - flag_d / deaths, CALM, "no warning: plainly Active in 2024"),
                          (flag_d / deaths, FLAG, "flagged in some way")):
        w = bw * val
        body.append(f'<rect x="{x:.1f}" y="{by:.1f}" width="{w:.1f}" height="32" fill="{col}"/>')
        body.append(txt(x + w / 2, by + 22, f"{val:.0%}", size=14, fill="#ffffff",
                        anchor="middle", weight="700"))
        body.append(txt(x + (6 if val > 0.5 else w - 6), by + 48, lab, size=10.5, fill=col,
                        anchor="start" if val > 0.5 else "end"))
        x += w

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Survive a strike-off proposal and you are back to an ordinary company's risk",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="a creditor or counterparty reading a strike-off notice",
                        decide="whether a discontinued strike-off still signals elevated risk",
                        wrong="hazard after discontinuance stays above the ordinary baseline")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    ps = next(d for d in series if "Strike" in d["k"])
    ac = next(d for d in series if d["k"] == "Active")
    foot = [f"A strike-off proposal is a one-year event: {ps['h1']:.0%} die in year one, then "
            f"{ps['h2']:.0%} of the survivors in year two — against {ac['h2']:.0%} for a company never "
            f"flagged. Administration is the opposite, 26% rising to 35%.",
            f"So the flag is worth acting on immediately and worth little after twelve months. The "
            f"absence of a flag is worth almost nothing: {1-flag_d/deaths:.0%} of departures never had one.",
            f"{total:,} companies, {deaths:,} departures. A death is a disappearance between snapshots; "
            f"the register publishes no dissolution date for the living."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for d in sorted(series, key=lambda d: -d["n"]):
        print(f"    {d['lab']:<34}h1 {d['h1']:>6.1%}   h2|alive {d['h2']:>6.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
