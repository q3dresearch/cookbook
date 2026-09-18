#!/usr/bin/env python3
"""Check this recipe against the official series, which is the first thing to do with it.

    python3 compare_ons.py

The register counts every company, including the dormant shells that never traded. The
Office for National Statistics counts ENTERPRISES -- units registered for VAT or PAYE --
which excludes most of those shells and includes sole traders that are not companies at
all. So the two measure different populations, and **this recipe's survival should come
out BELOW the official one**. If it does not, the method is wrong and everything built
on it inherits that.

Two further differences push the other way and are worth holding in mind:

  * ONS counts a death when a unit stops being VAT or PAYE active. A company can stop
    trading years before Companies House strikes it off, so register deaths LAG
    enterprise deaths, which on its own would make this recipe's survival look higher.
  * ONS follows a true birth cohort. This recipe builds a synthetic one from
    age-specific hazards measured over 2024-2026, so the two are not the same years.

The test is therefore directional and ordinal, not a numeric match: the level should sit
below, and the ranking of industries should broadly agree. Agreement of ordering across
two populations, two death definitions and two periods is worth more than a level match.
"""
import json, os, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlsxlite

DATA = os.environ.get("FSB_DATA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
XLSX = os.path.join(DATA, "ons-business-demography-2024.xlsx")
COHORT = "2019"          # the only birth year in the 2024 release old enough for 5-year survival

# ONS broad industry group -> this recipe's SIC section(s). Several ONS groups are
# subdivisions of one SIC section, so they are summed on counts, never averaged on
# percentages: a mean of three percentages weights a tiny group like a huge one.
MAP = {
    "Production": ["Manufacturing", "Mining", "Utilities", "Water & waste"],
    "Construction": ["Construction"],
    "Motor trades": ["Retail & wholesale"],
    "Wholesale": ["Retail & wholesale"],
    "Retail": ["Retail & wholesale"],
    "Transport and storage (inc postal)": ["Transport"],
    "Accommodation and food services": ["Hospitality"],
    "Information and communication": ["Information & communication"],
    "Finance and insurance": ["Finance & insurance"],
    "Property": ["Real estate"],
    "Professional, scientific and technical": ["Professional & scientific"],
    "Business administration and support services": ["Administrative & support"],
    "Education": ["Education"],
    "Health": ["Health & social work"],
    "Arts, entertainment, recreation and other services": ["Arts & recreation", "Other services"],
}


def read_ons():
    # stdlib reader rather than openpyxl, so this recipe needs nothing installed. Verified
    # cell by cell against openpyxl on this workbook: 89 rows, no disagreement.
    rows_ = list(xlsxlite.load_workbook(XLSX).rows("Table 4.2"))
    rows, year = {}, None
    for r in rows_:
        v = [x for x in r]
        if not v or v[0] is None:
            continue
        head = str(v[0]).strip()
        if head.isdigit() and len(head) == 4:
            year = head
            continue
        if year != COHORT or head in ("Total",):
            if year == COHORT and head == "Total":
                rows["__total__"] = (float(v[1]), float(v[10]))
            continue
        # Column 10 is the 5-year survivor COUNT; column 11 is the same as a percentage.
        # A first version read column 11 as the count and divided it by births, which
        # reported the whole United Kingdom at 0.0% survival and was obviously wrong --
        # obvious only because the number was absurd, which is not a check.
        try:
            births, surv5 = float(v[1]), float(v[10])
        except (TypeError, ValueError):
            continue
        rows[head] = (births, surv5)
    return rows


def main():
    ons = read_ons()
    mine = json.load(open(os.path.join(DATA, "survival.json")))
    curves = {k: v for k, v in mine["curves"].items()}
    five = {k: next(p["survival"] for p in v if p["age"] == 5) for k, v in curves.items()}
    all5 = next(s["survival_to_end"] for s in mine["survival"] if s["band"] == "3-5")

    tb, ts = ons["__total__"]
    print(f"== the headline check ==")
    print(f"  ONS, enterprises born {COHORT}, alive after 5 years: {ts/tb:.1%}  ({ts:,.0f} of {tb:,.0f})")
    print(f"  this recipe, companies on the register at age 5:     {all5:.1%}")
    print(f"  the register sits {ts/tb - all5:+.1%} relative to the official series")
    print("  Lower is the predicted direction: the register counts shells that never traded.")

    # collapse ONS groups onto this recipe's sections, on COUNTS
    agg = collections.defaultdict(lambda: [0.0, 0.0])
    for g, (b, s) in ons.items():
        if g.startswith("__"):
            continue
        secs = MAP.get(g) or next((v for k, v in MAP.items()
                                   if g.lower().startswith(k.split(" (")[0].lower()[:18])), None)
        if not secs:
            print(f"  !! unmapped ONS group, skipped: {g}")
            continue
        share = 1 / len(secs)
        for sec in secs:
            agg[sec][0] += b * share
            agg[sec][1] += s * share

    pairs = []
    print(f"\n== by industry, 5-year survival ==")
    print(f"  {'sector':<30}{'ONS':>8}{'register':>10}{'gap':>8}{'ONS births':>12}")
    for sec in sorted(agg, key=lambda s: -(agg[s][1] / agg[s][0])):
        b, s = agg[sec]
        if sec not in five or b < 3000:
            continue
        o, m = s / b, five[sec]
        pairs.append((o, m, sec))
        print(f"  {sec:<30}{o:>8.1%}{m:>10.1%}{m-o:>+8.1%}{b:>12,.0f}")

    below = sum(1 for o, m, _ in pairs if m < o)
    print(f"\n  the register is below the official figure in {below} of {len(pairs)} sectors")

    def spearman(xs, ys):
        def rank(v):
            order = sorted(range(len(v)), key=lambda i: v[i])
            r = [0.0] * len(v)
            i = 0
            while i < len(order):
                j = i
                while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                    j += 1
                for t in range(i, j + 1):
                    r[order[t]] = (i + j) / 2 + 1
                i = j + 1
            return r
        a, b_ = rank(xs), rank(ys)
        n = len(xs)
        ma, mb = sum(a) / n, sum(b_) / n
        num = sum((x - ma) * (y - mb) for x, y in zip(a, b_))
        den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b_)) ** 0.5
        return num / den if den else float("nan")

    rho = spearman([p[0] for p in pairs], [p[1] for p in pairs])
    print(f"  rank correlation between the two orderings: rho = {rho:+.2f} on {len(pairs)} sectors")
    print("  Two populations, two definitions of death, two periods. Ordering is the thing")
    print("  that should agree; the level is not expected to.")

    json.dump({"cohort": COHORT, "ons_total_5yr": ts / tb, "register_5yr": all5,
               "sectors": [{"sector": s, "ons": o, "register": m} for o, m, s in pairs],
               "rank_correlation": rho, "below_count": below, "n_sectors": len(pairs)},
              open(os.path.join(DATA, "ons_compare.json"), "w"), indent=1)
    print(f"\n  wrote {os.path.join(DATA, 'ons_compare.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
