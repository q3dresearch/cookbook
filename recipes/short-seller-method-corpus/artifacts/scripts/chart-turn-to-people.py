#!/usr/bin/env python3
"""Hindenburg learned to interview people. The others already knew.

    python chart-turn-to-people.py

Share of each firm's first-look reports that cite someone it interviewed, by era,
with 95% Wilson intervals.

Hindenburg's rise is real: 21% in 2017-19 against 75% in 2023-26, and the two
intervals do not touch. Muddy Waters' highest era is its FIRST — 73% in 2010-13 —
and every one of its intervals overlaps every other, so nothing about it can be
called a trend. Night Market the same.

That kills the reading of "the method got richer over time". The method did not
move; one firm moved into it. The bands are on the chart because without them
Muddy Waters' 73 → 33 → 31 → 71 → 50 looks like a story, and with eight to
fourteen reports per era it is not one.
"""
import math, re, sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpuslib, ctrllib, palette

OUT = Path(__file__).resolve().parents[1] / "charts" / "the-turn-to-people.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
COLS = ["#2361b0", "#b8912a", "#7a4a1e"]
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
ERAS = ["2010-13", "2014-16", "2017-19", "2020-22", "2023-26"]


def txt(x, y, s, *, size, fill, anchor="start", weight="normal", tab=False):
    st = "font-variant-numeric: tabular-nums;" if tab else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family=\'{FONT}\' font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
            f'style="{st}">{escape(s)}</text>')


def para(x, y, s, *, size, fill, chars, leading=17.0):
    words, line, out, n = s.split(), [], [], 0
    for w in words:
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
            line, n = [], n + 1
        line.append(w)
    if line:
        out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
        n += 1
    return out, n * leading


def wilson(k, n, z=1.96):
    """Score interval. The normal approximation is useless at n=8 and p near 1."""
    if n == 0:
        return 0.0, 0.0
    p, d = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def era(y):
    y = int(y)
    return ("2010-13" if y <= 2013 else "2014-16" if y <= 2016 else
            "2017-19" if y <= 2019 else "2020-22" if y <= 2022 else "2023-26")


def series():
    out = {}
    hb = corpuslib.load("initial")
    P = corpuslib.probes("Hindenburg")
    out["Hindenburg"] = [(era(p["date"][:4]),
                          bool(re.search(P["original interviews"], corpuslib.body(p), re.I)))
                         for p in hb]
    for key, label in (("muddywaters", "Muddy Waters"), ("nightmarket", "Night Market")):
        d, _ = ctrllib.load(key, with_pdf=True)
        d = [x for x in d if x["words"] >= ctrllib.MIN_WORDS]
        init, _, _ = ctrllib.split_reports(d)
        P = corpuslib.probes(label)
        out[label] = [(era(x["date"][:4]),
                       bool(re.search(P["original interviews"], x["text"], re.I)))
                      for x in init]
    return out


