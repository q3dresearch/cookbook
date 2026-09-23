#!/usr/bin/env python3
"""Does what a state generates, or what it sells, predict what electricity costs there?

    python3 price.py

The forecast work in figures 5 to 7 measured *demand* volatility. This asks the separate
question about **price**, which is not in the hourly grid feed at all -- EBA carries demand,
generation, interchange and CO2 and no prices. It is in the ELEC bulk file, which has sat
unused in this recipe until now.

**The unit is the state-quarter, 2001 to 2026**, which is a better join than anything else
here: price, generation mix and retail sales all share one geography and one frequency for
twenty-five years, with no balancing-authority-to-state mapping to fudge.

    ELEC.PRICE.{ST}-{SECTOR}.Q      average retail price, cents per kWh
    ELEC.GEN.{FUEL}-{ST}-99.Q       net generation by fuel, all sectors
    ELEC.SALES.{ST}-{SECTOR}.Q      retail sales, which gives the demand mix
    ELEC.COST_BTU.{FUEL}-{ST}-1.Q   what the fossil fuel itself cost

**Retail price is not wholesale price**, and the distinction decides what this can claim. A
retail tariff is set by a regulator, lags its inputs by months to years, and contains network
charges that have nothing to do with generation. So a weak relationship here is not evidence
that generation mix fails to move wholesale prices -- it is evidence that it does not reach
the retail bill quickly. Hourly locational marginal prices live with the ISOs and would need a
separate fetch; ERCOT already returns 403 to an honest bot.

**Volatility is the standard deviation of the year-over-year log change**, computed quarter by
quarter within each state. Year-over-year differencing removes the seasonal cycle and the
price level, which otherwise dominate: a state with expensive electricity is not the same as a
state with unstable electricity, and the raw standard deviation of price conflates them.

**The control that has to be in the model is the state's own fuel cost.** If gas-heavy states
have volatile prices, the interesting question is whether that survives holding what they paid
for gas -- otherwise the finding is "gas prices move", which nobody needs a model for.

**The aggregates have to come out, again.** ELEC carries `US`, `MTN`, `ENC`, `PCC` and the
other census regions in the same shape as the states. Ranking them together compares a
container against its own contents; see `shape.REGION` for the same trap in EBA.
"""
import collections, json, math, os, re, statistics, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
SRC = os.path.join(DATA, "eia-elec.zip")
CACHE = os.path.join(DATA, "price.json")

STATES = set("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS "
             "MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI "
             "WY".split())
P_PAT = re.compile(r"^ELEC\.PRICE\.([A-Z]{2})-(ALL|RES|COM|IND)\.Q$")
G_PAT = re.compile(r"^ELEC\.GEN\.([A-Z]{2,3})-([A-Z]{2})-(\d+)\.Q$")
S_PAT = re.compile(r"^ELEC\.SALES\.([A-Z]{2})-(ALL|RES|COM|IND)\.Q$")
C_PAT = re.compile(r"^ELEC\.COST_BTU\.([A-Z]{2,3})-([A-Z]{2})-(\d+)\.Q$")

GEN_SECTOR = "99"          # all sectors; 98 is electric power only
COST_SECTOR = "1"
# The one basket that does not double count. ELEC's fuel codes OVERLAP: AOR is "other
# renewables total" and already contains wind, solar, geothermal, wood and waste; TSN is all
# solar and equals SUN + DPV; SUN is utility scale and equals SPV + STH; and ALL sits in the
# same namespace as its own parts. Verified against ELEC's own ALL for 2024:
#   COW + NG + NUC + HYC + AOR + OOG + PEL + OTH + PC + HPS = 8,617 TWh = ALL.
# main() prints that ratio on every run, because the failure was silent and produced
# perfectly plausible percentages.
BASKET = ("COW", "NG", "NUC", "HYC", "AOR", "OOG", "PEL", "OTH", "PC", "HPS")
TOTAL = "ALL"              # the published total, used as the denominator directly
CLEAN = ("NUC", "HYC", "AOR")
VAR = ("WND", "SUN")       # weather-driven; SUN is utility scale, DPV is counted apart
FOSSIL = ("COW", "NG", "PEL", "PC", "OOG")
FROM = "2010"              # the window the volatility statistics are computed over


def qkey(s):
    return s if len(s) == 6 and "Q" in s else None


