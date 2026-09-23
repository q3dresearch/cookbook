#!/usr/bin/env python3
"""California's forecast has been decoupling from its own demand for four years.

    python3 chart-5-forecast.py

Every US balancing authority publishes a day-ahead demand forecast beside the demand it
recorded. Scoring it needs a baseline, because a grid whose load swings wildly is harder to
forecast than one that does not. The baseline is persistence -- the same hour one week
earlier, which carries the weekday and the hour for free.

    skill = 1 - MAE(forecast) / MAE(same hour last week)

1.0 is perfect, 0.0 is no better than repeating last week, negative is worse than doing
nothing. Every score here is also corrected for **scope**: rescaled by that year's median
actual-over-forecast ratio, so a grid that publishes a forecast of a different quantity is
not punished for it twice. The bottom panel is that ratio.

**Seven years, because a single year cannot tell these three faults apart.**

**CISO fell from +0.69 to -0.18** -- the largest decline of any grid above 5 GW, four
consecutive years of it, ending below the naive baseline. Its scope ratio slid the same way,
1.014 to 0.954: its published forecast is drifting further below its recorded demand every
year. That is what behind-the-meter solar does to a demand series, and a 2025 snapshot would
have called it a bad forecaster rather than a diverging one.

**Duke Energy Florida's offset has no start date.** 0.782 in 2019, 0.766 in 2025 -- flat for
seven years. It is a permanent scope mismatch, not an instrument that changed. **WACM's is the
opposite**: 0.999 drifting to 0.842. **LGEE and PNM both step in 2021**, in the same year,
which is what a reporting-standard change looks like rather than two coincidences. In any one
year all three read as the same fault.

**And the field is improving while difficulty holds flat.** Median corrected skill rose from
0.625 to 0.684 across these grids while median difficulty sat between 0.088 and 0.102. The
grids did not get easier; the forecasts got better.

**Where the decline comes from is figure 6, and the tails are figure 7.** Neither is in this
plate: this one establishes that the decline exists and is not a scoring artefact.

**Why this is a time series and not a scatter.** The earlier version plotted skill against
difficulty for one year. The two are uncorrelated -- **r = -0.02**, which is worth knowing and
does not need an axis. Spending that axis on time instead is what surfaces the four-year
decline, the undated offset and the shared 2021 step.
"""
import json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate, shape, skill                                               # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "5-forecast.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
YRS = [str(y) for y in range(2019, 2026)]
FLOOR_GW = 2.0
A_LO, A_HI = -1.0, 1.0          # skill
B_LO, B_HI = 0.74, 1.20         # scope ratio
NAMED_A = [("CISO", "California", RED), ("SOCO", "Southern", GREEN),
           ("PJM", "PJM", BLUE), ("ERCO", "ERCOT", BLUE), ("WACM", "WACM", AMBER)]
NAMED_B = [("FPC", "Duke Energy Florida", RED), ("WACM", "WACM", AMBER),
           ("LGEE", "LGEE", GREEN), ("PNM", "PNM", GREEN), ("CISO", "California", BLUE)]


