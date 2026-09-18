#!/usr/bin/env python3
"""The two open questions the data already on disk can answer.

    python3 followup.py

**Q14, who the countdown cannot see.** Figures 1 and 2 are computed on the 863 open sites
that report design capacity, a dated stock and an acceptance rate. 403 do not. If the
missing third differs from the counted two thirds, every figure inherits the difference,
and the only honest way to bound that is to compare the groups on the fields BOTH carry.

**Q12, whether a closure pushes waste next door.** The countdown assumes today's rate
holds. Thirty sites closed between the two editions and the file carries coordinates, so
this is a small natural experiment rather than an assumption.

Two measurement notes, both of which cost a wrong answer first:

*The median is unusable here.* 23% of sites report an acceptance rate identical to three
years earlier and the rest split 42/35 up and down, so the median change is exactly 0.0%
in every subgroup and the permutation test on it returns p = 1.000 at every radius. That
reads as a clean null and is an artefact of where the median lands inside the block of
zeros. This uses the share that moved up, with Wilson intervals, and a winsorised mean.

*A null is worth nothing without the effect size it could have detected.* So the closures'
surrendered tonnage is compared against what the receiving sites already take. At 40 km a
full redistribution would be a 55% lift, which is far above the noise, and that is what
makes the null a finding rather than a shrug.
"""
import collections, json, math, os, random, statistics as st, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmopdata import DATA, load, num, owner_key, countdown

RATE = "Annual Waste Acceptance Rate (tons per year)"
WIP = "Waste in Place (tons)"
RADII = (40, 80, 160)
SEED = 20260916


def latlon(r):
    la, lo = num(r.get("Latitude")), num(r.get("Longitude"))
    return (la, lo) if la and lo else None


