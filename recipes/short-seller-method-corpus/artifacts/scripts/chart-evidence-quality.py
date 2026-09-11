#!/usr/bin/env python3
"""Harder-to-get evidence goes with a bigger fall — in small caps, on very few reports.

    python chart-evidence-quality.py

Every report is drawn. With eight reports in a cell, a median on its own is a
decoration; the points are the evidence and the median is an annotation on them.

**What "quality" means here, and what it does not.** The axis is corpuslib's barrier
tiers, which rank evidence by what it costs an outsider to obtain: public filings and
court records are free, a terminal costs money, a former employee who agrees to talk
costs access, a whistleblower costs luck. That is a measure of EXCLUSIVITY, not of
truth. A leaked document can be wrong and an SEC filing is nearly always right — the
filing is simply already in the price, which is why exclusivity is the thing that
should move a stock and accuracy is not.

Using it here is legitimate only because it was built for a different question
("could an independent researcher do this work?") before any price data existed. An
axis invented after seeing returns would be worth nothing.

**The result is a lead, not a finding.** Under $2B the gap is 20 points and p = 0.022
on 8 against 11 reports — which does not clear a Bonferroni threshold of 0.013 for the
four comparisons run. Over $2B there is nothing at all. Three independent cuts point
the same way, and none of them is significant on its own.
"""
import json, statistics, random, sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import palette

RAW = Path(__file__).resolve().parents[1] / "raw"
OUT = Path(__file__).resolve().parents[1] / "charts" / "evidence-quality.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
LOWQ, HIQ = "#b8912a", "#1b4f8a"
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


def perm(a, b, n=50000, seed=3):
    obs = statistics.median(b) - statistics.median(a)
    pool, rng, hits = list(a) + list(b), random.Random(seed), 0
    for _ in range(n):
        rng.shuffle(pool)
        if abs(statistics.median(pool[len(a):]) - statistics.median(pool[:len(a)])) >= abs(obs):
            hits += 1
    return obs, hits / n


def load():
    rows = json.loads((RAW / "quality_events.json").read_text())
    sz = json.loads((RAW / "size_events.json").read_text())
    for r in rows:
        r["cap"] = None
        for s in sz:
            if s["firm"] == r["firm"] and abs((s.get("r1") or 0) - (r["r1"] or 0)) < 1e-9:
                r["cap"] = s["cap"]
                break
    return [r for r in rows if r["cap"]]


def main():
    rows = load()
    assert palette.check([LOWQ, HIQ], label="evidence palette")

    W, H = 940.0, 740.0
    L, R, T, B = 250.0, 236.0, 268.0, 150.0
    lo, hi = -0.55, 0.20
    def X(v): return L + (max(lo, min(hi, v)) - lo) / (hi - lo) * (W - L - R)

    groups = []
    for cl, ch, clab in ((0, 2e9, "target under $2B"), (2e9, 9e15, "target over $2B")):
        g = [r for r in rows if cl <= r["cap"] < ch]
        a = [r["r1"] for r in g if r["n_gated"] <= 1]
        b = [r["r1"] for r in g if r["n_gated"] >= 2]
        groups.append((clab, a, b))

    el = [f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "Harder-to-get evidence, bigger fall — in small caps only",
                  size=19, fill=INK, weight="600"))
    lead, dy = para(24, 58, "Each mark is one report's move against the market the day after "
                    "publication, split by whether it rests on evidence an outsider could not "
                    "obtain: a site visit, an interview, a terminal, a whistleblower.",
                    size=12.5, fill=INK2, chars=118)
    el += lead
    y0 = 58 + dy + 22
    gap0, p0 = perm(groups[0][1], groups[0][2])
    el.append(txt(24, y0, f"Under $2B the gap is {abs(gap0)*100:.0f} points. Over $2B there is none — "
                 "a big company absorbs the report whatever is in it.", size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, f"On {len(groups[0][1])} against {len(groups[0][2])} reports, p = {p0:.3f}. "
                 "A lead worth chasing, not a result.", size=13, fill=INK2))

    for v in [x / 100 for x in range(-50, 21, 10)]:
        el.append(f'<line x1="{X(v):.1f}" y1="{T-24:.1f}" x2="{X(v):.1f}" y2="{H-B+10:.1f}" '
                  f'stroke="{BASELINE if v == 0 else GRID}" stroke-width="{1.5 if v == 0 else 1}"/>')
        el.append(txt(X(v), H - B + 28, f"{v:+.0%}", size=11, fill=MUTED, anchor="middle", tab=True))
    el.append(txt(L, H - B + 52, "return against the market, day after publication", size=12, fill=INK2))

    rng = random.Random(7)
    yy = T
    for clab, a, b in groups:
        el.append(txt(24, yy - 12, clab, size=13, fill=INK, weight="600"))
        for lab, g, col in (("public or paid only", a, LOWQ),
                            ("needs access to a person", b, HIQ)):
            el.append(txt(L - 16, yy + 22, lab, size=11.5, fill=INK2, anchor="end"))
            el.append(txt(L - 16, yy + 36, f"{len(g)} reports", size=10.5, fill=MUTED, anchor="end", tab=True))
            for v in g:
                jitter = rng.uniform(-7, 7)
                el.append(f'<circle cx="{X(v):.1f}" cy="{yy+24+jitter:.1f}" r="5" fill="{col}" '
                          f'fill-opacity="0.5" stroke="{col}" stroke-width="1.4"/>')
            if g:
                m = statistics.median(g)
                el.append(f'<line x1="{X(m):.1f}" y1="{yy+6:.1f}" x2="{X(m):.1f}" y2="{yy+42:.1f}" '
                          f'stroke="{col}" stroke-width="3"/>')
                el.append(txt(X(m), yy + 2, f"{m:+.0%}", size=11, fill=col, anchor="middle",
                              weight="600", tab=True))
            yy += 62
        yy += 34

    lx = W - R + 14
    el.append(txt(lx, T + 4, "what counts as", size=12, fill=INK, weight="600"))
    el.append(txt(lx, T + 18, "hard to get", size=12, fill=INK, weight="600"))
    tiers, _ = para(lx, T + 42, "a terminal subscription, an import record, an expert network, "
                    "a site visit, an interview, a whistleblower", size=11, fill=INK2, chars=24, leading=14)
    el += tiers
    note, _ = para(lx, T + 150, "This ranks evidence by what it COSTS to obtain, not by whether it "
                   "is true. A leak can be wrong; a filing is nearly always right and already in "
                   "the price. Exclusivity is what should move a stock.",
                   size=11, fill=MUTED, chars=24, leading=14)
    el += note

    g1, p1 = perm(groups[1][1], groups[1][2])
    cap, _ = para(24, H - 96, f"The tiers come from corpuslib, written to ask whether an independent "
                  "researcher could reproduce this work — before any price data existed. An axis "
                  "invented after seeing returns would prove nothing. Over $2B the same split gives "
                  f"p = {p1:.2f}: no effect. Four comparisons were run in total, so a Bonferroni "
                  "threshold for 0.05 is 0.013 and the small-cap result does not clear it. Reports "
                  "whose target went bankrupt are missing from the price source, and they are the "
                  "ones most likely to have rested on the hardest evidence.",
                  size=11, fill=MUTED, chars=150, leading=15)
    el += cap
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print(f"  charts/evidence-quality.svg")
    for clab, a, b in groups:
        gp, pp = perm(a, b)
        print(f"    {clab:<18} {len(a)} vs {len(b)}   {statistics.median(a):+.1%} vs "
              f"{statistics.median(b):+.1%}   p={pp:.3f}")


if __name__ == "__main__":
    main()
