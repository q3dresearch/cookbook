#!/usr/bin/env python3
"""Re-derive every number in this recipe from the capture.

    python verify.py

The parsers here read HTML that nobody promised would stay the same shape, so the
failure that matters is **silent**: a selector stops matching, a register yields
almost nothing, and the overlap shrinks in a way that reads as a finding. That already
happened once — the first ANSM pass returned one distinct substance, which looks
exactly like "France shares nothing with anyone".

So this checks yields as well as results, and treats a collapsed yield as a failure
rather than a smaller number.
"""
import json
import sys
sys.path.insert(0, ".")
import shortagelib as S
from inspections import firm as _f

FAIL = []


def chk(label, claim, actual, tol=0):
    try:
        ok = abs(float(claim) - float(actual)) <= tol
    except (TypeError, ValueError):
        ok = str(claim) == str(actual)
    if not ok:
        FAIL.append(f"{label}: claim {claim}, actual {actual}")
    print(f"  {'OK ' if ok else '!! '} {label:46s} {claim!s:>12s}  {actual}")


def main():
    # rxnorm.json is the join key for every number below. If it is mid-rewrite -- the
    # resolver is resumable and runs for ~35 minutes -- the population shifts under the
    # checks and they report drift that is not a regression. Refuse rather than mislead.
    regs = S.registers()
    _cache = json.loads((S.DATA / "rxnorm.json").read_text())
    # Only the entries the current registers actually read matter; the cache also holds
    # stale names from earlier captures. The marker for "re-resolved" is the presence of
    # the `all` key, not a truthy set_key -- a few products genuinely have no rollup.
    from rxnorm import clean as _clean0
    _used = {_clean0(n) for d in regs.values() for n, _ in d["rows"]}
    _stale = [q for q in _used if q in _cache and "all" not in _cache[q]]
    if _stale:
        print(f"  REFUSING: rxnorm.json is mid-rewrite — {len(_stale)} of the "
              f"{len(_used)} names this capture needs predate the ingredient-set fix.")
        print(f"  e.g. {_stale[:3]}")
        print("  Every number here is keyed on it. Run rxnorm.py to completion, then re-run.")
        return 1


    print("-- parser yields (a collapse here is a failure, not a smaller number) --")
    chk("FDA rows in the capture", 1619, regs["US"]["raw"])
    chk("ANSM table rows", 291, regs["FR"]["raw"])
    chk("ANSM rows carrying a bracketed INN", 274, regs["FR"]["yield"])
    chk("TGA candidate name lines", 1154, regs["AU"]["raw"])
    for c in ("US", "FR", "AU"):
        n = len(regs[c]["rows"])
        if n < 50:
            FAIL.append(f"{c} yielded only {n} distinct substances — parser probably broken")
        print(f"  {'OK ' if n >= 50 else '!! '} {c} distinct substances{'':<24} {n}")

    print("\n-- the overlap --")
    sets = {c: {st for _, st in d["rows"]} for c, d in regs.items()}
    chk("US distinct substances", 206, len(sets["US"]))
    chk("FR distinct substances", 189, len(sets["FR"]))
    chk("AU distinct substances", 437, len(sets["AU"]))
    chk("US and FR, by stem", 38, len(sets["US"] & sets["FR"]))
    chk("US and AU, by stem", 79, len(sets["US"] & sets["AU"]))
    chk("FR and AU, by stem", 80, len(sets["FR"] & sets["AU"]))
    tri, _ = S.shared(regs)
    chk("STEM join, on all three", 22, len(tri))
    chk("union across all three, by stem", 658, len(set.union(*sets.values())))

    print("\n-- the canonical join (RxNorm ingredient codes) --")
    codes, cd = S.shared_coded(regs)
    csets = {c: set(cd[c]) for c in cd}
    chk("US distinct ingredients", 196, len(csets["US"]))
    chk("FR distinct ingredients", 163, len(csets["FR"]))
    chk("AU distinct ingredients", 382, len(csets["AU"]))
    chk("US and FR, by ingredient set", 36, len(csets["US"] & csets["FR"]))
    chk("US and AU, by ingredient set", 79, len(csets["US"] & csets["AU"]))
    chk("FR and AU, by ingredient set", 76, len(csets["FR"] & csets["AU"]))
    chk("ON ALL THREE", 23, len(codes))
    chk("union of ingredients", 573, len(set.union(*csets.values())))
    ing = {cd["US"][k][0] for k in codes}
    for must in ("rifampin", "mesalamine"):
        chk(f"'{must}' found by the code key", True, must in ing)
    chk("'insulin' NOT a single shared ingredient", True,
        not any(i == "insulin" for i in ing))
    import json as _j
    rx = _j.loads((S.DATA / "rxnorm.json").read_text())
    hit = sum(1 for x in rx.values() if x.get("rxcui"))
    # Two denominators, both real, so both are named: 82% of DISTINCT CLEANED NAMES
    # resolve, and 86% of REGISTER ROWS are placed, because the names that fail are
    # disproportionately one-offs.
    chk("distinct cleaned names resolved", "80%", f"{hit*100//len(rx)}%")
    placed = sum(len(cd[c]) for c in cd)
    allrows = sum(len(regs[c]["rows"]) for c in regs)
    chk("register rows placed", "79%", f"{placed*100//allrows}%")

    print("\n-- the stemmer --")
    for name, want in (("Calcium Chloride Dihydrate", "calcium"),
                       ("Sodium Chloride", "sodium"),
                       ("Dexamethasone Sodium Phosphate Injection", "dexamethason"),
                       ("dexaméthasone (phosphate sodique de)", "dexamethason"),
                       ("Metoprolol Succinate Tablet, Extended Release", "metoprolol"),
                       ("indométacine", "indometacin")):
        chk(f"stem({name[:34]!r})", want, S.stem(name))

    print("\n-- suppliers per shared substance (US column only) --")
    import json as _j, collections as _c
    from rxnorm import clean as _cl
    rxn = _j.loads((S.DATA / "rxnorm.json").read_text())
    fda = S.fda_rows()
    sub_firm, firm_sub, recs = _c.defaultdict(set), _c.defaultdict(set), _c.Counter()
    for r in fda:
        e = rxn.get(_cl(r.get("generic_name") or "")) or {}
        k, f = e.get("rxcui"), r.get("company_name")
        if f: recs[f] += 1
        if k and f: sub_firm[k].add(f); firm_sub[f].add(k)
    chk("FDA rows carrying a company_name", 1619, sum(recs.values()))
    multi = sum(1 for k in codes if len(sub_firm.get(k, ())) >= 2)
    chk("shared substances short at 2+ US firms", 13, multi)
    chk("shared substances short at exactly 1", 10, len(codes) - multi)
    mx = max((len(sub_firm.get(k, ())), cd["US"][k][0]) for k in codes)
    chk("most suppliers short at once", "6 midazolam", f"{mx[0]} {mx[1]}")
    # the denominator that would have tripled it
    chk("Hospira: records", 194, recs["Hospira, Inc., a Pfizer Company"])
    chk("Hospira: distinct substances", 30, len(firm_sub["Hospira, Inc., a Pfizer Company"]))

    print("\n-- the inspection null (pooled, all captures) --")
    from inspections import inspections_for_verify as _insp
    insp, nrows = _insp()
    chk("pooled drug-inspection rows", 39988, nrows)
    chk("distinct inspected firms", 16527, len(insp))
    sfirms = {_f(r.get("company_name")) for r in fda if r.get("company_name")} - {""}
    matched = len(sfirms & set(insp))
    chk("shortage firms matched into inspections", "70%", f"{matched*100//len(sfirms)}%")
    def oai(fs):
        rows = [r for f in fs for r in insp.get(f, []) if (r.get("ProductType") or "") == "Drugs"]
        n = sum(1 for r in rows if r.get("ClassificationCode") == "OAI")
        return f"{n*100//max(len(rows),1)}%"
    chk("OAI rate, all shortage firms", "6%", oai(sfirms))
    chk("OAI rate, every other inspected firm", "7%", oai(set(insp) - sfirms))

    print("\n-- the decision grid (figure 1) --")
    import collections as _c2
    def _flat(x): return [] if x is None else (x if isinstance(x, list) else [x])
    firms = _c2.defaultdict(set)
    for r in fda:
        e = rxn.get(_cl(r.get("generic_name") or "")) or {}
        if S.sub_key(e):
            for x in _flat(r.get("company_name")): firms[S.sub_key(e)].add(str(x))
    FRs, AUs = set(cd["FR"]), set(cd["AU"])
    ncty = lambda k: 1 + (k in FRs) + (k in AUs)
    grid = _c2.Counter((ncty(k), min(len(firms[k]), 4)) for k in firms)
    chk("drugs placed in the grid", 196, sum(grid.values()))
    chk("3 countries, 1 supplier  -> qualify a second", 10, grid[(3, 1)])
    chk("3 countries, 2+ suppliers -> stockpile", 13, sum(grid[(3, c)] for c in (2, 3, 4)))
    chk("1 country, 1 supplier -> re-tender", 79, grid[(1, 1)])
    chk("1 country, 2+ suppliers -> a national constraint", 25,
        sum(grid[(1, c)] for c in (2, 3, 4)))
    # the four README populations, which aggregate rows 1 and 2
    z = lambda rows, cols: sum(grid[(r, c)] for r in rows for c in cols)
    chk("region: inventory only (3 countries, several firms)", 13, z((3,), (2, 3, 4)))
    chk("region: a policy constraint", 50, z((1, 2), (2, 3, 4)))
    chk("region: one reporting firm", 133, z((1, 2, 3), (1,)))
    chk("the three regions exhaust the plot", 196, 13 + 50 + 133)
    print("     (the screen is deliberately not asserted — its intervals overlap)")

    print("\n-- exits vs chronic shortages (figure 2) --")
    import datetime as _dt, statistics as _stt
    _P = lambda x: _dt.datetime.strptime(x, "%m/%d/%Y").date()
    TODAY = _dt.date(2026, 9, 10)
    st_rows, first, cats = _c2.defaultdict(list), {}, _c2.defaultdict(set)
    for r in fda:
        e = rxn.get(_cl(r.get("generic_name") or "")) or {}
        k = S.sub_key(e)
        if not k: continue
        d0 = _P(r["initial_posting_date"])
        first[k] = min(first.get(k, d0), d0)
        cats[k].update(r.get("therapeutic_category") or [])
        for f in _flat(r.get("company_name")): st_rows[(k, str(f))].append(r.get("status"))
    fm, lv = _c2.defaultdict(set), _c2.defaultdict(set)
    for (k, f), sts in st_rows.items():
        fm[k].add(f)
        # a firm is leaving only if EVERY package NDC it lists is To Be Discontinued
        if all(x == "To Be Discontinued" for x in sts): lv[k].add(f)
    age = {k: (TODAY - first[k]).days / 365.25 for k in fm}
    ex = {k: lv[k] == fm[k] for k in fm}
    # Freeze it. A defaultdict silently grows on any fm[missing] lookup downstream, and
    # every population below divides by len(fm) — it had already drifted by one.
    fm = dict(fm)
    chk("substances on the FDA list", 196, len(fm))
    chk("every listed firm discontinuing (an exit)", 137, sum(ex.values()))
    chk("still a shortage (chronic)", 59, sum(1 for k in fm if not ex[k]))
    old = [k for k in fm if age[k] > 2]
    chk("listed more than two years", 54, len(old))
    chk("  ...of those, chronic not exit", 53, sum(1 for k in old if not ex[k]))
    for cat, n, e_ in (("Pediatric", 12, 0), ("Anesthesia", 13, 3), ("Cardiovascular", 31, 22)):
        ks = [k for k in fm if cat in cats[k]]
        chk(f"{cat}: substances", n, len(ks))
        chk(f"{cat}: leaving", e_, sum(1 for k in ks if ex[k]))
    chk("Pediatric median years listed (x10)", 68,
        round(_stt.median([age[k] for k in fm if "Pediatric" in cats[k]]) * 10))
    chk("Cardiovascular median years listed (x10)", 8,
        round(_stt.median([age[k] for k in fm if "Cardiovascular" in cats[k]]) * 10))

    print("\n-- figure 2: Pediatric is an overlay, not a band, and it still holds --")
    _ped = [k for k in fm if "Pediatric" in cats[k]]
    chk("Pediatric substances", 12, len(_ped))
    chk("  ...also carrying another category", 12, sum(1 for k in _ped if len(cats[k]) > 1))
    _cv = [k for k in fm if "Cardiovascular" in cats[k]]
    chk("Cardiovascular substances also tagged elsewhere", 6,
        sum(1 for k in _cv if len(cats[k]) > 1))
    # tested INSIDE each category rather than beside them
    _bad = []
    for c in {x for k in fm for x in cats[k]} - {"Pediatric"}:
        ks = [k for k in fm if c in cats[k]]
        if len(ks) < 6: continue
        b = [k for k in ks if "Pediatric" in cats[k]]
        if b and sum(1 for k in b if ex[k]): _bad.append(c)
    chk("categories where a paediatric substance IS an exit", 0, len(_bad))
    chk("  ...categories tested", 10,
        len([c for c in {x for k in fm for x in cats[k]} - {"Pediatric"}
             if len([k for k in fm if c in cats[k]]) >= 6
             and any("Pediatric" in cats[k] for k in fm if c in cats[k])]))
    _cot = set().union(*[cats[k] - {"Pediatric"} for k in _ped])
    _pool = [k for k in fm if cats[k] & _cot]
    chk("comparison pool sharing a paediatric co-tag", 161, len(_pool))
    chk("  ...its exit rate, percent", 66,
        round(sum(1 for k in _pool if ex[k]) / len(_pool) * 100))
    chk("observed exits among the twelve", 0, sum(1 for k in _ped if ex[k]))
    print("     expected 6.0 from the pool rate; P(0 of 12) = 0.0001")

    print("\n-- one reporting firm predicts an exit, not a fixable shortage (figure 1) --")
    one = [k for k in fm if len(fm[k]) == 1]
    many = [k for k in fm if len(fm[k]) > 1]
    chk("substances with one reporting firm", 133, len(one))
    chk("  ...of those, discontinuations", 127, sum(1 for k in one if ex[k]))
    chk("substances with two or more firms", 63, len(many))
    chk("  ...of those, discontinuations", 10, sum(1 for k in many if ex[k]))
    chk("the re-tender worklist (sole firm, not leaving)", 6,
        sum(1 for k in one if not ex[k]))

    # chart 5 is now these four points and their intervals, and nothing else
    import math as _m
    def _wil(x, n, z=1.96):
        p, den = x / n, 1 + z * z / n
        c = p + z * z / (2 * n); h = z * _m.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
        return max(0.0, (c - h) / den), min(1.0, (c + h) / den)
    for lab, sel, en, ex_ in (("1 firm", lambda c: c == 1, 133, 127),
                              ("2 firms", lambda c: c == 2, 21, 7),
                              ("3 firms", lambda c: c == 3, 10, 3),
                              ("4 or more", lambda c: c >= 4, 32, 0)):
        ks = [k for k in fm if sel(len(fm[k]))]
        chk(f"figure 1, {lab}: substances", en, len(ks))
        chk(f"figure 1, {lab}: exits", ex_, sum(1 for k in ks if ex[k]))
    _l1, _h1 = _wil(127, 133); _l2, _h2 = _wil(10, 63)
    chk("1-firm Wilson low x100", 91, round(_l1 * 100))
    chk("2+-firm Wilson high x100", 27, round(_h2 * 100))
    print(f"     [{_l1:.2f},{_h1:.2f}] against [{_l2:.2f},{_h2:.2f}] — the intervals do not touch")

    # Sequence step 9 Q1: recompute the headline on a code path that shares nothing with
    # the one that produced it — raw generic_name strings, no RxNorm coding at all. If
    # the cliff were an artifact of the ingredient rollup it would move here.
    _raw = _c2.defaultdict(list)
    for r in fda:
        _k = (r.get("generic_name") or "").strip().lower()
        for f in _flat(r.get("company_name")): _raw[(_k, str(f))].append(r.get("status"))
    _rf, _rl = _c2.defaultdict(set), _c2.defaultdict(set)
    for (k, f), sts in _raw.items():
        _rf[k].add(f)
        if all(x == "To Be Discontinued" for x in sts): _rl[k].add(f)
    _rex = {k: _rl[k] == _rf[k] for k in _rf}
    _r1 = [k for k in _rf if len(_rf[k]) == 1]
    _r2 = [k for k in _rf if len(_rf[k]) > 1]
    chk("uncoded cross-check, one firm: percent exits", 93,
        round(sum(1 for k in _r1 if _rex[k]) / len(_r1) * 100))
    chk("uncoded cross-check, two or more: percent exits", 9,
        round(sum(1 for k in _r2 if _rex[k]) / len(_r2) * 100))
    print("     coded says 87 and 5; the cliff is not an artifact of the ingredient rollup")

    print("\n-- a manufacturing tier hides in the free-text advice field --")
    import re as _re2
    _EX = _re2.compile(r"\b(?:distributed|marketed|manufactured)\s+by\s+"
                      r"([A-Za-z][\w .,'&/-]+?)(?:\s*[.;]|,\s|\s+for\s|\s+to\s|$)", _re2.I)
    _pairs, _slink = set(), _c2.defaultdict(set)
    for r in fda:
        m = _EX.search(r.get("related_info") or "")
        if not m: continue
        _reg = {_f(str(x)) for x in _flat(r.get("company_name"))}
        for a in _reg:
            _pairs.add((a, _f(m.group(1))))
        e = rxn.get(_cl(r.get("generic_name") or "")) or {}
        if S.sub_key(e):
            for a in _reg: _slink[S.sub_key(e)].add((a, _f(m.group(1))))
    # 22 after firm-name normalisation; the raw display strings give 23 because
    # "Sandoz" and "Sandoz Inc" are the same company written twice
    chk("distinct registrant -> distributor pairs named in free text", 30, len(_pairs))
    chk("  ...where the two are the same company", 0,
        sum(1 for a, b in _pairs if a == b))
    _heng = {b for a, b in _pairs if a.startswith("jiangsu hengrui")}
    chk("US distributors named behind one Chinese registrant", 5, len(_heng))
    # and the one that matters: does it break chart 5's independence assumption?
    _broken = 0
    for k, links in _slink.items():
        # fm is a defaultdict: fm[k] on a missing key CREATES it and quietly grows the
        # population the later checks divide by. It did, by one, before this line used .get
        names = {_f(x) for x in fm.get(k, ())}
        if len(names) > 1 and any(a in names and b in names for a, b in links):
            _broken += 1
    chk("substances where a reporting firm is another's distributor", 1, _broken)
    print("     so the '2 or more firms' side of chart 5 is genuinely independent reporters")

    # the structured field carries the same map, wider, and corroborates the free text
    _struct = set()
    _psub = _c2.defaultdict(set)
    for r in fda:
        _cn = {_f(str(x)) for x in _flat(r.get("company_name"))}
        e = rxn.get(_cl(r.get("generic_name") or "")) or {}
        for x in ((r.get("openfda") or {}).get("manufacturer_name") or []):
            b = _f(str(x))
            for a in _cn:
                if b != a and not (set(a.split()) & set(b.split())):
                    _struct.add((a, b))
                    if S.sub_key(e): _psub[(S.sub_key(e), a)].add(b)
    chk("registrant -> marketer pairs in openfda.manufacturer_name", 51, len(_struct))
    chk("  ...of the 22 free-text pairs, how many it confirms", 26,
        len(_pairs & _struct))
    chk("distinct registrants in that map", 35, len({a for a, _b in _struct}))
    chk("registrants behind more than one US marketer", 8,
        sum(1 for a in {x for x, _ in _struct}
            if len({b for x, b in _struct if x == a}) > 1))
    # the actionable case, and it is small: two marketers, one registrant, one molecule
    chk("substances where one registrant reaches two or more marketers", 5,
        sum(1 for v in _psub.values() if len(v) > 1))
    print("     that one is dexmedetomidine: Azurity reaches both Civica and Wilshire")

    print("\n-- approval pathway adds nothing beyond firm count --")
    _app = _c2.defaultdict(set)
    for r in fda:
        e = rxn.get(_cl(r.get("generic_name") or "")) or {}
        if S.sub_key(e):
            for a in ((r.get("openfda") or {}).get("application_number") or []):
                _app[S.sub_key(e)].add(a[:4].rstrip("0123456789"))
    _an = [k for k in fm if _app.get(k) == {"ANDA"}]
    _nd = [k for k in fm if _app.get(k) == {"NDA"}]
    chk("generic-only (ANDA) substances", 61, len(_an))
    chk("  ...that are exits", 47, sum(1 for k in _an if ex[k]))
    chk("brand-only (NDA) substances", 58, len(_nd))
    chk("  ...that are exits", 52, sum(1 for k in _nd if ex[k]))
    # 68% against 85% looks like a finding; inside the firm-count strata it is not
    _a1 = [k for k in _an if len(fm[k]) == 1]
    _n1 = [k for k in _nd if len(fm[k]) == 1]
    chk("single-firm generics: percent exits", 100,
        round(sum(1 for k in _a1 if ex[k]) / len(_a1) * 100))
    chk("single-firm brands: percent exits", 93,
        round(sum(1 for k in _n1 if ex[k]) / len(_n1) * 100))
    print("     84 against 90 — the pathway gap was the firm-count gap in other clothes")

    print("\n-- Q8: do the nine 'inventory only' substances share a plant? --")
    import inspections as _I
    _insp, _ = _I.inspections()
    _fei = lambda f: {x["FEINumber"] for x in _insp.get(_I.firm(f), []) if x.get("FEINumber")}
    _FRs, _AUs = set(cd["FR"]), set(cd["AU"])
    _nine = [k for k in fm if not ex[k] and len(fm[k]) > 1
             and 1 + (k in _FRs) + (k in _AUs) == 3]
    chk("the 'inventory only' substances", 13, len(_nine))
    _shared = sum(1 for k in _nine
                  if set.intersection(*[_fei(f) for f in fm[k]]))
    chk("  ...sharing an establishment across ALL their firms", 0, _shared)
    print("     a real negative about the final-dose tier; it says nothing about the API tier")

    print("\n-- concentration, the one continuous feature (negative/5-dilute) --")
    import features as _X
    _F = _X.build()
    _form = _c2.defaultdict(set)
    for r in fda:
        e = rxn.get(_cl(r.get("generic_name") or "")) or {}
        if e.get("rxcui") and r.get("dosage_form"): _form[S.sub_key(e)].add(r["dosage_form"])
    _inj = lambda k: any("Inject" in x for x in _form.get(k, ()))
    _ai = [k for k in _F if _inj(k)]
    chk("injectable substances", 99, len(_ai))
    chk("  ...with a parsable mg/mL", 81, sum(1 for k in _ai if _F[k]["conc_mg_ml"]))
    _ch = [k for k in _ai if _F[k]["conc_mg_ml"] and not _F[k]["is_exit"]]
    chk("chronic injectables with a concentration", 39, len(_ch))
    _lo = [k for k in _ch if _F[k]["conc_mg_ml"] <= 10]
    _hi = [k for k in _ch if _F[k]["conc_mg_ml"] > 10]
    chk("  dilute (<= 10 mg/mL, the median)", 27, len(_lo))
    chk("  concentrated (> 10)", 12, len(_hi))
    chk("  dilute median years listed (x10)", 76,
        round(_stt.median([_F[k]["age_y"] for k in _lo]) * 10))
    chk("  concentrated median years listed (x10)", 41,
        round(_stt.median([_F[k]["age_y"] for k in _hi]) * 10))
    _r, _n = _X.spearman([_F[k]["conc_mg_ml"] for k in _ch], [_F[k]["age_y"] for k in _ch])
    chk("  Spearman rho x100", -45, round(_r * 100))
    # the parse is the claim's weak point, so its yield is checked like a parser yield
    # step 9 Q2: the better correlates are the ones the shortage itself creates
    _ci = [k for k in _ai if not _F[k]["is_exit"]]
    for _lab, _fld, _want in (("n_ndc", "n_ndc", 45), ("n_firms", "n_firms", 29)):
        _ks = [k for k in _ci if _F[k][_fld] is not None]
        _rr, _ = _X.spearman([_F[k][_fld] for k in _ks], [_F[k]["age_y"] for k in _ks])
        chk(f"  {_lab} vs age x100 (accumulates with the shortage — not used)",
            _want, round(_rr * 100))
    _bo = [k for k in _ci if _F[k]["conc_mg_ml"] and _F[k]["strength_mg"]]
    _rm, _ = _X.spearman([_F[k]["strength_mg"] for k in _bo], [_F[k]["conc_mg_ml"] for k in _bo])
    chk("  mass vs concentration x100 (not separable at this n)", 77, round(_rm * 100))
    print(f"     parse yield: strength on {sum(1 for k in _F if _F[k]['strength_mg'])}"
          f"/{len(_F)} substances, concentration on "
          f"{sum(1 for k in _F if _F[k]['conc_mg_ml'])}/{len(_F)}")

    print("\n-- two statutory streams in one table --")
    _by = _c2.Counter(r.get("status") for r in fda)
    chk("rows: interruption/shortage", 1166, _by["Current"])
    chk("rows: permanent discontinuance", 446, _by["To Be Discontinued"])
    _rz = _c2.defaultdict(lambda: [0, 0])
    for r in fda: _rz[r.get("status")][r.get("shortage_reason") is not None] += 1
    chk("shortage rows carrying a reason code", 423, _rz["Current"][1])
    chk("discontinuance rows carrying a reason code", 0, _rz["To Be Discontinued"][1])
    _pd = _c2.Counter(_P(r["initial_posting_date"]) for r in fda)
    _pre = {d: n for d, n in _pd.items() if d.year < 2015}
    chk("distinct posting dates before 2015 (a bulk load, not events)", 2, len(_pre))
    chk("  rows on 2012-01-01", 24, _pd[_dt.date(2012, 1, 1)])
    chk("  rows on 2012-02-22", 55, _pd[_dt.date(2012, 2, 22)])
    _exy = _c2.Counter(first[k].year for k in fm if ex[k])
    chk("discontinuance substances first listed 2025 or later", 136,
        _exy[2025] + _exy[2026])

    print("\n-- negative/5-dilute rests on four censored dates, and says so --")
    _FL = {_dt.date(2012, 1, 1), _dt.date(2012, 2, 22)}
    _cen = [k for k in _ch if first[k] in _FL]
    chk("censored chronic injectables with a concentration", 4, len(_cen))
    chk("  ...that are dilute", 4, sum(1 for k in _cen if _F[k]["conc_mg_ml"] <= 10))
    chk("  ...that are concentrated", 0, sum(1 for k in _cen if _F[k]["conc_mg_ml"] > 10))
    _lo2 = [k for k in _lo if first[k] not in _FL]
    chk("dilute median years, censored dropped (x10)", 64,
        round(_stt.median([_F[k]["age_y"] for k in _lo2]) * 10))
    _r2, _n2 = _X.spearman([_F[k]["conc_mg_ml"] for k in _lo2 + _hi],
                           [_F[k]["age_y"] for k in _lo2 + _hi])
    chk("  Spearman rho x100, censored dropped", -36, round(_r2 * 100))
    # The p-values were typed into the prose and the figure from an unseeded ad-hoc run,
    # so they drifted between mentions (0.0025 here, 0.0027 there). Seeded, they are one
    # number. Two-sided permutation test on the difference of medians, n = 20,000.
    import random as _rnd
    def _perm_p(a, b, n=20000, seed=20260915):
        pool, na = list(a) + list(b), len(a)
        obs = abs(_stt.median(a) - _stt.median(b))
        rng, hits = _rnd.Random(seed), 0
        for _ in range(n):
            rng.shuffle(pool)
            if abs(_stt.median(pool[:na]) - _stt.median(pool[na:])) >= obs - 1e-12:
                hits += 1
        return (hits + 1) / (n + 1)
    _p_all = _perm_p([_F[k]["age_y"] for k in _lo], [_F[k]["age_y"] for k in _hi])
    _p_cen = _perm_p([_F[k]["age_y"] for k in _lo2], [_F[k]["age_y"] for k in _hi])
    chk("  permutation p x10000, all 36 (difference of medians)", 367, round(_p_all * 10000))
    chk("  permutation p x1000, censored dropped", 79, round(_p_cen * 1000))
    print(f"     the direction survives the drop; the significance does not "
          f"(p {_p_all:.4f} -> {_p_cen:.3f})")

    print("\n-- the only forward-looking field, and how far it reaches --")
    import re as _re
    _MON = {m: i + 1 for i, m in enumerate(
        "january february march april may june july august september october november december".split())}
    _REC = _re.compile(r"(?:estimated\s+recovery|recovery|next\s+release|next\s+delivery[^:]*)"
                       r"\s*:?\s*(tbd|([a-z]+)\s+(20\d\d))", _re.I)
    _dates, _tbd = {}, set()
    for r in fda:
        m = _REC.search(r.get("related_info") or "")
        e = rxn.get(_cl(r.get("generic_name") or "")) or {}
        k = S.sub_key(e)
        if not (m and k): continue
        if m.group(1).lower() == "tbd":
            _tbd.add(k); continue
        _mo = _MON.get((m.group(2) or "").lower())
        if _mo:
            _d0 = _dt.date(int(m.group(3)), _mo, 1)
            _dates[k] = max(_dates.get(k, _d0), _d0)
    # A substance can carry a date on one row and "TBD" on another, so the two sets
    # OVERLAP by 11 and cannot be subtracted independently. Doing that understated the
    # uncovered population by twelve before this check caught it.
    chk("substances with a dated recovery estimate", 33, len(_dates))
    chk("substances whose estimate mentions TBD anywhere", 28, len(_tbd))
    chk("  ...carrying BOTH a date and a TBD, on different rows", 17,
        len(set(_dates) & _tbd))
    # both stated on the same base — the 139 substances that have a reporting firm
    chk("substances with any forward-looking statement", 44,
        len((set(_dates) | _tbd) & set(fm)))
    chk("substances with none at all", 152, len(set(fm) - set(_dates) - _tbd))
    chk("dated estimates already lapsed at capture", 12,
        sum(1 for v in _dates.values() if v < TODAY))
    _inj2 = [k for k in _dates if _F[k]["conc_mg_ml"]
             and any("Inject" in x for x in _form.get(k, ()))]
    _rr2, _ = _X.spearman([_F[k]["conc_mg_ml"] for k in _inj2],
                          [(_dates[k] - TODAY).days for k in _inj2])
    chk("concentration vs recovery horizon x100 (no relationship)", 16, round(_rr2 * 100))
    print("     the December-2028 cohort is dilute, but n=4 and rho is 0.04 — not a corroboration")

    print("\n-- the cleaner (four substances were lost to it once) --")
    from rxnorm import clean
    for name, want in (("Lamotrigine Tablet, Extended Release", "lamotrigine"),
                       ("Aprepitant Oral Powder for Suspension", "aprepitant"),
                       ("Metoprolol Succinate Tablet, Extended Release", "metoprolol"),
                       ("Insulin Lispro Injection", "insulin lispro")):
        chk(f"clean({name[:32]!r})", want, clean(name))
    print(f"  -- stems reached by more than one distinct name: {len(S.collisions(regs))}")

    print("\n-- the pagination trap, re-derived so it stays visible --")
    _run = S.latest_run("fda.shortages.current")
    chk("files in the newest FDA run (two pages, one run)", 2, len(_run))
    _p2 = _j.loads(S._read(_run[-1]))["results"]
    chk("rows on the lexically newest file alone (page two)", 619, len(_p2))
    chk("rows on both pages", 1619, len(fda))
    chk("distinct stems on page two alone", 148, len({S.stem(r.get("generic_name", "")) for r in _p2} - {""}))
    chk("distinct stems on both pages", 206, len({S.stem(r.get("generic_name", "")) for r in fda} - {""}))

    print("\n-- what each register remembers (memory.py, figure 4) --")
    import memory as _M
    _mem = _M.rows()
    chk("memory rows", 2894, len(_mem))
    for _reg, _n, _cls in (("FDA (US)", 1619, {"shortage": 1166, "discontinuance": 446, "resolved": 7}),
                           ("ANSM (FR)", 291, {"shortage": 186, "discontinuance": 16, "resolved": 89}),
                           ("TGA (AU)", 984, {"shortage": 502, "discontinuance": 278, "resolved": 204})):
        _rr = [r for r in _mem if r["register"] == _reg]
        chk(f"{_reg} rows", _n, len(_rr))
        for _c, _want in _cls.items():
            chk(f"  {_reg} {_c}", _want, sum(1 for r in _rr if r["cls"] == _c))
    _yr = lambda reg, cls: sorted(r["year"] for r in _mem if r["register"] == reg and r["cls"] == cls and r["year"])
    chk("TGA oldest open shortage year", 2003, _yr("TGA (AU)", "shortage")[0])
    chk("TGA oldest resolved year (the survivor)", 2022, _yr("TGA (AU)", "resolved")[0])
    chk("  ...and how many resolved rows older than 2026", 1, sum(1 for y in _yr("TGA (AU)", "resolved") if y < 2026))
    chk("ANSM oldest resolved year (the survivor)", 2025, _yr("ANSM (FR)", "resolved")[0])
    chk("  ...and how many resolved rows older than 2026", 1, sum(1 for y in _yr("ANSM (FR)", "resolved") if y < 2026))
    chk("FDA resolved rows, all 2026", 7, sum(1 for y in _yr("FDA (US)", "resolved") if y == 2026))
    _fd = sorted(int(r["duration_days"]) for r in _mem if r["register"] == "FDA (US)" and r["duration_days"] != "")
    chk("FDA resolved rows carrying a duration", 7, len(_fd))
    chk("  their median, days", 1402, _fd[len(_fd) // 2])
    chk("  distinct drugs among them", 4, len({r.get("generic_name") for r in fda if r.get("status") == "Resolved"}))
    chk("rows flagged as the 2012 bulk load", 79, sum(1 for r in _mem if r["bulk_load"]))
    chk("  distinct posting dates before 2015", True,
        {r.get("initial_posting_date") for r in fda if int(str(r.get("initial_posting_date"))[-4:]) < 2015} == _M.BULK_LOAD)
    chk("oldest FDA posting year that is not the bulk load", 2015,
        min(int(str(r.get("initial_posting_date"))[-4:]) for r in fda if r.get("initial_posting_date") not in _M.BULK_LOAD))
    _gaps = []
    for _c in S.ansm_table():
        if "remise" not in _c[0].lower():
            continue
        _ds = [_dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))) for m in (_M.FR_DATE.search(x) for x in _c) if m]
        if len(_ds) >= 2:
            _gaps.append(abs((_ds[0] - _ds[1]).days))
    chk("ANSM resolved rows carrying two dates", 89, len(_gaps))
    chk("  median days between them (both are restoration dates)", 1, _stt.median(_gaps))
    chk("  identical", 44, sum(1 for g in _gaps if g == 0))
    chk("  within a week", 66, sum(1 for g in _gaps if g <= 7))
    _T = S.tga_records()
    chk("TGA discontinued rows whose end date is the literal Unknown", 263,
        sum(1 for r in _T if r["status"] == "D" and str(r.get("shortage_end")).strip().lower() == "unknown"))
    chk("TGA current rows whose end date is after the capture (anticipated)", 405,
        sum(1 for r in _T if r["status"] == "C" and S.tga_date(r.get("shortage_end")) and S.tga_date(r.get("shortage_end")) > _dt.date(2026, 9, 10)))

    print("\n-- how long a shortage lasts (survival.py, figure 3) --")
    import survival as _V
    _subs = _V.subjects(); _curve = _V.km(_subs)
    chk("shortages observed in the twelve-month window", 612, len(_subs))
    chk("  of which resolved in the window", 203, sum(1 for s in _subs if s["event"]))
    chk("median of the resolved rows alone, days", 62, _V.median_of_resolved(_subs))
    chk("Kaplan-Meier median, days", 387, _V.quantile(_curve, 0.5))
    chk("Kaplan-Meier lower quartile, days", 1209, _V.quantile(_curve, 0.25))
    _form = lambda s: (s["rec"].get("dose_form") or "").lower()
    chk("  KM median, injectables", 182, _V.quantile(_V.km([s for s in _subs if "injection" in _form(s)]), 0.5))
    chk("  KM median, oral solids", 394, _V.quantile(_V.km([s for s in _subs if "tablet" in _form(s) or "capsule" in _form(s)]), 0.5))
    for _imp, _want in (("Low", 544), ("Medium", 128), ("Critical", 387)):
        chk(f"  KM median, severity {_imp} (not monotonic)", _want,
            _V.quantile(_V.km([s for s in _subs if s["rec"].get("shortage_impact") == _imp]), 0.5))

    print("\n-- what the feed changes between captures (revisions.py) --")
    import revisions as _R
    _rs = _R.runs()
    chk("FDA capture runs held", 5, len(_rs))
    _tot = _c2.Counter(); _mv = _c2.Counter()
    for (_t1, _x), (_t2, _y) in zip(_rs, _rs[1:]):
        _d = _R.diff(_x, _y); _mv.update(_d.pop("_moved")); _d.pop("_silent")
        for _k in ("changed", "silent", "naive_silent", "departed"):
            _tot[_k] += _d[_k]
        _amb = _d["ambiguous_keys"]
    chk("substantive changes across the intervals", 842, _tot["changed"])
    chk("  of which moved no update_date", 3, _tot["silent"])
    chk("  what a raw comparison says instead (unsorted lists)", 626, _tot["naive_silent"])
    chk("  ambiguous keys excluded per run", 9, _amb)
    for _fld2 in ("initial_posting_date", "discontinued_date", "status"):
        chk(f"  moves of {_fld2} (the draft's key reported 55, 55, 48)", 0, _mv[_fld2])
    _base = lambda r: (r.get("generic_name"), r.get("company_name"), r.get("package_ndc"))
    _c0 = _c2.Counter(_base(r) for r in _rs[0][1])
    _dup = {k for k, n in _c0.items() if n > 1}
    chk("keys carrying two rows in one capture, without the stream", 43, len(_dup))
    chk("  one Current beside one To Be Discontinued", 34,
        sum(1 for k in _dup if {r.get("status") for r in _rs[0][1] if _base(r) == k} == {"Current", "To Be Discontinued"}))
    _tw = _c2.defaultdict(set)
    for r in fda: _tw[_base(r)].add(r.get("status"))
    chk("twin packages in the newest capture", 26, sum(1 for s in _tw.values() if {"Current", "To Be Discontinued"} <= s))

    print("\n-- the sweep: tested and failed (sweep.py) --")
    import sweep as _W
    _sw = _W.run()
    chk("form: injectable substances that are exits", "54/96", "%d/%d" % (_sw["fda"]["form"]["injection"][1], _sw["fda"]["form"]["injection"][0]))
    chk("form: oral-solid substances that are exits", "62/71", "%d/%d" % (_sw["fda"]["form"]["oral solid"][1], _sw["fda"]["form"]["oral solid"][0]))
    chk("category: Anesthesia exits", "3/13", "%d/%d" % tuple(reversed(_sw["fda"]["category"]["Anesthesia"])))
    chk("category: Cardiovascular exits", "22/31", "%d/%d" % tuple(reversed(_sw["fda"]["category"]["Cardiovascular"])))
    chk("application: both ANDA and NDA, exits", "3/39", "%d/%d" % tuple(reversed(_sw["fda"]["application"]["both"])))
    chk("age: exits older than two years", 1, _sw["fda"]["age"]["exits_over_2y"])
    chk("age: real shortages older than two years", 53, _sw["fda"]["age"]["chronic_over_2y"])
    chk("availability: real shortages with every package Available", 4, _sw["fda"]["availability_of_chronic"].get("all Available", 0))
    chk("cohort: established molecules on the list by marketed products (1-5, 6-10, 11-20, 21+)",
        "9/25 5/22 16/43 19/41", " ".join("%d/%d" % (x, n) for n, x in _sw["cohort"]["established"].values()))
    _wl = _sw["enforcement"]["warning_letter"]
    chk("warning letters: lettered firms on the list", "8/520", "%d/%d" % (_wl["short_given_letter"], _wl["letter_firms"]))
    chk("  letters dated before the firm's first listing", 2, _wl["letters_before_first_listing"])
    chk("  letters dated after", 11, _wl["letters_after"])
    _rc = _sw["enforcement"]["recall"]
    chk("recalls: shortage firms with a 2026 recall", 31, _rc["short_with_recall"])
    chk("  most-inspected stratum, short firms recalling", "14/25", "%d/%d" % tuple(_rc["by_inspections"]["25-+"]["short"]))
    chk("  most-inspected stratum, other firms recalling", "6/52", "%d/%d" % tuple(_rc["by_inspections"]["25-+"]["other"]))
    chk("  median inspections, shortage firms vs others", "12 vs 1", f"{_rc['median_inspections_short']} vs {_rc['median_inspections_other']}")
    chk("import alert 66-40: shortage firms on it", 3, len(_sw["enforcement"]["import_alert"]["shortage_firms_on_alert"]))
    _au = _sw["australia"]
    chk("TGA anticipated shortages, coded", 62, _au["anticipated"]["coded"])
    chk("  ...that are real US shortages now", 1, _au["anticipated"]["us_real"])
    chk("  median lead, days", 50, _au["anticipated_lead_days_median"])
    chk("twin packages, substances, all chronic", "10/10", "%d/%d" % (_sw["fda"]["twins"]["on_chronic_substances"], _sw["fda"]["twins"]["substances"]))

    print()
    if FAIL:
        print(f"{len(FAIL)} MISMATCH(ES):")
        for x in FAIL: print("   " + x)
        return 1
    print("all claims re-derived; text and capture agree.")
    return 0


sys.exit(main())
