#!/usr/bin/env python3
"""Every signal this archive was asked for, with its n, its effect in real units, its
control, and whether it survived.

    python sweep.py

A recipe that only reports what worked reports a biased sample of its own work. This
is the whole search: the signals that made it into a figure, the ones that were
tested and failed, and the ones that were merely a size effect. Each block returns
the numbers verify.py checks, so a "failed" here is re-derived rather than remembered.

Verdicts:  KEPT     drives a decision and survived a control -- it has a figure
           WEAK     direction consistent, evidence thin; stated in prose, not drawn
           FAILED   no relationship, or a relationship the control removed
"""
import collections, csv, datetime as dt, json, re, statistics as st, sys, urllib.parse
sys.path.insert(0, ".")
import shortagelib as S
import features as X
import survival as V
from inspections import firm, inspections
from rxnorm import clean

CAPTURE = dt.date(2026, 9, 10)
_D = lambda x: dt.datetime.strptime(x, "%m/%d/%Y").date()


def _rows(src):
    d = json.loads(S._read(S.latest(src)))
    r = d.get("results") or d.get("result") or d.get("data") or d
    if isinstance(r, dict):
        r = next(v for v in r.values() if isinstance(v, list))
    return r


def _key(name, rx):
    return S.sub_key(rx.get(clean(name)) or {})


def _by_substance(rx):
    by = collections.defaultdict(list)
    for r in S.fda_rows():
        k = _key(r["generic_name"], rx)
        if k:
            by[k].append(r)
    return by


# ---------------------------------------------------------------- FDA fields
def fda_fields(F, by):
    """Form, category, application type, reason, availability and age against exit."""
    out = {}
    chronic = [k for k in F if not F[k]["is_exit"]]
    fx = collections.defaultdict(lambda: [0, 0])
    for k in F:
        f = collections.Counter(r.get("dosage_form") or "?" for r in by[k]).most_common(1)[0][0]
        g = "injection" if f == "Injection" else ("oral solid" if f.startswith(("Tablet", "Capsule")) else "other")
        fx[g][0] += 1; fx[g][1] += F[k]["is_exit"]
    out["form"] = dict(fx)
    cx = collections.defaultdict(lambda: [0, 0])
    for k in F:
        for t in {t for r in by[k] for t in (r.get("therapeutic_category") or [])}:
            cx[t][0] += 1; cx[t][1] += F[k]["is_exit"]
    out["category"] = {t: v for t, v in cx.items() if v[0] >= 10}
    ax = collections.defaultdict(lambda: [0, 0])
    for k in F:
        apps = {a[:3] for r in by[k] for a in (r.get("openfda") or {}).get("application_number", [])}
        g = "ANDA only" if apps == {"AND"} else "NDA/BLA only" if apps and "AND" not in apps else "both" if apps else "no openfda"
        ax[g][0] += 1; ax[g][1] += F[k]["is_exit"]
    out["application"] = dict(ax)
    rs = collections.defaultdict(set)
    for k in chronic:
        for r in by[k]:
            if r.get("shortage_reason"):
                rs[r["shortage_reason"]].add(k)
    out["reason"] = {r: (len(ks), round(st.median(F[k]["age_y"] for k in ks), 1)) for r, ks in rs.items()}
    av = collections.Counter()
    for k in chronic:
        cur = [r.get("availability") for r in by[k] if r["status"] == "Current"]
        av["all Available" if all(a == "Available" for a in cur) else
           "all Unavailable" if all(a in ("Unavailable", "Unvailable") for a in cur) else
           "some Unavailable" if any(a in ("Unavailable", "Unvailable") for a in cur) else "Available/Limited"] += 1
    out["availability_of_chronic"] = dict(av)
    ex_age = [F[k]["age_y"] for k in F if F[k]["is_exit"]]
    ch_age = [F[k]["age_y"] for k in chronic]
    out["age"] = {"exits_median_y": round(st.median(ex_age), 1), "exits_over_2y": sum(a > 2 for a in ex_age),
                  "chronic_median_y": round(st.median(ch_age), 1), "chronic_over_2y": sum(a > 2 for a in ch_age),
                  "n_exits": len(ex_age), "n_chronic": len(ch_age)}
    tw = collections.defaultdict(set)
    for r in S.fda_rows():
        tw[(r["generic_name"], r["company_name"], r["package_ndc"])].add(r["status"])
    twins = [k for k, s in tw.items() if {"Current", "To Be Discontinued"} <= s]
    tk = {_key(g, RX) for g, _, _ in twins} - {None}
    out["twins"] = {"packages": len(twins), "substances": len(tk),
                    "on_chronic_substances": sum(1 for k in tk if not F[k]["is_exit"])}
    return out


