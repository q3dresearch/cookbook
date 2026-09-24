#!/usr/bin/env python3
"""Ten minutes of rest doubles a dataset's reuse, and it is the cheapest thing in the session.

    python3 chart-7-paradigm.py

One dot is one dataset, published 2019-2024, listing at least one paradigm. Split by whether
any of them is resting state.

**MRI: 7.8 downloads a year for task-only data against 17.7 where rest is present -- 2.28x,
p < 0.0001**, on 396 against 187 datasets. **EEG: 21.1 against 43.5, 2.06x, p = 0.006.** Two
strata, both significant, and a larger effect than modality or patient population.

**It is presence, not dose.** Splitting three ways inside MRI gives rest-only 19.0 and
rest-plus-task 17.5 -- indistinguishable -- against task-only 7.8. And the competing story,
that mixed datasets simply run more paradigms, fails on its own ground: among task-only
datasets the correlation between paradigm count and reuse is **+0.049, t = 1.27**. Adding a
sixth task buys nothing. Adding rest doubles it.

**It is not the lottery.** This archive is Gini 0.761 and its top 1% hold 26.5% of all
downloads, so a cell median can stand on one famous dataset. Dropping the two most-downloaded
from every cell moves MRI from 2.28x to 2.28x and EEG from 2.06x to 2.05x.

**Why it is prescriptive rather than merely true.** Resting state is the cheapest block in a
scanning session: no paradigm to design, no task to train, no behavioural pilot, no response
hardware. It is the one line of this recipe a lab can act on next week, and the cost side of
the comparison is near zero.

**The mechanism is inference and is labelled as such.** The plausible reading is that resting
data is analysis-agnostic -- anyone can ask their own question of it -- while task data only
ever answers the question its paradigm was built for. Nothing here measures that. The test is
citation *breadth* rather than count: if the reading is right, resting datasets are cited
across a wider range of topics, which needs an OpenAlex join and has not been run.

**What this plate cannot do.** MEG points the same way at 1.61x on eight datasets and does not
reach significance; iEEG has no resting cell at all. 202 datasets leave `tasksCompleted` empty
and are excluded rather than pooled, because a blank is a missing answer and not a claim that
no paradigm ran.
"""
import hashlib, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import modality, paradigm, plate                                         # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "7-paradigm.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
YLO, YHI = 0.3, 900.0
COLW, GAPIN, GAPOUT = 126, 24, 78


def jx(did, n):
    """Deterministic spread, widening only as far as the overlap needs. Python's hash() is
    salted per process and determinism.py exists because that shipped once."""
    h = int(hashlib.md5(did.encode()).hexdigest()[:8], 16)
    return ((h % 10000) / 10000.0 - 0.5) * COLW * min(0.82, 0.16 + 0.09 * math.sqrt(n))


