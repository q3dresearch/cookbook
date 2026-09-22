#!/usr/bin/env python3
"""Run this recipe's claims against the condensed file alone, with no source zip present.

    python3 verify-cached.py [2016]

`verify.py` is the authoritative check: it re-folds the 300 MB source and is what settles a
disagreement. This one exists for the reader who has neither the zip nor an hour to wait for
USAspending to generate it. It answers the same questions from `condensed-fy<Y>.json`, which
is ~22 KB, and it runs in under a second.

**It is also the test that the condensed layer is allowed to exist.** If a claim in the
recipe cannot be re-derived here, then the condensed file is not a summary of the source, it
is a lossy selection of it -- and the figure making that claim would silently depend on data
nobody keeps. Every claim below reproducing is what licenses deleting the zips.

The provenance block is printed rather than checked, because nothing here can verify it: a
cache can state which file it came from, and only the file itself can confirm it. That is
`verify.py`'s job, and it is why both scripts exist.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
FAILED = []


def chk(label, claimed, actual, tol=0.0):
    ok = abs(claimed - actual) <= tol if tol else claimed == actual
    print(f"  {'ok  ' if ok else 'FAIL'}  {label:<48} claim {claimed!s:>11}  "
          f"cache {actual!s:>11}")
    if not ok:
        FAILED.append(label)


def main():
    fy = (sys.argv[1] if len(sys.argv) > 1 else "2016")
    p = os.path.join(DATA, f"condensed-fy{fy}.json")
    if not os.path.exists(p):
        raise SystemExit(f"  condensed-fy{fy}.json missing - run condense.py {fy}")
    d = json.load(open(p))
    pv, f = d["provenance"], d["file"]
    sz, co, ge, of = d["size"], d["concentration"], d["geography"], d["offers"]
    print(f"\n  condensed-fy{fy}.json, {os.path.getsize(p)/1024:,.0f} KB")
    print(f"  built {pv['condensed_at']} from {pv['source']} "
          f"({pv['bytes']/1e6:,.0f} MB, sha256 {pv['sha256'][:16]}...)")
    print(f"  value rule: {pv['value_rule']}")
    print(f"  bid rule  : {pv['bid_rule']}\n")

    chk("transactions", 746960, f["transactions"])
    chk("awards", 554171, f["awards"])
    chk("net obligations $bn", 125.75, round(f["net"] / 1e9, 2), 0.01)
    chk("negative transactions %", 13.17,
        round(100 * f["negative_tx"] / f["transactions"], 2), 0.02)
    chk("modifications %", 46.1,
        round(100 * f["modification_tx"] / f["transactions"], 1), 0.2)
    chk("positive-only overstates the net %", 4.8,
        round(100 * (f["gross_positive"] - f["net"]) / f["net"], 1), 0.2)

    sbn = sz["classes"]["SMALL BUSINESS"]
    chk("small business, share of awards %", 52.4,
        round(100 * sbn[0] / f["awards"], 1), 0.05)
    chk("small business, share of dollars %", 26.1, round(100 * sbn[1] / f["net"], 1), 0.05)
    chk("median small-business award $", 8555, round(sz["median_small"]))
    chk("median other-than-small award $", 7314, round(sz["median_other"]), 1)
    chk("awards above $316m", 35, sz["above_316m"]["n"])
    chk("  of those, small business", 0, sz["above_316m"]["n_small"])
    chk("  their share of all money %", 23.7,
        round(100 * sz["above_316m"]["dollars"] / f["net"], 1), 0.05)

    half = lambda c: next(r for r, s in c if s >= 0.5)
    chk("recipients holding half the dollars", 74, half(co["dollar_curve"]), 2)
    chk("recipients holding half the awards", 994, half(co["award_curve"]), 12)

    chk("awards carrying both state codes", 547968, ge["both_codes"])
    chk("performed outside the recipient's state %", 40.8,
        round(100 * ge["cross_state"] / ge["both_codes"], 1), 0.05)
    chk("capital region by recipient %", 19.41,
        round(100 * ge["capital_rec"] / ge["with_rec"], 2), 0.05)
    chk("capital region by performance %", 20.27,
        round(100 * ge["capital_pop"] / ge["with_pop"], 2), 0.05)

    chk("awards with a usable bid count", 550977, of["usable"])
    chk("awards recording exactly zero offers", 1876, of["zero_offer_awards"], 4)
    chk("labelled competed yet drew one bid", 180868, of["competed_single"], 20)
    fo = of["full_open"]
    chk("FULL AND OPEN awards", 206656, fo["n"], 20)
    chk("  orders on a competed vehicle %", 74.7, round(100 * fo["vehicle"] / fo["n"], 1),
        0.05)
    chk("  carrying an only-one-source reason %", 16.8,
        round(100 * fo["only_one_source"] / fo["n"], 1), 0.05)
    chk("    of those, single-bid %", 97.8,
        round(100 * fo["only_one_source_single"] / fo["only_one_source"], 1), 0.05)
    sn, ss = of["sealed_competed"]
    chk("sealed or two-step, single-bid %", 6.5, round(100 * ss / sn, 1), 0.05)
    vt = of["by_procedure_competed"]["SUBJECT TO MULTIPLE AWARD FAIR OPPORTUNITY"]
    chk("vehicle orders, single-bid %", 59.9, round(100 * vt[1] / vt[0], 1), 0.05)

    chk("awards with a money ceiling recorded %", 29.7,
        round(100 * d["ceiling"]["with_ceiling"] / f["awards"], 1), 0.05)

    print()
    if FAILED:
        print(f"  {len(FAILED)} claim(s) the condensed file cannot answer: "
              + "; ".join(FAILED))
        print("  the condensed layer is lossy for these — do not delete the source")
        return 1
    print("  every claim reproduces from the condensed file")
    print("  (run verify.py against the source zip to confirm the cache is not stale)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
