#!/usr/bin/env python3
"""The join this recipe owed: does a metals price explain the recovery share?

    python3 metals.py

Two sections of this recipe reached for a commodity-price explanation and neither could test
it. This is the test. The hypothesis, written before the answer was seen:

    **H1.** The share of metal-bearing residue that is recovered rather than buried rises
    with the real price of the metals recovered from it.

**Power, stated first.** The Biennial Report is biennial and starts in 2001, so there are
eleven observations and no more. 2021 publishes no tonnage. 2023 has no price on this
instrument. 2015 is the cycle Steel Dust Recycling did not file and its recovery rate is an
artefact. That leaves **nine usable pairs**, at which a Spearman correlation needs |rho| >=
0.68 to reach p < 0.05. Anything smaller than that is not detectable here and a null result
means "this design could not see it", not "there is nothing there".
"""
import collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brdata                                                            # noqa: E402

DATA = os.path.join(HERE, "..", "data", "metals")
FAM = {"W304", "W319", "W504", "W309", "W312", "W505"}
num, REC, DIS = brdata.num, brdata.RECOVERY, brdata.DISPOSAL
TAINTED = {2015: "Steel Dust Recycling did not file this cycle"}


def prices(metal):
    """{year: (nominal $/t, constant 1998 $/t)} from the USGS workbook."""
    import openpyxl
    wb = openpyxl.load_workbook(os.path.join(DATA, f"ds140-{metal}.xlsx"), data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(c or "") for c in rows[4]]
    ni = hdr.index("Unit value ($/t)")
    ri = next(i for i, h in enumerate(hdr) if h.startswith("Unit value (98"))
    out = {}
    for r in rows[5:]:
        y = str(r[0] or "").strip()
        if y.isdigit() and r[ni] not in (None, "NA") and r[ri] not in (None, "NA"):
            out[int(y)] = (float(r[ni]), float(r[ri]))
    return out


def recovery():
    out = {}
    for y in brdata.CYCLES:
        a = b = 0.0
        for r in brdata.load(y):
            if r["form_code"] not in FAM:
                continue
            t = num(r["managed_tons"])
            if t <= 0:
                continue
            c = r["management_category"]
            if c in REC:
                a += t
            elif c in DIS:
                b += t
        if a + b > 1000:
            out[y] = (a, b, a / (a + b))
    return out


def spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                rk[order[k]] = avg
            i = j + 1
        return rk
    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx) ** 0.5
    vy = sum((b - my) ** 2 for b in ry) ** 0.5
    return cov / (vx * vy) if vx and vy else 0.0


def permute(xs, ys, rho, n=20000, seed=11):
    import random
    rnd = random.Random(seed)
    ys = list(ys)
    hits = 0
    for _ in range(n):
        rnd.shuffle(ys)
        if abs(spearman(xs, ys)) >= abs(rho):
            hits += 1
    return (hits + 1) / (n + 1)


def main():
    rec = recovery()
    zn, pb = prices("zinc"), prices("lead")
    print("cycle   recovered   buried   rate   zinc 98$/t   lead 98$/t   note")
    rows = []
    for y in sorted(rec):
        a, b, r = rec[y]
        z = zn.get(y, (None, None))[1]
        l = pb.get(y, (None, None))[1]
        note = TAINTED.get(y, "" if (z and l) else "no price on this instrument")
        print(f"{y}   {a/1e3:>8,.0f}k {b/1e3:>7,.0f}k {r:>6.0%}   "
              f"{z if z else '—':>10}   {l if l else '—':>10}   {note}")
        if z and l and y not in TAINTED:
            rows.append((y, r, z, l, a))
    print(f"\nusable pairs: {len(rows)}  ({', '.join(str(r[0]) for r in rows)})")

    out = {"n": len(rows), "years": [r[0] for r in rows], "tests": {}}
    for lab, xi in (("real zinc price", 2), ("real lead price", 3)):
        for dep, di, dl in ((("recovery share"), 1, "{:.0%}"), ("recovered tons", 4, "{:,.0f}")):
            xs = [r[xi] for r in rows]
            ys = [r[di] for r in rows]
            rho = spearman(xs, ys)
            p = permute(xs, ys, rho)
            lo, hi = min(xs), max(xs)
            ylo = [r[di] for r in rows if r[xi] <= sorted(xs)[len(xs) // 3]]
            yhi = [r[di] for r in rows if r[xi] >= sorted(xs)[-(len(xs) // 3)]]
            med = lambda v: sorted(v)[len(v) // 2]
            print(f"\n  {dep} vs {lab}:  rho {rho:+.2f}   p {p:.3f}   "
                  f"(detectable at |rho|>=0.68)")
            print(f"     price spans {lo:,.0f} to {hi:,.0f} 98$/t; "
                  f"{dep} in the cheapest third {dl.format(med(ylo))}, "
                  f"dearest third {dl.format(med(yhi))}")
            out["tests"][f"{dep} vs {lab}"] = {
                "rho": round(rho, 3), "p": round(p, 4),
                "median_low_third": med(ylo), "median_high_third": med(yhi)}
    open(os.path.join(HERE, "..", "data", "metals", "join.json"), "w").write(
        json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
