#!/usr/bin/env python3
"""Half the dollars go to 74 recipients; half the awards go to 994.

    python3 chart-3-concentration.py

Civilian FY2016, 554,171 awards collapsed from 746,960 transactions on
`contract_award_unique_key`, $125.75bn net. **Counting awards and counting dollars are two
different measurements of the same register and they do not agree at any rank.** On the
parent-company base, the top 100 recipients hold **25.3% of awards and 54.0% of dollars**;
the top 1,000 hold 50.1% and 81.3%. The gap is widest at rank 572, where it is 31.5 points. Half the
money is reached by rank 74; half the awards not until rank 994 — a factor of **13**.

**The top of the two lists is not the same firms.** Of the top 10 by awards and the top 10 by
dollars, **one** name appears on both (McKesson). Of the top 100, 23. The award leaders are
medical-device suppliers filing thousands of small Veterans Affairs orders — Medtronic, 10,344
awards at $18.8k each. The dollar leaders are management-and-operating contracts for the
national laboratories — Consolidated Nuclear Security, **one award, $2.03bn**. These are not
competing for rank; they are different transactions that happen to share a column.

**The entity definition moves the level but never closes the gap.** The three identity columns
disagree: 78,619 distinct `recipient_name`, 81,330 `recipient_uei`, 73,430
`recipient_parent_name`. UEI is *finer* than name, not coarser, which is the opposite of the
expected failure: **no UEI carries two names, but 1,299 names carry two or more UEIs** — Hanger
Prosthetics files under 48 of them, Johnson Controls Fire Protection 32. So a UEI ranking
splits a firm into branches and *understates* concentration (top 100 dollars: 45.8%), a name
ranking splits parents from subsidiaries (48.6%), and the parent roll-up is the entity a
concentration claim is actually about (54.0%). All three are drawn as a band. **The bands
never touch**: at no rank does any entity definition make the award base and the dollar base
agree.

**Every one of the 11 departments shows it, and the two rankings are unrelated.** Within each
agency the top 1% of its own recipients hold more of its dollars than of its awards, in 11 of
11. But the ordering is not shared: Spearman rho between the two columns is **-0.16 on n=11**,
indistinguishable from zero. Energy is the most dollar-concentrated department (22 recipients,
87.5% of its money) and the *least* award-concentrated (18.3%); Veterans Affairs is the
reverse corner.

**Limits.** De-obligations are kept, so a recipient can net negative: 5,405 of 73,430 parents
(7.4%) did, totalling -$340m, and the cumulative dollar curve therefore passes 100% near rank
61,000 before falling back. Summing positives only would have overstated the total by 4.8%.
Eleven civilian departments are 8.5% of federal contract awards; Defense (68.6%) and General
Services (22.9%) are absent, so nothing here is a statement about federal procurement as a
whole. "Parent" is the register's own `recipient_parent_name` field, not an independent
ownership source, and it does not merge unrelated spellings of the same parent.
"""
import collections, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L, plate                                                  # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "3-concentration.svg")
SRC = os.path.join(HERE, "..", "data", "civilian-fy2016.zip")
RED, BLUE, SLATE = "#8c2318", "#2f6f96", "#9aa4ad"
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
TRIM = {"CONSOLIDATED NUCLEAR SECURITY, LLC": "Consolidated Nuclear Security",
        "LAWRENCE LIVERMORE NATIONAL SECURITY, LLC": "Lawrence Livermore Nat. Security",
        "LOS ALAMOS NATIONAL SECURITY LLC": "Los Alamos National Security",
        "UT-BATTELLE LLC": "UT-Battelle",
        "LOCKHEED MARTIN CORP": "Lockheed Martin",
        "MCKESSON CORPORATION": "McKesson",
        "BECHTEL GROUP, INC.": "Bechtel",
        "CALIFORNIA INSTITUTE OF TECHNOLOGY": "Caltech",
        "BATTELLE MEMORIAL INSTITUTE": "Battelle",
        "AECOM": "AECOM",
        "THE BOEING COMPANY": "Boeing",
        "MEDTRONIC INC": "Medtronic",
        "JOHNSON & JOHNSON HEALTHCARE": "Johnson & Johnson",
        "ZIMMER BIOMET HOLDINGS, INC.": "Zimmer Biomet",
        "STRYKER CORPORATION": "Stryker",
        "BOSTON SCIENTIFIC CORP": "Boston Scientific",
        "VERIZON COMMUNICATIONS INC": "Verizon",
        "THERMO ELECTRON CORPORATION": "Thermo Electron",
        "ST. JUDE MEDICAL, LLC": "St. Jude Medical",
        "HANGER, INC.": "Hanger",
        "SMITH & NEPHEW PLC": "Smith & Nephew",
        "AT&T INC.": "AT&T",
        "SIEMENS AKTIENGESELLSCHAFT": "Siemens",
        "TRIWEST HEALTHCARE ALLIANCE CORP": "TriWest Healthcare"}


