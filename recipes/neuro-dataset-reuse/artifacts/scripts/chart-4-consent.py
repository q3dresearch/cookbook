#!/usr/bin/env python3
"""Nine in ten depositors remove the face, and it costs them nothing in reuse.

    python3 chart-4-consent.py

A structural MRI is a photograph of a face, and a depositor has two ways to publish one: remove
the face, or keep it and record that the participants agreed to that. **Either alone discharges
the obligation.** Reading the consent field by itself is a trap -- it is false on 646 of 795
datasets, which looks like mass non-compliance and is mostly the stricter answer.

**The question this plate exists to answer is what the control costs.** The standing objection
to mandatory defacing is that the algorithm damages the image and suppresses reuse. It does
not: **13.4 downloads a year for defaced datasets against 13.0 for undefaced ones, p = 0.90**,
and matching on era moves it to 13.1 against 13.0. A repository can require defacing without
paying for it.

**A null needs the size it could have seen.** On 528 against 40 datasets this design catches a
2.00x gap 85% of the time and a 1.75x gap 76% of the time, but only half of a 1.50x gap. So the
claim is that defacing costs nothing *large*, not that it costs nothing at all.

**What it cannot see, and this is the important limit.** A dataset that was never deposited
because of the requirement is not in this archive, by construction. MRI deposits did fall from
153 in 2020 to 101 and 81 in 2021-2022 before recovering to 152, 152 and 175 -- but in-person
scanning stopped in those years for reasons that had nothing to do with consent forms, and
nothing here separates the two. **This plate measures what the control costs the datasets that
were published. It is structurally blind to the ones that were not.**

**Eight datasets record neither answer** and that is the whole audit list. All eight were
published between 2020 and 2022, when the questions were new, and none since. These are
depositor assertions rather than inspections: an unticked box is not proof a face is visible.
"""
import math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import consent, plate                                                    # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "4-consent.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
YLO, YHI = 0.4, 900.0
COLW, GAP = 168, 96
SPEC = (("defaced", GREEN, ("the face is removed", "affirmedDefaced")),
        ("consent", BLUE, ("the face is kept, with", "recorded consent")),
        ("neither", RED, ("neither recorded", "the audit list")))


def jx(did, span):
    """Deterministic spread; Python's hash() is salted per process and would break rebuilds."""
    import hashlib
    h = int(hashlib.md5(did.encode()).hexdigest()[:8], 16)
    return ((h % 10000) / 10000.0 - 0.5) * span


def spread(n):
    """Jitter is anti-overlap, not a quantity, so it scales with how much overlap there is.
    Eight dots thrown across a full column read as scatter; the count is the message."""
    return COLW * min(0.8, 0.14 + 0.09 * math.sqrt(n))


