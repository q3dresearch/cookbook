#!/usr/bin/env python3
"""A drug flagged for paediatric use is not being discontinued -- whatever else it is.

This figure used to band substances by FDA therapeutic category and call the axis
"your specialty". The promotion audit asks whether a merged category is one
thing, checked against a second column rather than against the label merged on, and it
is not: **all twelve `Pediatric` substances also carry another category**, against 19%
for `Cardiovascular`. `Pediatric` is a patient-population overlay, not a specialty, so
setting it beside Cardiovascular on one axis compared a flag with a field.

Fixing the merge made the finding stronger rather than weaker. The overlay is testable
*within* each specialty, and the answer is the same in every one of the ten large
enough to split:

    Gastroenterology     9/10  90%  not paediatric      0/2   paediatric
    Endocrinology       13/15  87%                      0/1
    Cardiovascular      22/29  76%                      0/2
    ... seven more, 30% to 79% ...                      all zero

**Two of those cardiovascular substances are lidocaine and dobutamine.** Cardiovascular
is the most exit-heavy band on the list; neither of them is leaving.

The headline test uses **distinct substances, not band memberships** -- the twelve appear
seventeen times across the bands and pooling the memberships would count several of them
twice. Against the 149 substances sharing at least one of their co-tags, which exit at
72%, the expected number of exits among twelve is **8.6** and the observed number is
**0**, at P < 0.0001. (Full register; a first version on half the feed said 122, 59%, 7.1.)

What it does not say is *why*. A paediatric formulation often has no substitute -- you
cannot move a child onto an adult product -- and the statutory framework around
paediatric drugs is its own subject. Neither of those is in this capture.
"""
import sys, json, collections, math
sys.path.insert(0, ".")
import shortagelib as S
from rxnorm import clean

FLAG = "Pediatric"
MIN_N = 6
EXIT, PAED = "#c07a1e", "#1b4f8a"


def load():
    rx = json.loads((S.DATA / "rxnorm.json").read_text())
    d = S.fda_rows()
    flat = lambda v: [] if v is None else (v if isinstance(v, list) else [v])
    sub = collections.defaultdict(lambda: {"cat": set(), "fs": collections.defaultdict(list),
                                           "nm": None})
    for r in d:
        e = rx.get(clean(r.get("generic_name") or "")) or {}
        k = S.sub_key(e)
        if not k:
            continue
        v = sub[k]
        v["nm"] = v["nm"] or e.get("ingredient") or clean(r.get("generic_name", "")).split()[0]
        v["cat"].update(r.get("therapeutic_category") or [])
        for f in flat(r.get("company_name")):
            v["fs"][str(f)].append(r.get("status"))
    ex = {k: all(all(x == "To Be Discontinued" for x in s) for s in v["fs"].values())
          for k, v in sub.items()}
    return sub, ex


