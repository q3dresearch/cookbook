#!/usr/bin/env python3
"""Award-level fold keyed on the winner, cached beside the data. Q4's input.

Not a chart. `chart-12-repeat.py` draws it. One pass over civilian-fy2016.zip costs a
few minutes; delete `artifacts/data/q4-repeat-fy2016.json` to rebuild.

**Why this fold is award-level and not firm-level.** Q4 asks whether a firm that wins
often is paid differently. Every candidate answer is a rate or a median *per firm*, and
both have to be standardised against award size, which spans five orders of magnitude
here. Standardisation needs the individual awards, not the firm totals, so the cache
keeps one row per award and the firm roll-up happens in the chart.

**Identity.** Three columns are carried per award so the ranking can be rebuilt under
each: the cleaned `recipient_parent_name`, the raw `recipient_parent_name_raw` the filer
typed, and `recipient_parent_uei`. Q27 asks how much the cleaning moves the ranking; that
is a comparison of the first two, and it costs nothing once both are in the row.
`recipient_uei` is deliberately absent -- it is an establishment identifier here (1,299
names carry two or more of them) and grouping on it splits a firm into branches.

**The bid rule is the recipe's.** FIRST non-blank `number_of_offers_received` across the
award's transactions; a recorded `0` is a filing artefact and that award carries no bid
count at all rather than a count of zero. The `bids` column separates the two ways of
having none, because they are different filing behaviours: `0` is a filed zero (1,876
awards) and `-1` is nothing on file (1,318). Anything usable is 1 or more, so every
consumer filters on `> 0` and the two exclusions stay countable.

**Values keep de-obligations.** 13.17% of FY2016 transactions carry a negative
obligation; summing positives only overstates the net by 4.8%.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L                                                         # noqa: E402

DATA = os.path.join(HERE, "..", "data")
CACHE = os.path.join(DATA, "q4-repeat-fy2016.json")
SRC = os.path.join(DATA, "civilian-fy2016.zip")

# first non-blank wins, exactly as the rest of the recipe folds a transaction file
FIELDS = ["recipient_parent_name", "recipient_parent_name_raw", "recipient_parent_uei",
          "number_of_offers_received", "extent_competed_code",
          "solicitation_procedures_code", "product_or_service_code",
          "type_of_set_aside_code", "parent_award_id_piid",
          "awarding_agency_name", "naics_code",
          "contracting_officers_determination_of_business_size_code"]


def num_ok(o):
    try:
        float(o)
        return True
    except (TypeError, ValueError):
        return False


def bids(o):
    """The recipe's rule, shared with the offer figures: a recorded 0 is not a count."""
    try:
        n = int(float(o))
    except (TypeError, ValueError):
        return None
    return n if n >= 1 else None


class Vocab:
    """Column values stored once and referenced by index, so the cache stays small."""

    def __init__(self):
        self.idx, self.vals = {}, []

    def __call__(self, s):
        i = self.idx.get(s)
        if i is None:
            i = self.idx[s] = len(self.vals)
            self.vals.append(s)
        return i


def build():
    acc, tx, neg, pos = {}, 0, 0, 0.0
    for r in L.transactions(SRC):
        tx += 1
        k = r.get(L.KEY)
        if not k:
            continue
        a = acc.get(k)
        if a is None:
            a = acc[k] = {"obl": 0.0}
            for f in FIELDS:
                a[f] = ""
        fa = L.num(r.get("federal_action_obligation")) or 0.0
        a["obl"] += fa
        if fa < 0:
            neg += 1
        else:
            pos += fa
        for f in FIELDS:
            if not a[f]:
                a[f] = (r.get(f) or "").strip()

    vp, vr, vu = Vocab(), Vocab(), Vocab()
    vc, vs, vf, va, vg, vn, vb = (Vocab() for _ in range(7))
    rows = []
    for a in acc.values():
        raw = a["number_of_offers_received"]
        b = bids(raw)
        if b is None:
            # -1 is nothing on file, 0 is a filed zero. Both leave the award without a bid
            # count, but they are different filing behaviours and the recipe quotes both.
            b = 0 if num_ok(raw) else -1
        rows.append([
            vp(a["recipient_parent_name"].upper()),
            vr(a["recipient_parent_name_raw"].upper()),
            vu(a["recipient_parent_uei"].upper()),
            round(a["obl"], 2),
            b,
            vc(a["extent_competed_code"]),
            vs(a["solicitation_procedures_code"]),
            vf(a["product_or_service_code"][:1].upper()),
            va(a["type_of_set_aside_code"]),
            1 if a["parent_award_id_piid"] else 0,
            vg(a["awarding_agency_name"]),
            vn(a["naics_code"][:2]),
            vb(a["contracting_officers_determination_of_business_size_code"]),
        ])
    rows.sort()
    return {"n_tx": tx, "n_neg": neg, "pos_only": pos,
            "net": sum(r[3] for r in rows),
            "cols": ["parent", "parent_raw", "parent_uei", "obl", "bids", "competed",
                     "sol_proc", "psc_family", "set_aside", "on_vehicle", "agency",
                     "naics2", "biz_size"],
            "vocab": {"parent": vp.vals, "parent_raw": vr.vals, "parent_uei": vu.vals,
                      "competed": vc.vals, "sol_proc": vs.vals, "psc_family": vf.vals,
                      "set_aside": va.vals, "agency": vg.vals, "naics2": vn.vals,
                      "biz_size": vb.vals},
            "rows": rows}


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    if not os.path.exists(SRC):
        raise SystemExit("  civilian-fy2016.zip missing - run usa2.py")
    print("  folding civilian-fy2016.zip by award, keyed on the winner ...", flush=True)
    o = build()
    tmp = CACHE + ".tmp"
    json.dump(o, open(tmp, "w"), separators=(",", ":"))
    os.replace(tmp, CACHE)
    return o


if __name__ == "__main__":
    d = load()
    R = d["rows"]
    print(f"  {d['n_tx']:,} transactions -> {len(R):,} awards, "
          f"${d['net']/1e9:.2f}bn net")
    print(f"    {d['n_neg']:,} negative transactions ({d['n_neg']/d['n_tx']:.2%}); "
          f"positives only would overstate by {d['pos_only']/d['net']-1:.2%}")
    print(f"    with a usable bid count: {sum(1 for r in R if r[4] > 0):,}")
    print(f"    filed a zero offer count, which is not a bid count: "
          f"{sum(1 for r in R if r[4] == 0):,}")
    print(f"    nothing on file at all: {sum(1 for r in R if r[4] < 0):,}")
    for c in ("parent", "parent_raw", "parent_uei"):
        print(f"    distinct {c:<12} {len(d['vocab'][c]):,}")
