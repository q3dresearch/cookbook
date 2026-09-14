#!/usr/bin/env python3
"""Window features and a diagonal-covariance GMM, for detecting instrument regimes.

The point of doing this rather than reading `ai_summary_model` is that the declared
version stamp is a claim, not a measurement. If a provider changes a prompt, a
temperature or a truncation limit without bumping the model string, a comparison keyed
on that string sees nothing. Clustering the *output* catches the change either way,
and then the declared label becomes something to validate against rather than trust.

**The declared extractor is deliberately excluded from the feature matrix.** Feeding it
in would make "do the detected regimes match the declared ones" circular.

**Selection rule, stated because BIC alone gives the wrong answer.** A GMM has no
temporal prior, so it is free to split one stable era into two heavily overlapping
components that then alternate window to window. BIC rewards that: on this data it
picks k=5, whose segmentation flickers 43 times across 146 windows with a median run
of 2. So k is chosen as **the largest k whose every regime run is at least 3 windows
long** -- a contiguity requirement, disclosed rather than tuned, that a real regime
should meet and a noise split will not.
"""
import collections, statistics
import numpy as np

FEATURES = ["keywords per paper", "keyword length (chars)", "multi-word share",
            "summary length (chars)", "distinct keywords / total"]

# Written by the authors, not by any model, so no extractor change can move them.
# They are the control for "is this the instrument or is it the corpus" and are
# deliberately NOT part of the feature matrix the GMM is fitted on.
CONTROLS = ["abstract length (chars)", "title length (chars)", "authors per paper"]


def windows(rows, days, min_papers=120):
    """rows: (date, declared, keywords, ai_summary, abstract, title, nauthors).

    Windows are fixed CALENDAR bins of `days`, not blocks of N consecutive papers.
    Paper blocks looked equivalent and were not: their edges depend on how papers
    sharing a date happen to be ordered, and changing that tie-break alone moved the
    segmentation from three clean regimes to six flickering ones. A calendar bin is
    invariant to it. Bins holding fewer than `min_papers` are dropped rather than
    merged, so a quiet stretch never borrows from a neighbour.

    Returns (X, C, meta): X the model-written features the GMM is fitted on, C the
    author-written controls it never sees, meta the (start, end, declared) per window.
    """
    import datetime as dt
    d0 = dt.date.fromisoformat(min(r[0] for r in rows))
    buckets = collections.defaultdict(list)
    for r in rows:
        buckets[(dt.date.fromisoformat(r[0]) - d0).days // days].append(r)
    wins = [buckets[b] for b in sorted(buckets) if len(buckets[b]) >= min_papers]
    X, C, meta = [], [], []
    for w in wins:
        ks = [k for r in w for k in r[2]]
        if not ks:
            continue
        X.append([statistics.mean(len(r[2]) for r in w),
                  statistics.mean(len(k) for k in ks),
                  sum(1 for k in ks if " " in k)/len(ks),
                  statistics.mean(len(r[3]) for r in w),
                  len({k.lower() for k in ks})/len(ks)])
        C.append([statistics.mean(r[4] for r in w),
                  statistics.mean(r[5] for r in w),
                  statistics.mean(r[6] for r in w)])
        meta.append((min(r[0] for r in w), max(r[0] for r in w),
                     collections.Counter(r[1] for r in w).most_common(1)[0][0]))
    return np.array(X), np.array(C), meta


def fit(Z, k, seed=0, iters=600):
    rng = np.random.default_rng(seed)
    n, d = Z.shape
    mu = Z[rng.choice(n, k, replace=False)].copy()
    var = np.ones((k, d)); w = np.full(k, 1/k); prev = -np.inf
    for _ in range(iters):
        lp = np.log(w)[None] - 0.5*(np.log(2*np.pi*var).sum(1)[None]
                                    + (((Z[:, None]-mu[None])**2)/var[None]).sum(2))
        m = lp.max(1, keepdims=True)
        ll = float((m + np.log(np.exp(lp-m).sum(1, keepdims=True))).sum())
        R = np.exp(lp-m); R /= R.sum(1, keepdims=True)
        Nk = R.sum(0) + 1e-9
        mu = (R.T @ Z)/Nk[:, None]
        var = np.maximum(np.einsum("nk,nkd->kd", R, (Z[:, None]-mu[None])**2)/Nk[:, None], 1e-3)
        w = Nk/n
        if abs(ll-prev) < 1e-8: break
        prev = ll
    bic = ll - 0.5*(k*2*d + k - 1)*np.log(n)
    return ll, bic, R.argmax(1)


def runs(lab):
    return [(v, len(list(g))) for v, g in __import__("itertools").groupby(lab)]


def select(Z, kmax=6, min_run=3, restarts=12):
    """Largest k whose every INTERIOR regime run is >= min_run windows.

    The first and last runs are exempt because they are censored by the ends of the
    archive, not by the data: the Inkling regime is two windows long simply because
    capture stops there. Applying the rule to them rejected segmentations at 28- and
    35-day bins that agreed exactly with the accepted one on both boundaries.

    Returns (k, labels, table) where table rows are
    (k, log-likelihood, BIC, blocks, shortest interior run, passed).
    """
    table, best = [], None
    for k in range(1, kmax+1):
        ll, bic, lab = max((fit(Z, k, s) for s in range(restarts)), key=lambda t: t[0])
        rs = runs(lab)
        interior = [n for _, n in rs[1:-1]] or [min(n for _, n in rs)]
        ok = min(interior) >= min_run
        table.append((k, ll, bic, len(rs), min(interior), ok))
        if ok: best = (k, lab)
    return best[0], best[1], table
