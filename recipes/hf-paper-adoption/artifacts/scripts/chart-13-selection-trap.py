#!/usr/bin/env python3
"""The two funding signals: one is a 23x mirage, the other is real and thin.

Both panels score the same exposure-matched cohort -- 6,134 papers published
2023-06-01 to 2025-03-31, so every one has had eighteen months in which to be adopted.

**Team size looks like the best predictor in the recipe and is not a predictor at
all.** Papers with 25 or more authors are adopted at 9.28% against 0.41% for one or
two -- a 23x gradient, known at publication, beating the 7% that `1-no-predictor`
calls the strongest available feature. Then score it on the unit Q2 and Q3 insist on,
two *independent* organisations, and the gradient disappears: **0 of 1,343 at one to
four authors, 1 of 194 at twenty-five or more.** The grey line is flat on the floor.

A twenty-five-author paper is an industry lab's model report, and that lab's own
models cite it. Team size predicts **self-citation**. It measures whether the authors
run a model shop.

**An author track record survives the same test, and it is the only thing that does.**
Leak-free -- an author's earlier paper counts as adopted only if a model citing it was
created *before* the new paper was published, so nothing from the future leaks in.
The rate runs 1.08% for authors with no prior adopted paper, 2.62% with one, **11.54%
with two or more**. Eleven-fold, and available the week of publication.

**The catch is the interval, which is why it is drawn.** The top bucket is
twenty-six papers and its 95% interval runs from 4% to 29%. It is a real effect and a
thin one, and anyone acting on it should act on the lower bound.

**Both panels use the same outcome** -- "named by any top-1,000 model" -- which is
mostly a lab citing itself. That is the honest ceiling on this whole question and
`8-two-positives` is where it is drawn.
"""
import sys, collections, math
sys.path.insert(0, ".")
import paperlib as P
from adoption import ALIASES

LO, HI = "2023-06-01", "2025-03-31"
BUCKETS = [(1, 2, "1-2"), (3, 4, "3-4"), (5, 6, "5-6"), (7, 9, "7-9"),
           (10, 14, "10-14"), (15, 24, "15-24"), (25, 10**6, "25+")]


def wil(k, n, z=1.96):
    if not n: return (0, 0, 0)
    p = k/n; d = 1 + z*z/n; c = (p + z*z/(2*n))/d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return p, max(0, c-h), min(1, c+h)


