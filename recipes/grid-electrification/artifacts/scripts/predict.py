#!/usr/bin/env python3
"""What actually predicts how hard a grid is to forecast, and who forecasts it well.

    python3 predict.py

Two different outcomes, deliberately kept apart:

- **difficulty** -- the error a naive same-hour-last-week forecast makes, as a share of mean
  demand. This is the honest measure of "volatility": it is how much the load moves in ways
  a calendar cannot anticipate.
- **skill** -- how far the operator's own day-ahead forecast beats that baseline, after
  correcting for scope. Difficulty is a property of the grid; skill is a property of the
  forecaster, and a predictor of one need not predict the other.

**The candidate predictors, and which are honestly available.**

| asked for | what is used | where it comes from |
| --- | --- | --- |
| grid mix, renewable share | wind + solar share of the BA's own generation | EBA, in-dataset |
| temperature | seasonal amplitude: hottest monthly mean over coldest | EBA, in-dataset proxy |
| population | state population | SEDS |
| industry mix | industrial share of the state's electricity, and its price | SEDS |
| data centre appearances | PeeringDB facilities and network presences in the state | PeeringDB |
| -- | grid size in GW, and load flatness | EBA, as controls |

**Temperature is a proxy, not a measurement.** No temperature series is fetched here. A grid
whose hottest month averages twice its mildest is weather-driven and one whose months are
flat is not, and that ratio is computable from the demand itself. It confounds air
conditioning with anything else seasonal, and it is named as a proxy wherever it appears.

**Three of the predictors need a state, and a balancing authority is not a state.** PJM,
MISO, SPP, Bonneville, PacifiCorp and WACM span many, so they are **excluded from those three
tests and kept in the rest**, rather than being assigned a state that would be mostly wrong.
Every mapping below is one balancing authority whose footprint sits inside one state, and the
count of usable rows is printed with every correlation, because it is much smaller than the
count for the in-dataset predictors.

**Size is the control that eats findings here.** Mean demand runs from about 0.05 GW to over
100 GW. Every correlation is reported raw and again within the grids above 2 GW, and a
predictor that only works across that span is reporting size.
"""
import collections, json, math, os, re, statistics, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
sys.path.insert(0, HERE)
import shape, skill as SK                                                 # noqa: E402

SEDS = os.path.join(DATA, "eia-seds.zip")
CACHE = os.path.join(DATA, "predictors.json")
YEAR = "2025"
SEDS_YEAR = "2023"          # the last year SEDS sector series are complete
CLEAN_VAR = ("SUN", "WND")  # the weather-driven half of the generation mix

# One balancing authority, one state, only where the footprint genuinely sits inside it.
# The multi-state RTOs are absent on purpose: PJM, MISO, SWPP, BPAT, PACE, PACW, WACM,
# WAUW, SOCO, ISNE and SPA each span several, and assigning one would be mostly wrong.
BA_STATE = {
    "ERCO": "TX", "CISO": "CA", "LDWP": "CA", "BANC": "CA", "TIDC": "CA", "IID": "CA",
    "NYIS": "NY", "AZPS": "AZ", "SRP": "AZ", "TEPC": "AZ", "PSCO": "CO", "NWMT": "MT",
    "IPCO": "ID", "NEVP": "NV", "PNM": "NM", "EPE": "TX", "SCL": "WA", "TPWR": "WA",
    "PSEI": "WA", "CHPD": "WA", "DOPD": "WA", "GCPD": "WA", "PGE": "OR", "JEA": "FL",
    "TEC": "FL", "FPL": "FL", "FPC": "FL", "GVL": "FL", "TAL": "FL", "SEC": "FL",
    "FMPP": "FL", "HST": "FL", "DUK": "NC", "CPLE": "NC", "CPLW": "NC", "SCEG": "SC",
    "SC": "SC", "LGEE": "KY", "AECI": "MO", "TVA": "TN", "AVA": "WA",
}
SEDS_PAT = re.compile(r"^SEDS\.([A-Z]{5})\.([A-Z]{2})\.A$")
SEDS_CODES = ("ESICB", "ESCCB", "ESRCB", "ESTCB", "ESICD", "TPOPP")


