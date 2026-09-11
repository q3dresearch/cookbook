#!/usr/bin/env python3
"""A longer short report cites more KINDS of evidence, not more of the same kind.

    python chart-length-is-breadth.py

One claim, one scatter, one trend read off the data in bins.

The previous version carried two claims at once: length-is-breadth, which is solid
at r = +0.73, and campaigns-start-longer, which is a lead at p = 0.073. It drew 94
grey reference points under 56 coloured ones in two colours keyed to the weaker
claim, and a reader could not tell which of the two they were looking at. The weaker
claim now sits in its own strip at the bottom, sized like what it is.

The trend is drawn as binned medians rather than a fitted line. A regression line
through this cloud would assert linearity the data does not show — the relationship
flattens above about 15,000 words, where a report is already citing most of the
twelve kinds there are.
"""
import json, math, re, statistics, sys, collections, random
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpuslib, ctrllib, palette

OUT = Path(__file__).resolve().parents[1] / "charts" / "length-is-breadth.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, DOT = "#e1e0d9", "#c3c2b7", "#9db8d4"
MAIN, SECOND = "#1b4f8a", "#d17b00"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
XMAX, YMAX = 26000.0, 12.0
BINS = [0, 2500, 5000, 7500, 11000, 16000, XMAX]


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


def pearson(pts):
    n = len(pts)
    mx, my = sum(a for a, _ in pts) / n, sum(b for _, b in pts) / n
    den = math.sqrt(sum((a - mx) ** 2 for a, _ in pts) * sum((b - my) ** 2 for _, b in pts))
    return sum((a - mx) * (b - my) for a, b in pts) / den if den else 0.0


def data():
    """Per-firm points, because pooling them destroys the relationship.

    Pooled across six firms r is +0.29; within each firm it runs +0.19 to +0.79.
    The firms sit at different places on BOTH axes — Spruce Point publishes 13,756
    median words, Night Market 3,655 — so between-firm spread swamps the within-firm
    slope. One scatter of all 273 reports is a chart of that artefact.
    """
    per = {}
    for label, key in [("Hindenburg", None), ("Fuzzy Panda", "fuzzypanda"),
                       ("Night Market", "nightmarket"), ("Muddy Waters", "muddywaters"),
                       ("J Capital", "jcapital"), ("Spruce Point", "sprucepoint")]:
        if key is None:
            docs, P, get = corpuslib.load("initial"), corpuslib.probes(label), corpuslib.body
        else:
            docs, _ = ctrllib.first_look(key)
            P, get = corpuslib.probes(label), (lambda d: d["text"])
        per[label] = [(len(get(d).split()), sum(1 for k in P if re.search(P[k], get(d), re.I)))
                      for d in docs]

    d, _ = ctrllib.load("muddywaters", with_pdf=True)
    d = [x for x in d if x["words"] >= ctrllib.MIN_WORDS]
    init, fu, _ = ctrllib.split_reports(d)
    nfu = collections.Counter(x["target"] for x in fu)
    camp = [x["words"] for x in init if nfu[x["target"]] > 0]
    solo = [x["words"] for x in init if nfu[x["target"]] == 0]
    return per, solo, camp


def perm_p(a, b, n=20000, seed=11):
    obs = statistics.median(b) - statistics.median(a)
    pool, rng, hits = a + b, random.Random(seed), 0
    for _ in range(n):
        rng.shuffle(pool)
        if abs(statistics.median(pool[len(a):]) - statistics.median(pool[:len(a)])) >= abs(obs):
            hits += 1
    return obs, hits / n


