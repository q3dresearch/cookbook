#!/usr/bin/env python3
"""KEPT AS A WORKED FAILURE. Dilute injectables looked like the ones that never come back.

This shipped as a finding, computed on 619 of 1,619 FDA rows -- one page of a two-page
feed, read as the whole register. On that half, dilute chronic injectables had been
listed 8.4 years against 3.5 for concentrated ones, permutation p = 0.0025. On the full
register the gap is 7.6 against 4.1 years and p = 0.047; drop the four substances whose
posting date is the 2012 bulk load and it is p = 0.079. The direction survives, the
significance does not, and a prior at p = 0.05 on 39 substances does not change what a
buyer does. It is kept because it was persuasive: a mechanism story (a vial costs the
same to fill whatever it holds), a control (exits are young at every concentration), a
censoring caveat drawn on the figure -- and half the data.

The numbers on the figure are computed, not typed, so it stays an honest record of
what the full register says rather than a frozen copy of the wrong version.
"""
import sys, json, collections, math, statistics as st
import pathlib as _p; sys.path.insert(0, str(_p.Path(__file__).resolve().parent.parent))  # shortagelib lives one level up
import shortagelib as S
import features as X
from rxnorm import clean

EXIT, CHRON = "#c07a1e", "#1b4f8a"
CUT = 10.0                     # mg/mL, the median of the parsed values
import datetime as _dt
FLOOR = {_dt.date(2012, 1, 1), _dt.date(2012, 2, 22)}   # the database's own bulk load
TICKS = [0.001, 0.01, 0.1, 1, 10, 100, 1000]