def seds():
    """State electricity by sector, industrial price and population."""
    out = collections.defaultdict(dict)
    if not os.path.exists(SEDS):
        return {}
    with zipfile.ZipFile(SEDS).open("SEDS.txt") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            m = SEDS_PAT.match(d.get("series_id", ""))
            if not m or m.group(1) not in SEDS_CODES:
                continue
            for stamp, v in (d.get("data") or []):
                if str(stamp) == SEDS_YEAR and v is not None:
                    try:
                        out[m.group(2)][m.group(1)] = float(v)
                    except (TypeError, ValueError):
                        pass
    return dict(out)


def peeringdb():
    p = os.path.join(DATA, "peeringdb-fac.json")
    if not os.path.exists(p):
        return {}
    agg = collections.defaultdict(lambda: {"fac": 0, "net": 0})
    for f in json.load(open(p)):
        if f.get("country") != "US" or f.get("status") != "ok":
            continue
        st = (f.get("state") or "").strip().upper()[:2]
        if len(st) != 2:
            continue
        agg[st]["fac"] += 1
        agg[st]["net"] += int(f.get("net_count") or 0)
    return dict(agg)


def build():
    sk = SK.load()
    ann = json.load(open(os.path.join(DATA, "eba-annual.json")))["ba"]
    shp = json.load(open(os.path.join(DATA, "eba-hourly.json")))["shape"]
    st, pdb = seds(), peeringdb()
    rows = []
    for ba, yrs in sk["ba"].items():
        # The 14 EIA REGION codes are sums of the balancing authorities beside them --
        # TEN is TVA, NE is ISNE, CAL contains CISO. Leaving them in double-counts and
        # breaks independence, because a region and its members are not separate grids.
        if ba in shape.REGION:
            continue
        v = yrs.get(YEAR)
        if not v:
            continue
        gen = {k[3:]: (s.get(YEAR) or 0.0) for k, s in (ann.get(ba) or {}).items()
               if k.startswith("NG.")}
        tot = sum(gen.values())
        r = {"ba": ba, "gw": v["mean_mw"] / 1000,
             "difficulty": v["nmae_naive"], "skill": v["skill_adj"],
             "nmae": v["nmae_adj"], "p99": v["p99"], "peak_bias": v["peak_bias"],
             "season": v.get("season"),
             "var_share": (sum(gen.get(k, 0.0) for k in CLEAN_VAR) / tot) if tot else None,
             "flat": (shp.get(ba, {}).get(YEAR, {}) or {}).get("ratio")}
        s = BA_STATE.get(ba)
        if s and s in st:
            e = st[s]
            tot_e = e.get("ESTCB")
            r["state"] = s
            r["ind_share"] = (e["ESICB"] / tot_e) if tot_e and e.get("ESICB") else None
            r["ind_price"] = e.get("ESICD")
            r["pop"] = e.get("TPOPP")
            d = pdb.get(s)
            if d and e.get("TPOPP"):
                r["fac_per_m"] = d["fac"] / (e["TPOPP"] / 1000)
                r["net_per_m"] = d["net"] / (e["TPOPP"] / 1000)
                r["fac"] = d["fac"]
        rows.append(r)
    return {"year": YEAR, "seds_year": SEDS_YEAR, "rows": rows}


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    d = build()
    tmp = CACHE + ".tmp"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return d


def corr(pairs):
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None
             and not (isinstance(a, float) and math.isnan(a))]
    n = len(pairs)
    if n < 6:
        return None, None, n
    xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]

    def pear(xs, ys):
        mx, my = sum(xs) / n, sum(ys) / n
        sx = sum((x - mx) ** 2 for x in xs) ** .5
        sy = sum((y - my) ** 2 for y in ys) ** .5
        return (sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)
                if sx and sy else None)

    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0.0] * len(v)
        for pos, i in enumerate(o):
            rk[i] = float(pos)
        return rk
    return pear(xs, ys), pear(rank(xs), rank(ys)), n


PRED = [("gw", "grid size, GW (log)", True),
        ("season", "seasonal amplitude (temperature proxy)", False),
        ("var_share", "wind + solar share of own generation", False),
        ("flat", "load flatness, trough over peak", False),
        ("ind_share", "industrial share of state electricity", False),
        ("ind_price", "industrial electricity price", False),
        ("pop", "state population (log)", True),
        ("fac", "PeeringDB facilities in state (log)", True),
        ("fac_per_m", "facilities per million people", False),
        ("net_per_m", "network presences per million", False)]


