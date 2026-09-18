#!/usr/bin/env python3
"""Whether anything is actually consolidating, which the Lorenz curve cannot say.

    python3 chart-16-records.py

The concentration curve in the larder recipe this came from is over **records**, not facilities, and pooled across every management
category. It shows that ten rows are two fifths of the tonnage and that this has barely moved
since 2001. What it cannot show is whether anything is consolidating, because pooling hides
categories moving in opposite directions — and they do.

Plotting each category's record count against its tonnage, with the cycles joined into a path,
separates three things a single concentration number runs together:

- **Deep-well injection is the only genuine consolidation in the file.** Tonnage essentially
  flat, 21.6M to 20.6M, on 1,362 records falling to 777. The same material, through half the
  paperwork, at the same handful of Gulf Coast plants.
- **Other treatment collapsed as a reporting category**, 18,510 records to 1,124, while its
  tonnage fell by a third. A 94% fall in rows against a 33% fall in tons is not an industry
  leaving.
- **Landfill and "other recovery" went the other way entirely.** Landfill rows more than
  tripled while its tonnage fell; other recovery went from 1,708 rows to 40,622 — a
  twenty-four-fold increase — while its tonnage halved. Nobody made twenty-four times more
  waste. The filing granularity changed.

**Read against tonnage, a record count is not an activity measure.** It is a measure of how
finely that activity was written down, and the two have moved in opposite directions in most
of this register. That is the same lesson the first figure teaches with one national number,
and it turns out to be far more severe inside some categories than the national view suggests.

**A note on a typo that would have split a category silently.** `management_category` carries
both `SLUDGE TRTMNT / STAB / ENCAP` and, on 60 records in 2023, `SLUDGE TRTMNT / STAG / ENCAP`.
Any group-by on the raw string drops those sixty rows into a category of their own.
"""
import collections, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brdata, plate                                                     # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "records.svg")
BLUE, RED, GREEN, AMBER, PLUM = "#4a7fa8", "#8c2318", "#1b7f5a", "#c07a1e", "#7a4a8a"
num = brdata.num
YEARS = [y for y in brdata.CYCLES if y != 2021]
SHOW = ["WASTEWATER TREATMENT", "DEEPWELL / UNDERGROUND INJECTION", "OTHER TREATMENT", "LANDFILL", "INCINERATION",
        "ENERGY RECOVERY", "METALS RECOVERY", "OTHER RECOVERY", "FUEL BLENDING",
        "SOLVENTS RECOVERY", "SLUDGE TRTMNT / STAB / ENCAP"]
SHORT = {"WASTEWATER TREATMENT": "wastewater", "DEEPWELL / UNDERGROUND INJECTION": "deep-well", "LANDFILL": "landfill",
         "OTHER TREATMENT": "other treatment", "INCINERATION": "incineration",
         "ENERGY RECOVERY": "energy recovery", "METALS RECOVERY": "metals recovery",
         "OTHER RECOVERY": "other recovery", "FUEL BLENDING": "fuel blending",
         "SOLVENTS RECOVERY": "solvents recovery",
         "SLUDGE TRTMNT / STAB / ENCAP": "sludge treatment"}
COL = {"DEEPWELL / UNDERGROUND INJECTION": GREEN, "OTHER TREATMENT": RED, "LANDFILL": AMBER, "OTHER RECOVERY": PLUM}


def norm(c):
    """EPA writes STAG for STAB on 60 records in 2023; grouping on the raw string splits it."""
    return (c or "").replace("/ STAG /", "/ STAB /")


