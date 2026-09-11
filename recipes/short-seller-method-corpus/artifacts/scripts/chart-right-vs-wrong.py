#!/usr/bin/env python3
"""What separates the calls that were later corroborated from the ones that were not.

    python chart-right-vs-wrong.py

Both groups on the same clock, and then every measure that might tell them apart.

Left: cumulative return against the Russell 2000 from the report date, for targets
that later filed a restatement, delisting notice or bankruptcy and for those that did
not. Same horizons for both — the earlier version of this analysis ran only the
corroborated group to its own filing date, which is a post-mortem on winners with no
comparison group at all.

Right: the candidate explanations, ordered by how much they separate the two.

    already flagged before the report   67% vs 17%      the only large gap
    market cap                          $0.90B vs $3.06B   p = 0.267
    report length                       6,749 vs 10,735 words   p = 0.088
    kinds of evidence used              5 vs 6          p = 0.752

**The research method barely predicts correctness.** Evidence mix is flat across
almost every probe, and where it moves it moves the wrong way: reports that were NOT
corroborated used paid terminal data more often, 71% against 33%, and ran four
thousand words longer. More expensive research, longer write-up, no better hit rate.

What does separate them is the target's own filing record before anyone wrote
anything — 67% of corroborated targets had already filed a restatement or delisting
notice, against 17% of the others.

**"Not corroborated" is not "wrong."** Most short-seller claims are not accounting
claims, and nothing obliges a company to file a document conceding a related-party
allegation. Twelve corroborated reports against forty-eight is also too few to settle
anything; the flat method comparison is the finding, and it is a null.
"""
import json, math, statistics, sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import palette