def build():
    if not os.path.exists(SRC):
        raise SystemExit("  eia-elec.zip missing - run eia.py ELEC")
    price = collections.defaultdict(dict)      # (st,sector) -> {q: cents}
    sales = collections.defaultdict(dict)
    gen = collections.defaultdict(dict)        # (st,fuel) -> {q: MWh}
    cost = collections.defaultdict(dict)       # (st,fuel) -> {q: $/MMBtu}
    with zipfile.ZipFile(SRC).open("ELEC.txt") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            sid = d.get("series_id", "")
            tgt = key = None
            m = P_PAT.match(sid)
            if m and m.group(1) in STATES:
                tgt, key = price, (m.group(1), m.group(2))
            if tgt is None:
                m = S_PAT.match(sid)
                if m and m.group(1) in STATES:
                    tgt, key = sales, (m.group(1), m.group(2))
            if tgt is None:
                m = G_PAT.match(sid)
                if m and m.group(2) in STATES and m.group(3) == GEN_SECTOR:
                    tgt, key = gen, (m.group(2), m.group(1))
            if tgt is None:
                m = C_PAT.match(sid)
                if m and m.group(2) in STATES and m.group(3) == COST_SECTOR:
                    tgt, key = cost, (m.group(2), m.group(1))
            if tgt is None:
                continue
            for stamp, v in (d.get("data") or []):
                q = qkey(str(stamp))
                if not q or q < FROM or v is None:
                    continue
                try:
                    tgt[key][q] = float(v)
                except (TypeError, ValueError):
                    pass

    def vol(series):
        """SD of the year-over-year log change: removes season and level."""
        q = sorted(series)
        ch = []
        for k in q:
            y, n = int(k[:4]), k[4:]
            prev = f"{y-1}{n}"
            a, b = series.get(prev), series[k]
            if a and b and a > 0 and b > 0:
                ch.append(math.log(b / a))
        return (statistics.pstdev(ch), statistics.mean(ch), len(ch)) if len(ch) >= 12 \
            else (None, None, len(ch))

    out = {"from": FROM, "state": {}}
    for st in sorted(STATES):
        p = price.get((st, "ALL")) or {}
        if len(p) < 20:
            continue
        pv, pd, pn = vol(p)
        # The same statistic on two DISJOINT halves, to ask whether volatility is a
        # property of the state or an exposure to one national event. And a price level
        # on the early window, so the two axes can be matched when that matters.
        pre18 = {k: v for k, v in p.items() if k < "2018"}
        post18 = {k: v for k, v in p.items() if k >= "2018"}
        ev, _, en = vol(pre18)
        lv, _, ln = vol(post18)
        # a per-year national panel of the year-over-year move, to find the shock
        yr = {}
        for k in sorted(p):
            prev = f"{int(k[:4])-1}{k[4:]}"
            if prev in p and p[prev] > 0 and p[k] > 0:
                yr.setdefault(k[:4], []).append(math.log(p[k] / p[prev]))
        g = {fu: s for (s2, fu), s in gen.items() if s2 == st}
        recent = [f"{y}Q{q}" for y in range(2022, 2027) for q in range(1, 5)]

        def fuel(k):
            return sum((g.get(k) or {}).get(q, 0.0) for q in recent)
        tot = fuel(TOTAL)                     # the PUBLISHED total, never a sum of parts
        basket = sum(fuel(k) for k in BASKET)

        def share(keys):
            return (sum(fuel(k) for k in keys) / tot) if tot else None
        # Herfindahl over the non-overlapping basket: 1.0 is one fuel, low is diversified
        hhi = sum((fuel(k) / basket) ** 2 for k in BASKET) if basket > 0 else None
        cs = [vol(s)[0] for (s2, fu), s in cost.items()
              if s2 == st and fu == "NG" and vol(s)[0] is not None]
        cl = [statistics.mean([v for k, v in s.items() if k >= "2022"] or [0])
              for (s2, fu), s in cost.items() if s2 == st and fu == "NG"]
        sl = {sec: (sales.get((st, sec)) or {}) for sec in ("ALL", "RES", "COM", "IND")}
        sl0 = sl["ALL"]
        stot = sum(sl["ALL"].get(q, 0.0) for q in recent) or None
        dp = fuel("DPV")                      # not part of ALL: it never reaches the grid
        # An EARLY price and a LATE rooftop share, to test which way the arrow points.
        early = [v for k, v in p.items() if "2010" <= k < "2015"]
        dp_e = sum((g.get("DPV") or {}).get(f"{y}Q{q}", 0.0)
                   for y in range(2016, 2018) for q in range(1, 5))
        s_e = sum(sl0.get(f"{y}Q{q}", 0.0)
                  for y in range(2016, 2018) for q in range(1, 5)) if sl0 else 0.0
        out["state"][st] = {
            "price": statistics.mean(v for k, v in p.items() if k >= "2022")
            if any(k >= "2022" for k in p) else None,
            "price_vol": pv, "price_drift": pd, "n": pn,
            "vol_early": ev, "vol_late": lv, "n_early": en, "n_late": ln,
            "price_late": statistics.mean(post18.values()) if post18 else None,
            "price_pre18": statistics.mean(pre18.values()) if pre18 else None,
            "yr_move": {y: (sum(abs(x) for x in v) / len(v)) for y, v in yr.items()
                        if len(v) >= 3},
            "gas": share(["NG"]), "coal": share(["COW"]), "nuclear": share(["NUC"]),
            "var_ren": share(VAR), "clean": share(CLEAN), "hydro": share(["HYC"]),
            "fossil": share(FOSSIL), "hhi": hhi,
            "gas_cost_vol": cs[0] if cs else None,
            "gas_cost": cl[0] if cl else None,
            "dpv_share": (dp / stot) if stot else None,
            "basket_over_all": (basket / tot) if tot else None,
            "price_early": statistics.mean(early) if early else None,
            "dpv_early": (dp_e / s_e) if s_e else None,
            "ind_share": (sum(sl["IND"].get(q, 0.0) for q in recent) / stot)
            if stot else None,
            "res_share": (sum(sl["RES"].get(q, 0.0) for q in recent) / stot)
            if stot else None,
            "twh": tot / 1000 if tot else None}
    return out


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    print("  folding ELEC price, generation, sales and fuel cost ...", flush=True)
    d = build()
    tmp = CACHE + ".tmp"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return d


