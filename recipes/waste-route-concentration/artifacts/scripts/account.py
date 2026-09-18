#!/usr/bin/env python3
"""What decides a ton's fate, once it is not the price.

    python3 chart-14-account.py

The price join found nothing, which leaves two readings: the price is not a signal, or the
signal exists and nobody exploits it. The second is unfalsifiable as stated. It stops being
unfalsifiable if something *else* is shown to decide the outcome, because a mechanism that
already explains the variation leaves no room for an unexploited one.

**Fate is not random, and the ranking is not the obvious one.** Scored on held-out rows so
that high-cardinality variables cannot cheat, the single best predictor of which of twelve
routes a ton takes is **the facility handling it (53%)**, then **where it is (46%)**, then
**what the waste is (40%)**, then the generator's industry (34%).

**The facility belongs at the top of that list and is not a predictor.** A landfill only
landfills, so knowing the facility is close to being told the answer. An earlier version of
this panel scored in-sample and reported 94% for it — 3,104 memorised cells marking their own
work.

**Set it aside and location beats chemistry.** Where a waste physically sits predicts its fate
better than what it is, and location is also what adds most once the waste type is already
known (+9 points, against +7 for the facility and +0.6 for the generator's industry). The same
material meets a different fate in Arkansas than in Alabama, which is infrastructure.

**And underneath that sits the account.** Counted in distinct streams rather than tons — the
tonnage version is 84% against a 74% null and is almost entirely the arithmetic of one big
stream — the median generator with three or more streams sends **half of them to a single
receiver, against 20% under the null**, and **10% send every stream they have to one facility,
which chance never produces.**

**Tested without the circularity, it still holds.** Choose the vendor using only a generator's
*largest* stream, then read the outcome on its *other* streams. Those other streams carry 26.6%
of their tonnage to that same facility against 3.1% under the null, and their recovery rate is
**17 points higher** when the vendor — picked for a different waste — is recovery-led. Holding
the generator's industry and state constant as well, the gap halves to **+8 points** and stays
positive in 35 of 54 strata. Half the raw effect was industry and geography. The rest is who
you already buy from.

**So the shape of the mix is: material, then local infrastructure, then procurement inertia.**
Not optimisation and not a coin. It also explains the price null rather than merely sitting
beside it — a firm that routes its waste by an existing contract is not pricing each stream,
so there is no mechanism through which a metal price could move the tonnage.
"""
import collections, math, os, random, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate
import brdata, plate                                                            # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "account.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
GREEN, RED, BLUE, AMBER = "#1b7f5a", "#8c2318", "#4a7fa8", "#c07a1e"
FAINT = plate.FAINT
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
num, REC, DIS = brdata.num, brdata.RECOVERY, brdata.DISPOSAL


def txt(x, y, s, *, size, fill, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" style="font-variant-numeric: tabular-nums">{escape(str(s))}</text>')


def wrap(x, y, s, *, size, fill, chars, leading=13.5, weight="normal"):
    words, line, out, n = str(s).split(), [], [], 0
    for w in words:
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill, weight=weight))
            line, n = [], n + 1
        line.append(w)
    if line:
        out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill, weight=weight))
    return out


def ent(c):
    t = sum(c.values())
    return -sum((v / t) * math.log2(v / t) for v in c.values() if v > 0) if t else 0.0


