#!/usr/bin/env python3
"""Fold a 300 MB year into a few hundred KB, once, so nothing has to fold it again.

    python3 condense.py 2016 2015 ...       # or no arguments for every zip present

**The problem this solves.** A civilian fiscal year is a ~300 MB zip that USAspending
generates on request, and the generation is the slow part -- 40 minutes and up, server-side,
before a byte is transferred. Re-folding it on every figure build costs minutes; re-fetching
it costs the better part of an hour. Neither is necessary, because every figure in this
recipe wants distributions and cross-tabs, not rows.

**What this keeps.** Counters, cross-tabs and sampled cumulative curves -- never records. The
output is ~1/3000 the size of its input, small enough to live with the recipe, so a reader
can rebuild every figure and run `verify.py` without fetching anything.

**What it refuses to be.** A substitute for the source. The provenance block records the
source file's name, byte count and SHA-256, the fiscal year, the date it was condensed and
the two rules that are easy to get wrong (how an award's value is taken from its
transactions, and what counts as a bid). If the zip is present, `verify.py` re-derives the
numbers from it and compares; if it is absent, the recipe still builds but says so. A cache
that cannot say what it was built from is how drift gets in -- an atomic write prevents a
half-written file, not a stale one.

**Why the value is the MAXIMUM running total, not the last.** `base_and_all_options_value`
and the running obligation move backwards on ~30% of multi-transaction awards, so `last` is
close to a coin flip on those. That rule is stamped into the provenance because changing it
silently would change nearly every number downstream.
"""
import collections, datetime, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L                                                         # noqa: E402

DATA = os.path.join(HERE, "..", "data")
TODAY = datetime.date(2026, 9, 22).isoformat()
CAP = ("DC", "MD", "VA")
VEH = "SUBJECT TO MULTIPLE AWARD FAIR OPPORTUNITY"
COMPETED = {"FULL AND OPEN COMPETITION", "COMPETED UNDER SAP",
            "FULL AND OPEN COMPETITION AFTER EXCLUSION OF SOURCES",
            "COMPETITIVE DELIVERY ORDER", "FOLLOW ON TO COMPETED ACTION"}
ONLY_ONE = {"ONLY ONE SOURCE - OTHER", "URGENCY", "OTHER STATUTORY AUTHORITY",
            "MINIMUM GUARANTEE", "SOLE SOURCE", "UNIQUE SOURCE"}
SEALED = {"SEALED BID", "TWO STEP"}
# half-decade value bands, so a share can be read against award size without the raw values
EDGES = [0, 300, 1000, 3162, 10000, 31623, 100000, 316228, 1e6, 3.162e6, 1e7,
         3.162e7, 1e8, 3.162e8, 1e9, float("inf")]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def bids(o):
    """The recipe's one bid rule: a recorded 0 offers is not a bid count."""
    try:
        n = int(float(o))
    except (TypeError, ValueError):
        return None
    return n if n >= 1 else None


def band(v):
    for i in range(len(EDGES) - 1):
        if EDGES[i] <= v < EDGES[i + 1]:
            return i
    return len(EDGES) - 2


def curve(sorted_desc, total, points=240):
    """A cumulative share curve, sampled at log-spaced ranks rather than stored whole.

    81,330 recipients is a list nobody needs; what every figure reads off it is the share
    held by the top N, and that is smooth enough to sample.
    """
    out, run, j = [], 0.0, 0
    ranks = sorted({int(round(10 ** (i / 40))) for i in range(int(40 * 5.2))}
                   | {1, 10, 74, 100, 994, 1000, len(sorted_desc)})
    ranks = [r for r in ranks if 1 <= r <= len(sorted_desc)]
    for r in ranks:
        while j < r:
            run += sorted_desc[j]
            j += 1
        out.append([r, run / total if total else 0.0])
    return out


