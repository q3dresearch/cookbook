#!/usr/bin/env python3
"""The two routes a brain-scan depositor can take, and what each one costs in reuse.

    python3 consent.py

A structural MRI is a photograph of a face. OpenNeuro asks two questions about that, and they
are **branches of one decision, not two boxes that both have to be ticked**:

  affirmedDefaced  -- the scans have been defaced, so the face is gone
  affirmedConsent  -- the participants consented to publish structural scans *without* defacing

Either alone discharges the obligation. Reading `affirmedConsent` by itself therefore raises a
false alarm: it is false on 646 of 795 MRI datasets, which looks like mass non-compliance and
is mostly the stricter answer. Three routes, not four cells:

  DEFACED   736  the face is removed
  CONSENT    51  the face is kept, and the participants agreed to that
  NEITHER     8  no record of either, which is the entire audit list

**Age matters for the outcome and not for the route.** Downloads per year is undefined for a
dataset published weeks ago, so the medians here are computed only on datasets at least a year
old. Restricting further to 2021-2024, where both routes are well populated, moves the
comparison from 13.4-against-13.0 to 13.1-against-13.0 -- that is, not at all.
"""
import collections, json, os, random, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fold, modality                                                    # noqa: E402

MIN_AGE = 1.0
ROUTES = ("defaced", "consent", "neither")


def route(r):
    d, c = r.get("defaced"), r.get("consent")
    if d is None and c is None:
        return None                     # never asked; predates the field
    if d:
        return "defaced"
    return "consent" if c else "neither"


def rows():
    out = []
    for r in fold.load()["rows"]:
        if modality.modality(r) != "mri":
            continue
        k = route(r)
        if k:
            out.append(dict(r, route=k, yr=int(r["pub"][:4]),
                            rated=r["dl_yr"] is not None and r["age"] >= MIN_AGE))
    return out


def perm(a, b, iters=20000, seed=11):
    rng = random.Random(seed)
    obs = statistics.median(b) - statistics.median(a)
    pool, n, h = list(a) + list(b), len(a), 0
    for _ in range(iters):
        rng.shuffle(pool)
        if abs(statistics.median(pool[n:]) - statistics.median(pool[:n])) >= abs(obs):
            h += 1
    return obs, (h + 1) / (iters + 1)


def detectable(a, b, ks=(1.5, 1.75, 2.0), trials=200, seed=7):
    """The size of gap this design could actually have seen. A null without one is a claim
    about the sample, not about the world."""
    rng = random.Random(seed)
    out = {}
    for k in ks:
        hits = 0
        for _ in range(trials):
            fake = [rng.choice(a) * k for _ in range(len(b))]
            if perm(a, fake, iters=1200, seed=rng.randrange(1 << 30))[1] < 0.05:
                hits += 1
        out[k] = hits / trials
    return out


def main():
    rs = rows()
    by = collections.defaultdict(list)
    for r in rs:
        by[r["route"]].append(r)
    print(f"\n  {len(rs):,} MRI datasets answered at least one of the two questions")
    for k in ROUTES:
        g = by[k]
        rated = [x for x in g if x["rated"]]
        m = statistics.median(x["dl_yr"] for x in rated) if rated else None
        print(f"    {k:<9}{len(g):>5} ({len(g)/len(rs):>4.0%})   rated {len(rated):>4}   "
              + (f"median {m:>6.1f} dl/yr" if m else ""))
    a = [x["dl_yr"] for x in by["defaced"] if x["rated"]]
    b = [x["dl_yr"] for x in by["consent"] if x["rated"]]
    d, p = perm(a, b)
    print(f"\n  defaced vs consent: {statistics.median(b)/statistics.median(a):.2f}x, "
          f"gap {d:+.1f}, p {p:.4f}")
    print("  detectable effect at p<0.05:")
    for k, pw in detectable(a, b).items():
        print(f"    a {k:.2f}x difference would be caught {pw:.0%} of the time")
    print(f"\n  the audit list: {', '.join(sorted(x['id'] for x in by['neither']))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
