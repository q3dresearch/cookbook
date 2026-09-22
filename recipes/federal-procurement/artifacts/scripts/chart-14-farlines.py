#!/usr/bin/env python3
"""Four FAR dollar lines, and the bunching follows whichever one is in force.

    python3 chart-14-farlines.py

Figure 12 shows award values bunching below the simplified acquisition threshold, and the
bunching moving when that threshold moved. One line could be a coincidence of that line. Three
thresholds moved in 2018, so there are three experiments, and a fourth rule whose value barely
changed serves as the control.

**Two of the three follow their rule.** Simplified acquisition runs +18.1 and +29.1 at
$150,000 while that was the line, then **+37.4 at $250,000** once the line moved, with the old
value falling to +4.8. Certified cost or pricing data is weaker but points the same way: +7.0
and +9.7 at $750,000, then **+14.2 at $2,000,000**, with $750,000 collapsing to +0.6.

**The third runs backwards, for a reason this recipe already established.** The micro-purchase
line shows a **deficit** below it in every year, not an excess. Below that value a purchase
goes on a government card and is not filed as a contract action at all, so the line is a
reporting cliff rather than a behavioural one -- which is exactly what figure 20 measures from
the other side, as 78% of a missing fifth of a million awards.

**And the control does nothing.** The subcontracting-plan floor moved 7% against the others'
167% to 186%, and reads within six points of zero in all three years.

**What this cannot show.** Intent. A distribution that tracks a rule is evidence the rule
shapes what gets written down; it is not evidence that any award was split, and no award is
identified here. The estimator is figure 12's, imported unchanged, so these sit on its scale.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import farlines, plate                                                   # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "14-farlines.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"


def money(v):
    return f"${v/1e6:g}m" if v >= 1e6 else (f"${v/1e3:g}k" if v >= 1000 else f"${v:,}")


def main():
    d = farlines.load()
    years, rules = d["years"], d["rules"]

    W, H = 1240, 806
    s = plate.open_svg(
        W, H, "Four FAR dollar lines, and the bunching follows whichever one is in force",
        subtitle="Each panel is one rule. Two lines per panel: the excess just below the old "
                 "value and below the new one. Three of these thresholds moved in 2018.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone deciding whether below-threshold clustering is a rule effect or a "
            "habit of round numbers",
        decide="whether to screen on distance below the threshold in force that year, and "
               "for which rule",
        wrong="a rule's excess stays at its old value after the line moved, or the control "
              "rule moves with the others")
    s += fr

    PW, PH, GAPX = 268, 330, 28
    AY = y0 + 76
    elo, ehi = -38, 46
    for i, r in enumerate(rules):
        PX = 64 + i * (PW + GAPX)
        px = lambda j: PX + 34 + (PW - 62) * j / (len(years) - 1)
        py = lambda v: AY + PH - 34 - (PH - 54) * (max(min(v, ehi), elo) - elo) / (ehi - elo)
        ttl = RED if not r["is_test"] else INK
        s.append(txt(PX, AY - 40, r["name"], size=11.5, fill=ttl, weight="700"))
        s.append(txt(PX, AY - 25,
                     " then ".join(money(v) for v in r["values"])
                     + ("" if r["is_test"] else "  (the control)"),
                     size=9.5, fill=MUTED))
        for g in (-30, -15, 0, 15, 30, 45):
            s.append(f'<line x1="{px(0)-8:.1f}" y1="{py(g):.1f}" x2="{px(2)+8:.1f}" '
                     f'y2="{py(g):.1f}" stroke="{RULE if g == 0 else GRID}"/>')
            if i == 0:
                s.append(txt(px(0) - 14, py(g) + 3, f"{g:+d}%", size=9, fill=MUTED,
                             anchor="end"))
        for j, y in enumerate(years):
            s.append(txt(px(j), py(elo) + 16, "FY" + y, size=9, fill=MUTED,
                         anchor="middle"))
        # the year the rule changed, marked once per panel
        if r["rule"][years[0]] != r["rule"][years[-1]]:
            xm = (px(1) + px(2)) / 2
            s.append(f'<line x1="{xm:.1f}" y1="{py(ehi):.1f}" x2="{xm:.1f}" '
                     f'y2="{py(elo):.1f}" stroke="{FAINT}" stroke-dasharray="3 3"/>')
            s += halo(xm, py(ehi) + 11, "line moves", size=8.5, fill=MUTED,
                      anchor="middle", weight="700")
        for k, v in enumerate(r["values"]):
            col = (GREEN, BLUE)[k] if r["is_test"] else SLATE
            pts = []
            for j, y in enumerate(years):
                e = r["at"][y].get(str(v))
                if e:
                    pts.append((px(j), py(e["excess"]), e["excess"],
                                r["rule"][y] == v))
            if len(pts) > 1:
                s.append('<path d="' + " ".join(("M" if q == 0 else "L")
                                                + f"{a:.1f},{b:.1f}"
                                                for q, (a, b, _, _) in enumerate(pts))
                         + f'" fill="none" stroke="{col}" stroke-width="2.0" '
                           f'stroke-opacity="0.85"/>')
            for a, b, ex, live in pts:
                s.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="{4.6 if live else 3.0:.1f}" '
                         f'fill="{col if live else "#fcfcfb"}" stroke="{col}" '
                         f'stroke-width="1.6"/>')
            lx, ly = pts[-1][0] + 8, pts[-1][1] + 3
            if i == len(rules) - 1:
                lx, ly = pts[0][0] - 8, pts[0][1] + 3
            s += halo(lx, ly, money(v), size=9.5, fill=col, weight="700",
                      anchor="end" if i == len(rules) - 1 else "start")
        live = r["at"][years[-1]].get(str(r["rule"][years[-1]]))
        if live:
            s += halo(PX, AY + PH - 6, f"in force: {live['excess']:+.1f}%", size=9.5,
                      fill=ttl, weight="700")
    s.append(txt(64, AY + PH + 30, "a filled mark is the value that was the rule that year; "
                                   "a hollow one is the same value when it was not",
                 size=9.5, fill=MUTED))
    s.append(f'<text x="28" y="{AY+PH/2:.1f}" font-size="9.5" fill="{INK2}" '
             f'transform="rotate(-90 28 {AY+PH/2:.1f})" text-anchor="middle">'
             f'excess awards just below, against the local trend</text>')

    cy = AY + PH + 62
    s.append(txt(28, cy, "the one that runs backwards is the one that is not a behaviour at "
                         "all", size=12, fill=INK, weight="600"))
    s += wrap(28, cy + 20,
              "Below the micro-purchase line a purchase goes on a government card and is "
              "never filed as a contract action, so the register thins out under it instead "
              "of piling up. That is the same fact figure 20 measures from the other side, "
              "where raising the line from $3,500 to $10,000 removed 78% of a missing fifth "
              "of a million awards. A rule can shape the distribution by changing behaviour "
              "or by changing what gets written down, and only the first is worth screening "
              "for.",
              size=10.5, fill=INK2, chars=186, leading=14.5)

    foot = (
        "USAspending API v2 bulk download; FY2016, FY2017 and FY2025, eleven civilian "
        "departments, positive awards only. Threshold values and their change dates are the "
        "FAR's, not inferred. Figure 12's estimator, imported unchanged. CAVEAT: a "
        "distribution tracking a rule is not evidence that any award was split, and none is "
        "identified. Defense (68.6% of federal contract awards) is absent.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=186, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=186, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for r in rules:
        print(f"    {'test' if r['is_test'] else 'ctrl'} {r['name']:<24}" + "  ".join(
            f"FY{y} {r['at'][y][str(r['rule'][y])]['excess']:+6.1f}%" for y in years))
    return 0


if __name__ == "__main__":
    sys.exit(main())
