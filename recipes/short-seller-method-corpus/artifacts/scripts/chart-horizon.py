#!/usr/bin/env python3
"""The size of the effect depends on the window you pick. Its reliability does not.

    python chart-horizon.py

Nine horizons from one trading day to one year, all measured from the day before the
report and net of the Russell 2000.

The top panel is the median abnormal return, and it wanders: -3.4% at a day, -6.7%
at a month, -2.9% at two, -8.3% at a year. It is not a decay and it is not a drift
— it is noise around a small negative number, and whichever horizon an author picks
becomes their headline. The first version of this recipe used thirty trading days,
which is not a calendar period at all, and which happens to sit near a local trough.

The bottom panel is the share of targets that underperformed, and it behaves: 78%
at a day, falling steadily to 55% at a year. That IS a decay, it is monotone, and it
says the thing worth saying — a short report reliably moves a stock down on the day
and the reliability erodes from there until, a year out, it is barely better than a
coin toss.

So read the bottom panel. The top one mostly measures the author's choice of window.
"""
import json, statistics, sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import event_study as E
import palette

RAW = Path(__file__).resolve().parents[1] / "raw"
OUT = Path(__file__).resolve().parents[1] / "charts" / "horizon-sensitivity.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
MAIN, WARN = "#1b4f8a", "#d17b00"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
HOR = [1, 3, 5, 10, 21, 42, 63, 126, 252]
CAL = {1: "1 day", 3: "3 days", 5: "1 week", 10: "2 weeks", 21: "1 month",
       42: "2 months", 63: "1 quarter", 126: "6 months", 252: "1 year"}


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


def measure():
    E.BENCH_PRICES = E.bench_series()
    cands = json.load(open(RAW / "join_candidates.json"))
    rows = []
    for c in cands:
        s = E.series(c["ticker"])
        if not s:
            continue
        dates = [d for d, _ in s]
        i = next((k for k, d in enumerate(dates) if d >= c["date"]), None)
        if i is None or i < 1:
            continue
        eve, be = s[i - 1][1], E.BENCH_PRICES.get(dates[i - 1])
        if not eve or not be:
            continue
        out = {}
        for h in HOR:
            if i + h >= len(s):
                continue
            bh = E.BENCH_PRICES.get(dates[i + h])
            if bh:
                out[h] = (s[i + h][1] / eve) / (bh / be) - 1
        if out:
            rows.append(out)
    return rows


