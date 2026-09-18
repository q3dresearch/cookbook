#!/usr/bin/env python3
"""Recompute every number this recipe publishes, from the snapshots rather than the derived JSON.

    FSB_DATA=/path/to/corpus python3 verify.py

**Why this exists.** Seven figures and a README share the same facts, and prose drifts from code
silently. Re-reading `survival.json` would only re-read what `survive.py` wrote, so this reloads
the Companies House snapshots and recomputes.

It is not optional caution. The sibling recipe `landfill-countdown` shipped four numbers that no
script produced -- a hardcoded headline, an unstated threshold, a miscount, and a percentage its
own figure contradicted on the same page -- and none of it was visible until something recomputed
from source. On its first run this script found no drift here: every published number reproduces.

**Replicate the figure's definition, not a reasonable one.** Four claims appeared to disagree on
the first attempt and all four were this script's fault. "Flagged" in figure 6 means any of five
statuses, not the strike-off flag alone. Its departures are measured over the whole two years
from the 2024 base, not per interval. "In Administration" is an exact status string, not a
substring match. And figure 7's register share excludes rows with no postcode or an unusable
incorporation date. A verifier that invents its own basis manufactures drift.

The corpus is 1.5 GB and is not committed. Without it this script says so and stops, rather than
reporting a smaller answer: a survival rate computed on a missing snapshot is not a smaller
measurement, it is a wrong one.

If a number here disagrees with the README, **this script is authoritative and the prose is a
bug**, per the repo's own rule.
"""
import collections, csv, glob, gzip, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import survive                                                           # noqa: E402

DATA = survive.DATA
AGENT_TOP = 40
# figure 6's own vocabulary, not a reasonable-looking substitute
FLAGGED = ("Proposal to Strike off", "Liquidation", "Administration", "Receiver", "Voluntary")
WATCH = ("Active", "Active - Proposal to Strike off", "Liquidation", "In Administration")


def geo(name):
    with gzip.open(os.path.join(DATA, name), "rt", newline="") as fh:
        yield from csv.DictReader(fh)


def main():
    files = sorted(glob.glob(os.path.join(DATA, "compact-*.csv.gz")))
    dates = [os.path.basename(f)[8:18] for f in files]
    gfiles = sorted(glob.glob(os.path.join(DATA, "geo-*.csv.gz")))
    if len(files) < 3 or len(gfiles) < 3:
        print(f"  found {len(files)} compact and {len(gfiles)} geo snapshot(s) in {DATA}")
        print("  need three of each. Point FSB_DATA at the corpus, or run fetch.py -- a")
        print("  survival rate on a missing snapshot is a wrong number, not a smaller one.")
        return 1

    snaps = {d: survive.load(f) for f, d in zip(files, dates)}
    for d in dates:
        print(f"  {d}: {len(snaps[d]):,} live companies")
    t0, t1, t2 = dates

    print(f"\n  == survival: the register admits only one death, disappearance ==")
    haz = collections.defaultdict(lambda: [0, 0])
    for x, y in ((t0, t1), (t1, t2)):
        for num, (inc, sc, cat, st) in snaps[x].items():
            if not inc:
                continue
            age = survive.months_between(inc, x) / 12
            if age < 0:
                continue
            bd = survive.band(age)
            if bd is not None:
                haz[bd][0] += 1
                haz[bd][1] += num not in snaps[y]
    surv = 1.0
    for lo, hi in survive.BANDS:
        lab = f"{lo}-{hi}" if hi < 200 else f"{lo}+"
        if lab not in haz or lo >= 5:
            continue
        risk, died = haz[lab]
        rate = died / risk if risk else 0
        surv *= (1 - rate) ** (hi - lo)
        print(f"  {'annual hazard, age ' + lab:<40}{rate:>9.2%}   n={risk:,}")
    print(f"  {'gone by age five':<40}{1-surv:>9.1%}   README: two-thirds")

    # Figure 6's basis exactly: one base snapshot, a two-year window, exact status strings.
    print(f"\n  == is a death visible before it happens? ==")
    s24 = {r["number"]: r["status"] for r in geo("geo-2024-09-01.csv.gz")}
    s25 = {r["number"] for r in geo("geo-2025-09-01.csv.gz")}
    s26 = {r["number"] for r in geo("geo-2026-09-01.csv.gz")}
    st = collections.defaultdict(lambda: [0, 0, 0])
    for num, status in s24.items():
        v = st[status]
        v[0] += 1
        v[1] += num in s25
        v[2] += num in s26
    total = sum(v[0] for v in st.values())
    deaths = sum(v[0] - v[2] for v in st.values())
    flag_d = sum(v[0] - v[2] for k, v in st.items() if any(f in k for f in FLAGGED))
    flagged_n = sum(v[0] for k, v in st.items() if any(f in k for f in FLAGGED))
    print(f"  {'status':<34}{'n':>10}{'year one':>11}{'survivors':>11}")
    for k in WATCH:
        if k not in st:
            continue
        n, a1, a2 = st[k]
        S1 = a1 / n
        print(f"  {k[:32]:<34}{n:>10,}{1-S1:>11.1%}{((S1-a2/n)/S1 if S1 else 0):>11.1%}")
    print(f"  {'flagged share of the register':<34}{flagged_n/total:>21.1%}   README: 8.6%")
    print(f"  {'departures carrying no warning':<34}{1-flag_d/deaths:>21.0%}   README: 81%")

    # Figure 7's basis exactly: rows with a postcode and a usable incorporation date.
    print(f"\n  == the forty busiest registered offices ==")
    alive = s26
    rows = list(geo("geo-2024-09-01.csv.gz"))
    pc = collections.Counter(r["postcode"] for r in rows if r["postcode"])
    top = pc.most_common(AGENT_TOP)
    agents = {p for p, _ in top}
    by = collections.defaultdict(lambda: [0, 0, 0, 0])
    per = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        inc = r["incorp"]
        if not r["postcode"] or len(inc) != 7 or not inc[:4].isdigit():
            continue
        y, s = int(inc[:4]), r["number"] in alive
        v = by[y]
        if r["postcode"] in agents:
            v[0] += 1; v[1] += s
            q = per[r["postcode"]]; q[0] += 1; q[1] += s
        else:
            v[2] += 1; v[3] += s
    ta = sum(by[y][0] for y in by); to = sum(by[y][2] for y in by)
    tos = sum(by[y][3] for y in by)
    use = [y for y in by if by[y][0] >= 200]
    std = sum((by[y][1] / by[y][0]) * by[y][2] for y in use) / sum(by[y][2] for y in use)
    print(f"  {'companies at the forty':<40}{ta:>12,}   README: 449,461")
    print(f"  {'share of the register':<40}{ta/(ta+to):>12.1%}   README: 8.1%")
    for y in (2012, 2023):
        if y in by and by[y][0] and by[y][2]:
            print(f"  {str(y) + ' cohort, two-year survival':<40}"
                  f"{by[y][1]/by[y][0]:>11.1%} at an agent{by[y][3]/by[y][2]:>8.1%} elsewhere")
    print(f"  {'age-standardised gap':<40}{(tos/to-std)*100:>11.1f} points   README: 8.9")
    for p, n in top[:3]:
        q = per[p]
        print(f"    {p:<10}{n:>9,} companies   {1-q[1]/q[0]:>5.0%} gone in two years")
    return 0


if __name__ == "__main__":
    sys.exit(main())
