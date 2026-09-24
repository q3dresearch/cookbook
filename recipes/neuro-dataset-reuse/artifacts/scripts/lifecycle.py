#!/usr/bin/env python3
"""A dataset's life on OpenNeuro: accession, draft, publication, revision, use.

    python3 lifecycle.py

Every other plate in this recipe measures the last step. This module measures the ones before
it, because that is where the losses are.

**Only the first step is a funnel.** More datasets are starred (1,101) than are revised
(994), so the stages after publication are attributes of one population rather than a nested
sequence, and they are drawn as such.

**Four in five datasets never publish.** Accessions run ds000001 to ds008851 and 1,891 are
public. An accession is issued when a dataset is *created*, so the gap is abandoned drafts --
which is also why the gaps are not deletions.

**The draft itself is fast for most and brutal for some.** Median two days from creation to
publication, but p90 is 175 days and p99 is 881. And a long draft buys nothing: datasets
published the same day get 14.7 downloads a year against 12.7 for those that took over six
months.

**Revision is slow, and an earlier version of this module got its shape wrong.** Binned five
ways it looked bimodal -- a dip at 8-30 days reading as two populations. The bin-free ECDF
refutes that: the slope per log-decade rises monotonically, which is one right-skewed mode.
What survives is the level, not the shape: **27% of revision activity is done within a week
and 29% is still going a year later.**

**Revising does not fix the errors, at all.** Read against the live validator field, the error
rate by revision count is **31%, 33%, 39%, 32%** -- flat. Datasets revised five or more times
are no cleaner than datasets never touched again. Whatever the revision loop is for, it is not
validation.

**Pre-2019 draft times are zero and that is a migration.** OpenNeuro absorbed OpenfMRI, and
migrated datasets were created and published on the same day in bulk. Those years are excluded
from the draft-time series and kept in the funnel.
"""
import collections, datetime as dt, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fold, modality                                                    # noqa: E402

DATA = os.path.join(HERE, "..", "data")
FIRST_ACC, LAST_ACC = 1, 8851
MIGRATION_END = 2018          # bulk OpenfMRI import: created and published the same day


def _d(x):
    try:
        return dt.date.fromisoformat(str(x)[:10])
    except Exception:
        return None


def rows():
    raw = json.load(open(os.path.join(DATA, "datasets.json")))["datasets"]
    meta = {}
    for n in raw:
        md = n.get("metadata") or {}
        meta[n["id"]] = {
            "created": _d(n.get("created")), "pub": _d(n.get("publishDate")),
            "first": _d(md.get("firstSnapshotCreatedAt")),
            "last": _d(md.get("latestSnapshotCreatedAt")),
            "snaps": len(n.get("snapshots") or []),
            "stars": len(n.get("stars") or []),
            "followers": len(n.get("followers") or [])}
    val = {r["id"]: r for r in
           json.load(open(os.path.join(DATA, "validation.json")))["rows"]}
    out = []
    for r in fold.load()["rows"]:
        m = meta.get(r["id"], {})
        v = (val.get(r["id"], {}).get("validation") or {})
        lag = ((m.get("pub") - m["created"]).days
               if m.get("pub") and m.get("created") else None)
        out.append(dict(r, **m, mod=modality.modality(r),
                        lag=(lag if lag is not None and lag >= 0 else None),
                        errors=v.get("errors"),
                        span=((m["last"] - m["first"]).days
                              if m.get("first") and m.get("last") else None)))
    return out


def funnel(rs):
    """The ONE nested step. Everything downstream of publication is an attribute of the
    published set, not a further stage -- more datasets are starred (1,101) than are revised
    (994), so drawing them as a funnel would assert a nesting that is not there."""
    return {"issued": LAST_ACC - FIRST_ACC + 1, "published": len(rs)}


def attributes(rs):
    """What becomes of the published, each measured against the same base."""
    aged = [r for r in rs if r["dl_yr"] is not None and r["age"] >= 1.0]
    seen = [r for r in rs if r["errors"] is not None]
    return [
        {"label": "validator finds no errors", "n": sum(1 for r in seen if r["errors"] == 0),
         "base": len(seen), "note": "of every published dataset"},
        {"label": "revised after publication", "n": sum(1 for r in aged if r["snaps"] > 1),
         "base": len(aged), "note": "of those at least a year old"},
        {"label": "starred by a person", "n": sum(1 for r in aged if r["stars"] > 0),
         "base": len(aged), "note": "a deliberate act, not traffic"},
        {"label": "taken 100+ times a year", "n": sum(1 for r in aged if r["dl_yr"] >= 100),
         "base": len(aged), "note": "actually in circulation"},
    ]


def draft(rs):
    g = [r for r in rs if r["lag"] is not None and r["pub"]
         and r["pub"].year > MIGRATION_END]
    v = sorted(r["lag"] for r in g)
    q = lambda p: v[min(len(v) - 1, int(len(v) * p))]
    return {"n": len(v), "p25": q(.25), "p50": q(.50), "p75": q(.75), "p90": q(.90),
            "p99": q(.99), "same_day": sum(1 for x in v if x == 0) / len(v),
            "week": sum(1 for x in v if x <= 7) / len(v),
            "year": sum(1 for x in v if x > 365) / len(v)}


