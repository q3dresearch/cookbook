#!/usr/bin/env python3
"""Concentration over twenty-two years, and why the obvious measure shows none.

    python3 chart-18-ginitrend.py

The Lorenz figure beside this one is a single cycle. Running it on all eleven gives a flat answer that is wrong,
and the reason is worth more than the trend.

**Measured across every firm, nothing moves.** Wastewater treatment's Gini is 0.96 in 2001 and
0.96 in 2023. Solvents recovery 0.95 to 0.96. Deep-well 0.66 to 0.63. Landfill 0.84 to 0.83.
Read straight, the register says American hazardous waste management has not concentrated at
all since 2001.

**It says that because firms are leaving.** Wastewater treatment went from 962 companies to
367, solvents recovery 521 to 242, other treatment 258 to 77 — a 55% to 70% fall across the
register. Those exits come off the bottom of the distribution, and removing the small tail
holds the Gini still while the survivors pull apart. **The coefficient is being propped up by
the thing it is supposed to detect.**

**Hold the count constant and the concentration appears.** Recomputing on each route's largest
thirty firms only, so no arithmetic depends on how many small ones filed:

- **other treatment 0.70 to 0.95** — Ascend Performance Materials growing into 86% of a route
- **energy recovery 0.38 to 0.60**, the largest rise in a route that is not dominated by one name
- **incineration 0.43 to 0.63**, **solvents recovery 0.57 to 0.72**, **deep-well 0.50 to 0.62**
- metals recovery alone is flat, 0.80 to 0.81

Seven of eight routes concentrated among their biggest firms while the all-firms measure said
none of them did.

**So a Gini trend needs its denominator pinned.** Any inequality statistic computed on a
membership that is itself shrinking measures two things at once, and in this file they cancel
almost exactly.
"""
import collections, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brdata, plate                                                     # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "ginitrend.svg")
num = brdata.num
YEARS = [y for y in brdata.CYCLES if y != 2021]
TOPN = 30
SUF = re.compile(r"\b(LLC|INC|INCORPORATED|CORP|CORPORATION|COMPANY|LTD|PLANT|FACILITY|"
                 r"SITE|WORKS|PLT|DIVISION|THE)\b")
PAL = {"OTHER TREATMENT": ("#8c2318", "other treatment"),
       "ENERGY RECOVERY": ("#c07a1e", "energy recovery"),
       "INCINERATION": ("#c0562e", "incineration"),
       "SOLVENTS RECOVERY": ("#5aa17f", "solvents recovery"),
       "DEEPWELL / UNDERGROUND INJECTION": ("#7a4a8a", "deep-well injection"),
       "LANDFILL": ("#b0563a", "landfill"),
       "WASTEWATER TREATMENT": ("#4a7fa8", "wastewater treatment"),
       "METALS RECOVERY": ("#1b7f5a", "metals recovery")}


def company(n):
    n = (n or "?").upper().replace(",", " ").replace(".", " ").replace("-", " ")
    n = re.sub(r"\bU\s*S\s+ECOLOGY\b", "US_ECOLOGY", n)
    n = SUF.sub(" ", n)
    n = re.sub(r"[^A-Z0-9_ ]", " ", n)
    t = [x for x in n.split() if x]
    return " ".join(t[:2]) if t else "?"


def gini(v):
    v = sorted(v)
    n, tot = len(v), sum(v)
    return (2 * sum((i + 1) * x for i, x in enumerate(v)) / (n * tot) - (n + 1) / n) if tot and n else 0


def build():
    out = {}
    for y in YEARS:
        cat = collections.defaultdict(collections.Counter)
        for r in brdata.load(y):
            t = num(r["managed_tons"])
            if t > 0:
                cat[(r["management_category"] or "").replace("/ STAG /", "/ STAB /")][
                    company(r["handler_name"])] += t
        out[y] = {}
        for c, fc in cat.items():
            v = sorted(fc.values(), reverse=True)
            if len(v) < 3:
                continue
            out[y][c] = {"n": len(v), "all": gini(v),
                         "top": gini(v[:TOPN]) if len(v) >= TOPN else None}
    return out


