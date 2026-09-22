#!/usr/bin/env python3
"""A sixth of the register has a status that is not a status.

    python3 chart-5-unknown.py

`UNKNOWN` is the second most common value in the register's status field -- **96,931 studies,
16.1%**, behind only COMPLETED. Read as an outcome it says a sixth of all clinical research
ended in some indeterminate way.

**It is not an outcome. It is a timer.** ClinicalTrials.gov assigns it when a study's
completion date has passed and the sponsor has not updated the record for over two years. It
describes the *record*, not the trial: every one of these studies had a real ending that
nobody came back to write down.

**The proof is that it is structurally unreachable for recent cohorts.** Share of each
registration year now marked UNKNOWN: **8.4% for 2005, rising to 27.1% for 2022-23, then
17.2% for 2024, 0.3% for 2025 and 0.0% for 2026.** A 2026 registration cannot be two years
stale. The collapse at the right edge is not a sudden improvement in record-keeping; it is
the definition running out of runway. Any cross-sectional table of trial outcomes that
includes this row is mixing a state with a clock.

**Why it also rises with age, up to a point.** Older cohorts have had longer to be abandoned,
so the share climbs -- but it stops climbing around 2022 and turns over, which the age
explanation alone does not predict. The turn is the two-year rule biting: 2024 registrations
mostly have not had a completion date pass *and* two silent years yet.

**What it costs to read it as an outcome.** The same figure shows COMPLETED falling from 78.5%
to 19.4% across the same cohorts, which would be a catastrophic collapse in trial completion
if it were real. It is the same artefact from the other side: recent trials have not finished
yet. **Both rows are cohort age wearing a status field's clothes.**
"""
import collections, csv, datetime, gzip, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                            # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID         # noqa: E402

