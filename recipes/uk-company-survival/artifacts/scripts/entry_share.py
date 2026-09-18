#!/usr/bin/env python3
"""Who is still starting companies in which sector: the UK against Norway.

    python3 entry_share.py

This is the comparison the survival half cannot make. Survival levels are not comparable
across countries because they are set by filing deadlines and strike-off practice -- the
UK hazard peaks at one to two years because first accounts fall due at twenty-one months,
which is company law rather than economics. Entry has no such problem: a registration is
a registration, and the SHARE of new companies formed in each sector is a statement about
where people think there is a business, in that country, in that year.

It is also the right instrument for the question that prompted this. A sector can lose
most of its output while its surviving firms die at perfectly ordinary rates, because the
survivors are the ones that adapted. What shows a sector emptying out is that nobody
starts one any more.

THE BIAS THIS HAS TO HANDLE. Both registers are snapshots of the LIVING, so a company
born in 2005 only appears if it is still here. Sectors die at different rates -- 17% of
UK retail companies reach five years against 59% of real estate ones -- so old birth
years are not merely thinned, they are thinned UNEVENLY, which is exactly the shape that
manufactures a trend.

Two defences, both reported:

  * The headline comparison uses only the **last five years**, where little has had time
    to die and the distortion is small.
  * The longer UK series is shown with the observed counts **divided by that sector's own
    survival to that age**, reconstructing the births. Norway gets no such correction,
    because this recipe could not measure Norwegian survival, so its long series is shown
    as observed and labelled as such.
"""
import collections, csv, datetime as dt, gzip, json, os, sys

DATA = os.environ.get("FSB_DATA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
THIS_YEAR = 2026
RECENT = 5

SECTION = [(1, 3, "Agriculture"), (5, 9, "Mining"), (10, 33, "Manufacturing"),
           (35, 35, "Utilities"), (36, 39, "Water & waste"), (41, 43, "Construction"),
           (45, 47, "Retail & wholesale"), (49, 53, "Transport"), (55, 56, "Hospitality"),
           (58, 63, "Information & communication"), (64, 66, "Finance & insurance"),
           (68, 68, "Real estate"), (69, 75, "Professional & scientific"),
           (77, 82, "Administrative & support"), (84, 84, "Public administration"),
           (85, 85, "Education"), (86, 88, "Health & social work"),
           (90, 93, "Arts & recreation"), (94, 96, "Other services"),
           (97, 99, "Households & extraterritorial")]


def section(code):
    """UK SIC 2007 and Norwegian NACE share a division numbering, which is the only
    reason this comparison is possible at all."""
    c = (code or "").replace(".", "").strip()
    if not c[:2].isdigit() or c == "99999":
        return None
    d = int(c[:2])
    for lo, hi, name in SECTION:
        if lo <= d <= hi:
            return name
    return None


# Norway's register holds sole traders and associations that Companies House never sees,
# so the Norwegian pull is aksjeselskap only -- the limited company. The UK side has to be
# restricted the same way or the comparison is between two different animals. Companies
# House categories: "Private Limited Company" and its Scottish/NI variants.
UK_LTD = {"Private Limited Company", "PRI/LTD BY GUAR/NSC (Private, limited by guarantee, no share capital)",
          "PRI/LBG/NSC (Private, Limited by guarantee, no share capital, use of 'Limited' exemption)",
          "Private Limited Company by guarantee without share capital, use of 'Limited' exemption"}


def uk(limited_only=True):
    f = os.path.join(DATA, "compact-2026-09-01.csv.gz")
    out = collections.defaultdict(collections.Counter)
    kept = tot = 0
    with gzip.open(f, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            tot += 1
            if limited_only and r.get("category") and r["category"] not in UK_LTD:
                continue
            y = r["incorp"][:4]
            s = section(r["sic"])
            if y.isdigit() and s:
                kept += 1
                out[int(y)][s] += 1
    print(f"  UK: {kept:,} of {tot:,} records used"
          f"{' (limited companies only)' if limited_only else ''}")
    return out


def norway():
    import glob
    cand = sorted(glob.glob(os.path.join(DATA, "norway-as*.csv.gz")))
    if not cand:
        raise SystemExit("  no Norwegian extract yet")
    f = cand[-1]
    out = collections.defaultdict(collections.Counter)
    with gzip.open(f, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            y = (r["registered"] or "")[:4]
            s = section(r["nace"])
            if y.isdigit() and s:
                out[int(y)][s] += 1
    return out


def shares(counts, years):
    tot = collections.Counter()
    for y in years:
        tot.update(counts.get(y, {}))
    n = sum(tot.values())
    return {k: v / n for k, v in tot.items()}, n


def main():
    U, N = uk(), norway()
    years = list(range(THIS_YEAR - RECENT, THIS_YEAR))
    su, nu = shares(U, years)
    sn, nn = shares(N, years)
    print(f"== share of new company registrations by sector, {years[0]}-{years[-1]} ==")
    print(f"   UK {nu:,} companies | Norway {nn:,} limited companies\n")
    print(f"  {'sector':<30}{'UK':>8}{'Norway':>9}{'difference':>13}")
    rows = []
    for s in sorted(set(su) | set(sn), key=lambda s: -(su.get(s, 0))):
        a, b = su.get(s, 0), sn.get(s, 0)
        if max(a, b) < 0.008:
            continue
        rows.append((s, a, b))
        print(f"  {s:<30}{a:>8.1%}{b:>9.1%}{b-a:>+13.1%}")

    print(f"\n== manufacturing's share of new registrations, over time ==")
    print(f"  {'year':<7}{'UK observed':>14}{'UK birth-corrected':>21}{'Norway observed':>18}")
    surv = {}
    try:
        cur = json.load(open(os.path.join(DATA, "survival.json")))["curves"]
        for s, pts in cur.items():
            surv[s] = pts
    except Exception:
        pass

    def corrected(counts, year, sec):
        """Observed survivors divided by that sector's survival to this age."""
        age = THIS_YEAR - year
        pts = surv.get(sec)
        if not pts:
            return None
        f = next((p["survival"] for p in pts if p["age"] >= age), pts[-1]["survival"])
        return counts.get(year, {}).get(sec, 0) / f if f else None

    series = []
    for y in range(1996, THIS_YEAR):
        tu = sum(U.get(y, {}).values())
        tn = sum(N.get(y, {}).values())
        if tu < 500 or tn < 200:
            continue
        mu = U.get(y, {}).get("Manufacturing", 0) / tu
        mn = N.get(y, {}).get("Manufacturing", 0) / tn
        cu_m = corrected(U, y, "Manufacturing")
        cu_t = sum(x for s in SECTION if (x := corrected(U, y, s[2])) is not None)
        cm = (cu_m / cu_t) if (cu_m and cu_t) else None
        series.append({"year": y, "uk": mu, "uk_corrected": cm, "no": mn})
        if y % 3 == 0 or y >= THIS_YEAR - 3:
            print(f"  {y:<7}{mu:>14.2%}{(f'{cm:.2%}' if cm else '—'):>21}{mn:>18.2%}")

    json.dump({"years": years, "uk_n": nu, "norway_n": nn,
               "recent_shares": [{"sector": s, "uk": a, "norway": b} for s, a, b in rows],
               "manufacturing_series": series},
              open(os.path.join(DATA, "entry_share.json"), "w"), indent=1)
    print(f"\n  wrote {os.path.join(DATA, 'entry_share.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
