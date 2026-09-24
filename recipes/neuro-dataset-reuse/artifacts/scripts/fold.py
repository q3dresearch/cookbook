#!/usr/bin/env python3
"""OpenNeuro datasets reduced to what is observable at publication, plus what happened after.

    python3 fold.py

**The outcome is `analytics.downloads`, and it is cumulative.** It never resets, so it is a
stock and not a rate: a dataset published in 2018 has had eight years to collect them and one
published last month has had weeks. Ranking on the raw count measures the calendar. Every
rate here is **downloads per year since publication**, and the raw stock is kept beside it so
the difference can be shown rather than asserted.

**What counts as observable at publication.** Only things a depositor controls or knows on the
day they publish: the modality, how many subjects and sessions, how many files and how large,
how many tasks, whether a paper DOI is attached, whether the BIDS validator complains, the
species, the study domain and whether a clinical diagnosis is recorded. Downloads, views,
stars and followers are outcomes and never predictors.

**Views are not downloads and are kept apart.** A view is a page load, including from a search
engine; a download is somebody taking the data. They are reported separately and correlate
imperfectly, so pooling them would blur the only outcome that means reuse.

**The two consent fields are kept as three-valued.** `affirmedDefaced` and
`affirmedConsent` are carried through as True, False or None, because None means the depositor
answered neither way and collapsing it to False would invent non-compliance.

**Six datasets are missing and that is recorded, not rounded away.** The API reports 1,897 and
returns 1,891; six come back null through four retries. The population here is 1,891.
"""
import collections, datetime as dt, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
SRC = os.path.join(DATA, "datasets.json")
CACHE = os.path.join(DATA, "folded.json")
NOW = dt.date(2026, 9, 23)          # the retrieval date; ages are measured against it


def parse(ts):
    if not ts:
        return None
    try:
        return dt.date.fromisoformat(str(ts)[:10])
    except ValueError:
        return None


def build():
    raw = json.load(open(SRC))
    out = []
    for n in raw["datasets"]:
        ls = n.get("latestSnapshot") or {}
        sm = ls.get("summary") or {}
        md = n.get("metadata") or {}
        de = ls.get("description") or {}
        iss = ls.get("issuesStatus") or {}
        an = n.get("analytics") or {}
        pub = parse(n.get("publishDate")) or parse(n.get("created"))
        if not pub:
            continue
        age = (NOW - pub).days / 365.25
        subs = sm.get("subjects") or []
        sess = sm.get("sessions") or []
        tasks = sm.get("tasks") or []
        mods = sm.get("modalities") or md.get("modalities") or []
        auth = de.get("Authors") or []
        out.append({
            "id": n.get("id"), "pub": pub.isoformat(), "age": age,
            # outcomes
            "downloads": an.get("downloads") or 0, "views": an.get("views") or 0,
            "stars": len(n.get("stars") or []), "followers": len(n.get("followers") or []),
            # observable at publication
            "modality": (sm.get("primaryModality") or (mods[0] if mods else "") or "").lower(),
            "modalities": [str(m).lower() for m in mods],
            "n_mod": len(mods), "subjects": len(subs), "sessions": len(sess),
            "tasks": len(tasks), "files": sm.get("totalFiles") or 0,
            "size": ls.get("size") or 0, "processed": bool(sm.get("dataProcessed")),
            "authors": len(auth),
            "has_doi": bool(de.get("DatasetDOI")),
            "paper_doi": bool(md.get("associatedPaperDOI")),
            "species": (md.get("species") or "").strip().lower(),
            "domain": (md.get("studyDomain") or "").strip().lower(),
            "dx": (md.get("dxStatus") or "").strip().lower(),
            "longitudinal": (md.get("studyLongitudinal") or "").strip().lower(),
            "funder": bool(md.get("grantFunderName")),
            "errors": iss.get("errors"), "warnings": iss.get("warnings"),
            # the two consent assertions; None means the depositor answered neither way
            "defaced": md.get("affirmedDefaced"), "consent": md.get("affirmedConsent"),
            "versions": len(n.get("snapshots") or []),
        })
    for r in out:
        r["dl_yr"] = r["downloads"] / r["age"] if r["age"] > 0.08 else None
        r["vw_yr"] = r["views"] / r["age"] if r["age"] > 0.08 else None
    return {"retrieved": raw["retrieved"], "reported_count": raw.get("reported_count"),
            "null_nodes_skipped": raw.get("null_nodes_skipped"), "rows": out}


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    d = build()
    tmp = CACHE + ".tmp"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return d