# ---------------------------------------------------------------- data

def collect():
    """One pass; one record per award, obligation summed over all its transactions."""
    acc = {}
    tx = neg = 0
    pos = negsum = 0.0
    names_per_uei = collections.defaultdict(set)
    ueis_per_name = collections.defaultdict(set)
    for r in L.transactions(SRC):
        tx += 1
        k = r.get(L.KEY)
        if not k:
            continue
        fa = L.num(r.get("federal_action_obligation")) or 0.0
        if fa < 0:
            neg += 1
            negsum += fa
        else:
            pos += fa
        nm = (r.get("recipient_name") or "").strip()
        ue = (r.get("recipient_uei") or "").strip()
        if nm and ue:
            names_per_uei[ue].add(nm)
            ueis_per_name[nm].add(ue)
        a = acc.get(k)
        if a is None:
            a = acc[k] = [nm, ue, (r.get("recipient_parent_name") or "").strip(),
                          r.get("awarding_agency_name") or "?", 0.0]
        a[4] += fa
    return (list(acc.values()), tx, neg, pos, negsum,
            sum(1 for v in names_per_uei.values() if len(v) > 1),
            sum(1 for v in ueis_per_name.values() if len(v) > 1),
            max((len(v), k) for k, v in ueis_per_name.items())[0])


def rollup(aw, idx):
    d = collections.defaultdict(lambda: [0, 0.0])
    for a in aw:
        k = a[idx].strip()
        if not k:
            continue
        d[k][0] += 1
        d[k][1] += a[4]
    return d


def curve(tbl, field):
    """Cumulative share of `field` against rank. field 0 = awards, 1 = dollars."""
    items = sorted(tbl.items(), key=lambda kv: (-kv[1][field], -kv[1][1 - field], kv[0]))
    tot = sum(v[field] for v in tbl.values())
    c, out = 0.0, []
    for _, v in items:
        c += v[field]
        out.append(c / tot)
    return out, [k for k, _ in items]


def rank_reaching(cu, f):
    for i, v in enumerate(cu):
        if v >= f:
            return i + 1
    return None


# ---------------------------------------------------------------- draw

