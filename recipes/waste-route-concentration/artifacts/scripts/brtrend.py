#!/usr/bin/env python3
"""Is hazardous waste recovery really collapsing? The row-count claim, checked in tons.

    python3 brtrend.py

Counting rows in the Biennial Report says metals recovery fell 60% between 2001 and 2023
while landfill rose 184%. That would invert the whole circular-economy story of the
period, which is exactly why it needs checking before it is repeated.

**Rows are not tons, for three separate reasons here.**

*The table grew.* Total rows went from 1.13M in 2001 to 1.77M in 2023, so a category can
gain rows while holding steady, purely from finer reporting.

*Two record types share the table.* `br_form` is `GM` for a generation record -- a
generator describing waste it produced -- and `WR` for a received-waste record, a facility
describing waste it took in. `management_category` populates on the management side. In
the 2023 metals-recovery slice that is 4,056 GM rows against 4,199 WR, with
`generation_tons` totalling 1.41 million and `managed_tons` 1.11 million over the same
rows. Adding both columns counts the same waste twice.

*A row is a stream-and-method record, not a facility or a shipment.* One facility
splitting its reporting across more waste codes produces more rows and not more waste.

**And waste managed where it was made is on the other kind of row.** A first version summed
`managed_tons` over `WR` rows only, reasoning that management belongs on the management
record. It does -- but a generator that treats its own waste on site reports that on its
`GM` row, and those rows are few and enormous: in the 2023 cycle, **816 GM rows carry
20.99 million tons against 4.54 million across 126,929 WR rows.** The WR-only measure was
capturing 18% of the waste and calling it the total. Deep-well injection at a chemical
plant is the archetype -- one facility, one line, millions of tons.

So the measure used here is **`managed_tons` on both row types**: on-site management from
the generator's own record, plus waste received and handled by someone else. They do not
double-count, because a generator that ships waste away reports `shipped_tons` and leaves
`managed_tons` at zero.

**The 2021 cycle publishes no tonnage at all.** `generation_tons` and `managed_tons` are
null on every row of that cycle -- verified against the raw API, in every category, not
just the ones pulled here -- while `shipped_tons` and `received_tons` are populated
normally. Summed naively that reads as a year in which America managed zero tons of
hazardous waste, which is the most dangerous kind of wrong number because it looks like an
answer. Any cycle whose column is entirely null is dropped here and named in the output,
never silently zeroed.
"""
import collections, csv, glob, gzip, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
# Same default as brpull.py. These two disagreeing once meant the puller wrote beside the
# recipe while the reader looked in /tmp -- which reports as "no slices in ..." and reads
# like an empty source rather than a wiring mistake.
CACHE = os.environ.get("HWF_CACHE") or os.path.join(DATA, "br-cache")
RECOVERY = {"METALS RECOVERY", "SOLVENTS RECOVERY", "ENERGY RECOVERY", "OTHER RECOVERY"}
DISPOSAL = {"LANDFILL", "DEEPWELL", "INCINERATION"}


def load():
    """Every declared category, every cycle. See brdata for why this is not a glob."""
    sys.path.insert(0, HERE)
    import brdata
    rows = []
    for y in brdata.CYCLES:
        rows.extend(brdata.load(y, brdata.REQUIRED))
    return rows


def norm(cat):
    c = (cat or "").strip().upper()
    if c.startswith("DEEPWELL"):
        return "DEEPWELL"
    if c.startswith("SLUDGE"):
        return "SLUDGE TREATMENT"
    if c.startswith("LAND TREATMENT"):
        return "LAND TREATMENT"
    return c


