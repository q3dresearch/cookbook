#!/usr/bin/env python3
"""Whether a dataset contains resting-state recording, and what that is worth in reuse.

    python3 paradigm.py

`tasksCompleted` lists the paradigms a session ran. As free text it is uncountable -- 993
distinct values over 1,254 datasets -- but **one thing in it is countable**: whether any entry
mentions rest. 99 datasets say exactly `['rest']`, and rest appears somewhere in many more.

**The variable is presence, not dose, and that was tested rather than assumed.** Splitting
three ways inside MRI gives rest-only **19.0** downloads a year, rest-plus-task **17.5** and
task-only **7.8**. The first two are indistinguishable, so the binary is *contains rest*. The
alternative explanation -- that mixed datasets simply run more paradigms -- fails: among
task-only datasets the correlation between task count and reuse is **+0.049, t = 1.27**.

**Era is matched at 2019-2024** because downloads per year falls with age, and both groups are
well populated there.

**Datasets listing no task at all are excluded, not pooled.** 202 of them leave the field
empty, which is a missing answer and not a statement that no paradigm ran. Their median of 16.7
sits between the two groups and would blur both.
"""
import collections, json, math, os, random, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fold, modality                                                    # noqa: E402

DATA = os.path.join(HERE, "..", "data")
LO, HI = 2019, 2024
MIN_AGE = 1.0


def rows():
    md = {n["id"]: (n.get("metadata") or {})
          for n in json.load(open(os.path.join(DATA, "datasets.json")))["datasets"]}
    out = []
    for r in fold.load()["rows"]:
        if r["dl_yr"] is None or r["age"] < MIN_AGE:
            continue
        v = md.get(r["id"], {}).get("tasksCompleted")
        t = [str(x).strip().lower() for x in v] if isinstance(v, list) else (
            [str(v).strip().lower()] if v else [])
        yr = int(r["pub"][:4])
        if not t or not (LO <= yr <= HI):
            continue
        out.append(dict(r, tasks=t, yr=yr, mod=modality.modality(r),
                        rest=any("rest" in x for x in t)))
    return out


def perm(a, b, iters=20000, seed=5):
    rng = random.Random(seed)
    obs = statistics.median(b) - statistics.median(a)
    pool, n, h = list(a) + list(b), len(a), 0
    for _ in range(iters):
        rng.shuffle(pool)
        if abs(statistics.median(pool[n:]) - statistics.median(pool[:n])) >= abs(obs):
            h += 1
    return obs, (h + 1) / (iters + 1)


def strata(rs, min_task=40, min_rest=12):
    by = collections.defaultdict(lambda: {"task": [], "rest": []})
    for r in rs:
        by[r["mod"]]["rest" if r["rest"] else "task"].append(r)
    out = []
    for m, g in by.items():
        if len(g["task"]) >= min_task and len(g["rest"]) >= min_rest:
            a = [x["dl_yr"] for x in g["task"]]
            b = [x["dl_yr"] for x in g["rest"]]
            _, p = perm(a, b)
            # the archive is a lottery: verify a median is not standing on one winner
            a2 = [x["dl_yr"] for x in sorted(g["task"], key=lambda r: -r["downloads"])[2:]]
            b2 = [x["dl_yr"] for x in sorted(g["rest"], key=lambda r: -r["downloads"])[2:]]
            out.append({
                "mod": m, "task": g["task"], "rest": g["rest"],
                "med_t": statistics.median(a), "med_r": statistics.median(b),
                "ratio": statistics.median(b) / statistics.median(a), "p": p,
                "robust": statistics.median(b2) / statistics.median(a2),
                "top_share": max(x["downloads"] for x in g["rest"])
                             / sum(x["downloads"] for x in g["rest"])})
    return sorted(out, key=lambda s: -len(s["task"]))


def dose(rs):
    """Is 'contains rest' really 'runs more paradigms'? Scored on task-only datasets, where
    rest cannot be the explanation."""
    # a never-downloaded dataset has no log. It stays in every median on this plate --
    # it is the real bottom of the distribution -- and is dropped only here, where the
    # correlation needs a log. An earlier pass dropped it everywhere via a falsy test.
    all_t = [r for r in rs if not r["rest"]]
    to = [r for r in all_t if r["dl_yr"] > 0]
    x = [math.log10(len(r["tasks"])) for r in to]
    y = [math.log10(r["dl_yr"]) for r in to]
    n = len(to)
    mx, my = sum(x) / n, sum(y) / n
    sx = sum((a - mx) ** 2 for a in x) ** .5
    sy = sum((b - my) ** 2 for b in y) ** .5
    r = sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)
    return {"n": n, "dropped": len(all_t) - n, "r": r,
            "t": r * math.sqrt(n - 2) / math.sqrt(1 - r * r)}


def threeway(rs, mod="mri"):
    out = {}
    for k, pick in (("rest only", lambda t: all("rest" in x for x in t)),
                    ("rest + task", lambda t: any("rest" in x for x in t)
                                              and not all("rest" in x for x in t)),
                    ("task only", lambda t: not any("rest" in x for x in t))):
        g = [r for r in rs if r["mod"] == mod and pick(r["tasks"])]
        if g:
            out[k] = {"n": len(g), "med": statistics.median(x["dl_yr"] for x in g)}
    return out


def main():
    rs = rows()
    print(f"\n  {len(rs)} datasets published {LO}-{HI} listing at least one paradigm\n")
    print(f"  {'modality':<7}{'task n':>8}{'task':>8}{'rest n':>8}{'rest':>8}"
          f"{'ratio':>8}{'p':>9}{'drop top2':>11}")
    for s in strata(rs):
        print(f"  {modality.NICE.get(s['mod'], s['mod']):<7}{len(s['task']):>8}"
              f"{s['med_t']:>8.1f}{len(s['rest']):>8}{s['med_r']:>8.1f}"
              f"{s['ratio']:>7.2f}x{s['p']:>9.4f}{s['robust']:>10.2f}x")
    d = dose(rs)
    print(f"\n  dose check: among {d['n']} task-only datasets ({d['dropped']} with zero "
          f"downloads dropped, no log), corr(log paradigms, log dl/yr) = {d['r']:+.3f}, "
          f"t = {d['t']:+.2f}")
    print("\n  three-way inside MRI:")
    for k, v in threeway(rs).items():
        print(f"    {k:<12}n={v['n']:>4}  median {v['med']:>6.1f} dl/yr")
    return 0


if __name__ == "__main__":
    sys.exit(main())