def main():
    F = X.build()
    d = S.fda_rows()
    rx = json.loads((S.DATA / "rxnorm.json").read_text())
    form = collections.defaultdict(set)
    for r in d:
        e = rx.get(clean(r.get("generic_name") or "")) or {}
        if S.sub_key(e) and r.get("dosage_form"):
            form[S.sub_key(e)].add(r["dosage_form"])
    inj = lambda k: any("Inject" in x for x in form.get(k, ()))
    _P = lambda x: _dt.datetime.strptime(x, "%m/%d/%Y").date()
    firstd = {}
    for r in d:
        e = rx.get(clean(r.get("generic_name") or "")) or {}
        if S.sub_key(e):
            t = _P(r["initial_posting_date"])
            firstd[S.sub_key(e)] = min(firstd.get(S.sub_key(e), t), t)
    pts = [k for k in F if inj(k) and F[k]["conc_mg_ml"]]
    ch = [k for k in pts if not F[k]["is_exit"]]
    lo_all = [k for k in ch if F[k]["conc_mg_ml"] <= CUT]
    lo_cen = [k for k in lo_all if firstd[k] not in FLOOR]
    hi_all = [k for k in ch if F[k]["conc_mg_ml"] > CUT]
    med = lambda ks: st.median([F[k]["age_y"] for k in ks])
    import random as _rnd
    def perm_p(a, b, n=20000, seed=20260915):
        pool, na = list(a) + list(b), len(a)
        obs = abs(st.median(a) - st.median(b)); rng, hits = _rnd.Random(seed), 0
        for _ in range(n):
            rng.shuffle(pool)
            if abs(st.median(pool[:na]) - st.median(pool[na:])) >= obs - 1e-12:
                hits += 1
        return (hits + 1) / (n + 1)
    age = lambda ks: [F[k]["age_y"] for k in ks]
    p_all, p_cen = perm_p(age(lo_all), age(hi_all)), perm_p(age(lo_cen), age(hi_all))
    rho_all, _ = X.spearman([F[k]["conc_mg_ml"] for k in ch], age(ch))
    rho_cen, _ = X.spearman([F[k]["conc_mg_ml"] for k in lo_cen + hi_all], age(lo_cen + hi_all))
    n_cen = len(lo_all) - len(lo_cen)

    W, L, T, PH = 1080, 132, 214, 420
    PW = W - L - 210
    lg = lambda v: math.log10(max(v, 1e-3))
    X0, X1 = lg(0.0015), lg(700)
    xs = lambda v: L + PW * (lg(v) - X0) / (X1 - X0)
    YMAX = 16.0
    ys = lambda a: T + PH - PH * min(a, YMAX) / YMAX
    body = []

    body.append(f'<rect x="{L:.1f}" y="{T:.1f}" width="{xs(CUT)-L:.1f}" height="{PH:.1f}" '
                f'fill="{CHRON}" fill-opacity="0.045"/>')
    for t in TICKS:
        if not (X0 <= lg(t) <= X1):
            continue
        body.append(f'<line x1="{xs(t):.1f}" y1="{T:.1f}" x2="{xs(t):.1f}" '
                    f'y2="{T+PH:.1f}" stroke="{S.RULE}" stroke-width="1"/>')
        lab = f"{t:g}" if t >= 1 else f"{t}".rstrip("0")
        body.append(S.txt(xs(t), T + PH + 20, lab, size=11, fill=S.MUTED,
                          anchor="middle", tab=True))
    body.append(S.txt(L, T + PH + 42, "concentration, mg per mL — a log axis, five orders of magnitude",
                      size=12, fill=S.INK2))
    for g in range(0, int(YMAX) + 1, 4):
        body.append(f'<line x1="{L:.1f}" y1="{ys(g):.1f}" x2="{L+PW:.1f}" y2="{ys(g):.1f}" '
                    f'stroke="{S.RULE}" stroke-width="1"/>')
        body.append(S.txt(L - 10, ys(g) + 4, f"{g}", size=11, fill=S.MUTED,
                          anchor="end", tab=True))
    body.append(S.txt(L - 10, T - 38, "years on the", size=11, fill=S.INK2, anchor="end"))
    body.append(S.txt(L - 10, T - 24, "FDA list", size=11, fill=S.INK2, anchor="end"))

    body.append(f'<line x1="{xs(CUT):.1f}" y1="{T-52:.1f}" x2="{xs(CUT):.1f}" '
                f'y2="{T+PH:.1f}" stroke="{S.BASELINE}" stroke-width="1.3"/>')
    body.append(S.txt(xs(CUT) - 10, T - 56, f"dilute — median {med(lo_cen):.1f} years short", size=11,
                      fill=CHRON, weight="600", anchor="end"))
    body.append(S.txt(xs(CUT) - 10, T - 42, f"{med(lo_all):.1f} if the {n_cen} censored dates are believed",
                      size=10, fill=S.MUTED, anchor="end"))
    body.append(S.txt(xs(CUT) + 10, T - 56, f"concentrated — median {med(hi_all):.1f}", size=11,
                      fill=S.MUTED, weight="600"))
    body.append(S.txt(xs(CUT) + 10, T - 42, f"none of these {len(hi_all)} is censored",
                      size=10, fill=S.MUTED))

    for half, ks in (("lo", [k for k in ch if F[k]["conc_mg_ml"] <= CUT
                             and firstd[k] not in FLOOR]),
                     ("hi", [k for k in ch if F[k]["conc_mg_ml"] > CUT])):
        m = st.median([F[k]["age_y"] for k in ks])
        x0 = L if half == "lo" else xs(CUT)
        x1 = xs(CUT) if half == "lo" else L + PW
        body.append(f'<line x1="{x0+6:.1f}" y1="{ys(m):.1f}" x2="{x1-6:.1f}" y2="{ys(m):.1f}" '
                    f'stroke="{CHRON if half=="lo" else S.MUTED}" stroke-width="1.6" '
                    f'stroke-dasharray="7 5"/>')

    dots = [(xs(F[k]["conc_mg_ml"]), ys(F[k]["age_y"]), k) for k in pts]
    for cx, cy, k in dots:
        col = EXIT if F[k]["is_exit"] else CHRON
        if firstd[k] in FLOOR:      # a ring: the date is the bulk load, the real one is earlier
            body.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.6" fill="none" '
                        f'stroke="{col}" stroke-width="1.8"/>')
            body.append(f'<path d="M{cx:.1f} {cy-7:.1f} L{cx:.1f} {cy-16:.1f}" stroke="{col}" '
                        f'stroke-width="1.1" stroke-dasharray="2 2"/>')
        else:
            body.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="{col}" '
                        f'fill-opacity="0.85"/>')
    # Label only the long-running ones, and only where the text clears every other dot
    # as well as every label already placed — overprinting a mark hides a data point.
    placed = []
    for cx, cy, k in sorted(dots, key=lambda t: -F[t[2]]["age_y"]):
        if F[k]["age_y"] < 5.5 or F[k]["is_exit"]:
            continue
        w = 7 + len(F[k]["name"]) * 5.2
        clear = all(not (cx + 4 < px < cx + w and abs(cy - py) < 7)
                    for px, py, _ in dots)
        if clear and all(abs(cx - px) > w or abs(cy - py) > 13 for px, py in placed):
            body.append(S.txt(cx + 7, cy + 4, F[k]["name"], size=9.5, fill=S.INK2))
            placed.append((cx, cy))

    ly = T + 24
    for c, lab in ((CHRON, "still in short supply"), (EXIT, "being discontinued")):
        body.append(f'<circle cx="{W-200:.1f}" cy="{ly-4:.1f}" r="4" fill="{c}"/>')
        body.append(S.txt(W - 190, ly, lab, size=10.5, fill=S.INK2))
        ly += 17
    body.append(f'<circle cx="{W-200:.1f}" cy="{ly-4:.1f}" r="4.6" fill="none" '
                f'stroke="{CHRON}" stroke-width="1.8"/>')
    body.append(S.txt(W - 190, ly, "date is the 2012 bulk load —", size=10.5, fill=S.INK2))
    body.append(S.txt(W - 190, ly + 14, "the real start is earlier", size=10.5, fill=S.INK2))
    note, _h = S.para(W - 200, T + 106,
                      "Exits are young at every concentration, which is the control. But "
                      "all four censored points are dilute and none of the eleven "
                      "concentrated ones is — so the gap is censored in the direction "
                      "that flatters it.",
                      size=10, fill=S.MUTED, chars=30, leading=13)
    body += note

    svg = S.frame(
        W, T + PH + 156,
        "Dilute injectables looked like the ones that never come back — on half the register",
        "Every injectable the FDA lists as short whose concentration can be parsed from its "
        "presentation string. The direction is consistent; the magnitude rests on four "
        "substances whose posting date is the database's own 2012 bulk load.",
        body,
        footer=[
            f"Shipped as advice on half the register. On all {len(ch)} chronic injectables the gap is p = "
            f"{p_all:.3f}; without the {n_cen} bulk-load dates, p = {p_cen:.3f}. A prior at best, not a rule.",
            f"Split at the median, 10 mg/mL, not an optimised cut. All {len(ch)}: gap {med(lo_all)-med(hi_all):.1f}y, "
            f"p = {p_all:.3f}, rho {rho_all:+.2f}. Excluding the {n_cen} censored: gap {med(lo_cen)-med(hi_all):.1f}y, "
            f"p = {p_cen:.3f}, rho {rho_cen:+.2f} on {len(lo_cen)+len(hi_all)}.",
            "Concentration parses for 61 of 73 injectables (84%). Lyophilised powders and "
            "unit-dosed biologics have no mg/mL and are absent, not zero.",
            "Package counts (rho +0.51) and firm counts (+0.37) track age better and are unusable: "
            "both accumulate BECAUSE a shortage persists.",
            "A molecule's mg/mL cannot be caused by its own shortage, which is why the weaker "
            "correlate is the one drawn. It is not separable from mass per container (rho +0.77).",
            "Age is time on the list, not expected duration: every row is still open, so this is "
            "the age of the current backlog. Concentration proxies value density, not margin.",
        ])
    print(S.write("negative/5-dilute.svg", svg))
    print(f"  all {len(ch)}: {med(lo_all):.1f} vs {med(hi_all):.1f} y, p {p_all:.4f}, rho {rho_all:+.2f} | censored dropped: {med(lo_cen):.1f} vs {med(hi_all):.1f}, p {p_cen:.4f}, rho {rho_cen:+.2f} | n_cen {n_cen}")


if __name__ == "__main__":
    main()
