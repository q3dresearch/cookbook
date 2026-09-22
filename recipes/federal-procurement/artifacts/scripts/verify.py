#!/usr/bin/env python3
"""Recompute every number the seven figures and the README lean on.

    python3 verify.py

**Why this exists.** Building this recipe, five numbers reached a draft without being
measured: a vehicle share quoted as 74.7% that is 74.5% on either defensible base, a
sealed-bid rate quoted as 6.5% that is 7.0%, a negative-transaction share of 12.5% that is
13.17%, a modification share of 44% that is 46.1%, and a positive-only overstatement of 7%
that is 4.8%. Four came from a subagent's prose and one from mine. None of them changed a
conclusion, which is exactly why nothing caught them.

A second class this catches: a figure whose *subject* has expired. The money-ceiling column
was 29.7% populated in FY2016 and is ~100% in recent data, so figure 15 describes a fault that
has since been fixed. That is a finding, not a bug, but it has to be known.

If a number here disagrees with the README, **this script is authoritative and the prose is a
bug**, per the repo's own rule.
"""
import collections, datetime, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L                                                         # noqa: E402

DATA = os.path.join(HERE, "..", "data")
TODAY = datetime.date(2026, 9, 22)
FAILED = []
VEH = "SUBJECT TO MULTIPLE AWARD FAIR OPPORTUNITY"
ONLY_ONE = {"ONLY ONE SOURCE - OTHER", "URGENCY", "OTHER STATUTORY AUTHORITY",
            "MINIMUM GUARANTEE", "SOLE SOURCE", "UNIQUE SOURCE"}
# Exactly the chart's sets, which its own footer states. Omitting FOLLOW ON TO COMPETED
# ACTION from the first one costs 137 awards; folding TWO STEP in with SEALED BID is the
# difference between a 6.5% and a 7.0% sealed-bid rate.
COMPETED = {"FULL AND OPEN COMPETITION", "COMPETED UNDER SAP",
            "FULL AND OPEN COMPETITION AFTER EXCLUSION OF SOURCES",
            "COMPETITIVE DELIVERY ORDER", "FOLLOW ON TO COMPETED ACTION"}
SEALED = {"SEALED BID", "TWO STEP"}


def chk(label, claimed, actual, tol=0.0):
    ok = abs(claimed - actual) <= tol if tol else claimed == actual
    print(f"  {'ok  ' if ok else 'FAIL'}  {label:<54} claim {claimed!s:>12}   "
          f"computed {actual!s:>12}")
    if not ok:
        FAILED.append(label)


def d(s):
    s = (s or "").strip()[:10]
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        return None


def bids(o):
    """The charts' rule, stated once: a recorded 0 is not a bid count.

    1,876 FY2016 awards record exactly zero offers received. An award that was made
    cannot have drawn no bids, so that is a filing artefact and the charts drop it.
    Keeping it moves the FULL AND OPEN vehicle share from 74.7% to 74.5% and the
    sealed-bid single-bid rate from 6.5% to 7.0% -- which is how two wrong numbers
    reached the README. The rule lives here so both can be checked against it.
    """
    try:
        n = int(float(o))
    except (TypeError, ValueError):
        return None
    return n if n >= 1 else None


def one(o):
    b = bids(o)
    return None if b is None else b == 1


