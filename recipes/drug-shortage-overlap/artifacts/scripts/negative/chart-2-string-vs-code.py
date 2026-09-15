#!/usr/bin/env python3
"""What a string join gets wrong, measured against a substance code.

The first version of this recipe joined three national registers on a normalised
**name stem** and reported eighteen substances short in all three. Resolving every name
to an RxNorm **ingredient** code instead gives nineteen, and the two lists disagree in
both directions. The disagreements are the finding, because each kind is structural
rather than unlucky.

**A string key cannot find a drug that two countries spell differently on purpose.**

    rxcui 52582   US "Mesalamine"   FR "mésalazine"    AU "mesalazine"
    rxcui  9384   US "Rifampin"     FR "rifampicine"   AU "rifampicin"

Those are United States Adopted Names against International Nonproprietary Names --
the same divergence as acetaminophen and paracetamol, or albuterol and salbutamol. The
stems are `mesalamin` against `mesalazin` and `rifampin` against `rifampicin`. **No
amount of stemming bridges an `m` to a `z`.** Both are genuine three-country shortages
and both went unreported.

**And a string key merges molecules that happen to share a word.**

    US   insulin lispro          rxcui  86009
    FR   insulin glargine        rxcui 274783
    AU   insulin, regular human  rxcui 253182

All three countries are short of insulin. They are short of three different insulins.
The string join called that one shared substance and it is not one.

**The near-miss worth recording.** A first pass at the code join reported fourteen and
appeared to catch five string errors. Four of those were the *cleaner*, not the string
key: `Lamotrigine Tablet, Extended Release` reduced to `lamotrigine extended release`,
failed to resolve, and looked exactly like a drug the United States has no shortage of.
An unresolved name and an absent drug are the same shape, which is the same trap the
ANSM parser fell into earlier in this recipe.

**Coverage is the honest limit.** RxNav is an English vocabulary applied to three
national registers, and it places 82% of names. The rest are unresolved, not absent.
"""
import sys, json
import pathlib as _p; sys.path.insert(0, str(_p.Path(__file__).resolve().parent.parent))  # shortagelib lives one level up
import shortagelib as S
from rxnorm import clean

CACHE = S.DATA / "rxnorm.json"


def main():
    regs = S.registers()
    rx = json.loads(CACHE.read_text())
    codes, unres, tot = {}, 0, 0
    for c, d in regs.items():
        m = {}
        for n, _ in d["rows"]:
            tot += 1
            e = rx.get(clean(n)) or {}
            if e.get("rxcui"):
                m.setdefault(e["rxcui"], (e.get("ingredient") or clean(n), n))
            else:
                unres += 1
        codes[c] = m
    sets = {c: set(v) for c, v in codes.items()}
    code_tri = set.intersection(*sets.values())
    stem_tri, _ = S.shared(regs)

    stem_of_code = {}
    for k in code_tri:
        stem_of_code[k] = {S.stem(codes[c][k][1]) for c in codes}
    agreed = {k for k in code_tri if stem_of_code[k] & set(stem_tri)}
    only_code = sorted(code_tri - agreed, key=lambda k: codes["US"][k][0])
    only_stem = sorted(set(stem_tri) - {s for k in agreed for s in stem_of_code[k]})

    W, T = 1020, 262
    RH = 22
    H = (T - 60) + 2*70 + len(only_code)*38 + len(only_stem)*40 + 132
    body = []
    for i, (lab, n, col, sub) in enumerate((
            ("STRING STEM", len(stem_tri), S.MUTED, "normalised name"),
            ("RxNORM INGREDIENT", len(code_tri), S.COOL, "substance code"),
            ("THEY AGREE ON", len(agreed), S.INK, "both keys find these"),
            ("REGISTER ROWS PLACED", f"{(tot-unres)*100//tot}%", S.MUTED, f"{tot-unres} of {tot} rows"))):
        x = 40 + i*250
        body.append(S.txt(x, T-152, lab, size=11, fill=col, weight="600"))
        body.append(S.txt(x, T-126, f"{n}", size=30, fill=col, weight="600", tab=True))
        body.append(S.txt(x, T-106, sub, size=10.5, fill=S.MUTED))

    y = T - 60
    for title, note, items, col, kind in (
            ("THE CODE FINDS THESE AND THE STRING CANNOT", 
             "United States Adopted Name against International Nonproprietary Name — no stemming bridges these",
             only_code, S.COOL, "code"),
            ("THE STRING CLAIMED THIS AND THE CODE SPLITS IT",
             "one word, three different molecules — all three countries are short of insulin, and of three different insulins",
             only_stem, S.HOT, "stem")):
        body.append(S.txt(28, y, title, size=12, fill=col, weight="600"))
        body.append(S.txt(28, y+15, note, size=10, fill=S.MUTED))
        body.append(f'<line x1="28" y1="{y+24:.1f}" x2="{W-28}" y2="{y+24:.1f}" '
                    f'stroke="{S.RULE}" stroke-width="1"/>')
        y += 46
        if kind == "code":
            for k in items:
                body.append(S.txt(40, y+4, codes["US"][k][0], size=12.5, fill=S.INK, weight="600"))
                body.append(S.txt(210, y+4, f"rxcui {k}", size=10.5, fill=col, tab=True))
                for j, c in enumerate(("US", "FR", "AU")):
                    body.append(S.txt(330 + j*230, y+4, codes[c][k][1][:28], size=11, fill=S.COUNTRY[c]))
                st = sorted(stem_of_code[k])
                body.append(S.txt(40, y+19, "stems: " + "  vs  ".join(st), size=9.5, fill=S.HOT))
                y += RH + 16
        else:
            for st in items:
                body.append(S.txt(40, y+4, st, size=12.5, fill=S.INK, weight="600"))
                for j, c in enumerate(("US", "FR", "AU")):
                    hit = [(k, v) for k, v in codes[c].items() if S.stem(v[1]) == st]
                    if hit:
                        k, v = hit[0]
                        body.append(S.txt(330 + j*230, y+4, v[1][:26], size=11, fill=S.COUNTRY[c]))
                        body.append(S.txt(330 + j*230, y+18, f"rxcui {k}", size=9.5, fill=S.HOT, tab=True))
                y += RH + 18
        y += 24

    foot = [f"Two keys on the same three registers: a normalised name stem finds {len(stem_tri)}, an RxNorm "
            f"ingredient code finds {len(code_tri)}, and they agree on {len(agreed)}.",
            "The code wins where countries spell a molecule differently by convention, and where one word covers "
            "several molecules. Neither case is reachable by a better regular expression.",
            "A first pass reported 14 and looked like it caught five string errors. Four were the "
            "CLEANER: 'Lamotrigine Tablet, Extended Release' failed to resolve and looked absent.",
            f"RxNav places {(tot-unres)*100//tot}% of register rows and 82% of distinct names; the "
            "rest are unresolved, not absent.",
            "Combination products roll up to one ingredient, which is the code key's own "
            "over-merging — Q11, and the resolver has since been fixed to keep the full set."]
    print(S.write("negative/2-string-vs-code.svg", S.frame(
        W, H, "A name is not a molecule, and the difference is measurable",
        "The same three registers joined twice — on a normalised name stem, and on an RxNorm ingredient code — "
        "with every case where the two disagree.", body, foot, chars=132)))


main()
