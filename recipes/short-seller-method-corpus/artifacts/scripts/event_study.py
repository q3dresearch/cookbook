#!/usr/bin/env python3
"""What the target's stock did, 30 trading days either side of the report.

    python event_study.py

Day 0 is the first trading day on or after the report's publication date. Returns
are cumulative from day -30, so the line shows the whole window relative to where
the stock stood a month before anyone had read the thing.

Three cautions are built into the output rather than left to a footnote.

**Trading days, not calendar days.** A calendar window silently varies in length
with weekends and holidays, and short reports cluster on Tuesdays and Wednesdays.

**The report date is not the trade date.** A report published after the close moves
the next session, so day 0 to day +1 is one event, not two. The split is reported.

**Survivors only.** A target that went bankrupt is not in the price source under
the symbol its report named, so the series most likely to show a large fall is the
series most likely to be missing. The count of missing targets is printed beside
every result, because a median drawn from survivors is not a median of the practice.
"""
import json, statistics, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw"
PRICES = RAW / "prices"
WINDOW = 30
BENCH = "IWM"   # Russell 2000. Short targets are small caps far more often than not,
                # and benchmarking a micro-cap against the S&P overstates its abnormal
                # move in any month the large-cap index diverges from small caps.


def series(sym):
    f = PRICES / f"{sym}.json"
    if not f.exists():
        return None
    rows = json.loads(f.read_text())
    # 'a' is the split/dividend-adjusted close; 'c' is raw. Adjusted is correct for
    # a return series — a 10-for-1 split would otherwise read as a 90% fall.
    out = sorted(((r["t"], r.get("a", r["c"])) for r in rows if r.get("a") or r.get("c")))
    return out


def bench_series():
    s = series(BENCH)
    return dict(s) if s else {}


def window(sym, date):
    s = series(sym)
    if not s:
        return None, "no price series"
    dates = [d for d, _ in s]
    idx = next((i for i, d in enumerate(dates) if d >= date), None)
    if idx is None:
        return None, "report is after the last price"
    if idx < WINDOW:
        return None, "listing starts inside the pre-window"
    if idx + WINDOW >= len(s):
        return None, "delisted or halted inside the post-window"
    base = s[idx - WINDOW][1]
    if not base:
        return None, "zero base price"
    # Keep the PRICES, not just returns against a fixed base. Differencing two
    # cumulative returns is not the return over the span between them: it produced
    # a "-104%" one-day move for POET, which is impossible for a long position and
    # was really a large rise followed by a large fall, measured in the wrong space.
    prices = [s[idx - WINDOW + k][1] for k in range(2 * WINDOW + 1)]
    wdates = [s[idx - WINDOW + k][0] for k in range(2 * WINDOW + 1)]
    # Indexed to the report EVE, not to day -30. A -30 baseline folds a month of
    # pre-existing drift into the headline: the same 85 events read -10.2% at day
    # +30 against a -30 base and -7.5% against the eve, and only the second is a
    # statement about the report.
    eve = prices[WINDOW - 1]
    bench = BENCH_PRICES
    bpr = [bench.get(d) for d in wdates]
    beve = bpr[WINDOW - 1]
    abn = None
    if beve and all(b for b in bpr):
        abn = [(p / eve) / (b / beve) - 1 for p, b in zip(prices, bpr)]
    return {"days": list(range(-WINDOW, WINDOW + 1)),
            "dates": wdates,
            "prices": prices,
            "cum": [p / base - 1 for p in prices],
            "rel": [p / eve - 1 for p in prices],
            "abn": abn}, ""


BENCH_PRICES = {}


def main():
    global BENCH_PRICES
    BENCH_PRICES = bench_series()
    print(f"  benchmark {BENCH}: {len(BENCH_PRICES)} trading days")
    cands = json.loads((RAW / "join_candidates.json").read_text())
    cov = json.loads((PRICES / "coverage.json").read_text()) if (PRICES / "coverage.json").exists() else {}
    kept, dropped = [], defaultdict(list)
    for c in cands:
        w, why = window(c["ticker"], c["date"])
        if w:
            kept.append({**c, **w})
        else:
            dropped[why].append(c["ticker"])

    print(f"  {len(cands)} report-ticker pairs -> {len(kept)} with a usable ±{WINDOW}-day window")
    for why, syms in sorted(dropped.items(), key=lambda kv: -len(kv[1])):
        print(f"    dropped {len(syms):>3}: {why}  ({', '.join(sorted(set(syms))[:6])})")
    if cov:
        from collections import Counter
        print("  price-source coverage: " + ", ".join(
            f"{v} {k}" for k, v in Counter(x["outcome"] for x in cov.values()).most_common()))
    if not kept:
        print("  nothing to summarise.")
        return kept

    def at(day):
        return [k["cum"][day + WINDOW] for k in kept]

    def ret(k, a, b):
        """Actual return from day a to day b, from prices."""
        pa, pb = k["prices"][a + WINDOW], k["prices"][b + WINDOW]
        return (pb / pa - 1) if pa else float("nan")
    print(f"\n  cumulative return from day -{WINDOW}, median across {len(kept)} events")
    for d in (-30, -10, -1, 0, 1, 5, 10, 20, 30):
        v = sorted(at(d))
        med = statistics.median(v)
        print(f"    day {d:>+4}   median {med:>+7.1%}   quartiles {v[len(v)//4]:>+7.1%} .. {v[3*len(v)//4]:>+7.1%}")
    # The event itself, isolated from the drift before it.
    # The three spans must not overlap. "Before" ran -30 to 0 and day 0 IS the
    # report day, so the reaction was being counted as drift that preceded it —
    # which reversed the reading of the whole study.
    before = [ret(k, -30, -1) for k in kept]
    move = [ret(k, -1, 1) for k in kept]
    after = [ret(k, 1, 30) for k in kept]
    print(f"\n  day -30 to -1 (before, drift):     median {statistics.median(before):>+7.1%}")
    print(f"  day  -1 to +1 (the report itself): median {statistics.median(move):>+7.1%}")
    print(f"  day  +1 to +30 (after):            median {statistics.median(after):>+7.1%}")
    neg = sum(1 for m in move if m < 0)
    print(f"  {neg}/{len(move)} fell on the report ({neg/len(move):.0%})")
    (RAW / "event_windows.json").write_text(json.dumps(kept, indent=1))
    return kept


if __name__ == "__main__":
    main()
