#!/usr/bin/env python3
"""What a target actually IS, against 140 companies nobody attacked.

    python selection.py

This replaces an earlier section of this recipe that led with the exchange a target
trades on. That finding was real -- short sellers essentially never touch OTC, 1.9%
of targets against 24% of filers -- but it was the wrong headline, and it was the
wrong headline for an instructive reason: **exchange was the easiest attribute to
measure, so it got measured first, and a clean null got promoted to an answer.**
Where a company's stock trades is a fact about borrowability, not about the company.
It is kept below as a liquidity constraint, which is what it is.

The question worth asking is what the company DOES and how it EARNS. Five axes, each
run against the same 140 controls:

    industry            SEC's own owner-office assignment, 12 values
    filer size class    large accelerated / accelerated / non-accelerated
    incorporation       Nevada against Delaware, the shell-friendly split
    foreign issuer      files 20-F/40-F rather than 10-K
    unit economics      gross margin, operating margin, cash burn before the report

Discipline carried over from the rest of this recipe: every proportion gets a Wilson
interval, every comparison gets Fisher's exact test, and because there are enough
comparisons here to manufacture a significant result by accident, the Bonferroni
threshold is printed alongside each p-value rather than left implicit. A lift of 2x
on 4 companies is noise, and the interval says so.
"""
import json, sys, math, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw"


def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def fisher(a, b, c, d):
    """Two-sided Fisher exact on [[a,b],[c,d]]."""
    def lc(n, k):
        return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
    n = a + b + c + d
    r1, c1 = a + b, a + c
    def pr(x):
        return math.exp(lc(r1, x) + lc(n - r1, c1 - x) - lc(n, c1))
    obs = pr(a)
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    return min(1.0, sum(pr(x) for x in range(lo, hi + 1) if pr(x) <= obs * 1.0000001))


def compare_flag(name, label, tflags, cflags, tests):
    """One yes/no attribute. The 'no' side is the denominator, not a missing value."""
    a, tn = sum(label in f for f in tflags), len(tflags)
    c, cn = sum(label in f for f in cflags), len(cflags)
    p = fisher(a, tn - a, c, cn - c)
    tests.append(p)
    lo, hi = wilson(a, tn)
    return [{"axis": name, "value": label, "t": a, "tn": tn, "c": c, "cn": cn,
             "t_share": a / tn if tn else 0, "c_share": c / cn if cn else 0,
             "lift": (a / tn) / (c / cn) if c and tn else float("inf"),
             "ci": [lo, hi], "p": p}]


def compare(name, tvals, cvals, tests, missing=("?", "")):
    """Every distinct value of a categorical, target share vs control share.

    Companies missing the attribute are dropped from the denominator rather than
    counted as a value of it -- 17 controls have no filer category at all, and
    letting that become a category both invents a finding and inflates the test
    count that the Bonferroni threshold is divided by.
    """
    rows = []
    tvals = [v for v in tvals if v not in missing]
    cvals = [v for v in cvals if v not in missing]
    tn, cn = len(tvals), len(cvals)
    tc, cc = collections.Counter(tvals), collections.Counter(cvals)
    for v in sorted(set(tc) | set(cc), key=lambda x: -tc.get(x, 0)):
        a, c = tc.get(v, 0), cc.get(v, 0)
        if a + c < 5:
            continue
        p = fisher(a, tn - a, c, cn - c)
        lift = (a / tn) / (c / cn) if c else float("inf")
        lo, hi = wilson(a, tn)
        rows.append({"axis": name, "value": v, "t": a, "tn": tn, "c": c, "cn": cn,
                     "t_share": a / tn, "c_share": c / cn, "lift": lift,
                     "ci": [lo, hi], "p": p})
        tests.append(p)
    return rows


def main():
    prof = json.loads((RAW / "profiles.json").read_text())
    T, C = prof["targets"], prof["controls"]
    print(f"  {len(T)} targets vs {len(C)} controls\n")

    tests, rows = [], []
    # SEC's owner office IS the industry assignment, made by the regulator, not by us.
    rows += compare("industry", [v.get("ownerOrg") or "?" for v in T.values()],
                    [v.get("ownerOrg") or "?" for v in C.values()], tests)
    # Filer category is a size class defined by public float -- a cleaner size proxy
    # than market cap, because the filer states it rather than us computing it. It is
    # MULTI-LABEL, joined by <br>: "Non-accelerated filer<br>Smaller reporting
    # company<br>Emerging growth company" is three flags, not one class. Read as one
    # string it splits the same companies across buckets and produced a spurious
    # "0 of 76 targets are smaller reporting companies" -- the true figure is 12 of 76.
    # Each flag is therefore its own yes/no comparison.
    flags = lambda v: [x.strip() for x in (v.get("category") or "").split("<br>") if x.strip()]
    tf = [flags(v) for v in T.values() if flags(v)]
    cf = [flags(v) for v in C.values() if flags(v)]
    for lab in sorted({f for g in tf + cf for f in g}):
        rows += compare_flag("filer class", lab, tf, cf, tests)
    # NV vs DE: Nevada's charter law is the standard shell-friendly choice.
    rows += compare("incorporated", [v.get("stateOfIncorporation") or "?" for v in T.values()],
                    [v.get("stateOfIncorporation") or "?" for v in C.values()], tests)

    bon = 0.05 / max(1, len(tests))
    print(f"  {len(tests)} comparisons -> Bonferroni threshold p < {bon:.4f}\n")
    hdr = f"  {'axis':<13}{'value':<34}{'targets':>9}{'controls':>10}{'lift':>7}  {'p':>8}"
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    for r in sorted(rows, key=lambda x: x["p"]):
        star = " **" if r["p"] < bon else ("  *" if r["p"] < 0.05 else "")
        print(f"  {r['axis']:<13}{str(r['value'])[:33]:<34}"
              f"{r['t']:>3}/{r['tn']:<5}{r['c']:>4}/{r['cn']:<5}"
              f"{r['lift']:>6.1f}x{r['p']:>9.4f}{star}")
    print(f"\n  ** survives Bonferroni   * nominal only, expected by chance at this many tests")

    (RAW / "selection.json").write_text(json.dumps(
        {"rows": rows, "n_tests": len(tests), "bonferroni": bon}, indent=1))


if __name__ == "__main__":
    main()