RAW = Path(__file__).resolve().parents[1] / "raw"
OUT = Path(__file__).resolve().parents[1] / "charts" / "right-vs-wrong.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
YES, NO = "#b03a2e", "#1b4f8a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
HOR = [21, 63, 126, 252, 504, 756]
LAB = {21: "1 mo", 63: "1 qr", 126: "6 mo", 252: "1 yr", 504: "2 yr", 756: "3 yr"}


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
    paths = json.loads((RAW / "matched_paths.json").read_text())
    rw = json.loads((RAW / "right_wrong.json").read_text())
    assert palette.check([YES, NO], label="corroboration palette")
    A = [p for p in paths if p["right"]]
    B = [p for p in paths if not p["right"]]

    W, H = 960.0, 790.0
    PW, PH = 400.0, 300.0
    LX, TY = 92.0, 268.0
    RX = LX + PW + 118.0
    ylo, yhi = -0.72, 0.16
    def X(i): return LX + i / (len(HOR) - 1) * PW
    def Y(v): return TY + PH - (max(ylo, min(yhi, v)) - ylo) / (yhi - ylo) * PH

    el = [f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "The method barely predicts which calls land. The filing record does.",
                  size=19, fill=INK, weight="600"))
    lead, dy = para(24, 58, f"{len(paths)} targets on the same clock: those that later filed a "
                    "restatement, delisting notice or bankruptcy, against those that did not. "
                    "Right-hand panel is every candidate explanation for the gap.",
                    size=12.5, fill=INK2, chars=118)
    el += lead
    y0 = 58 + dy + 22
    a252 = statistics.median(p["path"]["252"] for p in A if "252" in p["path"])
    b252 = statistics.median(p["path"]["252"] for p in B if "252" in p["path"])
    el.append(txt(24, y0, f"A year on, corroborated targets are {a252:+.0%} against the market and "
                 f"the rest are {b252:+.0%}. The paths separate and stay separated.",
                 size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, "But almost nothing about how the report was researched tells you "
                 "in advance which group it is in.", size=13, fill=INK2))

    el.append(txt(LX, TY - 16, "cumulative return vs the Russell 2000, from the report",
                  size=12, fill=INK2, weight="600"))
    for v in [x / 100 for x in range(-70, 11, 10)]:
        el.append(f'<line x1="{LX:.1f}" y1="{Y(v):.1f}" x2="{LX+PW:.1f}" y2="{Y(v):.1f}" '
                  f'stroke="{BASELINE if v == 0 else GRID}" stroke-width="{1.4 if v == 0 else 1}"/>')
        el.append(txt(LX - 10, Y(v) + 4, f"{v:+.0%}", size=10.5, fill=MUTED, anchor="end", tab=True))
    for i, h in enumerate(HOR):
        el.append(txt(X(i), TY + PH + 20, LAB[h], size=10.5, fill=MUTED, anchor="middle"))
    for g, col, name in ((A, YES, "later filed"), (B, NO, "did not")):
        pts = []
        for i, h in enumerate(HOR):
            v = [p["path"][str(h)] for p in g if str(h) in p["path"]]
            if len(v) >= 5:
                pts.append((X(i), Y(statistics.median(v)), len(v)))
        el.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts)
                  + f'" fill="none" stroke="{col}" stroke-width="3"/>')
        for x, y, n in pts:
            el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{col}" stroke="{SURFACE}" stroke-width="1.6"/>')
        el.append(txt(pts[-1][0] + 10, pts[-1][1] + 4, f"{name} ({len(g)})", size=11,
                      fill=col, weight="600"))

    # right panel: what separates them
    R = [r for r in rw if r["right"]]
    Wr = [r for r in rw if not r["right"]]
    # The two panels rest on different subsets and the chart has to say so: the left
    # needs a price series, the right needs the report text linked to a ticker. An
    # unlabelled n in one panel and a different unlabelled n in the other is how a
    # reader ends up comparing numbers that were never computed on the same rows.
    el.append(txt(RX, TY - 30, "what separates the two groups", size=12, fill=INK2, weight="600"))
    el.append(txt(RX, TY - 16, f"{len(R)} corroborated vs {len(Wr)} not — a smaller set than the "
                  "panel at left", size=10, fill=MUTED))
    items = []
    items.append(("already flagged before",
                  sum(1 for r in R if r["flagged"]) / len(R),
                  sum(1 for r in Wr if r["flagged"]) / len(Wr), True))
    for p in ("paid terminal", "own field legwork", "original interviews", "SEC filings",
              "court / litigation", "expert network"):
        items.append((p, sum(1 for r in R if r["ev"][p]) / len(R),
                      sum(1 for r in Wr if r["ev"][p]) / len(Wr), False))
    items.sort(key=lambda t: -abs(t[1] - t[2]))
    BW = 200.0
    for i, (lab, a, b, hi) in enumerate(items):
        y = TY + 14 + i * 40
        el.append(txt(RX, y - 6, lab, size=11, fill=INK if hi else INK2,
                      weight="600" if hi else "normal"))
        el.append(f'<line x1="{RX:.1f}" y1="{y+10:.1f}" x2="{RX+BW:.1f}" y2="{y+10:.1f}" '
                  f'stroke="{GRID}" stroke-width="1"/>')
        for v, col in ((a, YES), (b, NO)):
            el.append(f'<circle cx="{RX + v*BW:.1f}" cy="{y+10:.1f}" r="5.5" fill="{col}"/>')
        el.append(txt(RX + BW + 12, y + 14, f"{a:.0%} / {b:.0%}", size=10.5, fill=MUTED, tab=True))
    el.append(txt(RX, TY + 14 + len(items) * 40 + 2, "0%", size=10, fill=MUTED, tab=True))
    el.append(txt(RX + BW, TY + 14 + len(items) * 40 + 2, "100%", size=10, fill=MUTED,
                  anchor="end", tab=True))

    ly = TY + PH + 54
    for i, (c, lab) in enumerate(((YES, f"later filed a restatement, delisting notice or bankruptcy ({len(A)})"),
                                  (NO, f"did not ({len(B)})"))):
        el.append(f'<circle cx="{31:.1f}" cy="{ly+i*19-4:.1f}" r="5.5" fill="{c}"/>')
        el.append(txt(46, ly + i * 19, lab, size=11, fill=INK2))

    cap, _ = para(24, ly + 52, "\"Did not file\" is not \"was wrong\": nothing obliges a company to "
                  "file a document conceding a related-party or paid-promotion allegation, and most "
                  f"short-seller claims are not accounting claims. {len(R)} corroborated reports "
                  f"against {len(Wr)} carry every comparison on the right, so the flat method result "
                  "is a null rather than a measurement. The left panel uses a larger set because it "
                  "needs only a price series. Reports that were NOT corroborated used paid terminal "
                  "data more often, 71% against 33%, and ran four thousand words longer.",
                  size=11, fill=MUTED, chars=152, leading=15)
    el += cap
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print(f"  charts/right-vs-wrong.svg — {len(A)} corroborated vs {len(B)}; 1yr {a252:+.0%} vs {b252:+.0%}")


if __name__ == "__main__":
    main()