def main():
    per, solo, camp = data()
    assert palette.check([MAIN, SECOND], label="length palette")
    rs = {k: pearson(v) for k, v in per.items()}
    allpts = [p for v in per.values() for p in v]

    W, H = 960.0, 880.0
    COLS, PW, PH = 3, 252.0, 150.0
    LX, TY, GX, GY = 84.0, 258.0, 26.0, 78.0

    el = [f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "Longer reports are wider, not padded", size=20, fill=INK, weight="600"))
    lead, dy = para(24, 58, f"{len(allpts)} first-look reports: how long each is against how many "
                    "of the twelve kinds of evidence it cites. One panel per firm, because the "
                    "firms sit at different places on both axes.", size=12.5, fill=INK2, chars=118)
    el += lead
    y0 = 58 + dy + 26
    lo_f = min(rs, key=lambda k: rs[k])
    hi_f = max(rs, key=lambda k: rs[k])
    el.append(txt(24, y0, f"The relationship holds inside every firm — r from {rs[lo_f]:+.2f} to "
                 f"{rs[hi_f]:+.2f}. Length buys range, not repetition.",
                 size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, f"Pooled across all six it reads {pearson(allpts):+.2f}, which is an "
                 "artefact: between-firm spread swamps the slope inside each.",
                 size=13, fill=INK2))

    for i, (firm, pts) in enumerate(sorted(per.items(), key=lambda kv: -rs[kv[0]])):
        cx = LX + (i % COLS) * (PW + GX)
        cy = TY + (i // COLS) * (PH + GY)
        def X(v, cx=cx): return cx + min(v, XMAX) / XMAX * PW
        def Y(v, cy=cy): return cy + PH - min(v, YMAX) / YMAX * PH
        el.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{PW:.1f}" height="{PH:.1f}" '
                  f'fill="#ffffff" fill-opacity="0.55"/>')
        for v in (0, 4, 8, 12):
            el.append(f'<line x1="{cx:.1f}" y1="{Y(v):.1f}" x2="{cx+PW:.1f}" y2="{Y(v):.1f}" '
                      f'stroke="{GRID}" stroke-width="1"/>')
            if i % COLS == 0:
                el.append(txt(cx - 8, Y(v) + 4, str(v), size=9.5, fill=MUTED, anchor="end", tab=True))
        for v in (0, 10000, 20000):
            if i // COLS == 1:
                el.append(txt(X(v), cy + PH + 16, f"{v//1000}k" if v else "0", size=9.5,
                              fill=MUTED, anchor="middle", tab=True))
        for w, e in pts:
            el.append(f'<circle cx="{X(w):.1f}" cy="{Y(e):.1f}" r="3.4" fill="{DOT}" fill-opacity="0.6"/>')
        line = []
        for b in range(len(BINS) - 1):
            g = [(w, e) for w, e in pts if BINS[b] <= w < BINS[b + 1]]
            if len(g) < 3:
                continue
            line.append((X(statistics.median(w for w, _ in g)),
                         Y(statistics.median(e for _, e in g))))
        if len(line) > 1:
            el.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in line)
                      + f'" fill="none" stroke="{MAIN}" stroke-width="2.5"/>')
        el.append(txt(cx, cy - 22, firm, size=12.5, fill=INK, weight="600"))
        el.append(txt(cx, cy - 8, f"n={len(pts)}   median {statistics.median(w for w, _ in pts):,.0f} words",
                      size=10, fill=MUTED, tab=True))
        el.append(txt(cx + PW - 4, cy + 16, f"r = {rs[firm]:+.2f}", size=13, fill=MAIN,
                      anchor="end", weight="700", tab=True))
    el.append(txt(LX, TY + 2 * PH + GY + 42, "words in the report", size=11.5, fill=INK2))
    el.append(f'<text x="{-(TY + PH):.1f}" y="22" transform="rotate(-90)" '
              f'font-family=\'{FONT}\' font-size="11.5" fill="{INK2}" text-anchor="middle">'
              "kinds of evidence cited</text>")

    # ---- the weaker claim, kept small and separate
    sy = TY + 2 * PH + GY + 96
    el.append(f'<line x1="24" y1="{sy-26:.1f}" x2="{W-24}" y2="{sy-26:.1f}" stroke="{GRID}" stroke-width="1"/>')
    gap, p = perm_p(solo, camp)
    el.append(txt(24, sy - 8, "a separate and weaker finding — Muddy Waters first reports that "
                  "became campaigns are the longer ones", size=11.5, fill=INK2, weight="600"))
    sx0, sx1 = 210.0, W - 250.0
    def SX(v): return sx0 + min(v, XMAX) / XMAX * (sx1 - sx0)
    for i, (lab, g, col) in enumerate((("no follow-up", solo, MAIN), ("became a campaign", camp, SECOND))):
        yy = sy + 16 + i * 26
        el.append(txt(sx0 - 12, yy + 4, f"{lab} ({len(g)})", size=10.5, fill=INK2, anchor="end"))
        for w in g:
            el.append(f'<circle cx="{SX(w):.1f}" cy="{yy:.1f}" r="3.2" fill="{col}" fill-opacity="0.45"/>')
        m = statistics.median(g)
        el.append(f'<line x1="{SX(m):.1f}" y1="{yy-9:.1f}" x2="{SX(m):.1f}" y2="{yy+9:.1f}" '
                  f'stroke="{col}" stroke-width="3"/>')
        el.append(txt(SX(m), yy - 13, f"{m:,.0f}", size=9.5, fill=col, anchor="middle", weight="600", tab=True))
    el.append(txt(sx1 + 16, sy + 20, f"gap {gap:,.0f} words, p = {p:.2f}", size=10.5, fill=INK2, tab=True))
    el.append(txt(sx1 + 16, sy + 34, "a lead, not a result", size=10, fill=MUTED))

    cap, _ = para(24, H - 56, "Evidence kinds are the twelve probes in corpuslib, so this counts "
                  "what a report declares. Lines are medians of reports in a word band, drawn only "
                  "where a band holds three or more — not a fitted line, because the relationship "
                  f"flattens once a report cites most of the twelve. {sum(1 for w, _ in allpts if w > XMAX)} "
                  f"reports run past {XMAX/1000:.0f}k words and sit on the right edge of their panel.",
                  size=10.5, fill=MUTED, chars=158, leading=14)
    el += cap
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print(f"  charts/length-is-breadth.svg — per-firm r " +
          ", ".join(f"{k.split()[0]} {v:+.2f}" for k, v in sorted(rs.items(), key=lambda x: -x[1])))


if __name__ == "__main__":
    main()
