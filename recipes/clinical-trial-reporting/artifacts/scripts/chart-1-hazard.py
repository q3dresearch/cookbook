#!/usr/bin/env python3
"""The deadline is a wall, not a slope — and only some sponsors can see it.

    python3 chart-1-hazard.py

Figure 3 counted submissions by lag and found a pile-up before the deadline at 5.8x the
surrounding baseline. That count understates it, because it mixes two things: how likely a
sponsor is to report, and how many sponsors are left who have not.

**The conditional hazard separates them.** Of the trials still unreported at the start of each
30-day window, what share reports during it. That denominator shrinks as trials leave, so a
flat count is a rising rate.

**Read that way the deadline is a wall.** The hazard sits at **0.22% per month** through the
first four months, drifts up to 1.1% by month ten, then jumps to **3.0% in the month before
the deadline and 4.6% in the month it falls** -- **twenty-one times the baseline**. The month
after, it collapses to 1.25%.

**It never recovers.** After the spike the hazard decays slowly and never returns to anything
like the deadline level. A sponsor who misses the date does not catch up later at a higher
rate; they join a slow tail. That is why the three-year rate in figure 3 is flat while the
one-year rate rose -- **the deadline is the only moment at which this register exerts
force**, and it exerts it once.

**And the wall is not visible to everyone.** The right panel puts each sponsor class's
deadline-window hazard against its own baseline. The classes with regulatory staff spike
hardest; the classes that rarely report barely register the date at all. **A deadline that
only the already-compliant respond to is not a general instrument.**

**What the hazard cannot say.** It measures the rate among those still at risk, so it says
nothing about the roughly three quarters who never enter the numerator at all. That share is
figure 3's gap, and this figure sits on top of it rather than replacing it.
"""
import collections, csv, datetime, gzip, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                            # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID         # noqa: E402

