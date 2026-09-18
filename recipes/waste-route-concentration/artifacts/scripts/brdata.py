#!/usr/bin/env python3
"""One loader, one declared basket, so a figure means the same thing twice.

    python3 brdata.py        # report what is cached against what is required

**Why this exists.** The first analyses globbed `*-{cycle}.csv.gz` out of the cache and
summed whatever was there. The cache was being written by a background pull at the same
time, so the basket grew underneath the work: a concentration figure computed when six
management categories were cached said 2001 held 30.8 million tons, and the same code an
hour later — with wastewater treatment added — said **226 million**. Neither number was
wrong for its basket. Both were wrong to be called "2001".

So nothing globs any more. A script names the categories it wants, `load()` refuses
quietly-missing ones, and the basket travels with the number.

`REQUIRED` is every management category the register uses. `RECOVERY` and `DISPOSAL` are
the two groupings the recipe argues about. A figure that uses a subset says so on its face.
"""
import csv, glob, gzip, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
# Set BR_CACHE to reuse a pull from elsewhere; otherwise the cache lands beside this recipe.
# It is never committed -- the repo ships the fetcher instead, so a fork is cheap.
CACHE = os.environ.get("BR_CACHE") or os.path.join(DATA, "br-cache")
CYCLES = list(range(2001, 2024, 2))

REQUIRED = ["METALS_RECOVERY", "SOLVENTS_RECOVERY", "ENERGY_RECOVERY", "OTHER_RECOVERY",
            "FUEL_BLENDING", "INCINERATION", "LANDFILL", "DEEPWELL", "WASTEWATER_TREATMENT",
            "SLUDGE_TREATMENT", "LAND_TREATMENT", "OTHER_TREATMENT"]
RECOVERY = {"METALS RECOVERY", "SOLVENTS RECOVERY", "ENERGY RECOVERY", "OTHER RECOVERY"}
DISPOSAL = {"LANDFILL", "INCINERATION", "DEEPWELL"}


def num(v):
    return float(v) if v not in ("", "None", None) else 0.0


def have():
    """{category: set of cycles present}"""
    out = {}
    for p in glob.glob(os.path.join(CACHE, "*.csv.gz")):
        base = os.path.basename(p)[:-len(".csv.gz")]
        cat, _, cyc = base.rpartition("-")
        if cat and cyc.isdigit():
            out.setdefault(cat, set()).add(int(cyc))
    return out


def missing(basket=None, cycles=None):
    basket = basket or REQUIRED
    cycles = cycles or CYCLES
    h = have()
    return [(c, y) for c in basket for y in cycles if y not in h.get(c, set())]


def load(cycle, basket=None, strict=True):
    """Every row of one cycle, from exactly the named categories.

    Raises rather than returning a short answer when a slice is absent, because a missing
    slice reads as a smaller industry and nothing in the output would say otherwise."""
    basket = basket or REQUIRED
    gaps = [c for c in basket
            if not os.path.exists(os.path.join(CACHE, f"{c}-{cycle}.csv.gz"))]
    if gaps and strict:
        raise SystemExit(f"  cycle {cycle} is missing {len(gaps)} slice(s): "
                         f"{', '.join(sorted(gaps))}\n  run fetch.py --all first")
    rows = []
    for c in basket:
        p = os.path.join(CACHE, f"{c}-{cycle}.csv.gz")
        if not os.path.exists(p):
            continue
        with gzip.open(p, "rt", encoding="utf-8", newline="") as f:
            rows.extend(list(csv.DictReader(f)))
    return rows


def main():
    h = have()
    print(f"  cache: {CACHE}")
    print(f"  {sum(len(v) for v in h.values())} slices across {len(h)} categories\n")
    print(f"  {'category':<24}{'cycles':>8}  missing")
    for c in REQUIRED:
        got = sorted(h.get(c, set()))
        miss = [y for y in CYCLES if y not in got]
        print(f"  {c:<24}{len(got):>8}  {', '.join(map(str, miss)) if miss else '—'}")
    m = missing()
    print(f"\n  {len(m)} slice(s) missing of {len(REQUIRED)*len(CYCLES)}."
          f"{'  Complete.' if not m else '  Analyses are NOT yet reproducible.'}")
    return 0 if not m else 1


if __name__ == "__main__":
    sys.exit(main())
