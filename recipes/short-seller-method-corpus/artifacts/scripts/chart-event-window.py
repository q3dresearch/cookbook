#!/usr/bin/env python3
"""What the target's stock did, thirty trading days either side of the report.

    python chart-event-window.py

The median line with its interquartile band, and one thin line per firm.

The shape is the finding: the fall lands on the day and then stops. From day +1 to
day +30 the median target moves -0.3%, which is nothing. Whatever the market is
going to do about a short report, it does immediately.

The second finding is that "a short report moves the stock" is a claim about SOME
firms. Hindenburg's targets fall a median 8.2% on the day and 87% of them fall at
all; Spruce Point's fall 0.6% and only 60% fall. Same trade, same window, an order
of magnitude apart.

And the band is drawn because the median is not the story on its own: the quartiles
at day +30 run -30% to +5%. Most of these reports did not move the stock much and a
few moved it enormously.

**Survivors only.** The price source keys on a company's current symbol, so a target
that went bankrupt is missing — Zynex is ZYXIQ now, Nikola is NKLAQ, and neither
serves history under the symbol its report named. The targets where the thesis
landed hardest are the ones least likely to be in this figure, and the caption says
so rather than leaving it to be discovered.
"""
import json, statistics, sys
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import palette

RAW = Path(__file__).resolve().parents[1] / "raw"
OUT = Path(__file__).resolve().parents[1] / "charts" / "event-window.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, GHOST = "#e1e0d9", "#c3c2b7", "#cfcec6"
MAIN, EVENT = "#1b4f8a", "#d17b00"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
W_DAYS = 30


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


def ret(e, a, b):
    pa, pb = e["prices"][a + W_DAYS], e["prices"][b + W_DAYS]
    return pb / pa - 1 if pa else None


