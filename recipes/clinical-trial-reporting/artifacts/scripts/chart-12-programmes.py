#!/usr/bin/env python3
"""A drug's phases stop being a sequence as soon as the drug works.

    python3 chart-12-programmes.py

"Do phase 1, 2 and 3 of the same product differ" needs a product key, and this register has
none -- no NDC, no UNII, no ChEMBL id. The only candidate is the free-text intervention name.

**The string join works better than expected.** Normalising DRUG and BIOLOGICAL intervention
names and dropping placebo-like terms gives 132,790 keys; **16,676 span two or more phases and
cover 162,173 trials, 26.9% of the register**. Spot-checked raw, the groups are real:
`cabazitaxel (XRP6258)`, `Cabazitaxel (XRP6258)` and `cabazitaxel` collapse correctly.

**And the semantic is wrong anyway.** The largest groups are cyclophosphamide (2,887 trials
since 1976), cisplatin, carboplatin, dexamethasone. These are not development programmes. They
are backbone agents that appear in other drugs' trials, at every phase, for fifty years.

**The test that settles it.** Within each key, does phase rise with time? A development
programme should: phase 1 first, phase 3 later. Across 7,553 keys with five or more trials the
median correlation is **+0.09** -- essentially none. Cyclophosphamide is **−0.30**. Even
pembrolizumab, first trial 2010, manages only +0.11.

**Because the ordering dissolves on success.** Split keys by how long they have been in the
register and the correlation decays with age: **+0.22** for keys spanning under three years,
+0.25 at four to seven, +0.12 at eight to fourteen, and **−0.01** past fifteen. The share of
keys whose earliest trials are phase 1 falls from **49% to 19%** across the same split. A drug
that works re-enters phase 1 as a combination partner, and its own phase sequence stops being
a sequence.

**So the honest answer is a boundary.** This register can compare phases *in aggregate* --
figure 11 does, and finds phase 2 the slowest. It cannot follow one product through its
phases, because "the same product" in an intervention list means *this molecule appears*, not
*this programme advanced*. The subset where it can is young compounds, and they are the ones
with the fewest trials and the least follow-up.
"""
import collections, csv, datetime, gzip, os, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                            # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID         # noqa: E402

DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(HERE, "..", "charts", "12-programmes.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
PHN = {"PHASE1": 1, "PHASE2": 2, "PHASE3": 3, "PHASE4": 4}
NOISE = re.compile(r"\b(\d+(\.\d+)?\s*(mg|g|mcg|ug|ml|l|iu|units?|%|mg/kg|mg/m2|kg)"
                   r"|tablet|capsule|injection|infusion|solution|oral|iv|im|sc|topical"
                   r"|placebo\s*comparator|active\s*comparator|arm|group|cohort|dose|daily"
                   r"|weekly|bid|qd|tid|once|twice|per\s*day)\b")
STOP = {"placebo", "standard of care", "control", "no intervention", "usual care",
        "saline", "normal saline", "sham", "vehicle", "observation", "none",
        "standard care", "best supportive care", "water", "sham comparator"}
SPANS = [("under 3 years", 0, 4), ("4 to 7", 4, 8), ("8 to 14", 8, 15),
         ("15 or more", 15, 999)]


def norm(s):
    s = s.lower().strip()
    s = re.sub(r"[\(\[].*?[\)\]]", " ", s)
    s = NOISE.sub(" ", s)
    s = re.sub(r"[^a-z0-9\- ]", " ", s)
    return re.sub(r"\s+", " ", s).strip(" -")


def parse(d):
    if not d:
        return None
    try:
        if len(d) == 7:
            return datetime.date(int(d[:4]), int(d[5:7]), 15)
        if len(d) == 10:
            return datetime.date(int(d[:4]), int(d[5:7]), int(d[8:10]))
    except ValueError:
        pass
    return None


def load(n):
    try:
        with gzip.open(os.path.join(DATA, n), "rt", newline="", encoding="utf-8") as f:
            return {r["nct_id"]: r for r in csv.DictReader(f)}
    except EOFError:
        raise SystemExit(f"  {n} is truncated — re-run its fetcher")


def main():
    nm, mn, ex = load("names.csv.gz"), load("studies.csv.gz"), load("extra.csv.gz")
    prod = collections.defaultdict(list)
    for nct, r in nm.items():
        m, e = mn.get(nct), ex.get(nct)
        if not m or not e:
            continue
        st = parse(e["start"])
        ph = PHN.get((m["phases"] or "").split("|")[0])
        if not st or not ph:
            continue
        names = [x for x in (r["names"] or "").split("|") if x]
        types = [x for x in (r["types"] or "").split("|") if x]
        for i, n in enumerate(names):
            if (types[i] if i < len(types) else "") not in ("DRUG", "BIOLOGICAL"):
                continue
            k = norm(n)
            if k and k not in STOP and len(k) >= 3:
                prod[k].append({"y": st.year, "ph": ph})
    keys = []
    for k, v in prod.items():
        if len(v) < 5 or len({x["ph"] for x in v}) < 2:
            continue
        ys = [x["y"] for x in v]
        n = len(v)
        my, mp = sum(ys) / n, sum(x["ph"] for x in v) / n
        den = (sum((x["y"] - my) ** 2 for x in v)
               * sum((x["ph"] - mp) ** 2 for x in v)) ** 0.5
        keys.append({"k": k, "n": n, "span": max(ys) - min(ys), "first": min(ys),
                     "r": (sum((x["y"] - my) * (x["ph"] - mp) for x in v) / den
                           if den else 0.0),
                     "p1": statistics.median([x["ph"] for x in v
                                              if x["y"] <= min(ys) + 1])})
    keys.sort(key=lambda d: -d["n"])
    allr = [d["r"] for d in keys]

    W, H = 1200, 790
    s = plate.open_svg(W, H, "A drug's phases stop being a sequence as soon as the "
                             "drug works")
    fr, _ = plate.frame(W, 62,
                        who="anyone trying to follow one compound through its phases",
                        decide="whether an intervention name is a development programme",
                        wrong="phase rises with time inside the large product keys")
    s += fr

    # ---------- left: the correlation, per key, against how many trials it has
    AX, AY, AH, AW = 28, 176, 420, 620
    x0, pw = AX + 52, AW - 96
    import math
    px = lambda n: x0 + pw * (math.log10(max(n, 5)) / math.log10(3200))
    py = lambda r: AY + AH - 56 - (AH - 90) * ((r + 1) / 2)
    for r_ in (-1, -0.5, 0, 0.5, 1):
        s.append(f'<line x1="{x0:.1f}" y1="{py(r_):.1f}" x2="{px(3200):.1f}" '
                 f'y2="{py(r_):.1f}" stroke="{INK2 if r_ == 0 else GRID}"'
                 + (' stroke-dasharray="4 3"' if r_ == 0 else "") + '/>')
        s.append(txt(x0 - 8, py(r_) + 3, f"{r_:+.1f}" if r_ else "0", size=9, fill=MUTED,
                     anchor="end"))
    s.append(txt(AX, AY - 18, "within a product key, how strongly phase rises with time",
                 size=11, fill=INK2))
    for n_, lab in ((5, "5"), (20, "20"), (100, "100"), (500, "500"), (3000, "3,000")):
        s.append(txt(px(n_), py(-1) + 18, lab, size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, py(-1) + 36, "trials carrying that product name (log scale)",
                 size=10, fill=MUTED))
    for d in keys:
        col = GREEN if d["span"] < 8 else (RED if d["span"] >= 15 else SLATE)
        s.append(f'<circle cx="{px(d["n"]):.1f}" cy="{py(d["r"]):.1f}" r="1.7" '
                 f'fill="{col}" fill-opacity="0.30"/>')
    # these four sit within a few hundredths of each other, so the labels are fanned out
    # with leader lines rather than stacked on top of one another
    NAMED = {"cyclophosphamide": 44, "pembrolizumab": -46, "cisplatin": -18,
             "bevacizumab": 14}
    for d in keys:
        if d["k"] in NAMED:
            cx, cy2 = px(d["n"]), py(d["r"])
            ly2 = cy2 + NAMED[d["k"]]
            s.append(f'<circle cx="{cx:.1f}" cy="{cy2:.1f}" r="4.4" fill="none" '
                     f'stroke="{INK}" stroke-width="1.6"/>')
            s.append(f'<line x1="{cx-5:.1f}" y1="{cy2:.1f}" x2="{cx-14:.1f}" '
                     f'y2="{ly2-3:.1f}" stroke="{MUTED}" stroke-width="0.9"/>')
            s += halo(cx - 18, ly2, f"{d['k']} {d['r']:+.2f}", size=9, fill=INK,
                      anchor="end", weight="700")
    med = statistics.median(allr)
    s.append(f'<line x1="{x0:.1f}" y1="{py(med):.1f}" x2="{px(3200):.1f}" '
             f'y2="{py(med):.1f}" stroke="{AMBER}" stroke-width="1.8"/>')
    s += halo(px(7), py(med) - 8, f"median {med:+.2f} across {len(keys):,} keys",
              size=10, fill=AMBER, weight="700")
    ly = AY + 8
    for col, lab in ((GREEN, "in the register under 8 years"),
                     (SLATE, "8 to 14 years"), (RED, "15 years or more")):
        s.append(f'<circle cx="{x0+14:.1f}" cy="{ly-3.5:.1f}" r="3.6" fill="{col}" '
                 f'fill-opacity="0.55"/>')
        s.append(txt(x0 + 24, ly, lab, size=9.5, fill=INK2))
        ly += 15

    # ---------- right: the decay with age
    BX, BY, BW = 700, 176, 472
    s.append(txt(BX, BY - 18, "phase-versus-time correlation, by how long the key has "
                              "been around", size=11, fill=INK2))
    sx0, spw = BX + 40, BW - 190
    y = BY + 26
    for lab, lo, hi in SPANS:
        S = [d for d in keys if lo <= d["span"] < hi]
        if len(S) < 30:
            continue
        mr = statistics.median([d["r"] for d in S])
        p1 = sum(1 for d in S if d["p1"] <= 1.5) / len(S)
        col = GREEN if mr > 0.18 else (RED if mr < 0.05 else SLATE)
        s.append(txt(BX, y, lab, size=10.5, fill=INK, weight="600"))
        s.append(txt(BX, y + 13, f"{len(S):,} keys · median "
                                 f"{statistics.median([d['n'] for d in S]):.0f} trials",
                     size=9, fill=MUTED))
        zero = sx0 + spw * 0.5
        w = spw * 0.5 * (mr / 0.35)
        s.append(f'<line x1="{zero:.1f}" y1="{y-6:.1f}" x2="{zero:.1f}" y2="{y+30:.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(f'<rect x="{min(zero, zero+w):.1f}" y="{y+18:.1f}" '
                 f'width="{abs(w):.1f}" height="12" fill="{col}" fill-opacity="0.7"/>')
        s += halo(zero + w + (7 if w >= 0 else -7), y + 28, f"{mr:+.2f}", size=10.5,
                  fill=col, weight="700", anchor="start" if w >= 0 else "end")
        s += halo(BX + BW - 6, y + 13, f"{p1:.0%} start at phase 1", size=9.5, fill=col,
                  anchor="end")
        y += 62
    s += wrap(BX, y + 4,
              "A drug that works re-enters phase 1 as a combination partner, so its own "
              "phase sequence stops being a sequence. The ordering is only legible while a "
              "compound is young — and those keys have the fewest trials and the least "
              "follow-up, which is the opposite of where the statistical power is.",
              size=10.5, fill=INK2, chars=62, leading=14)

    ty = AY + AH + 46
    s.append(txt(AX, ty, "the join works; the meaning does not", size=12.5, fill=INK,
                 weight="600"))
    s += wrap(AX, ty + 20,
              "Normalised intervention names give 16,676 keys spanning two or more phases "
              "across 162,173 trials, and spot-checked raw they collapse correctly. But the "
              "largest are cyclophosphamide, cisplatin and carboplatin — backbone agents "
              "appearing in other drugs' trials at every phase for fifty years. This "
              "register can compare phases in aggregate; it cannot follow one product "
              "through its own.",
              size=11, fill=INK2, chars=92, leading=15)

    fy = H - 24 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"ClinicalTrials.gov API v2, fetched 2026-09-22; intervention names from a "
              f"third walk. Keys are DRUG and BIOLOGICAL intervention names, lowercased with "
              f"dose and formulation tokens stripped and placebo-like terms dropped — a "
              f"deliberately shallow rule, because a deeper one starts merging distinct "
              f"molecules. Drawn: the {len(keys):,} keys with at least five trials spanning "
              f"at least two phases. A trial listing several drugs contributes to each, so "
              f"a phase 3 trial of one drug on a standard backbone counts for both.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {len(keys):,} keys, median r {med:+.3f}")
    for lab, lo, hi in SPANS:
        S = [d for d in keys if lo <= d["span"] < hi]
        if len(S) >= 30:
            print(f"    {lab:<14}{len(S):>6,} keys  median r "
                  f"{statistics.median([d['r'] for d in S]):+.2f}  "
                  f"{sum(1 for d in S if d['p1'] <= 1.5)/len(S):.0%} start at phase 1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
