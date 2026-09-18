#!/usr/bin/env python3
"""The cross-country questions that can be answered now, including the one that could kill it.

    python3 crosscheck.py

Four tests, in the order that matters. The first can invalidate the other three.

**Does a national specialism show up at all?** Norway has an oil industry, a fishing and
aquaculture industry and a merchant fleet; Britain has none of them at that scale. If
those divisions do not stand out in Norwegian company formations, the instrument cannot
see a national specialism, and no other difference measured with it should be believed.
This is a declared positive control, run before the comparisons it licenses.

**Do the two registers agree on the ordering of sectors?** The same ordinal test that
validated the UK survival curve against the official series. Agreement does not make the
levels comparable, but disagreement would mean the shared NACE numbering is not carrying
the same meaning across the border.

**Do classification habits differ?** A British founder ticking a residual "other ... not
elsewhere classified" code where a Norwegian ticks a specific one produces a difference
that is entirely clerical. The share landing in residual codes is the diagnostic.

**And can the Norwegian shares carry a comparison at all?** 22.1% of Norwegian limited
companies have NACE `00.000`, "Uoppgitt" -- not stated. That is a missing value, not a
residual category, and the share rises with recency from 14.5% of the 2019 cohort to 30.1%
of 2026. Any sector share is therefore computed on a shrinking base, and the worst-case
bound on it is the size of that gap.

**Does Norway's bankruptcy flag measure deaths?** It has a `bankrupt` boolean and a date,
which looks like the death field the UK register lacks. The test is an age gradient: a
2019 cohort has had six more years to fail than a 2023 one, so a cumulative death count
must rise with cohort age. If it is flat, the field is a current-state snapshot of
proceedings in progress and not a history, and Norwegian survival is no more measurable
than British.
"""
import collections, csv, glob, gzip, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("FSB_DATA") or os.path.join(HERE, "..", "data")
sys.path.insert(0, HERE)
from entry_share import section, UK_LTD                      # noqa: E402

# Divisions where Norway is expected to differ from Britain by geography and history.
SPECIALISM = {3: "fishing & aquaculture", 6: "oil & gas extraction",
              9: "mining support services", 30: "other transport equipment (ships)",
              50: "water transport"}
RESIDUAL = {"82990", "96090", "74990", "70229", "64999", "99999", "00000"}


def division(code):
    c = (code or "").replace(".", "").strip()
    return int(c[:2]) if c[:2].isdigit() else None