def main():
    data = series()
    assert palette.check(COLS, label="firm palette")

    W, H = 960.0, 660.0
    L, R, T, B = 88.0, 250.0, 250.0, 96.0
    def X(i): return L + (i / (len(ERAS) - 1)) * (W - L - R)
    def Y(v): return (H - B) - v * (H - B - T)

    el = [f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "One firm learned to interview people", size=19, fill=INK, weight="600"))
    lead, dy = para(24, 58, "Share of each firm's first-look reports citing someone it "
                    "interviewed, by era. Bands are 95% intervals — with eight to fourteen "
                    "reports in an era, they are wide on purpose.", size=12.5, fill=INK2, chars=116)
    el += lead
    y0 = 58 + dy + 24
    el.append(txt(24, y0, "Hindenburg goes 21% to 75% and its intervals separate. Muddy Waters' "
                 "highest era is its first, in 2010.", size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, "So this is not the practice changing. It is one firm growing into "
                 "a method the others already had.", size=13, fill=INK2))

    for v in (0, 0.25, 0.5, 0.75, 1.0):
        el.append(f'<line x1="{L}" y1="{Y(v):.1f}" x2="{W-R}" y2="{Y(v):.1f}" stroke="{GRID}" stroke-width="1"/>')
        el.append(txt(L - 12, Y(v) + 4, f"{v:.0%}", size=11, fill=MUTED, anchor="end", tab=True))
    for i, e in enumerate(ERAS):
        el.append(txt(X(i), H - B + 22, e, size=11.5, fill=MUTED, anchor="middle", tab=True))
    el.append(f'<line x1="{L}" y1="{Y(0):.1f}" x2="{W-R}" y2="{Y(0):.1f}" stroke="{BASELINE}" stroke-width="1.5"/>')
    el.append(f'<text x="{-(T + (H-B-T)/2):.1f}" y="26" transform="rotate(-90)" '
              f'font-family=\'{FONT}\' font-size="12" fill="{INK2}" text-anchor="middle">'
              "reports citing an interview</text>")

    summary = []
    for j, (name, rows) in enumerate(data.items()):
        pts = []
        for i, e in enumerate(ERAS):
            g = [v for b, v in rows if b == e]
            if not g:
                continue
            k, n = sum(g), len(g)
            lo, hi = wilson(k, n)
            pts.append((i, k / n, lo, hi, n))
        band = " ".join(f"{X(i):.1f},{Y(hi):.1f}" for i, _, _, hi, _ in pts)
        band += " " + " ".join(f"{X(i):.1f},{Y(lo):.1f}" for i, _, lo, _, _ in reversed(pts))
        el.append(f'<polygon points="{band}" fill="{COLS[j]}" fill-opacity="0.12"/>')
        el.append('<polyline points="' + " ".join(f"{X(i):.1f},{Y(p):.1f}" for i, p, _, _, _ in pts)
                  + f'" fill="none" stroke="{COLS[j]}" stroke-width="2.5"/>')
        for i, p, lo, hi, n in pts:
            el.append(f'<circle cx="{X(i):.1f}" cy="{Y(p):.1f}" r="5.5" fill="{COLS[j]}" '
                      f'stroke="{SURFACE}" stroke-width="2"/>')
        a, z = pts[0], pts[-1]
        sep = not (a[2] <= z[3] and z[2] <= a[3])
        summary.append((name, a, z, sep, COLS[j]))
        # No label at the line end: it lands on top of the legend, which already
        # carries the name and the colour.

    lx = W - R + 12
    el.append(txt(lx, T + 4, "does the first era differ", size=12, fill=INK, weight="600"))
    el.append(txt(lx, T + 20, "from the last?", size=12, fill=INK, weight="600"))
    yy = T + 48
    for name, a, z, sep, c in summary:
        el.append(f'<circle cx="{lx+6:.1f}" cy="{yy-4:.1f}" r="5.5" fill="{c}"/>')
        el.append(txt(lx + 20, yy, name, size=11.5, fill=INK2, weight="600"))
        v, _ = para(lx, yy + 16, (f"{a[1]:.0%} to {z[1]:.0%} — intervals separate, the move is real"
                                  if sep else
                                  f"{a[1]:.0%} to {z[1]:.0%} — intervals overlap, no trend shown"),
                    size=11, fill=INK if sep else MUTED, chars=28, leading=14)
        el += v
        yy += 74

    cap, _ = para(24, H - 48, "First-look reports only. An interview is detected from phrases like "
                  "“we spoke with”, “we interviewed” and “told us”, so it counts what a report "
                  "declares — a firm that interviews someone and does not say so is invisible here. "
                  "Era boundaries are fixed in advance, not chosen to fit.",
                  size=11, fill=MUTED, chars=152, leading=15)
    el += cap
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print("  charts/the-turn-to-people.svg")
    for name, a, z, sep, _ in summary:
        print(f"    {name:<14} {a[1]:>4.0%} (n={a[4]:>2}) -> {z[1]:>4.0%} (n={z[4]:>2})  "
              f"{'SEPARATED' if sep else 'overlapping — no trend'}")


if __name__ == "__main__":
    main()