def table(rows, outcome, label):
    print(f"\n  WHAT PREDICTS {label.upper()}   ({outcome})")
    print(f"  {'predictor':<42}{'n':>5}{'Pearson':>10}{'Spearman':>10}"
          f"{'  above 2 GW':>16}")
    for key, name, lg in PRED:
        def val(r):
            v = r.get(key)
            if v is None or v <= 0 and lg:
                return None
            return math.log10(v) if lg else v
        p, s, n = corr([(val(r), r.get(outcome)) for r in rows])
        big = [r for r in rows if r["gw"] >= 2]
        p2, s2, n2 = corr([(val(r), r.get(outcome)) for r in big])
        f = lambda x: f"{x:+.2f}" if x is not None else "  . "
        print(f"  {name:<42}{n:>5}{f(p):>10}{f(s):>10}"
              f"{f(p2) + ' (n=' + str(n2) + ')':>16}")


def main():
    d = load()
    rows = d["rows"]
    print(f"\n  {len(rows)} balancing authorities, {d['year']}; state predictors from "
          f"SEDS {d['seds_year']}")
    print(f"  {sum(1 for r in rows if r.get('state'))} carry a single-state mapping")
    table(rows, "difficulty", "how hard the grid is to forecast")
    table(rows, "skill", "how well the operator beats the naive baseline")
    table(rows, "p99", "the tail: 99th percentile absolute error")
    print(f"\n  difficulty (naive error) median "
          f"{statistics.median(r['difficulty'] for r in rows):.2%}, range "
          f"{min(r['difficulty'] for r in rows):.2%} to "
          f"{max(r['difficulty'] for r in rows):.2%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


# --- joint model -----------------------------------------------------------------
# Every raw correlation above is a marginal one, and these predictors are correlated with
# each other: flatness against industrial share is +0.67, against log size +0.46. So the
# question "does X predict difficulty" is not answerable one column at a time.

MODEL_A = [("gw", True), ("flat", False), ("season", False), ("var_share", False)]
MODEL_B = MODEL_A + [("fac_per_m", False)]


def regress(rows, keys, ykey):
    """Standardised OLS. Returns (betas, R2, n) with every variable in SD units."""
    def g(r, k, lg):
        v = r.get(k)
        if v is None or (lg and v <= 0):
            return None
        return math.log10(v) if lg else v
    data = []
    for r in rows:
        xs = [g(r, k, lg) for k, lg in keys]
        y = r.get(ykey)
        if y is None or any(x is None for x in xs):
            continue
        data.append((xs, y))
    n, p = len(data), len(keys)
    if n < p + 4:
        return None
    cols = [[d[0][j] for d in data] for j in range(p)]
    mu = [sum(c) / n for c in cols]
    sd = [max((sum((v - m) ** 2 for v in c) / n) ** .5, 1e-12) for c, m in zip(cols, mu)]
    ys = [d[1] for d in data]
    my = sum(ys) / n
    sy = max((sum((v - my) ** 2 for v in ys) / n) ** .5, 1e-12)
    X = [[1.0] + [(d[0][j] - mu[j]) / sd[j] for j in range(p)] for d in data]
    Yv = [(v - my) / sy for v in ys]
    m = p + 1
    A = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(m)]
         + [sum(X[i][a] * Yv[i] for i in range(n))] for a in range(m)]
    for c in range(m):
        piv = max(range(c, m), key=lambda k: abs(A[k][c]))
        A[c], A[piv] = A[piv], A[c]
        if abs(A[c][c]) < 1e-10:
            return None
        for k in range(m):
            if k == c:
                continue
            f = A[k][c] / A[c][c]
            for j in range(c, m + 1):
                A[k][j] -= f * A[c][j]
    beta = [A[i][m] / A[i][i] for i in range(m)]
    pred = [sum(beta[j] * X[i][j] for j in range(m)) for i in range(n)]
    ss = sum((Yv[i] - pred[i]) ** 2 for i in range(n))
    tt = sum(v * v for v in Yv) or 1e-12
    return dict(zip([k for k, _ in keys], beta[1:])), 1 - ss / tt, n


def marginal(rows, key, lg, ykey):
    """The plain Pearson correlation, for the same rows the joint model would use."""
    def g(r):
        v = r.get(key)
        if v is None or (lg and v <= 0):
            return None
        return math.log10(v) if lg else v
    p, _, n = corr([(g(r), r.get(ykey)) for r in rows])
    return p, n
