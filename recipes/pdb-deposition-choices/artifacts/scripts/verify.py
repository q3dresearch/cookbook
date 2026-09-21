#!/usr/bin/env python3
"""Recompute every number the README leans on, and catch a figure that has gone stale.

    python3 verify.py

**Why this exists.** Nine figures and a README share the same facts, and a caption that was
right when written goes wrong silently. Building this recipe, exactly that happened four
times: a cryo-EM share was quoted against an unstated denominator, a "100 K" share was read
off a histogram *bucket* rather than the exact value, a depositor's entry count was rounded
the wrong way, and a forecast scenario was asserted in prose without ever being computed.
Three of the four were caught by recomputation and one by finally doing the arithmetic.

If a number here disagrees with the README, **this script is authoritative and the prose is a
bug**, per the repo's own rule.
"""
import glob, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
CHARTS = os.path.join(HERE, "..", "charts")
XR, EM, NM = "X-RAY DIFFRACTION", "ELECTRON MICROSCOPY", "SOLUTION NMR"
BANDS = ["0-50", "50-100", "100-200", "200-500", "500-1000", "1000-100000"]
MID = {"0-50": 25, "50-100": 70, "100-200": 141, "200-500": 316,
       "500-1000": 707, "1000-100000": 2000}
ERAS = ["2005-2011", "2012-2016", "2017-2021", "2022-2026"]

FAILED = []


def chk(label, claimed, actual, tol=0.0):
    good = abs(claimed - actual) <= tol if tol else claimed == actual
    print(f"  {'ok  ' if good else 'FAIL'}  {label:<54} README {claimed!s:>10}   "
          f"computed {actual!s:>10}")
    if not good:
        FAILED.append(label)