def fold16():
    """One pass over FY2016 collecting everything the checks need."""
    acc, ntx, nmod, nneg, gross_pos = {}, 0, 0, 0, 0.0
    for r in L.transactions(os.path.join(DATA, "civilian-fy2016.zip")):
        k = r.get(L.KEY)
        if not k:
            continue
        ntx += 1
        v = L.num(r.get("federal_action_obligation"))
        if v is not None:
            if v < 0:
                nneg += 1
            else:
                gross_pos += v
        if (r.get("modification_number") or "").strip() not in ("", "0"):
            nmod += 1
        a = acc.get(k)
        if a is None:
            a = acc[k] = {"obl": 0.0, "sb": "", "par": "", "off": "", "cmp": "",
                          "sol": "", "fo": "", "pop": "", "rec": "", "ceil": "",
                          "psc": "", "ag": "", "cur": None, "pot": None}
        a["obl"] += v or 0.0
        for dst, col in (("sb", "contracting_officers_determination_of_business_size"),
                         ("par", "recipient_parent_name"), ("off", "number_of_offers_received"),
                         ("cmp", "extent_competed"), ("sol", "solicitation_procedures"),
                         ("fo", "fair_opportunity_limited_sources"),
                         ("pop", "primary_place_of_performance_state_code"),
                         ("rec", "recipient_state_code"),
                         ("ceil", "potential_total_value_of_award"),
                         ("psc", "product_or_service_code"),
                         ("ag", "awarding_agency_name")):
            if not a[dst]:
                a[dst] = (r.get(col) or "").strip()
        for dst, col in (("cur", "period_of_performance_current_end_date"),
                         ("pot", "period_of_performance_potential_end_date")):
            x = d(r.get(col))
            if x and (a[dst] is None or x > a[dst]):
                a[dst] = x
    return acc, ntx, nmod, nneg, gross_pos


