"""Capture the FDA GRAS Notice Inventory.

One GET, no auth. FDA serves the whole inventory as CSV from a ColdFusion
export behind the CFSAN app; the content type says Excel and lies.

The inventory is *not* perishable — FDA retains withdrawn and rejected notices
with an explicit status back to 1998 — so this is a larder ingredient, not a
wss capture. We keep a dated copy anyway, because a re-derive should never
depend on the publisher still being up.
"""
import hashlib, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
# Written for an earlier layout and left resolving two levels too shallow when
# the scripts moved under the recipe, so every path pointed at nothing. Anchor
# on the recipe, then walk up to the larder root.
RECIPE = os.path.dirname(os.path.dirname(HERE))
CHARTS = os.path.join(RECIPE, "artifacts", "charts")
DEST = RAW
SOURCES = {
    # human food: a bulk CSV export (content type claims Excel and lies)
    "gras-notices": ("https://www.cfsanappsexternal.fda.gov/scripts/fdcc/cfc/"
                     "XMLService.cfm?method=downloadxls&set=GRASNotices"),
    # animal food: no export, so the rendered inventory table itself
    "agras-notices": ("https://www.fda.gov/animal-veterinary/"
                      "generally-recognized-safe-gras-notification-program/"
                      "current-animal-food-gras-notices-inventory"),
    # everything FDA permits in food, each row tagged with the 21 CFR section
    # that allows it. This is what a withdrawn substance is checked against to
    # see whether it took another door. Same download endpoint, different set.
    "food-substances": ("https://www.hfpappexternal.fda.gov/scripts/fdcc/cfc/"
                        "XMLService.cfm?method=downloadxls&set=FoodSubstances"),
}
UA = "q3dresearch-cookbook/1.0 (+https://github.com/q3dresearch/cookbook; research use)"


MIN_BYTES = {"gras-notices": 100_000, "agras-notices": 10_000,
             "food-substances": 500_000}
EXT = {"gras-notices": "csv", "agras-notices": "html",
       "food-substances": "csv"}


def grab(name, url, day):
    path = os.path.join(DEST, f"{name}-{day}.{EXT[name]}")
    if os.path.exists(path):
        print(f"  already captured today: {os.path.basename(path)}")
        return None
    p = subprocess.run(["curl", "-sS", "-L", "--compressed", "--max-time", "180",
                        "-A", UA, url], capture_output=True)
    if p.returncode != 0 or len(p.stdout) < MIN_BYTES[name]:
        print(f"  FAILED {name}: rc={p.returncode} bytes={len(p.stdout)}",
              file=sys.stderr)
        return "fail"
    with open(path, "wb") as f:
        f.write(p.stdout)
    sha = hashlib.sha256(p.stdout).hexdigest()
    man = os.path.join(DEST, "manifest.csv")
    new = not os.path.exists(man)
    with open(man, "a", encoding="utf-8") as f:
        if new:
            f.write("file,url,bytes,sha256,fetched_at\n")
        f.write(f"{os.path.basename(path)},{url},{len(p.stdout)},{sha},"
                f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
    print(f"  {name}: {len(p.stdout):,} bytes, sha256 {sha[:16]}…")
    return None


def main():
    os.makedirs(DEST, exist_ok=True)
    day = time.strftime("%Y-%m-%d")
    bad = [grab(n, u, day) for n, u in SOURCES.items()]
    return 1 if "fail" in bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