# ---------------------------------------------------------------- supplier depth
def cohort_depth(by, rx):
    """Drugs@FDA marketed-product counts for the archive's 304-molecule cohort, against
    presence on the shortage list. The 131 'established' members were chosen on product
    count, not on being short, so they are the control group."""
    man = list(csv.DictReader((S.ARCHIVE / "manifest" / "fda.drugsfda.cohort-status" / "2026-09.csv").open()))
    latest = {}
    for r in man:
        m = re.search(r"name%3A%22(.+?)%22", r["url"])
        if not m or not r["raw_ref"]:
            continue
        mol = urllib.parse.unquote(m.group(1))
        if mol not in latest or r["fetched_at"] > latest[mol]["fetched_at"]:
            latest[mol] = r
    counts = {}
    for mol, r in latest.items():
        p = S.ARCHIVE / r["raw_ref"]
        if not p.exists():
            p = p.with_name(p.name + ".gz")
        if not p.exists():
            continue
        counts[mol] = {x["term"]: x["count"] for x in json.loads(S._read(str(p))).get("results", [])}
    import yaml as _y
    coh = _y.safe_load((S.ARCHIVE / "cohorts" / "injectable-generics" / "2026-09-03.yml").read_text())
    path = {m["entity_id"]: m["paths"][0] for m in coh["members"]}
    names = collections.defaultdict(set)
    for r in S.fda_rows():
        names[(r.get("generic_name") or "").upper()].add(r["status"])
        for s in (r.get("openfda") or {}).get("substance_name", []):
            names[s.upper()].add(r["status"])
    def listed(mol):
        return any(n == mol or n.startswith(mol + " ") or mol in n.split(" ") for n in names)
    bins = lambda v: "1-5" if v <= 5 else "6-10" if v <= 10 else "11-20" if v <= 20 else "21+"
    out = {}
    for pth in ("established", "new_entrant"):
        g = collections.defaultdict(lambda: [0, 0])
        for mol, c in counts.items():
            if path.get(mol) != pth:
                continue
            mk = c.get("Prescription", 0) + c.get("Over-the-counter", 0)
            g[bins(mk)][0] += 1; g[bins(mk)][1] += listed(mol)
        out[pth] = {b: g[b] for b in ("1-5", "6-10", "11-20", "21+")}
    return {"molecules": len(counts), **out}


