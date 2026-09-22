#!/usr/bin/env python3
"""The bunching below the threshold is broad, and no matching hole opens above it.

    python3 chart-13-bunching.py

Figure 12 showed that award values pile up just under the simplified acquisition threshold
and that the pile moved when the rule moved. Two things it deliberately did not say: **who**
does it, and whether the awards that appear below the line are **missing from above it**.

**Q30 -- where the excess lives.** The same estimator, imported from `thresh.py`, run inside
each department and each product/service family. The excess is not the property of a handful
of buyers: fourteen of twenty-seven subgroups in FY2017 and twelve of twenty in FY2025 clear
a null band built from the same estimator pointed at values with no rule behind them. It is
broad, with a gradient: Health and Human Services and medical and lab equipment run at two to
three times the register-wide rate in both years and repeat across them, while thirteen of
twenty-seven and eight of twenty cannot be told from the null at all.

**And the cut with the best story cannot be scored at all.** Q18 put competitive behaviour at
the contract vehicle, which made a handful of vehicles the likeliest home for this. The
estimator needs 400 awards inside a $120,000 window; the FY2017 window is shared by 21,600
parent PIIDs and the largest holds 162. Zero vehicles reach the floor in either year.

**Q32 -- the deficit above is absent.** If work were being held under the line, the two bins
above it would be short by roughly what the two bins below are long. They are not short: they
are 8.4% and 10.1% **above** the fitted trend, a deficit-to-excess ratio of -0.25 in both
years. One subgroup of twenty-seven and one of twenty read below the null band, where chance
alone gives between two and three.

**Three binnings, and the answer survives all of them**, which is why the footnote can say it
in one line. (1) As figure 12 bins it, above reads +8.4% and +10.1%. (2) Counting an award of
exactly $150,000 as at-or-below the line, which is how the FAR reads "not exceeding", turns
that into -12.8% and -7.9%, ratio +0.23 and +0.14 -- but the same reading gives -14.4% and
-14.9% at $200,000, where no rule exists. (3) Dropping the pile priced at exactly the tested
value from both sides gives -15.5% and -10.2% at the rule against -18.3% and -17.1% at
$200,000. In every one of them the hole above the rule is no deeper than the hole this
estimator reports at a value with no rule behind it. `subthresh.sweep_rank` ranks the rule
against the other 32 values on figure 12's grid: the excess **below** is the maximum of the
sweep in both years and both binnings, and the reading **above** sits in the ordinary middle
of it.

**So the excess is not visibly displacement.** Either the work is genuinely new small awards,
or it moved from far enough above the line that a trend fitted across $120,000 absorbs it
without a trace. This figure cannot separate those two, and it weakens any reading of figure 12 that treats a below-line award as a moved one. What it does not weaken is figure 12's own
claim: the excess below is still rank one of thirty-three in both years.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate, subthresh                                                  # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "13-bunching.svg")
RED, BLUE = "#8c2318", "#4a7fa8"
COL = {"2017": BLUE, "2025": RED}
XLO, XHI = -40, 120
ROW, HEAD = 14.6, 21.0
CUT = {"department": "BY DEPARTMENT", "family": "BY PRODUCT OR SERVICE FAMILY"}


def layout(o):
    """The rows of one panel, in order, before any pixel is spent."""
    out = [("head", "EVERY AWARD IN THE WINDOW"),
           ("all", {"name": "all eleven departments", "n": o["window_n"],
                    "below": o["all"]["below"]["excess"],
                    "above": o["all"]["above"]["excess"]})]
    for b in o["blocks"]:
        out.append(("head", f"{CUT[b['cut']]}, {len(b['rows'])} OF {b['n_groups']} SCORED"))
        out += [("row", r) for r in b["rows"]]
    v = o["vehicle"]
    out.append(("head", f"BY CONTRACT VEHICLE, {v['scored']} OF {v['n_groups']:,} SCORED"))
    out.append(("note", f"largest holds {v['biggest']} awards, the floor is "
                        f"{subthresh.MIN_WINDOW}"))
    return out


def height(rows):
    return sum(HEAD if k == "head" else ROW for k, _ in rows)


def panel(x, w, o, y_, rows):
    """One year. Label column, then a percent axis shared with the other panel."""
    s = []
    lab_w = 200
    px = x + lab_w + 90
    pw = w - lab_w - 90
    sx = lambda v: px + pw * (min(max(v, XLO), XHI) - XLO) / (XHI - XLO)
    bot = y_ + height(rows)

    lo, hi = o["band"]
    s.append(f'<rect x="{sx(lo):.1f}" y="{y_-6:.1f}" width="{sx(hi)-sx(lo):.1f}" '
             f'height="{bot-y_+2:.1f}" fill="{FAINT}" fill-opacity="0.20"/>')
    for e in (lo, hi):
        s.append(f'<line x1="{sx(e):.1f}" y1="{y_-6:.1f}" x2="{sx(e):.1f}" '
                 f'y2="{bot+2:.1f}" stroke="{FAINT}"/>')
    for g in range(XLO, XHI + 1, 40):
        s.append(f'<line x1="{sx(g):.1f}" y1="{y_-6:.1f}" x2="{sx(g):.1f}" '
                 f'y2="{bot+2:.1f}" stroke="{INK2 if g == 0 else GRID}"'
                 f'{" stroke-opacity=\"0.45\"" if g == 0 else ""}/>')
        s.append(txt(sx(g), y_ - 14, f"{g:+d}%" if g else "0%", size=9, fill=MUTED,
                     anchor="middle"))
    s.append(txt(px - 46, y_ - 14, "awards", size=8.5, fill=MUTED, anchor="end"))
    s.append(txt(px - 46, y_ - 25, "in window", size=8.5, fill=MUTED, anchor="end"))

    col = COL[o["y"]]
    yy = y_
    for kind, r in rows:
        if kind == "head":
            yy += HEAD
            s.append(txt(x, yy - 6, r, size=8.5, fill=MUTED, weight="700", spacing="0.8"))
            continue
        yy += ROW
        b = yy - 4
        if kind == "note":
            # an empty track, so the cut Q30 asks for most loudly is visibly empty rather
            # than quietly missing from the plate
            s.append(txt(x + 8, b, r, size=9.5, fill=FAINT))
            s.append(f'<line x1="{px:.1f}" y1="{b-3.6:.1f}" x2="{px+pw:.1f}" '
                     f'y2="{b-3.6:.1f}" stroke="{FAINT}" stroke-dasharray="2 4"/>')
            continue
        strong = kind == "all"
        nm = r["name"] if strong else (f"{r['label']}  {r['name']}"
                                       if r.get("label") != r["name"] else r["name"])
        s.append(txt(x, b, nm, size=10, fill=INK if strong else INK2,
                     weight="700" if strong else "normal"))
        s.append(txt(px - 46, b, f"{r['n']:,}", size=9.5, fill=MUTED, anchor="end"))
        # the ring is wider than the dot and unfilled, so a subgroup whose two sides agree
        # shows a dot inside a ring instead of one mark hiding the other
        s.append(f'<circle cx="{sx(r["above"]):.1f}" cy="{b-3.6:.1f}" r="5.0" '
                 f'fill="none" stroke="{col}" stroke-width="1.35"/>')
        s.append(f'<circle cx="{sx(r["below"]):.1f}" cy="{b-3.6:.1f}" r="3.6" '
                 f'fill="{col}"/>')
    return s


def main():
    d = subthresh.load()
    rep = subthresh.report(d)
    ys = [y for y in ("2017", "2025") if y in rep]
    for y in ys:
        rep[y]["y"] = y
    lay = {y: layout(rep[y]) for y in ys}

    W = 1240
    # Source, caveats and the context that changes the reading -- nothing about how the
    # estimator works, which is in this file's docstring and in `subthresh.py`.
    # See webprobes/doctrine/what-a-footnote-carries.md.
    # Trimmed from the plate per doctrine/what-a-footnote-carries.md; kept here because it is method: f
    # oot = ( USAspending API v2 bulk download, eleven civilian departments, awards summed to
    # a net obligation, positive awards only: FY2017 {rep['2017']['n_positive']:,} and FY2025
    # {rep['2025']['n_positive']:,}. The hole above the line is no deeper at the rule than
    # where no rule exists, so nothing here shows the excess is work moved down rather than
    # newly created. FY2016 excluded, its peak not identified. These eleven departments are
    # 8.5% of federal contract awards, Defense 68.6%. No award is identified as split.)
    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2017 and FY2025, positive "
        "awards only, using figure 12's estimator unchanged. CAVEAT: the deficit above the "
        "line is no deeper at the rule than at values with no rule behind it, so nothing "
        "here shows the excess is work moved down rather than work that was always small. "
        "These eleven civilian departments are 8.5% of federal contract awards; Defense "
        "(68.6%) is absent, so this is not federal procurement as a whole.")
    fl = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=186, leading=14))

    fr, y0 = plate.frame(
        W, 86,
        who="an auditor deciding where to point a below-threshold screen, and whether a "
            "below-line award is a moved one",
        decide="whether to target a buyer, a product family or a vehicle, and whether to "
               "read the excess as work held under the line",
        wrong="a ring sits left of the null band -- a real hole above the line -- or the "
              "filled marks collapse into it")
    ly = y0 + 22
    y_ = ly + 96
    H = int(y_ + max(height(lay[y]) for y in ys) + 160 + 14 * fl)

    s = plate.open_svg(
        W, H,
        "The bunching below the threshold is broad, and no matching hole opens above it",
        subtitle="Figure 12's excess-mass estimator, imported and pointed at one department "
                 "or product family at a time, then mirrored to read the two bins just above "
                 "the line.")
    s += fr

    s.append(txt(46, ly, "filled: awards in the two $5,000 bins just below the line, against "
                         "the local trend", size=9.5, fill=INK2))
    s.append(f'<circle cx="34" cy="{ly-3.4:.1f}" r="3.9" fill="{INK2}"/>')
    s.append(f'<circle cx="{28+404:.1f}" cy="{ly-3.4:.1f}" r="5.0" fill="none" '
             f'stroke="{INK2}" stroke-width="1.35"/>')
    s.append(txt(28 + 416, ly, "ring: the two bins just above it", size=9.5, fill=INK2))
    s.append(f'<rect x="{28+678:.1f}" y="{ly-10:.1f}" width="26" height="11" '
             f'fill="{FAINT}" fill-opacity="0.20"/>')
    s.append(f'<line x1="{28+678:.1f}" y1="{ly-10:.1f}" x2="{28+678:.1f}" '
             f'y2="{ly+1:.1f}" stroke="{FAINT}"/>')
    s.append(f'<line x1="{28+704:.1f}" y1="{ly-10:.1f}" x2="{28+704:.1f}" '
             f'y2="{ly+1:.1f}" stroke="{FAINT}"/>')
    s.append(txt(28 + 712, ly, "band: middle 80% of the same subgroups read at $200,000 and "
                               "$300,000, where no rule exists", size=9.5, fill=INK2))

    pw = (W - 56 - 44) / 2
    for i, y in enumerate(ys):
        o = rep[y]
        x = 28 + i * (pw + 44)
        s.append(txt(x, y_ - 62, f"FY{y}, the rule is ${o['rule']:,}", size=12.5,
                     fill=COL[y], weight="700"))
        s.append(txt(x, y_ - 44,
                     f"{o['clear_below']} of {o['n_rows']} subgroups exceed the band below "
                     f"the line; {o['clear_above']} falls under it above, where chance alone "
                     f"gives {round(0.1 * o['n_rows'])}",
                     size=10, fill=MUTED))
        s += panel(x, pw, o, y_, lay[y])

    fy = H - 24 - 14 * fl
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=186, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}  {W}x{H}")
    for y in ys:
        o = rep[y]
        print(f"    FY{y} rule ${o['rule']:,}: window {o['window_n']:,}, band "
              f"{o['band'][0]:+.1f}% to {o['band'][1]:+.1f}%, {o['clear_below']}/"
              f"{o['n_rows']} clear below, {o['clear_above']}/{o['n_rows']} deficit above, "
              f"ratio {o['all']['ratio']:+.2f} (statutory "
              f"{o['all_statutory']['ratio']:+.2f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