ROWS = os.path.join(HERE, "..", "data", "studies.csv.gz")
OUT = os.path.join(HERE, "..", "charts", "5-unknown.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
SERIES = [("UNKNOWN", RED, "UNKNOWN"), ("COMPLETED", GREEN, "COMPLETED"),
          ("RECRUITING", BLUE, "RECRUITING"), ("TERMINATED", AMBER, "TERMINATED")]


def parse(d):
    if not d:
        return None
    try:
        if len(d) == 7:
            return datetime.date(int(d[:4]), int(d[5:7]), 15)
        if len(d) == 10:
            return datetime.date(int(d[:4]), int(d[5:7]), int(d[8:10]))
    except ValueError:
        pass
    return None


def main():
    try:
        with gzip.open(ROWS, "rt", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except EOFError:
        raise SystemExit("  studies.csv.gz is truncated — re-run ctg2.py")

    by = collections.defaultdict(collections.Counter)
    for r in rows:
        d = parse(r["first_post"])
        if d and 2005 <= d.year <= 2026:
            by[d.year][r["status"]] += 1
    yrs = sorted(by)
    tot = {y: sum(by[y].values()) for y in yrs}
    unk_total = sum(1 for r in rows if r["status"] == "UNKNOWN")

    W, H = 1200, 640
    s = plate.open_svg(W, H, "A sixth of the register has a status that is not a status")
    fr, _ = plate.frame(W, 62,
                        who="anyone tabulating trial outcomes from the status field",
                        decide="whether a status row is a state or a clock",
                        wrong="UNKNOWN's share is flat across registration cohorts")
    s += fr

    AX, AY, AH, AW = 28, 158, 400, 700
    x0, pw = AX + 46, AW - 92
    px = lambda y: x0 + pw * ((y - yrs[0]) / (yrs[-1] - yrs[0]))
    py = lambda f: AY + AH - 54 - (AH - 88) * f
    for f in (0, .25, .5, .75, 1.0):
        s.append(f'<line x1="{x0:.1f}" y1="{py(f):.1f}" x2="{px(yrs[-1]):.1f}" '
                 f'y2="{py(f):.1f}" stroke="{GRID}"/>')
        s.append(txt(x0 - 8, py(f) + 3, f"{f:.0%}", size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, AY - 18, "share of that registration year's studies now carrying "
                              "each status", size=11, fill=INK2))
    for y in range(2005, 2027, 5):
        s.append(f'<line x1="{px(y):.1f}" y1="{py(0):.1f}" x2="{px(y):.1f}" '
                 f'y2="{py(0)+5:.1f}" stroke="{MUTED}"/>')
        s.append(txt(px(y), py(0) + 18, str(y), size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, py(0) + 36, "year the study was first posted to the register",
                 size=10, fill=MUTED))

    for key, col, lab in SERIES:
        pts = [(px(y), py(by[y][key] / tot[y])) for y in yrs]
        s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                        for i, (a, b) in enumerate(pts))
                 + f'" fill="none" stroke="{col}" stroke-width="2.6"/>')
        for a, b in pts:
            s.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="2.6" fill="{col}"/>')
        if key == "UNKNOWN":
            # both UNKNOWN and TERMINATED end at zero, so this one is named at its peak
            pk = max(yrs, key=lambda y: by[y][key] / tot[y])
            s += halo(px(pk) - 8, py(by[pk][key] / tot[pk]) - 9, lab, size=10.5, fill=col,
                      anchor="end", weight="700")
        else:
            dy = {"COMPLETED": -11, "RECRUITING": -11, "TERMINATED": 16}[key]
            s += halo(pts[-1][0] - 4, pts[-1][1] + dy, lab, size=10.5, fill=col,
                      anchor="end", weight="700")

    peak = max(yrs, key=lambda y: by[y]["UNKNOWN"] / tot[y])
    s.append(f'<line x1="{px(peak):.1f}" y1="{py(by[peak]["UNKNOWN"]/tot[peak]):.1f}" '
             f'x2="{px(peak):.1f}" y2="{py(0):.1f}" stroke="{RED}" stroke-width="1" '
             f'stroke-dasharray="2 3"/>')
    for i, line in enumerate(("a 2026 registration cannot be",
                              "two years stale, so the collapse",
                              "at the right edge is the definition",
                              "running out of runway")):
        s += halo(px(2024.2), py(0.72) + i * 13, line, size=10.5, fill=RED,
                  anchor="end", weight="700")

    BX, BY = 770, 158
    s.append(txt(BX, BY - 18, "what the field says, if you read it as an outcome",
                 size=11, fill=INK2))
    y = BY + 12
    for key, col, lab in SERIES:
        first = by[2005][key] / tot[2005]
        last = by[2026][key] / tot[2026]
        s.append(txt(BX, y, lab, size=10.5, fill=col, weight="700"))
        s += halo(BX + 392, y, f"{first:.1%}  to  {last:.1%}", size=10.5, fill=col,
                  anchor="end", weight="700")
        s.append(txt(BX, y + 13, "registered 2005 versus registered 2026", size=9,
                     fill=MUTED))
        y += 40
    s += wrap(BX, y + 4,
              f"Read as outcomes these are impossible: trial completion did not fall from "
              f"78.5% to 19.4%, and abandonment did not vanish. Both rows are cohort age. "
              f"UNKNOWN needs a passed completion date plus two silent years, and COMPLETED "
              f"needs the trial to have finished — neither is available to a 2026 "
              f"registration, and both are available to a 2005 one.",
              size=10.5, fill=INK2, chars=54, leading=14)
    y += 104
    s.append(f'<rect x="{BX-10:.1f}" y="{y-16:.1f}" width="402" height="62" '
             f'fill="{RED}" fill-opacity="0.07"/>')
    s.append(txt(BX, y, "the rule this breaks", size=11, fill=RED, weight="700"))
    s += wrap(BX, y + 17,
              f"{unk_total:,} studies carry UNKNOWN. Any cross-sectional table of trial "
              f"outcomes that includes that row is mixing a state with a clock.",
              size=10.5, fill=INK2, chars=54, leading=14)

    fy = H - 24 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"ClinicalTrials.gov API v2, fetched 2026-09-22, all {len(rows):,} registered "
              f"studies. Cohort is the year the record was first posted, which is complete for "
              f"every row. UNKNOWN is assigned by the register when a study's completion date "
              f"has passed and the record has not been updated in over two years; it is not "
              f"submitted by the sponsor. Every status is shown as a share of its own "
              f"registration year, so the four lines do not sum to one — the remaining "
              f"statuses are omitted for legibility, not excluded from the denominator.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for y_ in (2005, 2015, 2022, 2023, 2024, 2025, 2026):
        print(f"    {y_}: UNKNOWN {by[y_]['UNKNOWN']/tot[y_]:>6.1%}   "
              f"COMPLETED {by[y_]['COMPLETED']/tot[y_]:>6.1%}   n={tot[y_]:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