def build():
    out = {}
    for y in YEARS:
        per = collections.defaultdict(list)
        for r in brdata.load(y):
            t = num(r["managed_tons"])
            if t > 0:
                per[norm(r["management_category"])].append(t)
        out[y] = {k: (len(v), sum(v),
                      sum(sorted(v, reverse=True)[:max(1, len(v) // 100)]) / sum(v))
                  for k, v in per.items()}
    return out


def main():
    d = build()
    W, H = 1200, 800
    s = plate.open_svg(W, H, "Record counts and tonnage move in opposite directions, by category")
    fr, _ = plate.frame(W, 62,
                        who="anyone reading a count of records as a count of activity",
                        decide="whether a category's record count can be used as a volume measure",
                        wrong="records and tonnage move together inside a category")
    s += fr

    AX, AY, AW, AH = 28, 206, 560, 420
    s.append(txt(AX, AY - 26, "how much each moved, 2001 to 2023", size=12.5, fill=INK, weight="600"))
    s.append(txt(AX, AY - 10, "multiple of its 2001 value, log scale", size=10.5, fill=MUTED))
    # A dumbbell rather than a log-log path. Eleven paths on one panel is unreadable, and a
    # line joining cycle to cycle claims a route the category may not have taken. The claim
    # here is only about the two endpoints, so only the two endpoints are drawn.
    rows = [k for k in SHOW if k in d[YEARS[0]] and k in d[YEARS[-1]]]
    ratio = {k: (d[YEARS[-1]][k][0] / d[YEARS[0]][k][0],
                 d[YEARS[-1]][k][1] / d[YEARS[0]][k][1]) for k in rows}
    rows.sort(key=lambda k: -ratio[k][0] / ratio[k][1])
    x0, x1 = AX + 132, AX + AW - 46
    lo, hi = 0.04, 30.0
    lx = lambda v: x0 + (x1 - x0) * (math.log10(max(v, lo)) - math.log10(lo)) / (
        math.log10(hi) - math.log10(lo))
    rh = (AH - 8) / len(rows)
    for v in (0.1, 0.25, 0.5, 1, 2, 5, 10, 25):
        s.append(f'<line x1="{lx(v):.1f}" y1="{AY-6}" x2="{lx(v):.1f}" y2="{AY+AH-12:.1f}" '
                 f'stroke="{RULE if v == 1 else GRID}"/>')
        s.append(txt(lx(v), AY + AH + 6, f"x{v:g}", size=9.5,
                     fill=INK2 if v == 1 else MUTED, anchor="middle",
                     weight="700" if v == 1 else "normal"))
    s.append(txt(lx(1), AY + AH + 20, "same as 2001", size=9, fill=MUTED, anchor="middle"))
    for i2, k in enumerate(rows):
        y = AY + i2 * rh + 10
        nr, tr = ratio[k]
        s.append(txt(AX, y + 4, SHORT.get(k, k), size=10.5, fill=INK2))
        s.append(f'<line x1="{lx(nr):.1f}" y1="{y:.1f}" x2="{lx(tr):.1f}" y2="{y:.1f}" '
                 f'stroke="{FAINT}" stroke-width="2"/>')
        s.append(f'<circle cx="{lx(tr):.1f}" cy="{y:.1f}" r="4.4" fill="{BLUE}"/>')
        s.append(f'<circle cx="{lx(nr):.1f}" cy="{y:.1f}" r="4.4" fill="{AMBER}"/>')
        far = max(nr, tr)
        lead, trail = ("rows", AMBER) if nr > tr else ("tons", BLUE)
        s += halo(lx(far) + 9, y + 1, f"{lead} x{max(nr, tr):,.1f}", size=9.5, fill=trail)
        s += halo(lx(far) + 9, y + 12, f"{'tons' if lead == 'rows' else 'rows'} "
                                       f"x{min(nr, tr):,.1f}", size=9,
                  fill=BLUE if lead == "rows" else AMBER, weight="normal")
    s.append(txt(x1, AY - 26, "records", size=10, fill=AMBER, weight="700", anchor="end"))
    s.append(txt(x1, AY - 10, "tonnage", size=10, fill=BLUE, weight="700", anchor="end"))
    s += wrap(AX, AY + AH + 26,
              "Where the two dots sit on opposite sides of the centre line, the category filed "
              "more rows for less waste. Other recovery went to twenty-four times the rows on "
              "half the tonnage. Deep-well is the only one that moved the other way on both — "
              "fewer rows, and the tonnage held.", size=10.5, fill=INK2, chars=92)

    BX, BY, BH2 = 660, 206, 420
    s.append(txt(BX, BY - 26, "and who the giants are inside each one", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(BX, BY - 10, "share of a category's tonnage in its largest 1% of records",
                 size=10.5, fill=MUTED))
    rows = sorted([k for k in SHOW if k in d[2001] and k in d[2023]],
                  key=lambda k: -d[2023][k][2])
    rh = BH2 / len(rows)
    xb0, xb1 = BX + 150, BX + 400
    for v in (0, 0.5, 1.0):
        xx = xb0 + (xb1 - xb0) * v
        s.append(f'<line x1="{xx:.1f}" y1="{BY-6}" x2="{xx:.1f}" y2="{BY+BH2-14:.1f}" stroke="{GRID}"/>')
        s.append(txt(xx, BY + BH2 + 2, f"{v:.0%}", size=9.5, fill=MUTED, anchor="middle"))
    for i, k in enumerate(rows):
        y = BY + i * rh + 8
        a, b = d[2001][k][2], d[2023][k][2]
        col = COL.get(k, FAINT if abs(b - a) < 0.08 else (GREEN if b < a else RED))
        s.append(txt(BX, y + 4, SHORT.get(k, k), size=10.5, fill=INK2))
        s.append(f'<line x1="{xb0+(xb1-xb0)*a:.1f}" y1="{y:.1f}" x2="{xb0+(xb1-xb0)*b:.1f}" '
                 f'y2="{y:.1f}" stroke="{col}" stroke-width="2.4"/>')
        s.append(f'<circle cx="{xb0+(xb1-xb0)*a:.1f}" cy="{y:.1f}" r="3" fill="none" '
                 f'stroke="{col}" stroke-width="1.6"/>')
        s.append(f'<circle cx="{xb0+(xb1-xb0)*b:.1f}" cy="{y:.1f}" r="4.2" fill="{col}"/>')
        s += halo(xb1 + 12, y + 4, f"{b:.0%}", size=10, fill=col)
    s += wrap(BX, BY + BH2 + 24,
              "Scale-free, so the cycles are comparable even though the record counts are not. "
              "Wastewater treatment is 100%: its top 1% of rows is all of it. Energy recovery "
              "nearly doubled, 37% to 69%, which is the one real concentration in the file.",
              size=10.5, fill=INK2, chars=62)

    fy = H - 20 - 14 * 3
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              "All twelve management categories; the eleven with meaningful tonnage are drawn. "
              "management_category carries a typo — SLUDGE TRTMNT / STAG / ENCAP on 60 records in "
              "2023 — which is normalised here, because grouping on the raw string files those "
              "rows as a category of their own. 2021 publishes no tonnage and is omitted. Method "
              "in the recipe.", size=11, fill=MUTED, chars=152, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for k in sorted(SHOW, key=lambda k: -d[2023].get(k, (0, 0, 0))[1]):
        if k in d[2001] and k in d[2023]:
            n0, t0, p0 = d[2001][k]
            n1, t1, p1 = d[2023][k]
            print(f"    {SHORT.get(k,k):<19}{n0:>8,}->{n1:>8,} recs  {t0/1e6:>6.1f}M->{t1/1e6:>5.1f}M"
                  f"  top1% {p0:>4.0%}->{p1:>4.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
