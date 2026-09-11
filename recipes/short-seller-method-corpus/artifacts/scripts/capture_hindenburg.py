#!/usr/bin/env python3
"""Capture the Hindenburg Research archive from its WordPress REST API.

    python capture_hindenburg.py

105 posts, August 2017 to January 2025, full HTML body text. The firm wound down in
January 2025, so this archive is closed: no new posts, and nothing pruned. That is
what makes it worth reading as a corpus rather than a feed — there is no
survivorship in it, because the firm stopped rather than the archive being edited.

It is also why this script exists. The site is a private company's and can be
switched off at any time; nothing here is archived by anyone else. The capture is
written once and never refetched, the header total is checked against the rows
received, and a sha256 goes in the manifest so a later reader can tell whether they
are holding the same bytes these charts were computed from.

`per_page` is capped at 100 by WordPress, so this pages. `_fields` is passed to keep
the payload to what the analysis reads — the full response carries rendering
metadata that triples the size.
"""
import json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "raw" / "hindenburg"
UA = "q3dresearch-cookbook/1.0 (+https://github.com/q3dresearch/cookbook; research use)"
BASE = "https://hindenburgresearch.com/wp-json/wp/v2/posts"
FIELDS = "id,date,slug,link,title,content"


def curl(url, want_headers=False):
    cmd = ["curl", "-sS", "-L", "--compressed", "--max-time", "60", "-A", UA]
    if want_headers:
        cmd += ["-D", "-", "-o", "/dev/null"]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, timeout=90)
    if r.returncode != 0:
        raise RuntimeError(f"curl {r.returncode}: {r.stderr.decode()[:120]}")
    return r.stdout.decode("utf-8", "replace")


def expected_total():
    """WordPress reports the archive size in a header. Worth asking first: if the
    rows received do not match it, the capture is short and must not be used."""
    h = curl(f"{BASE}?per_page=1", want_headers=True)
    for line in h.splitlines():
        if line.lower().startswith("x-wp-total:"):
            return int(line.split(":", 1)[1].strip())
    return None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d")
    dest = OUT / f"hindenburg-corpus-{stamp}.json"
    existing = sorted(OUT.glob("hindenburg-corpus-*.json"))
    if existing and not dest.exists():
        print(f"  already captured: {existing[-1].name}")
        print("  capture is the irreversible step — delete the file to refetch deliberately.")
        return

    total = expected_total()
    print(f"  archive reports {total} posts")
    posts, page = [], 1
    while True:
        body = curl(f"{BASE}?per_page=100&page={page}&_fields={FIELDS}&orderby=date&order=asc")
        try:
            batch = json.loads(body)
        except json.JSONDecodeError:
            raise RuntimeError(f"page {page} was not JSON: {body[:120]}")
        if isinstance(batch, dict) and batch.get("code"):
            break                                     # rest_post_invalid_page_number
        if not batch:
            break
        posts += batch
        print(f"    page {page}: {len(batch)} posts (running {len(posts)})", flush=True)
        page += 1
        time.sleep(1.0)

    if total is not None and len(posts) != total:
        raise RuntimeError(f"got {len(posts)} posts, header said {total} — refusing to write a short capture")
    empty = [p["slug"] for p in posts if not p.get("content", {}).get("rendered")]
    if empty:
        raise RuntimeError(f"{len(empty)} posts came back with no body: {empty[:4]}")

    dest.write_text(json.dumps(posts, indent=1))
    words = sum(len(p["content"]["rendered"].split()) for p in posts)
    print(f"  {len(posts)} posts, ~{words:,} words -> {dest.relative_to(HERE.parents[1])}")


if __name__ == "__main__":
    main()
