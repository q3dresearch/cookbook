#!/usr/bin/env python3
"""Recompute every number this recipe leans on, and catch a figure that has gone stale.

    python3 verify.py

**Why this exists.** Fourteen figures and a README share the same facts, and a caption that was
right when written goes wrong silently. In the workspace this came from, one figure's caption
said a group held half its shallow share to 50 m; a change of baseline had moved it to 100 m
and the sentence stayed. Nothing catches that except recomputing, and nothing catches a
corrected script whose figure was never rebuilt except comparing timestamps.

If a number here disagrees with the README, **this script is authoritative and the prose is a
bug**, per the repo's own rule.
"""
import collections, glob, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
CHARTS = os.path.join(HERE, "..", "charts")
CLEAN = "ON_LAND,DEPTH_EXCEEDS_BATH,NO_MATCH,NOT_MARINE"


def load(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        raise SystemExit(f"  {name} missing — run fetch.py first")
    return json.load(open(p))


def spearman(a, b):
    def rk(xs):
        order = sorted(range(len(xs)), key=lambda i: xs[i])
        out = [0] * len(xs)
        for p, i in enumerate(order):
            out[i] = p
        return out
    ra, rb, n = rk(a), rk(b), len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** .5
    return num / den if den else 0.0


def main():
    bad = 0
    print("\n  SAMPLING CONCENTRATION")
    g = load("grid3.json")["features"]
    cells = sorted((f["properties"].get("n", 0) for f in g), reverse=True)
    tot = sum(cells)
    print(f"    cells                         {len(cells):,}")
    print(f"    top 27 cells hold             {sum(cells[:27])/tot:.1%}")
    print(f"    cells under 100 records       {sum(1 for c in cells if c < 100)/len(cells):.0%}")
    md = [c for c in load("map-depth.json")["cells"] if c["top_share"] is not None]
    print(f"    median top-dataset share      {statistics.median(c['top_share'] for c in md):.0%}"
          f"   over half one dataset {sum(1 for c in md if c['top_share']>.5)/len(md):.0%}")

    print("\n  DEPTH IS THE INSTRUMENT, FOR PLANTS AND CELLS")
    pr = load("producers.json")
    rows = []
    for k, v in pr.items():
        b = v["depth"]
        t = sum(r["records"] for r in b) or 1
        rows.append({"k": k, "dna": v["dna_share"],
                     "deep": sum(r["records"] for r in b if r["from"] >= 50) / t})
    water = [r for r in rows if r["k"] != "Globothalamea"]
    rho_w = spearman([r["dna"] for r in water], [r["deep"] for r in water])
    rho_a = spearman([r["dna"] for r in rows], [r["deep"] for r in rows])
    print(f"    rho(sequencing share, below 50 m)   {rho_w:+.2f} over {len(water)} water-sampled")
    print(f"    with forams (drill core) added back {rho_a:+.2f}")
    if round(rho_w, 2) != 0.97:
        print("      ^ README says +0.97"); bad += 1

    print("\n  THE LIGHT CLIFF")
    cl = load("cliffs.json")
    G = {x["from"]: x["records"] for x in cl["global"]}
    edges = sorted(G)[:21]
    EXPECT = {"seagrasses": 20, "kelp / brown algae": 30, "red algae": 50, "green algae": 70,
              "sponges": None, "bristle worms": None, "ray-finned fish": None}
    for sci, v in cl["taxa"].items():
        t = {x["from"]: x["records"] for x in v["depth"]}
        base = (sum(t.get(e, 0) for e in edges[:2])
                / max(sum(G[e] for e in edges[:2]), 1)) or 1e-12
        rel = [(t.get(e, 0) / G[e] if G.get(e) else 0) / base for e in edges]
        cross = next((edges[i] for i in range(len(rel)) if all(r < .1 for r in rel[i:])), None)
        want = EXPECT.get(v["common"], "?")
        flag = "" if want == "?" or cross == want else f"   <- README says {want}"
        if flag:
            bad += 1
        print(f"    {v['common']:<20}crosses 10^-1 at {str(cross)+' m':>8}{flag}")

    print("\n  THE FLAGS ARE A HABITAT MAP")
    fl = load("flags.json")
    for c in sorted(fl["classes"], key=lambda c: -c["flags"]["ON_LAND"] / max(c["records"], 1))[:3]:
        n = max(c["records"], 1)
        print(f"    {c['common']:<20}on land {c['flags']['ON_LAND']/n:6.1%}   "
              f"below the sea floor {c['flags']['DEPTH_EXCEEDS_BATH']/n:5.1%}")
    same = sum(1 for c in fl["checks"] if c["cross_raw"] == c["cross_clean"])
    print(f"    crossings unchanged by cleaning     {same} of {len(fl['checks'])}")
    print(f"    top 200 m, raw vs cleaned           {fl['top200_raw']:.1%} -> "
          f"{fl['top200_clean']:.1%}")
    if same != len(fl["checks"]):
        print("      ^ README says all of them"); bad += 1

    print("\n  WHAT THE NEXT HUNDRED SPECIES COST")
    sa = load("saturation.json")
    Y, CUT = sa["years"], sa["cut"]
    ci = Y.index(CUT)

    def _ols(xs, ys):
        n = len(xs); mx, my = sum(xs) / n, sum(ys) / n
        b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (
            sum((x - mx) ** 2 for x in xs) or 1e-9)
        return my - b * mx, b
    under = 0
    for sci, v in sa["classes"].items():
        N, S = v["records"], v["species"]
        Nf, Sf = N[:ci + 1], S[:ci + 1]
        if min(Sf) <= 0:
            continue
        best = None
        for e in [i / 40 for i in range(0, 400)]:
            K = 10 ** e
            x = [n / (n + K) for n in Nf]
            sm = sum(a * b for a, b in zip(Sf, x)) / (sum(a * a for a in x) or 1e-9)
            err = sum((sm * a - b) ** 2 for a, b in zip(x, Sf))
            if best is None or err < best[0]:
                best = (err, sm, K)
        if best[1] * N[-1] / (N[-1] + best[2]) < S[-1]:
            under += 1
    print(f"    saturating fit under-predicts  {under} of {len(sa['classes'])} classes")
    if under != len(sa["classes"]):
        print("      ^ README says all of them"); bad += 1
    price = {}
    for sci, v in sa["classes"].items():
        a, b = _ols([math.log10(n) for n in v["records"]], v["species"])
        if b > 0:
            price[v["common"]] = v["records"][-1] * (10 ** (100 / b) - 1)
    for k in ("sponges", "sea snails", "seabirds"):
        if k in price:
            print(f"    100 more {k:<14}{price[k]:>14,.0f} records")

    print("\n  WHEN EACH CLASS WAS DESCRIBED")
    de = load("described.json")
    agg = collections.Counter()
    for v in de["classes"].values():
        for y, n in v["hist"].items():
            agg[int(y)] += n
    full = {y: n for y, n in agg.items() if y + de["bin"] - 1 <= 2024}
    peak = max(full, key=lambda y: full[y])
    print(f"    species with a year            {sum(full.values()):,}")
    print(f"    busiest bin                    {peak}–{peak+4} at {full[peak]:,}")
    for war in (1915, 1945):
        exp = (full.get(war - 5, 0) + full.get(war + 5, 0)) / 2
        print(f"    {war}–{war+4} against neighbours   {full.get(war,0)/exp-1:+.0%}")
    for k in ("seabirds", "bristle worms"):
        v = next((x for x in de["classes"].values() if x["common"] == k), None)
        if v:
            h = {int(a): b for a, b in v["hist"].items()}
            print(f"    {k:<16}median {v['median']}, "
                  f"{(h.get(2010,0)+h.get(2015,0))/10/max(v['dated'],1)*1000:5.1f} new per "
                  f"year per 1,000 known")

    print("\n  CONCERN FOLLOWS ATTENTION")
    rl = load("redlist.json")
    t, c = rl["threatened"], rl["control"]
    zt = sum(1 for x in t if x["recent"] == 0) / len(t)
    zc = sum(1 for x in c if x["recent"] == 0) / len(c)
    print(f"    threatened unseen 10 yr        {zt:.1%}  (n={len(t):,})")
    print(f"    matched control                {zc:.1%}  (n={len(c):,})")
    if not zt < zc:
        print("      ^ README says threatened are BETTER monitored"); bad += 1
    ex = [x for x in t if x["category"] == "EX"]
    print(f"    listed Extinct, unseen         "
          f"{sum(1 for x in ex if x['recent']==0)/len(ex):.1%}  (n={len(ex)}) — the control")

    print("\n  FOUR OF FIVE CRITERIA OUT OF REACH")
    cb = load("criterionb.json")
    for cat in ("CR", "EN", "VU"):
        v = [x for x in cb["species"] if x["category"] == cat]
        und = [x for x in v if not x["over_b2"]]
        print(f"    {cat}  n={len(v):<4} B2 ruled out "
              f"{sum(1 for x in v if x['over_b2'])/len(v):.0%}   still possible {len(und)}, "
              f"median records {statistics.median([x['records'] for x in und]):,.0f}")

    print("\n  IT SEES FISHING, NOT FARMING")
    at = load("attention.json")
    asp = [x for x in at["species"] if x["datasets"] and x["records"]]
    xs = [math.log10(x["datasets"]) for x in asp]
    ys = [math.log10(x["records"]) for x in asp]
    a, b = _ols(xs, ys)
    sd = statistics.pstdev([q - (a + b * p) for p, q in zip(xs, ys)])
    res = {k: [] for k in (None, "farmed", "wild")}
    for x in asp:
        res[x["control"]].append(
            (math.log10(x["records"]) - (a + b * math.log10(x["datasets"]))) / sd)
    base = statistics.median(res[None])
    for k in ("wild", "farmed"):
        print(f"    {k:<8}n={len(res[k]):<4} vs background "
              f"{statistics.median(res[k])-base:+.2f} sd")
    if statistics.median(res["wild"]) - base < 0.9:
        print("      ^ README says wild-caught ~+1.04 sd"); bad += 1

    print("\n  THE LABEL MOVES BECAUSE KNOWLEDGE MOVES")
    h = load("redlisthistory.json")
    moves = [m for tr in h["transitions"] for m in tr["moves"]]
    T = {"CR", "EN", "VU"}
    into = collections.Counter(m["from"] for m in moves
                               if m["from"] not in T and m["to"] in T)
    zero = [tr for tr in h["transitions"] if tr["changed"] == 0]
    print(f"    category changes               {len(moves):,}")
    print(f"    entered threatened from DD     {into.get('DD',0):,}  (largest single flow in)")
    print(f"    distinct states                {len(h['versions'])-len(zero)} "
          f"from {len(h['versions'])} files")

    print("\n  STALENESS")
    for svg in sorted(glob.glob(os.path.join(CHARTS, "*.svg"))):
        stem = os.path.basename(svg)[:-4]
        cands = [p for p in glob.glob(os.path.join(HERE, "*.py"))
                 if stem in os.path.basename(p)]
        if cands and os.path.getmtime(svg) < max(os.path.getmtime(c) for c in cands):
            print(f"    {stem:<20}FIGURE OLDER THAN ITS SCRIPT"); bad += 1
    print(f"    {len(glob.glob(os.path.join(CHARTS, '*.svg')))} figures checked")

    print(f"\n  {'all numbers agree with the README' if not bad else f'{bad} DISAGREEMENT(S)'}\n")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
