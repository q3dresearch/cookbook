#!/usr/bin/env python3
"""Whether a dataset's cost per download can be forecast at the moment it is deposited.

    python3 roi.py

**Cost per download is two thirds a reuse metric.** In log units the spread decomposes
exactly: `log(award/downloads) = log(award) - log(downloads)`, and because the two are
uncorrelated the variances add. The award contributes **31%** and the download count **69%**.
A dataset does not look expensive per download because it was expensive; it looks expensive
because nobody took it.

**Money does not buy reuse.** Across 86 datasets joined to a single-project NIH award,
`corr(log award, log downloads per year) = -0.12`, t = -1.10. Not distinguishable from zero,
and pointing the wrong way if it were.

**Scale barely buys reuse either.** On the whole archive, `log(downloads/yr) ~ log(subjects)`
has a slope of **+0.22**: ten times the subjects returns **1.66x** the downloads, so doubling
a cohort returns about **16%**. Sample size is not a reuse strategy.

**The only lever that moves is what the data is.** Holding subject count fixed, every modality
beats MRI: PET 2.49x, EEG 2.22x, fNIRS 1.80x, iEEG 1.69x, MEG 1.57x. MRI is 66% of the archive
and the weakest per subject in it. But a lab does not pick a modality for reuse reasons -- it
picks the one the science needs -- so this is a description of a crowded market, not an
instruction.

**And none of it forecasts.** Every model here is scored out of sample by ten-fold
cross-validation, because in-sample R2 on 86 rows is a measure of how many columns you used.
On the funded subset "everything observable" reaches **0.189 in sample and -0.071 held out**.
On the full archive the honest ceiling is **0.104**.

**So 62% of the eventual cost per download is a coin flip at deposit.** 31% is the award, known
exactly. Of the remaining 69%, about a tenth is forecastable. That is the number that decides
the policy question: a funder cannot screen out the dataset that will cost a million dollars a
download, because at the moment of the decision it is indistinguishable from the one that will
cost three hundred.
"""
import collections, math, os, random, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import costjoin, fold, modality                                          # noqa: E402

MODS = ("ieeg", "eeg", "meg", "pet", "nirs")     # mri is the reference level
L = lambda v: math.log10(max(v, 1e-9))


def ols(X, y):
    p, N = len(X[0]), len(y)
    A = [[sum(X[i][a] * X[i][b] for i in range(N)) for b in range(p)]
         + [sum(X[i][a] * y[i] for i in range(N))] for a in range(p)]
    for c in range(p):
        pv = max(range(c, p), key=lambda r: abs(A[r][c]))
        if abs(A[pv][c]) < 1e-12:
            return None
        A[c], A[pv] = A[pv], A[c]
        for r in range(p):
            if r != c:
                f = A[r][c] / A[c][c]
                for k in range(c, p + 1):
                    A[r][k] -= f * A[c][k]
    return [A[i][p] / A[i][i] for i in range(p)]


def r2(X, y, b):
    yb = sum(y) / len(y)
    return 1 - (sum((y[i] - sum(b[j] * X[i][j] for j in range(len(b)))) ** 2
                    for i in range(len(y)))
                / sum((v - yb) ** 2 for v in y))


def kfold(X, y, k=10, seed=3):
    """Held-out R2. In-sample R2 on 86 rows counts columns, not signal, so nothing here is
    reported without this beside it."""
    idx = list(range(len(y)))
    random.Random(seed).shuffle(idx)
    pred = [None] * len(y)
    for f in range(k):
        te = set(idx[f::k])
        tr = [i for i in range(len(y)) if i not in te]
        # a rare modality can land wholly in the test split, leaving its dummy constant in
        # training; drop those columns for this fold rather than abandoning the whole score
        keep = [j for j in range(len(X[0]))
                if j == 0 or len({X[i][j] for i in tr}) > 1]
        b = ols([[X[i][j] for j in keep] for i in tr], [y[i] for i in tr])
        if b is None:
            return None
        for i in te:
            pred[i] = sum(b[c] * X[i][j] for c, j in enumerate(keep))
    yb = sum(y) / len(y)
    return 1 - (sum((y[i] - pred[i]) ** 2 for i in range(len(y)))
                / sum((v - yb) ** 2 for v in y))


def funded():
    return [r for r in costjoin.rows() if r["downloads"] > 0 and r["dl_yr"]]


def archive():
    out = [r for r in fold.load()["rows"] if r["dl_yr"] and r["age"] >= 1.0
           and r["subjects"] > 0]
    for r in out:
        r["mod"] = modality.modality(r)
    return out


def feats(r, use):
    f = [1.0]
    if "award" in use:
        f.append(L(r["award"]))
    if "subj" in use:
        f.append(L(max(r["subjects"], 1)))     # a 0-subject dataset must not become -9
    if "files" in use:
        f.append(L(max(r["files"], 1)))
    if "mod" in use:
        f += [1.0 if r["mod"] == m else 0.0 for m in MODS]
    if "doi" in use:
        f.append(1.0 if r["paper_doi"] else 0.0)
    if "era" in use:
        f.append(int(r["pub"][:4]) - 2020)
    return f