def corr(pairs):
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
    n = len(pairs)
    if n < 8:
        return None, None, n
    xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]

    def pe(a, b):
        ma, mb = sum(a) / n, sum(b) / n
        sa = sum((x - ma) ** 2 for x in a) ** .5
        sb = sum((y - mb) ** 2 for y in b) ** .5
        return (sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb)
                if sa and sb else None)

    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for p, i in enumerate(o):
            r[i] = float(p)
        return r
    return pe(xs, ys), pe(rk(xs), rk(ys)), n


def main():
    d = load()
    rows = d["rows"]
    live = [r for r in rows if r["dl_yr"] is not None]
    print(f"\n  {len(rows):,} datasets with a publication date "
          f"(API reported {d['reported_count']:,}, {d['null_nodes_skipped']} came back null)")
    print(f"  {len(live):,} published more than a month ago, so a rate is defined")
    print(f"  published {min(r['pub'] for r in rows)} to {max(r['pub'] for r in rows)}")

    print(f"\n  THE TRAP, measured before anything is built on it")
    for k, lab in (("downloads", "raw downloads"), ("dl_yr", "downloads per year")):
        p, s, n = corr([(r["age"], r[k]) for r in live])
        print(f"    age against {lab:<20} r {p:+.2f}  rho {s:+.2f}  (n={n:,})")

    dl = sorted(r["dl_yr"] for r in live)
    print(f"\n  downloads per year: median {statistics.median(dl):,.1f}  "
          f"p10 {dl[len(dl)//10]:,.1f}  p90 {dl[-len(dl)//10]:,.1f}  max {dl[-1]:,.0f}")
    zero = sum(1 for r in live if r["downloads"] == 0)
    print(f"  never downloaded at all: {zero:,} of {len(live):,} ({zero/len(live):.1%})")

    print(f"\n  BY MODALITY")
    by = collections.defaultdict(list)
    for r in live:
        by[r["modality"] or "(none)"].append(r)
    print(f"    {'modality':<14}{'n':>6}{'median dl/yr':>14}{'median subjects':>17}"
          f"{'median GB':>11}")
    for k, g in sorted(by.items(), key=lambda t: -len(t[1]))[:10]:
        print(f"    {k:<14}{len(g):>6}{statistics.median(x['dl_yr'] for x in g):>14,.1f}"
              f"{statistics.median(x['subjects'] for x in g):>17,.0f}"
              f"{statistics.median(x['size'] for x in g)/1e9:>11,.1f}")

    print(f"\n  WHAT PREDICTS DOWNLOADS PER YEAR")
    print(f"    {'predictor':<38}{'n':>6}{'Pearson':>10}{'Spearman':>10}")
    for key, lab, lg in (("subjects", "number of subjects (log)", True),
                         ("sessions", "number of sessions (log)", True),
                         ("tasks", "number of tasks (log)", True),
                         ("files", "number of files (log)", True),
                         ("size", "size in bytes (log)", True),
                         ("authors", "number of authors", False),
                         ("versions", "number of published versions", False),
                         ("n_mod", "number of modalities", False),
                         ("warnings", "BIDS validator warnings", False),
                         ("errors", "BIDS validator errors", False),
                         ("age", "age in years", False)):
        def v(r):
            x = r.get(key)
            if x is None:
                return None
            return math.log10(x) if lg and x > 0 else (None if lg else x)
        p, s, n = corr([(v(r), r["dl_yr"]) for r in live])
        f = lambda z: f"{z:+.2f}" if z is not None else "  .  "
        print(f"    {lab:<38}{n:>6}{f(p):>10}{f(s):>10}")
    for key, lab in (("paper_doi", "has an associated paper DOI"),
                     ("has_doi", "has a dataset DOI"),
                     ("funder", "names a grant funder"),
                     ("processed", "contains derivatives")):
        a = [r["dl_yr"] for r in live if r[key]]
        b = [r["dl_yr"] for r in live if not r[key]]
        if len(a) < 8 or len(b) < 8:
            continue
        print(f"    {lab:<38}{len(a):>6} yes median {statistics.median(a):>7,.1f}   "
              f"{len(b):>5} no median {statistics.median(b):>7,.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
