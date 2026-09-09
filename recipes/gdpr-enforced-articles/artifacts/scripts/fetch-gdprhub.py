#!/usr/bin/env python3
"""Fetch every GDPR decision page from GDPRhub and parse its template.

    python fetch-gdprhub.py --out gdprhub.jsonl [--workers 3] [--limit N]

GDPRhub is noyb's wiki of European data-protection decisions. Every decision
page carries a `DPAdecisionBOX` template with ~46 named fields — jurisdiction,
outcome, decision date, the fine, and up to twenty cited GDPR articles — so the
useful content is structured and needs no text mining.

Writes JSONL and resumes: an interrupted run picks up from the titles already in
the output file. A full sweep is roughly 170 batches, so resuming matters more
than speed.

Politeness, since this is a small charity's wiki and not an API product:
identified user agent, a delay between batches, modest concurrency, and it stops
on the first non-200 rather than hammering. robots.txt was `Allow: /` when this
was written; check it still is.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

API = "https://gdprhub.eu/api.php"
UA = "q3dresearch-cookbook/1.0 (+https://github.com/q3dresearch/cookbook)"
BATCH = 40                      # MediaWiki caps untrusted clients at 50 titles
_lock = threading.Lock()


def get(params: dict) -> dict:
    params = {**params, "format": "json"}
    url = f"{API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                if r.status != 200:
                    raise OSError(f"HTTP {r.status}")
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:                       # noqa: BLE001 — reported, not hidden
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
            print(f"    retry {attempt+1}: {e}", file=sys.stderr)
    raise AssertionError("unreachable")


def all_titles(cache: str | None = None) -> list[str]:
    """Every page in the main namespace, which on this wiki is the decisions.

    Cached to disk: enumeration is fourteen slow requests before any useful work
    happens, and a resumed run should not repeat them.
    """
    if cache:
        try:
            with open(cache, encoding="utf-8") as fh:
                titles = json.load(fh)
            print(f"  {len(titles):,} titles from cache", file=sys.stderr, flush=True)
            return titles
        except FileNotFoundError:
            pass
    out, cont = [], {}
    while True:
        d = get({"action": "query", "list": "allpages", "aplimit": "500",
                 "apnamespace": "0", **cont})
        out += [p["title"] for p in d["query"]["allpages"]]
        print(f"  enumerated {len(out):,}", file=sys.stderr, flush=True)
        if "continue" not in d:
            if cache:
                with open(cache, "w", encoding="utf-8") as fh:
                    json.dump(out, fh)
            return out
        cont = d["continue"]


def parse_box(text: str) -> dict | None:
    """Pull the named fields out of the DPAdecisionBOX template.

    Split on newline-pipe rather than any pipe: field values contain pipes
    inside wiki links, and splitting on all of them truncates the value.
    """
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)   # comments sit between fields
    i = text.find("{{DPAdecisionBOX")
    if i < 0:
        return None
    body = text[i:]
    depth, end = 0, len(body)
    for j, ch in enumerate(body):
        if body[j:j + 2] == "{{":
            depth += 1
        elif body[j:j + 2] == "}}":
            depth -= 1
            if depth == 0:
                end = j
                break
    fields = {}
    for part in re.split(r"\n\s*\|", body[:end]):
        if "=" not in part:
            continue
        k, _, v = part.partition("=")
        k = k.strip()
        if k and not k.startswith("{{"):
            fields[k] = v.strip()
    return fields or None


# Presentation-only template fields. Dropping them keeps the corpus readable;
# they carry no information about the decision.
CHROME = {"DPA-BG-Color", "DPAlogo", "DPA_With_Country", "Initial_Contributor"}


def record(title: str, text: str) -> dict | None:
    """One decision: the convenience fields the scripts use, plus the raw template.

    `fields` keeps every named parameter verbatim. An earlier version kept only
    the eleven that the first question needed, and the second question — how long
    a case takes — wanted Date_Started, which meant fetching the whole wiki again.
    Storage is cheap and this API is slow, so keep everything and decide later.
    """
    f = parse_box(text)
    if f is None:
        return None
    fields = {k: v for k, v in f.items() if k not in CHROME and v}
    arts = [f[k] for k in sorted(f, key=lambda x: (len(x), x))
            if re.fullmatch(r"GDPR_Article_\d+", k) and f[k]]
    parties = [f[k] for k in sorted(f) if re.fullmatch(r"Party_Name_\d+", k) and f[k]]

    # The prose after the template opens with a one-line summary. Worth keeping
    # bounded: fine reductions ("paid a reduced fine of EUR 1,200,000") appear
    # only there, never in the Fine field.
    tail = text.split("}}", 1)[-1].strip() if "}}" in text else ""
    summary = " ".join(tail.split())[:600]

    return {
        "title": title,
        "juris": f.get("Jurisdiction", ""),
        "dpa": f.get("DPA_Abbrevation", ""),
        "year": f.get("Year", ""),
        "date_started": f.get("Date_Started", ""),
        "date_decided": f.get("Date_Decided", ""),
        "date_published": f.get("Date_Published", ""),
        "type": f.get("Type", ""),
        "outcome": f.get("Outcome", ""),
        "fine": f.get("Fine", ""),
        "currency": f.get("Currency", ""),
        "party": parties[0] if parties else "",
        "parties": parties,
        "appeal_to_status": f.get("Appeal_To_Status", ""),
        "appeal_to_body": f.get("Appeal_To_Body", ""),
        "appeal_from_body": f.get("Appeal_From_Body", ""),
        "national_laws": [f[k] for k in sorted(f)
                          if re.fullmatch(r"National_Law_Name_\d+", k) and f[k]],
        "articles": arts,
        "summary": summary,
        "fields": fields,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    done = set()
    try:
        with open(a.out, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    done.add(json.loads(line)["title"])
        print(f"  resuming: {len(done):,} already fetched", file=sys.stderr)
    except FileNotFoundError:
        pass

    titles = [t for t in all_titles(a.out + ".titles.json") if t not in done]
    if a.limit:
        titles = titles[:a.limit]
    print(f"  {len(titles):,} to fetch, {len(done):,} cached", file=sys.stderr, flush=True)
    batches = [titles[i:i + BATCH] for i in range(0, len(titles), BATCH)]
    n_ok = n_skip = 0
    t0 = time.time()

    def do(bi_batch):
        nonlocal n_ok, n_skip
        bi, batch = bi_batch
        time.sleep(a.delay * (bi % a.workers))
        d = get({"action": "query", "prop": "revisions", "rvprop": "content",
                 "rvslots": "main", "titles": "|".join(batch)})
        rows = []
        for p in d.get("query", {}).get("pages", {}).values():
            try:
                text = p["revisions"][0]["slots"]["main"]["*"]
            except (KeyError, IndexError):
                continue
            r = record(p["title"], text)
            if r:
                rows.append(r)
        with _lock:
            n_ok += len(rows)
            n_skip += len(batch) - len(rows)
            with open(a.out, "a", encoding="utf-8") as fh:
                for r in rows:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            el = time.time() - t0
            pct = (bi + 1) / len(batches)
            print(f"  batch {bi+1}/{len(batches)}  {n_ok:,} decisions  "
                  f"{n_skip:,} non-decision pages  eta {el/pct-el:>5.0f}s",
                  file=sys.stderr, flush=True)

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(do, enumerate(batches)))
    print(f"\n  {n_ok:,} decisions written to {a.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
