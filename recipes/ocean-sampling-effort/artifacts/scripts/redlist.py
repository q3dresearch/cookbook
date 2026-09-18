#!/usr/bin/env python3
"""Can this register serve as a monitoring instrument for threatened marine species?

    python3 redlist.py         # fetch and cache (a few minutes, ~2,400 calls)

Everything in figures 1-8 is descriptive: where things were recorded and what that says about
the recording. `checklist/redlist` is the one join in the API that carries an outside judgement
-- the IUCN threat category -- and turns the register on a named decision. For each threatened
species this pulls total records, records in the last decade, and the last year it was seen.

**What this is NOT.** It is not an audit of IUCN. Assessments draw on literature, targeted
survey and expert judgement, almost none of which is in OBIS. A Critically Endangered species
with two OBIS records is not an assessment resting on two observations. The question here runs
the other way: *given* that someone has decided a species is threatened, can this register tell
you how it is doing? For a large share the answer is no, and that is a statement about the
instrument, not about the assessment.

**A field that cannot be read the obvious way.** OBIS stamps `category` only for CR, EN, VU and
EX. Least Concern, Near Threatened and Data Deficient all come back `None`, as does a species
IUCN has never looked at: humpback whale, harbour porpoise and blue shark are all `None` here
and all three are assessed. So `category is None` CANNOT be read as "unassessed", and the
"heavily observed but never assessed" list that suggests itself is not obtainable from it.

**Transitions are not in this file, and cannot be.** A redlist row carries no assessment date,
no Red List version and no previous category -- the endpoint returns a *current state* and
nothing else. Species entering or leaving threatened status is therefore unanswerable from OBIS
today, and no amount of work on this data changes that. What does change it is capture: every
run writes `redlist-categories-<date>.json.gz`, a dated {name: category} mapping, so that a run
next year is a diff rather than another snapshot of now. The first one is worth nothing and the
second is worth the whole question.

**The control is record count, not species count.** A species with six records will have few
recent ones whatever its status, so a raw comparison of threatened against everything else
measures rarity. Non-threatened species are therefore sampled from the same families and
matched on log10(total records), and the comparison is made inside those strata.
"""
import datetime, gzip, json, math, os, random, shutil, sys, time
import urllib.parse, urllib.request
import concurrent.futures as cf
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("OBIS_DATA") or os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "redlist.json")
UA = "web-snapshots research bot (dl.eeee.nv@gmail.com)"
RECENT = 2016                      # "the last decade", against a 2026 fetch
SEED = 20260918                    # sampling must be reproducible; see determinism.py


def g(path, params=None):
    u = f"https://api.obis.org/v3/{path}" + (
        "?" + urllib.parse.urlencode(params) if params else "")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(u, headers={"User-Agent": UA}), timeout=300) as r:
                return json.load(r)
        except Exception:                                                # noqa: BLE001
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))


def years(sp):
    """Total, last-decade and last-seen for one species. Records with no date are invisible
    to statistics/years, so `dated` is reported separately from the checklist's own count."""
    try:
        y = g("statistics/years", {"scientificname": sp}) or []
    except Exception:                                                    # noqa: BLE001
        return None
    # statistics/years normally returns a list of {year, records}. For some names it returns
    # a dict instead -- an error envelope, not a histogram -- and iterating that yields the
    # keys as strings. Fail the species rather than the run.
    if not isinstance(y, list) or any(not isinstance(r, dict) for r in y):
        return None
    dated = sum(r.get("records", 0) for r in y)
    seen = [r["year"] for r in y if r.get("records")]
    return {"dated": dated, "recent": sum(r["records"] for r in y if r["year"] >= RECENT),
            "last": max(seen) if seen else None}


def load():
    if not os.path.exists(OUT):
        raise SystemExit("  redlist.json not cached -- run redlist.py first")
    return json.load(open(OUT))