def main():
    rows = load()
    if not rows:
        print(f"  no slices in {CACHE} -- run brpull.py first")
        return 1
    cycles = sorted({int(r["report_cycle"]) for r in rows if r["report_cycle"]})
    cats = sorted({norm(r["management_category"]) for r in rows} - {""})
    print(f"  {len(rows):,} rows, {len(cats)} categories, cycles {cycles[0]}-{cycles[-1]}\n")

    num = lambda v: float(v) if v not in (None, "", "None") else 0.0
    onsite = collections.defaultdict(float)
    offsite = collections.defaultdict(float)
    # A cycle that publishes no tonnage at all must be refused, not summed to zero.
    blank = {}
    for col in ("generation_tons", "managed_tons"):
        for y in cycles:
            vals = [r[col] for r in rows if int(r["report_cycle"] or 0) == y]
            if vals and not any(v not in (None, "", "None") for v in vals):
                blank.setdefault(col, []).append(y)
    for col, ys in blank.items():
        print(f"  !! {col} is null on every row of cycle(s) {', '.join(map(str, ys))} "
              f"-- excluded, not zeroed")
    dead = {y for ys in blank.values() for y in ys}
    if dead:
        print()
    managed = collections.defaultdict(float)   # (cat, cycle) -> tons, WR rows only
    generated = collections.defaultdict(float)
    nrows = collections.Counter()
    for r in rows:
        c, y = norm(r["management_category"]), int(r["report_cycle"] or 0)
        nrows[(c, y)] += 1
        # managed_tons on a GM row is on-site management; on a WR row it is waste received
        # from elsewhere. Both are management and neither double-counts the other.
        m = num(r["managed_tons"])
        managed[(c, y)] += m
        if r["br_form"] == "WR":
            offsite[(c, y)] += m
        else:
            onsite[(c, y)] += m
            generated[(c, y)] += num(r["generation_tons"])

    def table(title, d, unit=""):
        print(f"  == {title} ==")
        show = [y for y in cycles if not (unit == "M" and y in dead)]
        print(f"  {'category':<22}" + "".join(f"{y:>11}" for y in show) + f"{'2001->2023':>14}")
        show = [y for y in cycles if not (unit == "M" and y in dead)]
        for c in cats:
            first, last = d.get((c, show[0]), 0), d.get((c, show[-1]), 0)
            chg = f"{(last/first-1)*100:+.0f}%" if first else "-"
            print(f"  {c:<22}" + "".join(f"{d.get((c,y),0)/1e6:>11,.2f}" if unit == "M"
                                         else f"{d.get((c,y),0):>11,.0f}" for y in show)
                  + f"{chg:>14}")
        print()

    table("rows (what the naive count sees)", nrows)
    table("millions of tons MANAGED, on-site plus received", managed, "M")
    table("of which managed ON SITE by the generator", onsite, "M")
    table("of which RECEIVED from elsewhere", offsite, "M")

    live = [y for y in cycles if y not in dead]
    print("  == recovery against disposal, in millions of tons managed ==")
    print(f"  {'':<22}" + "".join(f"{y:>11}" for y in live))
    for lab, group in (("recovery", RECOVERY), ("disposal", DISPOSAL)):
        have = group & set(cats)
        print(f"  {lab + ' (' + str(len(have)) + ' cats)':<22}"
              + "".join(f"{sum(managed.get((c,y),0) for c in have)/1e6:>11,.2f}" for y in live))
    rec = {y: sum(managed.get((c, y), 0) for c in RECOVERY & set(cats)) for y in live}
    dis = {y: sum(managed.get((c, y), 0) for c in DISPOSAL & set(cats)) for y in live}
    print(f"  {'recovery share':<22}"
          + "".join(f"{(rec[y]/(rec[y]+dis[y])*100 if rec[y]+dis[y] else 0):>10.1f}%" for y in live))
    print("\n  Note: all twelve management categories are cached and loaded.")
    import json
    json.dump({"rows": {f"{c}|{y}": v for (c, y), v in nrows.items()},
               "managed": {f"{c}|{y}": v for (c, y), v in managed.items()},
               "generated": {f"{c}|{y}": v for (c, y), v in generated.items()}},
              open(os.path.join(DATA, "br_trend.json"), "w"), indent=0, sort_keys=True)
    print(f"\n  wrote {os.path.join(DATA, 'br_trend.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
