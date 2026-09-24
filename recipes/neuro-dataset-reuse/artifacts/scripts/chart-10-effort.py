#!/usr/bin/env python3
"""Two kinds of effort a depositor can spend after the data is collected, and what each returns.

    python3 chart-10-effort.py

Both panels put effort on the horizontal and its yield on the vertical, at the same scale, so
they can be read against each other.

**Taking longer to publish is associated with less reuse, not more.** Median downloads a year
by draft length: **17.7 same day, 20.8 at one to three days, then 16.4, 13.8, 13.6 and 8.2 for
drafts over a year.** The continuous fit is **-0.077 per log-decade of draft days at t =
-4.54** on 1,803 datasets, which is a hundredfold longer draft for roughly **30% fewer
downloads**. An earlier version of this plate called the delay "friction with no yield"; that
was too kind by a significant margin.

**Revising does nothing measurable to validity.** At exact snapshot counts the error rate runs
**31, 33, 41, 35, 38, 31, 48, 33%** and the fit is **+0.028 at t = +0.77** -- indistinguishable
from flat, and pointing the wrong way if anything. A dataset revised eight times is no more
likely to pass the validator than one nobody touched again.

**Neither panel is causal and the direction is arguable in both.** A dataset that languishes in
draft may be one whose author had already lost interest, which would produce this correlation
with no friction at all. A dataset that gets revised many times may be one that was messy to
begin with. What the plate establishes is that **neither kind of effort predicts the outcome
people spend it for**, which is enough to stop recommending either as a lever.

**Exact counts, not bands.** The previous version of this material binned revision spans five
ways and read a dip as two populations; the bin-free form refuted it. These points are exact
snapshot counts and the fits are on the continuous variable, so there is no bin choice left to
carry a story.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lifecycle, plate                                                  # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "10-effort.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"


def main():
    rs = lifecycle.rows()
    pay = lifecycle.payoff(rs)
    qly = lifecycle.quality(rs)

    W, H = 1180, 780
    s = plate.open_svg(
        W, H, "Two kinds of effort after the data is collected, and neither one pays",
        subtitle="Left: how long a dataset sat in draft, against how often it is taken. "
                 "Right: how many times it was revised, against whether it passes the "
                 "validator. Effort rises to the right in both.")
    fr, y0 = plate.frame(
        W, 86,
        who="a depositor deciding whether to polish before publishing or to keep revising "
            "after, and a repository deciding what to nudge people towards",
        decide="whether either kind of post-collection effort improves the outcome it is "
               "spent on",
        wrong="either fit is significant in the direction the effort intends")
    s += fr

    PW, PH, PY = 368, 330, y0 + 70
    for pi, (pts, fit, xlab, ylab, col, fmt, note) in enumerate((
            (pay["points"], pay["fit"], "days the dataset sat in draft",
             "median downloads a year", BLUE, lambda v: f"{v:.1f}",
             "more time spent, to the right"),
            (qly["points"], qly["fit"], "number of published snapshots",
             "share carrying a validator error", AMBER, lambda v: f"{v:.0%}",
             "more revision, to the right"))):
        PX = 248 + pi * (PW + 92)
        vals = [p["median"] if "median" in p else p["rate"] for p in pts]
        hi = max(vals) * 1.25
        bx = lambda i: PX + PW * i / (len(pts) - 1)
        by = lambda v: PY + PH - PH * v / hi
        for f in (0, .25, .5, .75, 1.0):
            s.append(f'<line x1="{PX-12:.1f}" y1="{by(hi*f):.1f}" x2="{PX+PW+12:.1f}" '
                     f'y2="{by(hi*f):.1f}" stroke="{GRID}"/>')
            s.append(txt(PX - 18, by(hi * f) + 3, fmt(hi * f), size=9, fill=MUTED,
                         anchor="end"))
        s.append(txt(PX - 18, PY - 16, ylab, size=10, fill=INK2))
        for i, p in enumerate(pts):
            v = p["median"] if "median" in p else p["rate"]
            s.append(f'<circle cx="{bx(i):.1f}" cy="{by(v):.1f}" r="5" fill="{col}" '
                     f'fill-opacity="0.5" stroke="{col}" stroke-width="1.6"/>')
            s += halo(bx(i), by(v) - 12, fmt(v), size=9.5, fill=col, anchor="middle",
                      weight="700")
            s.append(txt(bx(i), PY + PH + 18, str(p.get("label", p.get("k"))), size=9,
                         fill=MUTED, anchor="middle"))
            s.append(txt(bx(i), PY + PH + 31, f"n={p['n']}", size=8, fill=FAINT,
                         anchor="middle"))
        s.append('<polyline points="' + " ".join(
            f"{bx(i):.1f},{by(p['median'] if 'median' in p else p['rate']):.1f}"
            for i, p in enumerate(pts)) + f'" fill="none" stroke="{col}" '
            f'stroke-width="1.6" stroke-opacity="0.45"/>')
        s.append(txt(PX, PY + PH + 50, xlab, size=10, fill=INK2))
        s += halo(PX + PW, PY + PH + 50, note, size=9.5, fill=MUTED, anchor="end",
                  weight="700")
        sig = abs(fit["t"]) >= 2
        s += halo(PX + PW / 2, PY - 38,
                  f"slope {fit['slope']:+.3f}   t = {fit['t']:+.2f}   "
                  + ("SIGNIFICANT, and negative" if sig else "flat"),
                  size=11, fill=(RED if sig else INK2), anchor="middle", weight="700")

    TX, ty = 34, PY + 6
    for head, body, col in (
            ("polishing before you publish",
             f"A hundredfold longer draft predicts about 30% fewer downloads. Whatever the "
             f"wait is for, reuse is not it.", RED),
            ("revising after you publish",
             "The error rate does not move. Eight rounds leave a dataset as likely to fail "
             "as never touching it.", AMBER),
            ("neither is causal",
             "A languishing draft may mean an author who had already moved on. A "
             "much-revised dataset may have been messy to start with.", MUTED),
            ("but the advice survives either way",
             "Neither effort predicts the outcome it is spent on, which is enough to stop "
             "recommending it as a lever.", INK2)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        w = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=26, leading=12.5)
        s += w
        ty += 12.5 * len(w) + 14

    foot = (
        f"OpenNeuro GraphQL API, no key, fetched 2026-09-24; dataset.created, "
        f"dataset.publishDate, snapshot count and latestSnapshot.validation. Points are "
        f"exact snapshot counts on the right and draft-day bands on the left; both fits are "
        f"on the continuous variable, so no bin choice carries either result. CAVEAT: "
        f"observational, and the direction of causation is arguable in both panels.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    draft  slope {pay['fit']['slope']:+.4f}  t {pay['fit']['t']:+.2f}")
    print(f"    revise slope {qly['fit']['slope']:+.4f}  t {qly['fit']['t']:+.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
