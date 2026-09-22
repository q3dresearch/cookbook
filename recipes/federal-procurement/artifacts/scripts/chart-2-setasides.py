#!/usr/bin/env python3
"""Every department is below the line, and a set-aside lacks the tail, not the typical award.

    python3 chart-2-setasides.py

Figure 1 shows the award base and the dollar base parting company. This asks who it lands on.

**It is not one department's habit.** The dollar share sits below the award share in **11 of
11** departments, from a ratio of 0.86 at Agriculture to 0.07 at Energy, which gives 67% of
its awards to small business and 4.7% of its dollars. Leaving any single department out moves
the headline dollar share only between 24.6% and 32.2%.

**And the reserved programmes are not small work.** All ten reservations with 500 or more
awards have a median award **above** the register's own median of $7,978. The main
small-business set-aside is 17.4% of awards against 8.5% of dollars while its typical award is
larger than the typical federal award -- the shortfall is a missing tail, not small work.

**One mark to read carefully.** The blank set-aside field is 2% of awards and 9.1% of dollars,
and 26% of that is a single $3.0bn contract, with the top ten at 73.5%. It is drawn with a
warning because without the top-contributor check it reads as a programme.

**Two panels, not three.** The control that asked whether reserved awards are documented
differently came back empty, and a failed control is a paragraph for the recipe rather than a
column of prose competing with the marks. It is in the README.
"""
import bisect, collections, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate, sbiz                                                       # noqa: E402
from sbiz import (read_awards, med, SRC, SMALL, NONE_SA, SHORT, SA_SHORT,
                  RED, AMBER, GREEN, BLUE, SLATE)                  # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "2-setasides.svg")