def snapshot_categories(rows):
    """The diffable object: species -> category, dated, one file per day. Small on purpose,
    because what matters later is which names moved, not how many records they had."""
    d = os.path.join(DATA, "snapshots")
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, f"redlist-categories-{datetime.date.today().isoformat()}.json.gz")
    if os.path.exists(out):
        return out, False
    body = {"fetched": datetime.date.today().isoformat(),
            "note": "OBIS stamps only CR/EN/VU/EX; LC, NT, DD and unassessed are all absent",
            "categories": {x["name"]: x["category"] for x in sorted(rows, key=lambda r: r["name"])}}
    with gzip.open(out, "wt") as gz:
        json.dump(body, gz, indent=1)
    return out, True


def main():
    if os.path.exists(OUT):
        d = load()
        print(f"  cached: {len(d['threatened'])} threatened, {len(d['control'])} control")
        p, fresh = snapshot_categories(d["threatened"])
        print(f"  {'wrote' if fresh else 'already have'} {os.path.basename(p)}")
        prior = sorted(f for f in os.listdir(os.path.join(DATA, "snapshots"))
                       if f.startswith("redlist-categories-"))
        if len(prior) > 1:
            a = json.load(gzip.open(os.path.join(DATA, "snapshots", prior[-2]), "rt"))["categories"]
            b = json.load(gzip.open(os.path.join(DATA, "snapshots", prior[-1]), "rt"))["categories"]
            moved = {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if a.get(k) != b.get(k)}
            print(f"  against {prior[-2]}: {len(moved)} species changed category")
            for k, (x, y) in sorted(moved.items())[:20]:
                print(f"      {k:<34}{x or 'not listed':<12} -> {y or 'delisted'}")
        else:
            print("  only one snapshot exists, so no transition can be computed yet")
        return 0
    red = g("checklist/redlist", {"size": 5000}).get("results") or []
    red = [x for x in red if x.get("scientificName")]
    print(f"  {len(red)} threatened species from checklist/redlist")

    fams = sorted({x.get("family") for x in red if x.get("family")})
    tnames = {x["scientificName"] for x in red}
    pool = defaultdict(list)                       # log10 bucket -> candidate control species
    for i, fam in enumerate(fams):
        try:
            full = g("checklist", {"scientificname": fam, "size": 3000}).get("results") or []
        except Exception:                                                # noqa: BLE001
            continue
        for x in full:
            n, nm = x.get("records") or 0, x.get("scientificName")
            if nm and nm not in tnames and not x.get("category") and n > 0:
                pool[int(math.log10(n))].append({"scientificName": nm, "family": fam,
                                                 "class": x.get("class"), "records": n})
        if i % 40 == 0:
            print(f"    families {i}/{len(fams)}")
    want = defaultdict(int)
    for x in red:
        want[int(math.log10(max(x.get("records") or 1, 1)))] += 1
    rng = random.Random(SEED)
    control = []
    for b, k in want.items():                      # match the threatened record distribution
        cand = pool.get(b, [])
        rng.shuffle(cand)
        control += cand[:k]
    print(f"  {len(control)} control species matched on log10(records) within family")

    def fetch(x):
        return x, years(x["scientificName"])
    out = {"threatened": [], "control": [], "recent_from": RECENT, "seed": SEED}
    for label, rows in (("threatened", red), ("control", control)):
        done = 0
        with cf.ThreadPoolExecutor(6) as ex:
            for x, y in ex.map(fetch, rows):
                done += 1
                if y is None:
                    continue
                out[label].append({"name": x["scientificName"], "class": x.get("class"),
                                   "family": x.get("family"),
                                   "category": x.get("category"),
                                   "records": x.get("records") or 0, **y})
                if done % 300 == 0:
                    print(f"    {label} {done}/{len(rows)}")
        print(f"  {label}: {len(out[label])} fetched")
    os.makedirs(DATA, exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=2)
    p, _ = snapshot_categories(out["threatened"])
    print(f"\n  written to {OUT}")
    print(f"  snapshot {os.path.basename(p)} — the object a future run diffs against")
    return 0


if __name__ == "__main__":
    sys.exit(main())