def main():
    ms, f = P.models(), P.feed()
    cited, indep, first = set(), collections.defaultdict(set), {}
    for m in ms:
        o = ALIASES.get(m["id"].split("/")[0], m["id"].split("/")[0])
        c = m.get("createdAt")
        for a in P.arxiv_ids(m):
            cited.add(a)
            if not P.foreign_base(m): indep[a].add(o)
            if c and (a not in first or c < first[a]): first[a] = c
    coh = [(k, v) for k, v in f.items() if LO <= v["publishedAt"][:10] <= HI]

    def akey(a):
        u = (a.get("user") or {}).get("name")
        return ("u:" + u) if u else ("n:" + (a.get("name") or "").strip().lower())
    prior, res = collections.Counter(), {}
    for k, v in sorted(f.items(), key=lambda kv: kv[1]["publishedAt"]):
        ks = [akey(a) for a in (v.get("authors") or []) if akey(a) not in ("n:", "u:")]
        res[k] = max([prior[a] for a in ks], default=0)
        was = k in first and first[k] < v["publishedAt"]
        for a in ks:
            if was: prior[a] += 1

    W, L, R, T = 940, 92, 66, 176
    PH, GAP = 210, 116
    H = T + PH*2 + GAP + 150
    pw = W - L - R
    body = []

    # ---- panel A: team size
    a0 = T
    rows = []
    for lo, hi, lab in BUCKETS:
        sel = [k for k, v in coh if lo <= len(v.get("authors") or []) <= hi]
        rows.append((lab, len(sel), sum(1 for k in sel if k in cited),
                     sum(1 for k in sel if len(indep.get(k, ())) >= 2)))
    mx = 10.5
    sy = lambda v: a0 + PH - v/mx*PH
    sx = lambda i: L + (i + 0.5)/len(rows)*pw
    for g in (0, 2, 4, 6, 8, 10):
        body.append(f'<line x1="{L}" y1="{sy(g):.1f}" x2="{L+pw:.1f}" y2="{sy(g):.1f}" '
                    f'stroke="{P.INK if g == 0 else P.GRID}" stroke-width="{1.3 if g == 0 else 1}"/>')
        body.append(P.txt(L-10, sy(g)+4, f"{g}%", size=11, fill=P.MUTED, anchor="end", tab=True))
    for i, (lab, n, ad, mo) in enumerate(rows):
        body.append(P.txt(sx(i), a0+PH+20, lab, size=11, fill=P.MUTED, anchor="middle"))
        body.append(P.txt(sx(i), a0+PH+34, f"n={n:,}", size=9.5, fill=P.MUTED, anchor="middle"))
    d1 = " ".join(("M" if i == 0 else "L") + f"{sx(i):.1f} {sy(r[2]/r[1]*100):.1f}" for i, r in enumerate(rows))
    body.append(f'<path d="{d1}" fill="none" stroke="{P.HOT}" stroke-width="2.4"/>')
    d2 = " ".join(("M" if i == 0 else "L") + f"{sx(i):.1f} {sy(r[3]/r[1]*100):.1f}" for i, r in enumerate(rows))
    body.append(f'<path d="{d2}" fill="none" stroke="{P.MUTED}" stroke-width="2.4"/>')
    for i, r in enumerate(rows):
        body.append(f'<circle cx="{sx(i):.1f}" cy="{sy(r[2]/r[1]*100):.1f}" r="4" fill="{P.HOT}"/>')
        body.append(f'<circle cx="{sx(i):.1f}" cy="{sy(r[3]/r[1]*100):.1f}" r="3.4" fill="{P.MUTED}"/>')
    body.append(P.txt(L-10, a0-44, "TEAM SIZE — a 23x gradient that is not there", size=12.5, fill=P.INK, weight="600"))
    body.append(P.txt(L-10, a0-26, "share of the cohort adopted, by number of authors", size=11, fill=P.MUTED))
    body.append(P.txt(sx(6)-8, sy(9.28)-12, f"{rows[-1][2]/rows[-1][1]*100:.1f}% — named by ANY model",
                      size=11.5, fill=P.HOT, weight="600", anchor="end"))
    body.append(P.txt(sx(0), sy(3.4), "named by TWO INDEPENDENT orgs —", size=11, fill=P.INK2, weight="600"))
    body.append(P.txt(sx(0), sy(3.4)+14, "1 paper across all seven buckets", size=11, fill=P.INK2))
    body.append(f'<line x1="{sx(0):.1f}" y1="{sy(3.0):.1f}" x2="{sx(0):.1f}" y2="{sy(0.35):.1f}" '
                f'stroke="{P.MUTED}" stroke-width="1" stroke-dasharray="3 3"/>')

    # ---- panel B: track record
    b0 = T + PH + GAP
    tr = []
    for lo, hi, lab in ((0, 0, "none"), (1, 1, "one"), (2, 10**6, "two or more")):
        sel = [k for k, v in coh if lo <= res[k] <= hi]
        k_ = sum(1 for x in sel if x in cited)
        tr.append((lab, len(sel), k_, *wil(k_, len(sel))))
    mxb = 32
    syb = lambda v: b0 + PH - v/mxb*PH
    bx = lambda i: L + (i + 0.5)/len(tr)*pw
    for g in (0, 10, 20, 30):
        body.append(f'<line x1="{L}" y1="{syb(g):.1f}" x2="{L+pw:.1f}" y2="{syb(g):.1f}" '
                    f'stroke="{P.INK if g == 0 else P.GRID}" stroke-width="{1.3 if g == 0 else 1}"/>')
        body.append(P.txt(L-10, syb(g)+4, f"{g}%", size=11, fill=P.MUTED, anchor="end", tab=True))
    for i, (lab, n, k_, p_, lo_, hi_) in enumerate(tr):
        x = bx(i)
        body.append(f'<line x1="{x:.1f}" y1="{syb(lo_*100):.1f}" x2="{x:.1f}" y2="{syb(hi_*100):.1f}" '
                    f'stroke="{P.COOL}" stroke-width="2.4" stroke-opacity="0.45"/>')
        for e in (lo_, hi_):
            body.append(f'<line x1="{x-7:.1f}" y1="{syb(e*100):.1f}" x2="{x+7:.1f}" y2="{syb(e*100):.1f}" '
                        f'stroke="{P.COOL}" stroke-width="2"/>')
        body.append(f'<circle cx="{x:.1f}" cy="{syb(p_*100):.1f}" r="5.5" fill="{P.COOL}"/>')
        off = -13 if p_*100 > 6 else -18
        body.append(P.txt(x, syb(hi_*100)+off if p_*100 <= 6 else syb(p_*100)+off,
                          f"{p_*100:.2f}%", size=12, fill=P.COOL,
                          anchor="middle", weight="600", tab=True))
        body.append(P.txt(x, b0+PH+20, lab, size=11.5, fill=P.INK, anchor="middle"))
        body.append(P.txt(x, b0+PH+34, f"n={n:,}  ·  {k_} adopted", size=9.5, fill=P.MUTED, anchor="middle"))
    body.append(P.txt(L-10, b0-44, "AUTHOR TRACK RECORD — real, and thin", size=12.5, fill=P.INK, weight="600"))
    body.append(P.txt(L-10, b0-26, "prior papers of theirs already adopted, counted only if adopted BEFORE this one",
                      size=11, fill=P.MUTED))
    body.append(P.txt(bx(2)+24, syb(tr[2][4]*100), "95% interval", size=10.5, fill=P.MUTED))
    body.append(P.txt(bx(2)+24, syb(tr[2][4]*100)+13, "4% to 29%", size=10.5, fill=P.MUTED))

    foot = ["Same cohort in both panels: 6,134 papers with 18+ months of exposure, of which 73 are named by a "
            "top-1,000 model.",
            "TOP — the orange gradient is real and measures the wrong thing: a 25-author paper is a lab's model "
            "report, and that lab's own models cite it.",
            "Scored on independent organisations instead, the grey line never leaves the floor.",
            "BOTTOM — leak-free by construction, so nothing from the future enters. Eleven-fold, on 26 papers. Act "
            "on the lower bound, not the point estimate.",
            "Both score 'named by any top-1,000 model', which is mostly self-citation — the ceiling on this whole "
            "question, drawn in 8-two-positives."]
    print(P.write("13-selection-trap.svg", P.frame(
        W, H, "One funding signal is a mirage, the other is real and thin",
        "Everything available at publication that looks like it predicts adoption, scored twice: on any citation, "
        "and on independent organisations.", body, foot, chars=124)))


main()