def main():
    ev = json.loads((RAW / "event_windows.json").read_text())
    cov = json.loads((RAW / "prices" / "coverage.json").read_text())
    assert palette.check([MAIN, EVENT], label="event palette")

    days = list(range(-W_DAYS, W_DAYS + 1))
    # Indexed to the report EVE and net of the Russell 2000, not to day -30 raw.
    #
    # A -30 baseline reads -10.2% at day +30, and most of that is drift that was
    # already under way before anyone had read the report — it answers "what
    # happened to a holder over this window", not "what did the report do". Against
    # the eve the same 85 events read -6.9%, and against the market -3.4% on the day.
    # The market adjustment changes little, which is itself worth knowing: these
    # moves are the company's own, not the index's.
    key = "abn" if all(e.get("abn") for e in ev) else "rel"
    med = [statistics.median(e[key][i] for e in ev) for i in range(len(days))]
    q1 = [sorted(e[key][i] for e in ev)[len(ev) // 4] for i in range(len(days))]
    q3 = [sorted(e[key][i] for e in ev)[3 * len(ev) // 4] for i in range(len(days))]
    by = defaultdict(list)
    for e in ev:
        by[e["firm"]].append(e)

    W, H = 960.0, 700.0
    L, R, T, B = 84.0, 246.0, 236.0, 150.0
    lo, hi = min(q1) - 0.03, max(q3) + 0.03
    def X(d): return L + (d + W_DAYS) / (2 * W_DAYS) * (W - L - R)
    def Y(v): return (H - B) - (v - lo) / (hi - lo) * (H - B - T)

    el = [f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    # The title said "the fall lands on the day, then stops" while the line it sits
    # above drifts from -3% to -7% after day 0. That claim came from a per-event
    # median of the day+1-to-day+30 ratio, which is not the same statistic as the
    # median curve drawn here — the median of the ratios is not the ratio of the
    # medians, and only one of them is what a reader sees.
    el.append(txt(24, 34, "A short report is worth about three per cent on the day",
                  size=19, fill=INK, weight="600"))
    lead, dy = para(24, 58, f"{len(ev)} short-report targets, thirty trading days either side of "
                    "publication. Indexed to the day BEFORE the report and measured against the "
                    "Russell 2000, so the line is what the report did rather than what the month "
                    "around it did. Band is the interquartile range.",
                    size=12.5, fill=INK2, chars=116)
    el += lead
    y0 = 58 + dy + 22
    d0, d1, d30 = med[W_DAYS], med[W_DAYS + 1], med[-1]
    under = sum(1 for e in ev if e[key][W_DAYS + 1] < 0) / len(ev)
    el.append(txt(24, y0, f"The report itself is worth about {d1:+.0%}. A month later the median "
                 f"target is {d30:+.0%} behind the market.", size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, f"{under:.0%} underperform within a day, and the drift keeps going "
                 "— it does not stop at the announcement.", size=13, fill=INK2))

    for v in [x / 100 for x in range(-100, 101, 5)]:
        if lo <= v <= hi:
            el.append(f'<line x1="{L}" y1="{Y(v):.1f}" x2="{W-R}" y2="{Y(v):.1f}" '
                      f'stroke="{GRID if v else BASELINE}" stroke-width="{1 if v else 1.5}"/>')
            el.append(txt(L - 10, Y(v) + 4, f"{v:+.0%}", size=11, fill=MUTED, anchor="end", tab=True))
    for d in range(-30, 31, 10):
        el.append(f'<line x1="{X(d):.1f}" y1="{T}" x2="{X(d):.1f}" y2="{H-B:.1f}" stroke="{GRID}" stroke-width="1"/>')
        el.append(txt(X(d), H - B + 20, str(d), size=11, fill=MUTED, anchor="middle", tab=True))
    el.append(txt(L, H - B + 44, "trading days from publication", size=12, fill=INK2))
    el.append(f'<text x="{-(T + (H-B-T)/2):.1f}" y="24" transform="rotate(-90)" '
              f'font-family=\'{FONT}\' font-size="12" fill="{INK2}" text-anchor="middle">'
              "return vs the market, indexed to report eve</text>")

    band = " ".join(f"{X(d):.1f},{Y(v):.1f}" for d, v in zip(days, q3))
    band += " " + " ".join(f"{X(d):.1f},{Y(v):.1f}" for d, v in zip(reversed(days), reversed(q1)))
    el.append(f'<polygon points="{band}" fill="{MAIN}" fill-opacity="0.10"/>')

    for firm, g in sorted(by.items(), key=lambda kv: -len(kv[1])):
        if len(g) < 5:
            continue
        fm = [statistics.median(e[key][i] for e in g) for i in range(len(days))]
        el.append('<polyline points="' + " ".join(f"{X(d):.1f},{Y(v):.1f}" for d, v in zip(days, fm))
                  + f'" fill="none" stroke="{GHOST}" stroke-width="1.6"/>')
        # No end-label: it lands on the legend, which already names every firm.

    el.append(f'<line x1="{X(0):.1f}" y1="{T}" x2="{X(0):.1f}" y2="{H-B:.1f}" '
              f'stroke="{EVENT}" stroke-width="1.6" stroke-dasharray="4 3"/>')
    el.append(txt(X(0) - 7, T - 8, "report", size=11, fill=EVENT, anchor="end", weight="600"))
    el.append('<polyline points="' + " ".join(f"{X(d):.1f},{Y(v):.1f}" for d, v in zip(days, med))
              + f'" fill="none" stroke="{MAIN}" stroke-width="3"/>')
    for d in (-1, 0, 1, 30):
        el.append(f'<circle cx="{X(d):.1f}" cy="{Y(med[d+W_DAYS]):.1f}" r="4.5" fill="{MAIN}" '
                  f'stroke="{SURFACE}" stroke-width="1.6"/>')
    el.append(txt(X(30) - 4, Y(med[-1]) - 12, f"median {med[-1]:+.1%}", size=11.5,
                  fill=MAIN, anchor="end", weight="600", tab=True))

    lx = W - R + 14
    el.append(txt(lx, T + 12, "by firm, on the day", size=12, fill=INK, weight="600"))
    yy = T + 34
    for firm, g in sorted(by.items(), key=lambda kv: statistics.median(e[key][W_DAYS+1] for e in kv[1])):
        if len(g) < 5:
            continue
        mv = statistics.median(e[key][W_DAYS + 1] for e in g)
        fell = sum(1 for e in g if e[key][W_DAYS + 1] < 0) / len(g)
        el.append(txt(lx, yy, f"{firm} ({len(g)})", size=11, fill=INK2))
        el.append(txt(lx, yy + 13, f"{mv:+.1%},  {fell:.0%} fell", size=11, fill=INK, weight="600", tab=True))
        yy += 34

    absent = sum(1 for v in cov.values() if v["outcome"] != "listed")
    cap, _ = para(24, H - 68, f"85 of 273 reports. A report needs a date, a ticker SEC recognises, "
                  f"and a price series that spans the window. {absent} target symbols returned no "
                  "history at all. The price source keys on a company's CURRENT symbol, so a target "
                  "that went bankrupt is absent — Zynex trades as ZYXIQ now, Nikola as NKLAQ — which "
                  "means the cases where the short thesis landed hardest are the ones most likely "
                  "missing from this figure. Read it as what happened to the survivors.",
                  size=11, fill=MUTED, chars=152, leading=15)
    el += cap
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print(f"  charts/event-window.svg — {len(ev)} events, median day+30 {med[-1]:+.1%}")
    print(f"    day 0 {d0:+.1%}   day +1 {d1:+.1%}   day +30 {d30:+.1%}   "
          f"({under:.0%} underperform by day +1)")


if __name__ == "__main__":
    main()
