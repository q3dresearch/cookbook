#!/usr/bin/env python3
"""BIDS errors fell from 62% of datasets to nearly none, and then the checking stopped.

    python3 chart-3-validity.py

OpenNeuro runs the BIDS validator over every deposit and publishes the result as an error and
warning count. Two series come out of it, and they move in opposite directions.

**The archive got clean.** Among datasets whose validation result is published, the share
carrying at least one error falls from **62% in 2016-2018 to 18% by 2020, 4% by 2021 and 0-1%
from 2022**. That is a real improvement in a standard's adoption, and it is the kind of thing
a standard is for.

**And then it stopped being recorded.** The share of deposits with any published validation
status falls from **100% before 2019 to 81% in 2023, 63% in 2024, 7% in 2025 and 1% in 2026**.
819 of 1,891 datasets carry no validation result at all, and almost all of them are recent.

**Which means the clean-looking recent years are not evidence of anything.** A 0% error rate
computed on 7% of 2025's deposits is a statement about twenty-one datasets. The archive may
still be clean; this file cannot say so, and a reader who takes the falling error line at face
value across the whole span will believe something the coverage line refutes.

**Why the two lines must be on one plate.** Either alone is misleading in the opposite
direction: the error line alone says the problem is solved, the coverage line alone says the
archive is unaudited. Together they say the problem *was* solved and the audit then went dark,
which is a different and more useful statement.

**Validated datasets that do carry errors are downloaded less** -- a median 8.8 a year against
13.5 for clean ones, about a third lower. That is a correlation on 177 datasets and nothing
here establishes that the errors caused it; a dataset with validator errors may simply be
older, and error rates and age move together on this plate.
"""
import collections, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fold, plate                                                       # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "3-validity.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
MIN_N = 8                       # a share on fewer than this is not drawn as a point


