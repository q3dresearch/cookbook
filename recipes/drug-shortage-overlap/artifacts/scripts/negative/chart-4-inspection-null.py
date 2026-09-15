#!/usr/bin/env python3
"""Shortage firms are not inspected worse than anybody else. A null worth keeping.

The obvious explanation for a drug shortage is a firm with compliance problems, and it
is testable: the FDA publishes every drug inspection it has run since 2009 with an
outcome code -- **NAI** no action, **VAI** voluntary action, **OAI** official action,
which is the serious one. Pool all of it, key it to the firms reporting shortages, and
compare against every other inspected firm.

**They are the same.** Firms short of the nineteen substances short in all three
countries run a 7% OAI rate. All US shortage firms run 6%. The other sixteen thousand
inspected firms run 7%. A shortage is not a compliance story.

**This is the control that makes the rest of the recipe honest.** `3-suppliers` shows
nine of the nineteen short at several independent firms at once, which points upstream.
This rules out the nearest alternative -- that the firms involved are simply worse
operators -- and it does so by running the same measurement on everyone rather than
looking only at the firms of interest.

**The pooling was the whole job, and it nearly went the other way.** A single capture
file holds 1,167 inspection rows and matched only 15% of shortage firms, which looked
like a name-matching failure and would have been reported as one. The fourteen captures
pool to **39,988 rows across fiscal years 2009 to 2026**, and the match rises to 73%.
It was a paginated slice, not a broken join.

**What it does not rule out.** A reporting firm is a marketing company. The inspections
attach to establishments that company owns, which is closer to the plant than
`company_name` but is still not the API supplier two tiers upstream. Note also that
China is the third most-inspected country overall (1,609 drug inspections) and does not
appear among the shortage firms' establishments at all -- consistent with these being
US-facing marketers rather than the upstream manufacturers.
"""
import sys, collections, json
import pathlib as _p; sys.path.insert(0, str(_p.Path(__file__).resolve().parent.parent))  # shortagelib lives one level up
import shortagelib as S
from rxnorm import clean

from inspections import firm, inspections


def main():
    insp, nrows = inspections()
    regs = S.registers()
    codes, cd = S.shared_coded(regs)
    rx = json.loads((S.DATA / "rxnorm.json").read_text())
    sh = S.fda_rows()
    shared_firms, all_short = set(), set()
    for r in sh:
        e = rx.get(clean(r.get("generic_name") or "")) or {}
        f = firm(r.get("company_name"))
        if not f: continue
        all_short.add(f)
        if e.get("rxcui") in set(codes): shared_firms.add(f)

    def prof(fs):
        rows = [r for f in fs for r in insp.get(f, [])
                if (r.get("ProductType") or "") == "Drugs"]
        cls = collections.Counter(r.get("ClassificationCode") for r in rows)
        fei = {r.get("FEINumber") for r in rows}
        cc = collections.Counter(r.get("CountryName") for r in rows)
        return cls, sum(cls.values()), len(fs), len(fei), cc

    groups = [("firms short of the 19 shared substances", *prof(shared_firms)),
              ("all US shortage firms", *prof(all_short)),
              ("every other inspected firm", *prof(set(insp) - all_short))]

    W, L, T = 1000, 300, 250
    RH = 96
    H = T + RH*len(groups) + 120
    pw = W - L - 250
    body = []
    CODE = [("NAI", "no action indicated", S.COOL),
            ("VAI", "voluntary action", S.WARM),
            ("OAI", "OFFICIAL ACTION — the serious one", S.HOT)]
    for g in (0, 25, 50, 75, 100):
        x = L + g/100*pw
        body.append(f'<line x1="{x:.1f}" y1="{T-16:.1f}" x2="{x:.1f}" y2="{T+RH*len(groups)-30:.1f}" '
                    f'stroke="{S.GRID}" stroke-width="1"/>')
        body.append(S.txt(x, T-24, f"{g}%", size=11, fill=S.MUTED, anchor="middle", tab=True))
    body.append(S.txt(L, T-46, "share of that group's drug inspections, by outcome", size=12, fill=S.INK2))
    for i, (code, lab, col) in enumerate(CODE):
        body.append(f'<rect x="{L+i*210}" y="{T-88}" width="11" height="11" rx="2" fill="{col}"/>')
        body.append(S.txt(L+i*210+17, T-78, f"{code} — {lab}", size=10.5,
                          fill=col if code == "OAI" else S.MUTED, weight="600" if code == "OAI" else "normal"))

    for gi, (lab, cls, tot, nf, nfei, cc) in enumerate(groups):
        y = T + RH*gi
        body.append(S.txt(L-18, y+6, lab, size=12, fill=S.INK, anchor="end", weight="600"))
        body.append(S.txt(L-18, y+22, f"{nf:,} firms · {nfei:,} establishments · {tot:,} inspections",
                          size=10, fill=S.MUTED, anchor="end"))
        x = L
        for code, _, col in CODE:
            n = cls.get(code, 0)
            w = n/max(tot, 1)*pw
            body.append(f'<rect x="{x:.1f}" y="{y-6:.1f}" width="{w:.1f}" height="24" '
                        f'fill="{col}" fill-opacity="{0.95 if code=="OAI" else 0.55}"/>')
            if w > 40:
                body.append(S.txt(x + w/2, y+10, f"{n*100//max(tot,1)}%", size=11.5,
                                  fill=S.SURFACE, anchor="middle", weight="600", tab=True))
            x += w
        body.append(S.txt(L+pw+14, y+10, f"OAI {cls.get('OAI',0)*100//max(tot,1)}%", size=12.5,
                          fill=S.HOT, weight="600", tab=True))
        # under the bar, not left of it: right-aligned into the label gutter these ran
        # off the edge of the frame.
        body.append(S.txt(L, y+36, "establishments in: " + ", ".join(f"{c} {n}" for c, n in cc.most_common(5)),
                          size=9.5, fill=S.MUTED))

    foot = [f"Pooled from {nrows:,} drug inspection rows across fiscal years 2009-2026. The serious outcome, OAI, "
            f"runs 7%, 6% and 7% — there is no difference to explain.",
            "This is the control for 3-suppliers: nine of the nineteen are short at several independent firms at "
            "once, and it is not because those firms are worse operators.",
            "A single capture file holds 1,167 rows and matched 15% of shortage firms, which looked like a broken "
            "name join. The 14 captures pool to 73%. It was a paginated slice.",
            "A reporting firm is a marketing company, so these establishments are closer to the "
            "plant than company_name, and still not the API supplier two tiers upstream.",
            "Of 234 establishments behind the 73 matched firms, 61 firms have a US site, 11 an "
            "Indian one and 2 a Chinese one — small, not absent, which is a difference that matters."]
    print(S.write("negative/4-inspection-null.svg", S.frame(
        W, H, "Shortage firms are inspected no worse than anyone else",
        "FDA drug-inspection outcomes for the firms reporting shortages, against every other inspected firm, "
        "pooled across 2009-2026.", body, foot, chars=130)))


main()
