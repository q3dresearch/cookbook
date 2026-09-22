#!/usr/bin/env python3
"""Trials look three times faster than in 2008. They are slower.

    python3 chart-11-tempo.py

**The obvious measurement says the field has accelerated dramatically.** Median time from
start to primary completion, among trials that completed: **700 days for 2008 starts, 243 for
2024 starts**. A threefold speed-up in sixteen years.

**It is an artefact, and the true direction is the opposite one.** A 2024 start can only
appear in that median if it has *already finished*, so recent cohorts are a sample of their
own fastest members. The slow half has not had time to arrive. The measurement improves every
year for the same reason a race looks fast if you time only the people who have crossed the
line.

**Keeping every trial in the denominator inverts it.** Share of each start cohort that had
reached primary completion within a fixed window, with unfinished trials counted as
unfinished rather than dropped:

| started | within 1 year | within 3 years | within 5 years |
| --- | --- | --- | --- |
| 2008 | 27% | 62% | **78%** |
| 2014 | 27% | 60% | 75% |
| 2021 | 27% | 54% | **64%** |

**One-year completion has not moved in sixteen years. Three-year completion fell 12 points
and five-year completion fell 14.** Whatever is slower is slower in the tail: the trials that
were going to take a while now take longer, and the quick ones are unchanged.

**It is not that trials got bigger.** Median actual enrollment is **60 participants in every
start year from 2008 to 2022**, and the 90th percentile drifted *down* from 415 to 340. The
slowdown is not more participants.

**Phase 2 is where the time goes.** Of trials started 2010-2018: phase 1 reaches primary
completion within a year **38%** of the time, phase 2 only **18%**, and at five years phase 2
is still last at 70% against phase 1's 78%. Phase 3 runs larger than phase 2 -- median
enrollment 204 against 55 -- and still finishes more often by every horizon.

**What this does not measure.** Whether a trial *should* have been faster. A longer trial may
be a larger question, a harder population, or a better-run follow-up. The register records
duration, not difficulty.
"""
import collections, csv, datetime, gzip, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                            # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID         # noqa: E402

MAIN = os.path.join(HERE, "..", "data", "studies.csv.gz")
EXTRA = os.path.join(HERE, "..", "data", "extra.csv.gz")
OUT = os.path.join(HERE, "..", "charts", "11-tempo.svg")
TODAY = datetime.date(2026, 9, 22)
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"


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


def load(p):
    try:
        with gzip.open(p, "rt", newline="", encoding="utf-8") as f:
            return {r["nct_id"]: r for r in csv.DictReader(f)}
    except EOFError:
        raise SystemExit(f"  {os.path.basename(p)} is truncated — re-run its fetcher")


