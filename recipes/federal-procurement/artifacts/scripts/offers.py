#!/usr/bin/env python3
"""Shared fold for the three competition figures.

Not a chart. `chart-5-offers.py` draws the label against the bid count,
`chart-18-labelgap.py` draws the same gap per department, and
`chart-19-procedure.py` draws what the procedure actually run predicts. All three read
one award-level pass over the zip, which costs minutes, so it lives here and caches.

The split exists because these were one plate carrying five chart blocks -- two scatters,
a distribution bar, a mosaic and a full-width block chart. Two is the ceiling; see
webprobes/doctrine/one-chart-per-plate.md.

**The bid rule, stated once.** Take `number_of_offers_received` from the award's base
transaction where the file has one and otherwise from a modification, which copies it; the
two disagree on 3 awards in 554,171. A recorded 0 is a filing artefact and not a count.
"""
import collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L, plate                                                  # noqa: E402
from plate import (txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT,  # noqa: E402
                   SURFACE)

SRC = os.path.join(HERE, "..", "data", "civilian-fy2016.zip")
CACHE = os.path.join(HERE, "..", "data", "offers-civilian-fy2016.json")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"

COMPETED = {"FULL AND OPEN COMPETITION", "COMPETED UNDER SAP",
            "FULL AND OPEN COMPETITION AFTER EXCLUSION OF SOURCES",
            "COMPETITIVE DELIVERY ORDER", "FOLLOW ON TO COMPETED ACTION"}
UNCOMPETED = {"NOT COMPETED", "NOT COMPETED UNDER SAP", "NOT AVAILABLE FOR COMPETITION",
              "NON-COMPETITIVE DELIVERY ORDER"}
NO_SET_ASIDE = {"NO SET ASIDE USED.", "NONE", "?", ""}
PROC = {"SUBJECT TO MULTIPLE AWARD FAIR OPPORTUNITY": "order against a vehicle",
        "SIMPLIFIED ACQUISITION": "simplified acquisition",
        "NEGOTIATED PROPOSAL/QUOTE": "proposal or quote solicited",
        "SEALED BID": "sealed bid or two-step", "TWO STEP": "sealed bid or two-step",
        "ARCHITECT-ENGINEER FAR 6.102": "architect-engineer"}
PROC_ORDER = ["order against a vehicle", "simplified acquisition",
              "proposal or quote solicited", "sealed bid or two-step",
              "architect-engineer", "other or not recorded"]
SHORT = {"Department of Veterans Affairs": "Veterans Affairs",
         "Department of Justice": "Justice",
         "Department of Health and Human Services": "Health & Human Services",
         "Department of Homeland Security": "Homeland Security",
         "Department of Agriculture": "Agriculture",
         "Department of the Interior": "Interior",
         "Department of Commerce": "Commerce",
         "Department of Transportation": "Transportation",
         "National Aeronautics and Space Administration": "NASA",
         "Environmental Protection Agency": "EPA",
         "Department of Energy": "Energy"}



def nlines(text, chars):
    """How many lines plate.wrap will produce -- the plate is sized from this."""
    n, line = 1, []
    for w in str(text).split():
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            n, line = n + 1, []
        line.append(w)
    return n


