#!/usr/bin/env python3
"""Do these articles co-occur, and does that make the per-article fine a fiction?

    python gdpr-cocitation.py <gdprhub.jsonl>

A fine is imposed on a decision, not on an article. Any statement of the form
"Article X costs EUR N" attributes a joint outcome to one of its parts, and if
articles travel in packs the number is not about that article at all.

Three tests, in increasing strength:

    1. how many articles a decision cites — if it were usually one, there is
       no confound to worry about
    2. conditional co-citation, P(Y | X) — whether a given article ever appears
       without a particular companion
    3. solo fines — the median when an article is the ONLY one cited, which is
       the only clean attribution available, reported with its sample size so a
       reader can see when it rests on nine cases

The honest conclusion is usually that a per-article fine is an association and
not an effect, and this prints the numbers needed to say so precisely.
"""
from __future__ import annotations

import collections
import importlib.util
import json
import statistics
import sys
from pathlib import Path


def _analysis():
    spec = importlib.util.spec_from_file_location(
        "gdpr_analysis", str(Path(__file__).with_name("gdpr-article-concentration.py")))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    g = _analysis()
    rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]

    cases = []
    for r in rows:
        arts = {g.artnum(x) for x in r["articles"]}
        arts = frozenset(a for a in arts if a and a not in g.SCAFFOLD)
        if not arts:
            continue
        cur = (r.get("currency") or "").strip().upper()
        fine = None
        if cur in ("EUR", "€") or (not cur and r.get("juris") in g.EUROZONE):
            fine = g.money(r.get("fine", ""))
        cases.append((arts, fine))
    n = len(cases)
    print(f"\n  {n:,} decisions citing at least one breachable article\n")

    # 1. how many articles per decision
    sizes = collections.Counter(len(a) for a, _ in cases)
    print("  ARTICLES PER DECISION")
    mx = max(sizes.values())
    for k in sorted(sizes):
        c = sizes[k]
        print(f"    {k:>2} article{'s' if k > 1 else ' '}  {c:>6,}  {c/n:>5.1%}  "
              f"{'█' * max(1, round(c/mx*24))}")
    multi = sum(c for k, c in sizes.items() if k > 1)
    print(f"    {multi/n:.0%} of decisions cite more than one article, so most fines "
          f"cannot be attributed to a single one.")

    cited = collections.Counter()
    for arts, _ in cases:
        for a in arts:
            cited[a] += 1
    top = [a for a, _ in cited.most_common(8)]

    # 2. conditional co-citation
    print("\n  CO-CITATION — P(row article | column article), and how often each is alone")
    print(f"    {'':<9}" + "".join(f"{'A'+str(c):>7}" for c in top) + f"{'alone':>8}")
    for a in top:
        cells = []
        for b in top:
            if a == b:
                cells.append("     —")
                continue
            both = sum(1 for arts, _ in cases if a in arts and b in arts)
            cells.append(f"{both/cited[b]:>6.0%}")
        alone = sum(1 for arts, _ in cases if arts == {a})
        print(f"    Art {a:<5}" + "".join(f"{c:>7}" for c in cells)
              + f"{alone/cited[a]:>8.0%}")
    print("    Read down a column: of decisions citing that article, the share that also")
    print("    cite the row article. A high cell means the pair is one population.")

    # 3. solo fines vs fines in company
    print("\n  FINE ATTRIBUTION — median when an article is alone, versus alongside others")
    print(f"    {'article':<9}{'solo n':>8}{'solo median':>14}{'with others n':>15}"
          f"{'median':>12}")
    for a in top:
        solo = [f for arts, f in cases if arts == {a} and f]
        comp = [f for arts, f in cases if a in arts and len(arts) > 1 and f]
        sm = f"{statistics.median(solo):,.0f}" if len(solo) >= 5 else "too few"
        cm = f"{statistics.median(comp):,.0f}" if len(comp) >= 5 else "too few"
        print(f"    Art {a:<5}{len(solo):>8,}{sm:>14}{len(comp):>15,}{cm:>12}")
    print("    A solo median resting on fewer than five cases is not reported. Where solo")
    print("    and combined diverge, the combined figure is measuring the company an")
    print("    article keeps, not the article.")

    # Does the biggest fine driver travel with a particular companion?
    print("\n  WHAT RIDES ALONG WITH THE EXPENSIVE ONES")
    fined = [(arts, f) for arts, f in cases if f]
    if len(fined) >= 40:
        med = statistics.median(f for _, f in fined)
        big = [arts for arts, f in fined if f >= med]
        small = [arts for arts, f in fined if f < med]
        lift = []
        for a in cited:
            nb = sum(1 for arts in big if a in arts)
            ns = sum(1 for arts in small if a in arts)
            if nb + ns >= 12:
                lift.append(((nb / max(len(big), 1)) - (ns / max(len(small), 1)), a, nb, ns))
        lift.sort(reverse=True)
        print(f"    Fines at or above the median of EUR {med:,.0f} versus below, "
              f"{len(big):,} against {len(small):,} decisions:")
        for d, a, nb, ns in lift[:5]:
            print(f"      Art {a:<4} appears in {nb/max(len(big),1):>5.0%} of expensive vs "
                  f"{ns/max(len(small),1):>5.0%} of cheap   {d:+.0%}")
        for d, a, nb, ns in lift[-3:]:
            print(f"      Art {a:<4} appears in {nb/max(len(big),1):>5.0%} of expensive vs "
                  f"{ns/max(len(small),1):>5.0%} of cheap   {d:+.0%}")
        print("    This is association only. Fine size also tracks the company's size, the")
        print("    authority's own scale, and the year, none of which are in this corpus.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