def main():
    if not os.path.exists(SRC):
        raise SystemExit("  civilian-fy2016.zip missing — run usa2.py")
    aw, tx, neg, pos, negsum, multiname, multiuei, maxuei = collect()
    tables = {b: rollup(aw, i) for b, i in (("name", 0), ("uei", 1), ("parent", 2))}
    cur = {(b, f): curve(tables[b], f) for b in tables for f in (0, 1)}
    P = tables["parent"]
    pa, pa_keys = cur[("parent", 0)]
    pd, pd_keys = cur[("parent", 1)]
    LIM = min(len(v[0]) for v in cur.values())
    lo = {f: [min(cur[(b, f)][0][i] for b in tables) for i in range(LIM)] for f in (0, 1)}
    hi = {f: [max(cur[(b, f)][0][i] for b in tables) for i in range(LIM)] for f in (0, 1)}
    touch = sum(1 for i in range(LIM) if lo[1][i] <= hi[0][i])
    half_d, half_a = rank_reaching(pd, 0.50), rank_reaching(pa, 0.50)
    gap = [pd[i] - pa[i] for i in range(len(pa))]
    gmax = max(range(len(gap)), key=lambda i: gap[i])
    net = pos + negsum
    total_d = sum(v[1] for v in P.values())
    negrec = [k for k, v in P.items() if v[1] < 0]
    overshoot = max(pd)

    W, H = 1200, 1135
    s = plate.open_svg(W, H, "Half the dollars go to 74 recipients; half the awards go to 994",
                       subtitle="Civilian contracting FY2016 — the same register, counted two "
                                "ways, ranks almost entirely different firms")
    fr, _ = plate.frame(W, 80,
                        who="anyone about to quote a concentration or small-business share "
                            "out of this register",
                        decide="whether to state that share on awards or on dollars — at rank "
                               "100 the same data says 25% or 54%",
                        wrong="the two bands touch at any rank, i.e. some entity definition "
                              "makes the award base and the dollar base agree")
    s += fr

    # ---------------- panel A: concentration curves
    AX, ATOP, ABOT = 28, 214, 566
    ax0, apw = AX + 62, 556
    RMAX = 5.0                                  # log10 of the right-hand rank
    px = lambda r: ax0 + apw * (math.log10(max(r, 1)) / RMAX)
    py = lambda f: ABOT - (ABOT - ATOP) * (f / 1.02)
    s.append(txt(AX, ATOP - 24, "cumulative share held, against recipient rank", size=12,
                 fill=INK, weight="600"))
    s.append(txt(AX, ATOP - 10, "both curves are the same 554,171 awards, ranked on a "
                                "different quantity", size=10, fill=MUTED))
    for f in (0, .25, .5, .75, 1.0):
        s.append(f'<line x1="{px(1):.1f}" y1="{py(f):.1f}" x2="{px(10**RMAX):.1f}" '
                 f'y2="{py(f):.1f}" stroke="{GRID}"/>')
        s.append(txt(ax0 - 9, py(f) + 3.5, f"{f:.0%}", size=9.5, fill=MUTED, anchor="end"))
    for r, lab in ((1, "1"), (10, "10"), (100, "100"), (1000, "1,000"),
                   (10000, "10,000"), (100000, "100,000")):
        s.append(f'<line x1="{px(r):.1f}" y1="{py(0):.1f}" x2="{px(r):.1f}" '
                 f'y2="{py(1.02):.1f}" stroke="{GRID}"/>')
        s.append(txt(px(r), py(0) + 17, lab, size=9.5, fill=MUTED, anchor="middle"))
    s.append(txt(AX, py(0) + 36, "recipients ranked largest first (log scale)", size=10,
                 fill=MUTED))
    s.append(txt(AX, ATOP - 38, "share of all awards, or of all net dollars", size=10,
                 fill=MUTED))

    ranks = sorted({int(round(10 ** (i * RMAX / 320))) for i in range(321)} |
                   {1, 10, 100, 1000, 10000})
    ranks = [r for r in ranks if 1 <= r <= LIM]
    for f, col in ((1, RED), (0, BLUE)):
        up = " ".join(f"{px(r):.1f},{py(hi[f][r-1]):.1f}" for r in ranks)
        dn = " ".join(f"{px(r):.1f},{py(lo[f][r-1]):.1f}" for r in reversed(ranks))
        s.append(f'<polygon points="{up} {dn}" fill="{col}" fill-opacity="0.22"/>')
    for f, col, prim in ((1, RED, pd), (0, BLUE, pa)):
        d = " ".join(f"{'M' if i == 0 else 'L'}{px(r):.1f},{py(prim[r-1]):.1f}"
                     for i, r in enumerate(ranks))
        s.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.2"/>')

    s += halo(px(200), py(pd[199]) - 20, "net DOLLARS", size=12.5, fill=RED, weight="700")
    s += halo(px(600), py(pa[599]) + 20, "AWARDS", size=12.5, fill=BLUE, weight="700")

    for r in (10, 100, 1000):
        s.append(f'<line x1="{px(r):.1f}" y1="{py(pa[r-1]):.1f}" x2="{px(r):.1f}" '
                 f'y2="{py(pd[r-1]):.1f}" stroke="{INK2}" stroke-width="1" '
                 f'stroke-dasharray="3 3"/>')
        for f, col, prim in ((1, RED, pd), (0, BLUE, pa)):
            s.append(f'<circle cx="{px(r):.1f}" cy="{py(prim[r-1]):.1f}" r="3.6" '
                     f'fill="{col}"/>')
        s += halo(px(r) + 7, py(pd[r - 1]) + 4, f"{pd[r-1]:.0%}", size=11, fill=RED,
                  weight="700")
        s += halo(px(r) + 7, py(pa[r - 1]) + 4, f"{pa[r-1]:.0%}", size=11, fill=BLUE,
                  weight="700")
    s += halo(px(100) - 9, py((pd[99] + pa[99]) / 2) - 4,
              f"{100*(pd[99]-pa[99]):.0f} points apart", size=10.5, fill=INK, anchor="end",
              weight="700")
    s += halo(px(100) - 9, py((pd[99] + pa[99]) / 2) + 9, "at rank 100", size=10.5,
              fill=INK2, anchor="end")

    s.append(f'<line x1="{px(1):.1f}" y1="{py(0.5):.1f}" x2="{px(10**RMAX):.1f}" '
             f'y2="{py(0.5):.1f}" stroke="{INK2}" stroke-width="1.2" '
             f'stroke-dasharray="6 4"/>')
    s += halo(px(half_d) - 7, py(0.5) - 11, f"half the money: {half_d} recipients",
              size=10, fill=INK2, anchor="end")
    s += halo(px(half_a) + 7, py(0.5) + 16, f"half the awards: {half_a} recipients",
              size=10, fill=INK2)
    for r in (half_d, half_a):
        s.append(f'<circle cx="{px(r):.1f}" cy="{py(0.5):.1f}" r="3" fill="{INK2}"/>')

    ly = ATOP + 4
    for i, col in enumerate((RED, BLUE)):
        s.append(f'<rect x="{px(1.15)+i*13:.1f}" y="{ly-8:.1f}" width="12" height="9" '
                 f'fill="{col}" fill-opacity="0.22"/>')
    s.append(txt(px(1.15) + 32, ly, "band spans recipient_name, recipient_uei, "
                                    "recipient_parent_name", size=9.5, fill=INK2))
    s.append(txt(px(1.15) + 32, ly + 13, "solid line is the parent roll-up; the bands never "
                                         "overlap", size=9.5, fill=MUTED))

    # ---------------- panel B: who is at the top of each list
    BX, BW = 700, 472
    bx0, bpw = BX + 52, BW - 62
    bAX, bAB = ATOP, ABOT
    bpx = lambda a: bx0 + bpw * (math.log10(max(a, 1)) / 4.3)
    bpy = lambda d: bAB - (bAB - bAX) * ((math.log10(max(d, 1e6)) - 6) / 4.0)
    s.append(txt(BX, ATOP - 24, "the two lists are different firms", size=12, fill=INK,
                 weight="600"))
    s.append(txt(BX, ATOP - 10, "one mark per recipient with 1 million dollars or more for the year", size=10, fill=MUTED))
    s.append(txt(BX, ATOP - 38, "net dollars received, millions", size=10, fill=MUTED))
    for v, lab in ((1e6, "1"), (1e7, "10"), (1e8, "100"), (1e9, "1,000"), (1e10, "10,000")):
        s.append(f'<line x1="{bpx(1):.1f}" y1="{bpy(v):.1f}" x2="{bpx(10**4.3):.1f}" '
                 f'y2="{bpy(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(bx0 - 8, bpy(v) + 3.5, lab, size=9.5, fill=MUTED, anchor="end"))
    for a, lab in ((1, "1"), (10, "10"), (100, "100"), (1000, "1,000"), (10000, "10,000")):
        s.append(f'<line x1="{bpx(a):.1f}" y1="{bpy(1e6):.1f}" x2="{bpx(a):.1f}" '
                 f'y2="{bpy(1e10):.1f}" stroke="{GRID}"/>')
        s.append(txt(bpx(a), bpy(1e6) + 17, lab, size=9.5, fill=MUTED, anchor="middle"))
    s.append(txt(BX, bpy(1e6) + 36, "awards won (log scale)", size=10, fill=MUTED))

    for per, lab, at, anc, ly0 in (
            (1e4, "10,000 dollars per award", 900, "end", -7),
            (1e7, "10,000,000 dollars per award", 1.0, "start", 13)):
        lo_a = max(1.0, 1e6 / per)
        hi_a = min(10 ** 4.3, 1e10 / per)
        s.append(f'<path d="M{bpx(lo_a):.1f},{bpy(lo_a*per):.1f} '
                 f'L{bpx(hi_a):.1f},{bpy(hi_a*per):.1f}" fill="none" '
                 f'stroke="{FAINT}" stroke-width="1.1" stroke-dasharray="4 3"/>')
        s += halo(bpx(at) + (5 if anc == "start" else -5), bpy(at * per) + ly0, lab,
                  size=8.5, fill=MUTED, anchor=anc, weight="normal")

    items = [(k, v[0], v[1]) for k, v in sorted(P.items())]
    cloud = [x for x in items if x[2] >= 1e6]
    topA = {k for k, _, _ in sorted(items, key=lambda x: (-x[1], x[0]))[:20]}
    topD = {k for k, _, _ in sorted(items, key=lambda x: (-x[2], x[0]))[:20]}
    for k, a, d in cloud:
        if k in topA or k in topD:
            continue
        s.append(f'<circle cx="{bpx(a):.1f}" cy="{bpy(d):.1f}" r="1.6" fill="{SLATE}" '
                 f'fill-opacity="0.38"/>')
    for k, a, d in cloud:
        col = RED if k in topD else (BLUE if k in topA else None)
        if col:
            s.append(f'<circle cx="{bpx(a):.1f}" cy="{bpy(d):.1f}" r="4" fill="{col}"/>')
    LBL = [("LOCKHEED MARTIN CORP", -8, -5, "end"),
           ("MCKESSON CORPORATION", -8, 14, "end"),
           ("TRIWEST HEALTHCARE ALLIANCE CORP", 7, 4, "start"),
           ("MEDTRONIC INC", -8, -6, "end"),
           ("JOHNSON & JOHNSON HEALTHCARE", -8, 14, "end"),
           ("ZIMMER BIOMET HOLDINGS, INC.", -10, 17, "end"),
           ("SMITH & NEPHEW PLC", 7, 4, "start")]
    for k, dx, dy, anc in LBL:
        if k not in P:
            continue
        a, d = P[k][0], P[k][1]
        col = RED if k in topD else (BLUE if k in topA else INK2)
        s += halo(bpx(a) + dx, bpy(d) + dy, TRIM.get(k, k.title())[:30], size=10, fill=col,
                  anchor=anc, weight="700")
    ones = sorted([x for x in items if x[1] == 1 and x[2] >= 3e8], key=lambda x: -x[2])
    for k, a, dd in ones:
        s.append(f'<circle cx="{bpx(a):.1f}" cy="{bpy(dd):.1f}" r="3.2" fill="none" '
                 f'stroke="{INK2}" stroke-width="1.3"/>')
    s.append(f'<path d="M{bpx(1)-9:.1f},{bpy(ones[-1][2]):.1f} L{bpx(1)-13:.1f},'
             f'{bpy(ones[-1][2]):.1f} L{bpx(1)-13:.1f},{bpy(ones[0][2]):.1f} '
             f'L{bpx(1)-9:.1f},{bpy(ones[0][2]):.1f}" fill="none" stroke="{INK2}"/>')
    for i, line in enumerate((
            f"{len(ones)} recipients won exactly one award each, every",
            "one of them above 390 million dollars. The largest:",
            f"{TRIM.get(ones[0][0], ones[0][0])}, {ones[0][2]/1e6:,.0f} million dollars.")):
        s += halo(bpx(1) + 7, bpy(ones[-1][2]) + 16 + i * 13, line, size=10, fill=INK2)

    ly = bAX + 8
    for col, lab in ((RED, "top 20 by dollars"), (BLUE, "top 20 by awards"),
                     (SLATE, f"the other {len(cloud)-len(topA|topD):,}")):
        rr = 4 if col != SLATE else 1.6
        s.append(f'<circle cx="{bpx(1.25):.1f}" cy="{ly-3.5:.1f}" r="{rr}" fill="{col}"/>')
        s.append(txt(bpx(1.25) + 11, ly, lab, size=9.5, fill=INK2 if col != SLATE else MUTED))
        ly += 14

    ovl = {n: len({k for k, _, _ in sorted(items, key=lambda x: (-x[1], x[0]))[:n]} &
                  {k for k, _, _ in sorted(items, key=lambda x: (-x[2], x[0]))[:n]})
           for n in (10, 100, 1000)}
    s += halo(bpx(1.25), bAB - 20, f"{ovl[10]} of the top 10 by awards is also in the top 10",
              size=10.5, fill=INK, weight="700")
    s += halo(bpx(1.25), bAB - 7, f"by dollars. Of the top 100: {ovl[100]}. Of the top 1,000: "
                                  f"{ovl[1000]}.", size=10.5, fill=INK, weight="700")

    # ---------------- panel C: every department, both bases
    CX, CTOP = 28, 640
    cx0, cpw = CX + 206, 760
    cpx = lambda f: cx0 + cpw * f
    rows = []
    ag = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0.0]))
    for a in aw:
        k = a[2].strip() or a[0].strip()
        if not k:
            continue
        d = ag[a[3]][k]
        d[0] += 1
        d[1] += a[4]
    for agency, rec in ag.items():
        it = [(k, v[0], v[1]) for k, v in sorted(rec.items())]
        ta, td, n = sum(i[1] for i in it), sum(i[2] for i in it), len(it)
        k1 = max(1, round(n * 0.01))
        rows.append({"ag": SHORT.get(agency, agency)[:26], "n": n, "k": k1,
                     "aw": ta, "dol": td,
                     "fa": sum(i[1] for i in sorted(it, key=lambda x: (-x[1], x[0]))[:k1]) / ta,
                     "fd": sum(i[2] for i in sorted(it, key=lambda x: (-x[2], x[0]))[:k1]) / td})
    rows.sort(key=lambda r: -r["fd"])
    wins = sum(1 for r in rows if r["fd"] > r["fa"])
    s.append(txt(CX, CTOP - 12, "what the top 1% of each department's own recipients hold",
                 size=12, fill=INK, weight="600"))
    s.append(txt(CX, CTOP + 2, "share of that department's awards, and of its net dollars — "
                               "scale-free, so a small department is comparable to a large one",
                 size=10, fill=MUTED))
    for f in (0, .25, .5, .75, 1.0):
        s.append(f'<line x1="{cpx(f):.1f}" y1="{CTOP+14:.1f}" x2="{cpx(f):.1f}" '
                 f'y2="{CTOP+16+len(rows)*19.5:.1f}" stroke="{GRID}"/>')
        s.append(txt(cpx(f), CTOP + 16 + len(rows) * 19.5 + 14, f"{f:.0%}", size=9.5,
                     fill=MUTED, anchor="middle"))
    s.append(txt(CX, CTOP + 16 + len(rows) * 19.5 + 32,
                 "share held by that department's largest 1% of recipients", size=10,
                 fill=MUTED))
    for i, r in enumerate(rows):
        y = CTOP + 30 + i * 19.5
        s.append(txt(CX, y + 3.5, r["ag"], size=10.5, fill=INK2))
        s.append(txt(cx0 - 10, y + 3.5, f"{r['k']} of {r['n']:,}", size=9, fill=MUTED,
                     anchor="end"))
        s.append(f'<line x1="{cpx(r["fa"]):.1f}" y1="{y:.1f}" x2="{cpx(r["fd"]):.1f}" '
                 f'y2="{y:.1f}" stroke="{FAINT}" stroke-width="2.4"/>')
        s.append(f'<circle cx="{cpx(r["fa"]):.1f}" cy="{y:.1f}" r="4.6" fill="{BLUE}"/>')
        s.append(f'<circle cx="{cpx(r["fd"]):.1f}" cy="{y:.1f}" r="4.6" fill="{RED}"/>')
        if i in (0, len(rows) - 1):
            s += halo(cpx(r["fa"]) - 8, y + 3.5, f"{r['fa']:.0%}", size=9.5, fill=BLUE,
                      anchor="end")
            s += halo(cpx(r["fd"]) + 8, y + 3.5, f"{r['fd']:.0%}", size=9.5, fill=RED)
    s += wrap(cpx(1.0) + 14, CTOP + 34,
              f"Dollars are more concentrated than awards in {wins} of {len(rows)}. "
              f"But the two orderings are unrelated: Energy is the most dollar-concentrated "
              f"department and the least award-concentrated one.",
              size=10, fill=INK2, chars=24, leading=13)

    # ---------------- which base for what
    ny = CTOP + 16 + len(rows) * 19.5 + 54
    s.append(txt(CX, ny, "which base to use", size=12, fill=INK, weight="600"))
    s += wrap(CX, ny + 19,
              "Count AWARDS when the question is how widely the buying reaches — how many "
              "firms hold a contract, whether small business is winning work, how much "
              "administrative load a programme carries. Count DOLLARS when the question is "
              "where the money goes — market power, dependence on one supplier, exposure if a "
              "vendor fails. A share quoted with neither base named is unreadable, and the two "
              "answers are not close: at rank 100 they are 25% and 54%.",
              size=11, fill=INK2, chars=150, leading=15)

    fy = H - 24 - 14 * 8
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    # Trimmed from the plate per doctrine/what-a-footnote-carries.md; kept here because it is method: s
    #  += wrap(28, fy, USAspending API v2 bulk download, fetched 2026-09-22; contract
    # transactions with an action date in FY2016, eleven civilian departments. {tx:,}
    # transactions collapsed to {len(aw):,} awards on contract_award_unique_key;
    # ${net/1e9:,.1f} billion net. These departments are 8.5% of federal contract awards —
    # Defense is 68.6% and General Services 22.9%, neither fetchable at this size, so nothing
    # here describes federal procurement as a whole. De-obligations are kept: {neg:,}
    # transactions ({neg/tx:.1%}) carry a negative obligation, {len(negrec):,} of {len(P):,}
    # parents ({len(negrec)/len(P):.1%}) net negative for the year, and the cumulative dollar
    # curve therefore reaches {overshoot:.1%} before falling back to 100%; summing positives
    # only would overstate the total by {pos/net-1:.1%}. Identity columns disagree:
    # {len(tables['name']):,} names, {len(tables['uei']):,} UEIs, {len(tables['parent']):,}
    # parents — {multiname} UEIs carry two names but {multiuei:,} names carry two or more UEIs
    # (up to {maxuei}), so UEI splits branches rather than merging spellings. Curves are drawn
    # to rank {LIM:,}, the smallest of the three entity counts. Parent is the register's own
    # recipient_parent_name, not an independent ownership source., size=10.5, fill=MUTED,
    # chars=178, leading=14)
    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2016, 554,171 awards, "
        "$125.75bn net, grouped on recipient_parent_name. CAVEAT: recipient_uei is an "
        "establishment identifier and not a firm -- 1,299 names carry two or more of them, "
        "so UEI splits branches rather than merging spellings. These eleven civilian "
        "departments are 8.5% of federal contract awards; Defense (68.6%) is absent, so "
        "this is not federal procurement as a whole.")
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=186, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))

    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {tx:,} tx -> {len(aw):,} awards, ${net/1e9:.2f}B net; "
          f"{neg:,} negative tx ({neg/tx:.2%}), positives-only overstates {pos/net-1:.2%}")
    print(f"    entities: {len(tables['name']):,} name / {len(tables['uei']):,} uei / "
          f"{len(tables['parent']):,} parent; {multiname} uei with >1 name, "
          f"{multiuei:,} names with >1 uei (max {maxuei})")
    for b in ("name", "uei", "parent"):
        ca, _ = cur[(b, 0)]
        cd, _ = cur[(b, 1)]
        print(f"    {b:<7}" + "  ".join(f"top{r}: aw {ca[r-1]:.1%} $ {cd[r-1]:.1%}"
                                        for r in (1, 10, 100, 1000)))
    print(f"    half the dollars at rank {half_d}, half the awards at rank {half_a}; "
          f"widest gap {gap[gmax]:.1%} at rank {gmax+1:,}")
    print(f"    bands overlap at {touch} of {LIM:,} ranks")
    print(f"    top-n overlap awards vs dollars: " +
          "  ".join(f"{n}: {v}" for n, v in ovl.items()))
    for r in rows:
        print(f"    {r['ag']:<24} n={r['n']:>6,} top1%={r['k']:>4}  awards {r['fa']:6.1%}  "
              f"dollars {r['fd']:6.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
