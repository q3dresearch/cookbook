#!/usr/bin/env python3
"""Reference lists taken from the papers themselves, not from an index of them.

    python bibliographies.py            # resumes; safe to re-run

The ancestry walk needs to know what each paper cites. Three third-party routes were
tried first and all three failed:

    OpenAlex        86% resolve, but only 24% carry references -- it parses
                    them for published work and `type=preprint` returns zero,
                    which is most recent AI. 21% walkable.
    Crossref        404 on arXiv DOIs, and ACL deposits no references at all
                    (BERT's own venue DOI returns 0).
    OpenCitations   0 references for the same paper.

Semantic Scholar covers preprints properly but throttles anonymous callers to a 429
on the first request, and a key is not available here.

**So take the bibliography from the paper.** arXiv serves every submission's LaTeX
source, and the `.bbl` is the authors' own reference list. Five test papers parsed
5 for 5 against OpenAlex's 21%.

**It also removes a failure that nearly poisoned the last result.** OpenAlex's second
most-shared ancestor came back titled *"HISTORIAE, History of Socio-Cultural
Transformation as Linguistic Data"* on an unrelated LIPIcs DOI; its authorships were
Liu, Ott, Goyal, Du, Joshi, Chen, Levy, Lewis, Zettlemoyer. It was RoBERTa. A paper's
own `.bbl` cannot be mislabelled that way.

**Matching is by normalised title, not by id**, because a `.bbl` cites venues far more
often than arXiv numbers -- ViT's 58 entries carry 4 arXiv ids. Titles are fuzzier,
but the failure mode is a missed match rather than a wrong one, which is the right
direction to fail in when the output is "what does shipped AI rest on".

**Nothing is archived.** Source tarballs are streamed, parsed and discarded: arXiv
preserves its own history permanently, so this is enrichment and not capture, and
keeping 1.3 GB of LaTeX to extract a few hundred KB of titles would be waste. Only
the extracted bibliographies are written.
"""
import gzip
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import time
from pathlib import Path

import paperlib as P

HERE = Path(__file__).resolve().parent
OUT = P.RAW / "bibliographies.json"
# Identify honestly, and keep the contact address out of a public repository.
# OpenAlex's "polite pool" and arXiv both ask callers to supply a contact; an honest
# bot UA also gets fewer 403s than a browser string does. So the address is read from
# the environment and the committed default carries none.
#   export WSS_CONTACT="mailto:you@example.org"
UA = "q3dresearch wss +https://github.com/q3dresearch" + (
    f" ({os.environ['WSS_CONTACT']})" if os.environ.get("WSS_CONTACT") else "")
PAUSE = 3.0                      # arXiv asks for several seconds between requests
BIBITEM = re.compile(r"\\bibitem[^\n]*\n(.*?)(?=\\bibitem|\\end\{thebibliography\})", re.S)
BIBTEX_TITLE = re.compile(r"title\s*=\s*[{\"](.+?)[}\"]\s*,?\s*\n", re.S | re.I)


def clean(t: str) -> str:
    t = re.sub(r"\\href\s*\{[^}]*\}", " ", t)
    t = re.sub(r"\\url\s*\{[^}]*\}", " ", t)
    t = re.sub(r"[{}\\]|~", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" .,")
    return t


def from_bbl(text: str) -> list[str]:
    out = []
    for m in BIBITEM.finditer(text):
        blocks = [b.strip() for b in m.group(1).split("\\newblock") if b.strip()]
        if len(blocks) >= 2:
            t = clean(blocks[1])
            if 10 < len(t) < 220:
                out.append(t)
    return out


def from_bib(text: str) -> list[str]:
    return [c for c in (clean(m.group(1)) for m in BIBTEX_TITLE.finditer(text))
            if 10 < len(c) < 220]


def extract(blob: bytes) -> list[str]:
    """A submission is a tar.gz of sources, or a single gzipped .tex."""
    try:
        tf = tarfile.open(fileobj=io.BytesIO(blob))
    except Exception:
        try:
            return from_bbl(gzip.decompress(blob).decode("utf8", "replace"))
        except Exception:
            return []
    bbl, bib = [], []
    for m in tf.getmembers():
        if not m.isfile():
            continue
        if m.name.endswith(".bbl"):
            bbl.append(m)
        elif m.name.endswith(".bib"):
            bib.append(m)
    for m in bbl:                       # the .bbl is the compiled list actually cited
        got = from_bbl(tf.extractfile(m).read().decode("utf8", "replace"))
        if got:
            return got
    for m in bib:                       # a .bib may hold entries the paper never cites
        got = from_bib(tf.extractfile(m).read().decode("utf8", "replace"))
        if got:
            return got
    return []


def seeds():
    import glob
    archive = P.ARCHIVE  # see paperlib
    out = set()
    for p in sorted(glob.glob(str(archive / "raw" / "hf.models.top-downloads" / "*" / "*" / "*"))):
        op = gzip.open if p.endswith(".gz") else open
        for m in json.load(op(p, "rt")):
            out |= {t.split(":", 1)[1] for t in m.get("tags", []) if t.startswith("arxiv:")}
    return sorted(a for a in out if re.fullmatch(r"\d{4}\.\d{4,5}", a))


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    done = json.loads(OUT.read_text()) if OUT.exists() else {}
    ids = [a for a in seeds() if a not in done]
    print(f"  {len(ids)} to fetch ({len(done)} cached)", flush=True)
    bytes_seen = 0
    for i, a in enumerate(ids, 1):
        try:
            r = subprocess.run(["curl", "-sSL", "--max-time", "90", "-A", UA,
                                f"https://arxiv.org/e-print/{a}"],
                               capture_output=True, timeout=120)
            blob = r.stdout
            bytes_seen += len(blob)
            done[a] = extract(blob) if len(blob) > 500 else []
        except Exception:
            done[a] = []
        if i % 25 == 0:
            hit = sum(1 for v in done.values() if v)
            print(f"    {i}/{len(ids)}  parsed={hit}  {bytes_seen/1e6:.0f}MB streamed", flush=True)
            P.write_json_atomic(OUT, done)
        time.sleep(PAUSE)
    P.write_json_atomic(OUT, done)
    hit = sum(1 for v in done.values() if v)
    total = sum(len(v) for v in done.values())
    print(f"  {hit}/{len(done)} papers yielded a bibliography ({hit/len(done):.0%}), "
          f"{total:,} references, {bytes_seen/1e6:.0f}MB streamed and discarded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
