#!/usr/bin/env python3
"""A short report cannot move a large company, and takes a month to kill a small one.

    python chart-size.py

Each mark is one report, placed by the target's market capitalisation on the day
before publication and by what the stock did against the Russell 2000. Heavy marks
are the band medians at one day and at one month.

The relationship is not a slope and reporting it as one hides it: the correlation
between log market cap and the one-day move is -0.08, which reads as "size does not
matter". Banded, it plainly does, and not monotonically.

    micro caps barely move on the day and are down 17% in a month
    small and mid caps take the whole hit at once, 85-95% of them falling
    companies over $10B do not move at all — 53% fall, which is a coin toss

So the immediate reaction peaks in the middle. A mega-cap absorbs a short report;
a micro-cap is too illiquid to reprice in a day and gets there over weeks.

Market cap is price times the most recent cover-page share count SEC holds, so it is
stale by up to a quarter and counts restricted stock. Fine for bands, wrong for
anything finer.
"""
import json, math, statistics, sys
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import palette

RAW = Path(__file__).resolve().parents[1] / "raw"
OUT = Path(__file__).resolve().parents[1] / "charts" / "size-and-impact.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, GHOST = "#e1e0d9", "#c3c2b7", "#d7d6cf"
DAY1, DAY21 = "#1b4f8a", "#d17b00"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
BANDS = [(0, 3e8, "micro", "<$300M"), (3e8, 2e9, "small", "$300M-2B"),
         (2e9, 1e10, "mid", "$2-10B"), (1e10, 9e15, "large", ">$10B")]


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


