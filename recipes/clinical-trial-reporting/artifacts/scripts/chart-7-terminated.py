#!/usr/bin/env python3
"""Trials that stop early are reported more often than trials that finish.

    python3 chart-7-terminated.py

The expectation going in was the opposite. A terminated trial is the one nobody wants to write
up: the drug did not work, the funding went, the enrolment never came. If the register's
silence had a shape, that is where it should be deepest.

**It is the other way round.** Among completions 2012-2021, trials ending TERMINATED report
within three years **37.9%** of the time against **24.3%** for trials ending COMPLETED.

**And it is not composition.** Terminated trials skew slightly more industry than completed
ones -- 28% against 22% -- and industry reports more, so the pooled gap could be that alone.
Holding sponsor class fixed, it is not: inside the university and hospital group, which is
about 70% of both, terminated trials report at **31.6% against 16.4%**, nearly double. The
effect is largest exactly where the reporting rate is lowest.

**Two classes run the other way**, and they are the small ones: other federal agencies at
36.8% against 59.6%, other government at 2.0% against 4.2%. Both are on a few hundred
terminated trials, so the intervals are wide and the reversal is not established.

**What the figure does not claim.** A mechanism. Stopping early may close a project in a way
that finishing does not -- a termination is a decision someone files, where a completion hands
off to a manuscript that may never arrive -- but nothing in the register distinguishes that
from a dozen other stories. The measured fact is the ratio; the explanation is not in these
fields. **What it does rule out** is the intuition the figure started with: the register's
silence is not concentrated on the failures.

**A boundary worth naming.** WITHDRAWN studies are excluded. A withdrawn trial never enrolled
anyone, so it has no results to report and the duty does not attach in the same way. Folding
those 16,791 studies in would have made the comparison meaningless.
"""
import collections, csv, datetime, gzip, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                            # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID         # noqa: E402

ROWS = os.path.join(HERE, "..", "data", "studies.csv.gz")
OUT = os.path.join(HERE, "..", "charts", "7-terminated.svg")
TODAY = datetime.date(2026, 9, 22)
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
LABEL = {"NIH": "NIH", "FED": "other federal", "INDUSTRY": "industry",
         "NETWORK": "research network", "OTHER": "university, hospital, individual",
         "OTHER_GOV": "other government"}


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


def wilson(k, n, z=1.96):
    """95% interval. Drawn because the cells differ by two orders of magnitude and a bare
    point would let a 133-trial reversal look like the 81,471-trial baseline."""
    if not n:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(c - h, 0.0), min(c + h, 1.0)