def main():
    sk = skill.load()
    ba = {k: v for k, v in sk["ba"].items() if k not in shape.REGION}
    full = [b for b in ba if all(y in ba[b] for y in YRS)
            and ba[b]["2025"]["mean_mw"] >= FLOOR_GW * 1000]
    med_s = [statistics.median(ba[b][y]["skill_adj"] for b in full) for y in YRS]
    med_d = [statistics.median(ba[b][y]["nmae_naive"] for b in full) for y in YRS]
    below = [(b, y, ba[b][y]["skill_adj"]) for b in full for y in YRS
             if ba[b][y]["skill_adj"] < A_LO]
    ciso = ba["CISO"]

    W, H = 1160, 1010
    s = plate.open_svg(
        W, H, "California's forecast has been decoupling from its own demand for four years",
        subtitle=f"The {len(full)} US balancing authorities above {FLOOR_GW:.0f} GW with all "
                 f"seven years. Top: skill against a same-hour-last-week baseline. Bottom: "
                 f"what the forecast is a fraction OF.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone reading a grid operator's published forecast error",
        decide="whether a bad score is a bad forecaster, a different quantity, or a trend",
        wrong="the lines are flat and parallel, so one year would have told you the same")
    s += fr

    AX, AW = 226, W - 566
    px = lambda i: AX + AW * i / (len(YRS) - 1)

    def panel(top, height, lo, hi, field, ticks, fmt, title, note, named, medline):
        nonlocal s          # `s += ...` below would otherwise make s a local name
        ay = lambda v: top + height - height * (min(max(v, lo), hi) - lo) / (hi - lo)
        s.append(txt(AX - 4, top - 30, title, size=12.5, fill=INK, weight="600"))
        s.append(txt(AX - 4, top - 15, note, size=9.5, fill=MUTED))
        for i, y in enumerate(YRS):
            s.append(f'<line x1="{px(i):.1f}" y1="{top:.1f}" x2="{px(i):.1f}" '
                     f'y2="{top+height:.1f}" stroke="{GRID}"/>')
            s.append(txt(px(i), top + height + 17, y, size=9, fill=MUTED, anchor="middle"))
        for v in ticks:
            key = (field == "skill_adj" and abs(v) < 1e-9) or (field == "ratio" and v == 1.0)
            s.append(f'<line x1="{px(0):.1f}" y1="{ay(v):.1f}" x2="{px(len(YRS)-1):.1f}" '
                     f'y2="{ay(v):.1f}" stroke="{RULE if key else GRID}" '
                     f'stroke-width="{1.5 if key else 1}"/>')
            s.append(txt(px(0) - 8, ay(v) + 3, fmt(v), size=9, fill=MUTED, anchor="end"))
        for b in full:                                   # the field, as context
            pts = " ".join(f"{px(i):.1f},{ay(ba[b][y][field]):.1f}"
                           for i, y in enumerate(YRS))
            s.append(f'<polyline points="{pts}" fill="none" stroke="{FAINT}" '
                     f'stroke-width="1" stroke-opacity="0.55"/>')
        ends = []
        if medline:
            pts = " ".join(f"{px(i):.1f},{ay(v):.1f}" for i, v in enumerate(medline))
            s.append(f'<polyline points="{pts}" fill="none" stroke="{INK2}" '
                     f'stroke-width="2.6" stroke-dasharray="6 3"/>')
            ends.append([ay(medline[-1]), "median", INK2])
        for code, lab, col in named:
            if code not in ba:
                continue
            pts = " ".join(f"{px(i):.1f},{ay(ba[code][y][field]):.1f}"
                           for i, y in enumerate(YRS))
            s.append(f'<polyline points="{pts}" fill="none" stroke="{col}" '
                     f'stroke-width="2.2"/>')
            for i, y in enumerate(YRS):
                s.append(f'<circle cx="{px(i):.1f}" cy="{ay(ba[code][y][field]):.1f}" '
                         f'r="2.6" fill="{col}"/>')
            ends.append([ay(ba[code][YRS[-1]][field]), lab, col])
        ends.sort(key=lambda e: e[0])
        for i in range(1, len(ends)):                 # push apart where lines converge
            if ends[i][0] - ends[i - 1][0] < 13:
                ends[i][0] = ends[i - 1][0] + 13
        for yy, lab, col in ends:
            s += halo(px(len(YRS) - 1) + 9, yy + 4, lab, size=9.5, fill=col,
                      weight="700")
        return ay

    ayA = panel(y0 + 62, 300, A_LO, A_HI, "skill_adj", (-1.0, -0.5, 0.0, 0.5, 1.0),
                lambda v: f"{v:.1f}", "how far the forecast beats repeating last week",
                "1.0 perfect, 0.0 no better than the naive baseline, below the rule is "
                "worse than doing nothing", NAMED_A, med_s)
    s += halo(px(0) + 8, ayA(0.0) - 7, "no better than repeating last week", size=9.5,
              fill=INK2, weight="700")
    if below:
        s.append(txt(px(0) + 8, ayA(A_LO) - 8,
                     "below the axis: " + ", ".join(f"{b} in {y} at {v:+.2f}"
                                                    for b, y, v in below),
                     size=9, fill=MUTED))

    ayB = panel(y0 + 492, 218, B_LO, B_HI, "ratio", (0.8, 0.9, 1.0, 1.1, 1.2),
                lambda v: f"{v:.2f}",
                "what the forecast is a fraction of the demand published beside it",
                "1.00 means it forecasts the same quantity; a flat line off 1.00 is a "
                "permanent mismatch, a sloping one is a divergence", NAMED_B, None)

    TX, ty = W - 196, y0 + 74
    for head, body, col in (
            ("the four-year slide", f"CISO {ciso['2021']['skill_adj']:+.2f} in 2021 to "
                                    f"{ciso['2025']['skill_adj']:+.2f} in 2025, and its "
                                    f"scope ratio 1.014 to 0.954. Both drifting the same "
                                    f"way.", RED),
            ("three faults, one look", "Duke Energy Florida flat at 0.78 for seven years. "
                                       "WACM sliding from 1.00. LGEE and PNM stepping "
                                       "together in 2021.", AMBER),
            ("the field improved", f"Median skill {med_s[0]:.3f} to {med_s[-1]:.3f} while "
                                   f"median difficulty held between {min(med_d):.3f} and "
                                   f"{max(med_d):.3f}. Better forecasts, not easier "
                                   f"grids.", INK2),
            ("what a scatter hid", "Skill against difficulty is r = -0.02 -- worth knowing, "
                                   "not worth an axis. This one spends it on time.", MUTED)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        w = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=27, leading=12.5)
        s += w
        ty += 12.5 * len(w) + 16

    foot = (
        "EIA Hourly Electric Grid Monitor (EBA) bulk file, no key, fetched 2026-09-23; "
        "EBA.{BA}-ALL.DF.H against EBA.{BA}-ALL.D.H, UTC hours both cover, scored per year. "
        "Skill is corrected by each year's median actual-over-forecast ratio, which is the "
        "lower panel. CAVEAT: grids under 2 GW and the 14 EIA region aggregates are "
        "excluded; the regions are sums of the authorities beside them.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {len(full)} grids, {YRS[0]}-{YRS[-1]}")
    print(f"    median skill {med_s[0]:.3f} -> {med_s[-1]:.3f}; "
          f"median difficulty {med_d[0]:.3f} -> {med_d[-1]:.3f}")
    for c in ("CISO", "FPC", "WACM", "LGEE"):
        print(f"      {c:<6}skill " + " ".join(f"{ba[c][y]['skill_adj']:>6.2f}" for y in YRS)
              + "   scope " + " ".join(f"{ba[c][y]['ratio']:.3f}" for y in YRS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
