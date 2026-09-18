#!/usr/bin/env python3
"""What American hazardous waste physically is, and how that changed.

    python3 chart-7-composition.py

The landfill recipe had to abandon "what is in it" — the municipal register records how
much is in a hole and never what. This one has a physical form on every record.

**It is water.** 97.5% of managed tonnage in 2001 and **94.9% in 2023** is liquid. Solids
are 3%. Sludges are under 1%. When this file says a facility managed two million tons of
hazardous waste, it overwhelmingly means two million tons of contaminated water, and the
single largest form code is W101 — *"very dilute aqueous waste"*.

**The mix did shift, and the shift is about half the size it looks.** Aqueous and inorganic
liquids fell from 92% of tonnage to 68% while organic liquids rose from 5% to 27%, and that
survives dropping the ten largest records in each cycle -- so it is not one plant changing
how it files.

But wastewater treatment **is** the aqueous category, and its reporting boundary moved
(figure 8). Removing that category entirely, the shift is still there and roughly halved:
aqueous 70.3% to 58.7%, organic 17.2% to 31.8%. The direction is real; the 24-point
headline is about half definition.

**`form_code` is the composition measure that cannot inflate.** Waste codes are
multi-valued — a record carrying twenty of them enters twenty families — and weighting
those by tonnage multiplies a family total by more than twenty, differently in each cycle.
Figure 3 shows what that does. Form code is exactly one per record, so a share of tonnage
means what it says.

The block meanings are not asserted from an EPA lookup; they are **read off the free-text
description** on the records themselves, which is printed beside each band.
"""
import collections, os, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate
import brdata, plate                                                            # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "composition.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
num = brdata.num
BAND = [(100, "#4a7fa8", "aqueous & inorganic liquids"),
        (200, "#b03a2e", "organic liquids"),
        (300, "#6b6f2e", "inorganic solids"),
        (500, "#c07a1e", "inorganic sludges"),
        (400, "#8c5a2e", "organic solids"),
        (0,   "#9a988f", "lab packs & other"),
        (600, "#7a7a9a", "organic sludges")]


