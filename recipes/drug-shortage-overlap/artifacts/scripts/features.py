#!/usr/bin/env python3
"""Substance-level quantitative features, derived once and shared.

Everything this recipe drew before was a count or a category: how many countries, how
many firms, exit or chronic. These are the continuous columns the same records can
actually support, with the parse rate of each recorded next to it -- a feature that
resolves on 40% of rows is a different thing from one that resolves on 95%, and the
difference is invisible once it is a number in a chart.

Shared by `chart-7-*.py` and `verify.py` so the two cannot drift.
"""
import collections, datetime as dt, json, re, sys
sys.path.insert(0, ".")
import shortagelib as S
import inspections as I
from rxnorm import clean

CAPTURE = dt.date(2026, 9, 10)
_D = lambda x: dt.datetime.strptime(x, "%m/%d/%Y").date()
_flat = lambda v: [] if v is None else (v if isinstance(v, list) else [v])

# "4 mg/1 mL" -> (4.0 mg, 4.0 mg/mL); "20 mg" -> (20.0, None). Units are normalised to
# mg so strengths are comparable; anything else (%, units, "0.15") is left unparsed
# rather than guessed at.
# Volumes appear as "/1 mL", "per 2 mL", "/.4 mL" and bare "per mL". The first two
# spellings were all an earlier version handled, which silently dropped 16 injectables
# — and those skewed new and exit-heavy, so the omission was not neutral.
_STR = re.compile(r"(\d*\.?\d+)\s*(mcg|mg|g)\b\s*"
                  r"(?:(?:/|\bper\b)\s*(\d*\.?\d+)?\s*(ml)\b)?", re.I)
_MUL = {"mcg": 0.001, "mg": 1.0, "g": 1000.0}


def strength(p):
    m = _STR.search(p or "")
    if not m:
        return None, None
    mg = float(m.group(1)) * _MUL[m.group(2).lower()]
    if not m.group(4):                       # no volume unit -> a mass, not a strength
        return mg, None
    per = float(m.group(3)) if m.group(3) else 1.0     # bare "per mL" means per 1 mL
    return mg, (mg / per if per else None)


def _med(v):
    return sorted(v)[len(v) // 2] if v else None


def build():
    rx = json.loads((S.DATA / "rxnorm.json").read_text())
    d = S.fda_rows()
    regs = S.registers()
    _, cd = S.shared_coded(regs)
    FR, AU = set(cd["FR"]), set(cd["AU"])
    insp, _n = I.inspections()

    rows = collections.defaultdict(list)
    for r in d:
        e = rx.get(clean(r.get("generic_name") or "")) or {}
        if S.sub_key(e):
            rows[S.sub_key(e)].append((r, e))

    out = {}
    for k, rs in rows.items():
        per_firm = collections.defaultdict(list)
        for r, _e in rs:
            for f in _flat(r.get("company_name")):
                per_firm[str(f)].append(r.get("status"))
        # a firm leaves a molecule only if EVERY package NDC it lists for it is going
        leaving = {f for f, sts in per_firm.items()
                   if all(s == "To Be Discontinued" for s in sts)}

        est, foreign, last = set(), set(), []
        for f in per_firm:
            for e in insp.get(I.firm(f), []):
                fei = e.get("FEINumber")
                if not fei:
                    continue
                est.add(fei)
                if e.get("CountryCode") and e["CountryCode"] != "US":
                    foreign.add(fei)
            ds = [e["InspectionEndDate"] for e in insp.get(I.firm(f), [])
                  if e.get("InspectionEndDate")]
            if ds:
                last.append((CAPTURE - dt.date.fromisoformat(max(ds))).days / 365.25)

        mg = [s for s, _ in (strength(r["presentation"]) for r, _e in rs) if s]
        cc = [c for _s, c in (strength(r["presentation"]) for r, _e in rs) if c]
        out[k] = {
            "name": next((e.get("ingredient") for _r, e in rs if e.get("ingredient")),
                         clean(rs[0][0].get("generic_name", "")).split()[0]),
            "age_y": (CAPTURE - min(_D(r["initial_posting_date"]) for r, _e in rs)).days / 365.25,
            "stale_y": (CAPTURE - max(_D(r["update_date"]) for r, _e in rs)).days / 365.25,
            "n_firms": len(per_firm),
            "n_ndc": len({r.get("package_ndc") for r, _e in rs}),
            "n_countries": 1 + (k in FR) + (k in AU),
            "exit_share": len(leaving) / len(per_firm),
            "is_exit": leaving == set(per_firm),
            "n_strengths": len(set(mg)),
            "strength_mg": _med(mg),
            "conc_mg_ml": _med(cc),
            "n_estab": len(est),
            "foreign_estab_share": (len(foreign) / len(est)) if est else None,
            "insp_recency_y": _med(last),
            "reverified": sum(1 for r, _e in rs if r.get("update_type") == "Reverified") / len(rs),
        }
    return out


def spearman(xs, ys):
    """Rank correlation on the pairs where BOTH are present, with n reported."""
    p = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(p) < 8:
        return None, len(p)
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):                       # average ranks within a tie group
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for t in range(i, j + 1):
                r[o[t]] = (i + j) / 2 + 1
            i = j + 1
        return r
    a, b = rank([x for x, _ in p]), rank([y for _, y in p])
    n = len(p)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return (num / den if den else None), n


if __name__ == "__main__":
    F = build()
    cols = ["age_y", "stale_y", "n_firms", "n_ndc", "n_countries", "exit_share",
            "n_strengths", "strength_mg", "conc_mg_ml", "n_estab",
            "foreign_estab_share", "insp_recency_y", "reverified"]
    print(f"{len(F)} substances\n")
    print(f"{'feature':22s} {'present':>9s}  {'min':>8s} {'median':>8s} {'max':>9s}")
    for c in cols:
        v = [F[k][c] for k in F if F[k][c] is not None]
        print(f"  {c:20s} {len(v):4d}/{len(F):<4d} {min(v):8.2f} {_med(v):8.2f} {max(v):9.2f}")
    print("\nSpearman, |rho| >= 0.25 only (n = pairs where both are present):")
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            r, n = spearman([F[k][a] for k in F], [F[k][b] for k in F])
            if r is not None and abs(r) >= 0.25:
                print(f"  {a:20s} {b:22s} rho {r:+.2f}  n={n}")
