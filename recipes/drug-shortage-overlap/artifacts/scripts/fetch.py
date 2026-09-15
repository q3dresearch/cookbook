#!/usr/bin/env python3
"""Locate the capture this recipe reads, check it against provenance, and enrich.

    python fetch.py

WHY THIS ONE CANNOT JUST DOWNLOAD ITS CORPUS. The other recipes here fetch a
source that keeps its own history, so a fork gets the same bytes tomorrow. These
three do not. The FDA, ANSM and TGA shortage registers each publish only what is
short *right now*: a shortage that resolves leaves the page and no archive link
replaces it. Re-fetching them today gives you a different world, not a
reproduction -- which is why the capture is a separate repo (`wss-drug-scarcity`)
and why this script verifies rather than downloads.

So it does three things:

1. Finds the archive -- $WSS_DRUG_SCARCITY, or artifacts/data/wss-drug-scarcity, cloning
   https://github.com/q3dresearch/wss-drug-scarcity into the latter if neither exists.
2. Hashes the capture files the published figures were computed from -- every file of
   the newest run, which for the FDA feed is TWO pages; hashing only the newest file is
   how half a register was once published as the whole -- and
   compares them to provenance.json. **Drift here is a different capture date,
   not a changed file**: these are append-only, so a mismatch means you are
   pointed at another snapshot and every number below will differ.
3. Re-fetches the enrichment. RxNav is a stable NLM vocabulary with no key and
   its own history, so this part IS reproducible, and it is the slow part
   (~35 minutes for 658 names). It is skipped if the cache is already complete.

If you have no archive at all, the scripts still run against whatever capture
you point them at; they will simply describe that day instead of 2026-09-10.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
PROV = json.loads((RECIPE / "provenance.json").read_text())


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def archive() -> Path | None:
    env = os.environ.get("WSS_DRUG_SCARCITY")
    for c in ([Path(env)] if env else []) + [RECIPE / "artifacts" / "data" / "wss-drug-scarcity"]:
        if (c / "raw").is_dir():
            return c
    return None


def main() -> int:
    a = archive()
    if a is None:
        clone = RECIPE / "artifacts" / "data" / "wss-drug-scarcity"
        print(f"  no archive found; cloning the public one into {clone.relative_to(RECIPE)}")
        clone.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["git", "clone", "--depth", "1",
                            "https://github.com/q3dresearch/wss-drug-scarcity", str(clone)])
        a = archive() if r.returncode == 0 else None
        if a is None:
            print("  clone failed. Clone it by hand and set $WSS_DRUG_SCARCITY.")
            return 1
    print(f"  archive: {a}")

    want = PROV["sources"]["wss-drug-scarcity"]["files"]
    drift = 0
    for rel, exp in want.items():
        p = a / rel
        if not p.exists():
            print(f"  MISSING  {rel}")
            drift += 1
            continue
        got = {"bytes": p.stat().st_size, "sha256": sha256(p)}
        if got == exp:
            print(f"  ok       {rel}  ({got['bytes']} bytes)")
        else:
            drift += 1
            print(f"  DRIFT    {rel}")
            print(f"           published {exp['bytes']}b {exp['sha256'][:16]}")
            print(f"           yours     {got['bytes']}b {got['sha256'][:16]}")
    if drift:
        print(f"\n  {drift} of {len(want)} capture files differ from what the figures came from.")
        print("  These files are append-only, so this is a different capture date, not a")
        print("  changed file. Every number below will differ, visibly, which is the point.")

    cache = RECIPE / "artifacts" / "data" / "rxnorm.json"
    if cache.exists():
        c = json.loads(cache.read_text())
        # Only the names the CURRENT registers ask for matter; the cache also holds
        # names from earlier captures. verify.py applies the same test, and the two
        # must agree or one of them is crying wolf.
        sys.path.insert(0, str(Path(__file__).parent))
        import shortagelib as _S
        from rxnorm import clean as _clean
        used = {_clean(n) for d in _S.registers().values() for n, _ in d["rows"]}
        res = [q for q in used if c.get(q, {}).get("rxcui")]
        part = sum(1 for q in res if "all" not in c[q])
        if part:
            print(f"\n  rxnorm cache is incomplete: {part} of {len(res)} entries predate the")
            print("  ingredient-set key. Run rxnorm.py to completion; verify.py refuses until then.")
        else:
            print(f"\n  rxnorm cache complete: {len(res)} names carry an ingredient set.")
    else:
        print("\n  no rxnorm cache — running rxnorm.py (~35 minutes, resumable, no key needed)")
        subprocess.run([sys.executable, "rxnorm.py"], cwd=str(Path(__file__).parent))

    here = Path(__file__).parent
    for script in ("memory.py", "revisions.py"):
        print(f"\n  -- {script}")
        subprocess.run([sys.executable, str(here / script)], cwd=str(here))
    print("\n  next: python verify.py   (re-derives every published number)")
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
