#!/usr/bin/env python3
"""The market takes a month to work out which short reports were right.

    python chart-before-after.py

Every target that has a market cap, a price window and an SEC filing outcome. Left
panel is the month BEFORE the report, right panel the month after; horizontal axis is
the target's size on both. Red marks are targets that went on to file a restatement,
delisting notice or bankruptcy.

Read the three moments in order and the story is not the one the 2x2 told.

    before      doomed +0.9%   survived -6.9%      the wrong way round
    the report  doomed -2.8%   survived -2.7%      indistinguishable
    after       doomed -12.8%  survived +2.0%      a fifteen-point split

**Before** the report the companies heading for a restatement were holding up, while
the ones that turned out fine were already sliding. **On the day** the two are
identical to within a tenth of a point: whatever the short seller saw, the market did
not price it. **Then over the following month they separate by fifteen points.**

That is the arbitrage stated properly. It is not that a short report is worth 3% —
it is that the 3% is the same number whether the report was right or wrong, and the
difference arrives later, in a window a reader can still trade.

Size is on the x-axis because everything else in this recipe turned out to depend on
it. Here it does not: the correlation between log market cap and the post-report
return is +0.03. The separation is the colour, not the position.
"""
import json, math, statistics, sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import palette

RAW = Path(__file__).resolve().parents[1] / "raw"
OUT = Path(__file__).resolve().parents[1] / "charts" / "before-and-after.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
BAD, OK = "#b03a2e", "#1b4f8a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
XLO, XHI = 7.6, 11.9


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
    rows = json.loads((RAW / "scatter_rows.json").read_text())
    assert palette.check([BAD, OK], label="outcome palette")
    bad = [r for r in rows if r["bad"]]
    ok = [r for r in rows if not r["bad"]]

    W, H = 960.0, 810.0
    PW, PH, GX = 356.0, 300.0, 60.0
    LX, TY = 96.0, 268.0
    ylo, yhi = -0.62, 0.42

    def X(cap, ox): return ox + (max(XLO, min(XHI, math.log10(cap))) - XLO) / (XHI - XLO) * PW
    def Y(v): return TY + PH - (max(ylo, min(yhi, v)) - ylo) / (yhi - ylo) * PH

    el = [f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "The market takes a month to work out which reports were right",
                  size=19, fill=INK, weight="600"))
    lead, dy = para(24, 58, f"{len(rows)} short-report targets. Horizontal: size on both panels. "
                    "Vertical: the stock's move in the month before the report, then the month "
                    "after. Red went on to file a restatement, delisting notice or bankruptcy.",
                    size=12.5, fill=INK2, chars=118)
    el += lead
    y0 = 58 + dy + 22
    ev_b = statistics.median(r["event"] for r in bad)
    ev_o = statistics.median(r["event"] for r in ok)
    el.append(txt(24, y0, f"On the day itself the two are indistinguishable — {ev_b:+.1%} against "
                 f"{ev_o:+.1%}. Over the next month they split by fifteen points.",
                 size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, "And before the report the doomed ones were the ones holding up. "
                 "The signal is never in the price when the report lands.", size=13, fill=INK2))

    for p, (key, title) in enumerate((("pre", "the month BEFORE the report"),
                                      ("post", "the month AFTER the report"))):
        ox = LX + p * (PW + GX)
        el.append(txt(ox, TY - 34, title, size=12.5, fill=INK, weight="600"))
        mb = statistics.median(r[key] for r in bad)
        mo = statistics.median(r[key] for r in ok)
        el.append(txt(ox, TY - 16, f"ended badly {mb:+.1%}", size=11.5, fill=BAD, weight="600", tab=True))
        el.append(txt(ox + 150, TY - 16, f"survived {mo:+.1%}", size=11.5, fill=OK, weight="600", tab=True))
        for v in [x / 100 for x in range(-60, 41, 20)]:
            el.append(f'<line x1="{ox:.1f}" y1="{Y(v):.1f}" x2="{ox+PW:.1f}" y2="{Y(v):.1f}" '
                      f'stroke="{BASELINE if v == 0 else GRID}" stroke-width="{1.4 if v == 0 else 1}"/>')
            if p == 0:
                el.append(txt(ox - 10, Y(v) + 4, f"{v:+.0%}", size=11, fill=MUTED, anchor="end", tab=True))
        for e in range(8, 12):
            cap = 10 ** e
            lab = f"${10**(e-9):.0f}B" if e >= 9 else "$100M"
            el.append(f'<line x1="{X(cap,ox):.1f}" y1="{TY:.1f}" x2="{X(cap,ox):.1f}" '
                      f'y2="{TY+PH:.1f}" stroke="{GRID}" stroke-width="1"/>')
            el.append(txt(X(cap, ox), TY + PH + 20, lab, size=10.5, fill=MUTED, anchor="middle", tab=True))
        # medians as horizontal rules, so the eye has something to compare
        for g, col in ((ok, OK), (bad, BAD)):
            m = statistics.median(r[key] for r in g)
            el.append(f'<line x1="{ox:.1f}" y1="{Y(m):.1f}" x2="{ox+PW:.1f}" y2="{Y(m):.1f}" '
                      f'stroke="{col}" stroke-width="2" stroke-dasharray="6 4" opacity="0.75"/>')
        for r in rows:
            c = BAD if r["bad"] else OK
            # filled = had already filed a restatement or delisting before the report
            el.append(f'<circle cx="{X(r["cap"],ox):.1f}" cy="{Y(r[key]):.1f}" r="5.5" '
                      f'fill="{c if r["flagged"] else SURFACE}" fill-opacity="{0.75 if r["flagged"] else 1}" '
                      f'stroke="{c}" stroke-width="1.8"/>')
        el.append(txt(ox, TY + PH + 42, "market capitalisation at publication (log)", size=11.5, fill=INK2))

    ly = TY + PH + 84
    el.append(txt(24, ly, "colour is the outcome, fill is the warning sign", size=12, fill=INK, weight="600"))
    for i, (col, fill, lab) in enumerate((
            (BAD, True, f"later filed a restatement, delisting notice or bankruptcy ({len(bad)})"),
            (OK, True, f"did not ({len(ok)})"),
            (INK2, False, "hollow = clean filing history before the report; filled = already flagged"))):
        yy = ly + 20 + i * 19
        if i < 2:
            el.append(f'<circle cx="{31:.1f}" cy="{yy-4:.1f}" r="5.5" fill="{col}" fill-opacity="0.75" stroke="{col}" stroke-width="1.8"/>')
        else:
            el.append(f'<circle cx="{31:.1f}" cy="{yy-4:.1f}" r="5.5" fill="{SURFACE}" stroke="{MUTED}" stroke-width="1.8"/>')
        el.append(txt(46, yy, lab, size=11, fill=INK2))

    cap, _ = para(24, H - 66, "Returns are against the Russell 2000 and indexed within each window, "
                  "so the panels do not share a baseline — the left one ends where the report "
                  "begins. Correlation between log market cap and the post-report return is +0.03: "
                  "the separation here is the colour, not the position. Targets whose price could "
                  "not be recovered, which are disproportionately the bankrupt ones, are absent.",
                  size=11, fill=MUTED, chars=152, leading=15)
    el += cap
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print(f"  charts/before-and-after.svg — {len(rows)} targets, {len(bad)} ended badly")
    for k in ("pre", "event", "post"):
        print(f"    {k:<6} bad {statistics.median(r[k] for r in bad):>+7.1%}   "
              f"ok {statistics.median(r[k] for r in ok):>+7.1%}")


if __name__ == "__main__":
    main()