def main():
    rs = consent.rows()
    by = {k: [r for r in rs if r["route"] == k] for k, _, _ in SPEC}
    rated = {k: [r for r in v if r["rated"]] for k, v in by.items()}
    med = {k: statistics.median(r["dl_yr"] for r in v) if v else None
           for k, v in rated.items()}
    a = [r["dl_yr"] for r in rated["defaced"]]
    b = [r["dl_yr"] for r in rated["consent"]]
    _, p = consent.perm(a, b)
    pw = consent.detectable(a, b)

    W, H = 1180, 900
    s = plate.open_svg(
        W, H, "Nine in ten depositors remove the face, and it costs them nothing in reuse",
        subtitle=f"{len(rs):,} OpenNeuro datasets carrying structural MRI that answered "
                 f"either question. One dot is one dataset. Column width is the choice "
                 f"made; height is how often the result gets taken.")
    fr, y0 = plate.frame(
        W, 86,
        who="a repository writing a deposit policy for identifiable imaging, or a funder "
            "deciding whether to mandate defacing",
        decide="whether requiring defacing suppresses reuse, and which datasets need a human",
        wrong="the two medians differ by more than the design can detect, or a route is "
              "chosen for reasons this archive can see")
    s += fr

    AX, AY, AH = 232, y0 + 46, 448
    ay = lambda v: (AY + AH - (AH - 34) * (math.log10(min(max(v, YLO), YHI))
                                           - math.log10(YLO))
                    / (math.log10(YHI) - math.log10(YLO)))
    GUT = ay(YLO) + 40                       # rateless datasets, off the scale
    for v in (1, 10, 100, 500):
        s.append(f'<line x1="{AX-14:.1f}" y1="{ay(v):.1f}" '
                 f'x2="{AX + 3*COLW + 2*GAP + 14:.1f}" y2="{ay(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(AX - 22, ay(v) + 3, f"{v:,}", size=9, fill=MUTED, anchor="end"))
    s.append(f'<text x="{AX-54}" y="{ay(YLO):.1f}" font-size="10" fill="{INK2}" '
             f'transform="rotate(-90 {AX-54} {ay(YLO):.1f})">'
             f'downloads per year since publication (log scale)</text>')
    s.append(f'<line x1="{AX-14:.1f}" y1="{GUT-16:.1f}" '
             f'x2="{AX + 3*COLW + 2*GAP + 14:.1f}" y2="{GUT-16:.1f}" stroke="{MUTED}" '
             f'stroke-width="1" stroke-dasharray="4 4" stroke-opacity="0.5"/>')
    s += halo(AX - 22, GUT + 4, "under a year old", size=9, fill=MUTED, anchor="end")

    cx_of = {}
    for i, (k, col, lab) in enumerate(SPEC):
        x = AX + i * (COLW + GAP)
        cx = x + COLW / 2
        cx_of[k] = cx
        for r in by[k]:
            y = ay(r["dl_yr"]) if r["rated"] else GUT + 4
            s.append(f'<circle cx="{cx + jx(r["id"], spread(len(by[k]))):.1f}" cy="{y:.1f}" r="2.9" '
                     f'fill="{col}" fill-opacity="0.42" stroke="{col}" stroke-width="0.7" '
                     f'stroke-opacity="0.5"/>')
        if med[k] is not None:
            s.append(f'<line x1="{x:.1f}" y1="{ay(med[k]):.1f}" x2="{x+COLW:.1f}" '
                     f'y2="{ay(med[k]):.1f}" stroke="{col}" stroke-width="2.8"/>')
            s += halo(cx, ay(med[k]) - 10, f"{med[k]:.1f}", size=12, fill=col,
                      anchor="middle", weight="700")
        s.append(txt(cx, GUT + 44, f"{len(by[k]):,}", size=17, fill=col, anchor="middle",
                     weight="700"))
        s.append(txt(cx, GUT + 60, f"{len(by[k])/len(rs):.0%} of depositors", size=9.5,
                     fill=col, anchor="middle", weight="700"))
        for li, line in enumerate(lab):
            s.append(txt(cx, GUT + 78 + li * 12, line, size=9.5, fill=MUTED,
                         anchor="middle"))

    # the claim is the absence of a gap, so it gets drawn between the two medians
    x1, x2 = cx_of["defaced"], cx_of["consent"]
    top = min(ay(med["defaced"]), ay(med["consent"])) - 34
    s.append(f'<path d="M{x1:.1f},{ay(med["defaced"])-6:.1f} L{x1:.1f},{top:.1f} '
             f'L{x2:.1f},{top:.1f} L{x2:.1f},{ay(med["consent"])-6:.1f}" fill="none" '
             f'stroke="{INK2}" stroke-width="1.1"/>')
    s += halo((x1 + x2) / 2, top - 8,
              f"no difference:  {statistics.median(b)/statistics.median(a):.2f}x,  "
              f"p = {p:.2f}", size=12, fill=INK, anchor="middle", weight="700")
    ids = sorted(r["id"] for r in by["neither"])
    for li in range(0, len(ids), 4):        # parked above the gutter, clear of every dot
        s += halo(cx_of["neither"], GUT - 44 + (li // 4) * 12, ", ".join(ids[li:li + 4]),
                  size=8.5, fill=RED, anchor="middle", weight="700")

    TX, ty = AX + 3 * COLW + 2 * GAP + 40, AY - 6
    for head, body, col in (
            ("if you are writing a deposit policy",
             f"You can require defacing. The standing objection -- that the algorithm "
             f"damages the image and nobody reuses it -- does not appear at "
             f"{statistics.median(b)/statistics.median(a):.2f}x and p = {p:.2f}.", GREEN),
            ("how big a cost this could have missed",
             f"It catches a 2x gap {pw[2.0]:.0%} of the time and a 1.75x gap "
             f"{pw[1.75]:.0%}, but only {pw[1.5]:.0%} of a 1.5x gap. Read it as "
             f"\"no large cost\", not \"no cost\".", AMBER),
            ("what it is structurally blind to",
             "A dataset withheld because of the requirement never enters this archive. "
             "MRI deposits did dip in 2021-22, but in-person scanning stopped then for "
             "unrelated reasons and nothing here separates the two.", SLATE),
            ("if you are auditing",
             f"{len(by['neither'])} datasets, named on the plate, all published 2020-2022 "
             f"when the questions were new and none since. That is the whole list, and it "
             f"is short enough to open every one.", RED),
            ("why the middle column exists",
             f"{len(by['consent'])} datasets need the face -- craniofacial work, some "
             f"registration. It is a real minority route and it is not penalised.", BLUE)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        w = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=31, leading=12.5)
        s += w
        ty += 12.5 * len(w) + 14

    foot = (
        "OpenNeuro GraphQL API, no key, fetched 2026-09-24; metadata.affirmedDefaced and "
        "metadata.affirmedConsent, restricted to datasets whose modality resolves to MRI. "
        "Question wording is OpenNeuro's own. 377 further MRI datasets answered neither "
        "question because both fields postdate them, and are excluded rather than counted as "
        "refusals. p from a seeded 20,000-draw permutation test on the difference in medians. "
        "CAVEAT: these are depositor assertions, not inspections of the images.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for k, _, _ in SPEC:
        print(f"    {k:<9}{len(by[k]):>5} ({len(by[k])/len(rs):>4.0%})  rated "
              f"{len(rated[k]):>4}  median "
              + (f"{med[k]:.1f}" if med[k] is not None else "-"))
    print(f"    defaced vs consent p {p:.4f}; detects 2x at {pw[2.0]:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
