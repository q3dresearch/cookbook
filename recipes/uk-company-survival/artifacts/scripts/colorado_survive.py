#!/usr/bin/env python3
"""Colorado: real cohorts, and a test of the assumption the UK estimate rests on.

    python3 colorado_survive.py

The UK figure is a SYNTHETIC cohort. Age-specific hazards were measured over a two-year
window and strung together as though one company lived through all of them. That is only
a valid summary if the hazard depends on a company's age rather than on the era it was
born into, and in the UK that could only be half-checked, against two adjacent years.

Colorado has formation dates back to 1864 and dated deaths back to 1912, so the same
question can be asked of real cohorts twenty years apart. If five-year survival is flat
across founding decades, the UK's synthetic cohort is a fair summary. If it drifts, then
stringing hazards together describes a company that never existed.

A DEFINITION THAT IS NOT OBVIOUS, AND MOVES THE ANSWER. Colorado's largest single status
is "Delinquent" -- over a million entities that stopped filing and have not been
dissolved. They are neither trading nor ended. They carry no death date, so they are
treated here as ALIVE AND CENSORED, which is the conservative choice, and the cost of
that choice is reported rather than buried: the same curve is printed with them counted
as dead.
"""
import collections, csv, datetime as dt, gzip, json, os, sys

DATA = os.environ.get("FSB_DATA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
SRC = os.path.join(DATA, "colorado.csv.gz")
TODAY = dt.date(2026, 9, 16)
ENDED = {"Voluntarily Dissolved", "Administratively Dissolved", "Judicially Dissolved",
         "Revoked", "Merged", "Converted", "Withdrawn", "Dissolved (Term Expired)",
         "Consolidated", "Effectiveness Prevented"}
ZOMBIE = {"Delinquent", "Noncompliant", "Registered Agent Resigned"}
AGES = [1, 2, 3, 5, 8, 12, 20, 30]


def d(s):
    try:
        return dt.date.fromisoformat(s[:10])
    except Exception:
        return None


def load():
    rows = []
    with gzip.open(SRC, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            f = d(r["formed"])
            if not f or f > TODAY:
                continue
            rows.append((f, d(r["died"]), r["status"], r["type"]))
    return rows


def km(subjects, horizon=TODAY):
    """subjects: (formed, died_or_None). Right-censored at the capture date.
    -> {age: survival}. Exact, not banded: every company's full life is observed."""
    events = collections.Counter()
    exits = collections.Counter()
    for f, x in subjects:
        age = ((x or horizon) - f).days / 365.25
        b = int(age)
        exits[b] += 1
        if x:
            events[b] += 1
    n = len(subjects)
    surv, out, at_risk = 1.0, {}, n
    for b in range(0, 60):
        if at_risk <= 0:
            break
        e = events[b]
        if at_risk > 0:
            surv *= (1 - e / at_risk)
        out[b + 1] = surv
        at_risk -= exits[b]
    return out


def main():
    rows = load()
    print(f"  {len(rows):,} entities with a usable formation date")
    st = collections.Counter(r[2] for r in rows)
    ended = sum(v for k, v in st.items() if k in ENDED)
    zomb = sum(v for k, v in st.items() if k in ZOMBIE)
    print(f"  ended: {ended:,} ({ended/len(rows):.1%}) | zombie (stopped filing, not dissolved): "
          f"{zomb:,} ({zomb/len(rows):.1%}) | other/alive: {len(rows)-ended-zomb:,}")
    dated = sum(1 for r in rows if r[2] in ENDED and r[1])
    print(f"  of the ended, {dated:,} carry a parseable death date ({dated/ended:.1%})")

    print("\n== how a company ends, and how old it was ==")
    by = collections.defaultdict(list)
    for f, x, s, t in rows:
        if s in ENDED and x:
            by[s].append((x - f).days / 365.25)
    for s, ages in sorted(by.items(), key=lambda kv: -len(kv[1])):
        if len(ages) < 500:
            continue
        ages.sort()
        print(f"  {s:<28} {len(ages):>8,}  median age {ages[len(ages)//2]:5.1f}y   "
              f"quarter past {ages[int(len(ages)*0.75)]:5.1f}y")

    subs = [(f, x if (s in ENDED and x) else None) for f, x, s, t in rows]
    curve = km(subs)
    subs_z = [(f, x if ((s in ENDED or s in ZOMBIE) and x) else (TODAY if s in ZOMBIE else None))
              for f, x, s, t in rows]
    curve_z = km(subs_z)
    print("\n== survival by age, Colorado, every entity ever registered ==")
    print(f"  {'age':>5}{'survival':>11}{'if zombies count as dead':>27}")
    for a in AGES:
        print(f"  {a:>4}y{curve.get(a, float('nan')):>11.1%}{curve_z.get(a, float('nan')):>27.1%}")

    print("\n== THE TEST: is five-year survival stable across founding eras? ==")
    print(f"  {'formed':<14}{'n':>10}{'survived 5y':>13}{'10y':>8}")
    eras = collections.defaultdict(list)
    for f, x, s, t in rows:
        if f.year < 1900 or f.year > TODAY.year - 6:
            continue
        eras[f.year // 10 * 10].append((f, x if (s in ENDED and x) else None))
    era_rows = []
    for dec in sorted(eras):
        grp = eras[dec]
        if len(grp) < 2000:
            continue
        c = km(grp)
        era_rows.append((dec, len(grp), c.get(5), c.get(10)))
        print(f"  {dec}s{'':<9}{len(grp):>10,}{c.get(5, float('nan')):>13.1%}"
              f"{(c.get(10) if c.get(10) is not None else float('nan')):>8.1%}")
    vals = [r[2] for r in era_rows if r[2] is not None]
    if vals:
        print(f"  spread across eras: {min(vals):.1%} to {max(vals):.1%}, a range of {max(vals)-min(vals):.1%}")
        print("  A synthetic cohort is a fair summary only to the width of that range.")

    print("\n== by legal form ==")
    forms = collections.defaultdict(list)
    for f, x, s, t in rows:
        forms[t].append((f, x if (s in ENDED and x) else None))
    for t, grp in sorted(forms.items(), key=lambda kv: -len(kv[1]))[:6]:
        c = km(grp)
        print(f"  {t:<8} {len(grp):>9,}  5y {c.get(5, float('nan')):>6.1%}   10y {c.get(10, float('nan')):>6.1%}")

    json.dump({"n": len(rows), "ended": ended, "zombie": zomb,
               "survival": {str(a): curve.get(a) for a in AGES},
               "survival_zombie_dead": {str(a): curve_z.get(a) for a in AGES},
               "eras": [{"decade": d_, "n": n_, "s5": s5, "s10": s10} for d_, n_, s5, s10 in era_rows],
               "manner": {s: {"n": len(a), "median_age": sorted(a)[len(a)//2]} for s, a in by.items() if len(a) >= 500}},
              open(os.path.join(DATA, "colorado_survival.json"), "w"), indent=1)
    print(f"\n  wrote {os.path.join(DATA, 'colorado_survival.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
