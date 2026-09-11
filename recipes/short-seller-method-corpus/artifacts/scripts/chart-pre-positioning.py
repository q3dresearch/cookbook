#!/usr/bin/env python3
"""Something trades before the report. How much of it is the short seller is not knowable.

    python chart-pre-positioning.py

Two panels, and they are meant to be read against each other.

The top panel is a real measurement. Volume against each stock's own 100-day
baseline rises from 1.08x thirty sessions out to 1.88x on the eve, then 6.18x on the
day. The last three sessions before publication carry nearly double normal volume,
before anything is public. Whatever that is — the firm building its position, a leak,
other people noticing the same problem — it happens before the report exists.

The bottom panel is why that cannot be turned into a position size. Excess volume
over the pre-month is a median 8.0% of shares outstanding. The implied short position
is that number times whatever share of the flow belongs to the firm, and nobody knows
that share. At full attribution the firm holds 8% of the company, which is absurd. At
1% of flow it holds 0.08%, which is nothing. The answer spans two orders of magnitude
on a parameter no public source reports.

The standard tool for this inversion is Kyle's lambda — price impact per unit of
order flow, from Kyle (1985), Econometrica. It assumes the trade causes the move.
Here the report causes the move, so inverting it credits the announcement to the
firm's trading and overstates the position by however much the report itself was
worth. A firm accumulating quietly before publishing is also, deliberately,
minimising exactly the impact the method needs to see.
"""
import json, math, statistics, sys
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import palette

