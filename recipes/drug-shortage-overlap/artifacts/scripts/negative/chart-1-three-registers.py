#!/usr/bin/env python3
"""Nineteen substances are short in the United States, France and Australia at once.

Three regulators publish what is currently in short supply, independently, in three
incompatible formats. If a shortage were a national procurement failure the three lists
would barely intersect. **Eighteen substances appear on all three**, and reading the
list matters more than counting it: four are cytotoxics, five are anaesthesia and
seizure drugs, and almost every one is an old off-patent generic, most of them
injectable.

That is the signature of a supply chain rather than of three health systems failing
separately. Cheap sterile injectables are made by a small number of plants, and a
problem at one is a problem everywhere at once. A procurement failure would be national
and would not show up in Canberra, Paris and Washington in the same week.

**The join is a substance code, not a name.** Every register name is resolved through
RxNav to an RxNorm *ingredient* code, so `Dexamethasone Sodium Phosphate Injection`,
`dexaméthasone (phosphate sodique de)` and `dexamethasone sodium phosphate` all become
rxcui 3264. The names are still printed on every row so a reader can check the match
rather than trust it.

**An earlier version of this chart joined on a normalised name stem and got a
different list.** `2-string-vs-code` measures the difference: the string key missed
mesalamine and rifampin, because the United States writes `Rifampin` where France
writes `rifampicine`, and it wrongly merged three different insulins because they
share a word. Neither failure is reachable by a better regular expression.

**Counts are not comparable across registers and only the overlap is.** FDA records one
row per package NDC, ANSM and TGA per product, so 148 against 437 is a difference in
what a row means before it is a difference in how short a country is.

**One capture each, all taken 2026-09-10.** This is a cross-section. Whether the overlap
is growing needs the twelve months that `wss-drug-scarcity` was built to accumulate.
"""
import sys, collections
import pathlib as _p; sys.path.insert(0, str(_p.Path(__file__).resolve().parent.parent))  # shortagelib lives one level up
import shortagelib as S

WORD = {16: "Sixteen", 17: "Seventeen", 18: "Eighteen", 19: "Nineteen", 20: "Twenty"}

CLASS = {
    "cytotoxic and its antiemetic": ["bendamustine", "gemcitabine", "ifosfamide",
                                     "methotrexate", "aprepitant"],
    "anaesthesia, sedation, seizure": ["midazolam", "phenobarbital", "valproate",
                                       "lamotrigine", "methylphenidate"],
    "corticosteroid": ["dexamethasone", "methylprednisolone"],
    "cardiovascular": ["diltiazem", "metoprolol"],
    "anti-infective": ["clindamycin", "rifampin"],
    "other essentials": ["desmopressin", "hydroxocobalamin", "mesalamine"],
}
LOOSE = {}