SETS_FUNDED = ((("award",), "the size of the grant"),
               (("mod",), "what kind of data it is"),
               (("subj", "files"), "how much data there is"),
               (("doi",), "whether a paper is attached"),
               (("award", "mod", "subj", "files", "doi", "era"), "everything observable"))
SETS_ALL = ((("mod",), "what kind of data it is"),
            (("subj", "files"), "how much data there is"),
            (("mod", "subj", "files", "doi", "era"), "everything observable"))


def prune(X):
    """Drop columns that are constant on this subset. On the funded rows several modality
    dummies are all-zero, which makes the normal equations singular and silently deletes the
    whole model from the table rather than reporting it."""
    keep = [j for j in range(len(X[0]))
            if j == 0 or len({row[j] for row in X}) > 1]
    return [[row[j] for j in keep] for row in X]


def score(rows, sets):
    y = [L(r["dl_yr"]) for r in rows]
    out = []
    for use, lab in sets:
        X = prune([feats(r, use) for r in rows])
        b = ols(X, y)
        if b is None:
            raise RuntimeError(f"model {lab!r} is singular even after pruning")
        out.append({"label": lab, "n": len(rows), "insample": r2(X, y, b),
                    "heldout": kfold(X, y)})
    return out


def decompose():
    """The exact split of the cost-per-download spread into price and popularity."""
    rs = [r for r in costjoin.rows() if r["downloads"] > 0]
    la = [L(r["award"]) for r in rs]
    ld = [L(r["downloads"]) for r in rs]
    va, vd = statistics.variance(la), statistics.variance(ld)
    n = len(rs)
    ma, md = sum(la) / n, sum(ld) / n
    sa = sum((x - ma) ** 2 for x in la) ** .5
    sd = sum((x - md) ** 2 for x in ld) ** .5
    r = sum((a - ma) * (d - md) for a, d in zip(la, ld)) / (sa * sd)
    return {"n": n, "award_share": va / (va + vd), "download_share": vd / (va + vd),
            "corr": r, "t": r * math.sqrt(n - 2) / math.sqrt(1 - r * r),
            "spread": 10 ** (2 * statistics.variance([a - d for a, d in zip(la, ld)]) ** .5)}


def scaling():
    rs = archive()
    y = [L(r["dl_yr"]) for r in rs]
    X = [feats(r, ("subj", "mod")) for r in rs]
    b = ols(X, y)
    base = statistics.median(x["dl_yr"] for x in rs if x["mod"] == "mri")
    bs = statistics.median(x["subjects"] for x in rs if x["mod"] == "mri")
    mods = []
    for m in ("mri",) + MODS:
        g = [r for r in rs if r["mod"] == m]
        if len(g) < 10:
            continue
        ms = statistics.median(x["subjects"] for x in g)
        mods.append({"mod": m, "n": len(g), "subjects": ms,
                     "observed": statistics.median(x["dl_yr"] for x in g),
                     "size_says": base * (ms / bs) ** b[1]})
    return {"n": len(rs), "slope": b[1], "per_10x": 10 ** b[1], "per_2x": 2 ** b[1],
            "r2": r2(X, y, b), "mods": sorted(mods, key=lambda m: -m["observed"])}


def main():
    d = decompose()
    print(f"\n  COST PER DOWNLOAD, n = {d['n']}, spread {d['spread']:,.0f}x across 2sd")
    print(f"    {d['award_share']:.0%} of the spread is what was spent")
    print(f"    {d['download_share']:.0%} is how often it was taken")
    print(f"    corr(log award, log downloads) = {d['corr']:+.3f}, t = {d['t']:+.2f}")
    sc = scaling()
    print(f"\n  SCALE, n = {sc['n']}: slope {sc['slope']:+.3f} -- 10x the subjects returns "
          f"{sc['per_10x']:.2f}x, doubling returns {sc['per_2x']:.2f}x")
    for m in sc["mods"]:
        print(f"    {modality.NICE.get(m['mod'], m['mod']):<7}n={m['n']:>4}  "
              f"observed {m['observed']:>5.1f}  size says {m['size_says']:>5.1f}  "
              f"{m['observed']/m['size_says']:>5.2f}x")
    print(f"\n  {'predictors':<32}{'n':>6}{'in-sample':>12}{'held out':>11}")
    for lab, rows, sets in (("FUNDED", funded(), SETS_FUNDED),
                            ("ARCHIVE", archive(), SETS_ALL)):
        print(f"  -- {lab}")
        for s in score(rows, sets):
            print(f"  {s['label']:<32}{s['n']:>6}{s['insample']:>12.3f}"
                  f"{s['heldout']:>11.3f}")
    ceiling = max(s["heldout"] for s in score(archive(), SETS_ALL))
    known = d["award_share"] + d["download_share"] * ceiling
    print(f"\n  KNOWABLE AT DEPOSIT: {known:.0%}    A COIN FLIP: {1-known:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
