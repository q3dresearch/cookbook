#!/usr/bin/env python3
"""Turn the downloaded transaction zips into award-level records, with the traps handled.

    python3 load.py            # prints what is on disk and what survives each filter

Shared by every figure so the population is defined once. Four things this does that a naive
read would not, each of them a screen result rather than a precaution:

**Collapses transactions to awards.** 62% of rows are modifications; only 38% carry
`modification_number == '0'`. A row count is a count of paperwork. Awards are keyed on
`contract_award_unique_key`, which was checked against `award_id_piid` and agrees exactly --
11,414 distinct on 15,810 rows, with zero piids spanning two awards.

**Refuses `base_and_all_options_value` as a denominator.** It is a transaction-level field
equal to that action's own obligation on 69% of rows and `0.00` on modifications. Using it as
the award's base produced a growth ratio with a maximum of 4.8 billion. The comparable pair is
`current_total_value_of_award` against `potential_total_value_of_award`, which respects its own
ceiling: current exceeds potential on 0.0% of awards.

**Takes the maximum, not the last.** The award-level running total is not monotone -- it moves
backwards between consecutive modifications on 11% of multi-transaction awards. `last` is a
coin flip on those, so the maximum observed value is used and the non-monotone share is
counted and reported rather than smoothed away.

**Keeps negative obligations.** 12.4% of transactions carry one. They are de-obligations, they
are real, and dropping them overstates Commerce FY2024 by 6.9%.
"""
import collections, csv, glob, io, os, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
KEY = "contract_award_unique_key"


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def transactions(path):
    z = zipfile.ZipFile(path)
    for name in z.namelist():
        if not name.lower().endswith(".csv"):
            continue
        with z.open(name) as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8",
                                                     errors="replace")):
                yield r


def awards(paths):
    """One record per award. Values are the MAXIMUM seen, not the last -- see the docstring."""
    acc = {}
    nonmono = collections.Counter()
    for p in paths:
        for r in transactions(p):
            k = r.get(KEY) or r.get("award_id_piid")
            if not k:
                continue
            cur = num(r.get("current_total_value_of_award"))
            pot = num(r.get("potential_total_value_of_award"))
            fa = num(r.get("federal_action_obligation")) or 0.0
            a = acc.get(k)
            if a is None:
                a = acc[k] = {
                    "key": k, "piid": r.get("award_id_piid"),
                    "agency": r.get("awarding_agency_name"),
                    "sub_agency": r.get("awarding_sub_agency_name"),
                    "recipient": r.get("recipient_name"),
                    "uei": r.get("recipient_uei"),
                    "competed": r.get("extent_competed"),
                    "set_aside": r.get("type_of_set_aside"),
                    "pricing": r.get("type_of_contract_pricing"),
                    "naics": r.get("naics_code"), "psc": r.get("product_or_service_code"),
                    "award_type": r.get("award_type"),
                    "signed": (r.get("award_base_action_date") or "")[:10],
                    "cur": None, "pot": None, "obligated": 0.0,
                    "tx": 0, "mods": 0, "neg_tx": 0, "last_action": "",
                    "prev_cur": None, "back": 0,
                }
            a["tx"] += 1
            if (r.get("modification_number") or "") not in ("0", ""):
                a["mods"] += 1
            if fa < 0:
                a["neg_tx"] += 1
            a["obligated"] += fa
            d = (r.get("action_date") or "")[:10]
            if d > a["last_action"]:
                a["last_action"] = d
            if cur is not None:
                if a["prev_cur"] is not None and cur < a["prev_cur"] - 0.01:
                    a["back"] += 1
                a["prev_cur"] = cur
                a["cur"] = cur if a["cur"] is None else max(a["cur"], cur)
            if pot is not None:
                a["pot"] = pot if a["pot"] is None else max(a["pot"], pot)
    for a in acc.values():
        a.pop("prev_cur", None)
        nonmono["multi"] += a["tx"] > 1
        nonmono["went_backwards"] += a["back"] > 0 and a["tx"] > 1
    return list(acc.values()), dict(nonmono)


def files(pattern="*.zip"):
    return sorted(glob.glob(os.path.join(DATA, pattern)))


def main():
    fs = files()
    if not fs:
        raise SystemExit("  no zips in artifacts/data — run usa2.py or the all-agency request")
    print(f"  {len(fs)} file(s):")
    for f in fs:
        print(f"    {os.path.basename(f):<40}{os.path.getsize(f)/1e6:>8.1f} MB")
    aw, nm = awards(fs)
    print(f"\n  {len(aw):,} awards")
    print(f"    multi-transaction: {nm.get('multi',0):,}")
    print(f"    of those, running total went BACKWARDS at least once: "
          f"{nm.get('went_backwards',0):,} "
          f"({nm.get('went_backwards',0)/max(nm.get('multi',1),1):.0%})")
    usable = [a for a in aw if a["cur"] and a["pot"] and a["pot"] > 0]
    print(f"    with a usable current and potential: {len(usable):,} "
          f"({len(usable)/len(aw):.0%})")
    r = sorted(a["cur"] / a["pot"] for a in usable)
    q = lambda p: r[int(p * (len(r) - 1))]
    print(f"\n  exercised share (current / potential):")
    print(f"    p10 {q(.1):.2f}  p25 {q(.25):.2f}  median {q(.5):.2f}  p75 {q(.75):.2f}  "
          f"max {r[-1]:.3f}")
    print(f"    all options taken (>=0.999): {sum(1 for x in r if x>=0.999)/len(r):.0%}")
    print(f"    ceiling never reached (<0.999): {sum(1 for x in r if x<0.999)/len(r):.0%}")
    print(f"    above the ceiling (impossible): "
          f"{sum(1 for x in r if x>1.001)/len(r):.2%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
