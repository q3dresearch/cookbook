#!/usr/bin/env python3
"""The register against the official series: does this method survive a second opinion?

    python3 chart-2-official.py

One dot per industry, the Office for National Statistics on one axis and this recipe on
the other. The diagonal is where the two would agree exactly.

THE DIAGONAL IS NOT THE EXPECTATION, and drawing it without saying so would assert a
claim this recipe does not make. The two count different populations: the register holds
every company including dormant shells that never traded, while the official series
counts enterprises registered for VAT or PAYE. Points SHOULD fall below the line. What
has to agree is the ordering, and the ordering is the test.
"""
import json, os, sys
from xml.sax.saxutils import escape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plate                                                             # noqa: E402

DATA = os.environ.get("FSB_DATA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "charts", "2-official.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
COOL, HOT = "#1b4f8a", "#b03a2e"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


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
    d = json.load(open(os.path.join(DATA, "ons_compare.json")))
    secs = d["sectors"]
    W, H, L, T, S = 1060, 690, 104, 168, 400
    lo, hi = 0.10, 0.65
    xs = lambda v: L + S * (v - lo) / (hi - lo)
    ys = lambda v: T + S - S * (v - lo) / (hi - lo)
    body = []
    for g in range(10, 70, 10):
        v = g / 100
        body.append(f'<line x1="{xs(v):.1f}" y1="{T}" x2="{xs(v):.1f}" y2="{T+S}" stroke="{GRID}"/>')
        body.append(f'<line x1="{L}" y1="{ys(v):.1f}" x2="{L+S}" y2="{ys(v):.1f}" stroke="{GRID}"/>')
        body.append(txt(xs(v), T + S + 20, f"{g}%", size=11, fill=MUTED, anchor="middle"))
        body.append(txt(L - 10, ys(v) + 4, f"{g}%", size=11, fill=MUTED, anchor="end"))
    body.append(f'<line x1="{xs(lo):.1f}" y1="{ys(lo):.1f}" x2="{xs(hi):.1f}" y2="{ys(hi):.1f}" '
                f'stroke="{INK}" stroke-width="1.1" stroke-dasharray="4,4"/>')
    body.append(txt(xs(0.60) + 6, ys(0.60) - 6, "equal survival", size=11, fill=INK2))
    body.append(txt(xs(0.60) + 6, ys(0.60) + 9, "— not the expectation", size=10.5, fill=MUTED))
    body.append(txt(L + S / 2, T + S + 44, "official series: enterprises registered for VAT or PAYE",
                    size=12, fill=INK2, anchor="middle"))
    body.append(txt(L - 10, T - 38, "this recipe:", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - 24, "companies on", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - 10, "the register", size=11, fill=INK2, anchor="end"))

    # Labels sit to the RIGHT of every dot with a leader line back to it. A first version
    # alternated sides and cascaded downwards on collision, which walked four labels so
    # far from their points that the chart asserted the wrong sector for the wrong dot --
    # worse than no label. A leader line makes the association impossible to misread.
    placed = []
    for s in sorted(secs, key=lambda s: ys(s["register"])):
        x, y = xs(s["ons"]), ys(s["register"])
        above = s["register"] > s["ons"]
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{HOT if above else COOL}" '
                    f'fill-opacity="0.85"/>')
        ly = y + 3.5
        while any(abs(ly - q) < 12.5 for q in placed):
            ly += 12.5
        placed.append(ly)
        lx = x + 11
        if abs(ly - (y + 3.5)) > 2:
            body.append(f'<path d="M{x+6:.1f} {y:.1f} L{lx-3:.1f} {ly-3.5:.1f}" stroke="{MUTED}" '
                        f'stroke-width="0.8"/>')
        body.append(txt(lx, ly, s["sector"], size=10.5,
                        fill=HOT if above else INK2, anchor="start"))

    body += wrap(L + S + 168, T + 10,
                 f"Eleven of fourteen industries sit below the line, and the ranking agrees at "
                 f"rho {d['rank_correlation']:+.2f}. Two populations, two definitions of death and "
                 f"two periods, and they order industries the same way.",
                 size=11.5, fill=INK2, chars=32)
    body += wrap(L + S + 168, T + 118,
                 "The three above the line are the sectors full of dormant holding structures — a "
                 "property vehicle or a holding company sits on the register for years without ever "
                 "being a VAT or PAYE enterprise, so the register keeps it alive and the official "
                 "series never counted it born.",
                 size=11.5, fill=HOT, chars=32)
    body += wrap(L + S + 168, T + 268,
                 "Retail is the largest gap in the other direction, which is where cheap incorporation "
                 "and quick strike-off concentrate.",
                 size=11.5, fill=COOL, chars=32)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "The register agrees with the official series about the order, not the level",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="anyone reconciling Companies House against ONS business demography",
                        decide="which source to quote for a level, and which for a trend",
                        wrong="the two series diverge in direction rather than only in level")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    foot = [f"Overall the register says {d['register_5yr']:.1%} against the official {d['ons_total_5yr']:.1%}. "
            f"Lower was the prediction, because the register counts shells the official series never sees.",
            "This is a check, not a calibration. Nothing in the recipe was adjusted to fit the official "
            "series, and the residuals are left visible rather than absorbed.",
            "The official deaths are earlier by construction: a company stops trading long before Companies "
            "House strikes it off, which pushes this recipe's survival up rather than down."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
