#!/usr/bin/env python3
"""Did the thesis hold up -- against the company's own filings, not its stock price.

    python jackpot.py

Two questions the price-based outcome measures in this recipe cannot answer.

**Does a broken-economics claim survive contact with XBRL?** When a firm says the
unit economics do not work, the last annual figures the company filed BEFORE the
report either show it or they do not. This is the one allegation type a careful
outsider can check without a single source, which makes it the natural place to
start for anyone reproducing this work.

**Does an accusation of crime get conceded later?** A Wells notice, a grand jury, a
subpoena or a formal order of investigation disclosed in the company's own filings
after the report is the company admitting, under obligation, what the report alleged.

The comparison that makes either number mean anything is the 140 untargeted control
filers: "41% of targets burn cash" is a statistic about growth-stage companies until
you know the control rate.

Read the enforcement column carefully. A subpoena is not a conviction, and this
counts the company's disclosure of an investigation, not its outcome. And a report
can *cause* the disclosure it appears to predict -- regulators read these too. That
confound is real, is not resolved here, and the direction it pushes is toward
overstating the firms' hit rate.
"""
import json, sys, math, statistics, collections
from datetime import date
from pathlib import Path

TODAY = date.today().isoformat()

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw"
sys.path.insert(0, str(HERE))
from selection import wilson, fisher


# A margin needs a denominator worth dividing by. Riot Blockchain's last annual before
# Hindenburg's report showed revenue of $9,416 -- it was Bioptix, a tiny biotech that
# had just renamed itself -- against a $6.3m operating loss, giving an operating margin
# of -669x. That figure is arithmetically correct and analytically meaningless: below
# roughly $1m of revenue a company is not a business whose margin says anything, it is
# a shell with a story. Such companies are counted as NOMINAL REVENUE, which is itself
# a finding about the target, rather than as a ratio that would dominate every average.
REVENUE_FLOOR = 1_000_000


def meaningful(e):
    return e.get("status") == "ok" and (e.get("revenue") or 0) >= REVENUE_FLOOR


def econ(rows, key):
    return [v["economics"][key] for v in rows
            if meaningful(v["economics"]) and v["economics"].get(key) is not None]


# Time at risk has to be equalised before any "later disclosed" rate is comparable.
# A target attacked in 2014 has twelve years in which to disclose an investigation; one
# attacked in 2025 has months. Worse, it is not random which is which -- the targets
# whose economics were visibly broken have a median report year of 2022 against 2020
# for the rest, so they have TWO YEARS LESS exposure, which on its own would produce
# the lower enforcement rate this recipe reports. A fixed window removes that. Three
# years is the choice: long enough that most disclosures land inside it, short enough
# that reports through 2023 still have a full window.
WINDOW_YEARS = 3


def resplit(v, cutoff):
    """Re-split a company's enforcement hits at any date.

    Capture stores them already split at the report date, but both lists together are
    the complete hit list -- EDGAR full-text search returns every match, not a top-N
    page (checked: 30 of 30 for a company with 30). So a control captured against the
    corpus median date can be re-scored against a date drawn from the target
    distribution, which is what makes the two groups comparable.
    """
    hits = v["enforcement"]["before"] + v["enforcement"]["after"]
    return [h for h in hits if h["date"] > cutoff]


def enforced_at(v, cutoff, years=WINDOW_YEARS):
    y, m, d = (int(x) for x in cutoff.split("-"))
    end = f"{y + years:04d}-{m:02d}-{d:02d}"
    if end > TODAY:
        return None
    return any(h["date"] <= end for h in resplit(v, cutoff))


def enforced(v, years=WINDOW_YEARS):
    """Did an investigation get disclosed within `years` of the report? None if the
    window has not closed yet, so an unexpired company is excluded rather than
    silently counted as a no."""
    y, m, d = (int(x) for x in v["as_of"].split("-"))
    end = f"{y + years:04d}-{m:02d}-{d:02d}"
    if end > TODAY:
        return None
    return any(h["date"] <= end for h in v["enforcement"]["after"])


def broken(e):
    """Does the last annual before the report show a business that does not work?

    Returns None when it cannot be judged. Operating margin is preferred over cash
    burn because it is the cleaner statement about the business rather than about its
    financing, but either alone is enough to answer the question.
    """
    if not meaningful(e):
        return None
    om, burn = e.get("operating_margin"), e.get("cash_burn_ratio")
    if om is None and burn is None:
        return None
    return (om is not None and om < 0) or (burn is not None and burn < 0)


