#!/usr/bin/env python3
"""When each class was described: taxonomic authorship years, one pull per class.

    python3 described.py       # fetch and cache

Figure 9's accumulation curve runs on the date carried by a *record*, which is when a specimen
was collected, not when the species became known to science. `scientificNameAuthorship` carries
the real thing -- "Weber, 1913", "(Pallas, 1766)" -- and it is populated for essentially every
species row the checklist returns: 4,483 of 4,483 sponge species, 1,164 of 1,166 sharks.

**The year taken is the FIRST in the string, which is the original description.** Parentheses
around an authorship mean the species was later moved to another genus, and the year inside
them still belongs to the original description, so `(Pallas, 1766)` is 1766. Taking the last
year in the string instead would pick up a later revision where one is cited.

**What this can and cannot show.** It is a clean record of when taxonomy happened, so the
expedition eras, the war years and the molecular period are all visible directly. It says
nothing about when a species was first *seen*: a specimen can sit in a drawer for decades before
anyone describes it, and the lag between collection and description is not in this file.

**The checklist must be paged, and paged with the right word.** It caps at 10,000 rows and
returns HTTP 500 above that, and sea snails alone have 28,494. The paging parameter is `skip`:
`from`, `offset` and `after` are all accepted and silently ignored, returning page one again.
That matters more than usual here because the checklist is **sorted by record count descending**,
so a truncated pull would keep the best-recorded species and drop the rest -- and how well
recorded a species is correlates with how long ago it was described. Truncation would have bent
this figure toward the 19th century. `paged` records the distinct names actually assembled
against the total the API claims.

**Only `taxonRank == "Species"` rows are counted.** A checklist also returns genera and higher
ranks with their own authorships -- `Demospongiae Sollas, 1885` is the class itself -- and
counting those would put a spike wherever a group was erected.
"""
import json, os, re, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("OBIS_DATA") or os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "described.json")
UA = "web-snapshots research bot (dl.eeee.nv@gmail.com)"
YEAR = re.compile(r"\b(1[5-9]\d{2}|20[0-2]\d)\b")
BIN = 5
LO, HI = 1750, 2025

CLASSES = [
    ("Actinopterygii", "ray-finned fish"), ("Elasmobranchii", "sharks and rays"),
    ("Cephalopoda", "squid and octopus"), ("Malacostraca", "crabs and shrimp"),
    ("Gastropoda", "sea snails"), ("Bivalvia", "clams and mussels"),
    ("Polychaeta", "bristle worms"), ("Anthozoa", "corals and anemones"),
    ("Hydrozoa", "hydroids"), ("Scyphozoa", "true jellyfish"),
    ("Echinoidea", "sea urchins"), ("Asteroidea", "sea stars"),
    ("Holothuroidea", "sea cucumbers"), ("Demospongiae", "sponges"),
    ("Mammalia", "marine mammals"), ("Aves", "seabirds"),
    ("Bacillariophyceae", "diatoms"), ("Phaeophyceae", "brown algae"),
    ("Florideophyceae", "red algae"),
]


def g(path, params=None):
    u = f"https://api.obis.org/v3/{path}" + (
        "?" + urllib.parse.urlencode(params) if params else "")
    for a in range(4):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(u, headers={"User-Agent": UA}), timeout=600) as r:
                return json.load(r)
        except Exception:                                                # noqa: BLE001
            if a == 3:
                raise
            time.sleep(2 * (a + 1))


def load():
    if not os.path.exists(OUT):
        raise SystemExit("  described.json not cached -- run described.py first")
    return json.load(open(OUT))


def main():
    if os.path.exists(OUT):
        print(f"  cached: {len(load()['classes'])} classes")
        return 0
    out = {"bin": BIN, "lo": LO, "hi": HI, "classes": {}}
    for sci, common in CLASSES:
        res, seen, skip, total = [], set(), 0, None
        while True:
            r = g("checklist", {"scientificname": sci, "size": 10000, "skip": skip})
            page = r.get("results") or []
            total = r.get("total") if total is None else total
            if not page:
                break
            for x in page:
                nm = x.get("scientificName")
                if nm and nm not in seen:
                    seen.add(nm)
                    res.append(x)
            skip += len(page)
            if skip >= (total or 0) or len(page) < 10000:
                break
            time.sleep(0.3)
        if total and abs(len(res) - total) > max(5, total * 0.02):
            print(f"    WARNING {sci}: assembled {len(res)} distinct of {total} claimed")
        r = {"total": total}
        sp = [x for x in res if (x.get("taxonRank") or "").lower() == "species"]
        hist, yrs, noyear = {}, [], 0
        for x in sp:
            m = YEAR.search(str(x.get("scientificNameAuthorship") or ""))
            if not m:
                noyear += 1
                continue
            y = int(m.group(1))
            if not (LO <= y <= HI):
                continue
            yrs.append(y)
            hist[y // BIN * BIN] = hist.get(y // BIN * BIN, 0) + 1
        yrs.sort()
        out["classes"][sci] = {
            "common": common, "total_rows": r.get("total"), "paged": len(res),
            "species": len(sp),
            "dated": len(yrs), "no_year": noyear,
            "median": yrs[len(yrs) // 2] if yrs else None,
            "since2000": sum(1 for y in yrs if y >= 2000) / len(yrs) if yrs else 0,
            "hist": {str(k): v for k, v in sorted(hist.items())}}
        print(f"  {common:<20}{len(sp):>7,} species  {len(yrs):>7,} dated  "
              f"median {out['classes'][sci]['median']}  "
              f"{out['classes'][sci]['since2000']:5.1%} since 2000")
        time.sleep(0.4)
    os.makedirs(DATA, exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"\n  written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
