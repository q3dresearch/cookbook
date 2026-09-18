#!/usr/bin/env python3
"""Survival and substance by place, with the confounder checked before the geography.

    python3 location.py

Order matters here and it is the order of the questions file, not the order of interest.

**Question 4 runs first** because it can explain away the other three. `Accounts.Account
Category` is a legal-threshold size proxy: DORMANT, NO ACCOUNTS FILED, MICRO ENTITY, and
up. If survival depends on it — and a region's mix of company types differs — then a map
of survival by place is partly a map of company types, and drawing it first would be the
same mistake the landfill recipe made three times before learning to condition on the
variable that spans the range.

**Question 3 runs second.** A registered office is an address on a form. WC2H 9JQ holds
17,657 companies; the top ten postcodes hold 5.7% of the register. Those are formation
agents and they are removed and reported separately rather than averaged in.

**Question 1 is the one nobody else publishes.** ONS counts enterprises -- VAT or PAYE
registered, things that trade or employ -- and Companies House counts companies. The share
of a place's companies filing as DORMANT is the gap between those two populations,
measured on one side, without needing to match ONS geography.

**A first version of question 1 counted `NO ACCOUNTS FILED` as well, and it was wrong.**
That category is an age artefact: **99.9% of companies incorporated in 2024 carry it,
92.8% of 2023, and 2 to 5% of anything incorporated before 2022** -- first accounts are
simply not due yet. Combining it with DORMANT produced a measure of how many recent
incorporations an area had, dressed as a measure of substance, and it put Guernsey, Jersey
and the Isle of Man at the top with "95% not real businesses". They are nothing of the
kind: 78 to 89% of their companies were incorporated in 2020 or later. Everything below
is restricted to companies incorporated in 2021 or earlier, which have had time to file.

**Question 2 is the control.** ONS publishes five-year survival by region. If the
register-derived ordering by area does not agree with it, this is measuring where
accountants are and the honest output is a paragraph, not a map.

A death here is a disappearance: present in the 2024 snapshot, absent from the 2026 one.
That is a two-year window and it is all three snapshots can support.
"""
import collections, csv, gzip, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("FSB_DATA") or os.path.join(HERE, "..", "data")
AGENT_TOP = 40          # postcodes held out as formation agents
MIN_AREA = 2000         # a postcode area needs this many companies to be reported
DORMANT = {"DORMANT"}          # NOT "NO ACCOUNTS FILED": see the docstring, it is an age proxy
MATURE_BY = 2021               # incorporated by this year, so first accounts were due
# ONS Business Demography 2024, table 4.1: five-year survival of the 2019 birth cohort.
ONS_REGION = {"North East": 38.9, "North West": 36.6, "Yorkshire and The Humber": 40.1,
              "East Midlands": 38.5, "West Midlands": 30.6, "East": 40.4, "London": 38.2,
              "South East": 40.2, "South West": 43.5, "Wales": 38.1, "Scotland": 39.3,
              "Northern Ireland": 42.8}
# Postcode areas to ONS regions. Only areas that sit unambiguously inside one region are
# mapped; the rest are left out of the control rather than guessed across a boundary.
AREA_REGION = {
    "NE": "North East", "DH": "North East", "SR": "North East", "TS": "North East",
    "M": "North West", "L": "North West", "BL": "North West", "OL": "North West",
    "PR": "North West", "WA": "North West", "WN": "North West", "CH": "North West",
    "BB": "North West", "FY": "North West", "LA": "North West", "CA": "North West",
    "LS": "Yorkshire and The Humber", "BD": "Yorkshire and The Humber",
    "HD": "Yorkshire and The Humber", "HX": "Yorkshire and The Humber",
    "WF": "Yorkshire and The Humber", "S": "Yorkshire and The Humber",
    "HU": "Yorkshire and The Humber", "DN": "Yorkshire and The Humber",
    "YO": "Yorkshire and The Humber", "HG": "Yorkshire and The Humber",
    "NG": "East Midlands", "DE": "East Midlands", "LE": "East Midlands",
    "LN": "East Midlands", "NN": "East Midlands",
    "B": "West Midlands", "CV": "West Midlands", "DY": "West Midlands",
    "WS": "West Midlands", "WV": "West Midlands", "ST": "West Midlands",
    "TF": "West Midlands", "WR": "West Midlands", "HR": "West Midlands",
    "CB": "East", "CM": "East", "CO": "East", "IP": "East", "NR": "East",
    "SG": "East", "SS": "East", "AL": "East", "LU": "East", "PE": "East",
    "E": "London", "EC": "London", "N": "London", "NW": "London", "SE": "London",
    "SW": "London", "W": "London", "WC": "London",
    "BN": "South East", "CT": "South East", "GU": "South East", "ME": "South East",
    "MK": "South East", "OX": "South East", "PO": "South East", "RG": "South East",
    "RH": "South East", "SL": "South East", "SO": "South East", "TN": "South East",
    "BA": "South West", "BH": "South West", "BS": "South West", "DT": "South West",
    "EX": "South West", "GL": "South West", "PL": "South West", "SN": "South West",
    "SP": "South West", "TA": "South West", "TQ": "South West", "TR": "South West",
    "CF": "Wales", "SA": "Wales", "NP": "Wales", "LD": "Wales", "LL": "Wales", "SY": "Wales",
    "AB": "Scotland", "DD": "Scotland", "DG": "Scotland", "EH": "Scotland",
    "FK": "Scotland", "G": "Scotland", "IV": "Scotland", "KA": "Scotland",
    "KW": "Scotland", "KY": "Scotland", "ML": "Scotland", "PA": "Scotland",
    "PH": "Scotland", "TD": "Scotland", "ZE": "Scotland", "HS": "Scotland",
    "BT": "Northern Ireland",
}


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