def main():
    rows = measure()
    assert palette.check([MAIN, WARN], label="horizon palette")
    stats = {}
    for h in HOR:
        v = sorted(r[h] for r in rows if h in r)
        stats[h] = dict(n=len(v), med=statistics.median(v), q1=v[len(v) // 4],
                        q3=v[3 * len(v) // 4], neg=sum(1 for x in v if x < 0) / len(v))

    W, H = 940.0, 760.0
    L, R = 92.0, 176.0
    T1, B1 = 214.0, 430.0          # top panel: median return
    T2, B2 = 478.0, 612.0          # bottom panel: share negative
    lo = min(stats[h]["q1"] for h in HOR) - 0.03
    hi = max(stats[h]["q3"] for h in HOR) + 0.03
    def X(i): return L + i / (len(HOR) - 1) * (W - L - R)
    def Y1(v): return B1 - (v - lo) / (hi - lo) * (B1 - T1)
    def Y2(v): return B2 - (v - 0.45) / (0.85 - 0.45) * (B2 - T2)

    el = [f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "The effect size is your window choice. The hit rate is not.",
                  size=19, fill=INK, weight="600"))
    lead, dy = para(24, 58, f"{len(rows)} short-report targets at nine horizons, each measured from "
                    "the day before the report and net of the Russell 2000.",
                    size=12.5, fill=INK2, chars=118)
    el += lead
    y0 = 58 + dy + 22
    el.append(txt(24, y0, f"The median wanders — {stats[1]['med']:+.1%} at a day, "
                 f"{stats[21]['med']:+.1%} at a month, {stats[42]['med']:+.1%} at two, "
                 f"{stats[252]['med']:+.1%} at a year.", size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, f"The share that underperform decays cleanly: {stats[1]['neg']:.0%} "
                 f"to {stats[252]['neg']:.0%}. That is the number to quote.", size=13, fill=INK2))

    # ---- top panel
    el.append(txt(24, T1 - 16, "median abnormal return, with interquartile range",
                  size=12, fill=INK2, weight="600"))
    for v in [x / 100 for x in range(-40, 41, 10)]:
        if lo <= v <= hi:
            el.append(f'<line x1="{L}" y1="{Y1(v):.1f}" x2="{W-R}" y2="{Y1(v):.1f}" '
                      f'stroke="{GRID if v else BASELINE}" stroke-width="{1 if v else 1.5}"/>')
            el.append(txt(L - 10, Y1(v) + 4, f"{v:+.0%}", size=11, fill=MUTED, anchor="end", tab=True))
    band = " ".join(f"{X(i):.1f},{Y1(stats[h]['q3']):.1f}" for i, h in enumerate(HOR))
    band += " " + " ".join(f"{X(i):.1f},{Y1(stats[h]['q1']):.1f}" for i, h in reversed(list(enumerate(HOR))))
    el.append(f'<polygon points="{band}" fill="{MAIN}" fill-opacity="0.10"/>')
    el.append('<polyline points="' + " ".join(f"{X(i):.1f},{Y1(stats[h]['med']):.1f}" for i, h in enumerate(HOR))
              + f'" fill="none" stroke="{MAIN}" stroke-width="2.5"/>')
    for i, h in enumerate(HOR):
        el.append(f'<circle cx="{X(i):.1f}" cy="{Y1(stats[h]["med"]):.1f}" r="4.5" fill="{MAIN}" '
                  f'stroke="{SURFACE}" stroke-width="1.6"/>')

    # ---- bottom panel
    el.append(txt(24, T2 - 16, "share of targets that underperformed the market",
                  size=12, fill=INK2, weight="600"))
    for v in (0.5, 0.6, 0.7, 0.8):
        el.append(f'<line x1="{L}" y1="{Y2(v):.1f}" x2="{W-R}" y2="{Y2(v):.1f}" stroke="{GRID}" stroke-width="1"/>')
        el.append(txt(L - 10, Y2(v) + 4, f"{v:.0%}", size=11, fill=MUTED, anchor="end", tab=True))
    el.append(f'<line x1="{L}" y1="{Y2(0.5):.1f}" x2="{W-R}" y2="{Y2(0.5):.1f}" '
              f'stroke="{BASELINE}" stroke-width="1.5" stroke-dasharray="4 3"/>')
    el.append(txt(W - R + 8, Y2(0.5) + 4, "coin toss", size=10.5, fill=MUTED))
    el.append('<polyline points="' + " ".join(f"{X(i):.1f},{Y2(stats[h]['neg']):.1f}" for i, h in enumerate(HOR))
              + f'" fill="none" stroke="{WARN}" stroke-width="2.5"/>')
    for i, h in enumerate(HOR):
        el.append(f'<circle cx="{X(i):.1f}" cy="{Y2(stats[h]["neg"]):.1f}" r="4.5" fill="{WARN}" '
                  f'stroke="{SURFACE}" stroke-width="1.6"/>')
        el.append(txt(X(i), Y2(stats[h]["neg"]) - 12, f"{stats[h]['neg']:.0%}", size=10,
                      fill=WARN, anchor="middle", weight="600", tab=True))

    for i, h in enumerate(HOR):
        el.append(txt(X(i), B2 + 22, CAL[h], size=10.5, fill=INK2, anchor="middle"))
        el.append(txt(X(i), B2 + 36, f"{h}d", size=9.5, fill=MUTED, anchor="middle", tab=True))
    el.append(txt(L, B2 + 62, "trading days after publication", size=12, fill=INK2))

    cap, _ = para(24, H - 58, "Horizons are trading days, so weekends and holidays are already "
                  "excluded — 21 is a calendar month, 63 a quarter. The earlier version of this "
                  "recipe used 30, which is not a calendar period and sits near a local trough in "
                  "the top panel. Survivors only: a target that was delisted before a horizon "
                  "drops out of it, which is why the one-year column has 82 events and the "
                  "one-day column has 85.", size=11, fill=MUTED, chars=150, leading=15)
    el += cap
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print("  charts/horizon-sensitivity.svg")
    for h in HOR:
        s = stats[h]
        print(f"    {CAL[h]:<10}{h:>4}d  n={s['n']:<4} median {s['med']:>+6.1%}  below zero {s['neg']:>4.0%}")


if __name__ == "__main__":
    main()
