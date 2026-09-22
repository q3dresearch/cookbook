#!/usr/bin/env python3
"""The two columns figures 1-10 never opened: the cited exception, and what a mod does.

    python3 modauth.py        # folds the zip once, then prints the cross-tabs

Not a chart. `chart-14-modtypes.py` draws it. The pass costs minutes, so it caches beside
the data; delete the JSON to rebuild.

**Two units live in this file and they are not interchangeable.**
`other_than_full_and_open_competition` is an AWARD property -- the statutory authority cited
when the work was not fully competed -- so it is folded first-non-blank across the award's
transactions, exactly like the bid count. `action_type` is a TRANSACTION property: one award
carries many actions of different kinds, and collapsing it to the award would silently pick
one of them. It is therefore counted per transaction, and the award-level numbers derived
from it are sums of dollars, never a label.

**Both fields are coded twice and the code is the stable one.** FPDS relabelled every
exception mid-year -- `SAP NON-COMPETITION` and `SAP NON-COMPETITION (FAR 13)` are the same
code SP2, and `MICRO PURCHASE THRESHOLD` and `LESS THAN OR EQUAL TO THE MICRO-PURCHASE
THRESHOLD` are both MPT. Grouping on the printed label would split eighteen authorities into
thirty-five and halve the count of every one of them. Everything here groups on the code and
the label drift is counted and reported.
"""
import collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L                                                          # noqa: E402

DATA = os.path.join(HERE, "..", "data")
CACHE = os.path.join(DATA, "modauth-fy2016.json")
SRC = os.path.join(DATA, "civilian-fy2016.zip")
# Bumped whenever build() changes shape, so the cache rebuilds instead of being read with a
# schema it does not have. The zip's size and mtime alone would not have caught that.
VERSION = 2

# The action codes, in the order the bitmask uses. Anything outside this list lands in the
# last slot, so the mask is stable across rebuilds.
AT_CODES = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P", "R",
            "S", "T", "V", "W", "X"]
AT_BIT = {c: 1 << i for i, c in enumerate(AT_CODES)}
OTHER_BIT = 1 << len(AT_CODES)

# The three things a modification can be, for the award-level roll-up. The drawn figure uses
# the twenty codes individually; this coarser split exists so the award-level cross against
# the competition authority is a 3-column table rather than a 20-column one.
#   PLANNED  money against work already agreed and priced at award
#   SCOPED   a negotiated change to the agreement itself, in or out of scope
#   ADMIN    closeouts, terminations, name and address changes
PLANNED_AT = {"C", "G"}
SCOPED_AT = {"A", "B", "D", "L", "H"}

# award-slot indices
(AUTH, OFF, EXT, AG, PSC, SA, OBL, BASE, POST, MASK, TX, MODS,
 PLAN, SCOPE, ADMIN) = range(15)


def bids(o):
    """The recipe's rule: a recorded 0 is not a bid count, and that award is excluded."""
    try:
        n = int(float(o))
    except (TypeError, ValueError):
        return None
    return n if n >= 1 else None