def main():
    if not os.path.exists(SRC):
        raise SystemExit("  civilian-fy2016.zip missing -- run usa2.py")
    print("  reading transactions...", flush=True)
    aw, M = read_awards(SRC)
    ntx, disagree = M["tx"], M["disagree"]
    n = len(aw)
    tot = sum(a["ob"] for a in aw)
    sm = [a for a in aw if a["size"] == SMALL]
    aw_share = len(sm) / n
    dol_share = sum(a["ob"] for a in sm) / tot
    # --- B: one mark per department
    byag = collections.defaultdict(list)
    for a in aw:
        byag[a["ag"]].append(a)
    ags = []
    for ag, g in byag.items():
        if len(g) < 2000:
            continue
        t = sum(a["ob"] for a in g)
        s = [a for a in g if a["size"] == SMALL]
        ags.append({"ag": SHORT.get(ag, ag), "n": len(g), "x": len(s) / len(g),
                    "y": sum(a["ob"] for a in s) / t})
    ags.sort(key=lambda d: -d["n"])
    worst = min(ags, key=lambda d: d["y"] / d["x"])
    lo_lift = worst["y"] / worst["x"]
    hi_lift = max(d["y"] / d["x"] for d in ags)
    n_below = sum(1 for d in ags if d["y"] < d["x"])
    bn = [a for a in aw if a["ob"] >= 1e9]
    bn_worst = sum(1 for a in bn
                   if SHORT.get(a["ag"], a["ag"]) == worst["ag"])
    drops = []
    for ag in byag:
        sub = [a for a in aw if a["ag"] != ag]
        t = sum(a["ob"] for a in sub)
        drops.append(sum(a["ob"] for a in sub if a["size"] == SMALL) / t)

    # --- C: one mark per set-aside programme
    bysa = collections.defaultdict(list)
    for a in aw:
        bysa[a["sa"]].append(a["ob"])
    sas = []
    for k, v in bysa.items():
        if len(v) < 500:
            continue
        sas.append({"k": SA_SHORT.get(k, k.title()[:22]), "n": len(v), "med": med(v),
                    "mean": sum(v) / len(v), "aw": len(v) / n, "dol": sum(v) / tot,
                    "top": max(v) / sum(v) if sum(v) > 0 else 0.0})
    sas.sort(key=lambda d: -d["n"])
    reg_mean, reg_med = tot / n, med([a["ob"] for a in aw])
    anysa = [a for a in aw if a["sa"] and a["sa"] != NONE_SA]
    sa_aw, sa_dol = len(anysa) / n, sum(a["ob"] for a in anysa) / tot

    # --- the agency control on ceiling documentation
    grp = lambda a: ("none" if a["sa"] == NONE_SA else
                     "sdv" if a["sa"].startswith("SERVICE DISABLED") else
                     "8as" if a["sa"] == "8(A) SOLE SOURCE" else
                     "8ac" if a["sa"] == "8A COMPETED" else
                     "sbsa" if a["sa"] == "SMALL BUSINESS SET ASIDE - TOTAL" else
                     "any" if a["sa"] else None)
    pool = collections.defaultdict(lambda: [0, 0])
    per = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    for a in aw:
        g = grp(a)
        if g is None:
            continue
        for key in ({g} | ({"any"} if g not in ("none", "any") else set())):
            pool[key][0] += 1
            pool[key][1] += a["ceil"]
            d = per[a["ag"]][key]
            d[0] += 1
            d[1] += a["ceil"]
    base_cov = pool["none"][1] / pool["none"][0]
    ctl = {}
    for key in ("none", "any", "sbsa", "sdv", "8as", "8ac"):
        gaps = []
        for ag, d in per.items():
            b, v = d.get("none", [0, 0]), d.get(key, [0, 0])
            if b[0] < 500 or v[0] < 100:
                continue
            gaps.append(v[1] / v[0] - b[1] / b[0])
        ctl[key] = {"pool": pool[key][1] / pool[key][0] - base_cov, "k": len(gaps),
                    "up": sum(1 for g in gaps if g > 0), "med": med(gaps) if gaps else 0.0,
                    "cov": pool[key][1] / pool[key][0],
                    "lo": min(gaps) if gaps else 0.0, "hi": max(gaps) if gaps else 0.0}
    va = [a for a in aw if a["sa"].startswith("SERVICE DISABLED")]
    va_share = sum(1 for a in va if a["ag"] == "Department of Veterans Affairs") / len(va)


    right_of_med = sum(1 for d in sas if d["k"] not in ("no set-aside", "field left blank")
                       and d["med"] > reg_med)
    n_res = sum(1 for d in sas if d["k"] not in ("no set-aside", "field left blank"))
    sasd = [d for d in sas if d["n"] >= 800]
    tiny = [v for k, v in bysa.items() if len(v) < 800]
    small_k = len(tiny)
    small_aw = sum(len(v) for v in tiny) / n
    small_dol = sum(sum(v) for v in tiny) / tot


    # ------------------------------------------------------------------- draw
    W, H = 1280, 806
    s = plate.open_svg(
        W, H,
        "Every department is below the line, and a set-aside lacks the tail",
        subtitle=f"Where figure 1's gap lands. Small business is {aw_share:.1%} of civilian "
                 f"FY2016 awards and {dol_share:.1%} of the dollars; no department escapes it "
                 f"and no reserved programme has a small typical award.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone attributing the dollar gap to one agency's habit, or to set-asides "
            "being small work",
        decide="whether to treat the shortfall as a programme effect or as a missing tail",
        wrong="any department sits on or above the diagonal, or a reservation's median "
              "award falls below the register's own")
    s += fr

    # ---- panel A: one mark per department ---------------------------------
    AX, AY, AS = 64, y0 + 58, 452
    ax = lambda v: AX + 44 + (AS - 62) * v / 0.80
    ay = lambda v: AY + AS - 40 - (AS - 62) * v / 0.80
    s.append(txt(AX - 36, AY - 34, "small business inside each department",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(AX - 36, AY - 17, "share of its awards against share of its dollars; "
                                   "area is its awards", size=10, fill=MUTED))
    for g in (0.0, 0.25, 0.50, 0.75):
        s.append(f'<line x1="{ax(g):.1f}" y1="{ay(0):.1f}" x2="{ax(g):.1f}" '
                 f'y2="{ay(0.80):.1f}" stroke="{GRID}"/>')
        s.append(f'<line x1="{ax(0):.1f}" y1="{ay(g):.1f}" x2="{ax(0.80):.1f}" '
                 f'y2="{ay(g):.1f}" stroke="{GRID}"/>')
        s.append(txt(ax(g), ay(0) + 16, f"{g:.0%}", size=9, fill=MUTED, anchor="middle"))
        s.append(txt(ax(0) - 8, ay(g) + 3, f"{g:.0%}", size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX - 36, ay(0) + 34, "share of its awards", size=9.5, fill=MUTED))
    s.append(f'<text x="{AX-14}" y="{ay(0):.1f}" font-size="9.5" fill="{MUTED}" '
             f'transform="rotate(-90 {AX-14} {ay(0):.1f})">share of its dollars</text>')
    s.append(f'<path d="M{ax(0):.1f},{ay(0):.1f} L{ax(0.80):.1f},{ay(0.80):.1f}" '
             f'fill="none" stroke="{INK2}" stroke-width="1.4" stroke-dasharray="5 3"/>')
    s += halo(ax(0.30), ay(0.36), "on this line the two", size=9.5, fill=INK2)
    s += halo(ax(0.30), ay(0.36) + 12, "bases would agree", size=9.5, fill=INK2)
    OFF = {"Veterans Affairs": (-1, 4), "Health & Human Svcs": (-1, 14),
           "Commerce": (1, 4), "Interior": (1, 4), "Agriculture": (-1, 4),
           "Homeland Security": (1, 4), "Transportation": (1, 4), "Justice": (1, 14),
           "EPA": (-1, 4), "NASA": (1, 4), "Energy": (1, 4)}
    for d in sorted(ags, key=lambda z: -z["n"]):
        r = max(3.2, math.sqrt(d["n"]) / 62)
        s.append(f'<circle cx="{ax(d["x"]):.1f}" cy="{ay(d["y"]):.1f}" r="{r:.1f}" '
                 f'fill="{RED}" fill-opacity="0.16" stroke="{RED}" stroke-width="1.3"/>')
        sx, dy = OFF.get(d["ag"], (1, 4))
        s += halo(ax(d["x"]) + sx * (r + 5), ay(d["y"]) + dy, d["ag"], size=9.5, fill=RED,
                  anchor="start" if sx > 0 else "end", weight="700")
    s += halo(ax(0.02), ay(0.76), f"{n_below} of {len(ags)} below the line", size=9.5,
              fill=RED, weight="700")
    s += halo(ax(0.02), ay(0.76) - 13, f"leave any one out and the headline moves only "
              f"{min(drops):.1%} to {max(drops):.1%}", size=9.5, fill=INK2)

    # ---- panel B: one mark per set-aside programme ------------------------
    # Axes are the claim itself: a bigger typical award (x) against less than its
    # proportionate share of dollars (y). Median-against-mean on two identical log
    # ranges wasted most of the panel and did not draw the paradox.
    BX, BY, BS = 700, AY, 452
    lo, hi = 4000, 45000
    lg = lambda v: math.log10(min(max(v, lo), hi))
    bx = lambda v: BX + 58 + (BS - 76) * (lg(v) - lg(lo)) / (lg(hi) - lg(lo))
    ylo, yhi = 0.0, 4.8
    by = lambda v: BY + BS - 40 - (BS - 62) * (min(v, yhi) - ylo) / (yhi - ylo)
    s.append(txt(BX - 30, AY - 34, "each reserved programme: bigger awards, smaller share",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(BX - 30, AY - 17, "typical award against whether the programme takes "
                                   "dollars in proportion to its award count",
                 size=10, fill=MUTED))
    for v, lab in ((5000, "$5k"), (10000, "$10k"), (20000, "$20k"), (40000, "$40k")):
        s.append(f'<line x1="{bx(v):.1f}" y1="{by(ylo):.1f}" x2="{bx(v):.1f}" '
                 f'y2="{by(yhi):.1f}" stroke="{GRID}"/>')
        s.append(txt(bx(v), by(ylo) + 16, lab, size=9, fill=MUTED, anchor="middle"))
    for g in (0, 1, 2, 3, 4):
        s.append(f'<line x1="{bx(lo):.1f}" y1="{by(g):.1f}" x2="{bx(hi):.1f}" '
                 f'y2="{by(g):.1f}" stroke="{GRID}"/>')
        s.append(txt(bx(lo) - 8, by(g) + 3, f"{g}.0x", size=9, fill=MUTED, anchor="end"))
    s.append(txt(BX - 30, by(ylo) + 34, "median award in the programme (log)",
                 size=9.5, fill=MUTED))
    s.append(f'<text x="{BX+2}" y="{by(ylo):.1f}" font-size="9.5" fill="{MUTED}" '
             f'transform="rotate(-90 {BX+2} {by(ylo):.1f})">'
             f'dollar share divided by award share</text>')
    s.append(f'<line x1="{bx(reg_med):.1f}" y1="{by(ylo):.1f}" x2="{bx(reg_med):.1f}" '
             f'y2="{by(yhi):.1f}" stroke="{INK2}" stroke-width="1.2" stroke-dasharray="4 3"/>')
    s.append(f'<line x1="{bx(lo):.1f}" y1="{by(1.0):.1f}" x2="{bx(hi):.1f}" '
             f'y2="{by(1.0):.1f}" stroke="{INK2}" stroke-width="1.2" stroke-dasharray="4 3"/>')
    s += halo(bx(reg_med), by(0.08),
              f"the register's own median award, ${reg_med:,.0f}", size=9, fill=INK2,
              anchor="middle")
    s += halo(bx(hi) - 4, by(1.62), "on this line a programme takes dollars",
              size=9, fill=INK2, anchor="end")
    s += halo(bx(hi) - 4, by(1.62) + 12, "exactly in proportion to its awards",
              size=9, fill=INK2, anchor="end")
    SOFF = {"no set-aside": (-1, 4), "field left blank": (1, 4),
            "small business, total": (-1, 4), "8(a) competed": (-1, -8),
            "8(a) sole source": (1, -9), "service-disabled veteran": (1, 4),
            "HUBZone": (-1, -9), "small business, partial": (-1, 15),
            "Indian small business": (-1, 4), "women-owned": (-1, 4),
            "veteran sole source": (1, 15), "SDVOSB sole source": (1, 4)}
    for d in sorted(sas, key=lambda z: -z["n"]):
        r = max(3.4, math.sqrt(d["n"]) / 58)
        col = AMBER if d["top"] >= 0.20 else (GREEN if d["dol"] / d["aw"] < 1 else RED)
        ratio = d["dol"] / d["aw"]
        s.append(f'<circle cx="{bx(d["med"]):.1f}" cy="{by(ratio):.1f}" r="{r:.1f}" '
                 f'fill="{col}" fill-opacity="0.18" stroke="{col}" stroke-width="1.3"/>')
        sx, dy = SOFF.get(d["k"], (1, 4))
        s += halo(bx(d["med"]) + sx * (r + 5), by(ratio) + dy, d["k"], size=9.5,
                  fill=col, anchor="start" if sx > 0 else "end", weight="700")
    blank = next((d for d in sas if d["k"] == "field left blank"), None)
    if blank:
        s += halo(bx(blank["med"]) + 9, by(blank["dol"] / blank["aw"]) + 17,
                  f"{blank['top']:.0%} of this is one contract", size=9,
                  fill=AMBER, weight="700")
    right = sum(1 for d in sas if d["med"] > reg_med and d["k"] != "no set-aside")
    tot_res = sum(1 for d in sas if d["k"] != "no set-aside")
    s += halo(bx(lo) + 8, by(3.15), f"all set-asides together: {sa_aw:.1%} of awards, "
              f"{sa_dol:.1%} of dollars", size=9.5, fill=INK2)
    s += halo(bx(lo) + 8, by(3.15) + 13, f"{right} of {tot_res} reservations sit right of "
              f"the register's median", size=9.5, fill=INK2, weight="700")
    s += halo(bx(lo) + 8, by(3.15) + 26, "and below the proportionality line",
              size=9.5, fill=INK2, weight="700")

    # ---- footer -----------------------------------------------------------
    # FOOTNOTE BEFORE TRIMMING, kept because it is method and method belongs in the script: f
    # oot = (USAspending API v2 bulk download, fetched 2026-09-22; {ntx:,} prime contract
    # transactions with an action date in FY2016 for eleven civilian departments, collapsed
    # to {n:,} awards on contract_award_unique_key. Business size is the contracting
    # officer's determination on the base action, not an audited status; it disagrees
    # between transactions of one award on {disagree} rows. Departments with fewer than
    # 2,000 awards are not drawn, nor are set-aside programmes with fewer than 500. Dollars
    # are the sum of federal_action_obligation per award with de-obligations included. A
    # mark is drawn amber where one contract is 20% or more of its category's dollars, which
    # is true only of the blank set-aside field. The control asking whether reserved awards
    # are documented differently came back empty and is reported in the recipe, not here:
    # four of its five pooled differences reverse sign once measured inside each department.
    # These eleven departments are 8.5% of federal contract awards, Defense is 68.6% and
    # General Services 22.9%, so nothing here describes federal procurement as a whole. The
    # size-against-share view is figure 1.)
    # Trimmed from the plate per doctrine/what-a-footnote-carries.md; kept here because it is method: f
    # oot = ( USAspending API v2 bulk download, fetched 2026-09-22; FY2016, 554,171 awards.
    # CAVEAT: business size is the contracting officer's determination on the base action, not
    # an audited status. The blank set-aside mark is 26% a single $3.0bn contract, which is
    # why it is drawn amber. These eleven civilian departments are 8.5% of federal contract
    # awards; Defense (68.6%) is absent, so this is not federal procurement as a whole.)
    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2016, 554,171 awards. "
        "CAVEAT: business size is the contracting officer's determination on the base "
        "action, not an audited status. The blank set-aside mark is 26% a single $3.0bn "
        "contract, which is why it is drawn amber. These eleven civilian departments are "
        "8.5% of federal contract awards; Defense (68.6%) is absent, so this is not federal "
        "procurement as a whole.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=186, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=186, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {n_below}/{len(ags)} departments below the line; "
          f"leave-one-out {min(drops):.1%} to {max(drops):.1%}")
    print(f"    all set-asides {sa_aw:.1%} of awards, {sa_dol:.1%} of dollars; "
          f"register median ${reg_med:,.0f} mean ${reg_mean:,.0f}")
    for d in sorted(sas, key=lambda z: -z["n"])[:6]:
        print(f"      {d['k'][:26]:<28}n={d['n']:>7,} med ${d['med']:>9,.0f} "
              f"mean ${d['mean']:>10,.0f} top {d['top']:>5.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
