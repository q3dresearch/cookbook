#!/usr/bin/env python3
"""Whether hazardous waste should be studied as one subject or three.

    python3 chart-10-phase.py

95% of this register by tonnage is liquid, which makes "hazardous waste" sound like one
thing with a few odd corners. It is not. **What happens to a waste is decided almost
entirely by what phase it is in**, and the three phases have nothing in common:

- **Aqueous liquid, 47.7M tons.** Wastewater treatment 54%, deep-well injection 32%, other
  treatment 13%. Essentially none of it is recovered; it is treated or put underground.
- **Inorganic solid, 2.2M tons.** Landfill 50%, **metals recovery 30%**, stabilisation 12%.
- **Inorganic sludge, 0.7M tons.** Landfill 45%, **metals recovery 42%**.
- **Organic solid, 0.2M tons.** Incineration 29%, landfill 28%, energy recovery 25% — burnt
  one way or another.
- **Gas, 0.01M tons.** Fuel blending 43%.

So the policy levers are different instruments in different rooms. A liquids policy is about
injection wells and the boundary between the Clean Water Act and RCRA. A solids policy is
about landfill against recovery. An organics policy is about combustion. Nothing said about
the 95% applies to the 3% where the materials are.

**And the split isolates the trustworthy part of the file.** Figure 8 shows the tonnage
series is unusable across cycles because wastewater reporting was redefined — but wastewater
*is* the aqueous phase. The solid stream never went through that boundary change, and its
series is correspondingly well-behaved: **4.2M tons of inorganic solid in 2001 falling
steadily to 2.2M in 2023**, with no cliff.

That is the answer to whether these deserve separate studies. Not because the categories are
tidy, but because one of them can carry a twenty-two year trend and the other cannot.
"""
import collections, os, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate
import brdata, plate                                                            # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "phase.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
num = brdata.num
PHASE = {0: "lab packs & other", 100: "aqueous liquid", 200: "organic liquid",
         300: "inorganic solid", 400: "organic solid", 500: "inorganic sludge",
         600: "organic sludge", 800: "gas"}
ORDER = ["aqueous liquid", "organic liquid", "inorganic solid", "inorganic sludge",
         "lab packs & other", "organic solid", "organic sludge", "gas"]
ROUTE = [("WASTEWATER TREATMENT", "#4a7fa8", "wastewater treatment"),
         ("DEEPWELL / UNDERGROUND INJECTION", "#4a4a8a", "deep-well injection"),
         ("OTHER TREATMENT", "#7fa8c4", "other treatment"),
         ("LANDFILL", "#8c2318", "landfill"),
         ("INCINERATION", "#c0562e", "incineration"),
         ("METALS RECOVERY", "#1b7f5a", "metals recovery"),
         ("SOLVENTS RECOVERY", "#5aa17f", "solvents recovery"),
         ("OTHER RECOVERY", "#9ac4a8", "other recovery"),
         ("ENERGY RECOVERY", "#c07a1e", "energy recovery"),
         ("FUEL BLENDING", "#d9a441", "fuel blending"),
         ("SLUDGE TRTMNT / STAB / ENCAP", "#6b6f2e", "stabilisation")]


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


