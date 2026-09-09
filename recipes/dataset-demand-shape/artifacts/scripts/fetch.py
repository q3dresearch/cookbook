#!/usr/bin/env python3
"""Fetch the Meta Kaggle tables this recipe reads. No credentials needed.

    python fetch.py

Kaggle serves its own index of itself anonymously; each request redirects to a
signed storage URL. The file-listing endpoint 404s, so the filenames below are
known rather than discovered.

WHY NO DATA IS COMMITTED. A fork should be cheap: this recipe is scripts,
figures and prose, a few hundred kilobytes against ~1.5 GB of corpora. The cost
is that Meta Kaggle updates daily, so what you fetch will not be byte-identical
to what the published figures were computed from. That is what provenance.json
records — run this, compare, and the drift is visible rather than silently
producing different numbers from a different world.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
DATA = RECIPE / "artifacts" / "data"
UA = "q3dresearch cookbook (+https://github.com/q3dresearch/cookbook)"
BASE = "https://www.kaggle.com/api/v1/datasets/download/kaggle/meta-kaggle?file_name={f}"
TABLES = ["Datasets.csv", "DatasetVersions.csv", "Tags.csv", "DatasetTags.csv"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch() -> list[Path]:
    DATA.mkdir(exist_ok=True)
    out = []
    for name in TABLES:
        p = DATA / name
        if not p.exists():
            print(f"  fetching {name} …")
            req = urllib.request.Request(BASE.format(f=name), headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=1800) as r, p.open("wb") as fh:
                while chunk := r.read(1 << 20):
                    fh.write(chunk)
        out.append(p)
    return out


def main() -> int:
    files = fetch()
    mine = {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in files}
    (RECIPE / "provenance.local.json").write_text(
        json.dumps({"retrieved": time.strftime("%Y-%m-%d"), "tables": mine}, indent=2))

    pub = json.loads((RECIPE / "provenance.json").read_text())
    print(f"\n  published {pub['retrieved']} versus what you just fetched:")
    for name, cur in mine.items():
        was = pub["tables"].get(name, {})
        same = was.get("sha256") == cur["sha256"]
        delta = cur["bytes"] - was.get("bytes", cur["bytes"])
        print(f"    {name:<22} {'identical' if same else 'drifted'}"
              f"   {cur['bytes']/1e6:>8.1f} MB   {delta/1e6:+.1f} MB")
    if any(pub['tables'].get(k, {}).get('sha256') != v['sha256'] for k, v in mine.items()):
        print("\n  Drift is expected — Meta Kaggle updates daily. Your numbers will differ")
        print("  from the published figures, and now you know by how much.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