ROWS = os.path.join(HERE, "..", "data", "studies.csv.gz")
OUT = os.path.join(HERE, "..", "charts", "1-hazard.svg")
TODAY = datetime.date(2026, 9, 22)
WIN, NWIN, DEADLINE = 30, 30, 365
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
LABEL = {"NIH": "NIH", "FED": "other federal agency", "INDUSTRY": "industry",
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


def hazard(pop, nwin=NWIN, floor=300):
    """Of those still unreported entering each window, the share reporting during it."""
    out = []
    for b in range(nwin):
        lo, hi = b * WIN, (b + 1) * WIN
        at = [p for p in pop if p["fu"] >= hi and (p["lag"] is None or p["lag"] >= lo)]
        if len(at) < floor:
            break
        ev = sum(1 for p in at if p["lag"] is not None and lo <= p["lag"] < hi)
        out.append((lo, hi, ev / len(at), len(at)))
    return out


def main():
    try:
        with gzip.open(ROWS, "rt", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except EOFError:
        raise SystemExit("  studies.csv.gz is truncated — re-run ctg2.py")
    pop = []
    for r in rows:
        if r["study_type"] != "INTERVENTIONAL" or r["primary_completion_type"] != "ACTUAL":
            continue
        if (r["phases"] or "") in ("PHASE1", "EARLY_PHASE1", "EARLY_PHASE1|PHASE1"):
            continue
        pc = parse(r["primary_completion"])
        if not pc or pc > TODAY:
            continue
        rs = parse(r["results_submit"])
        pop.append({"lag": (rs - pc).days if rs else None, "fu": (TODAY - pc).days,
                    "sp": r["sponsor_class"] or "(blank)"})

    h = hazard(pop)
    base = sum(x[2] for x in h[:4]) / 4
    peak = max(h, key=lambda x: x[2])

    W, H = 1200, 690
    s = plate.open_svg(W, H, "The deadline is a wall, not a slope — and only some "
                             "sponsors can see it")
    fr, _ = plate.frame(W, 62,
                        who="anyone deciding whether a reporting deadline is working",
                        decide="whether the rule exerts force once or continuously",
                        wrong="the hazard after the deadline returns to the deadline level")
    s += fr

    # ---------- left: the hazard itself
    AX, AY, AH, AW = 28, 168, 420, 660
    x0, pw = AX + 50, AW - 96
    px = lambda d: x0 + pw * (d / (NWIN * WIN))
    top = 0.05
    py = lambda v: AY + AH - 54 - (AH - 88) * (v / top)
    for v in (0, .01, .02, .03, .04, .05):
        s.append(f'<line x1="{x0:.1f}" y1="{py(v):.1f}" x2="{px(NWIN*WIN):.1f}" '
                 f'y2="{py(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(x0 - 8, py(v) + 3, f"{v:.0%}" if v else "0", size=9, fill=MUTED,
                     anchor="end"))
    s.append(txt(AX, AY - 18, "of the trials still unreported, the share reporting in "
                              "each 30-day window", size=11, fill=INK2))
    for d in range(0, NWIN * WIN + 1, 180):
        s.append(f'<line x1="{px(d):.1f}" y1="{py(0):.1f}" x2="{px(d):.1f}" '
                 f'y2="{py(0)+5:.1f}" stroke="{MUTED}"/>')
        s.append(txt(px(d), py(0) + 18, str(d), size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, py(0) + 36, "days since primary completion", size=10, fill=MUTED))

    s.append(f'<line x1="{px(base and 0):.1f}" y1="{py(base):.1f}" '
             f'x2="{px(NWIN*WIN):.1f}" y2="{py(base):.1f}" stroke="{SLATE}" '
             f'stroke-width="1.2" stroke-dasharray="4 3"/>')
    s += halo(px(150), py(0.040), f"the dashed line is the baseline: {base:.2%} a month",
              size=9.5, fill=SLATE)
    s += halo(px(150), py(0.040) + 11, "averaged over the first four months", size=9,
              fill=MUTED)
    for lo, hi, v, n in h:
        hot = lo <= DEADLINE < hi or (lo <= DEADLINE - WIN < hi)
        s.append(f'<rect x="{px(lo):.1f}" y="{py(v):.1f}" '
                 f'width="{max(px(hi)-px(lo)-1.5,1):.1f}" height="{py(0)-py(v):.1f}" '
                 f'fill="{RED if hot else BLUE}" fill-opacity="{0.85 if hot else 0.5}"/>')
    s.append(f'<line x1="{px(DEADLINE):.1f}" y1="{py(top):.1f}" x2="{px(DEADLINE):.1f}" '
             f'y2="{py(0):.1f}" stroke="{RED}" stroke-width="1.5"/>')
    s += halo(px(DEADLINE) + 8, py(peak[2]) - 6, f"{peak[2]:.1%} — {peak[2]/base:.0f}x "
                                                 f"the baseline", size=11, fill=RED,
              weight="700")
    s += halo(px(DEADLINE) + 8, py(peak[2]) + 7, "the 12-month deadline", size=9.5, fill=RED)
    after = next(x for x in h if x[0] >= peak[1])
    s += halo(px(after[0]) + 10, py(after[2]) - 24, "and the month after: "
                                                    f"{after[2]:.2%}", size=10, fill=INK2)
    s += halo(px(after[0]) + 10, py(after[2]) - 12, "it never recovers", size=10,
              fill=INK2, weight="700")

    # ---------- right: who can see the wall
    BX, BY, BW = 740, 168, 432
    s.append(txt(BX, BY - 18, "each class's deadline-window hazard, against its own "
                              "baseline", size=11, fill=INK2))
    by_sp = collections.defaultdict(list)
    for p in pop:
        by_sp[p["sp"]].append(p)
    ratios = []
    for k, P in by_sp.items():
        if len(P) < 1500:
            continue
        hh = hazard(P, floor=150)
        if len(hh) < 14:
            continue
        b = sum(x[2] for x in hh[:4]) / 4
        pk = max((x for x in hh if 330 <= x[0] <= 390), key=lambda x: x[2], default=None)
        if not pk or not b:
            continue
        ratios.append({"k": k, "n": len(P), "b": b, "pk": pk[2], "r": pk[2] / b})
    ratios.sort(key=lambda d: -d["r"])
    mxr = max(d["r"] for d in ratios)
    for i, d in enumerate(ratios):
        y = BY + 18 + i * 44
        col = GREEN if d["r"] > 20 else (RED if d["r"] < 8 else BLUE)
        s.append(txt(BX, y, LABEL.get(d["k"], d["k"]), size=10.5, fill=INK, weight="600"))
        s.append(txt(BX, y + 13, f"{d['n']:,} trials · baseline {d['b']:.2%}", size=9,
                     fill=MUTED))
        w = (BW - 120) * d["r"] / mxr
        s.append(f'<rect x="{BX:.1f}" y="{y+18:.1f}" width="{max(w,2):.1f}" height="11" '
                 f'fill="{col}" fill-opacity="0.7"/>')
        s += halo(BX + max(w, 2) + 7, y + 27, f"{d['r']:.0f}x", size=11, fill=col,
                  weight="700")
    ly = BY + 18 + 44 * len(ratios) + 8
    s += wrap(BX, ly,
              "Each bar is that class's own spike against its own quiet months, so a class "
              "that reports rarely is not penalised for it — this is about whether the date "
              "registers at all. It does not register everywhere.",
              size=10.5, fill=INK2, chars=56, leading=14)

    fy = H - 24 - 14 * 3
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"ClinicalTrials.gov API v2, fetched 2026-09-22. Population as figure 3: "
              f"interventional, ACTUAL primary completion, not phase 1 — {len(pop):,} "
              f"studies. Hazard is computed on trials observed for the whole window and not "
              f"yet reported at its start, so administrative censoring removes a trial from "
              f"the denominator rather than counting it as a non-event. Baseline is the mean "
              f"of the first four windows. Windows with under 300 trials at risk are not "
              f"drawn, and per class the floor is 150. The hazard says nothing about the "
              f"roughly three quarters who never report at all — that is figure 3's gap, and "
              f"this figure sits on top of it.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    baseline {base:.2%}/month, peak {peak[2]:.2%} at {peak[0]}-{peak[1]}d "
          f"= {peak[2]/base:.1f}x, next window {after[2]:.2%}")
    for d in ratios:
        print(f"    {d['k']:<12}{d['n']:>8,}  baseline {d['b']:.2%}  peak {d['pk']:.2%}  "
              f"{d['r']:.1f}x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
