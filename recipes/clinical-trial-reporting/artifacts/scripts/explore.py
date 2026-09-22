#!/usr/bin/env python3
"""First look at the walked table: what is populated, what the dates mean, what is answerable.

    python3 explore.py

Run before any figure. It answers the questions that decide whether the planned figures are
possible at all, and it prints the boundaries rather than assuming them:

- **How precise are the dates?** A 365-day statutory deadline tested against month-precision
  dates carries +/-15 days. This counts how many dates are month-only.
- **Which population is actually subject to the rule?** The register carries no "applicable
  clinical trial" flag - ACT status is a legal determination, not a field. Any compliance
  figure here is therefore about an *approximation* of the regulated population, and the
  approximation has to be stated and sized rather than waved at.
- **Does `hasResults` agree with a results date being present?** Two ways of asking the same
  thing; if they disagree, one of them is not what it says.
- **Is `UNKNOWN` a status or an age?** Cross-tabulated against registration year.
"""
import collections, csv, datetime, gzip, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = os.path.join(HERE, "..", "data", "studies.csv.gz")


def load():
    """Tolerant of a truncated tail.

    The walk appends each page as a new gzip member, which concatenates fine — but a run
    killed mid-write leaves the final member without its end-of-stream marker, and a plain
    read then raises EOFError and yields *nothing*. That would make the checkpoint useless:
    the point of resuming is that what was already fetched is still there. So a truncated
    tail is reported and the recovered rows are returned."""
    if not os.path.exists(ROWS):
        raise SystemExit("  run ctg2.py first")
    rows, truncated = [], False
    try:
        with gzip.open(ROWS, "rt", newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows.append(r)
    except EOFError:
        truncated = True
    if truncated:
        print(f"  NOTE: the file ends mid-member — {len(rows):,} rows recovered, the fetch "
              f"was interrupted. Re-run ctg2.py to resume before trusting any total.")
    return rows


def parse(d):
    """Returns (date, precision). Month-precision dates are placed mid-month, and the
    precision is returned so a figure can show the uncertainty rather than hide it."""
    if not d:
        return None, None
    try:
        if len(d) == 7:
            y, m = int(d[:4]), int(d[5:7])
            return datetime.date(y, m, 15), "month"
        if len(d) == 10:
            return datetime.date(int(d[:4]), int(d[5:7]), int(d[8:10])), "day"
    except ValueError:
        return None, None
    return None, None


def pct(n, d):
    return f"{n/d:.1%}" if d else "-"


def main():
    rows = load()
    n = len(rows)
    print(f"\n  {n:,} rows, {len(rows[0])} columns")

    print("\n== how complete is each column")
    for c in rows[0]:
        f = sum(1 for r in rows if r[c])
        print(f"  {c:<26}{f:>9,}  {pct(f, n):>7}")

    print("\n== date precision (a 365-day deadline against month dates carries +/-15 days)")
    for c in ("primary_completion", "completion", "results_submit", "first_post"):
        prec = collections.Counter(parse(r[c])[1] for r in rows if r[c])
        tot = sum(prec.values())
        print(f"  {c:<22}" + "  ".join(f"{k or 'unparsed'}={v:,} ({pct(v, tot)})"
                                       for k, v in prec.most_common()))

    print("\n== does hasResults agree with a results date being present?")
    both = sum(1 for r in rows if r["has_results"] == "true" and r["results_submit"])
    flag_only = sum(1 for r in rows if r["has_results"] == "true" and not r["results_submit"])
    date_only = sum(1 for r in rows if r["has_results"] != "true" and r["results_submit"])
    print(f"  flag and date    {both:>9,}")
    print(f"  flag, no date    {flag_only:>9,}   <- the flag means something else if large")
    print(f"  date, no flag    {date_only:>9,}")

    print("\n== primary completion date type (the statutory clock starts here)")
    t = collections.Counter(r["primary_completion_type"] or "(absent)" for r in rows)
    for k, v in t.most_common():
        print(f"  {k:<22}{v:>9,}  {pct(v, n):>7}")

    print("\n== is UNKNOWN a status or an age?  status by registration year")
    yrs = collections.defaultdict(collections.Counter)
    for r in rows:
        d, _ = parse(r["first_post"])
        if d:
            yrs[d.year][r["status"]] += 1
    print(f"  {'year':<6}{'studies':>9}{'UNKNOWN':>10}{'share':>8}{'COMPLETED':>11}{'share':>8}")
    for y in sorted(yrs):
        if y < 2005 or y > 2026:
            continue
        c = yrs[y]
        tot = sum(c.values())
        print(f"  {y:<6}{tot:>9,}{c['UNKNOWN']:>10,}{pct(c['UNKNOWN'], tot):>8}"
              f"{c['COMPLETED']:>11,}{pct(c['COMPLETED'], tot):>8}")

    print("\n== the reporting lag, where both dates exist and completion is ACTUAL")
    lags = []
    for r in rows:
        if r["primary_completion_type"] != "ACTUAL":
            continue
        pc, _ = parse(r["primary_completion"])
        rs, _ = parse(r["results_submit"])
        if pc and rs:
            lags.append((rs - pc).days)
    lags.sort()
    if lags:
        q = lambda p: lags[int(p * (len(lags) - 1))]
        print(f"  {len(lags):,} trials with both dates and an ACTUAL completion")
        print(f"  p10 {q(.10):>6}d   p25 {q(.25):>6}d   median {q(.50):>6}d   "
              f"p75 {q(.75):>6}d   p90 {q(.90):>6}d")
        late = sum(1 for x in lags if x > 365)
        neg = sum(1 for x in lags if x < 0)
        print(f"  past the 365-day deadline: {late:,} ({pct(late, len(lags))})")
        print(f"  submitted BEFORE primary completion: {neg:,} ({pct(neg, len(lags))})"
              f"   <- if large, the dates do not mean what they say")
    return 0


if __name__ == "__main__":
    sys.exit(main())
