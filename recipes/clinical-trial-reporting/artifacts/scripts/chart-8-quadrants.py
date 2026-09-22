#!/usr/bin/env python3
"""Two things predict reporting, they multiply, and one group is immune to both.

    python3 chart-8-quadrants.py

Figure 4 found sponsor class spans twentyfold. Figure 6 found registration timing predicts
reporting inside every class. This crosses them, and adds the third candidate — how many
trials the sponsor runs — to see which survive together.

**Lead time is monotone and strong.** Share reporting within three years by the gap between
registration and primary completion: registered *after* finishing **5.6%**, under a year
**20.4%**, one to two years **28.2%**, two to four **32.4%**, over four **39.9%**. A sevenfold
range on a variable that is nothing but a date subtraction.

**Sponsor scale is a threshold, not a gradient.** Grouping the 17,748 lead sponsors by how
many trials they run: a sponsor with one trial reports 19.0% of the time, with 2-5 trials
19.3%, with 6-20 **17.6%**, with 21-100 18.5% -- **flat**. Then 101-500 jumps to **30.9%** and
501+ to **50.0%**. Running ten trials instead of one buys nothing. Running a hundred does.
Whatever the mechanism is, it appears between 100 and 500 trials and not before.

**Crossed, they multiply rather than substitute.** Inside industry, reporting runs 17.2% to
58.1% across lead-time bands; inside university and hospital sponsors, 4.2% to 26.6%. Each
variable keeps roughly its full effect with the other held fixed, so they are not two
measurements of one thing.

**And other government is flat against both.** 2.4%, 4.5%, 4.7%, 4.3% across lead time --
no gradient at all, on 2,306 trials. Every other class responds to registration timing. This
one does not respond to anything measured here, which makes it a different problem rather
than a worse version of the same one.

**The confound this does not resolve.** Lead time is partly a property of the trial -- a long
study registered properly has a long lead by construction -- so "longer lead" and "larger,
slower, better-resourced trial" are not separated here. The sponsor-scale panel is the closest
thing to a control, and it says scale alone does not explain it below 100 trials.
"""
import collections, csv, datetime, gzip, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                            # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID         # noqa: E402

ROWS = os.path.join(HERE, "..", "data", "studies.csv.gz")
OUT = os.path.join(HERE, "..", "charts", "8-quadrants.svg")
TODAY = datetime.date(2026, 9, 22)
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
BANDS = [("registered\nafter finishing", -10 ** 9, 0), ("under\n1 year", 0, 365),
         ("1 to 2\nyears", 365, 730), ("2 to 4\nyears", 730, 1460),
         ("over 4\nyears", 1460, 10 ** 9)]
SIZES = [("1", 1, 2), ("2–5", 2, 6), ("6–20", 6, 21), ("21–100", 21, 101),
         ("101–500", 101, 501), ("501+", 501, 10 ** 9)]