def ph(r):
    fc = (r["form_code"] or "").strip()
    if fc.startswith("W") and fc[1:].isdigit():
        return PHASE.get(int(fc[1:]) // 100 * 100)
    return None


def main():
    mix = collections.defaultdict(collections.Counter)
    tot = collections.Counter()
    for r in brdata.load(2023):
        t = num(r["managed_tons"])
        if t <= 0:
            continue
        p = ph(r)
        if not p:
            continue
        mix[p][r["management_category"]] += t
        tot[p] += t
    series = {}
    for y in brdata.CYCLES:
        c = collections.Counter()
        for r in brdata.load(y):
            t = num(r["managed_tons"])
            if t > 0:
                p = ph(r)
                if p:
                    c[p] += t
        if sum(c.values()):
            series[y] = c
    ys = sorted(series)

    W, H, LBL, BX, BW = 1180, 878, 28, 214, 400
    T, RH = 232, 46
    RX, RW, RT, RHH = 690, 290, 232, 300
    rows = [p for p in ORDER if tot[p] > 5_000]
    body = []
    body.append(txt(LBL, T - 44, "what happens to it, by what phase it is in",
                    size=12.5, fill=INK, weight="600"))
    body.append(txt(LBL, T - 28, "share of each phase's 2023 tonnage", size=10.5, fill=MUTED))
    for i, p in enumerate(rows):
        y = T + i * RH
        body.append(txt(LBL, y + 2, p, size=11.5, fill=INK, weight="600"))
        body.append(txt(LBL, y + 17, f"{tot[p]/1e6:,.2f}M tons", size=10, fill=MUTED))
        x = BX
        for k, col, lab in ROUTE:
            v = mix[p].get(k, 0.0) / tot[p]
            if v <= 0:
                continue
            w = BW * v
            body.append(f'<rect x="{x:.1f}" y="{y-9:.1f}" width="{max(w,0.7):.1f}" height="22" '
                        f'fill="{col}"/>')
            if w > 56:
                body.append(txt(x + w / 2, y + 6, f"{v:.0%}", size=10, fill="#ffffff",
                                anchor="middle", weight="700"))
            x += w
    y0 = T + RH * len(rows) + 8
    xp = BX
    for k, col, lab in ROUTE:
        if not any(mix[p].get(k, 0) / tot[p] > 0.03 for p in rows):
            continue
        body.append(f'<rect x="{xp:.1f}" y="{y0-9:.1f}" width="12" height="11" fill="{col}"/>')
        body.append(txt(xp + 17, y0, lab, size=10, fill=col))
        xp += 22 + len(lab) * 5.8
        if xp > BX + BW - 30:
            xp = BX
            y0 += 16

    body.append(txt(RX, RT - 44, "and only one of them can carry a trend",
                    size=12.5, fill=INK, weight="600"))
    body.append(txt(RX, RT - 28, "each phase indexed to its own 2001", size=10.5, fill=MUTED))
    tracked = (("aqueous liquid", "#4a7fa8"), ("inorganic solid", "#8c2318"))
    top = max(series[y].get(p, 0) / series[ys[0]][p] for p, _ in tracked for y in ys
              if series[ys[0]].get(p))
    ceil = 0.25 * -(-(top * 1.06) // 0.25)
    step = 0.25 if ceil <= 1.5 else 0.5
    cx = lambda y: RX + RW * (y - ys[0]) / (ys[-1] - ys[0])
    cy = lambda v: RT + RHH - RHH * min(v, ceil) / ceil
    for v in [x * step for x in range(int(round(ceil / step)) + 1)]:
        body.append(f'<line x1="{RX}" y1="{cy(v):.1f}" x2="{RX+RW}" y2="{cy(v):.1f}" stroke="{GRID}"/>')
        body.append(txt(RX - 8, cy(v) + 4, f"{v:.0%}", size=10, fill=MUTED, anchor="end"))
    for y in (2001, 2011, 2023):
        body.append(txt(cx(y), RT + RHH + 18, str(y), size=10, fill=MUTED, anchor="middle"))
    for p, col in tracked:
        base = series[ys[0]].get(p, 0)
        if not base:
            continue
        d = " ".join(f"{'M' if i==0 else 'L'}{cx(y):.1f},{cy(series[y].get(p,0)/base):.1f}"
                     for i, y in enumerate(ys))
        body.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.4"/>')
        jump = max(abs(series[b].get(p, 0) / series[a].get(p, 1) - 1)
                   for a, b in zip(ys, ys[1:]))
        body += halo(cx(ys[-1]) + 7, cy(series[ys[-1]].get(p, 0) / base) + 4,
                     p, size=10.5, fill=col)
        body += halo(cx(ys[-1]) + 7, cy(series[ys[-1]].get(p, 0) / base) + 18,
                     f"{series[ys[-1]].get(p,0)/base-1:+.0%} overall", size=9.5, fill=MUTED,
                     weight="normal")
        body += halo(cx(ys[-1]) + 7, cy(series[ys[-1]].get(p, 0) / base) + 30,
                     f"worst single jump {jump:+.0%}", size=9.5, fill=MUTED, weight="normal")
    cap = wrap(RX, RT + RHH + 42,
                 "The aqueous line is the one the wastewater redefinition moved, and it is 95% of the "
                 "tonnage: it can gain 71% in one cycle and lose 60% in the next, which is not a "
                 "quantity anyone is measuring. The solid line never went through that change and "
                 "never moves more than a quarter between cycles — 4.2M tons in 2001 falling steadily "
                 "to 2.2M. That is a series you can read.",
                 size=10.5, fill=INK2, chars=46, leading=13)
    body += cap
    body += wrap(RX, RT + RHH + 42 + 13 * (len(cap) + 1),
                 "Sludge is left off deliberately. In 2007 one handler, Eastman Kodak, is 81% of all "
                 "inorganic sludge in the country, and 79% in 2009; by 2011 it is gone. A national "
                 "line there would be one firm's silver recovery wearing a trend's clothes.",
                 size=10.5, fill=MUTED, chars=46, leading=13)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Liquids get injected, solids get buried or mined, organics get burnt",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="anyone about to study \"hazardous waste\" as one subject",
                        decide="whether to split the file by phase before analysing it",
                        wrong="management routes overlap substantially across phases")
    s += fr
    s += body
    fy = H - 20 - 15 * 3
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    sol = mix["inorganic solid"]
    rec = sol.get("METALS RECOVERY", 0) / tot["inorganic solid"]
    foot = [(INK2, f"Almost none of the liquid is recovered — it is treated or put underground. "
                   f"Recovery is a solids and sludge business: metals recovery takes "
                   f"{rec:.0%} of inorganic solids and "
                   f"{mix['inorganic sludge']['METALS RECOVERY']/tot['inorganic sludge']:.0%} of "
                   f"inorganic sludges, and none of the aqueous liquid. So nothing true of the 95% "
                   f"is true of the 3% where the materials are."),
            (MUTED, "Phase is read from form_code, which is exactly one per record and cannot "
                    "inflate. Tonnage is managed_tons on both record types, all twelve management "
                    "categories, 2023 unless a year is given.")]
    fyy = fy
    for col, line in foot:
        drawn = wrap(28, fyy, line, size=11, fill=col, chars=142, leading=14)
        s += drawn
        fyy += 14 * len(drawn)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for p in rows:
        top = ", ".join(f"{k.split('/')[0].strip().lower()[:16]} {v/tot[p]:.0%}"
                        for k, v in mix[p].most_common(2))
        print(f"    {p:<20}{tot[p]/1e6:>8,.2f}M  {top}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
