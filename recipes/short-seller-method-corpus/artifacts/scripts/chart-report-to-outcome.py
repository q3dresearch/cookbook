#!/usr/bin/env python3
"""Being right is not the same as being paid, and the wait is measured in years.

    python chart-report-to-outcome.py

One row per target that later filed a restatement, delisting notice or bankruptcy.
The bar runs from the report to that filing; its length is how long the wait was, and
the number at the end is what the stock did against the Russell 2000 over exactly
that period.

**This replaces a fixed 30-day window, which could not work.** The median target took
454 days to file, so a month-long window was measuring a period in which nothing had
happened yet — and the resulting scatter looked like noise because it was. The window
was not too small; it was aimed at the wrong moment. `before-and-after.svg` is kept
as the negative example.

What a variable horizon shows instead:

    median -45% against the market, over a median 454 days
    14 of 19 negative -- and 5 positive, two of them enormously
    the wait ranges from 20 days to six years

So even where a filing later conceded the point, **five targets in nineteen beat the
market between the report and the concession**, one of them by 194%. Bloom Energy was
vindicated by a restatement 148 days later and rose anyway. Being right about a
company is a claim about the company; being paid is a claim about the timing, and
this corpus says they are close to unrelated.
"""
import json, math, statistics, sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import palette

RAW = Path(__file__).resolve().parents[1] / "raw"
OUT = Path(__file__).resolve().parents[1] / "charts" / "report-to-outcome.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
DOWN, UP = "#1b4f8a", "#b03a2e"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


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
    rows = sorted(json.loads((RAW / "to_outcome.json").read_text()), key=lambda r: r["days"])
    assert palette.check([DOWN, UP], label="outcome palette")
    med_d = statistics.median(r["days"] for r in rows)
    med_r = statistics.median(r["ret"] for r in rows)
    neg = sum(1 for r in rows if r["ret"] < 0)

    W = 960.0
    ROW, LBL = 27.0, 158.0
    BARW = 470.0
    H = 268 + len(rows) * ROW + 150
    XMAX = math.log10(2400)
    def X(d): return LBL + (math.log10(max(15, d)) - math.log10(15)) / (XMAX - math.log10(15)) * BARW

    el = [f'<rect width="{W}" height="{H:.0f}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "Being right is not being paid, and the wait is years",
                  size=19, fill=INK, weight="600"))
    lead, dy = para(24, 58, f"The {len(rows)} targets that later filed a restatement, delisting "
                    "notice or bankruptcy. Each bar runs from the report to that filing; the number "
                    "is the stock against the Russell 2000 over exactly that period.",
                    size=12.5, fill=INK2, chars=118)
    el += lead
    y0 = 58 + dy + 22
    el.append(txt(24, y0, f"Median {med_r:+.0%} over a median {med_d:.0f} days — but {len(rows)-neg} "
                 f"of {len(rows)} rose, one of them by {max(r['ret'] for r in rows):+.0%}.",
                 size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, "A fixed 30-day window could not see any of this: the median target "
                 "had not filed anything yet. That chart is kept as the negative example.",
                 size=13, fill=INK2))

    ty = y0 + 54
    for d, lab in ((30, "1 month"), (90, "3 months"), (365, "1 year"), (730, "2 years"), (1825, "5 years")):
        el.append(f'<line x1="{X(d):.1f}" y1="{ty:.1f}" x2="{X(d):.1f}" '
                  f'y2="{ty + len(rows)*ROW + 8:.1f}" stroke="{GRID}" stroke-width="1"/>')
        el.append(txt(X(d), ty - 8, lab, size=10.5, fill=MUTED, anchor="middle"))
    el.append(f'<line x1="{LBL:.1f}" y1="{ty:.1f}" x2="{LBL:.1f}" y2="{ty + len(rows)*ROW + 8:.1f}" '
              f'stroke="{BASELINE}" stroke-width="1.5"/>')
    el.append(txt(LBL, ty - 26, "report", size=10.5, fill=INK2, weight="600", anchor="end"))

    for i, r in enumerate(rows):
        y = ty + 14 + i * ROW
        col = DOWN if r["ret"] < 0 else UP
        el.append(txt(LBL - 14, y + 4, r["t"], size=12, fill=INK, anchor="end", weight="600", tab=True))
        el.append(txt(24, y + 4, r["firm"], size=10.5, fill=MUTED))
        el.append(f'<line x1="{LBL:.1f}" y1="{y:.1f}" x2="{X(r["days"]):.1f}" y2="{y:.1f}" '
                  f'stroke="{col}" stroke-width="3" stroke-opacity="0.45"/>')
        el.append(f'<circle cx="{X(r["days"]):.1f}" cy="{y:.1f}" r="5" fill="{col}"/>')
        el.append(txt(X(r["days"]) + 12, y + 4, f"{r['ret']:+.0%}", size=11.5, fill=col,
                      weight="600", tab=True))
        el.append(txt(W - 40, y + 4, f"{r['days']:,}d", size=10.5, fill=MUTED, anchor="end", tab=True))

    ly = ty + len(rows) * ROW + 40
    el.append(txt(24, ly, "colour is the direction of the trade", size=11.5, fill=INK, weight="600"))
    for i, (c, lab) in enumerate(((DOWN, f"the stock underperformed the market ({neg})"),
                                  (UP, f"it beat the market anyway ({len(rows)-neg})"))):
        el.append(f'<circle cx="{31:.1f}" cy="{ly+18+i*18:.1f}" r="5" fill="{c}"/>')
        el.append(txt(46, ly + 22 + i * 18, lab, size=11, fill=INK2))

    cap, _ = para(24, ly + 66, "The filing is corroboration, not proof the allegation was right: a "
                  "delisting notice can follow a late filing or a share price under a dollar. "
                  "Horizontal axis is logarithmic — the shortest wait here is 20 days and the "
                  "longest six years, so a linear scale would compress two thirds of the rows "
                  "against the left edge. Targets whose price could not be recovered, which are "
                  "disproportionately the bankrupt ones, are missing entirely.",
                  size=11, fill=MUTED, chars=152, leading=15)
    el += cap
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print(f"  charts/report-to-outcome.svg — {len(rows)} targets, median {med_r:+.0%} over {med_d:.0f}d, "
          f"{neg} down / {len(rows)-neg} up")


if __name__ == "__main__":
    main()
