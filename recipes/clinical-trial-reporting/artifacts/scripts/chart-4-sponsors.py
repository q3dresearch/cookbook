#!/usr/bin/env python3
"""The flat quarter is an average of two fields that barely overlap.

    python3 chart-4-sponsors.py

Figure 3 found three-year reporting rising to about 25% by 2012 and flat ever since.
Pooled series hide
composition, and this one hides a lot of it.

**Split by who sponsored the trial and the range is twentyfold.** For completions 2015-2021,
share reporting within three years: **NIH 84.8%**, federal agencies 58.0%, **industry 51.4%**,
networks 33.7%, **academic and hospital sponsors 16.8%**, other government **3.4%**.

**And the group that reports least is almost the whole register.** `OTHER` -- universities,
hospitals, individual investigators -- is 56,208 of the 73,990 trials in this window, **76%**.
So the pooled 25% is not a typical rate. It is mostly one group's 17%, diluted upward by a
much smaller group's 51%.

**Which changes what the flat line in figure 3 means.** A pooled series that does not move is
consistent with nothing moving and equally with the groups moving in opposite directions. The
right panel separates them: it asks whether each class's own three-year rate has changed since
2010, and they have not converged.

**Whether the deadline itself registers for every class** is a separate question, and figure 1
answers it properly as a hazard against each class's own baseline -- 82x for industry against
1.4x for other government. It is not drawn again here; the per-class spike share is still
computed and printed by this script as a diagnostic, but a raw share of reports penalises a
class for reporting rarely, which is why figure 1's version is the one on a plate.

**What this cannot say.** `leadSponsorClass` is the *lead* sponsor only, and a university
running an industry-funded trial files as OTHER. So this separates who filed, not who paid,
and the industry figure is a floor rather than an estimate.
"""
import collections, csv, datetime, gzip, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                            # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID         # noqa: E402

ROWS = os.path.join(HERE, "..", "data", "studies.csv.gz")
OUT = os.path.join(HERE, "..", "charts", "4-sponsors.svg")
TODAY = datetime.date(2026, 9, 22)
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
LABEL = {"NIH": "NIH", "FED": "other federal agency", "INDUSTRY": "industry",
         "NETWORK": "research network", "OTHER": "university, hospital, individual",
         "OTHER_GOV": "other government", "INDIV": "individual"}
ORDER = ["NIH", "FED", "INDUSTRY", "NETWORK", "OTHER", "OTHER_GOV"]


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