def condense(fy):
    src = os.path.join(DATA, f"civilian-fy{fy}.zip")
    if not os.path.exists(src):
        raise SystemExit(f"  civilian-fy{fy}.zip missing - run usa2.py {fy}")
    print(f"  folding civilian-fy{fy}.zip ...", flush=True)

    acc, ntx, nmod, nneg, gross_pos = {}, 0, 0, 0, 0.0
    for r in L.transactions(src):
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
                          "sol": "", "fo": "", "sa": "", "pop": "", "rec": "",
                          "ceil": "", "psc": "", "ag": "", "at": ""}
        a["obl"] += v or 0.0
        for dst, col in (("sb", "contracting_officers_determination_of_business_size"),
                         ("par", "recipient_parent_name"),
                         ("off", "number_of_offers_received"),
                         ("cmp", "extent_competed"),
                         ("sol", "solicitation_procedures"),
                         ("fo", "fair_opportunity_limited_sources"),
                         ("sa", "type_of_set_aside"),
                         ("pop", "primary_place_of_performance_state_code"),
                         ("rec", "recipient_state_code"),
                         ("ceil", "potential_total_value_of_award"),
                         ("psc", "product_or_service_code"),
                         ("ag", "awarding_agency_name"),
                         ("at", "award_type")):
            if not a[dst]:
                a[dst] = (r.get(col) or "").strip()
    aw = list(acc.values())
    n = len(aw)
    net = sum(a["obl"] for a in aw)

    o = {"provenance": {
            "source": os.path.basename(src), "bytes": os.path.getsize(src),
            "sha256": sha256(src), "condensed_at": TODAY, "fiscal_year": int(fy),
            "award_key": L.KEY,
            "value_rule": "sum of federal_action_obligation per award; de-obligations kept",
            "bid_rule": "first non-blank number_of_offers_received; a recorded 0 is not a "
                        "bid count",
            "field_rule": "first non-blank value across the award's transactions"},
         "file": {"transactions": ntx, "awards": n, "negative_tx": nneg,
                  "modification_tx": nmod, "net": net, "gross_positive": gross_pos},
         "bands": {"edges": EDGES[:-1] + [None]}}

    # ---- size, and who is small ---------------------------------------------------
    sizes = collections.defaultdict(lambda: [0, 0.0])
    bnd = collections.defaultdict(lambda: [0, 0, 0.0, 0.0])     # n, n_small, $, $small
    for a in aw:
        s = a["sb"].upper() or "(blank)"
        sizes[s][0] += 1
        sizes[s][1] += a["obl"]
        if a["obl"] > 0:
            b = band(a["obl"])
            sm = s == "SMALL BUSINESS"
            bnd[b][0] += 1
            bnd[b][1] += sm
            bnd[b][2] += a["obl"]
            bnd[b][3] += a["obl"] if sm else 0.0
    o["size"] = {"classes": {k: v for k, v in sorted(sizes.items())},
                 "by_band": {str(k): v for k, v in sorted(bnd.items())}}
    sb = sorted(a["obl"] for a in aw if a["sb"].upper() == "SMALL BUSINESS")
    ot = sorted(a["obl"] for a in aw if a["sb"] and a["sb"].upper() != "SMALL BUSINESS")
    o["size"]["median_small"] = sb[len(sb) // 2]
    o["size"]["median_other"] = ot[len(ot) // 2]
    big = [a for a in aw if a["obl"] > 316e6]
    o["size"]["above_316m"] = {
        "n": len(big), "n_small": sum(1 for a in big if a["sb"].upper() == "SMALL BUSINESS"),
        "dollars": sum(a["obl"] for a in big)}
    sa = collections.defaultdict(lambda: [0, 0.0, []])
    for a in aw:
        g = sa[a["sa"].upper() or "(blank)"]
        g[0] += 1
        g[1] += a["obl"]
        g[2].append(a["obl"])
    o["set_aside"] = {k: [v[0], v[1], sorted(v[2])[len(v[2]) // 2]]
                      for k, v in sorted(sa.items()) if v[0] >= 200}

    # ---- concentration, as curves rather than 81,330 rows ---------------------------
    byp = collections.defaultdict(lambda: [0, 0.0])
    for a in aw:
        p = (a["par"] or "").upper().strip() or "(blank)"
        byp[p][0] += 1
        byp[p][1] += a["obl"]
    dsc = sorted((v[1] for v in byp.values()), reverse=True)
    csc = sorted((v[0] for v in byp.values()), reverse=True)
    o["concentration"] = {
        "parents": len(byp),
        "dollar_curve": curve(dsc, sum(dsc)), "award_curve": curve(csc, sum(csc)),
        "top20_by_dollars": [[k, v[0], v[1]] for k, v in
                             sorted(byp.items(), key=lambda kv: -kv[1][1])[:20]],
        "top20_by_awards": [[k, v[0], v[1]] for k, v in
                            sorted(byp.items(), key=lambda kv: -kv[1][0])[:20]]}

    # ---- geography ------------------------------------------------------------------
    st = collections.defaultdict(lambda: [0, 0, 0.0, 0.0])      # rec n, pop n, rec $, pop $
    both = cross = 0
    dcross = 0.0
    for a in aw:
        if a["rec"]:
            st[a["rec"]][0] += 1
            st[a["rec"]][2] += a["obl"]
        if a["pop"]:
            st[a["pop"]][1] += 1
            st[a["pop"]][3] += a["obl"]
        if a["rec"] and a["pop"]:
            both += 1
            if a["rec"] != a["pop"]:
                cross += 1
                dcross += a["obl"]
    o["geography"] = {
        "states": {k: v for k, v in sorted(st.items())},
        "both_codes": both, "cross_state": cross, "cross_dollars": dcross,
        "with_rec": sum(1 for a in aw if a["rec"]),
        "with_pop": sum(1 for a in aw if a["pop"]),
        "capital_rec": sum(1 for a in aw if a["rec"] in CAP),
        "capital_pop": sum(1 for a in aw if a["pop"] in CAP)}

    # ---- offers: the cross-tabs the competition figures read ------------------------
    def tab(keyfn, rows):
        t = collections.defaultdict(lambda: [0, 0])
        for a in rows:
            b = bids(a["off"])
            if b is None:
                continue
            k = keyfn(a)
            t[k][0] += 1
            t[k][1] += b == 1
        return {k: v for k, v in sorted(t.items())}
    usable = [a for a in aw if bids(a["off"]) is not None]
    fo = [a for a in usable if a["cmp"].upper() == "FULL AND OPEN COMPETITION"]
    comp = [a for a in usable if a["cmp"].upper() in COMPETED]
    o["offers"] = {
        "usable": len(usable),
        "zero_offer_awards": sum(1 for a in aw if (a["off"] or "").strip() in ("0", "0.0")),
        "by_extent": tab(lambda a: a["cmp"].upper() or "(blank)", aw),
        "by_procedure": tab(lambda a: a["sol"].upper() or "(blank)", aw),
        "by_procedure_competed": tab(lambda a: a["sol"].upper() or "(blank)", comp),
        "by_agency": tab(lambda a: a["ag"], aw),
        "by_agency_competed": tab(lambda a: a["ag"], comp),
        "by_setaside_competed": tab(lambda a: a["sa"].upper() or "(blank)", comp),
        "full_open": {
            "n": len(fo),
            "vehicle": sum(1 for a in fo if a["sol"].upper() == VEH),
            "only_one_source": sum(1 for a in fo if a["fo"].upper() in ONLY_ONE),
            "only_one_source_single":
                sum(1 for a in fo if a["fo"].upper() in ONLY_ONE and bids(a["off"]) == 1)},
        "sealed_competed": [sum(1 for a in comp if a["sol"].upper() in SEALED),
                            sum(1 for a in comp if a["sol"].upper() in SEALED
                                and bids(a["off"]) == 1)],
        "competed_single": sum(1 for a in comp if bids(a["off"]) == 1)}

    # ---- the money ceiling, which is the subject of figure 15 -------------------------
    cov = collections.defaultdict(lambda: [0, 0, 0, 0])   # n, with, competed n, competed with
    for a in aw:
        g = cov[a["ag"]]
        g[0] += 1
        g[1] += bool(a["ceil"])
        if a["cmp"].upper() in COMPETED:
            g[2] += 1
            g[3] += bool(a["ceil"])
    o["ceiling"] = {"with_ceiling": sum(1 for a in aw if a["ceil"]),
                    "by_agency": {k: v for k, v in sorted(cov.items())},
                    "by_award_type": tab(lambda a: a["at"].upper() or "(blank)", aw)}
    o["ceiling"]["by_award_type"] = {
        k: [v[0], sum(1 for a in aw if (a["at"].upper() or "(blank)") == k and a["ceil"])]
        for k, v in o["ceiling"]["by_award_type"].items()}
    return o


def path_for(fy):
    return os.path.join(DATA, f"condensed-fy{fy}.json")


def load(fy):
    p = path_for(fy)
    if os.path.exists(p):
        return json.load(open(p))
    o = condense(fy)
    tmp = p + ".tmp"
    json.dump(o, open(tmp, "w"))
    os.replace(tmp, p)
    return o


def main():
    years = [a for a in sys.argv[1:] if a.isdigit()]
    if not years:
        years = sorted(f[len("civilian-fy"):-4] for f in os.listdir(DATA)
                       if f.startswith("civilian-fy") and f.endswith(".zip"))
    for y in years:
        o = load(y)
        p = path_for(y)
        pv, fl = o["provenance"], o["file"]
        print(f"  FY{y}: {fl['awards']:,} awards from {fl['transactions']:,} transactions")
        print(f"    {pv['bytes']/1e6:,.0f} MB source -> {os.path.getsize(p)/1024:,.0f} KB "
              f"condensed  ({pv['bytes']/os.path.getsize(p):,.0f}x smaller)")
        print(f"    sha256 {pv['sha256'][:16]}...  condensed {pv['condensed_at']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