def corr(pairs):
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
    n = len(pairs)
    if n < 8:
        return None, None, n
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]

    def pe(xs, ys):
        mx, my = sum(xs) / n, sum(ys) / n
        sx = sum((x - mx) ** 2 for x in xs) ** .5
        sy = sum((y - my) ** 2 for y in ys) ** .5
        return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy) \
            if sx and sy else None

    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for pos, i in enumerate(o):
            r[i] = float(pos)
        return r
    return pe(xs, ys), pe(rk(xs), rk(ys)), n


PRED = [("gas", "gas share of generation"), ("coal", "coal share"),
        ("nuclear", "nuclear share"), ("var_ren", "wind + solar share"),
        ("clean", "carbon-free share"), ("hydro", "hydro share"),
        ("hhi", "fuel-mix concentration (Herfindahl)"),
        ("dpv_share", "rooftop solar, share of retail sales"),
        ("gas_cost_vol", "volatility of the state's own gas cost"),
        ("gas_cost", "level of the state's own gas cost"),
        ("ind_share", "industrial share of retail sales"),
        ("res_share", "residential share of retail sales")]


def main():
    d = load()
    st = d["state"]
    ok = [v for v in st.values() if v.get("price_vol") is not None]
    print(f"\n  {len(st)} states folded, {len(ok)} with a usable price series from "
          f"{d['from']}")
    bo = [v["basket_over_all"] for v in st.values()
          if v.get("basket_over_all") is not None]
    print(f"  COVERAGE CHECK, basket over published ALL: median "
          f"{statistics.median(bo):.4f}, range {min(bo):.4f} to {max(bo):.4f}  "
          f"(1.0000 = no double count)")
    print(f"  price level median {statistics.median(v['price'] for v in ok if v['price']):.2f} "
          f"cents/kWh; volatility median "
          f"{statistics.median(v['price_vol'] for v in ok):.3f}")
    for out, lab in (("price_vol", "PRICE VOLATILITY (sd of year-over-year log change)"),
                     ("price", "PRICE LEVEL, cents per kWh"),
                     ("price_drift", "PRICE DRIFT (mean year-over-year log change)")):
        print(f"\n  WHAT PREDICTS {lab}")
        print(f"  {'predictor':<42}{'n':>5}{'Pearson':>10}{'Spearman':>10}")
        for k, name in PRED:
            p, s, n = corr([(v.get(k), v.get(out)) for v in st.values()])
            f = lambda x: f"{x:+.2f}" if x is not None else "  . "
            print(f"  {name:<42}{n:>5}{f(p):>10}{f(s):>10}")
    top = sorted(ok, key=lambda v: -v["price_vol"])[:5]
    bot = sorted(ok, key=lambda v: v["price_vol"])[:5]
    inv = {id(v): k for k, v in st.items()}
    print(f"\n  most volatile: " + ", ".join(
        f"{inv[id(v)]} {v['price_vol']:.3f}" for v in top))
    print(f"  least volatile: " + ", ".join(
        f"{inv[id(v)]} {v['price_vol']:.3f}" for v in bot))
    return 0


if __name__ == "__main__":
    sys.exit(main())


