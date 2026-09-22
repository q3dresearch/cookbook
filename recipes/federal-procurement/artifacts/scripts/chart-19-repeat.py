#!/usr/bin/env python3
"""Winning ten thousand times pays the same per award as winning once.

    python3 chart-19-repeat.py

Q4 of this recipe -- *who wins repeatedly, and does that change what they are paid* -- asked
two things and only the first was ever answered. Figure 3 settled the concentration half:
half the dollars reach 74 parent recipients and half the awards 994, and they are almost
entirely different firms. This is the second half.

**The price of an award does not move with how often its winner wins.** Group the 73,431
parent recipients by how many FY2016 awards they took and the median award is flat across
four orders of magnitude of award count: $6,950 for a firm that won once, $9,796 at a dozen,
$8,190 for the forty firms above a thousand. Fitted continuously over twenty award-count
bins the slope is **x1.02 per tenfold increase in awards won, 95% CI 0.97 to 1.08** --
straddling one. On the award-level version of the same fit it is x1.01 (CI 0.97 to 1.05),
and the award-level Spearman correlation between an award's value and its winner's award
count is **+0.004 on 554,005 awards**. The bound is tight enough to matter: a premium of
**+5.3% per tenfold** would have cleared the 95% interval, and +10% would have cleared it
twice over. Incumbency is not paid for in the size of the cheque.

**What does move is the instrument.** The share of a firm's awards placed as orders against
a parent contract runs **12.1% for one-time winners to 70.8% at 300-999 awards**. That is
not an award-size artefact: standardised on the award's own value stratum and product family
-- the two things that would otherwise explain it -- the expected share only moves between
48.2% and 58.7%, so small winners sit **36 points below** what their mix predicts and large
ones **12 points above**, and the two cross at about twenty awards a year. It is not a
firm-size artefact either: inside the awards the contracting officer marked small-business it
runs 12.2% to 76.5%, a *steeper* gradient than the pooled one. 52,296 parents (71.2%) placed
no vehicle order at all in FY2016 and won a median of 1 award each; the largest of them took
632.

**Two rival explanations were measured and both failed.** Reserved awards look like the
story -- set-aside share falls from 36.9% at one award to 2.3% above a thousand -- but the
whole of that is business size: inside small-business awards it is 48.4% at one award and
still 42.3% at 300-999, moving only in the top band. And single bids look like the story at
the very top -- 75.8% for the forty largest winners against 53.8% for one-time winners --
but standardised on size and product family the excess is between -3.8 and +5.1 points at
every award count, and the forty firms in the top band run from **1.3% to 99.2%** singly.
A band-level rate there is an average over two populations, not a level.

**The ranking is not an artefact of name cleaning, which was worth checking.** Q27: ranking
on `recipient_parent_name_raw` -- what the filer typed -- instead of the cleaned parent name
keeps **96 of the cleaned top 100** and 960 of the top 1,000 inside the same cut, and moves
the top-100 award share only from 25.3% to 24.2%. `recipient_parent_uei` reproduces the
cleaned ranking to two decimal places (25.3%). 953 cleaned parents carry more than one raw
spelling and they hold 18.1% of all awards, so the cleaning is doing real work where the
mass is -- it just is not doing it to the answer.

**Method, since it is not on the plate.** Award value is the sum of
`federal_action_obligation` over the award's transactions, de-obligations kept. Single-bid
rates use the first non-blank `number_of_offers_received` per award, a recorded zero being a
filing artefact, which leaves 550,811 awards with a usable count. Expected shares are
indirect standardisation on the award's own value stratum crossed with its product-service
family, falling back to the value stratum alone below 40 awards in a cell (0.50% of awards).
Both fits weight each award-count bin equally, so the 36,991 one-time winners do not set the
slope alone. The pooled vehicle line dips in the top band, but the match beneath it dips too:
the excess over it is +9.9, +12.1 and +11.4 points across the last three bands.

**Limits.** Eleven civilian departments, 8.5% of federal contract awards; Defense and
General Services are absent. De-obligations are kept, so 19.8% of awards net zero or less
and 26.0% of one-time winners' awards do -- which is why the first box has no bottom.
"Parent" is the register's own field, not an independent ownership source.
"""
import bisect, collections, math, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate, q4rep                                                      # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "19-repeat.svg")
RED, BLUE, SLATE = "#8c2318", "#2f6f96", "#9aa4ad"

