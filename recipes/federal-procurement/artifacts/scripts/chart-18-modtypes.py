#!/usr/bin/env python3
"""What a modification does, and why counting modifications measures the wrong thing.

    python3 chart-18-modtypes.py

Questions 1 to 3 of this recipe -- how much do contracts grow after award, is growth the norm,
does competition predict it -- were abandoned when the money plan-versus-outcome pair turned
out to be 30% populated and missing not at random. `action_type` is a partial route back, and
it is a route back because of what it is rather than what it contains.

**The unit is the transaction, and that is the whole risk in this figure.** `action_type` is
FPDS's *Reason for Modification*. One award carries many actions of different kinds -- 54,420
awards take a funding action and 31,597 take a supplemental agreement, and the two sets
overlap heavily -- so there is no such thing as an award's action type. Folding it to the
award first-non-blank, the way this recipe correctly folds the bid count and the competition
authority, would silently pick whichever action happened to be filed first. Everything here is
counted per transaction, and the only award-level quantity is a sum of dollars.

**The 45.8% populated figure is not missingness.** The register's own spec makes the element
mandatory on modifications and has no code for a new award. Measured: 344,344 of 746,960 rows
carry it, and all 344,344 are modifications; 402,616 rows are base actions and **every one of
them is blank**. Two columns that are filed independently -- `modification_number` and
`action_type` -- partition the file identically, with zero disagreements. So the field is 100%
populated where it is defined, which is a different object from a column that is 46% there.

**What it says.** $75.66bn of FY2016's $125.75bn -- 60.2% -- arrives on a modification rather
than on a base action. Of that, 87.7% is a funding action or an exercised option: money moving
against work that was agreed and priced at award. 11.2% is a negotiated change to the
agreement, and the part of it the register labels a change order or additional work is 2.6%.
Meanwhile 41.3% of the modification *paperwork* is closeouts and administrative actions
carrying 1.1% of the money. **"Contracts grow" and "contracts get re-scoped" are different
numbers and this column separates them.**

**What it cannot do.** The file is filtered on action date, so an award's base action can sit
in FY2015 and its later modifications in FY2017. Award-level growth ratios are censored at
both ends and are not drawn: on the 71,848 awards that have both a base row and a
modification here and a positive base, 26,851 grew, 27,987 shrank, the median ratio is 1.00
and the maximum is 2.5 billion. The transaction-level split above has no such problem -- it is
an exact statement about which FY2016 dollars arrived on which kind of action.

**The two method points that used to sit in the footnote.** Dollars are
`federal_action_obligation` summed with de-obligations kept, because 13.17% of transactions
carry a negative one and dropping them overstates the total; that is why close out, the
terminations and the pooled tail sit left of zero, and the plate says so in the subtitle
rather than at the bottom of the page. And both fields here are read from their **code**
column and never their label: FPDS relabelled mid-year, so `action_type` A carries two
spellings in this file and seventeen of the eighteen competition authorities carry two --
grouping on the printed label would split eighteen authorities into thirty-five.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import modauth as MA, plate                                              # noqa: E402
from plate import (txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT,  # noqa: E402
                   SURFACE)

OUT = os.path.join(HERE, "..", "charts", "18-modtypes.svg")
AGREED, CHANGE, ADMIN = "#1b6a9c", "#c07a1e", "#6f7276"

SHORT = {"Department of Veterans Affairs": "Veterans Affairs",
         "Department of Justice": "Justice",
         "Department of Health and Human Services": "Health & Human Services",
         "Department of Homeland Security": "Homeland Security",
         "Department of Agriculture": "Agriculture",
         "Department of the Interior": "Interior",
         "Department of Commerce": "Commerce",
         "Department of Transportation": "Transportation",
         "Department of Energy": "Energy",
         "National Aeronautics and Space Administration": "NASA",
         "Environmental Protection Agency": "EPA"}

# The rows, in three groups. Each entry is (codes, the register's own wording shortened to fit
# the label column). Codes are pooled only where both measures are under a per cent; the
# pooled row says how many kinds it holds so the reader can see nothing large is hiding.
GROUPS = [
    ("money against work already agreed and priced", AGREED,
     [(["C"], "funding only action"),
      (["G"], "exercise an option")]),
    ("a negotiated change to the agreement", CHANGE,
     [(["B"], "supplemental agreement for work within scope"),
      (["D"], "change order"),
      (["A"], "additional work: new agreement, FAR part 6 applies"),
      (["L", "H"], "definitize a change order or a letter contract")]),
    ("administrative, closing and terminating", ADMIN,
     [(["M"], "other administrative action"),
      (["K"], "close out"),
      (["F"], "terminate for convenience"),
      (["N", "V", "J", "S", "X", "W", "E", "R", "T", "P"],
       "ten other kinds: novation, cancellation, PIID change")]),
]
# Where each department's name sits relative to its mark in the lower panel. Hand-placed
# after looking at the render at 1.6x: Health & Human Services and Homeland Security sit
# within a mark's width of each other and every automatic rule collided one of them.
BPOS = {"Energy": ("R", 0, 0), "Health & Human Services": ("A", 0, 0),
        "NASA": ("A", 0, 0), "Homeland Security": ("A", -18, 0),
        "Transportation": ("R", 0, 0), "Veterans Affairs": ("B", 0, 0),
        "Justice": ("L", 0, 0), "Interior": ("A", 0, 0),
        "Commerce": ("L", 0, 0), "Agriculture": ("L", 0, 0), "EPA": ("L", 0, 0)}


def nlines(text, chars):
    """How many lines plate.wrap will produce -- the plate is sized from this."""
    n, line = 1, []
    for w in str(text).split():
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            n, line = n + 1, []
        line.append(w)
    return n


def money(v):
    """ASCII only: a leading hyphen-minus, never U+2212."""
    s = "-" if v < 0 else ""
    a = abs(v)
    if a >= 1e9:
        return f"{s}${a/1e9:.1f}bn"
    if a >= 1e6:
        return f"{s}${a/1e6:.0f}m"
    return f"{s}${a/1e3:.0f}k"


def main():
    d = MA.load()
    act = d["action"]
    base = act["-blank-"]
    mods = {k: v for k, v in act.items() if k != "-blank-"}
    n_mod = sum(v["n"] for v in mods.values())
    post = sum(v["obl"] for v in mods.values())
    total = post + base["obl"]
    neg_tx = sum(v["n_neg"] for v in act.values())

    # ---- rows, with the group totals drawn on the same axis as their members -------------
    rows = []
    for gname, col, members in GROUPS:
        gn = sum(mods[c]["n"] for cs, _ in members for c in cs)
        gv = sum(mods[c]["obl"] for cs, _ in members for c in cs)
        rows.append({"head": True, "lab": gname, "col": col, "n": gn, "v": gv,
                     "code": ""})
        for cs, lab in members:
            rows.append({"head": False, "lab": lab, "col": col,
                         "n": sum(mods[c]["n"] for c in cs),
                         "v": sum(mods[c]["obl"] for c in cs),
                         "code": "+".join(cs) if len(cs) < 3 else f"{len(cs)} codes"})
    agreed = next(r for r in rows if r["head"] and r["col"] == AGREED)
    change = next(r for r in rows if r["head"] and r["col"] == CHANGE)
    admin = next(r for r in rows if r["head"] and r["col"] == ADMIN)
    rescope = sum(mods[c]["obl"] for c in ("D", "A", "L"))

    # ---- the departments, which is the falsifier ----------------------------------------
    deps = []
    for name, s in d["dept"].items():
        p = sum(v[1] for c, v in s.items() if c != "-base-")
        if abs(p) < 1e7:
            continue
        deps.append({"ag": SHORT.get(name, name[:24]), "post": p,
                     "plan": sum(v[1] for c, v in s.items() if c in MA.PLANNED_AT) / p,
                     "chg": sum(v[1] for c, v in s.items() if c in MA.SCOPED_AT) / p,
                     "tx": sum(v[0] for c, v in s.items() if c != "-base-")})
    deps.sort(key=lambda x: -x["post"])
    lo1 = min((change["v"] - x["chg"] * x["post"]) / (post - x["post"]) for x in deps)
    hi1 = max((change["v"] - x["chg"] * x["post"]) / (post - x["post"]) for x in deps)

    # ------------------------------------------------------------------------- drawing
    # Source, the two caveats that would make a reader wrong, and the population. Everything
    # else that used to sit here -- how the unit was chosen, the de-obligation handling, the
    # growth-ratio censoring arithmetic, the code-versus-label rule -- is method and lives in
    # the docstring. See doctrine/what-a-footnote-carries.md.
    foot = (f"USAspending API v2 bulk download, fetched 2026-09-22; FY2016 contract "
            f"transactions, {d['awards']:,} awards, {money(total)} net. "
            f"The upper panel's unit is the TRANSACTION, not the award: one award carries "
            f"several kinds of action at once. Per-award growth is NOT recoverable from this "
            f"file, which is filtered on action date, so an award's base and its later "
            f"modifications fall in different years. These eleven civilian departments are "
            f"8.5% of federal contract awards; Defense (68.6%) is absent.")

    W = 1200
    # The plot has to stop at 1108 rather than the usual 1172: the group mark for "already
    # agreed" sits at 87.7%, and its value label needs the last 60px of the plate.
    LX, CDX, PX, PW = 28, 88, 420, 688           # code, label, plot left, plot width
    ROW, HEADGAP = 29, 13
    xlo, xhi = -0.045, 0.90
    px = lambda v: PX + PW * (v - xlo) / (xhi - xlo)

    AH = 168                                      # panel A heading baseline
    AY = AH + 76                                  # first row centre
    ah = sum(ROW + (HEADGAP if r["head"] else 0) for r in rows)
    ABOT = AY + ah - ROW / 2 + 6

    BH = ABOT + 96                                # panel B heading baseline
    BX, BY, BW, BHT = 150, BH + 52, 880, 218
    FY = BY + BHT + 104
    H = FY + 14 * nlines(foot, 150) + 22

    s = plate.open_svg(W, H, "Three fifths of the money arrives on a modification, and 88% "
                             "of that changes nothing that was agreed")
    fr, _ = plate.frame(W, 62,
                        who="anyone quoting a post-award growth or scope-creep number from "
                            "this register, or screening contracts by how many times they "
                            "were modified",
                        decide="whether growth means new money on agreed work or a change to "
                               "the work, and which of the twenty action codes to count",
                        wrong="the change order and additional work rows carry a large share "
                              "of the dollars, or one department makes the split -- the "
                              "lower panel is that test")
    s += fr

    # ---- panel A: one row per action code, two positions on one axis ---------------------
    s.append(txt(LX, AH, "the money and the paperwork rank a modification almost oppositely",
                 size=12.5, fill=INK, weight="600"))
    # The de-obligation fact is context a reader needs to read the marks, so it goes here, in
    # place, rather than in the footnote: without it a bar left of zero looks like an error.
    s.append(txt(LX, AH + 18, f"{n_mod:,} modification transactions carrying {money(post)} "
                              f"net, against {base['n']:,} base actions carrying "
                              f"{money(base['obl'])}; de-obligations are kept, so a kind "
                              f"that gives back more than it obligates sits left of zero",
                 size=10, fill=MUTED))
    s.append(txt(LX, AH + 40, "share of the modification transactions (hollow) and share of "
                              "the dollars they obligate (filled)", size=10.5, fill=INK2))

    lx = px(0.60)
    s.append(f'<circle cx="{lx:.1f}" cy="{AH+36:.1f}" r="5.2" fill="{SURFACE}" '
             f'stroke="{INK2}" stroke-width="1.8"/>')
    s.append(txt(lx + 10, AH + 40, "one action", size=9.5, fill=MUTED))
    s.append(f'<circle cx="{lx+80:.1f}" cy="{AH+36:.1f}" r="5.2" fill="{INK2}"/>')
    s.append(txt(lx + 90, AH + 40, "one dollar", size=9.5, fill=MUTED))

    for v, lab in ((0.0, "0%"), (0.1, "10%"), (0.2, "20%"), (0.3, "30%"), (0.4, "40%"),
                   (0.5, "50%"), (0.6, "60%"), (0.7, "70%"), (0.8, "80%"), (0.9, "90%")):
        s.append(f'<line x1="{px(v):.1f}" y1="{AY-20:.1f}" x2="{px(v):.1f}" '
                 f'y2="{ABOT:.1f}" stroke="{GRID if v else RULE}"/>')
        s.append(txt(px(v), ABOT + 17, lab, size=9, fill=MUTED, anchor="middle"))
    s.append(txt(PX, ABOT + 36, "share of the modification transactions, and share of the "
                                "net dollars they obligate", size=10.5, fill=MUTED))

    y = AY
    for r in rows:
        if r["head"]:
            y += HEADGAP
        fn, fv = r["n"] / n_mod, r["v"] / post
        xa, xb = px(fn), px(fv)
        rad = 6.4 if r["head"] else 4.6
        s.append(f'<line x1="{xa:.1f}" y1="{y:.1f}" x2="{xb:.1f}" y2="{y:.1f}" '
                 f'stroke="{r["col"]}" stroke-width="{3.2 if r["head"] else 2.0}" '
                 f'stroke-opacity="0.55"/>')
        s.append(f'<circle cx="{xa:.1f}" cy="{y:.1f}" r="{rad:.1f}" fill="{SURFACE}" '
                 f'stroke="{r["col"]}" stroke-width="{2.2 if r["head"] else 1.7}"/>')
        s.append(f'<circle cx="{xb:.1f}" cy="{y:.1f}" r="{rad:.1f}" fill="{r["col"]}"/>')
        s.extend(halo(max(xa, xb) + rad + 8, y + 3.5, money(r["v"]),
                      size=10.5 if r["head"] else 9.5, fill=r["col"],
                      weight="700" if r["head"] else "600"))
        s.append(txt(LX if r["head"] else CDX, y + 3.5, r["lab"],
                     size=11.5 if r["head"] else 10.5,
                     fill=INK if r["head"] else INK2,
                     weight="600" if r["head"] else "normal"))
        s.append(txt(PX - 16, y + 3.5, f"{r['n']:,}", size=9.5,
                     fill=r["col"] if r["head"] else MUTED, anchor="end",
                     weight="700" if r["head"] else "normal"))
        if r["code"]:
            s.append(txt(LX, y + 3.5, r["code"], size=9, fill=FAINT))
        y += ROW
    s.append(txt(PX - 16, AY - 24, "actions", size=9, fill=MUTED, anchor="end"))

    # ---- panel B: the same split, one mark per department -------------------------------
    import math
    s.append(txt(LX, BH, "no one department makes the pooled number, and yet the change "
                         "share runs 2% to 28%", size=12.5, fill=INK, weight="600"))
    s.append(txt(LX, BH + 18, "one mark per department, area is its modification "
                              "transactions; Energy alone is 36.7% of the post-award "
                              "dollars and the smallest mark on the page",
                 size=10, fill=MUTED))
    s.append(txt(LX, BH + 40, "the department's post-award dollars", size=10.5, fill=INK2))

    bxlo, bxhi = 0.0, 0.305
    bylo, byhi = math.log10(0.7e9), math.log10(4e10)
    qx = lambda v: BX + BW * (v - bxlo) / (bxhi - bxlo)
    qy = lambda v: BY + BHT - BHT * (math.log10(v) - bylo) / (byhi - bylo)
    for v, lab in ((0.0, "0%"), (0.05, "5%"), (0.1, "10%"), (0.15, "15%"), (0.2, "20%"),
                   (0.25, "25%"), (0.3, "30%")):
        s.append(f'<line x1="{qx(v):.1f}" y1="{BY:.1f}" x2="{qx(v):.1f}" '
                 f'y2="{BY+BHT:.1f}" stroke="{GRID}"/>')
        s.append(txt(qx(v), BY + BHT + 17, lab, size=9, fill=MUTED, anchor="middle"))
    for v, lab in ((1e9, "$1bn"), (3e9, "$3bn"), (1e10, "$10bn"), (3e10, "$30bn")):
        s.append(f'<line x1="{BX:.1f}" y1="{qy(v):.1f}" x2="{BX+BW:.1f}" '
                 f'y2="{qy(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(BX - 9, qy(v) + 3, lab, size=9, fill=MUTED, anchor="end"))
    s.append(txt(BX, BY + BHT + 36, "share of that department's post-award dollars that is a "
                                    "negotiated change to the agreement", size=10.5,
                 fill=MUTED))

    gp = change["v"] / post
    s.append(f'<line x1="{qx(gp):.1f}" y1="{BY-8:.1f}" x2="{qx(gp):.1f}" '
             f'y2="{BY+BHT:.1f}" stroke="{CHANGE}" stroke-width="1.5" '
             f'stroke-dasharray="5 4"/>')
    s.extend(halo(qx(gp) + 7, BY - 12, f"all eleven pooled, {gp:.1%}", size=9.5, fill=CHANGE,
                  weight="700"))
    s.extend(halo(qx(gp) + 7, BY - 1, f"leaving any one out: {lo1:.1%} to {hi1:.1%}",
                  size=9.5, fill=MUTED))

    big = max(x["tx"] for x in deps)
    for x in deps:
        r = 4.5 + 20 * (x["tx"] / big) ** 0.5
        cx, cy = qx(x["chg"]), qy(x["post"])
        col = CHANGE if x["chg"] > gp else AGREED
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{col}" '
                 f'fill-opacity="0.18" stroke="{col}" stroke-width="1.5"/>')
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2" fill="{col}"/>')
        code, ex, ey = BPOS.get(x["ag"], ("R", 0, 0))
        dx, dy, an = {"L": (-(r + 7), 3.5, "end"), "R": (r + 7, 3.5, "start"),
                      "B": (0, r + 14, "middle"), "A": (0, -(r + 9), "middle")}[code]
        s.extend(halo(cx + dx + ex, cy + dy + ey, x["ag"], size=9.5, fill=col, anchor=an,
                      weight="700"))

    fy = FY
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" '
             f'stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {d['tx']:,} transactions, {d['awards']:,} awards, {money(total)} net")
    print(f"    modifications {n_mod:,} = {n_mod/d['tx']:.2%} of rows, carrying "
          f"{money(post)} = {post/total:.2%} of the money")
    print(f"    action_type on base rows {sum(v['on_base'] for v in mods.values())}, "
          f"on modification rows {sum(v['on_mod'] for v in mods.values()):,}")
    print(f"    negative transactions {neg_tx:,} = {neg_tx/d['tx']:.2%}, kept")
    print(f"    footnote {len(foot):,} characters (limit 500)")
    for r in rows:
        mark = "  " if r["head"] else "    "
        print(f"  {mark}{r['lab'][:52]:<54}{r['n']:>9,}{r['n']/n_mod:>8.2%}"
              f"{money(r['v']):>10}{r['v']/post:>8.2%}")
    print(f"    change order + additional work + definitize: {money(rescope)} = "
          f"{rescope/post:.2%} of post-award dollars")
    print(f"    department negotiated-change share {min(x['chg'] for x in deps):.1%} to "
          f"{max(x['chg'] for x in deps):.1%}, pooled {gp:.1%}, "
          f"leave-one-out {lo1:.1%} to {hi1:.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
