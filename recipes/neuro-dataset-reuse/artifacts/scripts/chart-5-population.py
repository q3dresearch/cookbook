#!/usr/bin/env python3
"""Datasets that name a patient population are reused about twice as often, and there are far fewer of them.

    python3 chart-5-population.py

One dot is one dataset. The **count of dots** is how many exist; the **height of dots** is how
often they are taken. Read together they say where the archive is thin relative to what people
want, which is the only question in it a depositor can act on.

**Within MRI: 174 healthy-control datasets at a median 10.6 downloads a year against 23
patient-population datasets at 24.5 -- 2.31x, p = 0.010.** Within EEG the gap points the same
way, 26.3 against 52.5 for 2.00x, but on 14 datasets it does not reach significance at p =
0.061. One stratum confirms and one is consistent but underpowered; both are drawn, because
showing only the significant one would be choosing the result.

**The pooled figure is 3.18x and it is wrong to quote.** Patient datasets skew toward EEG and
iEEG, which are more reused whatever population they study, so pooling counts that composition
as if it were the effect. The within-modality number is about 2x and that is the claim.

**Era is matched at 2018-2023 and that matters a lot.** Downloads per year falls with a
dataset's age, and unmatched the MRI gap reads 4.83x instead of 2.31x. Half of the apparent
effect was the calendar.

**The free-text escape does not carry the result.** `dxStatus` offers a dropdown and lets a
depositor type instead, and three typed answers name no clinical arm at all -- "healthy/control,
gifted children", "control vs dark reared" and "intracranial data". They are left in, because
picking which free text to drop after seeing the result is how a finding gets manufactured.
Removing them moves the pooled ratio from 3.18x to **3.35x**, so they were working against the
finding rather than producing it.

**What it does not show.** A patient cohort is harder and costlier to recruit, so this is not
free money; figure 2 puts the median NIH-funded dataset at $3.1m before any clinical
recruitment. Nor is the direction established: a lab that can recruit patients may also be a
lab that promotes its data. And `dxStatus` is a dropdown with a free-text escape, answered by
only a third of the archive, so this compares the datasets that answered.
"""
import collections, hashlib, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import modality, plate, population                                       # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "5-population.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
YLO, YHI = 0.4, 700.0
CW, GAPIN, GAPOUT = 118, 22, 74     # column width, within-pair gap, between-modality gap


def jitter(did, span):
    """Deterministic horizontal offset. Python's hash() is salted per process and would make
    the figure non-reproducible; determinism.py exists because that has happened here."""
    h = int(hashlib.md5(did.encode()).hexdigest()[:8], 16)
    return ((h % 10000) / 10000.0 - 0.5) * span


