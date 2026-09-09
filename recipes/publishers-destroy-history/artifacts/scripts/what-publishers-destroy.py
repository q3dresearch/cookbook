#!/usr/bin/env python3
"""What do these publishers actually destroy, measured rather than asserted?

    python tools/what-publishers-destroy.py

Every wss repo's description claims its publisher discards history. This reads
the manifests and checks. It counts SHRINK EVENTS — captures where a source
returned fewer bytes than the time before — because growth is ambiguous and
shrinkage is not. A source that grows may simply be appending, in which case
the old state is still inside the new one and nothing was lost. A source that
shrinks has removed something that was there, and the only remaining copy is
the one in the archive.

That distinction is the whole method. "N sources changed" would be a much
larger and much weaker number.

Read with the csv module, never awk: manifest ETag and Last-Modified fields
carry commas inside quotes, so a naive split reports a date as the outcome.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

# Scans whatever archives are present under artifacts/data. The sibling script
# clones one; point this at more and it scans more. It was written against the
# full fleet of nine, and reports honestly on however many it finds.
ROOT = Path(__file__).resolve().parents[2] / "artifacts" / "data"
GOOD = {"first_capture", "unchanged", "changed"}


def rows_for(src_dir: Path) -> list[dict]:
    out: list[dict] = []
    for f in sorted(src_dir.glob("*.csv")):
        with f.open(newline="") as fh:
            out.extend(csv.DictReader(fh))
    return sorted(out, key=lambda r: r.get("fetched_at") or "")


def main() -> int:
    fleet: list[tuple] = []
    obs = shrinks = repos = 0

    for repo in sorted(ROOT.glob("wss-*")):
        if repo.name == "wss-engine" or not (repo / "manifest").is_dir():
            continue
        repos += 1
        for src_dir in sorted((repo / "manifest").iterdir()):
            if not src_dir.is_dir():
                continue
            # One endpoint's history at a time: a source with several endpoints
            # interleaves sizes that have nothing to do with each other, and
            # comparing across them invents shrinks that never happened.
            by_url: dict[str, list[dict]] = defaultdict(list)
            for r in rows_for(src_dir):
                if r.get("outcome") in GOOD and (r.get("content_length") or "").isdigit():
                    by_url[r["url"]].append(r)

            n = worst = 0
            worst_when = worst_from = worst_to = ""
            for url, series in by_url.items():
                obs += len(series)
                for prev, cur in zip(series, series[1:]):
                    a, b = int(prev["content_length"]), int(cur["content_length"])
                    if b >= a or a == 0:
                        continue
                    n += 1
                    pct = (a - b) / a * 100
                    if pct > worst:
                        worst, worst_when = pct, cur["fetched_at"][:10]
                        worst_from, worst_to = a, b
            shrinks += n
            if n:
                fleet.append((worst, n, repo.name, src_dir.name, worst_when, worst_from, worst_to))

    print(f"\n  {repos} archives · {obs:,} observations · {shrinks} shrink event(s)\n")
    if not fleet:
        print("  No source has yet returned fewer bytes than the time before.")
        print("  Either these publishers only append, or the window is still too short.")
        return 0

    fleet.sort(reverse=True)
    print(f"  {'repo':<20} {'source':<32} {'when':<11} {'shrank':>8} {'events':>7}")
    print("  " + "-" * 82)
    for worst, n, repo, src, when, a, b in fleet:
        print(f"  {repo:<20} {src[:32]:<32} {when:<11} {worst:>7.1f}% {n:>7}")
        print(f"  {'':<20} {'':<32} {'':<11} {a:>8,} → {b:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