CLASSES = [("INDUSTRY", "industry", GREEN), ("OTHER", "university, hospital", BLUE),
           ("OTHER_GOV", "other government", RED)]


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
    base = []
    for r in rows:
        if r["study_type"] != "INTERVENTIONAL" or r["primary_completion_type"] != "ACTUAL":
            continue
        if (r["phases"] or "") in ("PHASE1", "EARLY_PHASE1", "EARLY_PHASE1|PHASE1"):
            continue
        pc, fp = parse(r["primary_completion"]), parse(r["first_post"])
        if not pc or not fp or not (2012 <= pc.year <= 2021):
            continue
        rs = parse(r["results_submit"])
        base.append({"lead": (pc - fp).days, "lag": (rs - pc).days if rs else None,
                     "fu": (TODAY - pc).days, "sp": r["sponsor_class"] or "?",
                     "name": r["sponsor_name"]})
    cnt = collections.Counter(p["name"] for p in base)

    def share(P, t=1095, floor=120):
        ar = [p for p in P if p["fu"] >= t]
        if len(ar) < floor:
            return None, len(ar)
        return sum(1 for p in ar if p["lag"] is not None and p["lag"] <= t) / len(ar), len(ar)

    W, H = 1200, 800
    s = plate.open_svg(W, H, "Two things predict reporting, they multiply, and one "
                             "group is immune to both")
    fr, _ = plate.frame(W, 62,
                        who="anyone choosing where to aim a reporting intervention",
                        decide="whether sponsor scale or registration discipline is the "
                               "lever",
                        wrong="the lead-time gradient disappears inside a sponsor class")
    s += fr

    # ---------- left: the crossing
    AX, AY, AH, AW = 28, 176, 380, 640
    x0, pw = AX + 54, AW - 100
    step = pw / (len(BANDS) - 1)
    bx = lambda i: x0 + step * i
    py = lambda f: AY + AH - 66 - (AH - 100) * (f / 0.62)
    for f in (0, .2, .4, .6):
        s.append(f'<line x1="{x0-14:.1f}" y1="{py(f):.1f}" x2="{bx(len(BANDS)-1)+14:.1f}" '
                 f'y2="{py(f):.1f}" stroke="{GRID}"/>')
        s.append(txt(x0 - 22, py(f) + 3, f"{f:.0%}", size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, AY - 18, "share reporting within three years", size=11, fill=INK2))
    for i, (lab, _, _) in enumerate(BANDS):
        for j, line in enumerate(lab.split("\n")):
            s.append(txt(bx(i), py(0) + 20 + j * 11, line, size=9, fill=MUTED,
                         anchor="middle"))
    s.append(txt(AX, py(0) + 50, "gap between registration and primary completion",
                 size=10, fill=MUTED))

    for key, lab, col in CLASSES:
        pts = []
        for i, (_, lo, hi) in enumerate(BANDS):
            P = [p for p in base if p["sp"] == key and lo <= p["lead"] < hi]
            v, n = share(P)
            if v is not None:
                pts.append((bx(i), py(v), v, n))
        if len(pts) < 3:
            continue
        s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                        for i, (a, b, _, _) in enumerate(pts))
                 + f'" fill="none" stroke="{col}" stroke-width="2.6"/>')
        for a, b, v, n in pts:
            s.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="4" fill="{col}"/>')
        s += halo(pts[-1][0] + 9, pts[-1][1] + 3, lab, size=10, fill=col, weight="700")
        s += halo(pts[0][0] - 9, pts[0][1] + 3, f"{pts[0][2]:.1%}", size=9.5, fill=col,
                  anchor="end")
        s += halo(pts[-1][0] + 9, pts[-1][1] + 15, f"{pts[-1][2]:.1%}", size=9.5, fill=col)

    # ---------- right: scale is a threshold
    BX, BY, BH, BW = 730, 176, 380, 440
    s.append(txt(BX, BY - 18, "share reporting, by how many trials that sponsor runs",
                 size=11, fill=INK2))
    sx0, spw = BX + 44, BW - 96
    sstep = spw / (len(SIZES) - 1)
    sbx = lambda i: sx0 + sstep * i
    spy = lambda f: BY + BH - 66 - (BH - 100) * (f / 0.62)
    for f in (0, .2, .4, .6):
        s.append(f'<line x1="{sx0-12:.1f}" y1="{spy(f):.1f}" '
                 f'x2="{sbx(len(SIZES)-1)+12:.1f}" y2="{spy(f):.1f}" stroke="{GRID}"/>')
        s.append(txt(sx0 - 20, spy(f) + 3, f"{f:.0%}", size=9, fill=MUTED, anchor="end"))
    pts = []
    for i, (lab, lo, hi) in enumerate(SIZES):
        P = [p for p in base if lo <= cnt[p["name"]] < hi]
        v, n = share(P)
        s.append(txt(sbx(i), spy(0) + 20, lab, size=9, fill=MUTED, anchor="middle"))
        if v is not None:
            pts.append((sbx(i), spy(v), v, n))
    s.append(txt(BX, spy(0) + 42, "trials that lead sponsor has in the register",
                 size=10, fill=MUTED))
    s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                    for i, (a, b, _, _) in enumerate(pts))
             + f'" fill="none" stroke={chr(34)}{AMBER}{chr(34)} stroke-width="2.6"/>')
    for a, b, v, n in pts:
        s.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="4.4" fill="{AMBER}"/>')
        s += halo(a, b - 10, f"{v:.1%}", size=9.5, fill=AMBER, anchor="middle",
                  weight="700")
    flat = [p for p in pts[:4]]
    s.append(f'<rect x="{flat[0][0]-14:.1f}" y="{spy(0.235):.1f}" '
             f'width="{flat[-1][0]-flat[0][0]+28:.1f}" height="{spy(0.145)-spy(0.235):.1f}" '
             f'fill="{MUTED}" fill-opacity="0.13"/>')
    s += halo((flat[0][0] + flat[-1][0]) / 2, spy(0.27), "flat from 1 to 100 trials",
              size=10, fill=INK2, anchor="middle", weight="700")

    ty = AY + AH + 42
    s.append(txt(AX, ty, "they multiply, and one class is flat against both",
                 size=12.5, fill=INK, weight="600"))
    s += wrap(AX, ty + 20,
              "Each variable keeps roughly its full effect with the other held fixed, so "
              "they are not two measurements of one thing. Other government is the exception "
              "and the interesting one: 2.4%, 4.5%, 4.7%, 4.3% across lead time is no "
              "gradient at all. Every other class responds to registration timing; that one "
              "responds to nothing measured here, which makes it a different problem rather "
              "than a worse version of the same one.",
              size=11, fill=INK2, chars=88, leading=15)
    s += halo(AX + 770, ty + 2, "what this does not separate", size=11, fill=MUTED,
              weight="700")
    s += wrap(AX + 770, ty + 20,
              "Lead time is partly a property of the trial: a long study registered properly "
              "has a long lead by construction. “longer lead” and “larger, "
              "slower, better-resourced” are not pulled apart here.",
              size=10.5, fill=INK2, chars=44, leading=14)

    fy = H - 24 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"ClinicalTrials.gov API v2, fetched 2026-09-22. Population as figure 3, "
              f"completions 2012–2021 — {len(base):,} trials across {len(cnt):,} distinct "
              f"lead sponsors. Sponsor scale counts trials filed under that exact sponsor "
              f"name in this window, so a name that changed spelling counts twice and the "
              f"large end is a floor. Cells with under 120 trials at three years of "
              f"follow-up are not drawn.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for lab, lo, hi in SIZES:
        v, n = share([p for p in base if lo <= cnt[p["name"]] < hi])
        print(f"    sponsor runs {lab:<9}{n:>8,}  {v:.1%}" if v else f"    {lab}: -")
    return 0


if __name__ == "__main__":
    sys.exit(main())
