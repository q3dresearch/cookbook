#!/usr/bin/env python3
"""Recompute every number this recipe leans on, and catch a figure that has gone stale.

    python3 verify.py

**Why this exists.** Three figures and a README share the same facts, and a caption that was
right when it was written goes wrong silently. In the workspace this recipe came from, one
footnote claimed a figure covered "the six management categories pulled so far" long after the
code had been loading all twelve — the numbers were right and the note was describing a
previous version of itself. Two more figures carried the same sentence. Nothing catches that
except recomputing, and nothing catches a corrected script whose figure was never rebuilt
except comparing the timestamps.

If a number here disagrees with the README, **this script is authoritative and the prose is a
bug**, per the repo's own rule.
"""
import collections, glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brdata                                                            # noqa: E402

num = brdata.num
SUF = re.compile(r"\b(LLC|INC|INCORPORATED|CORP|CORPORATION|COMPANY|LTD|PLANT|FACILITY|"
                 r"SITE|WORKS|PLT|DIVISION|THE)\b")
TOPN = 30


def company(n):
    n = (n or "?").upper().replace(",", " ").replace(".", " ").replace("-", " ")
    n = re.sub(r"\bU\s*S\s+ECOLOGY\b", "US_ECOLOGY", n)
    n = SUF.sub(" ", n)
    n = re.sub(r"[^A-Z0-9_ ]", " ", n)
    t = [x for x in n.split() if x]
    return " ".join(t[:2]) if t else "?"


def gini(v):
    v = sorted(v)
    n, tot = len(v), sum(v)
    return (2 * sum((i + 1) * x for i, x in enumerate(v)) / (n * tot) - (n + 1) / n) if tot and n else 0


def stale():
    """A figure older than the script that draws it is a caption describing a past version."""
    out = []
    for py in sorted(glob.glob(os.path.join(HERE, "*.py"))):
        stem = os.path.basename(py)[:-3]
        if stem in ("brdata", "plate", "fetch", "verify"):
            continue
        svg = os.path.join(HERE, "..", "charts", f"{stem}.svg")
        if not os.path.exists(svg):
            out.append((stem, "no figure built"))
        elif os.path.getmtime(svg) < os.path.getmtime(py):
            out.append((stem, "figure is older than its script"))
    return out


def load(cycle):
    cat = collections.defaultdict(collections.Counter)
    tons = collections.Counter()
    rows = 0
    for r in brdata.load(cycle):
        t = num(r["managed_tons"])
        if t <= 0:
            continue
        rows += 1
        c = (r["management_category"] or "").replace("/ STAG /", "/ STAB /")
        cat[c][company(r["handler_name"])] += t
        tons[c] += t
    return cat, tons, rows


def main():
    lag = stale()
    print("  stale figures:", "none" if not lag else "")
    for stem, why in lag:
        print(f"    {stem}: {why}")
    print()

    early, late = brdata.CYCLES[0], brdata.CYCLES[-1]
    ce, te, ne = load(early)
    cl, tl, nl = load(late)
    TOT = sum(tl.values())
    print(f"  {'':<26}{'':>10}{early:>22}{late:>22}")
    print(f"  {'route':<26}{'':>10}{'firms  gini  top30':>22}{'firms  gini  top30':>22}")
    rows = sorted(cl, key=lambda c: -tl[c])
    for c in rows:
        if tl[c] < 1000 or c not in ce:
            continue
        line = f"  {c.split('/')[0].strip()[:25]:<26}{tl[c]/1e6:>9,.1f}M"
        for cat in (ce, cl):
            v = sorted(cat[c].values(), reverse=True)
            g30 = f"{gini(v[:TOPN]):.2f}" if len(v) >= TOPN else "   —"
            line += f"{len(v):>9}{gini(v):>7.2f}{g30:>6}"
        print(line)

    print(f"\n  total managed tonnage {late}   {TOT/1e6:,.1f}M over {nl:,} records")
    print(f"  records with tonnage {early}    {ne:,}")
    site = collections.Counter()
    for r in brdata.load(late):
        t = num(r["managed_tons"])
        if t > 0:
            site[(r["handler_name"] or "?").split(",")[0][:34]] += t
    nm, v = site.most_common(1)[0]
    print(f"  largest single site           {nm}  {v/1e6:,.2f}M = {v/TOT:.1%} of national")
    ot = cl.get("OTHER TREATMENT", {})
    if ot:
        print(f"  other treatment, largest firm {max(ot.values())/sum(ot.values()):.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