def ladder_heldout(rows):
    """Held-out cross-entropy per record, because two earlier versions were wrong.

    An in-sample ladder rewards cardinality: it reported that knowing the handling facility
    removed 94% of the uncertainty, which was 3,104 memorised cells marking their own work.
    Scoring held-out fixes that. Weighting the score by tonnage then broke it differently —
    a few enormous rows falling in cells the training half scored near zero drove the whole
    number negative, i.e. worse than guessing the base rate. Tonnage spans orders of
    magnitude and one row can carry a percent of the file.

    So this scores **per record**: one filed decision, one vote. That is also the unit the
    question is about — what a filer does with a stream, not what happens to the marginal
    ton."""
    rnd = random.Random(5)
    idx = list(range(len(rows)))
    rnd.shuffle(idx)
    tr = [rows[i] for i in idx[:len(idx) // 2]]
    te = [rows[i] for i in idx[len(idx) // 2:]]
    base = collections.Counter(r["management_category"] for r in tr)
    bt = sum(base.values())
    prior = {k: v / bt for k, v in base.items()}

    def score(keyf, m=5.0):
        """Shrink each cell toward the base rate by a fixed pseudo-weight of m tons.

        A flat 50/50 blend with the prior caps every predictor near 50% however good it is,
        and a cell-size-independent blend punishes dense cells for the sins of sparse ones.
        Shrinking by a constant pseudo-weight lets a well-populated cell speak for itself
        while a thin one falls back, which is what makes the levels column comparable."""
        d = collections.defaultdict(collections.Counter)
        for r in tr:
            d[keyf(r)][r["management_category"]] += 1
        tot = w = 0.0
        for r in te:
            c = r["management_category"]
            cc = d.get(keyf(r))
            W = sum(cc.values()) if cc else 0.0
            pc = prior.get(c, 1e-9)
            p = (((cc.get(c, 0) if cc else 0) + m * pc) / (W + m))
            tot += -math.log2(max(p, 1e-12))
            w += 1
        return tot / w, len(d)

    H0, _ = score(lambda r: None)
    V = [("the facility handling it", lambda r: r["handler_id"], True),
         ("where it is (state)", lambda r: r["state"], False),
         ("what the waste is", lambda r: r["form_code"], False),
         ("the generator's industry", lambda r: (r["primary_naics"] or "?")[:3], False)]
    alone, plus = [], []
    hf, _ = score(lambda r: r["form_code"])
    for lab, kf, circ in V:
        L, n = score(kf)
        alone.append((lab, 1 - L / H0, n, circ))
        if lab != "what the waste is":
            L2, n2 = score(lambda r, k=kf: (r["form_code"], k(r)))
            plus.append((lab, (hf - L2) / H0, n2, circ))
    return H0, alone, plus, 1 - hf / H0


def build():
    rows = [r for r in brdata.load(2023) if num(r["managed_tons"]) > 0]
    H0, alone, plus, hform = ladder_heldout(rows)
    wr = [r for r in rows if r["br_form"] == "WR" and (r["shipper_id"] or "").strip()]
    vend = collections.defaultdict(lambda: [0.0, 0.0])
    sf = collections.defaultdict(lambda: collections.defaultdict(float))
    sfv = collections.defaultdict(lambda: collections.defaultdict(float))
    o_ = collections.defaultdict(lambda: [0.0, 0.0])
    formv = collections.defaultdict(collections.Counter)
    gn, gs = {}, {}
    for r in wr:
        t = num(r["managed_tons"]); c = r["management_category"]
        s = r["shipper_id"].strip(); f = r["form_code"]; h = r["handler_id"]
        if c in REC: vend[h][0] += t; o_[(s, f)][0] += t
        elif c in DIS: vend[h][1] += t; o_[(s, f)][1] += t
        sf[s][f] += t; sfv[(s, f)][h] += t; formv[f][h] += t
        gn.setdefault(s, (r["primary_naics"] or "?")[:3]); gs.setdefault(s, s[:2])
    orient = {h: a / (a + b) for h, (a, b) in vend.items() if a + b > 500}
    # Counted in STREAMS, not tons. The tonnage version is 84% against a 74% null: almost all
    # of it is the arithmetic of one dominant stream, not a choice. Counting distinct streams
    # removes that and leaves the decision.
    rnd = random.Random(7)
    obs, sim = [], []
    for s, v in sf.items():
        if len(v) < 3 or sum(v.values()) <= 50:
            continue
        per = collections.Counter()
        for f in v:
            per[max(sfv[(s, f)], key=sfv[(s, f)].get)] += 1
        obs.append(max(per.values()) / len(v))
        a = collections.Counter()
        for f in v:
            if not formv[f]:
                continue
            hs = list(formv[f]); ws = [formv[f][h] for h in hs]
            a[rnd.choices(hs, weights=ws)[0]] += 1
        if a:
            sim.append(max(a.values()) / len(v))
    obs.sort(); sim.sort()

    multi = {s: v for s, v in sf.items() if len(v) >= 2 and sum(v.values()) > 20}
    def run(fn):
        cells = collections.defaultdict(lambda: ([], []))
        for s, v in multi.items():
            fm = max(v, key=v.get)
            dv = max(sfv[(s, fm)], key=sfv[(s, fm)].get)
            o = orient.get(dv)
            if o is None:
                continue
            for f in v:
                if f == fm:
                    continue
                a, b = o_[(s, f)]
                if a + b <= 0:
                    continue
                cells[fn(s, f)][0 if o >= 0.5 else 1].append(a / (a + b))
        use = [(h, l) for h, l in cells.values() if len(h) >= 10 and len(l) >= 10]
        w = sum(len(h) + len(l) for h, l in use)
        g = sum((sum(h)/len(h) - sum(l)/len(l)) * (len(h)+len(l)) for h, l in use) / w
        return g, w, sum(1 for h, l in use if sum(h)/len(h) > sum(l)/len(l)), len(use)
    ctrl = [("same waste stream", run(lambda s, f: f)),
            ("+ same generator industry", run(lambda s, f: (f, gn[s]))),
            ("+ same generator state", run(lambda s, f: (f, gs[s]))),
            ("+ both", run(lambda s, f: (f, gn[s], gs[s])))]
    return (H0, alone, plus, hform), obs, sim, ctrl


def main():
    (H0, alone, plus, hform), obs, sim, ctrl = build()
    W, H = 1200, 775
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Not a coin toss: it is the map first, then the material, then the account.",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="a regulator or generator trying to raise the recovery rate",
                        decide="which lever to pull: commodity price, disposal fee, or procurement",
                        wrong="recovery moves with disposal fees but not with a change of vendor")
    s += fr

    AX, AY, AW = 28, 224, 232
    s.append(txt(AX, AY - 44, "what actually predicts a ton's fate", size=12.5, fill=INK, weight="600"))
    s.append(txt(AX, AY - 28, "uncertainty removed, scored per record on held-out rows", size=10.5, fill=MUTED))
    order = sorted(alone, key=lambda r: -r[1])
    pl = {lab: v for lab, v, _, _ in plus}
    s.append(txt(AX, AY - 10, "on its own", size=9.5, fill=BLUE, weight="600"))
    s.append(txt(AX + 76, AY - 10, "added to the waste type", size=9.5, fill=GREEN, weight="600"))
    for i2, (lab, v, n, circ) in enumerate(order):
        y = AY + i2 * 58
        s.append(txt(AX, y, lab + ("  *" if circ else ""), size=11, fill=INK,
                     weight="600" if not circ else "normal"))
        s.append(txt(AX + AW, y, f"{n:,} levels", size=9, fill=MUTED, anchor="end"))
        s.append(f'<rect x="{AX}" y="{y+6:.1f}" width="{AW}" height="12" fill="{GRID}"/>')
        s.append(f'<rect x="{AX}" y="{y+6:.1f}" width="{max(AW*v,0.8):.1f}" height="12" '
                 f'fill="{FAINT if circ else BLUE}"/>')
        s.append(txt(AX + AW + 8, y + 16, f"{v:.0%}", size=10.5,
                     fill=MUTED if circ else BLUE, weight="600"))
        inc = pl.get(lab)
        if inc is not None:
            s.append(f'<rect x="{AX}" y="{y+22:.1f}" width="{AW}" height="12" fill="{GRID}"/>')
            s.append(f'<rect x="{AX}" y="{y+22:.1f}" width="{max(AW*inc,0.8):.1f}" height="12" '
                     f'fill="{FAINT if circ else GREEN}"/>')
            s.append(txt(AX + AW + 8, y + 32, f"{inc:+.0%}", size=10.5,
                        fill=MUTED if circ else GREEN, weight="600"))
        else:
            s.append(txt(AX, y + 32, f"(the baseline, {hform:.0%} on its own)", size=9.5, fill=MUTED))
    s += wrap(AX, AY + 4 * 58 + 2,
              "* Circular: a landfill only landfills. Set it aside and location beats "
              "chemistry — on 51 levels against 50, so that is a fair fight.",
              size=10.5, fill=INK2, chars=44)

    BX, BY, BW_, BH = 408, 210, 330, 210
    s.append(txt(BX, BY - 44, "generators do not shop per stream", size=12.5, fill=INK, weight="600"))
    s.append(txt(BX, BY - 28, "share of a generator's distinct waste streams sent to one receiver",
                 size=10.5, fill=MUTED))
    cx = lambda v: BX + BW_ * v
    cy = lambda q: BY + BH - BH * q
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        s.append(f'<line x1="{cx(v):.1f}" y1="{BY}" x2="{cx(v):.1f}" y2="{BY+BH}" stroke="{GRID}"/>')
        s.append(txt(cx(v), BY + BH + 16, f"{v:.0%}", size=9.5, fill=MUTED, anchor="middle"))
    for arr, col, lab in ((sim, MUTED, "if each stream went to a\nfacility that handles it"),
                          (obs, GREEN, "what they actually do")):
        d = " ".join(f"{'M' if i == 0 else 'L'}{cx(v):.1f},{cy(i/len(arr)):.1f}"
                     for i, v in enumerate(arr))
        s.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.6"/>')
    med = lambda a: a[len(a)//2]
    s.append(txt(cx(med(obs)) - 6, cy(0.5) - 8, f"median {med(obs):.0%}", size=10.5, fill=GREEN,
                 anchor="end", weight="600"))
    s.append(txt(cx(med(sim)) + 6, cy(0.5) + 14, f"{med(sim):.0%}", size=10.5, fill=MUTED,
                 weight="600"))
    s.append(txt(BX, BY - 6, "what they actually do", size=10, fill=GREEN, weight="600"))
    s.append(txt(BX + 128, BY - 6, "if they shopped per stream", size=10, fill=MUTED))
    s += wrap(BX, BY + BH + 38,
              f"{sum(1 for v in obs if v > 0.999)/len(obs):.0%} send every stream they have to "
              f"one facility. Chance never does.", size=10.5, fill=INK2, chars=52)

    CX, CY, CW = 812, 210, 250
    s.append(txt(CX, CY - 44, "and it survives the obvious controls", size=12.5, fill=INK, weight="600"))
    s += wrap(CX, CY - 28, "extra recovery on a stream whose vendor was picked for a different waste",
              size=10.5, fill=MUTED, chars=44, leading=12)
    mx = max(g for _, (g, _, _, _) in ctrl)
    for i, (lab, (g, n, pos, k)) in enumerate(ctrl):
        y = CY + i * 56
        s.append(txt(CX, y, lab, size=11, fill=INK, weight="600" if i == 3 else "normal"))
        s.append(f'<rect x="{CX}" y="{y+6:.1f}" width="{max(CW*g/mx*0.86,0.8):.1f}" height="14" '
                 f'fill="{GREEN if i < 3 else AMBER}"/>')
        s.append(txt(CX + CW * g / mx * 0.86 + 8, y + 17, f"{g:+.0%}", size=10.5,
                     fill=GREEN if i < 3 else AMBER, weight="600"))
        s.append(txt(CX, y + 32, f"n {n:,} · {pos}/{k} strata positive", size=9.5, fill=MUTED))
    s += wrap(CX, CY + 4 * 56 + 2,
              "Half the raw effect was industry and geography. What survives them is "
              "procurement inertia.", size=10.5, fill=INK2, chars=44)

    s += wrap(28, 606,
              "A firm routing waste by an existing contract is not pricing each stream, so no "
              "metal price could move it. The lever is not the commodity price or the disposal "
              "fee — it is who holds the account.",
              size=13, fill=INK, chars=132, leading=17)

    fy = H - 20 - 14 * 5
    s.append(f'<line x1="28" y1="{fy-22:.1f}" x2="{W-28}" y2="{fy-22:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              "2023 cycle. Held-out cross-entropy over the twelve routes, scored per record; "
              "stable within 0.2 points across four splits. The vendor is set by a generator's "
              "largest stream and the outcome read only on its others, so nothing scores itself. "
              "Method in the recipe.",
              size=11, fill=MUTED, chars=152, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for lab, v, n, circ in sorted(alone, key=lambda r: -r[1]):
        print(f"    {lab:<28}{v:>7.1%}  {n:>6,} levels{'  (circular)' if circ else ''}")
    for lab, (g, n, pos, k) in ctrl:
        print(f"    {lab:<34}{g:+.1%}  n {n:,}  {pos}/{k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