def main():
    try:
        with gzip.open(ROWS, "rt", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except EOFError:
        raise SystemExit("  studies.csv.gz is truncated — re-run ctg2.py")
    base = []
    for r in rows:
        if r["study_type"] != "INTERVENTIONAL" or r["primary_completion_type"] != "ACTUAL":
            continue
        if (r["phases"] or "") in ("PHASE1", "EARLY_PHASE1", "EARLY_PHASE1|PHASE1"):
            continue
        pc = parse(r["primary_completion"])
        if not pc or not (2012 <= pc.year <= 2021):
            continue
        rs = parse(r["results_submit"])
        base.append({"lag": (rs - pc).days if rs else None, "fu": (TODAY - pc).days,
                     "sp": r["sponsor_class"] or "?", "st": r["status"]})

    def cell(sp, st, t=1095):
        ar = [p for p in base if p["fu"] >= t and p["st"] == st
              and (sp is None or p["sp"] == sp)]
        k = sum(1 for p in ar if p["lag"] is not None and p["lag"] <= t)
        return k, len(ar)

    classes = ["OTHER", "INDUSTRY", "NIH", "FED", "OTHER_GOV"]
    data = []
    for sp in [None] + classes:
        kc, nc = cell(sp, "COMPLETED")
        kt, nt = cell(sp, "TERMINATED")
        if nc < 120 or nt < 100:
            continue
        data.append({"sp": sp, "c": kc / nc, "nc": nc, "t": kt / nt, "nt": nt,
                     "ci_c": wilson(kc, nc), "ci_t": wilson(kt, nt)})

    W, H = 1200, 850
    s = plate.open_svg(W, H, "Trials that stop early are reported more often than "
                             "trials that finish")
    fr, _ = plate.frame(W, 62,
                        who="anyone assuming unreported trials are the failed ones",
                        decide="where in the register the missing results actually are",
                        wrong="terminated trials report less than completed ones, inside "
                              "the class that dominates the register")
    s += fr

    AX, AY, AW = 28, 176, 700
    x0, pw = AX + 236, AW - 300
    px = lambda f: x0 + pw * (f / 0.95)
    rowh = 74
    bot = AY + rowh * len(data)
    for f in (0, .25, .5, .75):
        s.append(f'<line x1="{px(f):.1f}" y1="{AY-14:.1f}" x2="{px(f):.1f}" '
                 f'y2="{bot-16:.1f}" stroke="{GRID}"/>')
        s.append(txt(px(f), bot - 2, f"{f:.0%}", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, AY - 32, "share reporting results within three years, with 95% "
                              "intervals", size=11, fill=INK2))
    s.append(txt(AX, bot + 16, "completions 2012–2021, so every cell has three years of "
                               "follow-up", size=10, fill=MUTED))

    for i, d in enumerate(data):
        y = AY + 10 + i * rowh
        name = "every class together" if d["sp"] is None else LABEL.get(d["sp"], d["sp"])
        s.append(txt(AX, y, name, size=11, fill=INK,
                     weight="700" if d["sp"] is None else "600"))
        if d["sp"] is None:
            s.append(f'<line x1="{AX:.1f}" y1="{y+40:.1f}" x2="{px(0.95):.1f}" '
                     f'y2="{y+40:.1f}" stroke="{RULE}"/>')
        for j, (key, ci, col, lab) in enumerate(
                ((d["c"], d["ci_c"], SLATE, f"completed · {d['nc']:,}"),
                 (d["t"], d["ci_t"], RED, f"terminated · {d['nt']:,}"))):
            yy = y + 12 + j * 15
            s.append(f'<line x1="{px(ci[0]):.1f}" y1="{yy:.1f}" x2="{px(ci[1]):.1f}" '
                     f'y2="{yy:.1f}" stroke="{col}" stroke-width="1.4"/>')
            for e in ci:
                s.append(f'<line x1="{px(e):.1f}" y1="{yy-3.5:.1f}" x2="{px(e):.1f}" '
                         f'y2="{yy+3.5:.1f}" stroke="{col}" stroke-width="1.4"/>')
            s.append(f'<circle cx="{px(key):.1f}" cy="{yy:.1f}" r="4.6" fill="{col}"/>')
            s += halo(px(key) + 9, yy + 3.5, f"{key:.1%}", size=10, fill=col, weight="700")
            s.append(txt(AX, yy + 3.5, lab, size=9.5, fill=col, anchor="start"))
        ratio = d["t"] / d["c"] if d["c"] else 0
        s += halo(px(0.95) + 8, y + 22, f"{ratio:.2f}x", size=12,
                  fill=GREEN if ratio > 1.1 else (RED if ratio < 0.9 else MUTED),
                  weight="700")

    BX = 780
    ty = bot + 44
    s.append(txt(AX, ty, "the intuition this rules out", size=12.5, fill=INK, weight="600"))
    s += wrap(AX, ty + 20,
              "A terminated trial is the one nobody wants to write up — the drug did not "
              "work, the money went, the enrolment never came. If the register's silence had "
              "a shape, that is where it should be deepest. It is the other way round, and "
              "the effect is largest inside the university and hospital group, which is about "
              "70% of both arms and has the lowest reporting rate of any large class.",
              size=11, fill=INK2, chars=92, leading=15)
    s += halo(AX + 800, ty + 2, "what it does not claim", size=11, fill=MUTED, weight="700")
    s += wrap(AX + 800, ty + 20,
              "A mechanism. Stopping early may close a project in a way finishing does not, "
              "but the register cannot separate that from a dozen other stories. The measured "
              "fact is the ratio. Withdrawn studies are excluded: they never enrolled anyone, "
              "so there is nothing to report.",
              size=10.5, fill=INK2, chars=42, leading=14)

    fy = H - 24 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"ClinicalTrials.gov API v2, fetched 2026-09-22. Population as figure 3, "
              f"restricted to completions 2012–2021. Intervals are 95% Wilson, drawn because "
              f"the cells span two orders of magnitude — the two classes that reverse the "
              f"finding have 133 and 147 terminated trials and their intervals say so. "
              f"Classes with under 120 completed or 100 terminated trials are not drawn.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for d in data:
        print(f"    {(d['sp'] or 'ALL'):<12}completed {d['c']:.1%} (n={d['nc']:,})   "
              f"terminated {d['t']:.1%} (n={d['nt']:,})   {d['t']/d['c']:.2f}x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