def main():
    rows = fold.load()["rows"]
    for r in rows:
        r["yr"] = int(r["pub"][:4])
    years = sorted({r["yr"] for r in rows})
    series = []
    for y in years:
        g = [r for r in rows if r["yr"] == y]
        v = [r for r in g if r["errors"] is not None]
        e = [r for r in v if r["errors"] > 0]
        series.append({"y": y, "n": len(g), "nv": len(v),
                       "cover": len(v) / len(g) if g else None,
                       "err": (len(e) / len(v)) if len(v) >= MIN_N else None,
                       "err_n": len(e)})
    val = [r for r in rows if r["errors"] is not None]
    bad = [r for r in val if r["errors"] > 0 and r["dl_yr"] is not None]
    ok = [r for r in val if r["errors"] == 0 and r["dl_yr"] is not None]

    W, H = 1180, 860
    s = plate.open_svg(
        W, H, "BIDS errors fell from 62% of datasets to nearly none, and then the checking "
              "stopped",
        subtitle=f"{len(rows):,} OpenNeuro datasets by publication year. One line is how many "
                 f"were checked. The other is how many of the checked ones failed. They move "
                 f"opposite ways.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone treating a public archive's validator status as evidence the data is "
            "usable, or a repository deciding what to re-run",
        decide="whether the recent half of this archive can be audited at all",
        wrong="coverage holds up in recent years, so the falling error rate means what it "
              "appears to")
    s += fr

    AX, AY, AW, AH = 250, y0 + 14, W - 560, 560
    px = lambda i: AX + AW * i / (len(years) - 1)
    ay = lambda v: AY + AH - 40 - (AH - 66) * v

    for i, y in enumerate(years):
        s.append(f'<line x1="{px(i):.1f}" y1="{ay(1.0):.1f}" x2="{px(i):.1f}" '
                 f'y2="{ay(0):.1f}" stroke="{GRID}"/>')
        s.append(txt(px(i), ay(0) + 17, str(y), size=9, fill=MUTED, anchor="middle"))
        s.append(txt(px(i), ay(0) + 31, f"{series[i]['n']}", size=8.5, fill=FAINT,
                     anchor="middle"))
    for v in (0, .25, .5, .75, 1.0):
        s.append(f'<line x1="{AX:.1f}" y1="{ay(v):.1f}" x2="{AX+AW:.1f}" '
                 f'y2="{ay(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(AX - 8, ay(v) + 3, f"{v*100:.0f}%", size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, ay(0) + 46, "publication year, with the number of deposits beneath",
                 size=10, fill=INK2))

    # anchor each label where the two lines are furthest apart, not at the crowded right end
    for key, col, lab, at, dy in (
            ("cover", BLUE, "had their validation result published", 2021, -13),
            ("err", RED, "of those checked, carried at least one error", 2019, 20)):
        pts = [(i, d[key]) for i, d in enumerate(series) if d[key] is not None]
        s.append('<polyline points="' + " ".join(f"{px(i):.1f},{ay(v):.1f}"
                                                 for i, v in pts) +
                 f'" fill="none" stroke="{col}" stroke-width="2.6"/>')
        for i, v in pts:
            s.append(f'<circle cx="{px(i):.1f}" cy="{ay(v):.1f}" r="3.4" fill="{col}"/>')
        li = years.index(at)
        lv = dict(pts)[li]
        s += halo(px(li) + 7, ay(lv) + dy, lab, size=9.5, fill=col, weight="700")

    # the years where the error rate rests on too few checked datasets to mean anything
    thin = [i for i, d in enumerate(series) if d["nv"] < 30 and d["n"] > 50]
    if thin:
        a, b = min(thin), max(thin)
        s.append(f'<rect x="{px(a)-14:.1f}" y="{ay(1.0):.1f}" '
                 f'width="{px(b)-px(a)+28:.1f}" height="{ay(0)-ay(1.0):.1f}" '
                 f'fill="{AMBER}" fill-opacity="0.07" stroke="{AMBER}" '
                 f'stroke-width="1" stroke-dasharray="3 3"/>')
        s += halo(px(a) - 8, ay(1.0) - 8, f"{series[a]['nv']} and {series[b]['nv']} datasets "
                  f"checked out of {series[a]['n']} and {series[b]['n']}", size=9.5,
                  fill=AMBER, anchor="end", weight="700")

    TX, ty = W - 240, AY + 20
    for head, body, col in (
            ("if you are picking a dataset",
             "From 2025 the archive gives you no quality signal at all. A recent dataset "
             "with no error count has not passed -- it has not been checked. Budget for "
             "running the validator yourself before you build on it.", RED),
            ("if you are running the repository",
             f"The backlog is {len(rows)-len(val):,} datasets and it is almost entirely "
             f"recent, so it is a re-run job and not a data-quality job. Clearing it is the "
             f"only thing that makes the last two years auditable.", BLUE),
            ("if you are citing a breakage rate",
             "\"17% of public datasets carry errors\" is true only of deposits made before "
             "2021, because those are the ones that were checked. Quoting it as a current "
             "figure inverts what this plate says.", AMBER),
            ("when this plate fails you",
             "It cannot tell an unrun validator from an unrecorded result, and those imply "
             "opposite repair work. If OpenNeuro's changelog says the field moved, the blue "
             "line is a schema change and the backlog is not real.", MUTED),
            ("the correlation is not an argument",
             f"Checked datasets with errors get "
             f"{statistics.median(x['dl_yr'] for x in bad):,.1f} downloads a year against "
             f"{statistics.median(x['dl_yr'] for x in ok):,.1f} for clean ones. Errors and "
             f"age move together on this very plate, so do not read it as a penalty for "
             f"being broken.", SLATE)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        w = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=32, leading=12.5)
        s += w
        ty += 12.5 * len(w) + 16

    foot = (
        "OpenNeuro GraphQL API, no key, fetched 2026-09-24; latestSnapshot.issuesStatus, "
        "which reports error and warning counts from the BIDS validator. A year's error rate "
        "is drawn only where at least 8 of its deposits were checked. CAVEAT: an absent "
        "validation result means the field is empty, not that the dataset failed -- and "
        "nothing here distinguishes a validator that was not run from one whose result was "
        "not attached.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for d in series:
        print(f"    {d['y']}  n={d['n']:>4}  checked {d['nv']:>4} ({d['cover']:>5.0%})  "
              f"errors {d['err_n']:>3}"
              + (f" ({d['err']:.0%})" if d["err"] is not None else " (too few)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
