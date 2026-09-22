#!/usr/bin/env python3
"""Stream each year's transactions into a compact per-year summary.

    python3 agg.py            # writes artifacts/data/summary-<scope>.json per file

**Why summaries rather than one big load.** A civilian year is ~750,000 transactions and the
decade is ~7.5 million, which is ~4.5 million awards. Held as records that is several
gigabytes for no reason: every figure here wants distributions and cross-tabs, not rows. So
each file is scanned once, folded into counters and histograms, and discarded.

**What is kept per award, and why that is the unit.** 44-62% of rows are modifications, so a
row count is a count of paperwork. Awards are keyed on `contract_award_unique_key` and the
award's value is the **maximum** running total seen, not the last -- the running total moves
backwards on 30% of multi-transaction awards, so `last` is a coin flip there.

**The central quantity is the exercised share**, `current_total_value_of_award` over
`potential_total_value_of_award`: how much of the authorised ceiling a contract actually
reached. It has a real boundary at 1.0 which the data respects, and it is *not*
current-over-base -- `base_and_all_options_value` is a transaction-level field and using it as
a denominator produces ratios in the billions.

A reservoir sample of whole awards is kept as well, because some figures need one mark per
award rather than a histogram, and 4.5 million marks is not a figure.
"""
import collections, json, math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L                                                         # noqa: E402

DATA = os.path.join(HERE, "..", "data")
BINS = [i / 20 for i in range(21)]          # exercised share, 0.00..1.00 in 0.05 steps
RESERVOIR = 40000


def vband(v):
    if v is None or v <= 0:
        return "none"
    e = int(math.floor(math.log10(v)))
    return f"1e{e}"


def fold(path, seed=11):
    """One pass over a zip; returns a summary dict small enough to keep."""
    rnd = random.Random(seed)
    acc = {}
    tx = neg = mods = 0
    for r in L.transactions(path):
        tx += 1
        k = r.get(L.KEY) or r.get("award_id_piid")
        if not k:
            continue
        fa = L.num(r.get("federal_action_obligation")) or 0.0
        if fa < 0:
            neg += 1
        if (r.get("modification_number") or "") not in ("0", ""):
            mods += 1
        cur = L.num(r.get("current_total_value_of_award"))
        pot = L.num(r.get("potential_total_value_of_award"))
        a = acc.get(k)
        if a is None:
            a = acc[k] = {"cur": None, "pot": None, "ob": 0.0, "tx": 0, "back": 0,
                          "prev": None,
                          "ag": (r.get("awarding_agency_name") or "?")[:44],
                          "cmp": (r.get("extent_competed") or "?")[:40],
                          "prc": (r.get("type_of_contract_pricing") or "?")[:40],
                          "sa": (r.get("type_of_set_aside") or "?")[:40],
                          "psc": (r.get("product_or_service_code") or "?")[:4],
                          "rec": (r.get("recipient_name") or "?")[:60],
                          "signed": (r.get("award_base_action_date") or "")[:10]}
        a["tx"] += 1
        a["ob"] += fa
        if cur is not None:
            if a["prev"] is not None and cur < a["prev"] - 0.01:
                a["back"] += 1
            a["prev"] = cur
            a["cur"] = cur if a["cur"] is None else max(a["cur"], cur)
        if pot is not None:
            a["pot"] = pot if a["pot"] is None else max(a["pot"], pot)

    s = {"file": os.path.basename(path), "transactions": tx, "awards": len(acc),
         "negative_tx": neg, "modification_tx": mods,
         "multi_tx_awards": 0, "went_backwards": 0, "usable": 0,
         "hist": {}, "by": {"ag": {}, "cmp": {}, "prc": {}, "sa": {}},
         "vband": collections.Counter(), "sample": [], "recipients": collections.Counter()}
    hist = collections.Counter()
    seen = 0
    for k, a in acc.items():
        if a["tx"] > 1:
            s["multi_tx_awards"] += 1
            if a["back"]:
                s["went_backwards"] += 1
        s["vband"][vband(a["pot"])] += 1
        s["recipients"][a["rec"]] += 1
        if not (a["cur"] and a["pot"] and a["pot"] > 0):
            continue
        s["usable"] += 1
        ratio = min(a["cur"] / a["pot"], 1.0)
        b = min(int(ratio * 20), 20)
        hist[b] += 1
        for dim, key in (("ag", a["ag"]), ("cmp", a["cmp"]), ("prc", a["prc"]),
                         ("sa", a["sa"])):
            d = s["by"][dim].setdefault(key, {"n": 0, "full": 0, "sum": 0.0})
            d["n"] += 1
            d["sum"] += ratio
            if ratio >= 0.999:
                d["full"] += 1
        seen += 1
        rec = {"r": round(ratio, 4), "pot": a["pot"], "ob": round(a["ob"], 2),
               "tx": a["tx"], "ag": a["ag"], "cmp": a["cmp"], "prc": a["prc"],
               "psc": a["psc"], "signed": a["signed"]}
        if len(s["sample"]) < RESERVOIR:
            s["sample"].append(rec)
        else:
            j = rnd.randrange(seen)
            if j < RESERVOIR:
                s["sample"][j] = rec
    s["hist"] = {str(k): v for k, v in sorted(hist.items())}
    s["vband"] = dict(s["vband"])
    s["recipients"] = dict(s["recipients"].most_common(400))
    return s


def main():
    files = L.files("civilian-fy*.zip") + L.files("dod-*.zip")
    if not files:
        raise SystemExit("  no population files yet — usa2.py is still fetching")
    for p in files:
        out = os.path.join(DATA, "summary-" + os.path.basename(p).replace(".zip", ".json"))
        if os.path.exists(out):
            print(f"  {os.path.basename(p):<26}already summarised")
            continue
        print(f"  {os.path.basename(p):<26}folding...", flush=True)
        s = fold(p)
        tmp = out + ".tmp"
        json.dump(s, open(tmp, "w"))
        os.replace(tmp, out)
        print(f"    {s['transactions']:>9,} tx  {s['awards']:>9,} awards  "
              f"{s['usable']:>9,} usable  "
              f"neg {s['negative_tx']/max(s['transactions'],1):.1%}  "
              f"mods {s['modification_tx']/max(s['transactions'],1):.0%}  "
              f"back {s['went_backwards']/max(s['multi_tx_awards'],1):.0%}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