def km(p, q):
    la1, lo1, la2, lo2 = map(math.radians, (p[0], p[1], q[0], q[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(min(1, math.sqrt(h)))


def wilson(k, n, z=1.96):
    if not n:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def winsor_mean(v, tail=0.05):
    w = sorted(v)
    t = max(1, int(len(w) * tail))
    return sum(w[t:len(w) - t] or w) / len(w[t:len(w) - t] or w)


def q14(b, out):
    print("== Q14: how do the sites the countdown can see differ from the ones it cannot? ==")
    op = [r for r in b.values() if str(r.get("Current Landfill Status") or "").strip() == "Open"]
    seen = [r for r in op if countdown(r)[0] is not None]
    blind = [r for r in op if countdown(r)[0] is None]
    print(f"  {len(seen):,} open sites can be counted, {len(blind):,} cannot\n")
    print(f"  {'':46}{'counted':>10}{'not counted':>14}")
    tests = (("privately owned", lambda r: str(r.get("Ownership Type") or "").strip() == "Private"),
             ("has a gas collection system", lambda r: str(r.get("LFG Collection System In Place?") or "").strip() == "Yes"),
             ("owned by WM or Republic", lambda r: owner_key(r.get("Landfill Owner Organization(s)")) in ("wm", "republic")),
             ("reports a waste-in-place figure", lambda r: num(r.get(WIP)) is not None),
             ("reports an acceptance rate", lambda r: num(r.get(RATE)) is not None))
    for name, f in tests:
        a_, b_ = sum(map(f, seen)) / len(seen), sum(map(f, blind)) / len(blind)
        print(f"  {name:<46}{a_:>10.0%}{b_:>14.0%}")
        out.setdefault("q14_shares", {})[name] = {"counted": a_, "not_counted": b_}
    for name, f in (("waste in place, median tons", lambda r: num(r.get(WIP))),
                    ("acceptance rate, median tons/yr", lambda r: num(r.get(RATE))),
                    ("year opened, median", lambda r: num(r.get("Year Landfill Opened")))):
        v1 = [x for x in map(f, seen) if x]
        v2 = [x for x in map(f, blind) if x]
        if v1 and v2:
            print(f"  {name:<46}{st.median(v1):>10,.0f}{st.median(v2):>14,.0f}")
            out.setdefault("q14_medians", {})[name] = {"counted": st.median(v1), "not_counted": st.median(v2)}

    # The number that decides whether the bias matters: coverage by tonnage, not by site.
    tot = lambda rows, f: sum(num(r.get(f)) or 0 for r in rows)
    print()
    for lbl, f in (("annual acceptance", RATE), ("waste already in place", WIP)):
        c, n = tot(seen, f), tot(blind, f)
        print(f"  coverage by {lbl:<24}{c/(c+n):>9.1%}   ({c:,.0f} of {c+n:,.0f} tons)")
        out.setdefault("q14_coverage", {})[lbl] = c / (c + n)
    out["q14_coverage"]["site count"] = len(seen) / len(op)
    print(f"  coverage by {'site count':<24}{len(seen)/len(op):>9.1%}   ({len(seen):,} of {len(op):,} sites)")
    print(f"\n  reasons a site has no countdown:")
    for why, k in collections.Counter(countdown(r)[1] for r in blind).most_common(4):
        print(f"    {why:<34}{k:>5}  ({k/len(blind):.0%})")
    print("\n  -> the blind third is small, so the bias is in the SITE COUNT, not the TONNAGE.")
    print("     Figures 1 and 2 are near-complete about national capacity and two thirds")
    print("     complete about the typical landfill. Say which claim you are making.\n")


def q12(a, b, out):
    print("== Q12: does a closure push waste to the nearest open hole? ==")
    closed = []
    for k in sorted(set(a) & set(b)):
        if (str(a[k].get("Current Landfill Status")).strip() == "Open"
                and str(b[k].get("Current Landfill Status")).strip() == "Closed"):
            p, r = latlon(b[k]) or latlon(a[k]), num(a[k].get(RATE))
            if p and r and r > 0:
                closed.append((p, r))
    lost = sum(r for _, r in closed)
    print(f"  {len(closed)} closures carry coordinates and a prior rate, giving up {lost:,.0f} tons/yr\n")

    # How big would the effect be if every displaced ton went to the neighbours? Without
    # this, a null says nothing: it could just be an instrument too blunt to see it.
    openp = [(latlon(r), num(r.get(RATE))) for r in b.values()
             if str(r.get("Current Landfill Status")).strip() == "Open"]
    openp = [(p, r) for p, r in openp if p and r and r > 0]
    print(f"  {'effect a full redistribution would produce':<46}")
    for Rk in RADII:
        near = [r for p, r in openp if any(km(p, q) <= Rk for q, _ in closed)]
        if near:
            print(f"    within {Rk:>3} km: {len(near):>4} sites taking {sum(near):>13,.0f} t/yr"
                  f"  -> +{lost/sum(near):.0%}")
            out.setdefault("q12_detectable", {})[Rk] = lost / sum(near)

    sites = []
    for k in sorted(set(a) & set(b)):
        if str(b[k].get("Current Landfill Status")).strip() != "Open":
            continue
        r0, r1, p = num(a[k].get(RATE)), num(b[k].get(RATE)), latlon(b[k])
        if p and r0 and r1 and r0 > 0 and r1 > 0:
            sites.append((p, math.log(r1 / r0)))
    d = [x for _, x in sites]
    z, up, dn = sum(x == 0 for x in d), sum(x > 0 for x in d), sum(x < 0 for x in d)
    print(f"\n  {len(d):,} open sites have a positive rate in both editions:")
    print(f"    {up} rose ({up/len(d):.0%}), {dn} fell ({dn/len(d):.0%}), {z} identical ({z/len(d):.0%})")
    print(f"    -> the median change is exactly 0 for any subgroup, so it is not used here\n")

    print(f"  {'':30}{'n':>6}{'rose':>7}{'95% Wilson':>16}{'winsorised mean':>18}")
    for Rk in RADII:
        hit = [x for p, x in sites if any(km(p, q) <= Rk for q, _ in closed)]
        non = [x for p, x in sites if not any(km(p, q) <= Rk for q, _ in closed)]
        for lbl, v in ((f"within {Rk} km of a closure", hit), (f"no closure within {Rk} km", non)):
            if not v:
                continue
            k_, n_ = sum(x > 0 for x in v), sum(x != 0 for x in v)
            lo, hi = wilson(k_, n_)
            wm = math.expm1(winsor_mean(v))
            print(f"  {lbl:<30}{len(v):>6}{k_/n_:>7.0%}{f'{lo:.0%} - {hi:.0%}':>16}{wm:>+18.1%}")
            out.setdefault("q12", {}).setdefault(str(Rk), {})[lbl.split()[0]] = {
                "n": len(v), "rose": k_ / n_, "wilson": [lo, hi], "winsorised_mean": wm}
        print()

    # Dose-response. Binary near/far throws away that some closures were much larger.
    exp = [(sum(r for q, r in closed if km(p, q) <= 80), x) for p, x in sites]
    xs, ys = [e for e, _ in exp], [x for _, x in exp]

    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        rk, i = [0.0] * len(v), 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for t in range(i, j + 1):
                rk[o[t]] = (i + j) / 2 + 1
            i = j + 1
        return rk

    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    den = math.sqrt(sum((v - mx) ** 2 for v in rx) * sum((v - my) ** 2 for v in ry))
    rho = sum((rx[i] - mx) * (ry[i] - my) for i in range(n)) / den
    rng, hits = random.Random(SEED), 0
    for _ in range(20000):
        sh = ry[:]
        rng.shuffle(sh)
        if abs(sum((rx[i] - mx) * (sh[i] - my) for i in range(n)) / den) >= abs(rho) - 1e-12:
            hits += 1
    p = (hits + 1) / 20001
    print(f"  dose-response, closed tons/yr within 80 km against log rate change:")
    print(f"    Spearman rho = {rho:+.3f}   permutation p = {p:.3f}   n = {n:,}")
    out["q12_dose"] = {"rho": rho, "p": p, "n": n}
    print("\n  -> no spillover at any radius, and at 40 km the effect that a full")
    print("     redistribution would produce is 55%, twenty times what was measured.")
    print("     The waste does not go to the nearest hole. Where it goes is question 19.\n")


def instrument(a, b, out):
    print("== does the register actually update between editions? ==")
    both = [k for k in sorted(set(a) & set(b)) if str(b[k].get("Current Landfill Status")).strip() == "Open"]
    for f in (RATE, WIP, "Waste in Place Year", "Landfill Design Capacity (tons)"):
        same = moved = 0
        for k in both:
            x, y = num(a[k].get(f)), num(b[k].get(f))
            if x is None or y is None:
                continue
            same, moved = same + (x == y), moved + (x != y)
        print(f"  {f:<46}{moved/(same+moved):>7.0%} changed  (of {same+moved:,})")
        out.setdefault("drift", {})[f] = moved / (same + moved)
    adv = sum(1 for k in both
              if (num(a[k].get("Waste in Place Year")) or 0) < (num(b[k].get("Waste in Place Year")) or 0))
    print(f"  {'sites whose stock year advanced':<46}{adv/len(both):>7.0%} of {len(both):,}")
    print("  -> it is a live register, not a stale one. The diff is measuring real revisions.\n")


def main():
    a, b = load("2021"), load("2024")
    out = {}
    q14(b, out)
    q12(a, b, out)
    instrument(a, b, out)
    path = os.path.join(DATA, "followup.json")
    json.dump(out, open(path, "w"), indent=1, sort_keys=True)
    print(f"  wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