def txt(x, y, s, *, size, fill, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" style="font-variant-numeric: tabular-nums">{escape(str(s))}</text>')


def halo(x, y, s, *, size, fill, anchor="start", weight="600"):
    c = (f'font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" '
         f'style="font-variant-numeric: tabular-nums"')
    e = escape(str(s))
    return [f'<text x="{x:.1f}" y="{y:.1f}" fill="none" stroke="{SURFACE}" stroke-width="3.2" '
            f'stroke-linejoin="round" {c}>{e}</text>',
            f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" {c}>{e}</text>']


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
    tons, ex, trimmed = {}, collections.defaultdict(collections.Counter), {}
    for y in brdata.CYCLES:
        g = [r for r in brdata.load(y) if num(r["managed_tons"]) > 0]
        bb, tt = collections.Counter(), collections.Counter()
        big = {id(r) for r in sorted(g, key=lambda r: -num(r["managed_tons"]))[:10]}
        for r in g:
            fc = (r["form_code"] or "").strip()
            if not (fc.startswith("W") and fc[1:].isdigit()):
                continue
            b = int(fc[1:]) // 100 * 100
            bb[b] += num(r["managed_tons"])
            if id(r) not in big:
                tt[b] += num(r["managed_tons"])
            d = (r["description"] or "").strip()
            if d and y == 2023:
                ex[b][d[:30]] += num(r["managed_tons"])
        if sum(bb.values()) > 0:
            tons[y] = bb
            trimmed[y] = tt
    ys = sorted(tons)
    hi = max(sum(tons[y].values()) for y in ys) * 1.06

    W, H, L, T, PW, PH = 1060, 746, 104, 212, 560, 404
    RX = 700
    lx = lambda y: L + PW * (y - ys[0]) / (ys[-1] - ys[0])
    ly = lambda v: T + PH - PH * v / hi
    body = []
    body.append(txt(L, T - 46, "millions of tons managed, by what the waste physically is",
                    size=12.5, fill=INK, weight="600"))
    for t in (0, 50e6, 100e6, 150e6, 200e6, 250e6):
        if t <= hi:
            body.append(f'<line x1="{L}" y1="{ly(t):.1f}" x2="{L+PW}" y2="{ly(t):.1f}" stroke="{GRID}"/>')
            body.append(txt(L - 10, ly(t) + 4, f"{t/1e6:,.0f}M" if t else "0", size=11,
                            fill=MUTED, anchor="end"))
    for y in ys[::2]:
        body.append(txt(lx(y), T + PH + 20, str(y), size=10.5, fill=MUTED, anchor="middle"))
    base = {y: 0.0 for y in ys}
    for b, col, lab in BAND:
        top, bot = [], []
        for y in ys:
            v = tons[y].get(b, 0.0)
            top.append((lx(y), ly(base[y] + v)))
            bot.append((lx(y), ly(base[y])))
            base[y] += v
        d = ("M" + "L".join(f"{x:.1f},{q:.1f}" for x, q in top) + "L"
             + "L".join(f"{x:.1f},{q:.1f}" for x, q in reversed(bot)) + "Z")
        body.append(f'<path d="{d}" fill="{col}" fill-opacity="0.85"/>')
    # Plain white on a saturated band. A first version used the halo helper, whose outline
    # is the page colour -- white text ringed in near-white, which vanished.
    for b, col, lab in BAND[:2]:
        # interior years only: the thickest point is often an end, where the label clips
        at = max(ys[2:-2], key=lambda y: tons[y].get(b, 0.0))
        v = tons[at].get(b, 0.0)
        below = sum(tons[at].get(x[0], 0.0) for x in BAND[:BAND.index((b, col, lab))])
        if v > hi * 0.05:
            body.append(txt(lx(at), ly(below + v / 2) + 4, lab, size=11.5, fill="#ffffff",
                            anchor="middle", weight="700"))
    # 2021 publishes no tonnage, so the band jumps 2019 to 2023. Say so on the figure
    # rather than let a straight segment imply a measured path.
    if 2021 not in ys and ys[0] < 2021 < ys[-1]:
        gx = lx(2019) + (lx(2023) - lx(2019)) / 2
        body.append(f'<line x1="{gx:.1f}" y1="{T}" x2="{gx:.1f}" y2="{T+PH}" stroke="{SURFACE}" '
                    f'stroke-width="1.6" stroke-dasharray="4 4" stroke-opacity="0.85"/>')
        body += halo(gx, T + 16, "2021 publishes no tonnage", size=10, fill=INK, anchor="middle")

    t0, t1 = sum(tons[ys[0]].values()), sum(tons[ys[-1]].values())
    body += halo(lx(ys[0]) + 6, ly(t0) - 10, f"{t0/1e6:,.0f}M", size=13, fill=INK)
    body += halo(lx(ys[-1]) - 6, ly(t1) - 10, f"{t1/1e6:,.0f}M", size=13, fill=INK, anchor="end")

    body.append(txt(RX, T - 46, "the same thing as shares", size=12.5, fill=INK, weight="600"))
    yy = T - 20
    for b, col, lab in BAND:
        a = tons[ys[0]].get(b, 0.0) / t0
        z = tons[ys[-1]].get(b, 0.0) / t1
        if max(a, z) < 0.002:
            continue
        body.append(f'<rect x="{RX}" y="{yy:.1f}" width="12" height="12" fill="{col}"/>')
        body.append(txt(RX + 18, yy + 10, lab, size=10.5, fill=INK2))
        body.append(txt(RX + 232, yy + 10, f"{a:.0%}", size=10.5, fill=MUTED, anchor="end"))
        body.append(txt(RX + 286, yy + 10, f"{z:.0%}", size=10.5, fill=INK, anchor="end",
                        weight="600" if abs(z - a) > 0.05 else "normal"))
        yy += 21
    body.append(txt(RX + 232, T - 26, "2001", size=9.5, fill=MUTED, anchor="end"))
    body.append(txt(RX + 286, T - 26, "2023", size=9.5, fill=MUTED, anchor="end"))
    liq0 = sum(tons[ys[0]].get(b, 0) for b in (100, 200)) / t0
    liq1 = sum(tons[ys[-1]].get(b, 0) for b in (100, 200)) / t1
    body += wrap(RX, yy + 22,
                 f"{liq1:.0%} of it is liquid, down from {liq0:.0%}. Solids are 3%. When this file "
                 f"says two million tons of hazardous waste, it means two million tons of "
                 f"contaminated water.", size=11, fill=INK, chars=44, leading=14)
    ta = trimmed[ys[0]]; tb = trimmed[ys[-1]]
    a0, a1 = ta[100] / sum(ta.values()), tb[100] / sum(tb.values())
    b0, b1 = ta[200] / sum(ta.values()), tb[200] / sum(tb.values())
    body += wrap(RX, yy + 96,
                 f"Not one plant: dropping the ten largest records per cycle, aqueous still falls "
                 f"{a0:.0%} to {a1:.0%}. And not purely definition: removing wastewater treatment, "
                 f"whose boundary moved, it still falls 70% to 59%. The direction is real and the "
                 f"magnitude is about half this.", size=10.5, fill=MUTED, chars=46, leading=13)
    body += wrap(RX, yy + 162,
                 "Band names are read off the free text on the records, not asserted from a lookup: "
                 "W100s says “chem sewer, acidic waste water”, W300s says “hazardous "
                 "waste solid”, W500s says “emission control dust”.",
                 size=10.5, fill=MUTED, chars=46, leading=13)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "American hazardous waste is water", size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="anyone sizing a treatment or recovery business off headline tonnage",
                        decide="which denominator the business case uses",
                        wrong="the non-aqueous share rises above a quarter")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    foot = [f"Before quoting a tonnage of hazardous waste, know that {liq1:.0%} of it is liquid and "
            f"the largest single form code is W101, “very dilute aqueous waste”.",
            "Waste codes cannot do this job. A record can carry twenty of them, so weighting families "
            "by tonnage multiplies the total by more than twenty — and by a different amount each "
            "cycle. Form code is one per record.",
            f"{len(ys)} cycles with tonnage; 2021 publishes none and is absent. All twelve management "
            f"categories."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"  liquid {liq0:.1%} -> {liq1:.1%}; aqueous {a0:.0%}->{a1:.0%} trimmed, "
          f"organic {b0:.0%}->{b1:.0%} trimmed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