# --- joint model -----------------------------------------------------------------
# Generation shares are compositional: gas against wind+solar is -0.52, coal against
# industrial share +0.53. One column at a time is not answerable, and coal + hydro + other
# is left out as the omitted base so the remaining three are interpretable.

KEYS = ["gas", "var_ren", "nuclear", "ind_share"]
ISLANDS = ("HI", "AK")        # oil-fired, unconnected, and they drive the renewable result


def regress(rows, keys, ykey):
    """Standardised OLS. Returns (betas, R2, n), everything in SD units."""
    data = []
    for r in rows:
        xs = [r.get(k) for k in keys]
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
    return dict(zip(keys, beta[1:])), 1 - ss / tt, n


def mainland(d):
    return [v for k, v in d["state"].items() if k not in ISLANDS]


# --- Shapley decomposition of R-squared (the LMG metric) ---------------------------
# A standardised OLS coefficient is NOT a Shapley value. It answers "move this one standard
# deviation and hold the rest still" -- an EFFECT, which keeps its sign. With correlated
# predictors it also hands the variance they share to whichever one the algebra favours, so
# it is a poor measure of IMPORTANCE.
#
# The Shapley value for R-squared -- the LMG metric of Lindeman, Merenda and Gold -- averages
# each predictor's incremental R-squared over every order the predictors could enter in. It
# splits shared variance evenly by construction, it sums exactly to the model's R-squared,
# and it is always non-negative, which means it LOSES THE SIGN. The two are complements:
# Shapley says how much a variable owns, the coefficient says which way it pushes.
#
# Computed exactly over all 2^p subsets rather than sampled, which is affordable below about
# a dozen predictors and avoids a stochastic answer in a figure that must rebuild identically.

import itertools                                                          # noqa: E402


def _r2(rows, keys, ykey):
    data = []
    for r in rows:
        xs = [r.get(k) for k in keys]
        y = r.get(ykey)
        if y is None or any(x is None for x in xs):
            continue
        data.append((xs, y))
    n, p = len(data), len(keys)
    if n < p + 2:
        return None
    if p == 0:
        return 0.0
    cols = [[d[0][j] for d in data] for j in range(p)]
    mu = [sum(c) / n for c in cols]
    sd = [max((sum((v - m) ** 2 for v in c) / n) ** .5, 1e-12) for c, m in zip(cols, mu)]
    ys = [d[1] for d in data]
    my = sum(ys) / n
    sy = max((sum((v - my) ** 2 for v in ys) / n) ** .5, 1e-12)
    X = [[1.0] + [(d[0][j] - mu[j]) / sd[j] for j in range(p)] for d in data]
    Y = [(v - my) / sy for v in ys]
    m = p + 1
    A = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(m)]
         + [sum(X[i][a] * Y[i] for i in range(n))] for a in range(m)]
    for c in range(m):
        piv = max(range(c, m), key=lambda k: abs(A[k][c]))
        A[c], A[piv] = A[piv], A[c]
        if abs(A[c][c]) < 1e-9:
            return None
        for k in range(m):
            if k == c:
                continue
            f = A[k][c] / A[c][c]
            for j in range(c, m + 1):
                A[k][j] -= f * A[c][j]
    beta = [A[i][m] / A[i][i] for i in range(m)]
    pred = [sum(beta[j] * X[i][j] for j in range(m)) for i in range(n)]
    ss = sum((Y[i] - pred[i]) ** 2 for i in range(n))
    tt = sum(v * v for v in Y) or 1e-12
    return max(0.0, 1 - ss / tt)


def shapley(rows, keys, ykey):
    """Exact Shapley decomposition of R-squared. Returns (per-key share, total R2, n)."""
    keys = list(keys)
    p = len(keys)
    # every model is fitted on the SAME rows, or the subsets are not comparable
    rows = [r for r in rows
            if r.get(ykey) is not None and all(r.get(k) is not None for k in keys)]
    n = len(rows)
    cache = {}
    for size in range(p + 1):
        for sub in itertools.combinations(range(p), size):
            cache[sub] = _r2(rows, [keys[i] for i in sub], ykey)
    fact = [1]
    for i in range(1, p + 1):
        fact.append(fact[-1] * i)
    out = {k: 0.0 for k in keys}
    for i, k in enumerate(keys):
        rest = [j for j in range(p) if j != i]
        for size in range(p):
            w = fact[size] * fact[p - size - 1] / fact[p]
            for sub in itertools.combinations(rest, size):
                a, b = cache.get(sub), cache.get(tuple(sorted(sub + (i,))))
                if a is None or b is None:
                    continue
                out[k] += w * (b - a)
    return out, cache[tuple(range(p))], n