def read(path):
    with gzip.open(path, "rt", newline="") as f:
        yield from csv.DictReader(f)


def main():
    alive26 = set()
    for r in read(os.path.join(DATA, "geo-2026-09-01.csv.gz")):
        alive26.add(r["number"])
    print(f"  2026 snapshot: {len(alive26):,} live companies")

    pc = collections.Counter()
    for r in read(os.path.join(DATA, "geo-2024-09-01.csv.gz")):
        if r["postcode"]:
            pc[r["postcode"]] += 1
    agents = {p for p, _ in pc.most_common(AGENT_TOP)}
    print(f"  holding out the {AGENT_TOP} busiest postcodes as formation agents: "
          f"{sum(pc[p] for p in agents):,} companies ({sum(pc[p] for p in agents)/sum(pc.values()):.1%})")
    print(f"    busiest: " + ", ".join(f"{p} {pc[p]:,}" for p, _ in pc.most_common(3)) + "\n")

    acct = collections.defaultdict(lambda: [0, 0])
    age = collections.defaultdict(lambda: [0, 0])          # incorporation year -> n, unfiled
    area = collections.defaultdict(lambda: [0, 0, 0, 0])   # n, survived, dormant, agent
    total = [0, 0]
    for r in read(os.path.join(DATA, "geo-2024-09-01.csv.gz")):
        surv = r["number"] in alive26
        a = (r["accounts"] or "").strip().upper()
        acct[a][0] += 1
        acct[a][1] += surv
        total[0] += 1
        total[1] += surv
        y = (r["incorp"] or "")[:4]
        if y.isdigit():
            age[int(y)][0] += 1
            age[int(y)][1] += a == "NO ACCOUNTS FILED"
        ar = r["area"]
        if not ar:
            continue
        if r["postcode"] in agents:
            area[ar][3] += 1
            continue
        if not (y.isdigit() and int(y) <= MATURE_BY):
            continue
        area[ar][0] += 1
        area[ar][1] += surv
        area[ar][2] += a in DORMANT

    print("== 4 (first, because it can explain the rest): does company type predict survival? ==")
    print(f"  {'account category':<30}{'n':>11}{'2yr survival':>14}")
    for k, (n, s) in sorted(acct.items(), key=lambda kv: -kv[1][0])[:8]:
        print(f"  {(k or '(blank)'):<30}{n:>11,}{s/n:>14.1%}")
    print(f"  {'ALL':<30}{total[0]:>11,}{total[1]/total[0]:>14.1%}")
    d = [k for k in acct if k in DORMANT]
    nd = sum(acct[k][0] for k in d)
    sd = sum(acct[k][1] for k in d)
    print(f"\n  dormant or never filed: {nd:,} companies, {sd/nd:.1%} survive two years")
    print(f"  everything else:        {total[0]-nd:,} companies, "
          f"{(total[1]-sd)/(total[0]-nd):.1%}")
    print("  -> a region's survival is partly its mix of company types. Held in mind below.\n")

    print("  and NO ACCOUNTS FILED is an age artefact, not a kind of company:")
    for y in (2024, 2023, 2022, 2021, 2019, 2015):
        if age[y][0]:
            print(f"    incorporated {y}: {age[y][1]/age[y][0]:>6.1%} have filed no accounts "
                  f"(n={age[y][0]:,})")
    print(f"  -> only companies incorporated {MATURE_BY} or earlier are used below.\n")

    rows = [(a, v) for a, v in area.items() if v[0] >= MIN_AREA]
    rows.sort(key=lambda t: -t[1][2] / t[1][0])
    print(f"== 1: where are companies least likely to be businesses? ==")
    print(f"  {len(rows)} postcode areas with {MIN_AREA:,}+ non-agent companies "
          f"incorporated by {MATURE_BY}")
    print(f"  {'area':<7}{'region':<26}{'n':>10}{'dormant':>17}{'2yr survival':>14}")
    for a, v in rows[:5] + rows[-5:]:
        print(f"  {a:<7}{AREA_REGION.get(a,'—'):<26}{v[0]:>10,}{v[2]/v[0]:>17.1%}{v[1]/v[0]:>14.1%}")
    allrows = [v for _, v in rows]
    print(f"  {'ALL':<33}{sum(v[0] for v in allrows):>10,}"
          f"{sum(v[2] for v in allrows)/sum(v[0] for v in allrows):>17.1%}"
          f"{sum(v[1] for v in allrows)/sum(v[0] for v in allrows):>14.1%}\n")

    print("== 2 (the control): does area survival agree with the ONS regional series? ==")
    # Same basket as the charted version: areas below MIN_AREA are excluded here too,
    # or the recipe quotes two different rho for the same control.
    reg = collections.defaultdict(lambda: [0, 0])
    for a, v in area.items():
        r = AREA_REGION.get(a)
        if r and v[0] >= MIN_AREA:
            reg[r][0] += v[0]
            reg[r][1] += v[1]
    keys = [k for k in ONS_REGION if k in reg and reg[k][0] > 0]
    mine = [reg[k][1] / reg[k][0] * 100 for k in keys]
    theirs = [ONS_REGION[k] for k in keys]
    rho = spearman(mine, theirs)
    print(f"  {'region':<26}{'register 2yr':>14}{'ONS 5yr (2019)':>17}")
    for k in sorted(keys, key=lambda k: -ONS_REGION[k]):
        print(f"  {k:<26}{reg[k][1]/reg[k][0]:>14.1%}{ONS_REGION[k]:>16.1f}%")
    print(f"\n  Spearman rho = {rho:+.3f} across {len(keys)} regions")
    print("  These measure different things — two years of all companies against five years")
    print("  of enterprises — so only the ORDERING is comparable, and that is the test.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