def main():
    rows = [r for r in json.loads((RAW / "size_events.json").read_text()) if "r21" in r]
    assert palette.check([DAY1, DAY21], label="size palette")

    W, H = 960.0, 720.0
    L, R, T, B = 92.0, 232.0, 244.0, 132.0
    XLO, XHI = 7.3, 12.0                       # log10 dollars: $20M to $1T
    ylo, yhi = -0.45, 0.25
    def X(cap): return L + (max(XLO, min(XHI, math.log10(cap))) - XLO) / (XHI - XLO) * (W - L - R)
    def Y(v): return (H - B) - (max(ylo, min(yhi, v)) - ylo) / (yhi - ylo) * (H - B - T)

    el = [f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "Size decides whether a short report lands", size=19, fill=INK, weight="600"))
    lead, dy = para(24, 58, f"{len(rows)} reports, placed by the target's market capitalisation the "
                    "day before publication against what the stock did relative to the Russell 2000. "
                    "Light marks are single reports at one day; heavy marks are band medians.",
                    size=12.5, fill=INK2, chars=118)
    el += lead
    y0 = 58 + dy + 22
    el.append(txt(24, y0, "Companies over $10B do not move — a coin toss whether they fall at all. "
                 "The hit peaks in the middle of the range.", size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, "Micro caps are the slow case: barely a move on the day, down 17% "
                 "against the market a month later.", size=13, fill=INK2))

    for v in [x / 100 for x in range(-40, 26, 10)]:
        el.append(f'<line x1="{L}" y1="{Y(v):.1f}" x2="{W-R}" y2="{Y(v):.1f}" '
                  f'stroke="{GRID if v else BASELINE}" stroke-width="{1 if v else 1.5}"/>')
        el.append(txt(L - 10, Y(v) + 4, f"{v:+.0%}", size=11, fill=MUTED, anchor="end", tab=True))
    for e in range(8, 13):
        cap = 10 ** e
        lab = f"${10**(e-9):.0f}B" if e >= 9 else f"${10**(e-6):.0f}M"
        el.append(f'<line x1="{X(cap):.1f}" y1="{T}" x2="{X(cap):.1f}" y2="{H-B:.1f}" stroke="{GRID}" stroke-width="1"/>')
        el.append(txt(X(cap), H - B + 20, lab, size=11, fill=MUTED, anchor="middle", tab=True))
    el.append(txt(L, H - B + 46, "market capitalisation the day before the report (log scale)",
                  size=12, fill=INK2))
    el.append(f'<text x="{-(T + (H-B-T)/2):.1f}" y="24" transform="rotate(-90)" '
              f'font-family=\'{FONT}\' font-size="12" fill="{INK2}" text-anchor="middle">'
              "return vs the market</text>")

    for r in rows:
        el.append(f'<circle cx="{X(r["cap"]):.1f}" cy="{Y(r["r1"]):.1f}" r="3.6" fill="none" '
                  f'stroke="{GHOST}" stroke-width="1.5"/>')

    lines = {1: [], 21: []}
    for lo, hi, short, lab in BANDS:
        g = [r for r in rows if lo <= r["cap"] < hi]
        if not g:
            continue
        mid = 10 ** statistics.median(math.log10(r["cap"]) for r in g)
        for h, col in ((1, DAY1), (21, DAY21)):
            v = [r[f"r{h}"] for r in g]
            m = statistics.median(v)
            lines[h].append((mid, m))
            el.append(f'<circle cx="{X(mid):.1f}" cy="{Y(m):.1f}" r="7" fill="{col}" '
                      f'fill-opacity="0.85" stroke="{SURFACE}" stroke-width="2"/>')
        neg = sum(1 for r in g if r["r1"] < 0) / len(g)
        el.append(txt(X(mid), T - 26, short, size=12, fill=INK, anchor="middle", weight="600"))
        el.append(txt(X(mid), T - 13, f"{lab}  n={len(g)}", size=10.5, fill=MUTED, anchor="middle", tab=True))
        el.append(txt(X(mid), H - B - 8, f"{neg:.0%} fell", size=10, fill=MUTED, anchor="middle", tab=True))
    for h, col in ((1, DAY1), (21, DAY21)):
        el.append('<polyline points="' + " ".join(f"{X(c):.1f},{Y(m):.1f}" for c, m in lines[h])
                  + f'" fill="none" stroke="{col}" stroke-width="2.5"/>')

    lx = W - R + 16
    el.append(txt(lx, T + 6, "band median", size=12, fill=INK, weight="600"))
    for i, (h, col, lab) in enumerate(((1, DAY1, "one day after"), (21, DAY21, "one month after"))):
        yy = T + 32 + i * 24
        el.append(f'<circle cx="{lx+7:.1f}" cy="{yy-4:.1f}" r="7" fill="{col}" fill-opacity="0.85"/>')
        el.append(txt(lx + 22, yy, lab, size=11.5, fill=INK2))
    el.append(f'<circle cx="{lx+7:.1f}" cy="{T+84:.1f}" r="3.6" fill="none" stroke="{GHOST}" stroke-width="1.5"/>')
    el.append(txt(lx + 22, T + 88, "one report, one day", size=11.5, fill=MUTED))
    note, _ = para(lx, T + 120, "Correlation between log market cap and the one-day move is -0.08. "
                   "Reported as a slope this relationship disappears; it is not a slope.",
                   size=11, fill=INK2, chars=24, leading=14)
    el += note

    cap, _ = para(24, H - 80, f"{len(rows)} of 273 reports: needs a date, a ticker SEC recognises, a "
                  "price series, and a share count from SEC's XBRL filings. Market cap is price times "
                  "the most recent cover-page share count, so it is stale by up to a quarter and "
                  "includes restricted stock — good enough to band by, not to rank within. Targets "
                  "that went bankrupt are missing from the price source entirely, and they are more "
                  "likely to have been small.", size=11, fill=MUTED, chars=152, leading=15)
    el += cap
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print("  charts/size-and-impact.svg")
    for lo, hi, short, lab in BANDS:
        g = [r for r in rows if lo <= r["cap"] < hi]
        if g:
            print(f"    {short:<6}{lab:<12}n={len(g):<4} day+1 {statistics.median(r['r1'] for r in g):>+6.1%}"
                  f"  day+21 {statistics.median(r['r21'] for r in g):>+6.1%}"
                  f"  {sum(1 for r in g if r['r1']<0)/len(g):>4.0%} fell")


if __name__ == "__main__":
    main()