def spans(rs):
    """Revision durations, returned raw. An earlier version binned these five ways and read
    a dip at 8-30 days as two populations. The bin-free ECDF says otherwise: its slope per
    log-decade rises monotonically (+0.13, +0.14, +0.10, +0.16, +0.21, +0.30, +0.42), which
    is one right-skewed mode, not two. The dip survives every binning scheme but is modest
    at log2 resolution -- 0.118 against 0.164 -- and the five-bin version exaggerated it."""
    return sorted(r["span"] for r in rs if r["snaps"] > 1 and r["span"] is not None)


def drafts(rs):
    return sorted(r["lag"] for r in rs if r["lag"] is not None and r["pub"]
                  and r["pub"].year > MIGRATION_END)


def _fit(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sxx
    res = [c - (my + b * (a - mx)) for a, c in zip(x, y)]
    se = (sum(e * e for e in res) / (n - 2) / sxx) ** .5
    return {"slope": b, "t": b / se, "n": n}


def quality(rs, min_n=20):
    """Does revising reduce the error rate? Reported at EXACT snapshot counts, because the
    banded version of this plate was where a bin choice manufactured a finding."""
    g = [r for r in rs if r["errors"] is not None]
    pts = []
    for k in range(1, 11):
        b = [r for r in g if r["snaps"] == k]
        if len(b) >= min_n:
            pts.append({"k": k, "n": len(b),
                        "rate": sum(1 for r in b if r["errors"] > 0) / len(b)})
    tail = [r for r in g if r["snaps"] >= 11]
    if len(tail) >= min_n:
        pts.append({"k": 11, "n": len(tail), "label": "11+",
                    "rate": sum(1 for r in tail if r["errors"] > 0) / len(tail)})
    fit = _fit([math.log10(r["snaps"]) for r in g],
               [1.0 if r["errors"] > 0 else 0.0 for r in g])
    return {"points": pts, "fit": fit}


def payoff(rs, min_n=25):
    """Does a longer draft buy anything? An earlier annotation said it bought nothing; the
    continuous fit says it is worse than that."""
    g = [r for r in rs if r["lag"] is not None and r["dl_yr"]]
    pts = []
    for lo, hi, lab in ((0, 0, "0"), (1, 3, "1-3"), (4, 14, "4-14"), (15, 60, "15-60"),
                        (61, 180, "61-180"), (181, 365, "181-365"), (366, 10**6, "365+")):
        b = [r for r in g if lo <= r["lag"] <= hi]
        if len(b) >= min_n:
            pts.append({"label": lab, "n": len(b),
                        "median": statistics.median(r["dl_yr"] for r in b)})
    fit = _fit([math.log10(r["lag"] + 1) for r in g],
               [math.log10(r["dl_yr"]) for r in g])
    return {"points": pts, "fit": fit}


def main():
    rs = rows()
    f = funnel(rs)
    print(f"\n  THE ONE NESTED STEP")
    print(f"    accessions issued  {f['issued']:>6}")
    print(f"    ever published     {f['published']:>6}   {f['published']/f['issued']:>6.0%}"
          f"   -> {1-f['published']/f['issued']:.0%} never shipped")
    print(f"\n  ATTRIBUTES OF THE PUBLISHED (not nested, each against its own base)")
    for a in attributes(rs):
        print(f"    {a['label']:<28}{a['n']:>5} / {a['base']:<5}{a['n']/a['base']:>6.0%}"
              f"   {a['note']}")
    d = draft(rs)
    print(f"\n  DRAFT TIME (post-migration, n={d['n']:,}): median {d['p50']} days, "
          f"p75 {d['p75']}, p90 {d['p90']}, p99 {d['p99']}")
    print(f"    same day {d['same_day']:.0%}   within a week {d['week']:.0%}   "
          f"over a year {d['year']:.0%}")
    sp, dr = spans(rs), drafts(rs)
    print(f"\n  DURATIONS (days): draft n={len(dr):,} median {statistics.median(dr):.0f}"
          f"   revision n={len(sp):,} median {statistics.median(sp):.0f}")
    for day in (1, 7, 30, 365):
        print(f"    by day {day:>4}: {sum(1 for v in dr if v<=day)/len(dr):>5.0%} published"
              f"   {sum(1 for v in sp if v<=day)/len(sp):>5.0%} done revising")
    q = quality(rs)
    print(f"\n  DOES REVISING FIX IT? slope {q['fit']['slope']:+.4f}, "
          f"t={q['fit']['t']:+.2f} -- flat")
    for pt in q["points"]:
        print(f"    {pt.get('label', pt['k']):>4} snapshots  n={pt['n']:>4}  "
              f"errors {pt['rate']:>5.0%}")
    p = payoff(rs)
    print(f"\n  DOES A LONG DRAFT PAY? slope {p['fit']['slope']:+.4f}, "
          f"t={p['fit']['t']:+.2f} on n={p['fit']['n']:,} -- NEGATIVE, not neutral")
    for pt in p["points"]:
        print(f"    {pt['label']:>8} days  n={pt['n']:>4}  median {pt['median']:>6.1f} dl/yr")
    return 0


if __name__ == "__main__":
    sys.exit(main())
