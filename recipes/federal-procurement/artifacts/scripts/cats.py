#!/usr/bin/env python3
"""Award-level fold by product/service family, cached beside the data.

Not a chart. `chart-8-categories.py` draws it. The fold costs a few minutes, so it
caches; delete the JSON to rebuild.

A PSC's first character is its family -- 'Y' is construction, '6' is medical and lab
equipment, 'R' is professional support. The families are the register's own taxonomy,
not a grouping invented here, which matters because the figure's claim is that this
taxonomy predicts competition better than the buyer does.
"""
import collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L                                                         # noqa: E402

DATA = os.path.join(HERE, "..", "data")
CACHE = os.path.join(DATA, "categories-fy2016.json")
SRC = os.path.join(DATA, "civilian-fy2016.zip")
VEH = "SUBJECT TO MULTIPLE AWARD FAIR OPPORTUNITY"
# Figure 5's sets, repeated because its mechanism only holds INSIDE the competed label:
# across all awards, vehicle orders are 60.0% single-bid and everything else 59.6%, which
# is not a mechanism, it is the uncompeted awards (99%+ single-bid whatever the procedure)
# swamping the comparison. Every rate below is therefore reported on both bases.
COMPETED = {"FULL AND OPEN COMPETITION", "COMPETED UNDER SAP",
            "FULL AND OPEN COMPETITION AFTER EXCLUSION OF SOURCES",
            "COMPETITIVE DELIVERY ORDER", "FOLLOW ON TO COMPETED ACTION"}
MIN_N = 1000              # families below this many offer-coded awards are not scored

FAM = {"1": "weapons", "2": "vehicles and engines", "3": "machinery",
       "4": "pipes, pumps, valves", "5": "construction materials",
       "6": "medical, lab and photo equipment", "7": "office, IT and furniture",
       "8": "clothing and subsistence", "9": "fuels and chemicals",
       "A": "research and development", "B": "special studies",
       "C": "architect and engineering", "D": "IT services",
       "E": "purchase of structures", "F": "natural resources",
       "G": "social services", "H": "quality control and testing",
       "J": "equipment maintenance", "K": "equipment modification",
       "L": "technical representative", "M": "facility operation",
       "N": "installation of equipment", "P": "salvage", "Q": "medical services",
       "R": "professional support", "S": "utilities and housekeeping",
       "T": "photographic and mapping", "U": "education and training",
       "V": "transport and travel", "W": "equipment lease",
       "X": "real property lease", "Y": "construction",
       "Z": "maintenance of real property"}


def bids(o):
    """The recipe's rule, shared with the offer figures: a recorded 0 is not a count."""
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
            a = acc[k] = {"psc": "", "ag": "", "sp": "", "par": "", "off": "",
                          "cmp": "", "obl": 0.0}
        a["obl"] += L.num(r.get("federal_action_obligation")) or 0.0
        for dst, c in (("psc", "product_or_service_code"),
                       ("ag", "awarding_agency_name"),
                       ("sp", "solicitation_procedures"),
                       ("par", "recipient_parent_name"),
                       ("cmp", "extent_competed"),
                       ("off", "number_of_offers_received")):
            if not a[dst]:
                a[dst] = (r.get(c) or "").strip()

    rows = [(a["psc"][:1].upper(), a["ag"], a["sp"].upper() == VEH,
             bids(a["off"]) == 1, a["obl"], (a["par"] or "?").upper(),
             a["cmp"].upper() in COMPETED)
            for a in acc.values()
            if a["psc"] and a["ag"] and bids(a["off"]) is not None]
    comp = [r for r in rows if r[6]]

    # what each department's own single-bid rate is, so a family can be scored against
    # the mix of departments that happen to buy it
    def drates(rs):
        dep = collections.defaultdict(lambda: [0, 0])
        for _, d, _, s, _, _, _ in rs:
            dep[d][0] += 1
            dep[d][1] += s
        return {d: k / n for d, (n, k) in dep.items()}
    drate, drate_c = drates(rows), drates(comp)

    # the award-level mechanism of figure 5, so it can be extrapolated to families
    vn = sum(1 for r in comp if r[2])
    vs = sum(1 for r in comp if r[2] and r[3])
    on = len(comp) - vn
    os_ = sum(1 for r in comp if not r[2] and r[3])

    mk = lambda: {"n": 0, "s": 0, "exp": 0.0, "veh": 0, "obl": 0.0,
                  "sup": collections.Counter()}
    fam = collections.defaultdict(mk)
    famc = collections.defaultdict(mk)
    for f, d, v, s, o, p, is_c in rows:
        g = fam[f]
        g["n"] += 1; g["s"] += s; g["exp"] += drate[d]; g["veh"] += v
        g["obl"] += o; g["sup"][p] += 1
        if is_c:
            h = famc[f]
            h["n"] += 1; h["s"] += s; h["exp"] += drate_c[d]; h["veh"] += v

    out = {"families": {},
           "national": sum(1 for r in rows if r[3]) / len(rows),
           "national_c": sum(1 for r in comp if r[3]) / len(comp),
           "veh_rate": vs / vn, "other_rate": os_ / on,
           "n_rows": len(rows), "n_comp": len(comp), "n_awards": len(acc),
           "veh_n": vn, "other_n": on}
    for f, g in sorted(fam.items()):
        if g["n"] < MIN_N:
            continue
        tot = sum(g["sup"].values())
        out["families"][f] = {
            "name": FAM.get(f, "other"), "n": g["n"], "rate": g["s"] / g["n"],
            "exp": g["exp"] / g["n"], "veh": g["veh"] / g["n"], "obl": g["obl"],
            "suppliers": len(g["sup"]),
            "top5": sum(c for _, c in g["sup"].most_common(5)) / tot,
            "cn": famc[f]["n"],
            "crate": famc[f]["s"] / famc[f]["n"] if famc[f]["n"] else None,
            "cexp": famc[f]["exp"] / famc[f]["n"] if famc[f]["n"] else None,
            "cveh": famc[f]["veh"] / famc[f]["n"] if famc[f]["n"] else None}
    return out


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    if not os.path.exists(SRC):
        raise SystemExit("  civilian-fy2016.zip missing - run usa2.py")
    print("  folding civilian-fy2016.zip by product family ...", flush=True)
    o = build()
    tmp = CACHE + ".tmp"
    json.dump(o, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return o


if __name__ == "__main__":
    d = load()
    print(f"  {len(d['families'])} families, {d['n_rows']:,} scored awards")
    print(f"  inside the competed label ({d['n_comp']:,} awards): vehicle orders "
          f"{d['veh_rate']:.1%} single-bid, other procedures {d['other_rate']:.1%}")
    print(f"  national single-bid: all {d['national']:.1%}, competed only "
          f"{d['national_c']:.1%}")
