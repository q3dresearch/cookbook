#!/usr/bin/env python3
"""Datasets joined to the NIH award that funded them, at the only grain that means anything.

    python3 costjoin.py

Not a chart. `chart-2-cost.py` reads this.

**Only single-project research grants count.** A first pass summed every activity code and got
$1,017.7m, of which $112.1m was one CTSA -- an award to a whole Clinical and Translational
Science Institute -- and $48.4m was a program project returning 123 rows because RePORTER
emits one per sub-project per year. Those fund buildings and cores, not a study, and
attributing them to a dataset is not an upper bound, it is a category error.

    kept    R01 R21 R37 R56 RF1 R00 R03 R15 K01 K08 K23 K25 K99 DP1 DP2
    dropped P01 P20 P30 P41 U01 U19 U24 UL1 UG3 UH2 UH3 T32 S10 ZIA ZIC F31 F32

After the filter: **82 projects, $246.7m, median $2.54m across a median five fiscal years.**

**It is still an upper bound and is labelled as one everywhere.** An R01 funds staff, analysis,
papers and students as well as scanning; the deposited dataset is one output. What the number
supports is a comparison between datasets, where the same overstatement applies to each.

**Three datasets spell it `RO1` with a letter O.** Those resolve to nothing in RePORTER. The
parser accepts the typo and rewrites it, because losing three real grants to a keyboard slip
is a worse error than the one it risks.
"""
import collections, json, os, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
sys.path.insert(0, HERE)
import fold, modality                                                    # noqa: E402

SINGLE = {"R01", "R21", "R37", "R56", "RF1", "R00", "R03", "R15",
          "K01", "K08", "K23", "K25", "K99", "DP1", "DP2"}
PAT = re.compile(r"\b([A-Z]{1,3}\d{0,2})[-\s]?([A-Z]{2})[-\s]?(\d{6})\b")


def fix_typo(text):
    """RO1 -> R01. A letter O where a zero belongs, in three datasets."""
    return re.sub(r"\bR([O])(\d)", lambda m: "R0" + m.group(2), str(text).upper())


def core_numbers(text):
    out = []
    for act, ic, serial in PAT.findall(fix_typo(text)):
        out.append(f"{act}{ic}{serial}")
    return list(dict.fromkeys(out))


def rows():
    raw = json.load(open(os.path.join(DATA, "datasets.json")))["datasets"]
    gr = json.load(open(os.path.join(DATA, "grants.json")))["project"]
    meta = {n["id"]: (n.get("metadata") or {}) for n in raw}
    base = {r["id"]: r for r in fold.load()["rows"]}
    out = []
    for did, m in meta.items():
        r = base.get(did)
        if not r or r["dl_yr"] is None:
            continue
        cns = [c for c in core_numbers(m.get("grantIdentifier") or "")
               if re.match(r"^([A-Z]{1,3}\d{0,2})", c).group(1) in SINGLE]
        awards = {c: gr.get(c) for c in cns if gr.get(c)}
        if not awards:
            continue
        total = sum(y["amount"] for v in awards.values() for y in v)
        yrs = max(len(v) for v in awards.values())
        out.append(dict(r, mod=modality.modality(r), cores=list(awards),
                        award=total, fy=yrs,
                        org=next(iter(awards.values()))[0].get("org"),
                        ic=next(iter(awards.values()))[0].get("ic"),
                        title=next(iter(awards.values()))[0].get("title"),
                        per_dl=(total / r["downloads"]) if r["downloads"] else None,
                        per_subj=(total / r["subjects"]) if r["subjects"] else None))
    return out


def funnel():
    """Every stage of the join, counted, so a caption cannot quietly go stale.

    The hardcoded stage counts in a figure's footnote drifted from 89 to 86 when the
    single-project restriction was tightened, and nothing caught it. These are computed.
    """
    raw = json.load(open(os.path.join(DATA, "datasets.json")))["datasets"]
    named = [n for n in raw if (n.get("metadata") or {}).get("grantIdentifier")]
    parsed = [n for n in named
              if core_numbers((n.get("metadata") or {})["grantIdentifier"])]
    return {"total": len(raw), "named": len(named), "parsed": len(parsed),
            "joined": len(rows())}


def main():
    rs = rows()
    f = funnel()
    print(f"\n  funnel: {f['total']:,} datasets -> {f['named']} name a grant -> "
          f"{f['parsed']} carry a parseable core number -> {f['joined']} join to a "
          f"single-project award")
    print(f"\n  {len(rs)} datasets joined to a single-project NIH award")
    aw = sorted(r["award"] for r in rs)
    print(f"  award behind a dataset: median ${statistics.median(aw):,.0f}  "
          f"p10 ${aw[len(aw)//10]:,.0f}  p90 ${aw[-len(aw)//10]:,.0f}")
    dl = [r for r in rs if r["per_dl"]]
    pd_ = sorted(r["per_dl"] for r in dl)
    print(f"\n  AWARD PER DOWNLOAD (an upper bound, {len(dl)} datasets)")
    print(f"    median ${statistics.median(pd_):,.0f}   p10 ${pd_[len(pd_)//10]:,.0f}   "
          f"p90 ${pd_[-len(pd_)//10]:,.0f}   max ${pd_[-1]:,.0f}")
    ps = sorted(r["per_subj"] for r in rs if r["per_subj"])
    print(f"  award per subject scanned: median ${statistics.median(ps):,.0f}   "
          f"p10 ${ps[len(ps)//10]:,.0f}   p90 ${ps[-len(ps)//10]:,.0f}")
    by = collections.defaultdict(list)
    for r in rs:
        by[r["mod"]].append(r)
    print(f"\n  {'modality':<10}{'n':>4}{'median award':>15}{'median subj':>13}"
          f"{'$/subject':>12}{'$/download':>13}")
    for k, g in sorted(by.items(), key=lambda t: -len(t[1])):
        p = [x["per_dl"] for x in g if x["per_dl"]]
        s = [x["per_subj"] for x in g if x["per_subj"]]
        print(f"  {modality.NICE.get(k,k):<10}{len(g):>4}"
              f"{statistics.median(x['award'] for x in g):>15,.0f}"
              f"{statistics.median(x['subjects'] for x in g):>13,.0f}"
              f"{(statistics.median(s) if s else 0):>12,.0f}"
              f"{(statistics.median(p) if p else 0):>13,.0f}")
    print(f"\n  most-downloaded per dollar:")
    for r in sorted(dl, key=lambda r: r["per_dl"])[:5]:
        print(f"    {r['id']}  ${r['per_dl']:>8,.0f}/download  "
              f"{r['downloads']:>6,} downloads  ${r['award']/1e6:>5,.1f}m  "
              f"{modality.NICE.get(r['mod'],r['mod'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
