#!/usr/bin/env python3
"""Where the work is done is not where the firm is registered, and place is a poor predictor.

    python3 chart-4-geography.py

This register carries two geographies per award: the recipient's own address and the primary
place of performance. Both are effectively complete -- 98.9% of FY2016 civilian awards carry
a state code for each, and the 0.69% of performance codes that are blank are almost exactly
the 3,835 awards performed abroad. That is rare enough to be worth using properly.

**They disagree on two awards in five.** 40.8% of 547,968 awards are performed in a state
other than the one the recipient is registered in; by dollars, 36.1%. It is not one
department's habit: the cross-state share runs from 33% at Agriculture to 54% at Energy, with
NASA the single outlier at 19% because its work happens at its own centres.

**The capital region dominates dollars, not awards.** DC, Maryland and Virginia together are
19.4% of awards by recipient address and 20.3% by place of performance -- barely different --
but 31.7% and 29.3% of the obligated dollars. And the aggregate hides that its three members
point opposite ways: DC takes in 2.2 times the work its address share would give it (80.2% of
DC-performed awards go to an out-of-state recipient), while Virginia performs only 0.62 of
its address share and sends 54.3% of its own awards elsewhere. Maryland is 1.34.

**Geography predicts competition about half as well as it looks like it does.** Single-offer
rate by place of performance spans 32 points across the 52 states with 500 or more coded
awards -- 46.3% in Alaska to 78.6% in Minnesota. Each state's own agency mix, scored at
national per-agency rates, predicts a spread of 18 points and accounts for 49% of the
between-state variance. Agency is not a nuisance here, it is half the effect.

**But the half agency does not explain is durable.** Folding FY2015 and FY2017 as well
gives the same states the same character: a state's single-offer rate in FY2015 predicts its
FY2017 rate at **r +0.72**, and at **r +0.67** after each year's agency mix is removed
entirely. The national rate is flat across the three years (59.4%, 59.5%, 58.6%) while the
median state swings 4.1 points, so this is not a national trend moving everyone together.
Place carries information that persists. Offer-code coverage is 99.8%, 99.7% and 98.7%, so
the comparison is not measuring the column going blank -- which it does later, badly.

**A note on the drawing.** The right panel used to be a second scatter with segments joining
each state to where it lands without its largest recipient. Those segments asserted a
direction through a space that has none, and they were unreadable where they crossed. A time
series earns its lines, because the x axis is ordered.

**What this does not show.** Defense is absent and its footprint is distinctive, so no share
here describes federal procurement. Shares are of the national award count and therefore
track population; only the departure from the diagonal is a within-state quantity. Place of
performance is the *primary* one, recorded per award -- a contract executed in four states
is coded to one.
"""
import collections, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L, plate                                                  # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "4-geography.svg")
SRC = os.path.join(HERE, "..", "data", "civilian-fy2016.zip")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
CAP = ("DC", "MD", "VA")
MIN_N = 500          # states below this many offer-coded awards are not scored
MIN_DRAW = 200       # codes below this many awards on both axes are not drawn
SHORT = {"Department of Veterans Affairs": "Veterans Affairs",
         "Department of Justice": "Justice",
         "Department of Health and Human Services": "Health & Human Services",
         "Department of Homeland Security": "Homeland Security",
         "Department of Agriculture": "Agriculture",
         "Department of the Interior": "Interior",
         "Department of Commerce": "Commerce",
         "Department of Transportation": "Transportation",
         "National Aeronautics and Space Administration": "NASA",
         "Environmental Protection Agency": "EPA",
         "Department of Energy": "Energy"}


def collect():
    """One record per award: the two state codes, agency, recipient, offers, dollars."""
    acc = {}
    for r in L.transactions(SRC):
        k = r.get(L.KEY)
        if not k:
            continue
        a = acc.get(k)
        if a is None:
            a = acc[k] = {"pop": "", "rec": "", "popc": "", "ag": "", "name": "",
                          "off": "", "obl": 0.0}
        a["obl"] += L.num(r.get("federal_action_obligation")) or 0.0
        for dst, col in (("pop", "primary_place_of_performance_state_code"),
                         ("rec", "recipient_state_code"),
                         ("popc", "primary_place_of_performance_country_code"),
                         ("ag", "awarding_agency_name"),
                         ("name", "recipient_name"),
                         ("off", "number_of_offers_received")):
            if not a[dst]:
                a[dst] = (r.get(col) or "").strip()
    return list(acc.values())