def build():
    acc = {}
    at = collections.defaultdict(lambda: [0, 0.0, 0, 0.0, 0, 0.0, 0])
    at_base = collections.Counter()
    at_mod = collections.Counter()
    auth_lab = collections.defaultdict(collections.Counter)
    at_lab = collections.defaultdict(collections.Counter)
    auth_where = collections.Counter()       # is the authority written on the base row?
    dept = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0.0]))
    tx_total = 0

    for r in L.transactions(SRC):
        tx_total += 1
        k = r.get(L.KEY)
        if not k:
            continue
        fa = L.num(r.get("federal_action_obligation")) or 0.0
        mod = (r.get("modification_number") or "").strip()
        is_base = mod in ("0", "")
        a = acc.get(k)
        if a is None:
            a = acc[k] = ["", "", "", "", "", "", 0.0, 0.0, 0.0, 0, 0, 0, 0.0, 0.0, 0.0]
        a[OBL] += fa
        a[TX] += 1
        if is_base:
            a[BASE] += fa
        else:
            a[POST] += fa
            a[MODS] += 1
            c0 = (r.get("action_type_code") or "").strip().upper()
            a[PLAN if c0 in PLANNED_AT else
              (SCOPE if c0 in SCOPED_AT else ADMIN)] += fa
        for slot, col in ((AUTH, "other_than_full_and_open_competition_code"),
                          (OFF, "number_of_offers_received"),
                          (EXT, "extent_competed"),
                          (AG, "awarding_agency_name"),
                          (PSC, "product_or_service_code"),
                          (SA, "type_of_set_aside")):
            if not a[slot]:
                v = (r.get(col) or "").strip()
                if v:
                    a[slot] = v

        ac = (r.get("action_type_code") or "").strip().upper()
        al = (r.get("action_type") or "").strip()
        s = at[ac]
        s[0] += 1
        s[1] += fa
        if fa > 0:
            s[2] += 1
            s[3] += fa
        elif fa < 0:
            s[4] += 1
            s[5] += fa
        else:
            s[6] += 1
        (at_base if is_base else at_mod)[ac] += 1
        if al:
            at_lab[ac][al] += 1
        if ac:
            a[MASK] |= AT_BIT.get(ac, OTHER_BIT)
        # the falsifier for the pooled split: does one department make the mix?
        d = dept[(r.get("awarding_agency_name") or "?")][ac or "-base-"]
        d[0] += 1
        d[1] += fa

        aw = (r.get("other_than_full_and_open_competition_code") or "").strip().upper()
        if aw:
            auth_lab[aw][(r.get("other_than_full_and_open_competition") or "").strip()] += 1
            auth_where["base" if is_base else "mod"] += 1

    # ------------------------------------------------------------------ award-level roll-up
    mk = lambda: {"n": 0, "n_bid": 0, "b1": 0, "b2": 0, "b35": 0, "b6": 0,
                  "obl": 0.0, "vals": [], "ext": collections.Counter(),
                  "ag": collections.Counter(), "sa": collections.Counter(),
                  "psc": collections.Counter(), "nonpos": 0,
                  "base$": 0.0, "plan$": 0.0, "scope$": 0.0, "admin$": 0.0, "nmod": 0}
    auth = collections.defaultdict(mk)
    ext_auth = collections.Counter()
    growth = {"with_base": 0, "base_pos": 0, "grew": 0, "shrank": 0, "flat": 0,
              "base_sum": 0.0, "post_sum": 0.0, "ratios": []}
    mask_n = collections.Counter()
    mask_money = collections.defaultdict(float)
    n_awards = len(acc)
    no_count = 0

    for a in acc.values():
        n = bids(a[OFF])
        code = a[AUTH] or "-none-"
        g = auth[code]
        g["n"] += 1
        g["obl"] += a[OBL]
        g["ext"][a[EXT] or "?"] += 1
        g["ag"][a[AG] or "?"] += 1
        g["sa"][a[SA] or "?"] += 1
        g["psc"][(a[PSC] or "?")[:1]] += 1
        g["base$"] += a[BASE]
        g["plan$"] += a[PLAN]
        g["scope$"] += a[SCOPE]
        g["admin$"] += a[ADMIN]
        g["nmod"] += a[MODS] > 0
        if a[OBL] <= 0:
            g["nonpos"] += 1
        else:
            g["vals"].append(a[OBL])
        if n is None:
            no_count += 1
        else:
            g["n_bid"] += 1
            g["b1"] += n == 1
            g["b2"] += n == 2
            g["b35"] += 3 <= n <= 5
            g["b6"] += n >= 6
        if a[AUTH]:
            ext_auth[a[EXT] or "?"] += 1
        # which action kinds touched this award, and the money that came after the base
        for c in AT_CODES:
            if a[MASK] & AT_BIT[c]:
                mask_n[c] += 1
        if a[MASK] & OTHER_BIT:
            mask_n["?"] += 1
        if a[BASE] or a[MODS] == 0:
            pass
        if a[MODS] and a[TX] > a[MODS]:          # a base row for this award is in this file
            growth["with_base"] += 1
            growth["base_sum"] += a[BASE]
            growth["post_sum"] += a[POST]
            if a[BASE] > 0:
                growth["base_pos"] += 1
                growth["ratios"].append((a[BASE] + a[POST]) / a[BASE])
                if a[POST] > 0.01:
                    growth["grew"] += 1
                elif a[POST] < -0.01:
                    growth["shrank"] += 1
                else:
                    growth["flat"] += 1

    def pcts(v):
        v = sorted(v)
        if not v:
            return {}
        q = lambda p: v[min(int(p * len(v)), len(v) - 1)]
        return {f"p{int(p*100)}": q(p) for p in
                (.01, .05, .1, .25, .5, .75, .9, .95, .99)} | {"max": v[-1], "min": v[0]}

    # FAR dollar lines the authorities name in their own text, FY2016 values
    LINES = [3500, 10000, 25000, 150000, 700000, 7000000]

    out = {"tx": tx_total, "awards": n_awards, "no_count": no_count,
           "auth_where": dict(auth_where),
           "action": {}, "auth": {}, "growth": {}, "ext_auth": dict(ext_auth),
           "dept": {d: {c: v for c, v in s.items()} for d, s in dept.items()}}

    for c, s in sorted(at.items(), key=lambda kv: -kv[1][0]):
        out["action"][c or "-blank-"] = {
            "n": s[0], "obl": s[1], "n_pos": s[2], "pos": s[3], "n_neg": s[4], "neg": s[5],
            "n_zero": s[6], "on_base": at_base[c], "on_mod": at_mod[c],
            "awards": mask_n[c] if c in AT_BIT else (mask_n["?"] if c else 0),
            "labels": dict(at_lab[c].most_common())}

    for c, g in auth.items():
        v = sorted(g["vals"])
        out["auth"][c] = {
            "n": g["n"], "n_bid": g["n_bid"], "b1": g["b1"], "b2": g["b2"],
            "b35": g["b35"], "b6": g["b6"], "obl": g["obl"], "nonpos": g["nonpos"],
            "pct": pcts(v),
            "above": {str(t): sum(1 for x in v if x > t) for t in LINES},
            "base$": g["base$"], "plan$": g["plan$"], "scope$": g["scope$"],
            "admin$": g["admin$"], "nmod": g["nmod"],
            "ext": dict(g["ext"].most_common(6)),
            "ag": dict(g["ag"].most_common(6)),
            "sa": dict(g["sa"].most_common(6)),
            "psc": dict(g["psc"].most_common(6)),
            "labels": dict(auth_lab[c].most_common()) if c != "-none-" else {},
            # a coarse log histogram so a distribution can be drawn without shipping 554k
            # floats: bins are half-decades from $10 to $10bn
            "hist": _hist(v)}

    r = sorted(growth["ratios"])
    out["growth"] = {k: v for k, v in growth.items() if k != "ratios"}
    out["growth"]["ratio_pct"] = pcts(r)
    out["growth"]["n_ratio"] = len(r)
    return out