def main():
    rs = paradigm.rows()
    st = paradigm.strata(rs)
    dose = paradigm.dose(rs)
    three = paradigm.threeway(rs)

    W, H = 1180, 880
    s = plate.open_svg(
        W, H, "Ten minutes of rest doubles a dataset's reuse, and it is the cheapest block "
              "in the session",
        subtitle=f"{len(rs):,} OpenNeuro datasets published {paradigm.LO}-{paradigm.HI} that "
                 f"listed a paradigm. One dot is one dataset, split by whether any of them "
                 f"is resting state.")
    fr, y0 = plate.frame(
        W, 86,
        who="a lab designing its next scanning session, or a funder writing a data-sharing "
            "condition that could ask for a resting block",
        decide="whether to add a resting run to a study built around a task",
        wrong="the two medians in a modality coincide, or the gap is really about running "
              "more paradigms rather than running rest")
    s += fr

    AX, AY, AH = 244, y0 + 50, 452
    ay = lambda v: (AY + AH - (AH - 36) * (math.log10(min(max(v, YLO), YHI))
                                           - math.log10(YLO))
                    / (math.log10(YHI) - math.log10(YLO)))
    right = AX + 2 * (2 * COLW + GAPIN) + GAPOUT
    for v in (1, 10, 100, 500):
        s.append(f'<line x1="{AX-14:.1f}" y1="{ay(v):.1f}" x2="{right:.1f}" '
                 f'y2="{ay(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(AX - 22, ay(v) + 3, f"{v:,}", size=9, fill=MUTED, anchor="end"))
    s.append(f'<text x="{AX-54}" y="{ay(YLO):.1f}" font-size="10" fill="{INK2}" '
             f'transform="rotate(-90 {AX-54} {ay(YLO):.1f})">'
             f'downloads per year since publication (log scale)</text>')

    x = AX
    for si, st_ in enumerate(st):
        pair = []
        for key, col, lab in (("task", SLATE, ("task only", "no resting run")),
                              ("rest", GREEN, ("contains rest", "alone or alongside"))):
            g = st_[key]
            med = st_["med_t"] if key == "task" else st_["med_r"]
            cx = x + COLW / 2
            for r in g:
                s.append(f'<circle cx="{cx + jx(r["id"], len(g)):.1f}" '
                         f'cy="{ay(r["dl_yr"]):.1f}" r="2.9" fill="{col}" '
                         f'fill-opacity="0.42" stroke="{col}" stroke-width="0.7" '
                         f'stroke-opacity="0.5"/>')
            s.append(f'<line x1="{x:.1f}" y1="{ay(med):.1f}" x2="{x+COLW:.1f}" '
                     f'y2="{ay(med):.1f}" stroke="{col}" stroke-width="2.8"/>')
            s += halo(cx, ay(med) - 10, f"{med:.1f}", size=12, fill=col, anchor="middle",
                      weight="700")
            s.append(txt(cx, ay(YLO) + 26, f"{len(g)}", size=16, fill=col, anchor="middle",
                         weight="700"))
            for li, line in enumerate(lab):
                s.append(txt(cx, ay(YLO) + 43 + li * 12, line, size=9.5, fill=col if li == 0
                             else MUTED, anchor="middle",
                             weight="700" if li == 0 else "normal"))
            pair.append((cx, ay(med)))
            x += COLW + (GAPIN if key == "task" else GAPOUT)
        (x1, y1), (x2, y2) = pair
        top = min(y1, y2) - 30
        s.append(f'<path d="M{x1:.1f},{y1-6:.1f} L{x1:.1f},{top:.1f} L{x2:.1f},{top:.1f} '
                 f'L{x2:.1f},{y2-6:.1f}" fill="none" stroke="{INK2}" stroke-width="1.1"/>')
        s += halo((x1 + x2) / 2, top - 8,
                  f"{st_['ratio']:.2f}x   p "
                  + ("< 0.0001" if st_["p"] < 0.0001 else f"= {st_['p']:.3f}"),
                  size=11.5, fill=INK, anchor="middle", weight="700")
        s += halo((x1 + x2) / 2, top - 26, modality.NICE.get(st_["mod"], st_["mod"]),
                  size=13, fill=INK, anchor="middle", weight="700")
        s += halo((x1 + x2) / 2, ay(YLO) + 72,
                  f"drop each cell's two biggest: {st_['robust']:.2f}x", size=9,
                  fill=MUTED, anchor="middle", weight="700")

    TX, ty = right + 34, AY - 4
    for head, body, col in (
            ("if you are designing a session",
             "Add a resting run. It needs no paradigm design, no task training, no "
             "behavioural pilot and no response hardware, and the datasets that have one "
             "are taken twice as often.", GREEN),
            ("it is presence, not dose",
             f"Rest-only {three['rest only']['med']:.1f} and rest-plus-task "
             f"{three['rest + task']['med']:.1f} are the same dataset as far as reuse is "
             f"concerned. Running a sixth task does nothing: paradigm count against reuse "
             f"is r = {dose['r']:+.3f}, t = {dose['t']:+.2f}.", INK2),
            ("it is not one famous dataset",
             f"This archive's top 1% hold 26.5% of all downloads, so cell medians get "
             f"checked. Dropping the two biggest from every cell leaves "
             f"{st[0]['robust']:.2f}x and {st[1]['robust']:.2f}x.", SLATE),
            ("the reason is inference, not measurement",
             "Resting data is plausibly analysis-agnostic while a task answers only its own "
             "question -- but nothing here measures that. The test is citation breadth, "
             "not count, and it needs a join that has not been run.", AMBER),
            ("where it does not hold",
             "MEG points the same way at 1.61x on eight datasets and misses significance. "
             "iEEG has no resting cell. 202 datasets leave the field empty and are "
             "excluded, not pooled.", RED)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        w = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=31, leading=12.5)
        s += w
        ty += 12.5 * len(w) + 14

    foot = (
        f"OpenNeuro GraphQL API, no key, fetched 2026-09-24; metadata.tasksCompleted, which "
        f"is free text -- 993 distinct values -- of which the only countable feature is "
        f"whether an entry mentions rest. Published {paradigm.LO}-{paradigm.HI}, at least a "
        f"year old. p from a seeded 20,000-draw permutation test on the difference in "
        f"medians. CAVEAT: a download is not a citation, and this compares datasets whose "
        f"depositors filled the field in.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for st_ in st:
        print(f"    {st_['mod']:<5} task {len(st_['task']):>4} @ {st_['med_t']:>5.1f}   "
              f"rest {len(st_['rest']):>3} @ {st_['med_r']:>5.1f}   {st_['ratio']:.2f}x  "
              f"p {st_['p']:.4f}  robust {st_['robust']:.2f}x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
