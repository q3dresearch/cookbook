#!/usr/bin/env python3
"""Counting records instead of tons, for twenty-two years, in six waste streams.

    python3 chart-1-rows-vs-tons.py

EPA's Biennial Report can be counted two ways. Count rows -- one per waste stream and
management method -- and American hazardous waste looks like a collapse of recycling and a
boom in burial: metals recovery down 60%, landfill up 184%, "other recovery" up **916%**.
Count tons and **every one of the twelve management categories falls**, and **five of them
reverse sign**: incineration is +48% by record and -46% by ton, wastewater treatment +15%
by record and **-83%** by ton.

The reason is that a row is a reporting unit, not a quantity. The table grew from 1.13
million rows in 2001 to 1.77 million in 2023 while the waste in it shrank, because
facilities report the same waste split across more codes and methods than they used to.

Each panel is indexed to its own 2001 so the two lines are comparable within a stream;
the absolute tonnage is printed because an index hides that deep-well injection is 93% of
everything here and solvents recovery is under 1%.

**The 2021 cycle is missing from the tonnage line and not interpolated.** EPA publishes
`generation_tons` and `managed_tons` as null on every row of that cycle, in every
category. A gap is drawn as a gap.

**And the 2019 tonnage spike is one record.** Watervliet Arsenal reported 55.4 million tons
of "industrial wastewater" in that cycle and nothing in any other -- more than the entire
national total for 2023. It is left in, because removing a record because it is
inconvenient is worse than showing that the series contains one; the 2001-to-2023 decline
survives dropping the fifty largest records in every cycle (-79% instead of -71%).
"""
import json, math, os, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(HERE, "..", "charts", "rows-vs-tons.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
ROWS_C, TONS_C = "#b03a2e", "#1b4f8a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
ORDER = ["OTHER RECOVERY", "LANDFILL", "INCINERATION", "WASTEWATER TREATMENT",
         "METALS RECOVERY", "DEEPWELL"]
NICE = {"DEEPWELL": "deep-well injection", "OTHER RECOVERY": "other recovery",
        "LANDFILL": "landfill", "METALS RECOVERY": "metals recovery",
        "SOLVENTS RECOVERY": "solvents recovery", "ENERGY RECOVERY": "energy recovery",
        "INCINERATION": "incineration", "WASTEWATER TREATMENT": "wastewater treatment",
        "FUEL BLENDING": "fuel blending", "SLUDGE TREATMENT": "sludge treatment",
        "LAND TREATMENT": "land treatment", "OTHER TREATMENT": "other treatment"}


def txt(x, y, s, *, size, fill, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" style="font-variant-numeric: tabular-nums">{escape(str(s))}</text>')


def wrap(x, y, s, *, size, fill, chars, leading=15.0):
    words, line, out, n = str(s).split(), [], [], 0
    for w in words:
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill)); line, n = [], n + 1
        line.append(w)
    if line:
        out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
    return out


def main():
    d = json.load(open(os.path.join(DATA, "br_trend.json")))
    rows, managed = d["rows"], d["managed"]
    cycles = sorted({int(k.split("|")[1]) for k in rows})
    live = [y for y in cycles if any(managed.get(f"{c}|{y}", 0) for c in ORDER)]

    W, H = 1040, 786
    L, T, PW, PH, GAP = 76, 210, 270, 150, 46
    body = []
    for i, cat in enumerate(ORDER):
        cx = L + (i % 3) * (PW + GAP)
        cy = T + (i // 3) * (PH + 96)
        r0 = rows.get(f"{cat}|{cycles[0]}", 0) or 1
        m0 = managed.get(f"{cat}|{live[0]}", 0) or 1
        rser = [(y, rows.get(f"{cat}|{y}", 0) / r0 * 100) for y in cycles]
        mser = [(y, managed.get(f"{cat}|{y}", 0) / m0 * 100) for y in live]
        hi = max([v for _, v in rser] + [v for _, v in mser] + [110])
        top = 1100 if hi > 400 else (400 if hi > 200 else 200)
        px = lambda y: cx + PW * (y - cycles[0]) / (cycles[-1] - cycles[0])
        py = lambda v: cy + PH - PH * min(v, top) / top
        body.append(f'<rect x="{cx}" y="{cy}" width="{PW}" height="{PH}" fill="{GRID}" '
                    f'fill-opacity="0.35"/>')
        body.append(f'<line x1="{cx}" y1="{py(100):.1f}" x2="{cx+PW}" y2="{py(100):.1f}" '
                    f'stroke="{MUTED}" stroke-width="1" stroke-dasharray="3 3"/>')
        body.append(txt(cx - 6, py(100) + 4, "100", size=9, fill=MUTED, anchor="end"))
        body.append(txt(cx - 6, cy + 8, f"{top}", size=9, fill=MUTED, anchor="end"))
        for series, col, w in ((rser, ROWS_C, 1.8), (mser, TONS_C, 2.2)):
            pth = " ".join(("M" if j == 0 else "L") + f"{px(y):.1f},{py(v):.1f}"
                           for j, (y, v) in enumerate(series))
            body.append(f'<path d="{pth}" fill="none" stroke="{col}" stroke-width="{w}"/>')
            ly_, lv = series[-1]
            body.append(f'<circle cx="{px(ly_):.1f}" cy="{py(lv):.1f}" r="3" fill="{col}"/>')
            body.append(txt(px(ly_) + 5, py(lv) + 4, f"{lv-100:+.0f}%", size=10, fill=col,
                            weight="600"))
        body.append(txt(cx, cy - 26, NICE[cat], size=13, fill=INK, weight="600"))
        tons = managed.get(f"{cat}|{live[-1]}", 0)
        body.append(txt(cx, cy - 11, f"{tons/1e6:,.2f}M tons managed in 2023", size=10, fill=MUTED))
        for y in (2001, 2011, 2023):
            body.append(txt(px(y), cy + PH + 15, str(y), size=9.5, fill=MUTED, anchor="middle"))

    y0 = T + (PH + 96) + PH + 44
    for col, lab in ((ROWS_C, "rows in the file"), (TONS_C, "tons actually managed")):
        body.append(f'<line x1="{L}" y1="{y0-4:.1f}" x2="{L+22}" y2="{y0-4:.1f}" '
                    f'stroke="{col}" stroke-width="2.4"/>')
        body.append(txt(L + 30, y0, lab, size=11.5, fill=col, weight="600"))
        y0 += 18
    body += wrap(L + 210, T + (PH + 96) + PH + 44,
                 "Each panel is indexed to its own 2001 value. The 2021 cycle publishes no tonnage "
                 "at all, so the blue line skips it rather than interpolating across it.",
                 size=10.5, fill=MUTED, chars=74, leading=13)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Counting records said recycling collapsed. Counting tons says everything shrank.",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="anyone about to quote a trend out of this register",
                        decide="which of the two numbers goes in the sentence — records or tons",
                        wrong="records and tons move together in a later cycle")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    foot = ["All twelve management categories fall in tons and five reverse sign against their "
            "record count: energy recovery, incineration, landfill, other recovery and wastewater "
            "treatment all gain records while losing waste.",
            "A record count is a measure of reporting practice that happens to be denominated in "
            "waste. Incineration gains 48% of its records and loses 46% of its tons.",
            "Tonnage is managed_tons on both record types: on-site treatment from the generator's "
            "own return plus waste received from elsewhere. On-site is 97% of it in 2001 and 91% "
            "in 2023 — this is overwhelmingly waste handled where it is made."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