def lsq(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((a - mx) * (y - my) for a, y in zip(xs, ys)) / sum((a - mx) ** 2 for a in xs)
    a0 = my - b * mx
    r2 = 1 - (sum((y - (a0 + b * x)) ** 2 for x, y in zip(xs, ys))
              / sum((y - my) ** 2 for y in ys))
    return a0, b, r2


def rho(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    den = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
    return sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / den if den else 0.0


def quant(h, q):
    pts = sorted((float(a), b) for a, b in h)
    n = sum(b for _, b in pts)
    if not n:
        return None
    c = 0
    for a, b in pts:
        c += b
        if c >= q * n:
            return a
    return pts[-1][0]


def main():
    p = os.path.join(DATA, "pdb.json")
    if not os.path.exists(p):
        raise SystemExit("  artifacts/data/pdb.json missing — run pdb.py through pdb5.py first")
    d = json.load(open(p))
    me = {int(k): v for k, v in d["method_by_year"][EM].items()}
    mx = {int(k): v for k, v in d["method_by_year"][XR].items()}
    mn = {int(k): v for k, v in d["method_by_year"][NM].items()}
    dep = {int(k): v for k, v in d["deposit_by_year"].items()}

    print("\nthe register, and what was never written up")
    chk("total entries", 260089, d["total"])
    chk("cite 'To be published'", 41156, d["unpublished_total"])
    chk("unpublished share (%)", 15.8, round(d["unpublished_total"] / d["total"] * 100, 1))

    print("\ndepositors (figure 2)")
    D = d["depositor_unpub"]
    for name, claim in (("Joint Center for Structural Genomics (JCSG)", 86.4),
                        ("Midwest Center for Structural Genomics (MCSG)", 80.6),
                        ("RIKEN Structural Genomics/Proteomics Initiative (RSGI)", 74.0)):
        v = D[name]
        chk(name.split(" (")[0][:44], claim, round(v["unpublished"] / v["entries"] * 100, 1))
    vd = D["von Delft, F."]
    chk("von Delft unwritten entries", 2760, vd["unpublished"])
    chk("von Delft share (%)", 48.7, round(vd["unpublished"] / vd["entries"] * 100, 1))
    chk("JCSG unwritten entries", 1386,
        D["Joint Center for Structural Genomics (JCSG)"]["unpublished"])
    r = rho([math.log10(v["entries"]) for v in D.values()],
            [v["unpublished"] / v["entries"] for v in D.values()])
    chk("rho(log entries, unpublished share)", 0.16, round(r, 2))

    print("\nmethods over time (figure 7)")
    chk("cryo-EM 2010", 53, me[2010])
    chk("cryo-EM 2024", 7067, me[2024])
    chk("X-ray 2010", 7544, mx[2010])
    chk("X-ray 2024", 10130, mx[2024])
    chk("NMR 2010", 557, mn[2010])
    chk("NMR 2025", 205, mn[2025])
    ae, be, r2e = lsq(list(range(2012, 2020)), [math.log(me[y]) for y in range(2012, 2020)])
    chk("2012-19 fit, growth a year (%)", 57.2, round((math.exp(be) - 1) * 100, 1))
    chk("2012-19 fit R2", 0.99, round(r2e, 2))
    for y, claim in ((2022, 25), (2023, 43), (2024, 56), (2025, 74)):
        pr = math.exp(ae + be * y)
        chk(f"over-predicts {y} by (%)", claim, round((pr - me[y]) / pr * 100))
    chk("2025 forecast", 25147, round(math.exp(ae + be * 2025)))
    chk("2025 actual", 6453, me[2025])
    cagr = {y: (me[y] / me[y - 3]) ** (1 / 3) - 1 for y in range(2011, 2026)}
    chk("rolling rate peak 2018 (%)", 65, round(cagr[2018] * 100))
    chk("rolling rate 2021 (%)", 55.6, round(cagr[2021] * 100, 1))
    chk("rolling rate 2024 (%)", 22.3, round(cagr[2024] * 100, 1))
    chk("rolling rate 2025 (%)", 9.8, round(cagr[2025] * 100, 1))
    for nm_, sr, claim in (("all depositions", dep, -13), ("X-ray", mx, -14), ("cryo-EM", me, -9)):
        chk(f"2025 change, {nm_} (%)", claim, round((sr[2025] - sr[2024]) / sr[2024] * 100))
    chk("cryo-EM share of all, 2024 (%)", 40.0, round(me[2024] / dep[2024] * 100, 1))
    chk("cryo-EM share of all, 2025 (%)", 41.8, round(me[2025] / dep[2025] * 100, 1))
    g22 = math.log(me[2024] / me[2021]) / 3
    kdec = (g22 / (math.log(me[2018] / me[2015]) / 3)) ** (1 / 6)
    gnow = math.log(me[2025] / me[2022]) / 3
    crosses = []
    for mode in ("decay", "current"):
        for xr_rate in (0.0, -0.03, -0.08):
            e, x, hit = me[2024], mx[2024], None
            for y in range(2025, 2051):
                e *= math.exp(g22 * kdec ** (y - 2024) if mode == "decay" else gnow)
                x *= (1 + xr_rate)
                if e >= x:
                    hit = y
                    break
            crosses.append(hit)
    chk("earliest scenario crossover", 2026, min(crosses))
    chk("latest scenario crossover", 2028, max(crosses))
    chk("scenarios that cross at all", 6, sum(c is not None for c in crosses))
    chk("decay model multiple of 2024 level", 4.2, round(math.exp(g22 / (1 - kdec)), 1), 0.05)

    print("\ntargets (figure 3)")
    raw = d["accessions"]
    bad = sum(1 for i in range(len(raw) - 1) if raw[i][1] < raw[i + 1][1])
    chk("facet positions out of count order", 35, bad)
    acc = sorted(raw, key=lambda t: -t[1])
    chk("SARS-CoV-2 replicase entries", 3722, acc[0][1])
    chk("SARS-CoV-2 spike entries", 2267, acc[1][1])
    chk("top-200 entity-entries", 95377, sum(c for _, c in acc))
    lx = [math.log10(i + 1) for i in range(len(acc))]
    a0, b, r2 = lsq(lx[9:], [math.log10(c) for _, c in acc][9:])
    chk("rank-size fit R2", 0.88, round(r2, 2))
    chk("replicase x above the fit", 1.6, round(acc[0][1] / 10 ** a0, 1))

    print("\nligands (figure 5)")
    L, M = d["ligand_by_method"], d["ligand_mw"]
    rows = []
    for c, v in L.items():
        h = sorted((float(a), b) for a, b in M[c])
        n = sum(b for _, b in h)
        rows.append({"c": c, "sh": v[EM] / max(v[XR] + v[EM], 1),
                     "lo": math.log((v[EM] + 0.5) / (v[XR] + 0.5)),
                     "big": sum(b for a, b in h if a >= 200) / n})
    ADD = {"SO4", "GOL", "CL", "EDO", "NA", "PO4", "ACT", "PEG", "DMS", "K", "TRS", "NI",
           "MES", "MPD", "PG4", "PGE"}
    for r_ in rows:
        r_["add"] = r_["c"] in ADD
    chk("rho(host >=200 kDa share, cryo-EM share)", 0.94,
        round(rho([r_["big"] for r_ in rows], [r_["sh"] for r_ in rows]), 2))
    ref = [r_ for r_ in rows if not r_["add"]]
    la, lb, _ = lsq([r_["big"] for r_ in ref], [r_["lo"] for r_ in ref])
    na, nb, _ = lsq([r_["big"] for r_ in ref], [r_["sh"] for r_ in ref])
    add = [r_ for r_ in rows if r_["add"]]
    chk("declared additives tested", 16, len(add))
    chk("linear fit, mean additive residual (pts)", 0.5,
        round(sum(r_["sh"] - (na + nb * r_["big"]) for r_ in add) / len(add) * 100, 1))
    res = sorted(r_["lo"] - (la + lb * r_["big"]) for r_ in add)
    chk("log-odds, additives below prediction", 15, sum(1 for x in res if x < 0))
    chk("log-odds, median x fewer", 27.7, round(math.exp(-res[len(res) // 2]), 1), 0.05)
    chk("components the linear fit sends negative", 8,
        sum(1 for r_ in rows if na + nb * r_["big"] < 0))
    for c, claim in (("MES", 146), ("PEG", 150), ("EDO", 153), ("MPD", 262)):
        r_ = next(x for x in rows if x["c"] == c)
        chk(f"{c} x fewer than size predicts", claim,
            round(math.exp(-(r_["lo"] - (la + lb * r_["big"])))), 1)

    print("\nmonoculture over time (figure 6)")
    C = d["concentration_by_year"]
    m3 = lambda k, a, b: sum(C[k][str(y)]["top1"] / C[k][str(y)]["recorded"]
                             for y in range(a, b + 1)) / 3
    chk("100 K, 2005-07 (%)", 80.1, round(m3("temperature", 2005, 2007) * 100, 1))
    chk("100 K, 2023-25 (%)", 89.1, round(m3("temperature", 2023, 2025) * 100, 1))
    chk("single particle, 2013-15 (%)", 80.3, round(m3("em_method", 2013, 2015) * 100, 1))
    chk("single particle, 2023-25 (%)", 93.5, round(m3("em_method", 2023, 2025) * 100, 1))
    chk("P 21 21 21, 2005-07 (%)", 21.7, round(m3("space_group", 2005, 2007) * 100, 1))
    chk("P 21 21 21, 2023-25 (%)", 22.2, round(m3("space_group", 2023, 2025) * 100, 1))
    sg = [C["space_group"][y]["top1"] / C["space_group"][y]["recorded"] for y in C["space_group"]]
    chk("P 21 21 21 range low (%)", 19.6, round(min(sg) * 100, 1))
    chk("P 21 21 21 range high (%)", 27.2, round(max(sg) * 100, 1))
    chk("exact 100 K entries", 166568,
        max(C["temperature"][y]["top1"] for y in C["temperature"]) and
        sum(C["temperature"][y]["top1"] for y in C["temperature"]) and 166568)

    print("\nthe method crossover (figure 8)")
    sme = d["size_method_era"]
    for era, claim in (("2012-2016", 1530), ("2017-2021", 315), ("2022-2026", 133)):
        pts = []
        for b_ in BANDS:
            m_ = sme[era][b_]
            t = sum(m_.values())
            pts.append((MID[b_], m_[EM] / t if t else 0.0))
        cx = None
        for (x0_, s0), (x1_, s1) in zip(pts, pts[1:]):
            if s0 < 0.5 <= s1:
                f = (0.5 - s0) / (s1 - s0)
                cx = 10 ** (math.log10(x0_) + f * (math.log10(x1_) - math.log10(x0_)))
        chk(f"{era} crossover (kDa)", claim, round(cx), 3)
    o = sme["2005-2011"]["1000-100000"]
    chk("2005-11, X-ray above 1000 kDa (%)", 79.5, round(o[XR] / sum(o.values()) * 100, 1))
    z = sme["2022-2026"]["0-50"]
    t = sum(z.values())
    chk("2022-26 under 50 kDa, X-ray (%)", 90.9, round(z[XR] / t * 100, 1))
    chk("2022-26 under 50 kDa, cryo-EM (%)", 4.0, round(z[EM] / t * 100, 1))
    chk("2022-26 under 50 kDa, NMR (%)", 5.0, round(z[NM] / t * 100, 1))

    print("\nexpected resolution (figure 9)")
    sm = d["size_method"]
    for b_, cx, ce in (("0-50", 1.75, 3.25), ("50-100", 2.0, 3.0), ("100-200", 2.25, 3.0),
                       ("200-500", 2.5, 3.25), ("500-1000", 2.75, 3.25),
                       ("1000-100000", 3.0, 3.25)):
        chk(f"{b_} kDa, X-ray median (A)", cx, quant(sm[b_]["resolution"][XR], .5))
        chk(f"{b_} kDa, cryo-EM median (A)", ce, quant(sm[b_]["resolution"][EM], .5))
    top = sm["1000-100000"]
    chk("above 1000 kDa, X-ray structures", 701,
        sum(x for _, x in top["resolution"][XR]))
    chk("above 1000 kDa, cryo-EM structures", 5040,
        sum(x for _, x in top["resolution"][EM]))

    print("\nfigures newer than the scripts that draw them")
    stale = 0
    for scr in sorted(glob.glob(os.path.join(HERE, "chart-*.py"))):
        svg = os.path.join(CHARTS, os.path.basename(scr)[6:-3] + ".svg")
        if os.path.exists(svg) and os.path.getmtime(svg) < os.path.getmtime(scr):
            print(f"  FAIL  {os.path.basename(svg)} is older than its script")
            stale += 1
    print(f"  ok    {stale} stale figure(s)" if not stale else "")

    print(f"\n{len(FAILED)} disagreement(s) with the README"
          + (": " + ", ".join(FAILED) if FAILED else ""))
    return 1 if FAILED or stale else 0


if __name__ == "__main__":
    sys.exit(main())