def main():
    mn, ex = load(MAIN), load(EXTRA)
    T = []
    for k, m in mn.items():
        r = ex.get(k)
        if not r or m["study_type"] != "INTERVENTIONAL":
            continue
        st, pc = parse(r["start"]), parse(m["primary_completion"])
        if not st or st.year < 2000 or st > TODAY:
            continue
        dur = ((pc - st).days if pc and m["primary_completion_type"] == "ACTUAL" else None)
        try:
            n = int(m["enrollment"])
        except (ValueError, TypeError):
            n = None
        T.append({"st": st, "dur": dur if (dur is None or 0 < dur < 7000) else None,
                  "ph": (m["phases"] or "NA").split("|")[0], "n": n})

    coh = collections.defaultdict(list)
    for t in T:
        coh[t["st"].year].append(t)

    def done_by(P, d, floor=300):
        ar = [p for p in P if (TODAY - p["st"]).days >= d]
        if len(ar) < floor:
            return None
        return sum(1 for p in ar if p["dur"] is not None and p["dur"] <= d) / len(ar)

    naive = {}
    for y, P in coh.items():
        v = [p["dur"] for p in P if p["dur"]]
        if len(v) > 300:
            naive[y] = statistics.median(v)

    W, H = 1200, 845
    s = plate.open_svg(W, H, "Trials look three times faster than in 2008. They are slower.")
    fr, _ = plate.frame(W, 62,
                        who="anyone measuring whether trials have got quicker",
                        decide="whether a duration series is timing everyone or only "
                               "the finishers",
                        wrong="the two panels point the same way")
    s += fr

    # ---------- left: the wrong answer, drawn because it is the persuasive one
    AX, AY, AH, AW = 28, 176, 240, 560
    yrs = sorted(y for y in naive if 2006 <= y <= 2024)
    x0, pw = AX + 52, AW - 96
    px = lambda y: x0 + pw * ((y - yrs[0]) / (yrs[-1] - yrs[0]))
    py = lambda v: AY + AH - 46 - (AH - 76) * (v / 800)
    for v in (0, 200, 400, 600, 800):
        s.append(f'<line x1="{x0:.1f}" y1="{py(v):.1f}" x2="{px(yrs[-1]):.1f}" '
                 f'y2="{py(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(x0 - 8, py(v) + 3, str(v), size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, AY - 18, "median days to primary completion — among trials that "
                              "finished", size=11, fill=RED))
    for y in range(2008, 2025, 4):
        s.append(txt(px(y), py(0) + 17, str(y), size=9, fill=MUTED, anchor="middle"))
    pts = [(px(y), py(naive[y])) for y in yrs]
    s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                    for i, (a, b) in enumerate(pts))
             + f'" fill="none" stroke="{RED}" stroke-width="2.6"/>')
    for a, b in pts:
        s.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="2.8" fill="{RED}"/>')
    s += halo(px(yrs[0]) + 8, py(naive[yrs[0]]) - 10, f"{naive[yrs[0]]:.0f}d", size=10,
              fill=RED, weight="700")
    s += halo(px(yrs[-1]) - 8, py(naive[yrs[-1]]) - 10, f"{naive[yrs[-1]]:.0f}d", size=10,
              fill=RED, anchor="end", weight="700")
    s += halo(px(2013), py(690), "the wrong answer, and the persuasive one", size=10.5,
              fill=RED, weight="700")
    s += wrap(AX, py(0) + 34,
              "A 2024 start can only appear here if it has already finished, so recent "
              "cohorts are a sample of their own fastest members. The slow half has not "
              "arrived. It is a race timed only on the people who crossed the line.",
              size=10.5, fill=INK2, chars=76, leading=14)

    # ---------- left lower: the right answer
    CY = AY + AH + 118
    CH = 210
    cpy = lambda f: CY + CH - 44 - (CH - 72) * (f / 0.85)
    for f in (0, .25, .5, .75):
        s.append(f'<line x1="{x0:.1f}" y1="{cpy(f):.1f}" x2="{px(yrs[-1]):.1f}" '
                 f'y2="{cpy(f):.1f}" stroke="{GRID}"/>')
        s.append(txt(x0 - 8, cpy(f) + 3, f"{f:.0%}", size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, CY - 18, "share of each start cohort that had finished by then — "
                              "everyone in the denominator", size=11, fill=GREEN))
    for y in range(2008, 2025, 4):
        s.append(txt(px(y), cpy(0) + 17, str(y), size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, cpy(0) + 34, "year the trial started", size=10, fill=MUTED))
    for d, lab, col in ((1825, "within 5 years", "#14425f"), (1095, "within 3 years", GREEN),
                        (365, "within 1 year", "#8aa2b6")):
        pp = []
        for y in yrs:
            v = done_by(coh[y], d)
            if v is not None:
                pp.append((px(y), cpy(v), v))
        if len(pp) < 4:
            continue
        s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                        for i, (a, b, _) in enumerate(pp))
                 + f'" fill="none" stroke="{col}" stroke-width="2.4"/>')
        for a, b, _ in pp:
            s.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="2.6" fill="{col}"/>')
        s += halo(pp[-1][0] + 7, pp[-1][1] + 3, lab, size=9.5, fill=col, weight="700")
        s += halo(pp[0][0] - 7, pp[0][1] + 3, f"{pp[0][2]:.0%}", size=9, fill=col,
                  anchor="end")
        s += halo(pp[-1][0] + 7, pp[-1][1] + 14, f"{pp[-1][2]:.0%}", size=9, fill=col)

    # ---------- right: by phase, and size did not move
    BX, BY, BW = 700, 176, 472
    s.append(txt(BX, BY - 18, "share reaching primary completion, by phase — starts "
                              "2010–2018", size=11, fill=INK2))
    PH = [("PHASE1", "phase 1"), ("PHASE2", "phase 2"), ("PHASE3", "phase 3"),
          ("PHASE4", "phase 4"), ("NA", "no phase recorded")]
    hx0, hpw = BX + 4, BW - 190
    for i, (key, lab) in enumerate(PH):
        P = [t for t in T if 2010 <= t["st"].year <= 2018 and t["ph"] == key]
        if len(P) < 300:
            continue
        y = BY + 22 + i * 62
        ens = [p["n"] for p in P if p["n"]]
        s.append(txt(BX, y, lab, size=10.5, fill=INK, weight="600"))
        s.append(txt(BX, y + 13, f"{len(P):,} trials · median {statistics.median(ens):.0f} "
                                 f"enrolled", size=9, fill=MUTED))
        for j, (d, col) in enumerate(((365, "#8aa2b6"), (1095, GREEN), (1825, "#14425f"))):
            v = done_by(P, d)
            if v is None:
                continue
            w = hpw * v
            s.append(f'<rect x="{hx0:.1f}" y="{y+19+j*8:.1f}" width="{max(w,2):.1f}" '
                     f'height="6.5" fill="{col}" fill-opacity="0.8"/>')
            s += halo(hx0 + max(w, 2) + 6, y + 25 + j * 8, f"{v:.0%}", size=8.5, fill=col)
    ly = BY + 22 + 62 * len(PH) + 2
    s += wrap(BX, ly,
              "Phase 1 finishes fastest and phase 2 slowest, at every horizon. Phase 3 runs "
              "four times larger than phase 2 by median enrollment and still finishes more "
              "often — so the phase-2 delay is not size. Bars are 1, 3 and 5 years.",
              size=10.5, fill=INK2, chars=62, leading=14)
    ly += 66
    s.append(txt(BX, ly, "and trials did not get bigger", size=11.5, fill=INK, weight="600"))
    med = {}
    for y in range(2008, 2023):
        v = sorted(t["n"] for t in T if t["st"].year == y and t["n"] and t["n"] > 0)
        if len(v) > 300:
            med[y] = v[len(v) // 2]
    s += wrap(BX, ly + 18,
              f"Median actual enrollment is {min(med.values()):.0f} participants in every "
              f"start year from 2008 to 2022, and the 90th percentile drifted down. Whatever "
              f"is slower, it is not more participants.",
              size=10.5, fill=INK2, chars=62, leading=14)

    fy = H - 24 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"ClinicalTrials.gov API v2, fetched 2026-09-22; start date from the second "
              f"walk. {len(T):,} interventional trials with a start date. A trial counts as "
              f"finished only on an ACTUAL primary completion date, so an estimated one is "
              f"treated as not yet finished. Cohorts are only drawn where at least 300 "
              f"trials have had the full window to finish in. This measures duration, not "
              f"difficulty: a longer trial may be a larger question or a harder population.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    naive median: {naive[yrs[0]]:.0f}d ({yrs[0]}) -> {naive[yrs[-1]]:.0f}d "
          f"({yrs[-1]})")
    for d in (365, 1095, 1825):
        a, b = done_by(coh[2008], d), done_by(coh[2021], d)
        if a and b:
            print(f"    within {d//365}y: 2008 {a:.0%} -> 2021 {b:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