def main():
    d = build()
    W, H = 1200, 828
    s = plate.open_svg(W, H, "Nothing concentrated, until you stop letting firms leave the sample")
    fr, _ = plate.frame(W, 62,
                        who="anyone quoting an inequality trend from a shrinking population",
                        decide="whether a flat Gini means a stable industry",
                        wrong="the fixed-count Gini goes flat once every route stops losing firms")
    s += fr

    PW, PH, PY = 320, 330, 232
    def panel(px0, key, title, sub):
        s.append(txt(px0, PY - 44, title, size=12.5, fill=INK, weight="600"))
        s.append(txt(px0, PY - 28, sub, size=10.5, fill=MUTED))
        cx = lambda y: px0 + PW * (y - YEARS[0]) / (YEARS[-1] - YEARS[0])
        if key == "n":
            cy = lambda v: PY + PH - PH * (math.log10(max(v, 20)) - 1.2) / (3.1 - 1.2)
            ticks = [(30, "30"), (100, "100"), (300, "300"), (1000, "1,000")]
        else:
            cy = lambda v: PY + PH - PH * (v - 0.3) / 0.75
            ticks = [(0.4, "0.4"), (0.6, "0.6"), (0.8, "0.8"), (1.0, "1.0")]
        for v, lab in ticks:
            s.append(f'<line x1="{px0}" y1="{cy(v):.1f}" x2="{px0+PW}" y2="{cy(v):.1f}" '
                     f'stroke="{GRID}"/>')
            s.append(txt(px0 - 7, cy(v) + 4, lab, size=9.5, fill=MUTED, anchor="end"))
        for y in (2001, 2011, 2023):
            s.append(txt(cx(y), PY + PH + 17, str(y), size=9.5, fill=MUTED, anchor="middle"))
        for c, (col, _) in PAL.items():
            pts = [(cx(y), cy(d[y][c][key])) for y in YEARS
                   if c in d[y] and d[y][c].get(key) is not None]
            if len(pts) < 3:
                continue
            path = " ".join(f"{'M' if i == 0 else 'L'}{a:.1f},{b:.1f}"
                            for i, (a, b) in enumerate(pts))
            s.append(f'<path d="{path}" fill="none" stroke="{col}" stroke-width="2.2"/>')
            s.append(f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="3.4" fill="{col}"/>')

    panel(64, "n", "firms are leaving", "companies filing in each route, log")
    panel(444, "all", "so the Gini shows nothing", "across every firm in the route")
    panel(824, "top", "until the count is pinned", f"across each route's largest {TOPN} firms")

    s += wrap(64, PY + PH + 44,
              "Wastewater goes from 962 firms to 367, other treatment 258 to 77 — a 55 to 70% "
              "fall across the register. Exits come off the bottom of the distribution.",
              size=10.5, fill=INK2, chars=48)
    s += wrap(444, PY + PH + 44,
              "Removing the small tail holds the coefficient still while the survivors pull "
              "apart, so the measure is propped up by the thing it should detect.",
              size=10.5, fill=INK2, chars=48)
    s += wrap(824, PY + PH + 44,
              f"Same firms counted every cycle: seven of eight routes concentrate. Only metals "
              f"recovery is flat.", size=10.5, fill=INK, chars=48)

    LY = PY + PH + 128
    s.append(txt(64, LY - 14, "Gini across the largest 30 firms, 2001 then 2023",
                 size=10.5, fill=INK, weight="600"))
    rank = sorted(PAL, key=lambda c: -(d[YEARS[-1]].get(c, {}).get("top") or 0))
    for i, c in enumerate(rank):
        col, lab = PAL[c]
        a = d[YEARS[0]].get(c, {}).get("top")
        b = d[YEARS[-1]].get(c, {}).get("top")
        if a is None or b is None:
            continue
        x = 64 + (i % 4) * 280
        y = LY + (i // 4) * 22
        s.append(f'<rect x="{x}" y="{y-8:.1f}" width="15" height="9" fill="{col}"/>')
        s.append(txt(x + 22, y, lab, size=10.5, fill=INK2))
        s.append(txt(x + 200, y, f"{a:.2f}", size=10, fill=MUTED, anchor="end"))
        # drawn, not typed: cairosvg has no glyph for U+2192 in this font and renders a box
        s.append(f'<line x1="{x+208}" y1="{y-4:.1f}" x2="{x+224}" y2="{y-4:.1f}" '
                 f'stroke="{MUTED}" stroke-width="1.1"/>')
        s.append(f'<path d="M{x+223},{y-7.5:.1f} L{x+229},{y-4:.1f} L{x+223},{y-0.5:.1f} Z" '
                 f'fill="{MUTED}"/>')
        s.append(txt(x + 262, y, f"{b:.2f}", size=10.5, fill=col, anchor="end", weight="700"))

    fy = H - 20 - 14 * 3
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"managed_tons on GM and WR rows, which do not overlap; all twelve management "
              f"categories, the eight with a continuous series drawn. Facility names are "
              f"normalised to an owner in every cycle independently, so a firm that renames "
              f"between cycles does not distort a within-cycle Gini. The fixed-count panel uses "
              f"each route's largest {TOPN} firms, so no arithmetic depends on how many small ones "
              f"filed. 2021 publishes no tonnage and is omitted. Method and limits in the recipe README.",
              size=11, fill=MUTED, chars=152, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for c in rank:
        a, b = d[YEARS[0]].get(c, {}), d[YEARS[-1]].get(c, {})
        if a.get("top") is None or b.get("top") is None:
            continue
        print(f"    {PAL[c][1]:<22}firms {a['n']:>4}->{b['n']:<4}  all-firm gini "
              f"{a['all']:.2f}->{b['all']:.2f}   top{TOPN} {a['top']:.2f}->{b['top']:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
