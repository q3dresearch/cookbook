"""List annotation candidates: the oldest and the most-churned sections."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
RECIPE = os.path.dirname(os.path.dirname(HERE))          # recipes/cfr-staleness
CHARTS = os.path.join(RECIPE, "artifacts", "charts")
# This recipe commits no data. capture.py writes into a work directory and every
# other script reads from the same one: set CFR_WORK, or accept ./work in the
# current directory. Nothing here reaches outside the recipe except that dir.
WORK = os.environ.get("CFR_WORK") or os.path.join(os.getcwd(), "work")
DERIVED = os.path.join(WORK, "derived")
RAW = os.path.join(WORK, "raw")
os.makedirs(DERIVED, exist_ok=True)
import sys
sys.path.insert(0, HERE)
import cfrlib
rows, live = cfrlib.load()
print("=== OLDEST 20 (by last amendment) ===")
for r in sorted(live, key=lambda r: r["d"][-1])[:20]:
    print(f"{r['d'][-1]}  {r['age']:5.1f}y  {r['agency'][:22]:22s} "
          f"{r['section']:<11s} {r['heading'][:64]}")
print("\n=== MOST AMENDED 20 ===")
for r in sorted(live, key=lambda r: -r["n_amend"])[:20]:
    print(f"n={r['n_amend']:3d}  {r['d'][0].year}-{r['d'][-1].year}  "
          f"{r['agency'][:20]:20s} {r['section']:<11s} {r['heading'][:60]}")
print("\n=== OLDEST, by agency ===")
seen = {}
for r in sorted(live, key=lambda r: r["d"][-1]):
    if r["agency"] not in seen:
        seen[r["agency"]] = r
for a, r in sorted(seen.items(), key=lambda kv: kv[1]["d"][-1]):
    print(f"{r['d'][-1]}  {a[:26]:26s} {r['section']:<11s} {r['heading'][:56]}")
