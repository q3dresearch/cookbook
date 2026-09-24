#!/usr/bin/env python3
"""The archive's BIDS error rate did not fall. The validator changed.

    python3 chart-3-validator.py

Three lines. Two are flat and one collapses, and the collapsing one is the only one anybody
would have drawn.

**Pooled, the error rate falls from 45% of 2023 deposits to 3% of 2026** -- which reads as a
standard being adopted. Split by the validator that produced the verdict, **v1 sits at 54-70%
and v2 at 1-18%, and neither moves.** What moved is the mix: v2's share of runs went 36% to
99%. The fall is composition.

**The control is the whole argument.** Hold the validator at v1 and move the year instead:
**2024 54%, 2025 70%.** On a fixed instrument the error rate went *up*.

**And v2 is not merely quieter.** Its median warning count is **3,523 against v1's 2,851**, so
it reclassifies errors as warnings rather than failing to see them. An "error" is a different
object in the two versions, and no arithmetic on this field spans them.

**This plate replaces one that was wrong for a different reason.** The first version read
`issuesStatus`, which is deprecated and populated on 57% of datasets, and called that missing
57% a collapse in *coverage* -- an 819-dataset backlog that does not exist. The live field
`validation` is populated on **1,893 of 1,893**. Both plates are in `artifacts/superseded/`
with the full account.

**What this cannot tell you.** Whether BIDS compliance actually improved. It did not improve
*here*, but 803 datasets carry no version stamp at all -- `validatorMetadata` only arrives
with newer runs -- and their 54% error rate merely resembles v1's 55%. The honest claim is
that this archive cannot support a compliance trend, not that the field failed to improve.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bidsvalid, plate                                                  # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "3-validator.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"


def main():
    rs = bidsvalid.rows()
    ser = bidsvalid.series(rs)
    pg = bidsvalid.pooled_by_gen(rs)
    ctl = bidsvalid.held_fixed(rs)
    gap = bidsvalid.deprecated_field_gap(rs)
    years = [c["year"] for c in ser]

    W, H = 1180, 880
    s = plate.open_svg(
        W, H, "The archive's BIDS error rate did not fall — the validator changed",
        subtitle=f"{sum(c['n'] for c in ser):,} datasets published {years[0]}-{years[-1]}, "
                 f"from the live validation field. The pooled line is the one anyone would "
                 f"draw. The two it sits between are what actually happened.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone about to report that a data standard is being adopted, or to compare "
            "validator output across years",
        decide="whether this archive can support a compliance trend at all",
        wrong="the two version lines converge, or holding the validator fixed still shows "
              "the rate falling")
    s += fr

    AX, AY, AW, AH = 268, y0 + 60, 560, 430
    px = lambda i: AX + AW * i / (len(years) - 1)
    ay = lambda v: AY + AH - AH * v
    for v in (0, .25, .5, .75, 1.0):
        s.append(f'<line x1="{AX-10:.1f}" y1="{ay(v):.1f}" x2="{AX+AW+10:.1f}" '
                 f'y2="{ay(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(AX - 18, ay(v) + 3, f"{v*100:.0f}%", size=9.5, fill=MUTED, anchor="end"))
    for i, y in enumerate(years):
        s.append(txt(px(i), ay(0) + 34, str(y), size=10.5, fill=MUTED, anchor="middle"))
        s.append(txt(px(i), ay(0) + 48, f"{ser[i]['n']} deposits", size=8.5, fill=FAINT,
                     anchor="middle"))
    s.append(txt(AX - 18, ay(1.0) - 16, "share of that year's datasets whose validator "
                                        "reported at least one error", size=10, fill=INK2))

    for key, col, lab in (("v1", RED, "checked by validator v1"),
                          ("v2+", GREEN, "checked by v2 or later")):
        pts = [(i, ser[i][key]["rate"]) for i in range(len(ser))
               if ser[i][key]["n"] >= bidsvalid.MIN_N]
        s.append('<polyline points="' + " ".join(f"{px(i):.1f},{ay(v):.1f}" for i, v in pts)
                 + f'" fill="none" stroke="{col}" stroke-width="2.8"/>')
        for i, v in pts:
            s.append(f'<circle cx="{px(i):.1f}" cy="{ay(v):.1f}" r="4.2" fill="{col}"/>')
            s += halo(px(i), ay(v) - 11, f"{v:.0%}", size=10, fill=col, anchor="middle",
                      weight="700")
            # below the point always; the year axis was moved down to make room
            s += halo(px(i), ay(v) + 17, f"n={ser[i][key]['n']}", size=8.5, fill=MUTED,
                      anchor="middle")
        li, lv = pts[0]
        s += halo(px(li) - 14, ay(lv) + 4, lab, size=10.5, fill=col, anchor="end",
                  weight="700")
    pts = [(i, ser[i]["pooled"]) for i in range(len(ser))]
    s.append('<polyline points="' + " ".join(f"{px(i):.1f},{ay(v):.1f}" for i, v in pts)
             + f'" fill="none" stroke="{INK}" stroke-width="2.2" stroke-dasharray="6 4"/>')
    for i, v in pts:
        s.append(f'<circle cx="{px(i):.1f}" cy="{ay(v):.1f}" r="3.6" fill="none" '
                 f'stroke="{INK}" stroke-width="1.8"/>')
    s += halo(px(0) + 14, ay(ser[0]["pooled"]) - 22,
              "pooled — the line anyone would have drawn", size=10.5, fill=INK,
              weight="700")
    for i, v in ((0, ser[0]["pooled"]), (len(ser) - 1, ser[-1]["pooled"])):
        s += halo(px(i) + (14 if i == 0 else -12), ay(v) - 8, f"{v:.0%}", size=10,
                  fill=INK, weight="700", anchor="start" if i == 0 else "end")

    SY = ay(0) + 76
    s.append(txt(AX - 18, SY - 10, "share of that year's stamped runs done by v2 or later — "
                                   "this is what moved", size=10, fill=INK2, weight="700"))
    bw = AW / len(years) * 0.78
    for i, c in enumerate(ser):
        x0 = px(i) - bw / 2                    # centred on the year it describes
        s.append(f'<rect x="{x0:.1f}" y="{SY:.1f}" width="{bw:.1f}" height="34" '
                 f'fill="{GRID}"/>')
        s.append(f'<rect x="{x0:.1f}" y="{SY:.1f}" width="{bw*c["share"]:.1f}" '
                 f'height="34" fill="{GREEN}" fill-opacity="0.5"/>')
        s += halo(px(i), SY + 22, f"{c['share']:.0%}", size=12, fill=GREEN,
                  anchor="middle", weight="700")

    TX, ty = AX + AW + 52, AY - 10
    for head, body, col in (
            ("if you are about to report adoption",
             f"Do not use this field across years. An error is a different object in the two "
             f"versions: v1 flags {pg['v1']['rate']:.0%} of datasets, v2 "
             f"{pg['v2+']['rate']:.0%}.", RED),
            ("the control",
             f"Hold the validator at v1 and move the year instead: "
             f"{list(ctl)[0]} {ctl[list(ctl)[0]]['rate']:.0%}, "
             f"{list(ctl)[1]} {ctl[list(ctl)[1]]['rate']:.0%}. The rate rose.", INK2),
            ("v2 reclassifies, it does not miss",
             f"Median warnings {pg['v2+']['warn']:,.0f} against v1's {pg['v1']['warn']:,.0f}.",
             AMBER),
            ("what is still unknown",
             f"Whether compliance improved. {pg['unstamped']['n']} datasets carry no version "
             f"stamp. This plate replaces one built on a deprecated field -- see "
             f"superseded/.", MUTED)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        w = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=29, leading=12.5)
        s += w
        ty += 12.5 * len(w) + 14

    foot = (
        f"OpenNeuro GraphQL API, no key, fetched 2026-09-24; latestSnapshot.validation and "
        f"summary.validatorMetadata. Drawn from {bidsvalid.LO} because fewer than a fifth of "
        f"earlier datasets carry a version stamp at all. A version line is plotted only where "
        f"that cell holds at least {bidsvalid.MIN_N} datasets. CAVEAT: v3 is grouped with v2, "
        f"which its rate supports; and the 803 unstamped datasets are excluded from the split "
        f"rather than assigned to v1.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for c in ser:
        print(f"    {c['year']}  pooled {c['pooled']:>4.0%}  v1 "
              + (f"{c['v1']['rate']:>4.0%}" if c['v1']['rate'] is not None else "   -")
              + f" (n={c['v1']['n']:>3})  v2+ "
              + (f"{c['v2+']['rate']:>4.0%}" if c['v2+']['rate'] is not None else "   -")
              + f" (n={c['v2+']['n']:>3})  share {c['share']:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