def pct(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {k/n:>4.0%}  [{lo:.0%}-{hi:.0%}]" if n else "no data"


def main():
    T = json.loads((RAW / "jackpot_targets.json").read_text())
    Cp = RAW / "jackpot_controls.json"
    C = json.loads(Cp.read_text()) if Cp.exists() else {}
    tv, cv = list(T.values()), list(C.values())
    print(f"  {len(tv)} targets, {len(cv)} controls\n")

    print("  --- do the numbers show a broken business, before the report? ---\n")
    print(f"  {'measure':<34}{'targets':<26}{'controls':<26}{'p':>8}")
    for label, key, bad in [
        ("negative gross margin", "gross_margin", lambda x: x < 0),
        ("negative operating margin", "operating_margin", lambda x: x < 0),
        ("operating cash flow negative", "cash_burn_ratio", lambda x: x < 0),
        ("burns > 50c per $1 revenue", "cash_burn_ratio", lambda x: x < -0.5),
    ]:
        t, c = econ(tv, key), econ(cv, key)
        a, cc = sum(map(bad, t)), sum(map(bad, c))
        p = fisher(a, len(t) - a, cc, len(c) - cc) if c else float("nan")
        print(f"  {label:<34}{pct(a, len(t)):<26}{pct(cc, len(c)):<26}{p:>8.4f}")

    for label, key in [("gross margin", "gross_margin"),
                       ("operating margin", "operating_margin")]:
        t, c = econ(tv, key), econ(cv, key)
        mt = f"{statistics.median(t):+.0%}" if t else "-"
        mc = f"{statistics.median(c):+.0%}" if c else "-"
        print(f"  median {label:<27}{mt:<26}{mc:<26}")

    print(f"\n  status breakdown (targets):",
          dict(collections.Counter(v["economics"].get("status") for v in tv)))

    print("\n  --- did the company concede an investigation? ---\n")
    # Controls were captured against one cutoff, so give each a report date drawn from
    # the target distribution and re-score. Without this the two groups differ in how
    # long they had to disclose anything, which decides the answer on its own.
    import random
    dates = sorted(v["as_of"] for v in tv)
    rnd = random.Random(20260912)
    cpaired = [(v, rnd.choice(dates)) for v in cv]

    te = [enforced(v) for v in tv]
    ce = [enforced_at(v, d) for v, d in cpaired]
    tk = [x for x in te if x is not None]
    ck = [x for x in ce if x is not None]
    a, c = sum(tk), sum(ck)
    p = fisher(a, len(tk) - a, c, len(ck) - c) if ck else float("nan")
    print(f"  {f'disclosed within {WINDOW_YEARS}y of the report':<34}"
          f"{pct(a, len(tk)):<26}{pct(c, len(ck)):<26}{p:>8.4f}")
    tb = sum(1 for v in tv if v["enforcement"]["before"])
    cb = sum(1 for v, d in cpaired if [h for h in
             v["enforcement"]["before"] + v["enforcement"]["after"] if h["date"] <= d])
    print(f"  {'(already disclosed beforehand)':<34}{pct(tb, len(tv)):<26}{pct(cb, len(cv)):<26}")
    print(f"  windows still open, excluded: {len(te) - len(tk)} targets, {len(ce) - len(ck)} controls")

    # Does the DECLARED thesis line up with what the filings later showed?
    # tickers.json is {firm: {slug: TICKER}}; invert it, keeping only slugs that are
    # first-look reports (thesis.json holds exactly those). Two slugs can share a
    # ticker -- "temenos" and "temenos-response" -- and only the first look is a thesis.
    th = {r["slug"]: r for r in json.loads((RAW / "thesis.json").read_text())}
    tk = json.loads((RAW / "tickers.json").read_text())
    by_sym = {}
    for firm_map in tk.values():
        for slug, sym in firm_map.items():
            if slug in th:
                by_sym.setdefault(sym, th[slug])
    joined = [(by_sym[sym], v) for sym, v in T.items() if sym in by_sym]
    print(f"\n  --- thesis against filings ({len(joined)} reports joined to a ticker) ---\n")
    if joined:
        for lab, sel in [("alleged a crime", lambda r: r["crime"]),
                         ("alleged accounting manipulation", lambda r: r["accounting"]),
                         ("alleged broken economics", lambda r: r["broken"])]:
            g = [v for r, v in joined if sel(r)]
            ng = [v for r, v in joined if not sel(r)]
            e = sum(1 for v in g if v["enforcement"]["after"])
            ne = sum(1 for v in ng if v["enforcement"]["after"])
            b = sum(1 for v in g if (v["economics"].get("cash_burn_ratio") or 0) < 0)
            print(f"  {lab:<38}n={len(g):<4} later enforcement {pct(e, len(g))}")
            print(f"  {'  reports that did NOT':<34}n={len(ng):<4} later enforcement {pct(ne, len(ng))}")
            print(f"  {'  of the alleging group, burning cash':<34}{pct(b, len(g))}\n")

    json.dump({"targets": len(tv), "controls": len(cv)},
              open(RAW / "jackpot_summary.json", "w"), indent=1)


if __name__ == "__main__":
    main()
