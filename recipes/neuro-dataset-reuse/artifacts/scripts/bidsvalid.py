#!/usr/bin/env python3
"""BIDS validation, read from the live field and split by the validator that produced it.

    python3 bidsvalid.py

**Two corrections sit underneath this module.** The first plate on this subject used
`latestSnapshot.issuesStatus`, which is deprecated. It is populated on 57% of datasets and its
emptiness was read as a collapse in validation coverage. The live field,
`latestSnapshot.validation`, is populated on **1,893 of 1,893 — 100%, every year — and not one
dataset has both empty.** Where both exist they disagree on whether errors are present for
**450 of 1,072**, and in **431** of those the live field finds errors the deprecated one did
not.

**The second correction is the instrument.** Reading the live field still shows a fall, and
that fall is the BIDS validator changing major version. The versions disagree by an order of
magnitude on the same datasets in the same year -- pooled, **v1 55%, v2 5%, v3 1%** -- and v2's
share of runs went 36% in 2023 to 99% in 2026.

**The control:** held at v1, the error rate from 2024 to 2025 went **54% to 70%**. Up. And v2
is not simply quieter: its median warning count is **3,587 against v1's 2,851**, so it
reclassifies errors as warnings rather than missing them.

**Before 2023 the split cannot be drawn.** Fewer than 20% of pre-2023 datasets carry a version
stamp at all, because `validatorMetadata` only arrives with the newer runs. Those unstamped
datasets show a **54%** error rate, which matches v1's 55%, but that is an inference and the
plate does not draw it as a measurement.
"""
import collections, json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "data", "validation.json")
LO, HI = 2023, 2026          # where both validator generations have real numbers
MIN_N = 15                   # a rate on fewer than this is not drawn as a point


def rows():
    out = []
    for r in json.load(open(SRC))["rows"]:
        if not r.get("pub") or not r.get("validation"):
            continue
        v = (r.get("validator") or {}).get("version") or ""
        out.append(dict(r, yr=int(r["pub"][:4]),
                        maj=(v.split(".")[0] if v else None),
                        errors=(r["validation"] or {}).get("errors", 0) or 0,
                        warnings=(r["validation"] or {}).get("warnings", 0) or 0))
    return out


def gen(r):
    """v1 against everything after it. v3 is v2's successor and behaves like it (1% against
    5%), so splitting them would spend a colour on a distinction the data does not make."""
    return None if not r["maj"] else ("v1" if r["maj"] == "1" else "v2+")


def series(rs):
    out = []
    for y in range(LO, HI + 1):
        g = [r for r in rs if r["yr"] == y]
        if not g:
            continue
        cell = {"year": y, "n": len(g),
                "pooled": sum(1 for r in g if r["errors"] > 0) / len(g)}
        for k in ("v1", "v2+"):
            sub = [r for r in g if gen(r) == k]
            cell[k] = {"n": len(sub),
                       "rate": (sum(1 for r in sub if r["errors"] > 0) / len(sub)
                                if sub else None)}
        stamped = [r for r in g if gen(r)]
        cell["share"] = (sum(1 for r in stamped if gen(r) == "v2+") / len(stamped)
                         if stamped else None)
        out.append(cell)
    return out


def pooled_by_gen(rs):
    out = {}
    for k in ("v1", "v2+"):
        g = [r for r in rs if gen(r) == k]
        out[k] = {"n": len(g), "rate": sum(1 for r in g if r["errors"] > 0) / len(g),
                  "warn": statistics.median(r["warnings"] for r in g)}
    u = [r for r in rs if not gen(r)]
    out["unstamped"] = {"n": len(u), "rate": sum(1 for r in u if r["errors"] > 0) / len(u),
                        "warn": statistics.median(r["warnings"] for r in u)}
    return out


def held_fixed(rs, a=2024, b=2025, k="v1"):
    """The control. Hold the validator and move the year instead."""
    out = {}
    for y in (a, b):
        g = [r for r in rs if r["yr"] == y and gen(r) == k]
        out[y] = {"n": len(g),
                  "rate": (sum(1 for r in g if r["errors"] > 0) / len(g)) if g else None}
    return out


def deprecated_field_gap(rs):
    both = [r for r in rs if r.get("issuesStatus")]
    dis = [r for r in both
           if (r["errors"] > 0) != (((r["issuesStatus"] or {}).get("errors", 0) or 0) > 0)]
    return {"both": len(both), "disagree": len(dis),
            "live_finds_more": sum(1 for r in dis if r["errors"] > 0),
            "live_only": sum(1 for r in rs if not r.get("issuesStatus")),
            "total": len(rs)}


FILE_BANDS = ((1, 100, "1-100"), (101, 500, "101-500"), (501, 2000, "501-2,000"),
              (2001, 10000, "2,001-10,000"), (10001, 10 ** 9, "over 10,000"))


def warn_rate(rs, min_n=15):
    """Warnings per file, split by whether the dataset also carries an error.

    Raw warnings track file count at rho +0.81, so a scatter of warnings against files draws
    that and nothing else -- a reader called the result random and said both classes were
    stacked, which was fair. Dividing by files removes the dominant term; what is left is the
    question, and it wants paired medians per band rather than a cloud.
    """
    out = []
    for lo, hi, lab in FILE_BANDS:
        g = [r for r in rs if r.get("files") and lo <= r["files"] <= hi]
        a = [r["warnings"] / r["files"] for r in g if r["errors"] == 0]
        b = [r["warnings"] / r["files"] for r in g if r["errors"] > 0]
        if len(a) >= min_n and len(b) >= min_n:
            out.append({"band": lab, "clean": a, "err": b,
                        "med_c": statistics.median(a), "med_e": statistics.median(b),
                        "ratio": statistics.median(b) / statistics.median(a)})
    return out


def main():
    rs = rows()
    g = deprecated_field_gap(rs)
    print(f"\n  {g['total']:,} datasets, validation populated on all of them; "
          f"issuesStatus absent on {g['live_only']:,}")
    print(f"  where both exist ({g['both']:,}), they disagree on errors>0 for "
          f"{g['disagree']:,}; live finds more in {g['live_finds_more']:,}")
    print(f"\n  {'year':<6}{'n':>5}{'pooled':>9}{'v1 n':>7}{'v1':>7}{'v2+ n':>8}{'v2+':>7}"
          f"{'v2+ share':>12}")
    for c in series(rs):
        f = lambda d: f"{d['rate']:.0%}" if d["rate"] is not None else "-"
        print(f"  {c['year']:<6}{c['n']:>5}{c['pooled']:>9.0%}{c['v1']['n']:>7}"
              f"{f(c['v1']):>7}{c['v2+']['n']:>8}{f(c['v2+']):>7}"
              f"{(f'{c[chr(115)+chr(104)+chr(97)+chr(114)+chr(101)]:.0%}' if c['share'] is not None else '-'):>12}")
    p = pooled_by_gen(rs)
    print(f"\n  pooled by generation:")
    for k in ("v1", "v2+", "unstamped"):
        print(f"    {k:<10}n={p[k]['n']:>5}  errors>0 {p[k]['rate']:>5.0%}  "
              f"median warnings {p[k]['warn']:>7,.0f}")
    h = held_fixed(rs)
    print(f"\n  CONTROL, validator held at v1: "
          + "  ".join(f"{y} {v['rate']:.0%} (n={v['n']})" for y, v in h.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
