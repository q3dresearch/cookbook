"""Capture raw eCFR part XML to disk. Resumable: an existing file is never refetched.

Scouting rule: keep the bytes, decide what we want from them later.
Raw payloads are stored gzipped (lossless, so still verbatim) alongside a
manifest row per fetch recording URL, sha256, byte count and fetch time.
"""
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
import csv, gzip, hashlib, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

TITLE = sys.argv[1]
DATE = sys.argv[2] if len(sys.argv) > 2 else "2026-09-01"
ROOT = RAW
DEST = f"{ROOT}/ecfr/title-{TITLE}/{DATE}"
MAN = f"{DEST}/manifest.csv"
os.makedirs(DEST, exist_ok=True)


def fetch(url, tries=4):
    for a in range(tries):
        p = subprocess.run(["curl", "-sS", "--compressed", "--max-time", "120",
                            "-w", "\n%{http_code}", url],
                           capture_output=True, text=True)
        body, _, code = p.stdout.rpartition("\n")
        if code.strip() == "200":
            return body
        time.sleep(2 * (a + 1))
    return None


def save(name, url, body):
    path = f"{DEST}/{name}.gz"
    raw = body.encode()
    with gzip.open(path, "wb") as f:
        f.write(raw)
    return {"name": name, "url": url, "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


rows = []
sp = f"{DEST}/structure.json.gz"
if not os.path.exists(sp):
    u = f"https://www.ecfr.gov/api/versioner/v1/structure/{DATE}/title-{TITLE}.json"
    rows.append(save("structure.json", u, fetch(u)))
struct = json.loads(gzip.open(sp, "rt").read())


def walk(n):
    yield n
    for c in n.get("children") or []:
        yield from walk(c)


import re
parts = sorted({n["identifier"] for n in walk(struct) if n.get("type") == "part"},
               key=lambda s: [int(x) if x.isdigit() else x
                              for x in re.split(r"(\d+)", s) if x])
todo = [p for p in parts if not os.path.exists(f"{DEST}/part-{p}.xml.gz")]
print(f"title {TITLE}: {len(parts)} parts, {len(todo)} to fetch, "
      f"{len(parts)-len(todo)} already on disk", flush=True)

done = [0]


def grab(part):
    u = (f"https://www.ecfr.gov/api/versioner/v1/full/{DATE}/"
         f"title-{TITLE}.xml?part={part}")
    b = fetch(u)
    if b is None:
        print(f"  FAIL part {part}", flush=True)
        return None
    r = save(f"part-{part}.xml", u, b)
    done[0] += 1
    if done[0] % 25 == 0:
        print(f"  {done[0]}/{len(todo)}", flush=True)
    time.sleep(0.15)
    return r


with ThreadPoolExecutor(max_workers=4) as ex:
    rows += [r for r in ex.map(grab, todo) if r]

new = not os.path.exists(MAN)
with open(MAN, "a", newline="") as f:
    w = csv.DictWriter(f, ["name", "url", "bytes", "sha256", "fetched_at"])
    if new:
        w.writeheader()
    w.writerows(rows)
tot = sum(os.path.getsize(f"{DEST}/{x}") for x in os.listdir(DEST))
print(f"captured {len(rows)} payloads; store now {tot/1e6:.1f} MB at {DEST}", flush=True)
