#!/usr/bin/env python3
"""Which GDPR articles actually get enforced, and which carry the money.

    python gdpr-article-concentration.py <gdprhub.jsonl>

Reads the corpus written by fetch-gdprhub.py — the whole population of decision
pages, not a sample. An earlier version of this recipe ran on a systematic 1-in-3
sample; the population is cheap enough here that there is no reason to defend a
sample's representativeness when you can just not take one.

Two distributions, and they are not the same question:

* **How often an article is cited** — what regulators engage with. This is what
  a builder wants: the things most likely to be examined.
* **What the fines attach to** — where the money is. A decision citing several
  articles contributes its fine to each, so these totals are exposure associated
  with an article, never a share of a fixed pot, and they must not be summed.

Art 4 is DEFINITIONS. It appears as scaffolding, not as a breach, and reading it
as "the fifth most-violated article" is wrong. Articles 58 (authority powers),
77 (right to complain) and 3 (territorial scope) are the same. All four are
excluded from the ranking and reported separately.
"""
from __future__ import annotations

import collections
import json
import re
import statistics
import sys

# Jurisdictions whose fines are in euro. Needed because the Currency field is
# often blank: a blank from Madrid is a euro, a blank from Warsaw is not, and
# assuming otherwise silently multiplies a Polish fine by about four.
EUROZONE = {"Austria", "Belgium", "Croatia", "Cyprus", "Estonia", "Finland",
            "France", "Germany", "Greece", "Ireland", "Italy", "Latvia",
            "Lithuania", "Luxembourg", "Malta", "Netherlands", "Portugal",
            "Slovakia", "Slovenia", "Spain", "EDPB", "EU"}

# Articles a controller cannot breach. Rather than judge these case by case, the
# rule follows the regulation's own structure:
#
#   Chapter I    (Art 1-4)    subject matter, scope, definitions
#   Chapter VI   (Art 51-59)  the supervisory authorities themselves
#   Chapter VII  (Art 60-76)  cooperation and consistency between authorities
#   Chapter VIII (procedural) the right to complain, judicial remedies,
#                             representation, and the criteria for setting a fine
#
# Chapters II-V are the obligations. Everything above is cited as the machinery a
# case runs on: Art 58 is the authority's power to act, Art 60 is the one-stop-shop
# mechanism that routes cross-border cases, and you are fined under Art 83, never
# for it. Left in deliberately: Art 82 (compensation) is a remedy rather than an
# obligation, but it names a liability the controller owes.
#
# This matters to the numbers, not just the taxonomy. Art 60 appears in 58
# decisions with a median fine of EUR 95,500,000 — it routes the largest
# cross-border cases — and ranking it as an enforced article puts "cooperation
# between supervisory authorities" near the top of a list a builder reads as
# things to get right.
SCAFFOLD_RANGES = ((1, 4), (51, 76))
SCAFFOLD_EXTRA = {77: "right to lodge a complaint", 78: "remedy against an authority",
                  79: "judicial remedy against a controller", 80: "representation",
                  83: "criteria for setting a fine"}


def scaffold_label(a: int) -> str:
    if a in SCAFFOLD_EXTRA:
        return SCAFFOLD_EXTRA[a]
    if 1 <= a <= 4:
        return "scope and definitions"
    if 51 <= a <= 59:
        return "the authority's own powers"
    if 60 <= a <= 76:
        return "cooperation between authorities"
    return "procedure"


def is_scaffold(a: int) -> bool:
    return any(lo <= a <= hi for lo, hi in SCAFFOLD_RANGES) or a in SCAFFOLD_EXTRA


class _Scaffold:
    """Membership by rule, but still iterable for the scripts that list it."""

    def __contains__(self, a):
        return isinstance(a, int) and is_scaffold(a)

    def _members(self):
        seen = {a for lo, hi in SCAFFOLD_RANGES for a in range(lo, hi + 1)}
        return sorted(seen | set(SCAFFOLD_EXTRA))

    def __iter__(self):
        return iter(self._members())

    def __len__(self):
        return len(self._members())


SCAFFOLD = _Scaffold()

TITLES = {5: "principles of processing", 6: "lawfulness of processing",
          12: "transparent information", 13: "information to be provided",
          14: "information (indirect collection)", 15: "right of access",
          17: "right to erasure", 21: "right to object", 24: "controller duty",
          25: "data protection by design", 28: "processors",
          32: "security of processing", 33: "breach notification",
          34: "communicating a breach", 9: "special categories of data",
          82: "right to compensation", 83: "conditions for fines",
          44: "transfers outside the EU", 7: "conditions for consent",
          35: "data protection impact assessment", 30: "records of processing",
          37: "designating a DPO", 38: "position of the DPO", 39: "DPO tasks",
          22: "automated decisions and profiling", 16: "right to rectification",
          18: "right to restriction", 20: "data portability",
          26: "joint controllers", 27: "representatives outside the EU",
          31: "cooperation with the authority", 46: "transfers by safeguards",
          49: "derogations for transfers", 88: "processing at work",
          85: "processing and free expression", 2: "material scope",
          10: "criminal conviction data", 11: "identification not required",
          19: "notifying rectification or erasure", 36: "prior consultation",
          40: "codes of conduct", 89: "research and statistics"}


def artnum(s: str) -> int | None:
    m = re.search(r"Article\s+(\d+)", s or "")
    return int(m.group(1)) if m else None


