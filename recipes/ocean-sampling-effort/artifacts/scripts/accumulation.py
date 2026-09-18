#!/usr/bin/env python3
"""Species do not run out. They get logarithmically more expensive.

    python3 chart-9-saturation.py

Everything earlier in this recipe describes what has been recorded. This is the one figure that
claims something about records that do not exist yet, so it is built around a holdout: fit on
everything OBIS holds dated 2000 or earlier, predict the 2024 point, and show the error.

**The saturating model is wrong, and wrong the same way every time.** A Michaelis-Menten curve
fitted to a century of accumulation under-predicts 2024 in **16 classes out of 16**, by a median
19%. It is not noise and it does not cancel: every class has already passed the ceiling that a
century of its own data implied. Anyone arguing from an accumulation curve that a marine group
is nearly fully described is making exactly this error.

**Returns do diminish — just not to a ceiling.** Sponges bought 69,227 new species per million
records between 1950 and 1980 and 2,640 per million since 2000, a 26-fold collapse, and no class
bucks it. The curve flattens forever without arriving. Of the three models tested on the same
holdout, a log-linear fit is the only roughly unbiased one: median error +6.1% against -19.0%
for saturating and +49.1% for a power law.

**What that buys is a price.** With species linear in log(effort), each tenfold increase in
records returns a constant number of new species, and the constant differs across classes by
nearly three orders of magnitude. A hundred new sponge species cost about 83,000 records. A
hundred new seabird species cost 63.5 million, which is more than eight years of the entire
register's intake at its current rate. Sponges are not cheap because the group is small --
there are 6,627 sponge species in OBIS against 1,232 seabirds.

**The load-bearing caveat is on the face of the figure.** A record counts as a record whether it
identifies to species or not, and groups differ in how often they do. If sponge datasets are
taxonomic inventories and seabird datasets are tracking studies, part of this gap is the
granularity of the record rather than the availability of the species.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "accumulation.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#7d8a96"


def sup(x, y, mant, exp, *, size, fill, anchor="start"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}">{mant}<tspan font-size="{size*0.72:.1f}" '
            f'dy="{-size*0.40:.1f}">{exp}</tspan></text>')


def fit_mm(N, S):
    best = None
    for e in [i / 40 for i in range(0, 400)]:
        K = 10 ** e
        x = [n / (n + K) for n in N]
        sm = sum(a * b for a, b in zip(S, x)) / (sum(a * a for a in x) or 1e-9)
        err = sum((sm * a - b) ** 2 for a, b in zip(x, S))
        if best is None or err < best[0]:
            best = (err, sm, K)
    return lambda n: best[1] * n / (n + best[2])


def _ols(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (
        sum((x - mx) ** 2 for x in xs) or 1e-9)
    return my - b * mx, b


def fit_power(N, S):
    a, b = _ols([math.log10(n) for n in N], [math.log10(s) for s in S])
    return lambda v: 10 ** (a + b * math.log10(v))


def fit_log(N, S):
    a, b = _ols([math.log10(n) for n in N], S)
    return lambda v: a + b * math.log10(v)


def main():
    d = json.load(open(os.path.join(HERE, "..", "data", "saturation.json")))
    Y, CUT = d["years"], d["cut"]
    ci = Y.index(CUT)
    MODELS = [("saturating", fit_mm, RED), ("power law", fit_power, AMBER),
              ("log-linear", fit_log, GREEN)]

    rows = []
    for sci, v in d["classes"].items():
        N, S = v["records"], v["species"]
        if min(S[:ci + 1]) <= 0:
            continue
        errs = {k: (f(N[:ci + 1], S[:ci + 1])(N[-1]) - S[-1]) / S[-1] for k, f, _ in MODELS}
        a, b = _ols([math.log10(n) for n in N], S)
        need = N[-1] * (10 ** (100 / b) - 1) if b > 0 else float("inf")
        rows.append({"common": v["common"], "sp": S[-1], "rec": N[-1], "b": b,
                     "need": need, "errs": errs})

    W, H = 1200, 1000
    s = plate.open_svg(W, H, "Species do not run out. They get logarithmically more expensive.")
    fr, _ = plate.frame(W, 62,
                        who="anyone planning a survey to find species not yet in the register",
                        decide="which class the next million records should be spent on",
                        wrong="the cheap classes are cheap because their records identify to "
                              "species more often, not because more species are there")
    s += fr

    # ---- left: the holdout. One mark per class per model, so the bias is visible as a
    # position and not asserted as a summary statistic.
    AX, AY, AH = 28, 250, 300
    s.append(txt(AX, AY - 50, "error on a year the fit never saw", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(AX, AY - 34, f"fitted on records dated {CUT} or earlier, predicting 2024",
                 size=10.5, fill=MUTED))
    x0, pw = AX + 96, 380
    LOE, HIE = -.55, 1.55
    px = lambda e: x0 + pw * ((min(max(e, LOE), HIE) - LOE) / (HIE - LOE))
    for e in (-.5, 0, .5, 1.0, 1.5):
        s.append(f'<line x1="{px(e):.1f}" y1="{AY-6:.1f}" x2="{px(e):.1f}" y2="{AY+AH-56:.1f}" '
                 f'stroke="{INK2 if e == 0 else GRID}" stroke-width="{1.4 if e == 0 else 1}"/>')
        s.append(txt(px(e), AY + AH - 40, f"{e*100:+.0f}%" if e else "0", size=9, fill=MUTED,
                     anchor="middle"))
    s.append(txt(x0, AY + AH - 24, "predicted minus actual, as a share of actual",
                 size=9.5, fill=MUTED))
    for i, (key, _, col) in enumerate(MODELS):
        y = AY + 26 + i * 76
        es = sorted(r["errs"][key] for r in rows)
        med = es[len(es) // 2]
        under = sum(1 for e in es if e < 0)
        s.append(txt(AX, y - 6, key, size=10.5, fill=col, weight="600"))
        s.append(txt(AX, y + 8, f"{under} of {len(es)} under", size=9, fill=MUTED))
        s.append(txt(AX, y + 21, f"median {med:+.1%}", size=9, fill=MUTED))
        for j, r in enumerate(rows):
            e = r["errs"][key]
            jitter = (j % 5 - 2) * 4.6
            s.append(f'<circle cx="{px(e):.1f}" cy="{y + jitter:.1f}" r="3.7" fill="{col}" '
                     f'fill-opacity="0.55" stroke="{col}" stroke-width="0.9"/>')
    s += wrap(AX, AY + AH + 6,
              "Each mark is one class, spread vertically only so they can be told apart. The "
              "saturating fit lands entirely left of zero — every class has already passed the "
              "ceiling a century of its own data implied, so that model cannot be used to argue "
              "a group is nearly described. A power law overshoots almost as consistently. The "
              "log-linear fit straddles zero, which is what makes the right-hand panel legible "
              "at all; its mean absolute error is still 15%, so read the ranking, not the digits.",
              size=10.5, fill=INK2, chars=76)

    # ---- right: the price, with species-known on the other axis so "it is just a small
    # group" can be checked rather than assumed
    BX, BY, BH = 560, 250, 430
    s.append(txt(BX, BY - 50, "what the next hundred species cost", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(BX, BY - 34, "records that must be added to the class, from the log-linear fit",
                 size=10.5, fill=MUTED))
    bx0, bpw = BX + 74, 360
    lo_s, hi_s = 2.0, 4.6
    lo_n, hi_n = 4.6, 8.0
    sx = lambda v: bx0 + bpw * ((math.log10(v) - lo_s) / (hi_s - lo_s))
    sy = lambda v: BY + BH - BH * ((math.log10(v) - lo_n) / (hi_n - lo_n))
    for e in range(2, 5):
        s.append(f'<line x1="{sx(10**e):.1f}" y1="{BY:.1f}" x2="{sx(10**e):.1f}" '
                 f'y2="{BY+BH:.1f}" stroke="{GRID}"/>')
        s.append(sup(sx(10 ** e), BY + BH + 16, "10", str(e), size=9, fill=MUTED,
                     anchor="middle"))
    for e in range(5, 9):
        s.append(f'<line x1="{bx0:.1f}" y1="{sy(10**e):.1f}" x2="{sx(10**hi_s):.1f}" '
                 f'y2="{sy(10**e):.1f}" stroke="{GRID}"/>')
        s.append(sup(bx0 - 7, sy(10 ** e) + 3, "10", str(e), size=9, fill=MUTED, anchor="end"))
    s.append(txt(BX, BY + BH + 32, "species the class already has in OBIS", size=9.5, fill=MUTED))
    s.append(f'<text transform="translate({BX+10},{BY+BH/2}) rotate(-90)" font-size="9.5" '
             f'fill="{MUTED}" text-anchor="middle">records needed for 100 more species</text>')
    placed = []
    for r in sorted(rows, key=lambda r: r["need"]):
        if not math.isfinite(r["need"]):
            continue
        cx, cy = sx(r["sp"]), sy(r["need"])
        col = GREEN if r["need"] < 5e5 else (BLUE if r["need"] < 5e6 else RED)
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.6" fill="{col}" '
                 f'fill-opacity="0.8"/>')
        ly = cy + 3.5
        while any(abs(ly - q) < 11 and abs(cx - qx) < 130 for qx, q in placed):
            ly += 11
        placed.append((cx, ly))
        if abs(ly - (cy + 3.5)) > 13:
            s.append(f'<line x1="{cx+6:.1f}" y1="{cy:.1f}" x2="{cx+10:.1f}" y2="{ly-3:.1f}" '
                     f'stroke="{col}" stroke-width="0.8" stroke-opacity="0.55"/>')
        s += halo(cx + 10, ly, r["common"], size=9.5, fill=col)
    lx, ly = bx0 + 8, BY + 14
    for lab, col in (("under 500k records", GREEN), ("500k to 5M", BLUE), ("over 5M", RED)):
        s.append(f'<circle cx="{lx+5:.1f}" cy="{ly-3.5:.1f}" r="4.6" fill="{col}" '
                 f'fill-opacity="0.8"/>')
        s.append(txt(lx + 16, ly, lab, size=9.5, fill=INK2))
        ly += 14
    s += wrap(BX, BY + BH + 54,
              "Sponges and sea snails are the cheapest in the register and seabirds the dearest "
              "by a factor of 765. That is not a size effect: sponges hold 6,627 species against "
              "the seabirds' 1,232, so the group with five times the species is three orders of "
              "magnitude cheaper to extend. OBIS takes in roughly 7.5M records a year across "
              "everything, which makes 100 more sponge species about four days of global intake "
              "and 100 more seabird species about eight and a half years of it.",
              size=10.5, fill=INK2, chars=76)

    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              "OBIS v3 checklist with an enddate cut-off and statistics/years, fetched "
              "2026-09-18. The horizontal axis of the accumulation curve is the date ON the "
              "record, never the date it became known: a specimen collected in 1911 may have "
              "been keyed in in 2019, so this is what OBIS now holds dated on or before a year, "
              "not what was known in that year. A fitted ceiling is a ceiling on this register, "
              "bounded by what gets observed, digitised and submitted — a group nobody surveys "
              "has a low ceiling for that reason and not a biological one.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for k, _, _ in MODELS:
        es = sorted(r["errs"][k] for r in rows)
        print(f"    {k:<12}median {es[len(es)//2]:+7.1%}  mean|e| "
              f"{sum(abs(e) for e in es)/len(es):5.1%}  {sum(1 for e in es if e<0)}/{len(es)} under")
    return 0


if __name__ == "__main__":
    sys.exit(main())
