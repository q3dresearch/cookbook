#!/usr/bin/env python3
"""When six independent firms are short of one molecule, the cause is upstream of all six.

The three-register overlap suggests a supply chain rather than three procurement
failures, but suggestion is not measurement. The FDA record carries the reporting firm
on **every one of its 619 rows**, so the question can be asked directly: for each of the
nineteen substances short in all three countries, **how many separate US firms are short
of it at the same time?**

**Nine of the nineteen are short at two or more.** Methylphenidate is short at six
firms simultaneously, methylprednisolone at five. Six companies do not independently
fail at the same molecule in the same month; something they all depend on did. That is
the supply-chain reading, and for these nine it is evidence rather than inference.

**Ten of the nineteen are short at exactly one US firm**, and for those this measurement
cannot tell a supply problem from one company's problem. They are drawn in grey and
counted separately rather than folded into the headline, because a single supplier is
also what a market with one supplier looks like.

**Counting rows would have tripled the concentration.** Hospira appears on 76 shortage
records and makes **24** distinct substances; Fresenius Kabi 69 records and 27
substances. A record is a package NDC, so a firm shipping many pack sizes of one drug
votes many times. Every count here is distinct substances or distinct firms, never rows.

**And this is the US column only.** France and Australia publish no firm at all, so the
supplier count cannot be built for them — a drug short at one US firm might be short at
six French ones and this cannot see it. The overlap is three-country; the supplier
evidence is one-country.
"""
import sys, collections, json
import pathlib as _p; sys.path.insert(0, str(_p.Path(__file__).resolve().parent.parent))  # shortagelib lives one level up
import shortagelib as S
from rxnorm import clean


def main():
    regs = S.registers()
    codes, cd = S.shared_coded(regs)
    rx = json.loads((S.DATA / "rxnorm.json").read_text())
    d = S.fda_rows()

    sub_firm = collections.defaultdict(set)
    firm_sub = collections.defaultdict(set)
    rec = collections.Counter()
    for r in d:
        e = rx.get(clean(r.get("generic_name") or "")) or {}
        k, f = e.get("rxcui"), r.get("company_name")
        if f: rec[f] += 1
        if k and f:
            sub_firm[k].add(f); firm_sub[f].add(k)

    rows = sorted(((len(sub_firm.get(k, ())), cd["US"][k][0], sorted(sub_firm.get(k, ())))
                   for k in codes), key=lambda r: (-r[0], r[1]))
    multi = [r for r in rows if r[0] >= 2]

    RH, W, L, T = 27, 1020, 250, 250
    H = T + RH*len(rows) + 42 + 132
    pw = W - L - 320
    mx = max(r[0] for r in rows) + 1
    sx = lambda v: L + v/mx*pw
    body = []
    for g in range(0, mx + 1):
        body.append(f'<line x1="{sx(g):.1f}" y1="{T-16:.1f}" x2="{sx(g):.1f}" y2="{T+RH*len(rows)-10:.1f}" '
                    f'stroke="{S.GRID}" stroke-width="1"/>')
        body.append(S.txt(sx(g), T-24, g, size=11, fill=S.MUTED, anchor="middle", tab=True))
    body.append(S.txt(L, T-46, "separate US firms short of it at the same time", size=12, fill=S.INK2))

    # the denominator lesson, stated where it applies
    body.append(S.txt(28, T-152, "COUNTING ROWS WOULD HAVE TRIPLED THIS", size=11, fill=S.HOT, weight="600"))
    for i, (f, _) in enumerate(rec.most_common(3)):
        body.append(S.txt(28, T-130 + i*18, f"{f[:34]}", size=10.5, fill=S.MUTED))
        body.append(S.txt(330, T-130 + i*18, f"{rec[f]} records", size=10.5, fill=S.MUTED, anchor="end", tab=True))
        body.append(S.txt(460, T-130 + i*18, f"{len(firm_sub[f])} substances", size=10.5,
                          fill=S.INK2, anchor="end", tab=True))
    body.append(S.txt(560, T-130, "a record is a package NDC, so a firm shipping many", size=10, fill=S.MUTED))
    body.append(S.txt(560, T-114, "pack sizes of one drug votes many times", size=10, fill=S.MUTED))

    y = T
    GAPY = 42          # room for the divider labels, or they land on a row
    for idx, (n, name, firms) in enumerate(rows):
        if idx == len(multi):
            y += GAPY
        col = S.HOT if n >= 2 else S.MUTED
        body.append(S.txt(L-18, y+4, name, size=12, fill=S.INK if n >= 2 else S.MUTED,
                          anchor="end", weight="600" if n >= 2 else "normal"))
        body.append(f'<line x1="{sx(0):.1f}" y1="{y:.1f}" x2="{sx(n):.1f}" y2="{y:.1f}" '
                    f'stroke="{col}" stroke-width="7" stroke-opacity="0.22" stroke-linecap="round"/>')
        for j in range(n):
            body.append(f'<circle cx="{sx(j+0.5):.1f}" cy="{y:.1f}" r="4.2" fill="{col}"/>')
        if n >= 2:
            lbl = ", ".join(x.split(",")[0][:16] for x in firms[:3])
            if len(firms) > 3: lbl += f" +{len(firms)-3}"
            body.append(S.txt(sx(mx)+16, y+4, lbl[:52], size=9.5, fill=S.MUTED))
        y += RH

    ysep = T + RH*len(multi) + GAPY//2 - 6
    body.append(f'<line x1="28" y1="{ysep:.1f}" x2="{W-28}" y2="{ysep:.1f}" '
                f'stroke="{S.INK}" stroke-width="1.3" stroke-dasharray="5 3"/>')
    body.append(S.txt(28, ysep-10, f"{len(multi)} short at two or more US firms — upstream of all of them",
                      size=11, fill=S.HOT, weight="600"))
    body.append(S.txt(28, ysep+18, f"{len(rows)-len(multi)} short at exactly one — this cannot tell a supply "
                      f"problem from one company's", size=11, fill=S.MUTED, weight="600"))

    foot = [f"{len(multi)} of the {len(rows)} substances short in all three countries are short at two or more "
            f"separate US firms at once. Methylphenidate at six, methylprednisolone at five.",
            "Six companies do not independently fail at the same molecule in the same month. For these nine the "
            "supply-chain reading is evidence rather than inference.",
            "The other ten are a single US supplier, which is also what a market with one supplier looks like. "
            "Counted separately, not folded into the headline.",
            "US column only — France and Australia publish no firm at all, so a drug short at one US firm might "
            "be short at six French ones and this cannot see it."]
    print(S.write("negative/3-suppliers.svg", S.frame(
        W, H, "Nine of the nineteen are short at several US firms at once",
        "For each substance short in all three countries, how many separate US firms report a shortage of it "
        "simultaneously.", body, foot, chars=130)))


main()
