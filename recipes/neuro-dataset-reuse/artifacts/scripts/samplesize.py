#!/usr/bin/env python3
"""How big a neuroimaging study is, and whether that changed over a decade.

    python3 samplesize.py

This is the one question in this recipe that is about neuroscience rather than about the
repository. It has an answer the field itself argues about.

**The median MRI dataset went from 23 subjects to 31 in ten years.** The log-linear trend is
real -- **1.84x per decade, t = +4.42** -- but almost none of it is in the middle. p10 moved
**4 to 5** and p25 moved **13 to 13**. The bottom half of the distribution did not move at all.
p90 went 59 to 119 and p99 went 272 to 969.

**So the distribution did not shift, it stretched.** A handful of consortium-scale deposits
carry the entire trend while the typical lab collects the same thirty people it collected in
2016.

**Why that matters, in the field's own terms.** Marek et al. (Nature, 2022) argued that
reproducible brain-wide association studies need thousands of participants. In 2025-26,
**0.9% of deposited MRI datasets have a thousand or more**, and 13% have a hundred.

**What this does not say.** Not every study is a brain-wide association study: task fMRI
asking a within-subject question is properly powered at twenty or thirty, and iEEG has a median
of four because it needs a neurosurgical patient. A flat median is only a failure against the
subset of questions that need scale. The plate draws the distribution and names the benchmark;
it does not claim every mark should be above it.

**And it is a deposit archive, not a census of the field.** These are the studies whose authors
chose to share. Large consortium projects are disproportionately likely to do that, which
biases the upper tail **upwards** -- so the flat median is, if anything, generous.
"""
import json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fold, modality                                                    # noqa: E402

MOD = "mri"
BENCH = 1000            # Marek et al. 2022, "thousands of individuals"
MIN_N = 15


def rows(mod=MOD):
    out = []
    for r in fold.load()["rows"]:
        if r["subjects"] <= 0 or modality.modality(r) != mod:
            continue
        out.append(dict(r, yr=int(r["pub"][:4])))
    return out


def pct(vals, p):
    v = sorted(vals)
    return v[min(len(v) - 1, int(len(v) * p))]


def by_year(rs):
    out = []
    for y in sorted({r["yr"] for r in rs}):
        g = [r["subjects"] for r in rs if r["yr"] == y]
        if len(g) < MIN_N:
            continue
        out.append({"year": y, "n": len(g),
                    "p10": pct(g, .10), "p25": pct(g, .25), "p50": pct(g, .50),
                    "p75": pct(g, .75), "p90": pct(g, .90), "max": max(g),
                    "over": sum(1 for v in g if v >= BENCH) / len(g)})
    return out


def trend(rs):
    """Log-linear slope in subjects per decade, with a t statistic."""
    x = [r["yr"] - 2020 for r in rs]
    y = [math.log10(r["subjects"]) for r in rs]
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sxx
    res = [c - (my + b * (a - mx)) for a, c in zip(x, y)]
    se = (sum(e * e for e in res) / (n - 2) / sxx) ** .5
    return {"per_decade": 10 ** (b * 10), "t": b / se, "n": n}


def eras(rs, bands=((2016, 2018), (2019, 2021), (2022, 2024), (2025, 2026))):
    out = []
    for lo, hi in bands:
        g = [r["subjects"] for r in rs if lo <= r["yr"] <= hi]
        if not g:
            continue
        out.append({"era": f"{lo}-{hi}", "n": len(g),
                    **{k: pct(g, p) for k, p in
                       (("p10", .10), ("p25", .25), ("p50", .50),
                        ("p75", .75), ("p90", .90), ("p99", .99))},
                    "over": sum(1 for v in g if v >= BENCH) / len(g)})
    return out


def main():
    rs = rows()
    t = trend(rs)
    print(f"\n  {len(rs):,} {MOD.upper()} datasets with a subject count")
    print(f"  trend {t['per_decade']:.2f}x per decade, t = {t['t']:+.2f}\n")
    print(f"  {'era':<11}{'n':>5}{'p10':>6}{'p25':>6}{'p50':>6}{'p75':>6}{'p90':>7}"
          f"{'p99':>8}{'>=1000':>9}")
    for e in eras(rs):
        print(f"  {e['era']:<11}{e['n']:>5}{e['p10']:>6}{e['p25']:>6}{e['p50']:>6}"
              f"{e['p75']:>6}{e['p90']:>7}{e['p99']:>8}{e['over']:>9.1%}")
    a, b = eras(rs)[0], eras(rs)[-1]
    print(f"\n  change over the decade: "
          + "  ".join(f"{k} {a[k]}->{b[k]} ({b[k]/a[k]:.2f}x)"
                      for k in ("p10", "p25", "p50", "p75", "p90", "p99")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