# award-count bands. Drawn at the geometric mean of their members' actual counts, so the
# horizontal position is the award count itself rather than a bin index.
BANDS = [(1, 1), (2, 2), (3, 4), (5, 9), (10, 19), (20, 49), (50, 99), (100, 299),
         (300, 999), (1000, 10 ** 9)]
# finer bins for the continuous fit, because ten bins invite a curve that is not there
FINE = [1, 2, 3, 4, 6, 8, 12, 17, 24, 34, 48, 68, 96, 136, 192, 272, 384, 543, 768, 1086,
        10 ** 9]
# award-value strata for the standardisation. Negative and exactly-zero awards get their
# own strata: 19.8% of awards land there and a quantile cut would put a boundary inside
# the zero block.
EDGES = [1e3, 3e3, 1e4, 3e4, 1e5, 3e5, 1e6, 1e7]
MIN_STRAT = 40                       # below this the stratum falls back to size alone
NAMED = {"MEDTRONIC INC": ("Medtronic", -10, -17, "end"),
         "MCKESSON CORPORATION": ("McKesson", -10, 5, "end")}


def size_band(v):
    if v < 0:
        return 0
    if v == 0:
        return 1
    return 2 + bisect.bisect_left(EDGES, v)


def quant(sorted_vals, p):
    return sorted_vals[int(p * (len(sorted_vals) - 1))]