RAW = Path(__file__).resolve().parents[1] / "raw"
OUT = Path(__file__).resolve().parents[1] / "charts" / "pre-positioning.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
VOL, BOUND = "#1b4f8a", "#d17b00"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
W_DAYS = 30
THRESHOLD = 0.5     # EU/UK net-short disclosure threshold, % of issued capital


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
    vols = json.loads((RAW / "volume_windows.json").read_text())
    sized = json.loads((RAW / "size_events.json").read_text())
    assert palette.check([VOL, BOUND], label="pre-positioning palette")

    days = list(range(-W_DAYS, W_DAYS + 1))
    med = [statistics.median(r["v"][i] for r in vols) for i in range(len(days))]
    q3 = [sorted(r["v"][i] for r in vols)[3 * len(vols) // 4] for i in range(len(days))]

    # Excess volume in the pre-month, as a share of the company. Recomputed here so
    # the bound and the ramp come from one pass over the same reports.
    excess = []
    for r in sized:
        pass
    exc = json.loads((RAW / "excess_volume.json").read_text())
    med_exc = statistics.median(exc)

    W, H = 960.0, 820.0
    L, R = 92.0, 238.0
    T1, B1 = 236.0, 452.0
    T2, B2 = 556.0, 692.0
    def X(d): return L + (d + W_DAYS) / (2 * W_DAYS) * (W - L - R)
    def Y1(v): return B1 - (math.log10(max(0.8, v)) - math.log10(0.8)) / (math.log10(16) - math.log10(0.8)) * (B1 - T1)
    XA = [100, 50, 25, 10, 5, 2, 1]          # attribution: % of excess flow that is the firm
    def X2(i): return L + i / (len(XA) - 1) * (W - L - R)
    def Y2(p): return B2 - (math.log10(max(0.01, p)) - math.log10(0.01)) / (math.log10(20) - math.log10(0.01)) * (B2 - T2)

    el = [f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "Something trades before the report. Whose it is, nobody can say.",
                  size=19, fill=INK, weight="600"))
    lead, dy = para(24, 58, f"{len(vols)} reports. Top: daily volume against each stock's own "
                    "100-day baseline. Bottom: the short position that excess volume implies, "
                    "as a function of how much of it belongs to the firm.",
                    size=12.5, fill=INK2, chars=118)
    el += lead
    y0 = 58 + dy + 22
    el.append(txt(24, y0, f"Volume runs {med[W_DAYS-1]:.2f}x normal on the eve of publication, up "
                 f"from {med[0]:.2f}x a month out — before anything is public.",
                 size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, "That is measurable. Converting it to a position is not: the answer "
                 "moves two orders of magnitude on an unknowable share.", size=13, fill=INK2))

    # ---- panel 1: volume ramp
    el.append(txt(24, T1 - 16, "daily volume, multiple of the stock's own 100-day baseline",
                  size=12, fill=INK2, weight="600"))
    for v in (1, 2, 4, 8, 16):
        el.append(f'<line x1="{L}" y1="{Y1(v):.1f}" x2="{W-R}" y2="{Y1(v):.1f}" '
                  f'stroke="{BASELINE if v == 1 else GRID}" stroke-width="{1.5 if v == 1 else 1}"/>')
        el.append(txt(L - 10, Y1(v) + 4, f"{v}x", size=11, fill=MUTED, anchor="end", tab=True))
    for d in range(-30, 31, 10):
        el.append(f'<line x1="{X(d):.1f}" y1="{T1}" x2="{X(d):.1f}" y2="{B1:.1f}" stroke="{GRID}" stroke-width="1"/>')
        el.append(txt(X(d), B1 + 18, str(d), size=11, fill=MUTED, anchor="middle", tab=True))
    band = " ".join(f"{X(d):.1f},{Y1(v):.1f}" for d, v in zip(days, q3))
    band += " " + " ".join(f"{X(d):.1f},{Y1(1.0):.1f}" for d in reversed(days))
    el.append(f'<polygon points="{band}" fill="{VOL}" fill-opacity="0.08"/>')
    el.append(f'<line x1="{X(0):.1f}" y1="{T1}" x2="{X(0):.1f}" y2="{B1:.1f}" '
              f'stroke="{BOUND}" stroke-width="1.6" stroke-dasharray="4 3"/>')
    el.append(txt(X(0) - 7, T1 - 4, "report", size=11, fill=BOUND, anchor="end", weight="600"))
    el.append('<polyline points="' + " ".join(f"{X(d):.1f},{Y1(v):.1f}" for d, v in zip(days, med))
              + f'" fill="none" stroke="{VOL}" stroke-width="2.5"/>')
    for d in (-10, -3, -1, 0):
        el.append(f'<circle cx="{X(d):.1f}" cy="{Y1(med[d+W_DAYS]):.1f}" r="4.5" fill="{VOL}" '
                  f'stroke="{SURFACE}" stroke-width="1.6"/>')
        el.append(txt(X(d), Y1(med[d + W_DAYS]) - 11, f"{med[d+W_DAYS]:.2f}x", size=10,
                      fill=VOL, anchor="middle", weight="600", tab=True))
    el.append(txt(L, B1 + 40, "trading days from publication", size=12, fill=INK2))

    # ---- panel 2: the bound
    el.append(txt(24, T2 - 16, "implied short position, if the firm is this share of the excess flow",
                  size=12, fill=INK2, weight="600"))
    for p in (0.01, 0.1, 1, 10):
        el.append(f'<line x1="{L}" y1="{Y2(p):.1f}" x2="{W-R}" y2="{Y2(p):.1f}" stroke="{GRID}" stroke-width="1"/>')
        el.append(txt(L - 10, Y2(p) + 4, f"{p:g}%", size=11, fill=MUTED, anchor="end", tab=True))
    el.append(f'<line x1="{L}" y1="{Y2(THRESHOLD):.1f}" x2="{W-R}" y2="{Y2(THRESHOLD):.1f}" '
              f'stroke="{INK2}" stroke-width="1.4" stroke-dasharray="5 4"/>')
    # Sits at the left end: at the right it lands on the 0.40% data label.
    el.append(txt(L + 6, Y2(THRESHOLD) - 7, "0.5% — the EU/UK disclosure threshold",
                  size=10.5, fill=INK2))
    pts = [(X2(i), Y2(med_exc * a / 100)) for i, a in enumerate(XA)]
    el.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
              + f'" fill="none" stroke="{BOUND}" stroke-width="2.5"/>')
    for i, a in enumerate(XA):
        x, y = pts[i]
        el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{BOUND}" stroke="{SURFACE}" stroke-width="1.6"/>')
        el.append(txt(x, B2 + 18, f"{a}%", size=11, fill=MUTED, anchor="middle", tab=True))
        el.append(txt(x, y - 11, f"{med_exc*a/100:.2f}%", size=10, fill=BOUND,
                      anchor="middle", weight="600", tab=True))
    el.append(txt(L, B2 + 38, "share of the excess volume attributed to the short seller",
                  size=12, fill=INK2))

    lx = W - R + 16
    note, _ = para(lx, T2 + 6, "Nothing observable pins this axis down. A US filer discloses no "
                   "short position at all; the UK publishes only aggregates since 2025. "
                   "Germany still names holders above 0.5%, and almost none of these "
                   "targets are German-listed.", size=11, fill=INK2, chars=25, leading=14)
    el += note

    fb = defaultdict(list)
    for r in vols:
        fb[r["firm"]].append(statistics.median(r["v"][25:30]))
    el.append(txt(lx, T1 + 6, "volume, final 5 days", size=12, fill=INK, weight="600"))
    yy = T1 + 28
    for f, g in sorted(fb.items(), key=lambda kv: -statistics.median(kv[1])):
        if len(g) < 5:
            continue
        el.append(txt(lx, yy, f"{f} ({len(g)})", size=11, fill=MUTED))
        el.append(txt(lx + 150, yy, f"{statistics.median(g):.2f}x", size=11, fill=INK,
                      anchor="end", weight="600", tab=True))
        yy += 18

    cap, _ = para(24, H - 82, f"Baseline is each stock's median daily volume over sessions -130 to "
                  f"-31, so it predates any plausible position building. Excess volume over the "
                  f"pre-month is a median {med_exc:.1f}% of shares outstanding across {len(exc)} "
                  "reports with a share count. The bottom panel is arithmetic on that figure, not a "
                  "finding: it shows how little the data constrains the answer. Kyle (1985) is the "
                  "standard inversion and assumes the trade moves the price — here the report does, "
                  "so it would credit the announcement to the firm.",
                  size=11, fill=MUTED, chars=152, leading=15)
    el += cap
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print(f"  charts/pre-positioning.svg — eve {med[W_DAYS-1]:.2f}x, day0 {med[W_DAYS]:.2f}x, "
          f"median excess {med_exc:.1f}% of shares")


if __name__ == "__main__":
    main()