def main():
    rs = population.rows()
    st = population.strata(rs)

    W, H = 1180, 900
    s = plate.open_svg(
        W, H, "Datasets that name a patient population are reused about twice as often, and "
              "there are far fewer of them",
        subtitle=f"OpenNeuro datasets published {population.LO}-{population.HI} that answered "
                 f"dxStatus, at least a year old. One dot is one dataset. Count is supply; "
                 f"height is reuse.")
    fr, y0 = plate.frame(
        W, 86,
        who="a lab choosing what to collect next, or a funder deciding where a sharing "
            "mandate buys the most reuse",
        decide="whether the archive is short of patient data relative to demand for it",
        wrong="the two columns in a modality have the same median, or the gap disappears "
              "once age is matched")
    s += fr

    AX, AY, AH = 250, y0 + 54, 500
    ay = lambda v: (AY + AH - (AH - 40) * (math.log10(min(max(v, YLO), YHI))
                                           - math.log10(YLO))
                    / (math.log10(YHI) - math.log10(YLO)))
    for v in (1, 10, 100, 500):
        s.append(f'<line x1="{AX-14:.1f}" y1="{ay(v):.1f}" x2="{AX+620:.1f}" '
                 f'y2="{ay(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(AX - 22, ay(v) + 3, f"{v:,}", size=9, fill=MUTED, anchor="end"))
    s.append(f'<text x="{AX-52}" y="{ay(YLO):.1f}" font-size="10" fill="{INK2}" '
             f'transform="rotate(-90 {AX-52} {ay(YLO):.1f})">'
             f'downloads per year since publication (log scale)</text>')

    x = AX
    for si, st_ in enumerate(st):
        pair = []
        for grp, col, lab in (("control", SLATE, ("healthy /", "control")),
                              ("named", RED, ("names a patient", "population"))):
            g = st_["control"] if grp == "control" else st_["named"]
            med = st_["med_c"] if grp == "control" else st_["med_n"]
            cx = x + CW / 2
            for r in g:
                s.append(f'<circle cx="{cx + jitter(r["id"], CW * 0.74):.1f}" '
                         f'cy="{ay(r["dl_yr"]):.1f}" r="2.9" fill="{col}" '
                         f'fill-opacity="0.42" stroke="{col}" stroke-width="0.7" '
                         f'stroke-opacity="0.5"/>')
            s.append(f'<line x1="{x:.1f}" y1="{ay(med):.1f}" x2="{x+CW:.1f}" '
                     f'y2="{ay(med):.1f}" stroke="{col}" stroke-width="2.6"/>')
            s += halo(cx, ay(med) - 9, f"{med:.1f}", size=11, fill=col, anchor="middle",
                      weight="700")
            s.append(txt(cx, ay(YLO) + 20, f"{len(g)}", size=15, fill=col, anchor="middle",
                         weight="700"))
            for li, line in enumerate(lab):     # plate.wrap has no anchor; keep the
                s.append(txt(cx, ay(YLO) + 36 + li * 12, line,   # shared module unforked
                             size=9.5, fill=col, anchor="middle"))
            pair.append((cx, ay(med)))
            x += CW + (GAPIN if grp == "control" else GAPOUT)
        # the bracket carries the ratio, so the claim is drawn between the two medians
        (x1, y1), (x2, y2) = pair
        top = min(y1, y2) - 26
        s.append(f'<path d="M{x1:.1f},{y1-5:.1f} L{x1:.1f},{top:.1f} L{x2:.1f},{top:.1f} '
                 f'L{x2:.1f},{y2-5:.1f}" fill="none" stroke="{INK2}" stroke-width="1.1"/>')
        sig = "" if st_["p"] < 0.05 else "  (not significant)"
        s += halo((x1 + x2) / 2, top - 7,
                  f"{st_['ratio']:.2f}x   p = {st_['p']:.3f}{sig}", size=11,
                  fill=INK if st_["p"] < 0.05 else MUTED, anchor="middle", weight="700")
        s += halo((x1 + x2) / 2, top - 24, modality.NICE.get(st_["mod"], st_["mod"]),
                  size=13, fill=INK, anchor="middle", weight="700")
        s += halo((x1 + x2) / 2, ay(YLO) + 66,
                  f"{len(st_['control'])/len(st_['named']):.1f} control datasets for "
                  f"every 1 that names a population", size=9.5, fill=INK2, anchor="middle",
                  weight="700")

    a = [r["dl_yr"] for r in rs if r["grp"] == "control"]
    b = [r["dl_yr"] for r in rs if r["grp"] == "named"]
    pooled = statistics.median(b) / statistics.median(a)
    TX, ty = AX + 660, AY + 8
    for head, body, col in (
            ("why not pool them", f"Pooled across modalities the gap is {pooled:.2f}x, but "
                                  f"patient datasets skew toward EEG and iEEG, which are "
                                  f"more reused whatever they study. That is composition, "
                                  f"not effect.", AMBER),
            ("why the window", "Reuse front-loads, so an older dataset shows a lower rate. "
                               "Unmatched, MRI reads 4.83x instead of 2.31x -- half the "
                               "apparent effect was age.", INK2),
            ("one confirms, one cannot",
             "MRI clears p = 0.05 on 23 patient datasets. EEG points the same way on 14 and "
             "does not. Both are drawn.", SLATE),
            ("not a recommendation to spend",
             "A patient cohort costs more to recruit and this says nothing about that. It "
             "says the archive is thin where reuse is highest.", MUTED)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        w = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=32, leading=12.5)
        s += w
        ty += 12.5 * len(w) + 16

    foot = (
        f"OpenNeuro GraphQL API, no key, fetched 2026-09-24; metadata.dxStatus. CONTROL is "
        f"exactly the dropdown value \"healthy / control\"; NAMED is any other non-blank "
        f"answer. p from a seeded 20,000-draw permutation test on the difference in medians. "
        f"CAVEAT: dxStatus is answered by about a third of the archive and its free-text "
        f"escape is not a controlled vocabulary, so this compares the datasets that "
        f"answered. Nothing here establishes direction.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for st_ in st:
        print(f"    {st_['mod']:<6} ctrl {len(st_['control']):>4} @ {st_['med_c']:>6.1f}   "
              f"named {len(st_['named']):>3} @ {st_['med_n']:>6.1f}   "
              f"{st_['ratio']:.2f}x  p {st_['p']:.4f}")
    print(f"    pooled {pooled:.2f}x (composition-inflated, not quoted)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