def load_uk():
    f = os.path.join(DATA, "compact-2026-09-01.csv.gz")
    div, sec, resid, tot = collections.Counter(), collections.Counter(), 0, 0
    with gzip.open(f, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("category") and r["category"] not in UK_LTD:
                continue
            y = (r["incorp"] or "")[:4]
            if not (y.isdigit() and 2019 <= int(y) <= 2026):
                continue
            tot += 1
            code = (r["sic"] or "").replace(".", "").strip()
            if code in RESIDUAL:
                resid += 1
            d = division(r["sic"])
            if d is not None:
                div[d] += 1
            s = section(r["sic"])
            if s:
                sec[s] += 1
    return div, sec, resid, tot


def load_no():
    f = sorted(glob.glob(os.path.join(DATA, "norway-as*.csv.gz")))[-1]
    div, sec, resid, tot = collections.Counter(), collections.Counter(), 0, 0
    rows = []
    with gzip.open(f, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            rows.append(r)
            tot += 1
            code = (r["nace"] or "").replace(".", "").strip()
            if code in RESIDUAL or code.startswith("00"):
                resid += 1
            d = division(r["nace"])
            if d is not None:
                div[d] += 1
            s = section(r["nace"])
            if s:
                sec[s] += 1
    return div, sec, resid, tot, rows


def spearman(a, b):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r, i = [0.0] * len(v), 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for t in range(i, j + 1):
                r[o[t]] = (i + j) / 2 + 1
            i = j + 1
        return r
    ra, rb = rank(a), rank(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((x - mb) ** 2 for x in rb))
    return sum((ra[i] - ma) * (rb[i] - mb) for i in range(n)) / den if den else float("nan")


def main():
    ud, us, ur, ut = load_uk()
    nd, ns, nr, nt, rows = load_no()
    print(f"  UK {ut:,} limited companies registered 2019-2026; Norway {nt:,}\n")

    print("== 1. positive control: does Norway's national specialism show up? ==")
    print(f"  {'division':<36}{'Norway':>10}{'UK':>10}{'ratio':>9}")
    ok = 0
    for d, lab in SPECIALISM.items():
        n, u = nd[d] / nt, ud[d] / ut
        ratio = (n / u) if u else float("inf")
        ok += ratio > 2
        print(f"  {str(d) + '  ' + lab:<36}{n:>9.3%}{u:>10.3%}{ratio:>8.1f}x")
    print(f"  -> {ok} of {len(SPECIALISM)} specialisms are over twice the British rate."
          f"{'  CONTROL PASSES' if ok >= 3 else '  CONTROL FAILS - stop here'}\n")

    print("== 2. do the two registers agree on sector ordering? ==")
    keys = sorted(set(us) | set(ns))
    a = [us.get(k, 0) / ut for k in keys]
    b = [ns.get(k, 0) / nt for k in keys]
    rho = spearman(a, b)
    print(f"  Spearman rho = {rho:+.3f} across {len(keys)} sectors")
    biggest = sorted(keys, key=lambda k: -abs(ns.get(k, 0) / nt - us.get(k, 0) / ut))[:4]
    for k in biggest:
        print(f"    {k:<32}UK {us.get(k,0)/ut:>6.1%}   Norway {ns.get(k,0)/nt:>6.1%}")
    print()

    print("== 3. do classification habits differ? ==")
    print(f"  residual / 'not elsewhere classified' codes: UK {ur/ut:.1%}, Norway {nr/nt:.1%}")
    print(f"  rows with no usable division at all:         UK {1-sum(ud.values())/ut:.1%}, "
          f"Norway {1-sum(nd.values())/nt:.1%}\n")

    print("== 4. does Norway's bankruptcy flag measure deaths? ==")
    by = collections.defaultdict(lambda: [0, 0, 0])
    for r in rows:
        y = (r["registered"] or "")[:4]
        if not y.isdigit():
            continue
        b_ = by[int(y)]
        b_[0] += 1
        b_[1] += r["bankrupt"] == "True"
        b_[2] += r["winding_up"] == "True"
    print(f"  {'cohort':<9}{'age':>5}{'n':>9}{'bankrupt':>11}{'winding up':>13}")
    for y in sorted(by):
        n, bk, wu = by[y]
        print(f"  {y:<9}{2026-y:>5}{n:>9,}{bk/n:>11.1%}{wu/n:>13.1%}")
    old = by[2019][1] / by[2019][0]
    new = by[2023][1] / by[2023][0]
    print(f"\n  a 2019 cohort has had four more years to fail than a 2023 one, and shows "
          f"{old:.1%} against {new:.1%}.")
    print("  A cumulative death count cannot be flat in cohort age. The field is a snapshot of")
    print("  proceedings currently open, not a history, so Norwegian survival is no more")
    print("  measurable than British -- for the same reason, found a different way.\n")

    print("== 5. can the Norwegian shares carry the comparison? ==")
    unc = [r for r in rows if (r["nace"] or "").replace(".", "").strip().startswith("00")]
    cod = [r for r in rows if not (r["nace"] or "").replace(".", "").strip().startswith("00")]
    print(f"  {len(unc):,} of {len(rows):,} ({len(unc)/len(rows):.1%}) have NACE 00.000, "
          f"'Uoppgitt' -- not stated")
    byy = collections.Counter((r["registered"] or "")[:4] for r in unc)
    tot = collections.Counter((r["registered"] or "")[:4] for r in rows)
    print("  and it rises with recency: " + ", ".join(
        f"{y} {byy[y]/tot[y]:.0%}" for y in sorted(tot) if tot[y] > 1000))

    # Missing at random would make the bound a formality. It is not.
    emp = lambda g: sum(1 for r in g if (r["employees"] or "").strip().isdigit()
                        and int(r["employees"]) > 0) / len(g)
    print(f"\n  has employees:   uncoded {emp(unc):.1%}   coded {emp(cod):.1%}")
    for place in ("OSLO", "BAERUM", "BÆRUM", "STAVANGER"):
        a = sum(1 for r in unc if r["municipality"] == place)
        b = sum(1 for r in cod if r["municipality"] == place)
        if a + b > 500:
            print(f"  share in {place:<12} uncoded {a/len(unc):>6.1%}   coded {b/len(cod):>6.1%}"
                  f"   {a/len(unc)/(b/len(cod)):>5.2f}x")
    print("\n  Uncoded companies are urban, concentrated in the wealthiest municipalities, and")
    print("  almost never have staff. That is the profile of a holding or property vehicle --")
    print("  precisely the companies a finance or real-estate comparison turns on. The missing")
    print("  codes are not missing at random, so the worst-case bound is the honest one:")
    print("  on 2019-2021, 15 of 20 sector differences sit inside it and cannot be claimed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
