#!/usr/bin/env python3
"""How much landfill is left, who owns it, and what changed in three years.

    python3 measure.py

Everything is reported against its denominator, because the fields that matter are filled
on roughly half the register and the half that reports is unlikely to be random.
"""
import collections, json, os, statistics as st, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmopdata import DATA, EDITIONS, FRESH, load, num, owner_key, countdown


def main():
    a, b = load("2021"), load("2024")
    both = set(a) & set(b)
    print(f"  2021 edition {len(a):,} sites | 2024 edition {len(b):,} | same id in both {len(both):,}")
    print(f"  new since 2021 {len(set(b)-set(a)):,} | gone {len(set(a)-set(b)):,}")

    st_c = collections.Counter(str(r.get("Current Landfill Status") or "").strip() for r in b.values())
    print(f"  status now: " + ", ".join(f"{k} {v:,}" for k, v in st_c.most_common()))

    print(f"\n== the countdown: years until full, open sites only ==")
    years, why = {}, collections.Counter()
    for k, r in b.items():
        v, reason = countdown(r)
        if v is None:
            why[reason] += 1
        else:
            years[k] = v
    openn = st_c.get("Open", 0)
    print(f"  computable for {len(years):,} of {openn:,} open landfills ({len(years)/openn:.0%})")
    for reason, n in why.most_common(6):
        if reason and reason != "not open":
            print(f"     {n:>5,} excluded: {reason}")
    vals = sorted(years.values())
    print(f"  median {st.median(vals):.0f} years | quarter under {vals[len(vals)//4]:.0f} | "
          f"quarter over {vals[3*len(vals)//4]:.0f} | {sum(1 for v in vals if v < 5):,} under five years")

    print(f"\n== by state: where the room runs out ==")
    bys = collections.defaultdict(list)
    for k, v in years.items():
        bys[str(b[k].get("State") or "").strip()].append(v)
    rows = [(s, st.median(v), len(v)) for s, v in bys.items() if len(v) >= 8]
    rows.sort(key=lambda t: t[1])
    print(f"  {'state':<8}{'median years left':>19}{'sites':>8}")
    for s, m, n in rows[:8]:
        print(f"  {s:<8}{m:>19.0f}{n:>8}")
    print("  ...")
    for s, m, n in rows[-3:]:
        print(f"  {s:<8}{m:>19.0f}{n:>8}")

    print(f"\n== who owns the remaining room ==")
    cap = collections.Counter()
    sites = collections.Counter()
    tot = 0.0
    for k, r in b.items():
        c, w = num(r.get("Landfill Design Capacity (tons)")), num(r.get("Waste in Place (tons)"))
        if c is None or w is None or str(r.get("Current Landfill Status") or "").strip() != "Open":
            continue
        rem = max(c - w, 0)
        key = owner_key(r.get("Landfill Owner Organization(s)"))
        typ = str(r.get("Ownership Type") or "").strip()
        cap[(key, typ)] += rem
        sites[(key, typ)] += 1
        tot += rem
    print(f"  {tot/1e9:.1f} billion tons of remaining permitted capacity across "
          f"{sum(sites.values()):,} open sites that report both numbers")
    top = cap.most_common(8)
    print(f"  {'owner':<34}{'type':<10}{'remaining, Mt':>15}{'share':>8}{'sites':>7}")
    for (k, t), v in top:
        print(f"  {k[:32]:<34}{t:<10}{v/1e6:>15,.0f}{v/tot:>8.1%}{sites[(k,t)]:>7}")
    priv = sum(v for (k, t), v in cap.items() if t == "Private")
    print(f"  private share of remaining capacity: {priv/tot:.1%}")
    print(f"  top four owners hold {sum(v for _, v in top[:4])/tot:.1%}")

    print(f"\n== what changed between the two editions ==")
    raw = sum(1 for k in both
              if str(a[k].get("Landfill Owner Organization(s)")) != str(b[k].get("Landfill Owner Organization(s)")))
    real = [k for k in both
            if owner_key(a[k].get("Landfill Owner Organization(s)")) != owner_key(b[k].get("Landfill Owner Organization(s)"))]
    print(f"  owner string changed on {raw:,} sites; after normalising the name, {len(real):,} actually changed hands")
    print(f"  the difference is one rebrand: Waste Management became WM in 2022")
    moved = collections.Counter()
    for k in real:
        moved[(owner_key(a[k].get("Landfill Owner Organization(s)"))[:24],
               owner_key(b[k].get("Landfill Owner Organization(s)"))[:24])] += 1
    for (x, y), n in moved.most_common(5):
        print(f"     {n:>3}  {x:<26} -> {y}")
    gas = [k for k in both
           if str(a[k].get("LFG Collection System In Place?")).strip() in ("No", "None", "")
           and str(b[k].get("LFG Collection System In Place?")).strip() == "Yes"]
    lost = [k for k in both
            if str(a[k].get("LFG Collection System In Place?")).strip() == "Yes"
            and str(b[k].get("LFG Collection System In Place?")).strip() in ("No", "None", "")]
    closed = [k for k in both
              if str(a[k].get("Current Landfill Status")).strip() == "Open"
              and str(b[k].get("Current Landfill Status")).strip() == "Closed"]
    print(f"  gained a gas collection system: {len(gas)}   lost one: {len(lost)}   closed: {len(closed)}")

    json.dump({"sites_2021": len(a), "sites_2024": len(b), "status": dict(st_c),
               "countdown_n": len(years), "open": openn,
               "countdown_median": st.median(vals), "countdown_q1": vals[len(vals)//4],
               "countdown_q3": vals[3*len(vals)//4], "under_five": sum(1 for v in vals if v < 5),
               "years": years,
               "by_state": [{"state": s, "median_years": m, "sites": n} for s, m, n in rows],
               "remaining_total_tons": tot,
               "owners": [{"owner": k, "type": t, "remaining_tons": v, "sites": sites[(k, t)]}
                          for (k, t), v in cap.most_common(20)],
               "private_share": priv / tot,
               "owner_change_raw": raw, "owner_change_real": len(real),
               "gained_gas": len(gas), "lost_gas": len(lost), "closed": len(closed)},
              open(os.path.join(DATA, "landfill.json"), "w"), indent=1)
    print(f"\n  wrote {os.path.join(DATA, 'landfill.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