def load():
    try:
        with gzip.open(ROWS, "rt", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except EOFError:
        raise SystemExit("  studies.csv.gz is truncated — re-run ctg2.py")


def pop_rows(rows):
    out = []
    for r in rows:
        if r["study_type"] != "INTERVENTIONAL":
            continue
        if r["primary_completion_type"] != "ACTUAL":
            continue
        if (r["phases"] or "") in ("PHASE1", "EARLY_PHASE1", "EARLY_PHASE1|PHASE1"):
            continue
        pc = parse(r["primary_completion"])
        if not pc or pc > TODAY:
            continue
        rs = parse(r["results_submit"])
        out.append({"pc": pc, "lag": (rs - pc).days if rs else None,
                    "fu": (TODAY - pc).days, "sp": r["sponsor_class"] or "(blank)"})
    return out


def share(P, t):
    ar = [p for p in P if p["fu"] >= t]
    if len(ar) < 150:
        return None
    return sum(1 for p in ar if p["lag"] is not None and p["lag"] <= t) / len(ar)


def main():
    rows = load()
    pop = pop_rows(rows)
    win = [p for p in pop if 2015 <= p["pc"].year <= 2021]
    by = collections.defaultdict(list)
    for p in win:
        by[p["sp"]].append(p)
    stats = []
    for k in ORDER:
        P = by.get(k, [])
        if len(P) < 150:
            continue
        s3 = share(P, 1095)
        s1 = share(P, 365)
        reps = [p for p in P if p["lag"] is not None]
        spike = (sum(1 for p in reps if 335 <= p["lag"] < 365) / len(reps)) if reps else 0
        stats.append({"k": k, "n": len(P), "s1": s1, "s3": s3, "spike": spike})
    stats.sort(key=lambda d: -(d["s3"] or 0))
    total = sum(d["n"] for d in stats)

    W, H = 1200, 800
    s = plate.open_svg(W, H, "The flat quarter is an average of two fields that "
                             "barely overlap")
    fr, _ = plate.frame(W, 62,
                        who="anyone quoting a register-wide reporting rate",
                        decide="whether a pooled rate describes anybody in particular",
                        wrong="the sponsor classes sit within a few points of each other")
    s += fr

    # ---------- left: one-year against three-year, so level and speed are both axes
    AX, AY, AH, AW = 28, 168, 400, 620
    x0, pw = AX + 50, AW - 96
    px = lambda f: x0 + pw * (f / 0.95)
    py = lambda f: AY + AH - 54 - (AH - 88) * (f / 0.95)
    for f in (0, .25, .5, .75):
        s.append(f'<line x1="{px(0):.1f}" y1="{py(f):.1f}" x2="{px(0.95):.1f}" '
                 f'y2="{py(f):.1f}" stroke="{GRID}"/>')
        s.append(f'<line x1="{px(f):.1f}" y1="{py(0):.1f}" x2="{px(f):.1f}" '
                 f'y2="{py(0.95):.1f}" stroke="{GRID}"/>')
        s.append(txt(x0 - 8, py(f) + 3, f"{f:.0%}", size=9, fill=MUTED, anchor="end"))
        s.append(txt(px(f), py(0) + 18, f"{f:.0%}", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, AY - 18, "share reporting within three years", size=11, fill=INK2))
    s.append(txt(AX, py(0) + 36, "share reporting within one year — the statutory window",
                 size=10, fill=MUTED))
    s.append(f'<path d="M{px(0):.1f},{py(0):.1f} L{px(0.95):.1f},{py(0.95):.1f}" '
             f'fill="none" stroke="{MUTED}" stroke-width="1.1" stroke-dasharray="4 3"/>')
    for i, line in enumerate(("on this line, everyone who ever",
                              "reports does so within the year")):
        s += halo(px(0.60), py(0.76) + i * 11, line, size=9, fill=MUTED)

    pooled = share(win, 1095)
    pooled1 = share(win, 365)
    nmax = max(d["n"] for d in stats)
    area = lambda n: 4 + 26 * math.sqrt(n / nmax)
    for d in sorted(stats, key=lambda d: -d["n"]):
        col = GREEN if d["s3"] > 0.5 else (RED if d["s3"] < .2 else BLUE)
        cx, cy2, rr = px(d["s1"]), py(d["s3"]), area(d["n"])
        s.append(f'<circle cx="{cx:.1f}" cy="{cy2:.1f}" r="{rr:.1f}" fill="{col}" '
                 f'fill-opacity="0.20" stroke="{col}" stroke-width="1.5"/>')
        s.append(f'<circle cx="{cx:.1f}" cy="{cy2:.1f}" r="2" fill="{col}"/>')
        if d["k"] == "OTHER_GOV":
            # sits hard against the left edge; an end-anchored label falls off the plate
            s += halo(cx, cy2 + rr + 13, LABEL.get(d["k"], d["k"]), size=10, fill=col,
                      anchor="middle", weight="700")
            s += halo(cx, cy2 + rr + 24, f"{d['n']:,} trials", size=9, fill=MUTED,
                      anchor="middle")
        else:
            side = -1 if d["k"] == "INDUSTRY" else 1
            anc = "start" if side > 0 else "end"
            s += halo(cx + side * (rr + 7), cy2 + 3, LABEL.get(d["k"], d["k"]), size=10,
                      fill=col, anchor=anc, weight="700")
            s += halo(cx + side * (rr + 7), cy2 + 15, f"{d['n']:,} trials", size=9,
                      fill=MUTED, anchor=anc)
    s.append(f'<circle cx="{px(pooled1):.1f}" cy="{py(pooled):.1f}" r="5" fill="none" '
             f'stroke="{INK}" stroke-width="2"/>')
    s += halo(px(pooled1) + 10, py(pooled) - 8, f"pooled {pooled:.1%}", size=10, fill=INK,
              weight="700")

    by2 = AY + AH + 4
    s.append(txt(AX, by2, "a twenty-five-fold range, and the pooled figure describes nobody",
                 size=12.5, fill=INK, weight="600"))
    s += wrap(AX, by2 + 20,
              f"University, hospital and individual sponsors are "
              f"{max(stats, key=lambda d: d['n'])['n']:,} of {total:,} trials here — "
              f"{max(stats, key=lambda d: d['n'])['n']/total:.0%} — so the register-wide "
              f"{pooled:.1%} is mostly their rate, pulled up by a much smaller group "
              f"reporting three times as often. Every class sits well below the diagonal, so "
              f"reporting in years two and three is the norm everywhere, not the exception.",
              size=11, fill=INK2, chars=86, leading=15)

    # ---------- right: is the flat pooled line flat everywhere, or flat on average?
    BX, BY, BH, BW = 700, 168, 330, 472
    s.append(txt(BX, BY - 18, "each class's own three-year rate, by completion year",
                 size=11, fill=INK2))
    byc = collections.defaultdict(lambda: collections.defaultdict(list))
    for p_ in pop:
        byc[p_["sp"]][p_["pc"].year].append(p_)
    yrs = list(range(2010, 2023))
    hx0, hpw = BX + 42, BW - 168
    hpx = lambda y: hx0 + hpw * ((y - yrs[0]) / (yrs[-1] - yrs[0]))
    hpy = lambda f: BY + BH - 44 - (BH - 74) * f
    for f in (0, .25, .5, .75, 1.0):
        s.append(f'<line x1="{hx0:.1f}" y1="{hpy(f):.1f}" x2="{hpx(yrs[-1]):.1f}" '
                 f'y2="{hpy(f):.1f}" stroke="{GRID}"/>')
        s.append(txt(hx0 - 7, hpy(f) + 3, f"{f:.0%}", size=9, fill=MUTED, anchor="end"))
    for y in (2010, 2014, 2018, 2022):
        s.append(txt(hpx(y), hpy(0) + 17, str(y), size=9, fill=MUTED, anchor="middle"))
    s.append(txt(BX, hpy(0) + 34, "year the trial's primary completion fell", size=9.5,
                 fill=MUTED))
    moved = []
    for d in stats:
        pts, vals = [], []
        for y in yrs:
            v = share(byc[d["k"]].get(y, []), 1095)
            if v is not None:
                pts.append((hpx(y), hpy(v)))
                vals.append((y, v))
        if len(pts) < 6:
            continue
        col = GREEN if d["s3"] > 0.5 else (RED if d["s3"] < .2 else BLUE)
        s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a_:.1f},{b_:.1f}"
                                        for i, (a_, b_) in enumerate(pts))
                 + f'" fill="none" stroke="{col}" stroke-width="2.4"/>')
        s += halo(pts[-1][0] + 7, pts[-1][1] + 3, LABEL.get(d["k"], d["k"]).split(",")[0],
                  size=9.5, fill=col, weight="700")
        moved.append((d["k"], vals[0][1], vals[-1][1], (vals[-1][1] - vals[0][1]) * 100,
                      d["n"]))
    pool = [(hpx(y), hpy(share([p_ for p_ in pop if p_["pc"].year == y], 1095) or 0))
            for y in yrs]
    s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a_:.1f},{b_:.1f}"
                                    for i, (a_, b_) in enumerate(pool))
             + f'" fill="none" stroke="{INK}" stroke-width="2.6" stroke-dasharray="5 3"/>')
    s += halo(pool[-1][0] + 7, pool[-1][1] + 3, "pooled", size=9.5, fill=INK, weight="700")

    cy = BY + BH + 24
    s.append(txt(BX, cy, "the pooled line is flat because the flat group is most of it",
                 size=12, fill=INK, weight="600"))
    s += wrap(BX, cy + 18,
              "NIH gained about 43 points and industry about 10 across these cohorts, while "
              "university and hospital sponsors gained 3 and other government lost ground. "
              "The dashed pooled line barely moves because the group that did not improve is "
              "three quarters of the register. Figure 3's flat series is composition, not "
              "stasis — and reading it as \u201cnothing changed\u201d misses that the "
              "improvement is real and confined.",
              size=10.5, fill=INK2, chars=68, leading=14)

    fy = H - 24 - 14 * 3
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"ClinicalTrials.gov API v2, fetched 2026-09-22. Population as figure 3: "
              f"interventional, ACTUAL primary completion, not phase 1; here restricted to "
              f"completions 2015–2021 so every class has three years of follow-up, "
              f"{total:,} trials. `leadSponsorClass` names the *lead* sponsor only — a "
              f"university running an industry-funded trial files as OTHER — so this "
              f"separates who filed, not who paid, and the industry figure is a floor. "
              f"Classes with under 150 trials in the window are not drawn. Reporting means a "
              f"results submission date exists; non-reporters stay in every denominator.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    pooled {pooled:.1%} over {total:,}")
    for d in stats:
        print(f"    {d['k']:<12}{d['n']:>8,}  1y {d['s1']:.1%}  3y {d['s3']:.1%}  "
              f"spike {d['spike']:.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