# ---------------------------------------------------------------- enforcement
def enforcement():
    insp, _ = inspections()
    pop = set(insp)
    sf = {firm(r["company_name"]) for r in S.fda_rows()}
    out_ = sf & pop
    first = collections.defaultdict(lambda: dt.date.max)
    for r in S.fda_rows():
        first[firm(r["company_name"])] = min(first[firm(r["company_name"])], _D(r["initial_posting_date"]))
    res = {"inspected_firms": len(pop), "shortage_firms": len(sf), "shortage_firms_inspected": len(out_)}
    # warning letters, FY2022-26
    wl = collections.defaultdict(list)
    for r in _rows("fda.complianceactions.drugs"):
        if r.get("ActionType") == "Warning Letter":
            wl[firm(r.get("LegalName"))].append(r)
    fy = lambda r: int(r.get("FiscalYear") or 0)
    exp = {f for f in pop if any(fy(r) >= 2022 for r in wl.get(f, []))}
    a, c = len(exp & out_), len(out_ - exp)
    before = after = 0
    for f in out_ & exp:
        for r in wl[f]:
            try:
                ad = dt.date.fromisoformat(r["ActionTakenDate"][:10])
            except (ValueError, TypeError):
                continue
            if fy(r) >= 2019:
                before += ad < first[f]; after += ad >= first[f]
    res["warning_letter"] = {"letter_firms": len(exp), "short_given_letter": a, "short_given_none": c,
                             "p_short_letter": round(a / len(exp), 4), "p_short_none": round(c / len(pop - exp), 4),
                             "letters_before_first_listing": before, "letters_after": after}
    # recalls, Jan-Sep 2026, stratified by firm size (inspections on record)
    rf = {firm(x.get("FIRMLEGALNAM")) for x in _rows("fda.recalls.cder")}
    n_insp = {f: len(v) for f, v in insp.items()}
    strata = {}
    for lo, hi in ((1, 3), (4, 9), (10, 24), (25, 10 ** 6)):
        g = {f for f in pop if lo <= n_insp[f] <= hi}
        s, o = g & out_, g - out_
        strata[f"{lo}-{hi if hi < 10**6 else '+'}"] = {
            "short": [len(rf & s), len(s)], "other": [len(rf & o), len(o)]}
    res["recall"] = {"recall_firms": len(rf), "short_with_recall": len(rf & out_),
                     "other_with_recall": len(rf & (pop - out_)), "by_inspections": strata,
                     "median_inspections_short": sorted(n_insp[f] for f in out_)[len(out_) // 2],
                     "median_inspections_other": sorted(n_insp[f] for f in pop - out_)[len(pop - out_) // 2]}
    # import alert 66-40
    h = S._read(S.latest("fda.importalert.66-40"))
    ia = set()
    for b in re.findall(r'<div class="div-info".*?(?=<div class="div-info"|\Z)', h, re.S):
        lines = [x.strip() for x in re.sub(r"<[^>]+>", "\n", b).split("\n") if x.strip()]
        if lines:
            ia.add(firm(lines[0]))
    reg = {firm(m) for r in S.fda_rows() for m in (r.get("openfda") or {}).get("manufacturer_name", [])}
    res["import_alert"] = {"firms_on_alert": len(ia), "shortage_firms_on_alert": sorted(ia & sf),
                           "registrants_on_alert": sorted(ia & reg)}
    return res


# ---------------------------------------------------------------- Australia
def australia(rx):
    subs = V.subjects()
    res = {"window_subjects": len(subs), "resolutions": sum(s["event"] for s in subs),
           "naive_median": V.median_of_resolved(subs), "km_median": V.quantile(V.km(subs), 0.5),
           "km_q25": V.quantile(V.km(subs), 0.25)}
    sev = {}
    for imp in ("Low", "Medium", "Critical"):
        g = [s for s in subs if s["rec"].get("shortage_impact") == imp]
        sev[imp] = (len(g), sum(s["event"] for s in g), V.quantile(V.km(g), 0.5))
    res["severity"] = sev
    T = S.tga_records()
    regs = S.registers(); _, cd = S.shared_coded(regs)
    US, FR = set(cd["US"]), set(cd["FR"])
    us_real = {k for k, rs in _by_substance(rx).items() if any(r["status"] == "Current" for r in rs)}
    def share(rows):
        ks = {_key(r["active_ingredients"], rx) for r in rows} - {None}
        return {"coded": len(ks), "in_us": len(ks & US), "us_real": len(ks & us_real), "in_fr": len(ks & FR)}
    res["anticipated"] = share([r for r in T if r["status"] == "A"])
    res["current"] = share([r for r in T if r["status"] == "C"])
    lead = sorted((S.tga_date(r["shortage_start"]) - CAPTURE).days for r in T
                  if r["status"] == "A" and S.tga_date(r["shortage_start"]))
    res["anticipated_lead_days_median"] = lead[len(lead) // 2]
    return res


RX = None


def run():
    global RX
    RX = json.loads((S.DATA / "rxnorm.json").read_text())
    F = X.build()
    by = _by_substance(RX)
    return {"fda": fda_fields(F, by), "cohort": cohort_depth(by, RX),
            "enforcement": enforcement(), "australia": australia(RX)}


def main():
    r = run()
    f, c, e, a = r["fda"], r["cohort"], r["enforcement"], r["australia"]
    pct = lambda x, n: f"{x}/{n} ({x / n:.0%})" if n else "—"
    print("== FDA list: what separates an exit notice from a shortage ==")
    for g, (n, x) in sorted(f["form"].items(), key=lambda kv: -kv[1][0]):
        print(f"  form {g:<12} exits {pct(x, n)}")
    for g, (n, x) in sorted(f["category"].items(), key=lambda kv: kv[1][1] / kv[1][0]):
        print(f"  category {g:<26} exits {pct(x, n)}")
    for g, (n, x) in f["application"].items():
        print(f"  application {g:<13} exits {pct(x, n)}")
    print(f"  age: exits median {f['age']['exits_median_y']}y ({f['age']['exits_over_2y']} of {f['age']['n_exits']} over 2y); "
          f"chronic median {f['age']['chronic_median_y']}y ({f['age']['chronic_over_2y']} of {f['age']['n_chronic']} over 2y)")
    print("  reason on chronic substances (n, median age y):", f["reason"])
    print("  availability of chronic substances:", f["availability_of_chronic"])
    print("  twin packages:", f["twins"])
    print("\n== Drugs@FDA supplier depth (control group: top injectable generics) ==")
    for pth in ("established", "new_entrant"):
        print(f"  {pth}: " + "  ".join(f"{b}: {pct(x, n)}" for b, (n, x) in c[pth].items()))
    print("\n== enforcement ==")
    w = e["warning_letter"]
    print(f"  warning letter FY22-26: P(short|letter) {w['short_given_letter']}/{w['letter_firms']} = {w['p_short_letter']:.1%}; "
          f"P(short|none) {w['p_short_none']:.2%}; letters before first listing {w['letters_before_first_listing']}, after {w['letters_after']}")
    rc = e["recall"]
    print(f"  recalls 2026: {rc['short_with_recall']} of {e['shortage_firms_inspected']} shortage firms vs "
          f"{rc['other_with_recall']} of {e['inspected_firms'] - e['shortage_firms_inspected']} others; median inspections "
          f"{rc['median_inspections_short']} vs {rc['median_inspections_other']}")
    for k, v in rc["by_inspections"].items():
        print(f"    inspections {k:<5} short {pct(*v['short'])}   other {pct(*v['other'])}")
    print(f"  import alert 66-40: {e['import_alert']['firms_on_alert']} firms; shortage firms on it {e['import_alert']['shortage_firms_on_alert']}; "
          f"registrants {e['import_alert']['registrants_on_alert']}")
    print("\n== Australia ==")
    print(f"  duration: naive median {a['naive_median']} d, KM median {a['km_median']} d, q25 {a['km_q25']} d "
          f"({a['window_subjects']} shortages, {a['resolutions']} resolutions)")
    print("  severity (n, events, KM median):", a["severity"])
    print(f"  anticipated: {a['anticipated']} lead median {a['anticipated_lead_days_median']} d | current: {a['current']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
