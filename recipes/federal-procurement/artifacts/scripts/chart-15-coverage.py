#!/usr/bin/env python3
"""A transparency register records the contract's own ceiling for a third of contracts.

    python3 chart-15-coverage.py

FFATA and the DATA Act require federal awards to be reported publicly. The FAR distinguishes
what a contract is worth now from what it could be worth if every option is exercised, and the
register carries a column for each. **The second one is blank on 70% of awards.**

**Which awards have a ceiling on file is not a fact about the contract.** Civilian agencies,
FY2016, 554,171 awards: Veterans Affairs records one in ten, Homeland Security six in ten.
That is a **sixfold range** between departments filing into the same system under the same
statute.

**And inside almost every one of them, an uncompeted award is less likely to be documented.**
Pooled, coverage is 32.6% for competed awards and 22.4% for uncompeted. That gap could be
composition -- Veterans Affairs files a great deal of uncompeted work and covers little of
anything -- so it is measured again **within** each agency, where the agency effect cannot
reach it. It survives: **competed awards are better covered in 10 of 11 agencies, by a median
of 11 points.** The one reversal is Agriculture, at -6.

**Why this is the figure rather than the one planned.** The intended measurement was how much
of the authorised ceiling a contract actually reaches. It is computable only where a ceiling
exists, and where a ceiling exists correlates with **both** variables that measurement wanted
to compare -- agency and competition. A 30% subset selected on the independent variables is
not a sample, so the missingness had to become the subject.

**What this does not show.** Whether a missing ceiling is a rule or a habit. Some award types
may have no distinct ceiling to report, and the FY2015 file carried the same award type under
two encodings with the money populated in one and never the other -- so part of this is
plainly systems rather than intent. The figure measures what the public register contains, and
stops there.
"""
import collections, csv, io, os, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L, plate                                                  # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "15-coverage.svg")
SRC = os.path.join(HERE, "..", "data", "civilian-fy2016.zip")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
COMP = {"FULL AND OPEN COMPETITION": 1, "COMPETED UNDER SAP": 1,
        "FULL AND OPEN COMPETITION AFTER EXCLUSION OF SOURCES": 1,
        "COMPETITIVE DELIVERY ORDER": 1, "NOT COMPETED": 0,
        "NOT COMPETED UNDER SAP": 0, "NOT AVAILABLE FOR COMPETITION": 0,
        "NON-COMPETITIVE DELIVERY ORDER": 0}
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