def fold(path):
    """One pass over the zip, collapsed to awards. Cached: the pass costs minutes."""
    acc = {}
    tx = 0
    for r in L.transactions(path):
        tx += 1
        k = r.get(L.KEY)
        if not k:
            continue
        a = acc.get(k)
        if a is None:
            a = acc[k] = {"base": None, "any": None, "had_base": 0, "seen": 0,
                          "ag": r.get("awarding_agency_name") or "?",
                          "cmp": r.get("extent_competed") or "?",
                          "sa": r.get("type_of_set_aside") or "?",
                          "sp": r.get("solicitation_procedures") or "?",
                          "fo": r.get("fair_opportunity_limited_sources") or "?",
                          "amt": 0.0}
        a["amt"] += L.num(r.get("federal_action_obligation")) or 0.0
        is_base = (r.get("modification_number") or "") in ("0", "")
        a["had_base"] |= is_base
        o = (r.get("number_of_offers_received") or "").strip()
        if o:
            a["seen"] += 1
            if a["any"] is None:
                a["any"] = o
            if is_base and a["base"] is None:
                a["base"] = o

    def bids(a):
        v = a["base"] if a["base"] is not None else a["any"]
        try:
            n = int(float(v))
        except (TypeError, ValueError):
            return None
        return n if n >= 1 else None

    c = {"tx": tx, "awards": len(acc), "from_base": 0, "from_mod": 0, "no_count": 0,
         "cells": collections.Counter(), "ag": collections.defaultdict(collections.Counter),
         "sa": collections.defaultdict(collections.Counter),
         "proc": collections.defaultdict(collections.Counter),
         "fo_full_open": collections.Counter(), "dollars": collections.Counter(),
         "band": collections.Counter()}
    for a in acc.values():
        c["from_base"] += a["base"] is not None
        c["from_mod"] += a["base"] is None and a["any"] is not None
        n = bids(a)
        if n is None:
            c["no_count"] += 1
            continue
        cls = "C" if a["cmp"] in COMPETED else ("U" if a["cmp"] in UNCOMPETED else "?")
        one = "1" if n == 1 else "2+"
        ag = SHORT.get(a["ag"], a["ag"][:26])
        c["cells"][cls + "|" + one] += 1
        c["band"]["1" if n == 1 else ("2" if n == 2 else ("3-5" if n <= 5 else "6+"))] += 1
        c["dollars"][one] += a["amt"]
        d = c["ag"][ag]
        d["n"] += 1
        d["lab"] += cls == "C"
        d["multi"] += n > 1
        if cls == "C":
            side = "sa" if a["sa"] not in NO_SET_ASIDE else "open"
            s = c["sa"][ag]
            s[side] += 1
            s[side + "_1"] += n == 1
            p = c["proc"][PROC.get(a["sp"], "other or not recorded")]
            p["n"] += 1
            p["one"] += n == 1
        if a["cmp"] == "FULL AND OPEN COMPETITION":
            k = ("exception" if a["fo"] in
                 ("ONLY ONE SOURCE - OTHER", "ONLY ONE SOURCE", "URGENCY",
                  "OTHER STATUTORY AUTHORITY", "MINIMUM GUARANTEE", "SOLE SOURCE")
                 else "other")
            c["fo_full_open"][k] += 1
            c["fo_full_open"][k + "_1"] += n == 1
            c["fo_full_open"]["vehicle"] += a["sp"] == "SUBJECT TO MULTIPLE AWARD FAIR OPPORTUNITY"
            c["fo_full_open"]["all"] += 1
            c["fo_full_open"]["all_1"] += n == 1
    for key in ("cells", "fo_full_open", "dollars", "band"):
        c[key] = dict(c[key])
    for key in ("ag", "sa", "proc"):
        c[key] = {k: dict(v) for k, v in c[key].items()}
    return c


def cached():
    """The cache is the shipped artefact; the zip is optional.

    The stamp exists to notice a changed source, so it can only be checked when there IS
    a source. With the zip absent the cache is authoritative -- otherwise the receipt
    cannot be read without the thing it was built to replace, which defeats it.
    """
    if not os.path.exists(SRC):
        if os.path.exists(CACHE):
            return json.load(open(CACHE))
        raise SystemExit("  no civilian-fy2016.zip and no cache - run usa2.py 2016")
    stamp = f"{os.path.getsize(SRC)}:{int(os.path.getmtime(SRC))}"
    if os.path.exists(CACHE):
        try:
            c = json.load(open(CACHE))
            if c.get("stamp") == stamp:
                return c
        except (ValueError, OSError):
            pass
    print("  folding transactions (one pass, a few minutes)...", flush=True)
    c = fold(SRC)
    c["stamp"] = stamp
    tmp = CACHE + ".tmp"
    json.dump(c, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return c




def stats():
    """Everything the three plates read, derived once from the cache."""
    c = cached()
    total = c["awards"]
    counted = sum(c["cells"].values())
    ags = []
    for ag, d in c["ag"].items():
        s = c["sa"].get(ag, {})
        ags.append({"ag": ag, "n": d["n"], "lab": d["lab"] / d["n"],
                    "multi": d["multi"] / d["n"],
                    "nopen": s.get("open", 0), "nsa": s.get("sa", 0),
                    "open1": s.get("open_1", 0) / max(s.get("open", 1), 1),
                    "sa1": s.get("sa_1", 0) / max(s.get("sa", 1), 1)})
    ags.sort(key=lambda d: -d["n"])
    procs = [{"lab": k, "n": c["proc"][k]["n"],
              "one": c["proc"][k]["one"] / c["proc"][k]["n"]}
             for k in PROC_ORDER if k in c["proc"]]
    return {"c": c, "total": total, "counted": counted, "ags": ags, "procs": procs,
            "lab": sum(v for k, v in c["cells"].items() if k.startswith("C")),
            "multi": sum(v for k, v in c["cells"].items() if k.endswith("2+")),
            "both": c["cells"]["C|1"],
            "dollars": c["dollars"]["1"] + c["dollars"]["2+"],
            "nproc": sum(p["n"] for p in procs), "fo": c["fo_full_open"]}
