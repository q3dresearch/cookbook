#!/usr/bin/env python3
"""Method inventory from activist short-seller reports.

    python tools/short-seller-sources.py [corpus.json]

Reads a WordPress REST dump (`/wp-json/wp/v2/posts?_fields=…,content`) and
reports which evidence types each report declares, plus the inline
`(Source: …)` citations it carries.

Deliberately not an extractor. The corpus is ~100 reports; the numbers below
are for orienting a human who then reads them. Keyword classification of the
citation strings was tried and abandoned — it left 60% unclassified, and a
60%-miss classifier produces confident wrong percentages. Frequency-ranking
the raw labels is honest and was more informative anyway.
"""
import collections, html, json, re, sys

import corpuslib

SRC = re.compile(r"\(\s*Source:\s*([^)]{3,120})\)", re.I)

# Probes live in corpuslib so the chart, this inventory and the control corpus
# all measure the same thing. They used to be copied here and drifted apart.


def body(post):
    return html.unescape(re.sub(r"<[^>]+>", " ", post["content"]["rendered"]))


def main(path=None):
    # 94 initial reports. The API returns 105; the extra 11 are 9 rebuttals and
    # 2 house announcements, and they cite almost nothing, so including them
    # drags every share below down. See corpuslib.
    posts = json.load(open(path)) if path else corpuslib.load("initial")
    n = len(posts)
    print(f"corpus: {n} initial reports, {sum(len(body(p).split()) for p in posts):,} words\n")

    print("share of reports citing each evidence type:")
    for label, pat in corpuslib.probes().items():
        k = sum(1 for p in posts if re.search(pat, body(p), re.I))
        print(f"  {label:<26}{k:>4}/{n}  {k/n:>5.0%}")

    cites = []
    for p in posts:
        cites += [re.sub(r"\s+", " ", m.group(1)).strip() for m in SRC.finditer(body(p))]
    norm = [re.sub(r"\[.*?\]|\s*,?\s*\d[\d,\s.]*$|\s+Pg\.?.*$", "", c, flags=re.I).strip(" ,.")
            for c in cites]
    freq = collections.Counter(x for x in norm if x)
    print(f"\ninline citations: {len(cites):,} across {len(freq)} distinct labels")
    print("most-cited sources:")
    for s, c in freq.most_common(20):
        print(f"  {c:>4}  {s[:70]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