def _hist(v, lo=1.0, hi=1e10, per=4):
    """Counts per quarter-decade. Returns [lo_exp, per_decade, counts]."""
    import math
    nb = int(round((math.log10(hi) - math.log10(lo)) * per))
    out = [0] * (nb + 1)
    for x in v:
        b = int((math.log10(max(x, lo)) - math.log10(lo)) * per)
        out[min(max(b, 0), nb)] += 1
    return [math.log10(lo), per, out]


def load():
    if not os.path.exists(SRC) and os.path.exists(CACHE):
        return json.load(open(CACHE))   # the receipt stands without the zip
    stamp = f"v{VERSION}:{os.path.getsize(SRC)}:{int(os.path.getmtime(SRC))}"
    if os.path.exists(CACHE):
        try:
            c = json.load(open(CACHE))
            if c.get("stamp") == stamp:
                return c
        except (ValueError, OSError):
            pass
    if not os.path.exists(SRC):
        raise SystemExit("  civilian-fy2016.zip missing - run usa2.py")
    print("  folding civilian-fy2016.zip (one pass, a few minutes) ...", flush=True)
    c = build()
    c["stamp"] = stamp
    tmp = CACHE + ".tmp"
    json.dump(c, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return c


def main():
    d = load()
    print(f"  {d['tx']:,} transactions, {d['awards']:,} awards, "
          f"{d['no_count']:,} with no usable bid count")
    print(f"  authority written on base rows {d['auth_where'].get('base',0):,}, "
          f"on modification rows {d['auth_where'].get('mod',0):,}")
    print("\n  action_type, per TRANSACTION")
    print(f"    {'code':<6}{'label':<52}{'tx':>9}{'on base':>9}{'on mod':>9}"
          f"{'net $m':>12}{'awards':>9}")
    for c, s in d["action"].items():
        lab = next(iter(s["labels"]), "")[:50]
        print(f"    {c:<6}{lab:<52}{s['n']:>9,}{s['on_base']:>9,}{s['on_mod']:>9,}"
              f"{s['obl']/1e6:>12,.0f}{s['awards']:>9,}")
    g = d["growth"]
    print(f"\n  growth: {g['with_base']:,} awards have both a base row and a modification "
          f"in this file")
    print(f"    base $ {g['base_sum']/1e9:.2f}bn, post-base $ {g['post_sum']/1e9:.2f}bn")
    print(f"    of {g['base_pos']:,} with a positive base: grew {g['grew']:,}, "
          f"shrank {g['shrank']:,}, flat {g['flat']:,}")
    print(f"    growth ratio {g['ratio_pct']}")
    print("\n  post-base dollars by department, the falsifier for the pooled split")
    print(f"    {'department':<34}{'post $m':>10}{'planned':>9}{'scoped':>9}{'admin':>9}")
    for dname, s in sorted(d["dept"].items(),
                           key=lambda kv: -sum(v[1] for c, v in kv[1].items()
                                               if c != "-base-")):
        post = sum(v[1] for c, v in s.items() if c != "-base-")
        if abs(post) < 1e7:
            continue
        pl = sum(v[1] for c, v in s.items() if c in PLANNED_AT)
        sc = sum(v[1] for c, v in s.items() if c in SCOPED_AT)
        print(f"    {dname[:33]:<34}{post/1e6:>10,.0f}{pl/post:>9.1%}{sc/post:>9.1%}"
              f"{(post-pl-sc)/post:>9.1%}")

    print("\n  other_than_full_and_open_competition, per AWARD")
    print(f"    {'code':<6}{'label':<46}{'awards':>9}{'1 bid':>8}{'net $m':>11}"
          f"{'median $':>11}{'p99 $':>12}")
    for c, s in sorted(d["auth"].items(), key=lambda kv: -kv[1]["n"]):
        lab = next(iter(s["labels"]), "")[:44]
        one = s["b1"] / s["n_bid"] if s["n_bid"] else 0
        p = s["pct"]
        print(f"    {c:<6}{lab:<46}{s['n']:>9,}{one:>8.1%}{s['obl']/1e6:>11,.0f}"
              f"{p.get('p50',0):>11,.0f}{p.get('p99',0):>12,.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