def money(raw: str) -> float | None:
    """Parse a GDPRhub fine field. Returns None unless it is unambiguously one number.

    The field is free text written by many contributors: '5.000', '1,500',
    '20 000', 'EUR 1.000', '100.000 (reduced to 50.000)', '2,5 million'.

    Rather than enumerate the ways a value can be unusable, this accepts only what
    is certain: strip a leading or trailing currency token, and require everything
    left to be digits and separators. Anything with a surviving letter is dropped
    — '2.5m' silently read as 2.5 is a million-fold error in a headline, and there
    is no shortage of decisions with clean values.
    """
    if not raw:
        return None
    s = re.sub(r"[€$£]|\b(EUR|USD|GBP|PLN|SEK|NOK|DKK|HUF|CZK|RON|BGN|CHF|ISK)\b",
               " ", raw.strip(), flags=re.I)
    s = s.strip()
    if not s or not re.fullmatch(r"[\d.,\s]+", s):
        return None                       # a word survived: not a plain amount
    t = re.sub(r"\s", "", s)
    if "," in t and "." in t:             # both present: the rightmost is the decimal
        dec = max(t.rfind(","), t.rfind("."))
        t = re.sub(r"[.,]", "", t[:dec]) + "." + t[dec + 1:]
    elif t.count(",") == 1 and 1 <= len(t.split(",")[1]) <= 2:
        t = t.replace(",", ".")           # 1500,50 or 2,5 — decimal comma
    elif t.count(".") == 1 and 1 <= len(t.split(".")[1]) <= 2 and len(t.split(".")[0]) <= 3:
        pass                              # 100.50 — decimal point
    else:
        t = re.sub(r"[.,]", "", t)        # thousands separators only
    try:
        v = float(t)
    except ValueError:
        return None
    return v if 0 < v < 2e9 else None


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
    n = len(rows)

    cited: collections.Counter = collections.Counter()
    for r in rows:
        for a in {artnum(x) for x in r["articles"]}:
            if a:
                cited[a] += 1
    enforced = [(a, c) for a, c in cited.most_common() if a not in SCAFFOLD]
    tot = sum(c for _, c in enforced)

    print(f"\n  {n:,} decisions · {len(cited)} distinct articles cited · "
          f"{sum(1 for r in rows if not r['articles']):,} cite none\n")
    print("  enforced articles, share of decisions")
    for a, c in enforced[:14]:
        print(f"    Art {a:<4}{c:>6,}  {c/n:>5.1%}  {TITLES.get(a, '')[:32]}")
    print(f"\n    top 2 = {sum(c for _, c in enforced[:2])/tot:.0%} of enforced citations"
          f" · top 5 = {sum(c for _, c in enforced[:5])/tot:.0%}"
          f" · tail of {len(enforced)-5} = {sum(c for _, c in enforced[5:])/tot:.0%}")

    scaff = [(a, c) for a, c in cited.most_common() if a in SCAFFOLD]
    print(f"\n  scaffolding (cited, not breachable) — excluded above; "
          f"{sum(c for _, c in scaff):,} citations across {len(scaff)} articles")
    for a, c in scaff[:8]:
        print(f"    Art {a:<4}{c:>6,}  {c/n:>5.1%}  "
              f"{scaffold_label(a)}")

    # Fines. EUR only: converting a dozen currencies needs rates for the year of
    # each decision, and a wrong rate is a silent error in the headline number.
    eur = [r for r in rows
           if (r.get("currency") or "").strip().upper() in ("EUR", "\u20ac")
           or (not (r.get("currency") or "").strip() and r.get("juris") in EUROZONE)]
    fined = [(r, money(r.get("fine", ""))) for r in eur]
    fined = [(r, v) for r, v in fined if v]
    print(f"\n  fines: {sum(1 for r in rows if r.get('fine')):,} decisions carry a fine field, "
          f"{len(fined):,} parse to a single EUR amount")
    if fined:
        by_art: dict[int, list[float]] = collections.defaultdict(list)
        for r, v in fined:
            for a in {artnum(x) for x in r["articles"]}:
                if a and a not in SCAFFOLD:
                    by_art[a].append(v)
        print("    exposure by article — decisions citing it that carried a fine")
        blank = sum(1 for r, _ in fined if not (r.get("currency") or "").strip())
        print(f"    ({blank:,} of these had a blank currency and a eurozone "
              f"jurisdiction; non-eurozone blanks are dropped)")
        print(f"    {'art':<8}{'n':>6}{'median':>12}{'total':>16}")
        rank = sorted(by_art.items(), key=lambda kv: -sum(kv[1]))
        for a, vs in rank[:12]:
            print(f"    Art {a:<4}{len(vs):>6,}{statistics.median(vs):>12,.0f}"
                  f"{sum(vs):>16,.0f}  {TITLES.get(a, '')[:26]}")
        print("    (a decision citing several articles counts in each — do not sum)")

    print("\n  jurisdiction — PUBLICATION practice, not violation rate")
    for j, c in collections.Counter(r["juris"] for r in rows if r["juris"]).most_common(8):
        print(f"    {j[:26]:<28}{c:>6,}  {c/n:>5.1%}")

    print("\n  by year")
    for y, c in sorted(collections.Counter(
            r["year"] for r in rows if (r.get("year") or "").isdigit()).items()):
        print(f"    {y}  {c:>6,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