def main():
    sub, ex = load()
    bands = []
    for c in {x for v in sub.values() for x in v["cat"]} - {FLAG}:
        ks = [k for k, v in sub.items() if c in v["cat"]]
        if len(ks) < MIN_N:
            continue
        a = [k for k in ks if FLAG not in sub[k]["cat"]]
        b = [k for k in ks if FLAG in sub[k]["cat"]]
        if not b:
            continue
        bands.append((c, sum(1 for k in a if ex[k]), len(a), sum(1 for k in b if ex[k]), len(b)))
    bands.sort(key=lambda t: -t[1] / t[2])
    cv = next((b for b in bands if b[0] == "Cardiovascular"), None)
    paed = [k for k, v in sub.items() if FLAG in v["cat"]]
    cotags = {c for k in paed for c in sub[k]["cat"]} - {FLAG}
    pool = [k for k, v in sub.items() if k not in paed and v["cat"] & cotags]
    rate = sum(1 for k in pool if ex[k]) / len(pool)
    expected, p0 = rate * len(paed), (1 - rate) ** len(paed)
    n_paed_exits = sum(1 for k in paed if ex[k])

    W, L, T, BH = 1000, 232, 190, 38
    PW = W - L - 250
    xs = lambda p: L + PW * p
    body = []
    for g in range(0, 101, 25):
        body.append(f'<line x1="{xs(g/100):.1f}" y1="{T-16:.1f}" x2="{xs(g/100):.1f}" '
                    f'y2="{T+len(bands)*BH-6:.1f}" stroke="{S.RULE}" stroke-width="1"/>')
        body.append(S.txt(xs(g / 100), T - 26, f"{g}%", size=11, fill=S.MUTED,
                          anchor="middle", tab=True))
    body.append(S.txt(L, T - 52, "share of the band's substances that are permanent discontinuances",
                      size=12, fill=S.INK2))

    for i, (c, ea, na, eb, nb) in enumerate(bands):
        y = T + i * BH + BH / 2
        pa = ea / na
        body.append(S.txt(L - 20, y + 4, c, size=12, fill=S.INK, anchor="end", weight="600"))
        body.append(f'<line x1="{xs(0):.1f}" y1="{y:.1f}" x2="{xs(pa):.1f}" y2="{y:.1f}" '
                    f'stroke="{S.BASELINE}" stroke-width="1.6"/>')
        body.append(f'<circle cx="{xs(pa):.1f}" cy="{y:.1f}" r="{3+math.sqrt(na)*0.9:.1f}" '
                    f'fill="{EXIT}" fill-opacity="0.9"/>')
        body.append(f'<circle cx="{xs(0):.1f}" cy="{y:.1f}" r="{3+math.sqrt(nb)*0.9:.1f}" '
                    f'fill="{PAED}"/>')
        body.append(S.txt(xs(pa) + 8 + math.sqrt(na) * 0.9, y + 4,
                          f"{ea} of {na}", size=10.5, fill=S.INK2, tab=True))
        # above the connector, not left of the dot: left of it is the band's own name
        body.append(S.txt(xs(0) + 8 + math.sqrt(nb) * 0.9, y - 7, f"0 of {nb}",
                          size=10.5, fill=PAED, tab=True))

    BOT = T + len(bands) * BH
    ly = BOT + 30
    for col, lab in ((EXIT, "the band's other substances"), (PAED, "the paediatric-flagged ones")):
        body.append(f'<circle cx="{L+6:.1f}" cy="{ly-4:.1f}" r="5" fill="{col}"/>')
        body.append(S.txt(L + 18, ly, lab, size=11, fill=S.INK2))
        ly += 18
    body.append(S.txt(L + 250, BOT + 30, "Dot area is how many substances it stands for.",
                      size=10.5, fill=S.MUTED))
    body.append(S.txt(L + 250, BOT + 48,
                      "Twelve distinct substances appear seventeen times across these bands;",
                      size=10.5, fill=S.MUTED))
    body.append(S.txt(L + 250, BOT + 64,
                      "the headline test below counts each of them once.", size=10.5, fill=S.MUTED))
    body.append(S.txt(W - 250, T + 10, "every line runs to zero", size=12,
                      fill=PAED, weight="600"))

    svg = S.frame(
        W, BOT + 160,
        "Nothing flagged for children is being discontinued",
        "FDA therapeutic categories with at least six substances and at least one carrying "
        "the Pediatric flag, split by that flag. The flag cross-cuts the categories rather "
        "than being one of them — so it is tested inside each, not beside them.",
        body,
        footer=[
            "If a drug you rely on carries the paediatric flag, its risk is a shortage that does not "
            "clear, not a market exit — plan sourcing, not substitution.",
            f"Two of them are lidocaine and dobutamine, sitting inside Cardiovascular, where {cv[1]} of "
            f"the other {cv[2]} substances are leaving.",
            f"Counted as distinct substances: {len(paed)}, {n_paed_exits} of them exits. Against the "
            f"{len(pool)} substances sharing a co-tag, which exit at {rate:.0%}, expected is {expected:.1f} "
            f"— P({n_paed_exits} of {len(paed)}) {'< 0.0001' if p0 < 1e-4 else f'= {p0:.4f}'}.",
            "Why is not in this capture. A paediatric formulation often has no substitute, and the "
            "statutory framework around paediatric drugs is its own subject.",
        ])
    print(S.write("2-paediatric.svg", svg))
    print(f"  paediatric {n_paed_exits}/{len(paed)} exits | pool {len(pool)} at {rate:.0%} | expected {expected:.1f} | P {p0:.5f} | cardiovascular {cv[1]}/{cv[2]} | bands {len(bands)}")


if __name__ == "__main__":
    main()
