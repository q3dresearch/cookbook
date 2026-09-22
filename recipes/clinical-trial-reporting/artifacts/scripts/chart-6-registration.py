#!/usr/bin/env python3
"""Two duties, one failure. A trial registered late is a trial that will not report.

    python3 chart-6-registration.py

Registration and results are separate obligations with separate deadlines. ICMJE has required
registration **before the first participant** since 2005, as a condition of publication;
FDAAA requires it within 21 days of first enrolment. Results are a different clock entirely.

**A fifth of trials are registered after they have already finished.** Measured against the
primary completion date: **18-23% of every completion cohort since 2008**, with a tenth of all
trials registered more than **385 days** after the work ended. The rate has not fallen —
23.6% for 2008 completions, 18.1% for 2020, 22.6% for 2024. Twenty years of a journal policy
that was supposed to make this unpublishable has not moved it.

**And it predicts the other failure, inside every sponsor class.** Trials registered
prospectively report within three years far more often than trials registered after the fact:
industry **51.1% against 17.2%**, university and hospital **20.8% against 4.2%**, other
government 4.5% against 2.4%. The gap is threefold to fivefold and it survives holding the
sponsor class fixed, so it is **not the class effect from figure 4 in disguise**.

**Which means these are not two independent obligations being missed independently.** The same
trials fail both. Whatever the register is measuring here — administrative capacity, or
intent, or whether anyone is left on the project — it is one thing with two symptoms, and a
policy aimed at either one alone is aimed at half of it.

**What this cannot establish.** Direction. A trial registered late may report less because the
same team is absent from both, or because retrospective registration marks a study that was
never meant to be public. Nothing here separates those, and the register carries no field that
would.

**One boundary on the measurement.** "Retrospective" here means registered after the primary
completion date, which is stricter than the statute (21 days after first enrolment) and looser
than ICMJE (before the first participant). It is the version these two fields support.
"""
import collections, csv, datetime, gzip, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                            # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID         # noqa: E402