def single(a):
    try:
        return 1 if float(a["off"]) == 1 else 0
    except (TypeError, ValueError):
        return None


YRS = ("2015", "2016", "2017")
CACHE = os.path.join(HERE, "..", "data", "geo-3yr.json")


def three_year():
    """Per-state single-offer rate and agency-mix prediction, one entry per year.

    Cached beside the data because it folds three ~270 MB zips; delete the JSON to
    rebuild. Written atomically, so an interrupted run cannot leave a half-file that
    later reads as valid.
    """
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    out = {}
    for y in YRS:
        zp = os.path.join(HERE, "..", "data", "civilian-fy%s.zip" % y)
        if not os.path.exists(zp):
            raise SystemExit("  civilian-fy%s.zip missing - run usa2.py" % y)
        acc = {}
        for r in L.transactions(zp):
            k = r.get(L.KEY)
            if not k or k in acc:
                continue
            acc[k] = ((r.get("number_of_offers_received") or "").strip(),
                      (r.get("primary_place_of_performance_state_code") or "").strip(),
                      (r.get("awarding_agency_name") or "").strip())
        rows = []
        for o, st, ag in acc.values():
            if not st or not ag:
                continue
            try:
                rows.append((1 if float(o) == 1 else 0, st, ag))
            except (TypeError, ValueError):
                pass
        agt = collections.defaultdict(lambda: [0, 0])
        for v, st, ag in rows:
            agt[ag][0] += 1
            agt[ag][1] += v
        arate = {a: k / n for a, (n, k) in agt.items()}
        stt = collections.defaultdict(lambda: [0, 0, 0.0])
        for v, st, ag in rows:
            stt[st][0] += 1
            stt[st][1] += v
            stt[st][2] += arate[ag]
        out[y] = {st: [n, k / n, e / n]
                  for st, (n, k, e) in sorted(stt.items()) if n >= MIN_N}
    tmp = CACHE + ".tmp"
    json.dump(out, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return out


def main():
    if not os.path.exists(SRC):
        raise SystemExit("  civilian-fy2016.zip missing — run usa2.py")
    aw = collect()
    total = len(aw)

    # ---- panel A: recipient state against place of performance -------------------------
    R, P, RD, PD = (collections.Counter() for _ in range(4))
    for a in aw:
        if a["rec"]:
            R[a["rec"]] += 1
            RD[a["rec"]] += a["obl"]
        if a["pop"]:
            P[a["pop"]] += 1
            PD[a["pop"]] += a["obl"]
    nr, npp, nrd, npd = sum(R.values()), sum(P.values()), sum(RD.values()), sum(PD.values())
    both = [a for a in aw if a["pop"] and a["rec"]]
    cross = sum(1 for a in both if a["pop"] != a["rec"]) / len(both)
    dcross = 1 - sum(a["obl"] for a in both if a["pop"] == a["rec"]) / sum(a["obl"] for a in both)
    blank_pop = sum(1 for a in aw if not a["pop"])
    abroad = sum(1 for a in aw if not a["pop"] and a["popc"] and a["popc"] != "USA")

    codes = sorted([c for c in set(R) | set(P) if R[c] >= MIN_DRAW or P[c] >= MIN_DRAW],
                   key=lambda c: -P[c])
    skipped = sorted(c for c in set(R) | set(P) if c not in codes)
    pts = [{"c": c, "x": R[c] / nr, "y": P[c] / npp, "r": (P[c] / npp) / (R[c] / nr)}
           for c in codes if R[c]]
    near = sum(1 for d in pts if 0.8 <= d["r"] <= 1.25)

    capA = sum(R[c] for c in CAP) / nr, sum(P[c] for c in CAP) / npp
    capD = sum(RD[c] for c in CAP) / nrd, sum(PD[c] for c in CAP) / npd
    dc_in = [a for a in both if a["pop"] == "DC"]
    dc_out = sum(1 for a in dc_in if a["rec"] != "DC") / len(dc_in)
    va_out = [a for a in both if a["rec"] == "VA"]
    va_away = sum(1 for a in va_out if a["pop"] != "VA") / len(va_out)

    byag = collections.defaultdict(lambda: [0, 0])
    for a in both:
        byag[a["ag"]][0] += 1
        byag[a["ag"]][1] += a["pop"] != a["rec"]
    agx = sorted((s / t, SHORT.get(ag, ag)) for ag, (t, s) in byag.items() if t >= 5000)

    # ---- panel B: single-offer rate against what the agency mix predicts ---------------
    ok = [a for a in aw if single(a) is not None and a["pop"]]
    per = collections.defaultdict(lambda: [0, 0])
    for a in ok:
        per[a["ag"]][0] += 1
        per[a["ag"]][1] += single(a)
    rate = {ag: s / t for ag, (t, s) in per.items()}

    def score(exclude=None):
        st = collections.defaultdict(lambda: {"n": 0, "s": 0, "e": 0.0})
        for a in ok:
            if exclude and (a["pop"], a["name"]) in exclude:
                continue
            d = st[a["pop"]]
            d["n"] += 1
            d["s"] += single(a)
            d["e"] += rate[a["ag"]]
        return {c: (d["n"], d["s"] / d["n"], d["e"] / d["n"])
                for c, d in st.items() if d["n"] >= MIN_N}

    base = score()
    tops = collections.defaultdict(collections.Counter)
    for a in ok:
        tops[a["pop"]][a["name"]] += 1
    topname = {c: tops[c].most_common(1)[0][0] for c in base}
    topshare = {c: tops[c].most_common(1)[0][1] / base[c][0] for c in base}
    drop = score(exclude={(c, topname[c]) for c in base})

    B = []
    for c, (n, o, e) in base.items():
        n2, o2, e2 = drop[c]
        B.append({"c": c, "n": n, "obs": o, "exp": e, "res": o - e, "res2": o2 - e2,
                  "obs2": o2, "exp2": e2, "top": topshare[c], "topn": topname[c]})
    B.sort(key=lambda d: -d["res"])
    sd = lambda v: (sum((x - sum(v) / len(v)) ** 2 for x in v) / len(v)) ** 0.5
    O = [d["obs"] for d in B]
    E = [d["exp"] for d in B]
    RS = [d["res"] for d in B]
    RS2 = [d["res2"] for d in B]
    explained = 1 - sd(RS) ** 2 / sd(O) ** 2
    big = [d for d in B if abs(d["res"]) >= 0.04]
    shrank = sum(1 for d in big if abs(d["res2"]) < abs(d["res"]))
    movers = [d for d in B if abs(d["res2"] - d["res"]) >= 0.02]
    ky = next(d for d in B if d["c"] == "KY")
    ar = next(d for d in B if d["c"] == "AR")

    # ---- panel B: the same rate across three years, each state indexed to itself -------
    TY = three_year()
    common = sorted(c for c in TY[YRS[0]] if all(c in TY[y] for y in YRS))
    idx = {c: [TY[y][c][1] / TY[YRS[0]][c][1] * 100 for y in YRS] for c in common}
    natl = []
    for y in YRS:
        n = sum(TY[y][c][0] for c in common)
        natl.append(sum(TY[y][c][0] * TY[y][c][1] for c in common) / n)
    nidx = [v / natl[0] * 100 for v in natl]

    def rho(a, b):
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        return (sum((x - ma) * (y - mb) for x, y in zip(a, b))
                / (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5)

    r_raw = rho([TY[YRS[0]][c][1] for c in common], [TY[YRS[-1]][c][1] for c in common])
    r_res = rho([TY[YRS[0]][c][1] - TY[YRS[0]][c][2] for c in common],
                [TY[YRS[-1]][c][1] - TY[YRS[-1]][c][2] for c in common])
    med_swing = sorted(max(TY[y][c][1] for y in YRS) - min(TY[y][c][1] for y in YRS)
                       for c in common)[len(common) // 2]
    movers3 = sorted(common, key=lambda c: -abs(idx[c][-1] - 100))[:6]

    # =====================================================================================
    W, H = 1200, 960
    s = plate.open_svg(W, H,
                       "Two in five awards are performed outside the state the recipient "
                       "sits in",
                       subtitle="and a state's competition rate outlives its agency mix and "
                                "persists across three years")
    fr, _ = plate.frame(W, 86,
                        who="anyone reading a state's federal contract total as local "
                            "economic activity",
                        decide="whether to count an award where the recipient is registered "
                               "or where the work is performed",
                        wrong="the states fall on the left diagonal, or the indexed lines "
                              "on the right cross and re-order freely — then place is "
                              "noise and only the year matters")
    s += fr

    # ---- panel A -----------------------------------------------------------------------
    AX0, AY0, SIDE = 92, 204, 402
    lo, hi = 3e-4, 0.15
    lg = lambda v: (math.log10(max(v, lo)) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
    ax = lambda v: AX0 + SIDE * lg(v)
    ay = lambda v: AY0 + SIDE - SIDE * lg(v)
    s.append(txt(28, AY0 - 34, "where the firm is registered, against where the work is done",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(28, AY0 - 16, "one mark per state code, FY2016 civilian awards",
                 size=10, fill=MUTED))
    for v, lab in ((3e-4, "0.03%"), (1e-3, "0.1%"), (3e-3, "0.3%"),
                   (1e-2, "1%"), (3e-2, "3%"), (1e-1, "10%")):
        s.append(f'<line x1="{ax(v):.1f}" y1="{AY0:.1f}" x2="{ax(v):.1f}" '
                 f'y2="{AY0+SIDE:.1f}" stroke="{GRID}"/>')
        s.append(f'<line x1="{AX0:.1f}" y1="{ay(v):.1f}" x2="{AX0+SIDE:.1f}" '
                 f'y2="{ay(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(ax(v), AY0 + SIDE + 16, lab, size=9, fill=MUTED, anchor="middle"))
        s.append(txt(AX0 - 8, ay(v) + 3, lab, size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX0, AY0 + SIDE + 34, "share of awards, by the recipient's own state",
                 size=10.5, fill=INK2))
    s.append(f'<text x="{AX0-46}" y="{AY0+SIDE:.1f}" font-size="10.5" fill="{INK2}" '
             f'transform="rotate(-90 {AX0-46} {AY0+SIDE:.1f})">'
             f'share of awards, by place of performance</text>')
    s.append(f'<path d="M{ax(lo):.1f},{ay(lo):.1f} L{ax(hi):.1f},{ay(hi):.1f}" fill="none" '
             f'stroke="{INK2}" stroke-width="1.4" stroke-dasharray="5 3"/>')
    for m in (2.0, 0.5):
        x1 = max(lo, lo / m)
        x2 = min(hi, hi / m)
        s.append(f'<path d="M{ax(x1):.1f},{ay(x1*m):.1f} L{ax(x2):.1f},{ay(x2*m):.1f}" '
                 f'fill="none" stroke="{FAINT}" stroke-width="1" stroke-dasharray="2 4"/>')
    OFF = {"DC": (9, -6), "VA": (10, 4), "MD": (-9, -6), "CA": (-9, -7), "TX": (9, 4),
           "NJ": (9, 4), "MN": (-13, -6), "MS": (-9, -5), "WV": (9, -5),
           "NM": (9, -5), "DE": (9, 4), "WY": (-9, -5), "IA": (-9, -5), "PR": (9, 4)}
    for d in sorted(pts, key=lambda d: -abs(math.log(d["r"]))):
        col = BLUE if d["r"] > 1.25 else (RED if d["r"] < 0.8 else SLATE)
        cx, cy = ax(d["x"]), ay(d["y"])
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="{col}" '
                 f'fill-opacity="0.35" stroke="{col}" stroke-width="1.3"/>')
        if d["c"] in OFF:
            dx, dy = OFF[d["c"]]
            s += halo(cx + dx, cy + dy, d["c"], size=10, fill=col,
                      anchor="start" if dx > 0 else "end")
    lx, ly = AX0 + 168, AY0 + SIDE - 76
    for col, name in ((BLUE, "more work performed here than firms registered"),
                      (RED, "more firms registered here than work performed"),
                      (SLATE, f"the two within 1.25x ({near} of {len(pts)} codes)")):
        s.append(f'<circle cx="{lx:.1f}" cy="{ly-3.5:.1f}" r="4" fill="{col}" '
                 f'fill-opacity="0.35" stroke="{col}" stroke-width="1.3"/>')
        s.append(txt(lx + 12, ly, name, size=9.5, fill=INK2))
        ly += 14
    s.append(f'<path d="M{lx-6:.1f},{ly-3.5:.1f} L{lx+6:.1f},{ly-3.5:.1f}" stroke="{INK2}" '
             f'stroke-width="1.4" stroke-dasharray="5 3"/>')
    s.append(txt(lx + 12, ly, "dashed: the two shares agree", size=9.5, fill=INK2))
    ly += 14
    s.append(f'<path d="M{lx-6:.1f},{ly-3.5:.1f} L{lx+6:.1f},{ly-3.5:.1f}" stroke="{FAINT}" '
             f'stroke-width="1.2" stroke-dasharray="2 4"/>')
    s.append(txt(lx + 12, ly, "dotted guides: twice that, and half", size=9.5, fill=INK2))

    # ---- panel B -----------------------------------------------------------------------
    # A line here is honest because x is ordered. The previous version of this panel drew
    # segments between paired scatter marks, which asserted a direction through a space
    # that has none -- a reader said the linear lines confused the presentation, and they
    # were right: the pairs were counterfactual, not sequential.
    BX0, BY0, PW = 762, 204, 252
    ilo = math.floor(min(min(v) for v in idx.values()) / 5) * 5
    ihi = math.ceil(max(max(v) for v in idx.values()) / 5) * 5
    bx = lambda i_: BX0 + PW * i_ / (len(YRS) - 1)
    by = lambda v: BY0 + SIDE - SIDE * (v - ilo) / (ihi - ilo)
    s.append(txt(664, BY0 - 34, "the same rate three years running, each state indexed to "
                                "its own FY2015", size=12.5, fill=INK, weight="600"))
    s.append(txt(664, BY0 - 16, f"{len(common)} states with {MIN_N} or more offer-coded "
                                f"awards in every year; 100 is that state's own FY2015 rate",
                 size=10, fill=MUTED))
    for v in range(int(ilo), int(ihi) + 1, 10):
        s.append(f'<line x1="{BX0:.1f}" y1="{by(v):.1f}" x2="{BX0+PW:.1f}" '
                 f'y2="{by(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(BX0 - 8, by(v) + 3, str(v), size=9, fill=MUTED, anchor="end"))
    for i_, y in enumerate(YRS):
        s.append(txt(bx(i_), BY0 + SIDE + 16, "FY" + y, size=9, fill=MUTED, anchor="middle"))
    s.append(f'<text x="{BX0-44}" y="{BY0+SIDE:.1f}" font-size="10.5" fill="{INK2}" '
             f'transform="rotate(-90 {BX0-44} {BY0+SIDE:.1f})">'
             f"single-offer rate, indexed to that state's own FY2015 = 100</text>")

    hot = set(movers3)
    for c in common:
        if c in hot:
            continue
        d = " ".join(("M" if i_ == 0 else "L") + f"{bx(i_):.1f},{by(idx[c][i_]):.1f}"
                     for i_ in range(len(YRS)))
        s.append(f'<path d="{d}" fill="none" stroke="{SLATE}" stroke-width="1.1" '
                 f'stroke-opacity="0.5"/>')
    # the no-change line is the claim of this panel, so it outranks the grid
    s.append(f'<line x1="{BX0:.1f}" y1="{by(100):.1f}" x2="{BX0+PW:.1f}" '
             f'y2="{by(100):.1f}" stroke="{INK2}" stroke-width="1.3" '
             f'stroke-dasharray="5 3"/>')
    for c in sorted(hot, key=lambda z: -idx[z][-1]):
        col = GREEN if idx[c][-1] >= 100 else RED
        d = " ".join(("M" if i_ == 0 else "L") + f"{bx(i_):.1f},{by(idx[c][i_]):.1f}"
                     for i_ in range(len(YRS)))
        s.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.0"/>')
        for i_ in range(len(YRS)):
            s.append(f'<circle cx="{bx(i_):.1f}" cy="{by(idx[c][i_]):.1f}" r="2.6" '
                     f'fill="{col}"/>')
    d = " ".join(("M" if i_ == 0 else "L") + f"{bx(i_):.1f},{by(nidx[i_]):.1f}"
                 for i_ in range(len(YRS)))
    s.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="2.8"/>')

    placed = []
    rows_ = [(idx[c][-1], c) for c in hot] + [(nidx[-1], "")]
    for v, c in sorted(rows_, reverse=True):
        ly = by(v) + 3
        while any(abs(ly - q) < 12 for q in placed):
            ly += 12
        placed.append(ly)
        if not c:
            s += halo(bx(len(YRS) - 1) + 9, ly,
                      f"all {len(common)}: {natl[0]*100:.1f}% to {natl[-1]*100:.1f}%",
                      size=9.5, fill=INK, weight="700")
        else:
            s += halo(bx(len(YRS) - 1) + 9, ly,
                      f"{c} {TY[YRS[0]][c][1]*100:.0f} to {TY[YRS[-1]][c][1]*100:.0f}%",
                      size=9.5, fill=GREEN if idx[c][-1] >= 100 else RED, weight="700")
    s += halo(BX0 + 7, BY0 + SIDE - 32, "a state's FY2015 rate predicts its FY2017 rate",
              size=9.5, fill=INK2)
    s += halo(BX0 + 7, BY0 + SIDE - 19, f"r {r_raw:+.2f} raw; r {r_res:+.2f} with agency "
                                        f"mix removed", size=9.5, fill=INK2, weight="700")

    # ---- captions ----------------------------------------------------------------------
    cy0 = AY0 + SIDE + 62
    s.append(txt(28, cy0, "the capital region's edge is in dollars, not awards",
                 size=12, fill=INK, weight="600"))
    s += wrap(28, cy0 + 19,
              f"{cross:.1%} of the {len(both):,} awards carrying both codes are performed "
              f"outside the recipient's state, {dcross:.1%} of the dollars, and every "
              f"department does it — {agx[1][0]:.0%} at {agx[1][1]} to {agx[-1][0]:.0%} at "
              f"{agx[-1][1]}, with {agx[0][1]} the exception at {agx[0][0]:.0%}. "
              f"DC, Maryland and Virginia "
              f"are {capA[0]:.1%} of awards by address and {capA[1]:.1%} by performance — "
              f"barely different — but {capD[0]:.1%} and {capD[1]:.1%} of the dollars. Inside "
              f"the region the two measures point opposite ways: {dc_out:.0%} of DC-performed "
              f"awards go to an out-of-state recipient, and {va_away:.0%} of Virginia's own "
              f"awards are performed somewhere else.",
              size=10.5, fill=INK2, chars=98, leading=14.5)
    s.append(txt(664, cy0, "place is durable, and it is not merely the agency mix",
                 size=12, fill=INK, weight="600"))
    s += wrap(664, cy0 + 19,
              f"Agency mix is half of it: scored at national per-agency rates it spans "
              f"{(max(E)-min(E))*100:.0f} of the {(max(O)-min(O))*100:.0f}-point raw spread "
              f"and accounts for {explained:.0%} of the variance between states. The half it "
              f"leaves does not wash out. A state's FY2015 single-offer rate predicts its "
              f"FY2017 rate at r {r_raw:+.2f}, and still at r {r_res:+.2f} once each year's "
              f"agency mix is removed — so the spread is not agencies rotating through. The "
              f"national rate barely moves ({natl[0]:.1%}, {natl[1]:.1%}, {natl[2]:.1%}) "
              f"while the median state swings {med_swing*100:.1f} points and "
              f"{movers3[0]} moves {TY[YRS[0]][movers3[0]][1]*100:.0f}% to "
              f"{TY[YRS[-1]][movers3[0]][1]*100:.0f}%. Offer coverage is "
              f"99.8%, 99.7% and 98.7%, so the three years are comparable on this column.",
              size=10.5, fill=INK2, chars=88, leading=14.5)

    # Trimmed from the plate per doctrine/what-a-footnote-carries.md; kept here because it is method: f
    # oot = (USAspending API v2 bulk download, fetched 2026-09-22; contract transactions with
    # an action date in FY2016, eleven civilian departments, collapsed to {total:,} awards on
    # contract_award_unique_key. These departments are 8.5% of federal contract awards —
    # Defense alone is 68.6% and General Services 22.9%, and Defense's geographic footprint is
    # distinctive, so nothing here describes federal procurement as a whole. Sixty performance
    # codes: 50 states, DC, five territories and three freely associated states;
    # {blank_pop/total:.2%} are blank and {abroad:,} of those {blank_pop:,} are performances
    # abroad. {len(skipped)} codes under {MIN_DRAW} awards ({', '.join(sorted(skipped))}) are
    # not drawn. Dollars are federal_action_obligation summed per award, de-obligations
    # included. Both axes on the left are shares of the national award count and so track
    # population; only the departure from the diagonal is a within-state quantity. Top-handler
    # checks: DC's largest recipient of record is the redaction placeholder DOMESTIC AWARDEES
    # (UNDISCLOSED) at 21.7% of DC-addressed awards, and removing it moves DC from 2.2x to
    # 2.9x; Minnesota's is Medtronic at 41.4% and Indiana's Zimmer at 26.1%. The right panel
    # also folds FY2015 and FY2017 on the same award-level rules; offer-code coverage is
    # 99.8%, 99.7% and 98.7% and the national single-offer rate is 59.4%, 59.5% and 58.6%, so
    # the index is not tracking the column emptying. Dollars by place of performance are more
    # concentrated still — one Energy contractor is 58% of Idaho, 44% of New Mexico and 37% of
    # Tennessee.)
    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2016, with FY2015 and "
        "FY2017 for the right panel. CAVEAT: both axes on the left are shares of the "
        "national award count and so track population; only the departure from the diagonal "
        "is a within-state quantity. These eleven civilian departments are 8.5% of federal "
        "contract awards; Defense (68.6%) is absent, so this is not federal procurement as "
        "a whole.")
    nlines = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=190, leading=14))
    fy = H - 20 - 14 * nlines
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=190, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))

    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {total:,} awards; both states coded {len(both):,} ({len(both)/total:.2%})")
    print(f"    performed out of the recipient's state: {cross:.2%} of awards, "
          f"{dcross:.2%} of dollars")
    print(f"    capital region: recipient {capA[0]:.2%} awards / {capD[0]:.2%} dollars; "
          f"performance {capA[1]:.2%} awards / {capD[1]:.2%} dollars")
    for c in CAP:
        print(f"      {c}: recipient {R[c]/nr:.2%}, performance {P[c]/npp:.2%}, "
              f"ratio {(P[c]/npp)/(R[c]/nr):.2f}")
    print(f"    single-offer by state: observed {min(O):.1%} to {max(O):.1%} (sd "
          f"{sd(O)*100:.2f} pts); agency-mix expected {min(E):.1%} to {max(E):.1%} "
          f"(sd {sd(E)*100:.2f}); residual sd {sd(RS)*100:.2f}, explained {explained:.1%}")
    print(f"    residual sd without each state's largest recipient: {sd(RS2)*100:.2f} pts; "
          f"{shrank}/{len(big)} large residuals shrink")
    print(f"    Arkansas {ar['res']:+.1%} -> {ar['res2']:+.1%} without "
          f"{ar['topn']} ({ar['top']:.0%})")
    print(f"    three-year: r_raw {r_raw:+.3f}, r_residual {r_res:+.3f}, "
          f"median swing {med_swing*100:.2f} pts, national "
          f"{natl[0]:.3%} {natl[1]:.3%} {natl[2]:.3%}")
    for c in movers3:
        print(f"      {c} index " + " ".join(f"{v:.1f}" for v in idx[c])
              + f"   {TY[YRS[0]][c][1]:.1%} -> {TY[YRS[-1]][c][1]:.1%}")
    for d in B[:4] + B[-4:]:
        print(f"      {d['c']} n={d['n']:>6,} obs {d['obs']:.1%} exp {d['exp']:.1%} "
              f"resid {d['res']:+.1%} -> {d['res2']:+.1%} (top {d['top']:.0%} {d['topn'][:24]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
