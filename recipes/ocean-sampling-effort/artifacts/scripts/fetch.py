#!/usr/bin/env python3
"""Retrieve everything the fourteen figures need, and print the drift against provenance.json.

    python3 fetch.py

Standard library only, no key, nothing to install. Each step writes its files into
`artifacts/data/` and skips them if present, so a rerun is cheap and a partial run resumes.
**Budget an hour and 155 MB on a cold cache.** Three steps dominate: `redlist.py` makes about
3,200 per-species calls, `criterionb.py` about 700 grid pulls, and `redlisthistory.py`
downloads the nine IUCN Red List archives GBIF still mirrors.

That last one is a **capture, not a question** — bytes that perish, which belong in a capture
repo rather than a recipe. It is here so this folder reproduces standalone. The mirror **drops
transfers** at arbitrary points and succeeds seconds later, so every download is checked
against Content-Length and opened with `zipfile` before it reaches the cache.

**Expect the numbers to drift, and read the drift rather than ignoring it.** OBIS is live and
additive — the record count moved by 62,000 between two probes minutes apart while this was
being written — so a later fetch will not reproduce the published figures exactly. That is why
`provenance.json` records the SHA-256 and size of each file the published figures were computed
from, and why this script prints the comparison instead of quietly overwriting. A changed hash
with a similar size is the source moving; a changed hash with a very different size is worth
looking at before trusting anything downstream.
"""
import hashlib, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
PROV = os.path.join(HERE, "..", "..", "provenance.json")

# order matters only in that obis.py writes the base summaries the rest assume exist
STEPS = [
    ("obis.py", ["grid3.json", "statistics.json", "composition.json", "env.json"],
     "base grid, register totals, composition, depth/SST bins"),
    ("depth_of_map.py", ["map-depth.json"], "110 sampled cells, datasets per cell"),
    ("units.py", ["units-sample.json"], "organismQuantityType across twelve taxa"),
    ("classes.py", ["classes.json"], "depth and SST per animal class"),
    ("producers.py", ["producers.json"], "the same for plants, algae and single cells"),
    ("cliffs.py", ["cliffs.json"], "composition by depth bin, capture per band"),
    ("flags.py", ["flags.json"], "the register's own error flags, per class"),
    ("saturation.py", ["saturation.json"], "species accumulation per class, with a holdout"),
    ("described.py", ["described.json"], "taxonomic authorship years, paged with skip"),
    ("redlist.py", ["redlist.json"], "IUCN threat join + matched control (~15 min)"),
    ("criterionb.py", ["criterionb.json"], "lower-bound area of occupancy (~700 grid pulls)"),
    ("attention.py", ["attention.json"], "records vs datasets, declared FAO control lists"),
    ("redlisthistory.py", ["redlisthistory.json"], "nine IUCN archives from GBIF (~155 MB)"),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    os.makedirs(DATA, exist_ok=True)
    for script, outs, what in STEPS:
        if all(os.path.exists(os.path.join(DATA, o)) for o in outs):
            print(f"  {script:<18}cached      {what}")
            continue
        print(f"  {script:<18}fetching…   {what}", flush=True)
        r = subprocess.run([sys.executable, os.path.join(HERE, script)],
                           capture_output=True, text=True)
        if r.returncode:
            print(r.stdout[-2000:] + r.stderr[-2000:])
            raise SystemExit(f"  {script} failed")

    if not os.path.exists(PROV):
        print("\n  no provenance.json to compare against")
        return 0
    prov = json.load(open(PROV)).get("files", {})
    print(f"\n  drift against provenance.json ({json.load(open(PROV)).get('retrieved')})")
    moved = 0
    for name, rec in sorted(prov.items()):
        p = os.path.join(DATA, name)
        if not os.path.exists(p):
            print(f"    {name:<20}MISSING"); moved += 1; continue
        h, n = sha(p), os.path.getsize(p)
        if h == rec["sha256"]:
            print(f"    {name:<20}identical")
        else:
            d = (n - rec["bytes"]) / max(rec["bytes"], 1)
            print(f"    {name:<20}CHANGED   {rec['bytes']:>12,} -> {n:>12,} bytes  {d:+.1%}")
            moved += 1
    print(f"\n  {moved} of {len(prov)} files have moved. The published figures were computed "
          f"from the recorded ones;\n  a rerun will differ and that is the source, not a bug.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