ROWS = os.path.join(HERE, "..", "data", "studies.csv.gz")
OUT = os.path.join(HERE, "..", "charts", "6-registration.svg")
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
        if not pc or not fp or pc > TODAY:
            continue
        rs = parse(r["results_submit"])
        base.append({"pc": pc, "pro": fp <= pc, "gap": (pc - fp).days,
                     "lag": (rs - pc).days if rs else None, "fu": (TODAY - pc).days,
                     "sp": r["sponsor_class"] or "?"})

    def share(P, t=1095, floor=150):
        ar = [p for p in P if p["fu"] >= t]
        if len(ar) < floor:
            return None, len(ar)
        return sum(1 for p in ar if p["lag"] is not None and p["lag"] <= t) / len(ar), len(ar)

    W, H = 1200, 720
    s = plate.open_svg(W, H, "Two duties, one failure")
    fr, _ = plate.frame(W, 62,
                        who="anyone treating registration and reporting as separate problems",
                        decide="whether one policy lever reaches both",
                        wrong="the prospective and retrospective bars match inside a class")
    s += fr

    # ---------- left: the rate, flat for seventeen years
    AX, AY, AH, AW = 28, 168, 400, 560
    byy = collections.defaultdict(list)
    for p in base:
        byy[p["pc"].year].append(p)
    yrs = [y for y in range(2008, 2025) if len(byy[y]) > 2000]
    x0, pw = AX + 46, AW - 92
    px = lambda y: x0 + pw * ((y - yrs[0]) / (yrs[-1] - yrs[0]))
    py = lambda f: AY + AH - 54 - (AH - 88) * (f / 0.32)
    for f in (0, .1, .2, .3):
        s.append(f'<line x1="{x0:.1f}" y1="{py(f):.1f}" x2="{px(yrs[-1]):.1f}" '
                 f'y2="{py(f):.1f}" stroke="{GRID}"/>')
        s.append(txt(x0 - 8, py(f) + 3, f"{f:.0%}", size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, AY - 18, "share of the cohort registered after it had already finished",
                 size=11, fill=INK2))
    for y in range(2010, 2025, 5):
        s.append(txt(px(y), py(0) + 18, str(y), size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, py(0) + 36, "year the trial's primary completion fell", size=10,
                 fill=MUTED))
    pts = [(px(y), py(sum(1 for p in byy[y] if not p["pro"]) / len(byy[y]))) for y in yrs]
    s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                    for i, (a, b) in enumerate(pts))
             + f'" fill="none" stroke="{RED}" stroke-width="2.6"/>')
    for a, b in pts:
        s.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3" fill="{RED}"/>')
    lo = min(sum(1 for p in byy[y] if not p["pro"]) / len(byy[y]) for y in yrs)
    hi = max(sum(1 for p in byy[y] if not p["pro"]) / len(byy[y]) for y in yrs)
    s += halo(px(yrs[0]) + 6, py(hi) - 10, f"never leaves the {lo:.0%}–{hi:.0%} band",
              size=10.5, fill=RED, weight="700")
    s += halo(px(yrs[0]) + 6, py(hi) + 2, "in seventeen years", size=10.5, fill=RED,
              weight="700")
    ly = py(0) + 54
    s += wrap(AX, ly,
              "ICMJE has required registration before the first participant since 2005, as a "
              "condition of publication. A tenth of all trials are registered more than 385 "
              "days after the work ended. The policy is twenty years old and the rate has not "
              "moved.",
              size=11, fill=INK2, chars=76, leading=15)

    # ---------- right: and it predicts the other failure, within class
    BX, BY, BW = 660, 168, 512
    s.append(txt(BX, BY - 18, "share reporting within three years, split by whether the "
                              "trial was registered before it finished", size=11, fill=INK2))
    rows_out = []
    for k in ("INDUSTRY", "OTHER", "OTHER_GOV", "NIH", "FED"):
        P = [p for p in base if p["sp"] == k and 2012 <= p["pc"].year <= 2021]
        a, na = share([p for p in P if p["pro"]])
        b, nb = share([p for p in P if not p["pro"]])
        if a is None or b is None:
            continue
        rows_out.append((k, a, na, b, nb))
    rows_out.sort(key=lambda r: -r[1])
    bx0, bpw = BX + 4, BW - 150
    bpx = lambda f: bx0 + bpw * (f / 0.60)
    axis_y = BY + 62 * len(rows_out)
    for f in (0, .2, .4, .6):
        s.append(f'<line x1="{bpx(f):.1f}" y1="{BY+6:.1f}" x2="{bpx(f):.1f}" '
                 f'y2="{axis_y:.1f}" stroke="{GRID}"/>')
        s.append(txt(bpx(f), axis_y + 15, f"{f:.0%}", size=9, fill=MUTED, anchor="middle"))
    for i, (k, a, na, b, nb) in enumerate(rows_out):
        y = BY + 24 + i * 62
        s.append(txt(BX, y - 12, LABEL.get(k, k), size=10.5, fill=INK, weight="600"))
        s.append(f'<line x1="{bpx(b):.1f}" y1="{y+8:.1f}" x2="{bpx(a):.1f}" '
                 f'y2="{y+8:.1f}" stroke="{SLATE}" stroke-width="1.6"/>')
        s.append(f'<circle cx="{bpx(b):.1f}" cy="{y+8:.1f}" r="5.5" fill="{RED}"/>')
        s.append(f'<circle cx="{bpx(a):.1f}" cy="{y+8:.1f}" r="5.5" fill="{GREEN}"/>')
        s += halo(bpx(a) + 9, y + 12, f"{a:.1%}", size=10.5, fill=GREEN, weight="700")
        s += halo(bpx(b) - 9, y + 12, f"{b:.1%}", size=10.5, fill=RED, anchor="end",
                  weight="700")
        s += halo(bpx(max(a, b)) + 58, y + 12, f"{a/b:.1f}x", size=10, fill=INK2,
                  weight="700")
        s.append(txt(BX, y + 24, f"{na:,} prospective · {nb:,} retrospective", size=9,
                     fill=MUTED))
    ly2 = axis_y + 38
    s.append(f'<circle cx="{BX+5:.1f}" cy="{ly2-4:.1f}" r="4.5" fill="{GREEN}"/>')
    s.append(txt(BX + 16, ly2, "registered before it finished", size=10, fill=INK2))
    s.append(f'<circle cx="{BX+215:.1f}" cy="{ly2-4:.1f}" r="4.5" fill="{RED}"/>')
    s.append(txt(BX + 226, ly2, "registered after", size=10, fill=INK2))
    s += wrap(BX, ly2 + 20,
              "The gap holds inside every class, so it is not the sponsor effect from figure "
              "2 in disguise. The same trials miss both duties — one thing with two symptoms, "
              "and a policy aimed at either alone is aimed at half of it. Direction is not "
              "established: nothing here says which failure causes the other, or whether both "
              "follow from a third thing the register does not record.",
              size=10.5, fill=INK2, chars=68, leading=14)

    fy = H - 24 - 14 * 3
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"ClinicalTrials.gov API v2, fetched 2026-09-22. Population as figure 3: "
              f"interventional, ACTUAL primary completion, not phase 1 — {len(base):,} "
              f"studies with both a first-posted date and a completion date. "
              f"“Retrospective” means first posted to the register after the primary "
              f"completion date: stricter than FDAAA, which allows 21 days after first "
              f"enrolment, and looser than ICMJE, which requires registration before the "
              f"first participant. It is the version these two fields support. Right panel is "
              f"completions 2012–2021 so every cell has three years of follow-up; classes "
              f"with under 150 trials on either side are not drawn, which is why NIH's "
              f"retrospective arm is absent — it has 30.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    retrospective band {lo:.1%}–{hi:.1%} across {len(yrs)} cohorts")
    for k, a, na, b, nb in rows_out:
        print(f"    {k:<12}prospective {a:.1%} (n={na:,})   retrospective {b:.1%} "
              f"(n={nb:,})   {a/b:.1f}x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