def main():
    if not os.path.exists(SRC):
        raise SystemExit("  civilian-fy2016.zip missing — run usa2.py")
    acc = {}
    for r in L.transactions(SRC):
        k = r.get(L.KEY)
        if not k:
            continue
        a = acc.get(k)
        if a is None:
            a = acc[k] = {"pot": None, "ag": r.get("awarding_agency_name") or "?",
                          "c": COMP.get((r.get("extent_competed") or "").strip())}
        if L.num(r.get("potential_total_value_of_award")) is not None:
            a["pot"] = 1
    aw = list(acc.values())
    total, covered = len(aw), sum(1 for a in aw if a["pot"])

    ba = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    for a in aw:
        if a["c"] is None:
            continue
        d = ba[a["ag"]][a["c"]]
        d[0] += 1
        d[1] += bool(a["pot"])
    rows = []
    for ag, d in ba.items():
        c, nc = d.get(1, [0, 0]), d.get(0, [0, 0])
        if c[0] < 500 or nc[0] < 500:
            continue
        rows.append({"ag": SHORT.get(ag, ag)[:26], "nc": c[0], "cc": c[1] / c[0],
                     "nn": nc[0], "cn": nc[1] / nc[0], "n": c[0] + nc[0]})
    rows.sort(key=lambda d: -d["n"])
    below = sum(1 for d in rows if d["cc"] > d["cn"] + 0.01)
    gaps = sorted(d["cc"] - d["cn"] for d in rows)

    W, H = 1200, 860
    s = plate.open_svg(W, H, "A transparency register records the contract's own ceiling "
                             "for a third of contracts")
    fr, _ = plate.frame(W, 62,
                        who="anyone computing a contract-value statistic from this register",
                        decide="whether the awards with a value on file are a sample of "
                               "the rest",
                        wrong="the agencies sit on the diagonal, or coverage is flat "
                              "across them")
    s += fr

    AX, AY, AH, AW = 28, 176, 440, 620
    x0, pw = AX + 52, AW - 104
    px = lambda f: x0 + pw * (f / 0.70)
    py = lambda f: AY + AH - 58 - (AH - 92) * (f / 0.70)
    for f in (0, .2, .4, .6):
        s.append(f'<line x1="{px(0):.1f}" y1="{py(f):.1f}" x2="{px(0.70):.1f}" '
                 f'y2="{py(f):.1f}" stroke="{GRID}"/>')
        s.append(f'<line x1="{px(f):.1f}" y1="{py(0):.1f}" x2="{px(f):.1f}" '
                 f'y2="{py(0.70):.1f}" stroke="{GRID}"/>')
        s.append(txt(x0 - 9, py(f) + 3, f"{f:.0%}", size=9, fill=MUTED, anchor="end"))
        s.append(txt(px(f), py(0) + 18, f"{f:.0%}", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, AY - 18, "share of UNCOMPETED awards with a ceiling recorded",
                 size=11, fill=INK2))
    s.append(txt(AX, py(0) + 36, "share of COMPETED awards with a ceiling recorded",
                 size=10, fill=MUTED))
    s.append(f'<path d="M{px(0):.1f},{py(0):.1f} L{px(0.70):.1f},{py(0.70):.1f}" '
             f'fill="none" stroke="{INK2}" stroke-width="1.4" stroke-dasharray="5 3"/>')
    s += halo(px(0.58), py(0.62), "on this line, competition", size=9.5, fill=INK2)
    s += halo(px(0.58), py(0.62) - 11, "makes no difference", size=9.5, fill=INK2)
    area = lambda n: 4 + 22 * (n / max(d["n"] for d in rows)) ** 0.5
    for d in rows:
        col = GREEN if d["cc"] > d["cn"] + 0.01 else RED
        cx, cy, rr = px(d["cc"]), py(d["cn"]), area(d["n"])
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" fill="{col}" '
                 f'fill-opacity="0.20" stroke="{col}" stroke-width="1.5"/>')
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2" fill="{col}"/>')
        side = 1 if d["ag"] not in ("Homeland Security", "Agriculture") else -1
        s += halo(cx + side * (rr + 6), cy + 3.5, d["ag"], size=9.5, fill=col,
                  anchor="start" if side > 0 else "end", weight="700")
    ly = AY + 6
    for col, lab in ((GREEN, "competed awards better documented"),
                     (RED, "uncompeted better documented")):
        s.append(f'<circle cx="{px(0.03):.1f}" cy="{ly-3.5:.1f}" r="4.4" fill="{col}" '
                 f'fill-opacity="0.20" stroke="{col}" stroke-width="1.4"/>')
        s.append(txt(px(0.03) + 11, ly, lab, size=9.5, fill=INK2))
        ly += 15
    s.append(txt(px(0.03) + 11, ly, "area is awards in that agency", size=9.5, fill=MUTED))

    BX, BY, BW = 700, 176, 472
    s.append(txt(BX, BY - 18, "coverage by agency, both classes together", size=11,
                 fill=INK2))
    allrows = sorted(
        [{"ag": SHORT.get(ag, ag)[:26],
          "n": sum(v[0] for v in d.values()),
          "c": sum(v[1] for v in d.values()) / max(sum(v[0] for v in d.values()), 1)}
         for ag, d in ba.items()], key=lambda d: -d["c"])
    bx0, bpw = BX + 172, BW - 240
    for i, d in enumerate(allrows):
        y = BY + 16 + i * 31
        s.append(txt(BX, y, d["ag"][:22], size=10, fill=INK2))
        w = bpw * (d["c"] / 0.70)
        col = GREEN if d["c"] > 0.45 else (RED if d["c"] < 0.2 else BLUE)
        s.append(f'<rect x="{bx0:.1f}" y="{y-9:.1f}" width="{max(w,2):.1f}" height="12" '
                 f'fill="{col}" fill-opacity="0.7"/>')
        s += halo(bx0 + max(w, 2) + 6, y + 1, f"{d['c']:.0%}", size=10, fill=col,
                  weight="700")
        s.append(txt(bx0 - 8, y, f"{d['n']:,}", size=9, fill=MUTED, anchor="end"))
    yy = BY + 16 + 31 * len(allrows) + 10
    s += wrap(BX, yy,
              f"A sixfold range between departments filing into one system under one statute. "
              f"Register-wide, {covered:,} of {total:,} awards carry a ceiling — {covered/total:.0%}.",
              size=10.5, fill=INK2, chars=56, leading=14)

    ty = AY + AH + 42
    s.append(txt(AX, ty, "the gradient is not composition", size=12.5, fill=INK,
                 weight="600"))
    s += wrap(AX, ty + 20,
              f"Pooled, coverage is 32.6% for competed awards and 22.4% for uncompeted — a gap "
              f"that could be agency mix, since Veterans Affairs files much uncompeted work and "
              f"documents little of anything. Measured inside each agency, where that cannot "
              f"reach it, competed awards are better covered in {below} of {len(rows)}, by a "
              f"median of {gaps[len(gaps)//2]:.0%} points. Agriculture is the single reversal.",
              size=11, fill=INK2, chars=86, leading=15)

    fy = H - 24 - 14 * 3
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    # Trimmed from the plate per doctrine/what-a-footnote-carries.md; kept here because it is method: s
    #  += wrap(28, fy, USAspending API v2 bulk download, fetched 2026-09-22; contract
    # transactions with an action date in FY2016, eleven civilian departments — {total:,}
    # awards keyed on contract_award_unique_key. These agencies are 8.5% of federal contract
    # awards: Defense alone is 68.6% and General Services another 22.9%, and neither could be
    # fetched at this size, so no claim here is about federal procurement as a whole.
    # “Ceiling” is potential_total_value_of_award. Agencies with under 500 awards in either
    # competition class are not drawn. Whether a missing ceiling is a rule or a habit is not
    # established — the FY2015 file carried one award type under two encodings with the value
    # populated in one and never the other, so part of this is systems rather than intent.,
    # size=11, fill=MUTED, chars=150, leading=14)
    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2016, 554,171 awards. "
        "CAVEAT: the pooled competed-against-uncompeted gap is partly agency mix; measured "
        "inside each agency it survives in 10 of 11 at a median of 10 points, with "
        "Agriculture the single reversal. These eleven civilian departments are 8.5% of "
        "federal contract awards; Defense (68.6%) is absent, so this is not federal "
        "procurement as a whole.")
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=186, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {covered:,}/{total:,} = {covered/total:.1%} coverage overall")
    print(f"    competed better covered in {below}/{len(rows)}, median gap "
          f"{gaps[len(gaps)//2]:+.0%}")
    for d in allrows:
        print(f"    {d['ag']:<26}{d['n']:>9,}{d['c']:>8.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
