#!/usr/bin/env python3
"""Frequency and size are different rankings, and competition explains neither.

    python3 chart-17-holders.py

Figure 16 draws the shape of option time. This one asks who carries it, and tests the
explanation a reader reaches for first.

**How often a group holds option time and how much it holds are different rankings.**
Veterans Affairs carries some on 31.2% of its awards at a median of 63 days; Health and Human
Services on 10.3% at 661 days. By award type, definitive contracts are 28.8% at 730 days and
purchase orders 15.2% at 61.

**Competition does not explain it, and that is a measured null rather than an absence.**
Inside a department, competed awards carry option time more often in 8 of 11, by a median of
1.1 points, against 95% intervals about half a point wide -- so a three-point effect could not
have hidden. FY2015 independently gives 8 of 11 and 1.2 points. The same within-department
control moves money-ceiling *coverage* by a median of 11 points, which is what a real effect
looks like on this data.

That null is only worth stating because coverage here is ~100%. On the money columns the same
test would be measuring who files, not who competes.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate, sched                                                      # noqa: E402
from sched import load_year, nlines, step, CAP, SHORT, ATYPE             # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402
RED, AMBER, GREEN, BLUE, PLUM = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#6b4a80"

OUT = os.path.join(HERE, "..", "charts", "17-holders.svg")


def main():
    a = load_year("2016")
    b = load_year("2015")
    up = sum(1 for d in a["cmp"] if d["d"] > 0)
    med = sorted(d["d"] for d in a["cmp"])[len(a["cmp"]) // 2]

    W, H = 1240, 680
    s = plate.open_svg(
        W, H,
        "Frequency and size are different rankings, and competition explains neither",
        subtitle=f"Who carries the option time that figure 16 measures. Coverage on both "
                 f"schedule dates is {a['both']/a['awards']:.3%}, so the competition null "
                 f"below is a measured null and not a gap in the filing.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone ranking agencies on unexercised authority, or about to explain it "
            "with competition",
        decide="whether to rank a group on how often it holds option time or on how much",
        wrong="the two rankings agree, or the competition intervals clear zero in one "
              "direction")
    s += fr

    # ---------------------------------------------------------------- C: who holds it
    CX, CY, CW, CH = 28, y0 + 70, 600, 300
    cx = lambda f: CX + 56 + (CW - 96) * (f / 0.34)
    cy = lambda d: CY + CH - 24 - (CH - 54) * (math.log10(max(d, 40) / 40) / math.log10(20))
    for f in (0, .1, .2, .3):
        s.append(f'<line x1="{cx(f):.1f}" y1="{cy(40):.1f}" x2="{cx(f):.1f}" '
                 f'y2="{cy(800):.1f}" stroke="{GRID}"/>')
        s.append(txt(cx(f), cy(40) + 16, f"{f:.0%}", size=9, fill=MUTED, anchor="middle"))
    for d in (60, 120, 365, 730):
        s.append(f'<line x1="{cx(0):.1f}" y1="{cy(d):.1f}" x2="{cx(0.34):.1f}" '
                 f'y2="{cy(d):.1f}" stroke="{GRID}"/>')
        s.append(txt(cx(0) - 8, cy(d) + 3, f"{d:,}", size=9, fill=MUTED, anchor="end"))
    va = [d for d in a["ag"] if "Veterans" in d["k"]][0]
    hh = [d for d in a["ag"] if "Health" in d["k"]][0]
    s.append(txt(CX, CY - 24, "median gap in days where a gap exists (log)", size=11.5,
                 fill=INK2))
    s.append(txt(CX, CY - 9,
                 f"how often a group has option time against how much: Veterans Affairs "
                 f"{va['any']:.0%} of awards at {va['med']} days, Health and Human Services "
                 f"{hh['any']:.0%} at {hh['med']}", size=10, fill=MUTED))
    s.append(txt(cx(0), cy(40) + 32, "share of that group's awards with any option time",
                 size=10, fill=MUTED))
    big = max([d["n"] for d in a["ag"]] + [d["n"] for d in a["aty"]])
    ar = lambda n: 3.6 + 13 * (n / big) ** 0.5
    # Hand-placed: fifteen marks in one plane collide, and three of them (Homeland
    # Security, a BPA call, Interior) sit almost on top of each other. 0 is above the
    # mark, 2 is below it.
    PLACE = {"Veterans Affairs": (-1, 4), "Justice": (0, 0), "Health & Human Svcs": (1, 4),
             "Homeland Security": (-1, 5), "Agriculture": (-1, 4), "Interior": (-1, -3),
             "Commerce": (1, 4), "Transportation": (-1, 4), "NASA": (-1, 4),
             "EPA": (1, 3), "Energy": (1, 4), "delivery order": (0, 0),
             "purchase order": (1, 4), "BPA call": (1, 4), "definitive contract": (2, 0)}
    for kind, items, col in (("c", a["ag"], BLUE), ("s", a["aty"], AMBER)):
        for d in items:
            k = SHORT.get(d["k"], ATYPE.get(d["k"], d["k"]))
            X, Y, R = cx(d["any"]), cy(d["med"]), ar(d["n"])
            if kind == "c":
                s.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="{R:.1f}" fill="{col}" '
                         f'fill-opacity="0.17" stroke="{col}" stroke-width="1.4"/>')
            else:
                h = R * 0.886
                s.append(f'<rect x="{X-h:.1f}" y="{Y-h:.1f}" width="{2*h:.1f}" '
                         f'height="{2*h:.1f}" fill="{col}" fill-opacity="0.15" '
                         f'stroke="{col}" stroke-width="1.4"/>')
            s.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="1.7" fill="{col}"/>')
            sx, dy = PLACE.get(k, (1, 4))
            if sx in (0, 2):
                off = (-R - 7) if sx == 0 else (R + 13)
                s += halo(X, Y + off + dy, k, size=9.5, fill=col, anchor="middle",
                          weight="700")
            else:
                s += halo(X + sx * (R + 5), Y + dy, k, size=9.5, fill=col,
                          anchor="start" if sx > 0 else "end", weight="700")
    ly2 = CY + 16          # clear of the panel subtitle above it
    for col, lab, sq in ((BLUE, "one department", False), (AMBER, "one award type", True)):
        if sq:
            s.append(f'<rect x="{cx(0.004)-4:.1f}" y="{ly2-8:.1f}" width="8" height="8" '
                     f'fill="{col}" fill-opacity="0.15" stroke="{col}" stroke-width="1.3"/>')
        else:
            s.append(f'<circle cx="{cx(0.004):.1f}" cy="{ly2-4:.1f}" r="4.2" fill="{col}" '
                     f'fill-opacity="0.17" stroke="{col}" stroke-width="1.3"/>')
        s.append(txt(cx(0.004) + 10, ly2, lab, size=9.5, fill=INK2))
        ly2 += 14
    s.append(txt(cx(0.004) + 10, ly2, "area is awards in the group", size=9.5, fill=MUTED))
    s += halo(cx(0.235), cy(150) - 13, "frequency and size are", size=10, fill=INK2)
    s += halo(cx(0.235), cy(150), "different rankings", size=10, fill=INK2)

    # ---------------------------------------------------------------- D: the control
    DX, DY, DW = 668, CY - 24, 544
    s.append(txt(DX, DY, "competition does not explain it, and that is a measured null",
                 size=12.5, fill=INK, weight="600"))
    dd = a["cmp"]
    dx = lambda v: DX + 196 + (DW - 262) * ((v + 4) / 8)
    dy0 = DY + 26
    for v in (-4, -2, 0, 2, 4):
        s.append(f'<line x1="{dx(v):.1f}" y1="{dy0-6:.1f}" x2="{dx(v):.1f}" '
                 f'y2="{dy0+len(dd)*15-4:.1f}" stroke="{GRID if v else RULE}"/>')
        s.append(txt(dx(v), dy0 - 11, f"{v:+d}" if v else "0", size=9, fill=MUTED,
                     anchor="middle"))
    for i, d in enumerate(dd):
        y = dy0 + i * 15 + 4
        s.append(txt(DX, y, d["k"][:22], size=9.5, fill=INK2))
        s.append(txt(DX + 188, y, f"{d['nc']+d['nn']:,}", size=8.5, fill=MUTED,
                     anchor="end"))
        col = GREEN if d["d"] > 0 else RED
        s.append(f'<line x1="{dx(0):.1f}" y1="{y-3.5:.1f}" x2="{dx(d["d"]):.1f}" '
                 f'y2="{y-3.5:.1f}" stroke="{col}" stroke-width="2.4"/>')
        s.append(f'<line x1="{dx(d["d"]-d["ci"]):.1f}" y1="{y-3.5:.1f}" '
                 f'x2="{dx(d["d"]+d["ci"]):.1f}" y2="{y-3.5:.1f}" stroke="{col}" '
                 f'stroke-width="0.9"/>')
        s.append(f'<circle cx="{dx(d["d"]):.1f}" cy="{y-3.5:.1f}" r="2.6" fill="{col}"/>')
    yy = dy0 + len(dd) * 15 + 16
    s.append(txt(DX, yy, "percentage points, competed minus uncompeted, inside one "
                         "department", size=9.5, fill=MUTED))
    s += wrap(DX, yy + 20,
              f"Competed awards carry option time more often in {up} of {len(dd)} "
              f"departments, by a median of {med:.1f} points, from {min(d['d'] for d in dd):.1f} "
              f"to {max(d['d'] for d in dd):+.1f}; the hairline is the 95% interval, about half "
              f"a point wide, so a three-point effect could not have hidden here. The same "
              f"control on the same awards moves money-ceiling coverage by a median of 11 "
              f"points. FY2015 gives {sum(1 for d in b['cmp'] if d['d']>0)} of "
              f"{len(b['cmp'])} and {sorted(d['d'] for d in b['cmp'])[len(b['cmp'])//2]:.1f} "
              f"points.",
              size=10.5, fill=INK2, chars=80, leading=14)


    # ---------------------------------------------------------------- footer
    # Trimmed from the plate per doctrine/what-a-footnote-carries.md; kept here because it is method: f
    # oot = (USAspending API v2 bulk download, fetched 2026-09-22; contract transactions with
    # an action date in FY2016, eleven civilian departments, collapsed to {a['awards']:,}
    # awards on contract_award_unique_key, with FY2015 ({b['awards']:,} awards) as the
    # replication. Shares are of the group's own awards. The competition control is computed
    # inside each department and only where the department has at least 500 awards in each
    # arm, so it is not reading the mix of departments; the hairline is a 95% interval on the
    # difference. Award types below 5,000 awards are not drawn. Dates are the maximum seen
    # across an award's transactions. These eleven departments are 8.5% of federal contract
    # awards — Defense is 68.6% and General Services 22.9%, and neither could be fetched at
    # this size, so nothing here is a claim about federal procurement as a whole. The shape of
    # the quantity is figure 16.) ln = nlines(foot, 170) fy = H - 20 - 14 * ln s.append(f'<line
    # x1=28 y1={fy-18:.1f} x2={W-28} y2={fy-18:.1f} stroke={RULE}/>') s += wrap(28, fy, foot,
    # size=10.5, fill=MUTED, chars=170, leading=14)
    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2016 with FY2015 as the "
        "replication. Shares are of the group's own awards. CAVEAT: the competition control "
        "is computed inside each department, so it is not reading the mix of departments; "
        "the hairline is a 95% interval. These eleven civilian departments are 8.5% of "
        "federal contract awards; Defense (68.6%) is absent, so this is not federal "
        "procurement as a whole.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=170, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=170, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    competed higher in {up}/{len(dd)}, median {med:+.1f} pt")
    print(f"    footnote {len(foot)} chars over {ln} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