def main():
    print(f"\n  verifying against the files on disk, {TODAY}\n")
    acc, ntx, nmod, nneg, gross_pos = fold16()
    aw = list(acc.values())
    n = len(aw)
    net = sum(a["obl"] for a in aw)

    print("  -- the file itself " + "-" * 62)
    chk("transactions in civilian FY2016", 746960, ntx)
    chk("awards after collapsing on the key", 554171, n)
    chk("net obligations, $bn", 125.75, round(net / 1e9, 2), 0.01)
    chk("negative transactions, %", 13.17, round(100 * nneg / ntx, 2), 0.02)
    chk("modifications, %", 46.1, round(100 * nmod / ntx, 1), 0.2)
    chk("positive-only overstates the net by, %", 4.8,
        round(100 * (gross_pos - net) / net, 1), 0.2)

    print("\n  -- figure 1, small business " + "-" * 54)
    sb = [a for a in aw if a["sb"].upper() == "SMALL BUSINESS"]
    ot = [a for a in aw if a["sb"] and a["sb"].upper() != "SMALL BUSINESS"]
    med = lambda xs: sorted(xs)[len(xs) // 2]
    chk("small business, share of awards %", 52.4, round(100 * len(sb) / n, 1), 0.05)
    chk("small business, share of dollars %", 26.1,
        round(100 * sum(a["obl"] for a in sb) / net, 1), 0.05)
    chk("median small-business award, $", 8555, round(med([a["obl"] for a in sb])))
    chk("median other-than-small award, $", 7314, round(med([a["obl"] for a in ot])), 1)
    big = [a for a in aw if a["obl"] > 316e6]
    chk("awards above $316m", 35, len(big))
    chk("  of those, small business", 0, sum(1 for a in big if a["sb"].upper() == "SMALL BUSINESS"))
    chk("  they hold, % of all money", 23.7,
        round(100 * sum(a["obl"] for a in big) / net, 1), 0.05)

    print("\n  -- figure 3, concentration " + "-" * 55)
    byp = collections.defaultdict(lambda: [0, 0.0])
    for a in aw:
        key = (a["par"] or "").upper().strip() or "(blank)"
        byp[key][0] += 1
        byp[key][1] += a["obl"]
    dollars = sorted((v[1] for v in byp.values()), reverse=True)
    counts = sorted((v[0] for v in byp.values()), reverse=True)
    def half(seq, tot):
        run = 0.0
        for i, x in enumerate(seq, 1):
            run += x
            if run >= tot / 2:
                return i
    chk("recipients holding half the dollars", 74, half(dollars, net), 2)
    chk("recipients holding half the awards", 994, half(counts, n), 10)

    print("\n  -- figure 4, geography " + "-" * 59)
    both = [a for a in aw if a["pop"] and a["rec"]]
    chk("awards carrying both state codes", 547968, len(both), 400)
    chk("performed outside the recipient's state, %", 40.8,
        round(100 * sum(1 for a in both if a["pop"] != a["rec"]) / len(both), 1), 0.1)
    cap = {"DC", "MD", "VA"}
    # base is awards carrying that code, which is what the plate says; against every
    # award the same shares read 19.24 and 20.13, and the difference is the blanks
    nr = sum(1 for a in aw if a["rec"])
    npp = sum(1 for a in aw if a["pop"])
    chk("capital region, share of awards by recipient %", 19.41,
        round(100 * sum(1 for a in aw if a["rec"] in cap) / nr, 2), 0.05)
    chk("capital region, share of awards by performance %", 20.27,
        round(100 * sum(1 for a in aw if a["pop"] in cap) / npp, 2), 0.05)
    cache = os.path.join(DATA, "geo-3yr.json")
    if os.path.exists(cache):
        TY = json.load(open(cache))
        yrs = sorted(TY)
        common = sorted(c for c in TY[yrs[0]] if all(c in TY[y] for y in yrs))
        def rho(a_, b_):
            ma, mb = sum(a_) / len(a_), sum(b_) / len(b_)
            return (sum((x - ma) * (y - mb) for x, y in zip(a_, b_))
                    / (sum((x - ma) ** 2 for x in a_) * sum((y - mb) ** 2 for y in b_)) ** 0.5)
        chk("states scored in all three years", 52, len(common))
        chk("r, FY2015 rate vs FY2017 rate (raw)", 0.72,
            round(rho([TY[yrs[0]][c][1] for c in common],
                      [TY[yrs[-1]][c][1] for c in common]), 2), 0.005)
        chk("r, same with agency mix removed", 0.67,
            round(rho([TY[yrs[0]][c][1] - TY[yrs[0]][c][2] for c in common],
                      [TY[yrs[-1]][c][1] - TY[yrs[-1]][c][2] for c in common]), 2), 0.005)
    else:
        print("  skip  geo-3yr.json absent; run chart-3-geography.py first")

    print("\n  -- figure 5, single offers " + "-" * 55)
    u = [a for a in aw if one(a["off"]) is not None]
    chk("awards with a usable bid count", 550977, len(u), 0)
    zero = sum(1 for a in aw if (a["off"] or "").strip() in ("0", "0.0"))
    chk("  awards recording exactly zero offers, excluded", 1876, zero, 4)
    chk("single-bid overall, %", 59.7, round(100 * sum(1 for a in u if one(a["off"])) / len(u), 1), 0.1)
    lab = [a for a in u if a["cmp"].upper() in COMPETED]
    ls = sum(1 for a in lab if one(a["off"]))
    chk("labelled competed yet drew one bid", 180868, ls, 20)
    chk("  as a share of every award, %", 32.8, round(100 * ls / n, 1), 0.2)
    fo = [a for a in u if a["cmp"].upper() == "FULL AND OPEN COMPETITION"]
    chk("FULL AND OPEN awards", 206656, len(fo), 20)
    chk("  that are orders on a competed vehicle, %", 74.7,
        round(100 * sum(1 for a in fo if a["sol"].upper() == VEH) / len(fo), 1), 0.1)
    nar = [a for a in fo if a["fo"].upper() in ONLY_ONE]
    chk("  carrying an only-one-source reason, %", 16.8, round(100 * len(nar) / len(fo), 1), 0.1)
    chk("    of those, single-bid %", 97.8,
        round(100 * sum(1 for a in nar if one(a["off"])) / len(nar), 1), 0.1)
    comp = [a for a in u if a["cmp"].upper() in COMPETED]
    for name, keys, claim in (("vehicle orders", {VEH}, 59.9),
                              ("sealed bid or two-step", SEALED, 6.5)):
        sub = [a for a in comp if a["sol"].upper() in keys]
        chk(f"  {name}, single-bid % inside the competed label", claim,
            round(100 * sum(1 for a in sub if one(a["off"])) / len(sub), 1), 0.1)

    print("\n  -- figure 15, the money ceiling " + "-" * 51)
    chk("awards with a ceiling recorded, %", 29.7,
        round(100 * sum(1 for a in aw if a["ceil"]) / n, 1), 0.1)
    probe = os.path.join(DATA, "probe-commerce-fy2024.zip")
    if os.path.exists(probe):
        seen = {}
        for r in L.transactions(probe):
            k = r.get(L.KEY)
            if k and k not in seen:
                seen[k] = (r.get("potential_total_value_of_award") or "").strip()
        got = round(100 * sum(1 for v in seen.values() if v) / len(seen), 1)
        print(f"  note  the same column in Commerce FY2024 is {got}% populated — figure 15's "
              f"subject may be historical")

    print("\n  -- figures 15 and 16, schedule " + "-" * 53)
    bd = [a for a in aw if a["cur"] and a["pot"]]
    chk("awards with both schedule dates", 554164, len(bd), 20)
    gaps = sorted((a["pot"] - a["cur"]).days for a in bd if (a["pot"] - a["cur"]).days > 0)
    chk("  share carrying option time, %", 16.73, round(100 * len(gaps) / len(bd), 2), 0.02)
    q = lambda p: gaps[int(p * (len(gaps) - 1))]
    for p, claim in ((0.25, 31), (0.50, 182), (0.75, 730), (0.90, 1187)):
        chk(f"  gap days, p{int(p*100)}", claim, q(p), 2)
    chk("  gaps of exactly 365 days, %", 9.8, round(100 * gaps.count(365) / len(gaps), 1), 0.1)
    chk("  gaps of 28-31 days, %", 15.7,
        round(100 * sum(1 for g in gaps if 28 <= g <= 31) / len(gaps), 1), 0.1)
    chk("  awards with a reversed pair", 1, sum(1 for a in bd if a["pot"] < a["cur"]))

    print("\n  -- figure 9, product families " + "-" * 52)
    import cats
    cf = os.path.join(DATA, "categories-fy2016.json")
    if not os.path.exists(cf):
        print("  skip  categories-fy2016.json absent; run cats.py first")
    else:
        c = json.load(open(cf))
        F = {k: v for k, v in c["families"].items() if v["cn"] and v["cn"] >= 1000}
        sd = lambda v: (sum((x - sum(v) / len(v)) ** 2 for x in v) / len(v)) ** 0.5
        ks = sorted(F)
        act = [F[k]["crate"] for k in ks]
        vp = [c["other_rate"] + F[k]["cveh"] * (c["veh_rate"] - c["other_rate"]) for k in ks]
        chk("families with 1,000+ competed awards", 29, len(F))
        chk("lowest family single-bid rate, %", 14.6, round(100 * min(act), 1), 0.05)
        chk("highest family single-bid rate, %", 64.8, round(100 * max(act), 1), 0.05)
        chk("inside competed: vehicle orders single-bid %", 59.9,
            round(100 * c["veh_rate"], 1), 0.05)
        chk("inside competed: other procedures single-bid %", 32.5,
            round(100 * c["other_rate"], 1), 0.05)
        chk("department mix explains, %", 33.8,
            round(100 * (1 - sd([F[k]["crate"] - F[k]["cexp"] for k in ks]) ** 2
                         / sd(act) ** 2), 1), 0.2)
        chk("the vehicle line explains, %", 18.2,
            round(100 * (1 - sd([a - b for a, b in zip(act, vp)]) ** 2 / sd(act) ** 2), 1),
            0.2)
        # the confound the plate exists to name: on the all-award base the gap vanishes
        # the plate's own population: an award needs a product code to have a family,
        # so the all-award contrast is computed on that base too or it drifts 0.1 pt
        pop = [a for a in aw if a["psc"] and a["ag"] and one(a["off"]) is not None]
        chk("  the figure's population", 550467, len(pop))
        va = [a for a in pop if a["sol"].upper() == VEH]
        nva = [a for a in pop if a["sol"].upper() != VEH]
        chk("ALL awards: vehicle single-bid %", 60.0,
            round(100 * sum(1 for a in va if one(a["off"])) / len(va), 1), 0.1)
        chk("ALL awards: everything else single-bid %", 59.6,
            round(100 * sum(1 for a in nva if one(a["off"])) / len(nva), 1), 0.1)
        chk("facility operation, distinct parent suppliers", 335,
            c["families"]["M"]["suppliers"])
        chk("  its single-bid rate, all awards %", 26.4,
            round(100 * c["families"]["M"]["rate"], 1), 0.05)
        chk("medical/lab equipment, distinct parent suppliers", 10088,
            c["families"]["6"]["suppliers"])
        chk("  its single-bid rate, all awards %", 77.0,
            round(100 * c["families"]["6"]["rate"], 1), 0.05)

    print("\n  -- figure 12, the threshold experiment " + "-" * 43)
    tf = os.path.join(DATA, "thresholds.json")
    if not os.path.exists(tf):
        print("  skip  thresholds.json absent; run thresh.py first")
    else:
        th = json.load(open(tf))
        Y = th["years"]
        chk("FY2017 excess at its own rule, $150k %", 29.1,
            round(Y["2017"]["at_rule"]["excess"], 1), 0.2)
        chk("FY2025 excess at its own rule, $250k %", 37.4,
            round(Y["2025"]["at_rule"]["excess"], 1), 0.2)
        chk("  FY2025 at the OLD rule, $150k %", 4.8,
            round(Y["2025"]["at_other"]["excess"], 1), 0.2)
        pk = lambda y: max(((int(k), v["excess"]) for k, v in Y[y]["sweep"].items() if v),
                           key=lambda r: r[1])[0]
        chk("FY2017 sweep peaks at", 150000, pk("2017"))
        chk("FY2025 sweep peaks at", 250000, pk("2025"))
        chk("FY2016 sweep peaks away from its rule", 310000, pk("2016"))
        # the placebos are the figure's own falsifier: they must stay near zero
        for v in (200000, 300000, 350000):
            for y in ("2017", "2025"):
                e = Y[y]["sweep"][str(v)]["excess"]
                ok = abs(e) <= 20
                print(f"  {'ok  ' if ok else 'FAIL'}  placebo ${v//1000}k in FY{y} stays "
                      f"under 20%{'':<13} computed {e:>11.1f}")
                if not ok:
                    FAILED.append(f"placebo {v} FY{y}")
        chk("FY2025 positive awards", 232751, Y["2025"]["n_positive"])
        chk("FY2016 positive awards", 444495, Y["2016"]["n_positive"])

    print("\n  -- figures 6 to 8, 14, 18 to 20, from their caches " + "-" * 29)
    def J(name):
        f = os.path.join(DATA, name)
        return json.load(open(f)) if os.path.exists(f) else None

    o = J("offers-civilian-fy2016.json")
    if o:
        ag = o["ag"]
        gaps = sorted(d["lab"] / d["n"] - d["multi"] / d["n"] for d in ag.values())
        chk("fig 6: departments where the label exceeds the count", 11,
            sum(1 for g in gaps if g > 0))
        chk("  the gap's range, low end, points", 17.9, round(gaps[0] * 100, 1), 0.1)
        chk("  the gap's range, high end, points", 43.3, round(gaps[-1] * 100, 1), 0.1)
        sa = o["sa"]
        low = sum(1 for k, v in sa.items()
                  if v.get("sa", 0) >= 300 and v.get("open", 0) >= 300
                  and v["sa_1"] / v["sa"] < v["open_1"] / v["open"])
        chk("  set-asides draw MORE bidders in", 11, low)
        pr = o["proc"]
        chk("fig 7: vehicle orders, single-bid %", 59.9,
            round(100 * pr["order against a vehicle"]["one"]
                  / pr["order against a vehicle"]["n"], 1), 0.05)
        chk("  sealed bid or two-step, single-bid %", 6.5,
            round(100 * pr["sealed bid or two-step"]["one"]
                  / pr["sealed bid or two-step"]["n"], 1), 0.05)
        fo = o["fo_full_open"]
        chk("  FULL AND OPEN that are vehicle orders %", 74.7,
            round(100 * fo["vehicle"] / fo["all"], 1), 0.05)

    v = J("vehicles-fy2016.json")
    if v:
        R = [x for x in v["vehicles"] if x["n"] >= v["floor"]]
        chk("fig 8: vehicles with 50+ competed awards", 688, len(R))
        rr = sorted(x["rate"] for x in R)
        chk("  p10 of their single-bid rates, %", 0.0, round(100 * rr[len(rr) // 10], 1))
        chk("  p90, %", 99.0, round(100 * rr[9 * len(rr) // 10], 1), 1.0)
        big = [x for x in R if x["n"] >= 500]
        chk("  of those with 500+ awards, never a second bid", 6,
            sum(1 for x in big if x["rate"] == 0.0))
        chk("  and always a second bid", 0, sum(1 for x in big if x["rate"] == 1.0))

    fl = J("farlines.json")
    if fl:
        by = {r["name"]: r for r in fl["rules"]}
        sa = by["simplified acquisition"]
        chk("fig 14: simplified acquisition, FY2025 at its rule %", 37.4,
            round(sa["at"]["2025"][str(sa["rule"]["2025"])]["excess"], 1), 0.05)
        chk("  the same year at the OLD value %", 4.8,
            round(sa["at"]["2025"]["150000"]["excess"], 1), 0.05)
        cp = by["cost or pricing data"]
        chk("  cost-or-pricing, FY2025 at its rule %", 14.2,
            round(cp["at"]["2025"][str(cp["rule"]["2025"])]["excess"], 1), 0.05)
        mp = by["micro-purchase"]
        neg = all(mp["at"][y][str(mp["rule"][y])]["excess"] < 0 for y in fl["years"])
        print(f"  {'ok  ' if neg else 'FAIL'}  micro-purchase runs NEGATIVE in every year"
              f"{'':<22} computed {neg!s:>11}")
        if not neg:
            FAILED.append("micro-purchase sign")
        ctl = by["subcontracting plan"]
        worst = max(abs(ctl["at"][y][str(ctl["rule"][y])]["excess"]) for y in fl["years"])
        chk("  the control stays under 6 points", True, worst <= 6.0)

    m = J("modauth-fy2016.json")
    if m and "groups" in m:
        g = m["groups"]
        tot = sum(x["dollars"] for x in g.values())
        chk("fig 18: post-award money that is funding or options %", 87.7,
            round(100 * g["planned"]["dollars"] / tot, 1), 0.2)

    cm = J("comparability.json")
    if cm:
        A, B = cm["years"]["2016"], cm["years"]["2025"]
        loss = A["positive"] - B["positive"]
        under = sum(A["counts"][:3]) - sum(B["counts"][:3])
        chk("fig 20: awards lost between FY2016 and FY2025", 211744, loss)
        chk("  share of the loss under $10,000, %", 77.8, round(100 * under / loss, 1), 0.1)
        chk("  transactions per award, FY2016", 1.35, round(A["tx_per_award"], 2), 0.005)
        chk("  transactions per award, FY2025", 1.51, round(B["tx_per_award"], 2), 0.005)

    print()
    if FAILED:
        print(f"  {len(FAILED)} DISAGREEMENT(S): " + "; ".join(FAILED))
        return 1
    print("  every claim reproduces")
    return 0


if __name__ == "__main__":
    sys.exit(main())