def main():
    regs = S.registers()
    codes, cd = S.shared_coded(regs)
    sets = {c: set(cd[c]) for c in cd}
    # key the display on the ingredient NAME so the classes below stay readable
    names = collections.defaultdict(dict)
    ing = {}
    for k in codes:
        ing[k] = cd["US"][k][0]
        for c in cd:
            names[ing[k]][c] = cd[c][k][1]
    placed = [s for v in CLASS.values() for s in v]
    tri = sorted((ing[k] for k in codes),
                 key=lambda s: (placed.index(s) if s in placed else 99, s))

    RH, W, L, T = 24, 1060, 236, 282
    H = T + RH*(len(tri) + len(CLASS)) + 150
    body = []

    # ---- set structure, stated as numbers rather than drawn as areas
    bx, bw = 40, 250
    body.append(S.txt(bx, T-168, "WHAT EACH REGISTER HOLDS", size=11, fill=S.INK, weight="600"))
    for i, (c, lab) in enumerate((("US", "FDA · United States"), ("FR", "ANSM · France"),
                                  ("AU", "TGA · Australia"))):
        y = T - 148 + i*20
        body.append(S.txt(bx, y, lab, size=11, fill=S.COUNTRY[c]))
        body.append(S.txt(bx+200, y, f"{len(sets[c])}", size=11, fill=S.COUNTRY[c],
                          anchor="end", weight="600", tab=True))
    body.append(S.txt(bx+430, T-168, "AND WHAT THEY SHARE", size=11, fill=S.INK, weight="600"))
    pairs = [("US", "FR"), ("US", "AU"), ("FR", "AU")]
    for i, (a, b) in enumerate(pairs):
        y = T - 148 + i*20
        body.append(S.txt(bx+430, y, f"{a} and {b}", size=11, fill=S.INK2))
        body.append(S.txt(bx+560, y, f"{len(sets[a] & sets[b])}", size=11, fill=S.INK2,
                          anchor="end", weight="600", tab=True))
    body.append(S.txt(bx+430, T-148+3*20+4, "all three", size=12, fill=S.HOT, weight="600"))
    body.append(S.txt(bx+560, T-148+3*20+4, f"{len(tri)}", size=13, fill=S.HOT,
                      anchor="end", weight="600", tab=True))
    body.append(S.txt(bx+600, T-148+3*20+4,
                      f"of {len(set().union(*sets.values()))} distinct ingredients across all three",
                      size=10, fill=S.MUTED))

    # ---- the nineteen, named in every register
    for c, x in (("US", L+18), ("FR", L+300), ("AU", L+580)):
        body.append(S.txt(x, T-16, {"US": "FDA (United States)", "FR": "ANSM (France)",
                                    "AU": "TGA (Australia)"}[c], size=10.5,
                          fill=S.COUNTRY[c], weight="600"))
    y = T
    for cls, members in CLASS.items():
        ms = [s for s in tri if s in members]
        if not ms: continue
        body.append(S.txt(28, y+12, cls.upper(), size=10.5, fill=S.MUTED, weight="600"))
        body.append(f'<line x1="28" y1="{y+18:.1f}" x2="{W-28}" y2="{y+18:.1f}" '
                    f'stroke="{S.RULE}" stroke-width="1"/>')
        y += RH
        for st in ms:
            loose = st in LOOSE
            body.append(S.txt(L-18, y+4, st, size=11.5, anchor="end",
                              fill=S.MUTED if loose else S.INK, weight="600"))
            for c, x in (("US", L+18), ("FR", L+300), ("AU", L+580)):
                body.append(S.txt(x, y+4, (names[st].get(c) or "")[:33], size=10,
                                  fill=S.MUTED if loose else S.INK2))
            if loose:
                body.append(S.txt(L-18, y+15, LOOSE[st][:44], size=8.5, fill=S.HOT, anchor="end"))
            y += RH
        y += 6

    foot = [f"{len(tri)} substances on all three registers, from one capture of each taken 2026-09-10. "
            f"Four cytotoxics, five anaesthesia and seizure drugs, and otherwise the cheapest drugs in the formulary.",
            "The join is an RxNorm ingredient code, not a name — so salt forms collapse and the French "
            "'rifampicine' meets the American 'Rifampin'. The names are printed so it can be checked.",
            "A name-stem join gets this wrong in both directions — see 2-string-vs-code. It misses mesalamine "
            "and rifampin, and it merges three different insulins into one.",
            "Register totals are NOT comparable — FDA records per package NDC, ANSM and TGA per product. Only the "
            "overlap is.",
            "One capture each, taken 2026-09-10, so this is a cross-section and cannot say whether the overlap is "
            "growing."]
    print(S.write("negative/1-three-registers.svg", S.frame(
        W, H, f"{WORD.get(len(tri), len(tri))} drugs are short in three countries at once",
        "Every substance appearing on the United States, French and Australian shortage registers simultaneously, "
        "with the name each regulator gives it.", body, foot, chars=132)))


main()
