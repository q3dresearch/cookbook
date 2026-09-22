#!/usr/bin/env python3
"""Per-vehicle competition behaviour, cached beside the data.

Not a chart. `chart-15-vehicles.py` draws it.

**Why the vehicle and not a category.** Figure 5 explained single bids with
`solicitation_procedures`, which records whether an award was an order against a
multiple-award vehicle. That is a stand-in. `parent_award_id_piid` names the ACTUAL parent
contract, and it is populated on 67.9% of competed awards. The recipe has spent eight
figures measuring categories an award belongs to; this measures the instrument it was
placed against.

**The thing to check before believing any of it** is whether the 0% and 100% tails are
small-n artefacts, so every rate here ships with the award count that produced it and the
figure raises the floor tenfold to show the tails survive.
"""
import collections, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L                                                         # noqa: E402

DATA = os.path.join(HERE, "..", "data")
CACHE = os.path.join(DATA, "vehicles-fy2016.json")
SRC = os.path.join(DATA, "civilian-fy2016.zip")
COMPETED = {"FULL AND OPEN COMPETITION", "COMPETED UNDER SAP",
            "FULL AND OPEN COMPETITION AFTER EXCLUSION OF SOURCES",
            "COMPETITIVE DELIVERY ORDER", "FOLLOW ON TO COMPETED ACTION"}
FLOOR = 50            # vehicles below this many competed awards are not scored


def bids(o):
    """The recipe's rule: a recorded 0 offers is not a bid count."""
    try:
        n = int(float(o))
    except (TypeError, ValueError):
        return None
    return n if n >= 1 else None


def build():
    acc = {}
    for r in L.transactions(SRC):
        k = r.get(L.KEY)
        if not k:
            continue
        a = acc.get(k)
        if a is None:
            a = acc[k] = {"off": "", "cmp": "", "par": "", "psc": "", "ag": "",
                          "obl": 0.0}
        a["obl"] += L.num(r.get("federal_action_obligation")) or 0.0
        for d, c in (("off", "number_of_offers_received"),
                     ("cmp", "extent_competed"),
                     ("par", "parent_award_id_piid"),
                     ("psc", "product_or_service_code"),
                     ("ag", "awarding_agency_name")):
            if not a[d]:
                a[d] = (r.get(c) or "").strip()

    comp = [a for a in acc.values()
            if bids(a["off"]) is not None and a["cmp"].upper() in COMPETED]
    named = [a for a in comp if a["par"]]

    # each family's own rate, so a vehicle can be scored against the mix of things it buys
    fam = collections.defaultdict(lambda: [0, 0])
    for a in named:
        f = a["psc"][:1].upper() or "?"
        fam[f][0] += 1
        fam[f][1] += bids(a["off"]) == 1
    frate = {f: k / n for f, (n, k) in fam.items() if n >= 500}

    veh = collections.defaultdict(lambda: {"n": 0, "s": 0, "exp": 0.0, "nexp": 0,
                                           "obl": 0.0, "ag": collections.Counter(),
                                           "psc": collections.Counter()})
    for a in named:
        g = veh[a["par"]]
        g["n"] += 1
        g["s"] += bids(a["off"]) == 1
        g["obl"] += a["obl"]
        g["ag"][a["ag"]] += 1
        f = a["psc"][:1].upper() or "?"
        g["psc"][f] += 1
        if f in frate:
            g["exp"] += frate[f]
            g["nexp"] += 1

    rows = []
    for v, g in sorted(veh.items()):
        if g["n"] < FLOOR:
            continue
        rows.append({"id": v[:40], "n": g["n"], "rate": g["s"] / g["n"],
                     "obl": g["obl"],
                     "exp": (g["exp"] / g["nexp"]) if g["nexp"] >= 40 else None,
                     "nexp": g["nexp"],
                     "ag": g["ag"].most_common(1)[0][0],
                     "agshare": g["ag"].most_common(1)[0][1] / g["n"],
                     "psc": g["psc"].most_common(1)[0][0],
                     "pscshare": g["psc"].most_common(1)[0][1] / g["n"]})
    return {"vehicles": rows,
            "n_competed": len(comp), "n_named": len(named),
            "n_distinct": len(veh), "floor": FLOOR,
            "pooled_rate": sum(1 for a in named if bids(a["off"]) == 1) / len(named),
            "family_rates": frate}


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    if not os.path.exists(SRC):
        raise SystemExit("  civilian-fy2016.zip missing - run usa2.py")
    print("  folding civilian-fy2016.zip by parent vehicle ...", flush=True)
    d = build()
    tmp = CACHE + ".tmp"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return d


if __name__ == "__main__":
    d = load()
    R = d["vehicles"]
    print(f"  {d['n_named']:,} of {d['n_competed']:,} competed awards name a parent "
          f"({d['n_named']/d['n_competed']:.1%}); {d['n_distinct']:,} distinct vehicles")
    print(f"  {len(R):,} carry {d['floor']}+ awards; pooled single-bid {d['pooled_rate']:.1%}")
    for lo in (50, 100, 250, 500):
        g = sorted(x["rate"] for x in R if x["n"] >= lo)
        if len(g) < 10:
            continue
        print(f"    {lo:>4}+ awards: {len(g):>4} vehicles  p10 {g[len(g)//10]:>5.0%}  "
              f"median {g[len(g)//2]:>5.0%}  p90 {g[9*len(g)//10]:>5.0%}  "
              f"at 0% {sum(1 for r in g if r == 0):>3}  at 100% {sum(1 for r in g if r == 1):>3}")