def fit(xs, ys):
    """OLS of y on x, with the standard error of the slope. Both already in log10."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((a - mx) ** 2 for a in xs)
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    syy = sum((b - my) ** 2 for b in ys)
    sl = sxy / sxx
    ic = my - sl * mx
    res = [b - (ic + sl * a) for a, b in zip(xs, ys)]
    se = math.sqrt(sum(e * e for e in res) / (n - 2) / sxx)
    return sl, ic, se, sxy / math.sqrt(sxx * syy)


def spearman(pairs):
    n = len(pairs)

    def rk(f):
        o = sorted(range(n), key=lambda i: f(pairs[i]))
        r, i = [0.0] * n, 0
        while i < n:
            j = i
            while j + 1 < n and f(pairs[o[j + 1]]) == f(pairs[o[i]]):
                j += 1
            v = (i + j) / 2 + 1
            for t in range(i, j + 1):
                r[o[t]] = v
            i = j + 1
        return r
    a, b = rk(lambda p: p[0]), rk(lambda p: p[1])
    m1, m2 = sum(a) / n, sum(b) / n
    num = sum((p - m1) * (q - m2) for p, q in zip(a, b))
    den = math.sqrt(sum((p - m1) ** 2 for p in a) * sum((q - m2) ** 2 for q in b))
    return num / den


# ---------------------------------------------------------------- data

def fold():
    d = q4rep.load()
    V, R = d["vocab"], d["rows"]
    c = {k: i for i, k in enumerate(d["cols"])}
    P, OBL, BID, FAM, SA, VEH, BZ = (c[k] for k in ("parent", "obl", "bids", "psc_family",
                                                    "set_aside", "on_vehicle", "biz_size"))
    nosa = {i for i, s in enumerate(V["set_aside"]) if s in ("NONE", "")}
    small = V["biz_size"].index("S")

    # 166 awards carry no parent name at all. They cannot be attributed to a firm and
    # lumping them together would invent a 166-award recipient, so they leave the base.
    blank = V["parent"].index("") if "" in V["parent"] else -1
    R = [r for r in R if r[P] != blank]
    cnt = collections.Counter(r[P] for r in R)
    byfirm = collections.defaultdict(list)
    for r in R:
        byfirm[r[P]].append(r)

    # national rates per stratum, for indirect standardisation
    cell = collections.defaultdict(lambda: [0, 0, 0, 0, 0])      # n, veh, sa, bid_n, single
    size = collections.defaultdict(lambda: [0, 0, 0, 0, 0])
    for r in R:
        b = size_band(r[OBL])
        for t in (cell[(b, r[FAM])], size[b]):
            t[0] += 1
            t[1] += r[VEH]
            t[2] += r[SA] not in nosa
            if r[BID] > 0:
                t[3] += 1
                t[4] += r[BID] == 1
    fell = [0]

    def expect(r, i, dn):
        b = size_band(r[OBL])
        t = cell[(b, r[FAM])]
        if t[dn] < MIN_STRAT:
            fell[0] += 1
            t = size[b]
        return t[i] / t[dn] if t[dn] else 0.0

    rows = []
    for lo, hi in BANDS:
        ks = [k for k, n in cnt.items() if lo <= n <= hi]
        aws = [r for k in ks for r in byfirm[k]]
        sb = [r for r in aws if r[BID] > 0]
        sm = [r for r in aws if r[BZ] == small]
        smb = [r for r in sm if r[BID] > 0]
        med = sorted(st.median(x[OBL] for x in byfirm[k]) for k in ks)
        rows.append({
            "lo": lo, "hi": hi, "firms": len(ks), "awards": len(aws),
            "gm": math.exp(sum(math.log(cnt[k]) for k in ks) / len(ks)),
            "p25": quant(med, .25), "p50": quant(med, .50), "p75": quant(med, .75),
            "p10": quant(med, .10), "p90": quant(med, .90),
            "aw_med": st.median(r[OBL] for r in aws),
            "zero": sum(1 for r in aws if r[OBL] <= 0) / len(aws),
            "veh": sum(r[VEH] for r in aws) / len(aws),
            "veh_exp": sum(expect(r, 1, 0) for r in aws) / len(aws),
            "veh_sm": sum(r[VEH] for r in sm) / len(sm),
            "sm_n": len(sm),
            "sa": sum(1 for r in aws if r[SA] not in nosa) / len(aws),
            "sa_exp": sum(expect(r, 2, 0) for r in aws) / len(aws),
            "sa_sm": sum(1 for r in sm if r[SA] not in nosa) / len(sm),
            "bid_n": len(sb),
            "sb": sum(1 for r in sb if r[BID] == 1) / len(sb),
            "sb_exp": sum(expect(r, 4, 3) for r in sb) / len(sb),
            "sb_sm": sum(1 for r in smb if r[BID] == 1) / len(smb),
        })

    # the continuous fit, on the firm-median series and again award-level
    fb = collections.defaultdict(list)
    for k, n in cnt.items():
        fb[bisect.bisect_right(FINE, n) - 1].append(k)
    fx, fy, fine = [], [], []
    for i in sorted(fb):
        ks = fb[i]
        m = st.median(st.median(x[OBL] for x in byfirm[k]) for k in ks)
        g = math.exp(sum(math.log(cnt[k]) for k in ks) / len(ks))
        fine.append((g, m, len(ks)))
        if m > 0:
            fx.append(math.log10(g))
            fy.append(math.log10(m))
    slope, icpt, se, rr = fit(fx, fy)

    ab = collections.defaultdict(list)
    for r in R:
        ab[bisect.bisect_right(FINE, cnt[r[P]]) - 1].append(r[OBL])
    ax, ay = [], []
    for i in sorted(ab):
        m = st.median(ab[i])
        ks = fb[i]
        g = math.exp(sum(math.log(cnt[k]) for k in ks) / len(ks))
        if m > 0:
            ax.append(math.log10(g))
            ay.append(math.log10(m))
    aslope, _, ase, _ = fit(ax, ay)

    big = sorted(((cnt[k], st.median(x[OBL] for x in byfirm[k]), V["parent"][k])
                  for k in byfirm if cnt[k] >= 100), reverse=True)
    big_zero = sum(1 for _, m, _ in big if m <= 0)
    novehicle = [len(v) for k, v in byfirm.items() if not any(x[VEH] for x in v)]
    top = [(sum(1 for x in byfirm[k] if x[BID] == 1) /
            max(1, sum(1 for x in byfirm[k] if x[BID] > 0)), cnt[k], V["parent"][k])
           for k in byfirm if cnt[k] >= 1000]
    top.sort()

    return {
        "rows": rows, "fine": fine, "big": big, "big_zero": big_zero, "top": top,
        "slope": slope, "icpt": icpt, "se": se, "r2": rr * rr,
        "aslope": aslope, "ase": ase,
        "rho": spearman([(cnt[r[P]], r[OBL]) for r in R]),
        "firms": len(cnt), "awards": len(R), "all_awards": len(d["rows"]),
        "n_tx": d["n_tx"], "net": d["net"],
        "n_neg": d["n_neg"], "pos_only": d["pos_only"],
        "bid_n": sum(1 for r in R if r[BID] > 0),
        "zero": sum(1 for r in R if r[OBL] <= 0) / len(R),
        "novehicle": len(novehicle), "novehicle_med": st.median(novehicle),
        "novehicle_aw": sum(novehicle), "fellback": fell[0],
    }




# ---------------------------------------------------------------- draw

def main():
    D = fold()
    rows, W = D["rows"], 1200
    AX = 28
    NMAX = max(n for n, _, _ in D["big"])
    XMAX = math.log10(NMAX) * 1.055
    ax0, apw = AX + 74, W - AX - 74 - 268
    px = lambda n: ax0 + apw * (math.log10(max(n, 1)) / XMAX)
    RX = W - 252

    ATOP, ABOT = 214, 542
    YLO, YHI = 300.0, 100000.0
    lyr = math.log10(YHI) - math.log10(YLO)
    py = lambda v: ABOT - (ABOT - ATOP) * ((math.log10(v) - math.log10(YLO)) / lyr)
    BTOP, BBOT = 646, 858
    qy = lambda f: BBOT - (BBOT - BTOP) * (f / 0.80)

    # Source, base and one caveat. The estimator, the strata and the robustness checks are
    # in the docstring -- see doctrine/what-a-footnote-carries.md.
    foot = (
        f"USAspending API v2 bulk download; FY2016 contract transactions from eleven "
        f"civilian departments, 8.5% of federal contract awards - Defense and General "
        f"Services are absent, so this is not federal procurement as a whole. "
        f"{D['n_tx']:,} transactions collapse to {D['all_awards']:,} awards and "
        f"${D['net']/1e9:,.2f}bn net; the {D['awards']:,} naming a parent recipient are "
        f"the base. De-obligations are kept, so {D['zero']:.1%} of awards net zero or "
        f"less.")
    nfoot = len(plate.wrap(28, 0, foot, size=10.5, fill=MUTED, chars=178, leading=14))
    H = 972 + 14 * nfoot

    s = plate.open_svg(
        W, H, "Winning ten thousand times pays the same per award as winning once",
        subtitle=f"Civilian contracting FY2016, {D['firms']:,} parent recipients - what "
                 f"rises with a firm's award count is the vehicle, not the price")
    fr, _ = plate.frame(W, 80,
                        who="a firm deciding how to chase federal work, and oversight "
                            "deciding where to look for incumbency",
                        decide="whether to chase a larger award or a place on an umbrella "
                               "vehicle: the median award is flat near 8,000 dollars from "
                               "1 win to 10,344",
                        wrong="the median award value rises with awards won, or the "
                              "vehicle gradient flattens inside a single business-size "
                              "class")
    s += fr

    # ---------------- panel A: what they are paid
    s.append(txt(AX, ATOP - 26, "what one award is worth, against how many the firm won",
                 size=12, fill=INK, weight="600"))
    s.append(txt(AX, ATOP - 12, "box spans the 25th to 75th percentile of the firms in that "
                                "band; the bar across it is their median", size=10,
                 fill=MUTED))
    s.append(txt(AX, ATOP - 40, "net dollars obligated per award, log scale", size=10,
                 fill=MUTED))
    for v in (300, 1000, 3000, 10000, 30000, 100000):
        s.append(f'<line x1="{px(1):.1f}" y1="{py(v):.1f}" x2="{px(NMAX):.1f}" '
                 f'y2="{py(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(ax0 - 9, py(v) + 3.5, f"{v:,}", size=9.5, fill=MUTED, anchor="end"))
    for n in (1, 10, 100, 1000, 10000):
        s.append(f'<line x1="{px(n):.1f}" y1="{ATOP:.1f}" x2="{px(n):.1f}" '
                 f'y2="{ABOT:.1f}" stroke="{GRID}"/>')
        s.append(txt(px(n), ABOT + 16, f"{n:,}", size=9.5, fill=MUTED, anchor="middle"))
    for r in rows:
        s.append(txt(px(r["gm"]), ABOT + 32, f"{r['firms']:,}", size=8.5, fill=MUTED,
                     anchor="middle"))
    s.append(txt(AX, ABOT + 32, "firms", size=8.5, fill=MUTED))

    # the fitted trend and its 95% interval, drawn over the whole range
    hi_x = math.log10(NMAX)
    env = ([(x, D["icpt"] + (D["slope"] + 1.96 * D["se"]) * x)
            for x in (hi_x * k / 40 for k in range(41))] +
           [(x, D["icpt"] + (D["slope"] - 1.96 * D["se"]) * x)
            for x in (hi_x * k / 40 for k in range(40, -1, -1))])
    pts = " ".join(f"{px(10**x):.1f},{py(10**y):.1f}" for x, y in env)
    s.append(f'<polygon points="{pts}" fill="{SLATE}" fill-opacity="0.22"/>')
    s.append(f'<path d="M{px(1):.1f},{py(10**D["icpt"]):.1f} L{px(NMAX):.1f},'
             f'{py(10**(D["icpt"]+D["slope"]*hi_x)):.1f}" fill="none" stroke="{INK2}" '
             f'stroke-width="1.6" stroke-dasharray="7 4"/>')

    # one mark per firm that won 100 or more awards, inside the drawn range
    under = over = 0
    for n, m, _ in D["big"]:
        if YLO <= m <= YHI:
            s.append(f'<circle cx="{px(n):.1f}" cy="{py(m):.1f}" r="1.9" fill="{SLATE}" '
                     f'fill-opacity="0.5"/>')
        elif m < YLO:
            under += 1
        else:
            over += 1

    for r in rows:
        x = px(r["gm"])
        t = py(min(r["p75"], YHI))
        b = py(r["p25"]) if r["p25"] > YLO else ABOT
        s.append(f'<rect x="{x-9:.1f}" y="{t:.1f}" width="18" height="{b-t:.1f}" '
                 f'fill="{BLUE}" fill-opacity="0.15" stroke="{BLUE}" stroke-width="1.1"/>')
        s.append(f'<line x1="{x-11:.1f}" y1="{py(r["p50"]):.1f}" x2="{x+11:.1f}" '
                 f'y2="{py(r["p50"]):.1f}" stroke="{BLUE}" stroke-width="2.8"/>')
    s += halo(px(rows[0]["gm"]) + 14, py(rows[0]["p50"]) - 9,
              f"{rows[0]['p50']:,.0f} dollars", size=10.5, fill=BLUE, weight="700")
    s += halo(px(rows[-1]["gm"]) + 14, py(rows[-1]["p50"]) + 4,
              f"{rows[-1]['p50']:,.0f} dollars", size=10.5, fill=BLUE, weight="700")

    for n, m, nm in D["big"]:
        if nm in NAMED:
            lab, dx, dy, anc = NAMED[nm]
            s.append(f'<circle cx="{px(n):.1f}" cy="{py(m):.1f}" r="3.4" fill="{INK2}"/>')
            s += halo(px(n) + dx, py(m) + dy, f"{lab}: {n:,} awards at {m:,.0f} dollars",
                      size=9.5, fill=INK2, anchor=anc, weight="600")

    for i, line in enumerate((
            f"{rows[0]['zero']:.0%} of a one-time winner's awards net zero or",
            "less once de-obligations are kept, so the first",
            "box has no bottom")):
        s += halo(px(1.28), py(YLO) - 42 + i * 13, line, size=9.5, fill=MUTED)
    s.append(f'<line x1="{px(1):.1f}" y1="{ABOT:.1f}" x2="{px(NMAX):.1f}" '
             f'y2="{ABOT:.1f}" stroke="{RULE}"/>')

    # the reading, beside the panel
    s.append(txt(RX, ATOP - 12, "the answer to the price half", size=11, fill=INK,
                 weight="700"))
    s += wrap(RX, ATOP + 8,
              f"Fitted across {len(D['fine'])} award-count bins, the median award is "
              f"multiplied by {10**D['slope']:.2f} for every tenfold rise in awards won "
              f"(95% CI {10**(D['slope']-1.96*D['se']):.2f} to "
              f"{10**(D['slope']+1.96*D['se']):.2f}). The interval straddles 1.00.",
              size=10.5, fill=INK2, chars=35, leading=13.5)
    s += wrap(RX, ATOP + 84,
              f"A premium of {10**(1.96*D['se'])-1:+.1%} per tenfold would have cleared "
              f"that interval, so this is a measured null and not a missing measurement.",
              size=10.5, fill=MUTED, chars=35, leading=13.5)
    s += wrap(RX, ATOP + 152,
              f"Award-level the same fit gives {10**D['aslope']:.2f} per tenfold, and the "
              f"Spearman correlation between an award's value and its winner's award count "
              f"is {D['rho']:+.3f} on {D['awards']:,} awards.",
              size=10.5, fill=MUTED, chars=35, leading=13.5)
    s.append(f'<rect x="{RX:.1f}" y="{ATOP+230:.1f}" width="26" height="9" fill="{SLATE}" '
             f'fill-opacity="0.22"/>')
    s.append(txt(RX + 33, ATOP + 238, "fitted trend, 95% interval", size=9.5, fill=MUTED))
    s.append(f'<circle cx="{RX+13:.1f}" cy="{ATOP+254:.1f}" r="1.9" fill="{SLATE}" '
             f'fill-opacity="0.5"/>')
    for i, line in enumerate((
            f"one of the {len(D['big'])} firms that won 100 or",
            f"more awards. {under} sit below 300 dollars",
            f"({D['big_zero']} of them at zero or less)",
            f"and {over} above 100,000.")):
        s.append(txt(RX + 33, ATOP + 257 + i * 13, line, size=9.5, fill=MUTED))
    s += wrap(RX, ATOP + 318,
              "Not a name-cleaning artefact: ranking on the raw filer-typed parent name "
              "keeps 96 of the cleaned top 100 inside the top 100.",
              size=10.5, fill=MUTED, chars=35, leading=13.5)

    # ---------------- panel B: what moves instead
    s.append(txt(AX, BTOP - 40, "share of the firm's awards placed as orders against a "
                                "parent vehicle", size=12, fill=INK, weight="600"))
    s.append(txt(AX, BTOP - 26, "the same firms on the same horizontal axis; a vehicle "
                                "order is an award carrying parent_award_id_piid",
                 size=10, fill=MUTED))
    for f in (0, .2, .4, .6, .8):
        s.append(f'<line x1="{px(1):.1f}" y1="{qy(f):.1f}" x2="{px(NMAX):.1f}" '
                 f'y2="{qy(f):.1f}" stroke="{GRID}"/>')
        s.append(txt(ax0 - 9, qy(f) + 3.5, f"{f:.0%}", size=9.5, fill=MUTED, anchor="end"))
    for n in (1, 10, 100, 1000, 10000):
        s.append(f'<line x1="{px(n):.1f}" y1="{qy(0):.1f}" x2="{px(n):.1f}" '
                 f'y2="{qy(0.80):.1f}" stroke="{GRID}"/>')

    cross = next(i for i in range(len(rows)) if rows[i]["veh"] > rows[i]["veh_exp"])
    xc = (px(rows[cross - 1]["gm"]) + px(rows[cross]["gm"])) / 2
    s.append(f'<line x1="{xc:.1f}" y1="{qy(0):.1f}" x2="{xc:.1f}" y2="{qy(0.80):.1f}" '
             f'stroke="{INK2}" stroke-width="1" stroke-dasharray="3 3"/>')
    for i, line in enumerate(("right of this line a firm sits on a vehicle",
                              "more often than its own mix of work predicts")):
        s += halo(xc + 9, qy(0.21) + i * 13, line, size=9.5, fill=INK2)

    for key, col, wd, dash in (("veh_exp", FAINT, 1.8, ' stroke-dasharray="5 4"'),
                               ("veh_sm", BLUE, 2.0, ""), ("veh", RED, 2.6, "")):
        d = " ".join(f"{'M' if i == 0 else 'L'}{px(r['gm']):.1f},{qy(r[key]):.1f}"
                     for i, r in enumerate(rows))
        s.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{wd}"{dash}/>')
    for r in rows:
        for key, col, rad in (("veh_sm", BLUE, 3.0), ("veh", RED, 3.8)):
            s.append(f'<circle cx="{px(r["gm"]):.1f}" cy="{qy(r[key]):.1f}" r="{rad}" '
                     f'fill="{col}"/>')
    s += halo(px(rows[7]["gm"]), qy(rows[7]["veh"]) + 18, "every award", size=10.5,
              fill=RED, anchor="middle", weight="700")
    s += halo(px(rows[7]["gm"]), qy(rows[7]["veh_sm"]) - 11,
              "awards marked small business", size=10.5, fill=BLUE, anchor="middle",
              weight="700")
    s.append(f'<line x1="{px(10):.1f}" y1="{qy(0.645):.1f}" x2="{px(10):.1f}" '
             f'y2="{qy(0.550):.1f}" stroke="{FAINT}" stroke-width="1"/>')
    for i, line in enumerate(("expected from award size",
                              "and product family alone")):
        s += halo(px(10) - 7, qy(0.66) + i * 13, line, size=10.5, fill=MUTED,
                  anchor="end", weight="700")
    for r, col, key, dy in ((rows[0], RED, "veh", 4), (rows[8], RED, "veh", 19),
                            (rows[-1], BLUE, "veh_sm", 4)):
        s += halo(px(r["gm"]) + 12, qy(r[key]) + dy, f"{r[key]:.1%}", size=10.5, fill=col,
                  weight="700")

    for n in (1, 10, 100, 1000, 10000):
        s.append(txt(px(n), qy(0) + 16, f"{n:,}", size=9.5, fill=MUTED, anchor="middle"))
    s.append(txt(AX, qy(0) + 34, "awards won in FY2016, log scale", size=10, fill=MUTED))
    s.append(f'<line x1="{px(1):.1f}" y1="{qy(0):.1f}" x2="{px(NMAX):.1f}" '
             f'y2="{qy(0):.1f}" stroke="{RULE}"/>')

    s.append(txt(RX, BTOP - 26, "the answer to the other half", size=11, fill=INK,
                 weight="700"))
    s += wrap(RX, BTOP - 6,
              f"{D['novehicle']:,} of {D['firms']:,} parents "
              f"({D['novehicle']/D['firms']:.1%}) placed no vehicle order at all in FY2016 "
              f"and won a median of {D['novehicle_med']:.0f} award each. Chase the vehicle, "
              f"not the contract.",
              size=10.5, fill=INK2, chars=35, leading=13.5)
    s += wrap(RX, BTOP + 72,
              f"Two rival stories were measured and both failed. Set-asides fall from "
              f"{rows[0]['sa']:.1%} to {rows[-1]['sa']:.1%}, but that is business size: "
              f"inside small-business awards the same fall is {rows[0]['sa_sm']:.1%} to "
              f"{rows[8]['sa_sm']:.1%} at 300-999 awards. Single bids stay within "
              f"{min(r['sb']-r['sb_exp'] for r in rows)*100:+.1f} to "
              f"{max(r['sb']-r['sb_exp'] for r in rows)*100:+.1f} points of a "
              f"size-and-family match, and the {len(D['top'])} firms above a thousand "
              f"awards run {D['top'][0][0]:.1%} to {D['top'][-1][0]:.1%} singly.",
              size=10.5, fill=MUTED, chars=35, leading=13.5)

    fy = H - 26 - 14 * nfoot
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=178, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))

    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {D['n_tx']:,} tx -> {D['awards']:,} awards with a parent, "
          f"${D['net']/1e9:.2f}bn net, {D['firms']:,} parents, {D['bid_n']:,} with a "
          f"usable bid count")
    print(f"    price fit x{10**D['slope']:.3f}/decade (95% CI "
          f"{10**(D['slope']-1.96*D['se']):.3f}-{10**(D['slope']+1.96*D['se']):.3f}), "
          f"R2 {D['r2']:.3f}; award-level x{10**D['aslope']:.3f} "
          f"({10**(D['aslope']-1.96*D['ase']):.3f}-{10**(D['aslope']+1.96*D['ase']):.3f}); "
          f"spearman {D['rho']:+.4f}; of {len(D['big'])} firms with 100+ awards, {under} "
          f"below and {over} above the dollar range drawn")
    print("    band      firms   awards      p25/median/p75 of firm medians      veh    "
          "exp   smallbiz  setaside  sa(sb)  single   exp")
    for r in rows:
        print(f"    {r['lo']:>5}+{r['firms']:>8,}{r['awards']:>9,}  "
              f"{r['p25']:>8,.0f}/{r['p50']:>7,.0f}/{r['p75']:>8,.0f}  "
              f"{r['veh']:9.1%} {r['veh_exp']:6.1%} {r['veh_sm']:8.1%} {r['sa']:8.1%} "
              f"{r['sa_sm']:7.1%} {r['sb']:7.1%} {r['sb_exp']:6.1%}")
    print(f"    {D['novehicle']:,} parents never placed a vehicle order "
          f"({D['novehicle_aw']:,} awards, median {D['novehicle_med']:.0f} each)")
    print("    fine bins: " + "  ".join(f"{g:,.0f}:{m:,.0f}" for g, m, _ in D["fine"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
