#!/usr/bin/env python3
"""If you wanted to be in the business of taking hazardous waste, which door would you use.

    python3 chart-9-market.py

The register does not price anything and contains no capital costs, so it cannot say what a
facility costs to build or what a ton earns. It can say, exactly, **how many firms already
do each job, how big each of them is, and whether the work is growing** — which is the part
of a market-entry question that is usually guesswork.

Each mark is one of the twelve ways America handles hazardous waste, placed by how many
facilities accept it against how much each of them handles. Mark area is the size of the
route; colour is whether it grew or shrank since 2001.

**Deep-well injection is the extreme: nine facilities in the country, 94,000 tons each, and
the route grew 60%.** That combination — few incumbents, enormous throughput each, rising
demand — is a moat rather than an opening, and the reason is geology and a permit, neither
of which a competitor can buy quickly.

**Landfill is the growing volume business**: 34 sites, 43,000 tons each, up 28%.
**Fuel blending and wastewater treatment are the fragmented ends**, near 70 sites each at
under 8,000 tons, and both shrinking — a lot of competitors dividing a falling market.

**And the opening the data does show is not a route but a stream.** 1.17 million tons a year
of metal-bearing waste is landfilled, burned or injected rather than recovered, including
**196,000 tons carrying lead, 100,000 carrying chromium and 92,000 carrying cadmium**. That
is a physical quantity of recoverable metal being buried, and where it goes is named in
figure 4.

What this cannot tell you is whether recovering it pays, because nothing here is priced.
"""
import collections, math, os, re, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate
import brdata, plate                                                            # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "market.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
UP, DOWN = "#1b7f5a", "#b03a2e"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
num = brdata.num
NICE = {"DEEPWELL / UNDERGROUND INJECTION": "deep-well injection",
        "SLUDGE TRTMNT / STAB / ENCAP": "sludge stabilisation",
        "LAND TREATMENT / APPLICATION": "land treatment"}
MET = re.compile(r"D00[4-9]|D01[01]|K061|K062|F006|F007|F009")
DISP = {"LANDFILL", "INCINERATION", "DEEPWELL / UNDERGROUND INJECTION",
        "LAND TREATMENT / APPLICATION"}
MINSITES = 5


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


def routes(y):
    agg = collections.defaultdict(lambda: [0.0, set()])
    for r in brdata.load(y):
        if r["br_form"] != "WR":
            continue
        t = num(r["managed_tons"])
        if t <= 0:
            continue
        a = agg[r["management_category"]]
        a[0] += t
        a[1].add(r["handler_id"])
    return agg


def main():
    now, old = routes(2023), routes(2001)
    pts = []
    for k, (t, f) in now.items():
        if len(f) < MINSITES or t <= 0:
            continue
        o = old.get(k, [0.0, set()])[0]
        pts.append({"k": k, "lab": NICE.get(k, k.lower()), "t": t, "n": len(f),
                    "per": t / len(f), "g": (t / o - 1) if o else None})
    # the unrecovered metal, for the side panel
    met = collections.Counter()
    disp_t = 0.0
    for r in brdata.load(2023):
        if r["br_form"] != "WR":
            continue
        t = num(r["managed_tons"])
        if t <= 0 or r["management_category"] not in DISP:
            continue
        cs = set(re.findall(r"[A-Z]\d{3}", r["federal_waste_codes"] or ""))
        hit = [c for c in cs if MET.match(c)]
        if not hit:
            continue
        disp_t += t
        for c in hit:
            met[c] += t / len(cs)
    NAME = {"D008": "lead", "D007": "chromium", "D006": "cadmium", "D004": "arsenic",
            "D005": "barium", "D010": "selenium", "D009": "mercury", "D011": "silver",
            "F006": "plating sludge", "K061": "furnace dust"}

    W, H, L, T, PW, PH = 1060, 803, 104, 214, 480, 396
    RX, RW = 636, 330
    XLO, XHI, YLO, YHI = 6, 90, 3_000.0, 140_000.0
    lx = lambda v: L + PW * (math.log10(min(max(v, XLO), XHI)) - math.log10(XLO)) / (math.log10(XHI) - math.log10(XLO))
    ly = lambda v: T + PH - PH * (math.log10(min(max(v, YLO), YHI)) - math.log10(YLO)) / (math.log10(YHI) - math.log10(YLO))
    body = []
    body.append(txt(L, T - 46, "every route into the business, 2023", size=12.5, fill=INK, weight="600"))
    body.append(txt(L, T - 30, "how many firms already do it against how much each one handles",
                    size=10.5, fill=MUTED))
    for t in (10, 20, 40, 80):
        body.append(f'<line x1="{lx(t):.1f}" y1="{T}" x2="{lx(t):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
        body.append(txt(lx(t), T + PH + 20, str(t), size=11, fill=MUTED, anchor="middle"))
    for t, lab in ((5e3, "5k"), (1e4, "10k"), (3e4, "30k"), (1e5, "100k")):
        body.append(f'<line x1="{L}" y1="{ly(t):.1f}" x2="{L+PW}" y2="{ly(t):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ly(t) + 4, lab, size=11, fill=MUTED, anchor="end"))
    body.append(txt(L + PW / 2, T + PH + 46, "facilities accepting that kind of waste",
                    size=12, fill=INK2, anchor="middle"))
    body.append(txt(L - 10, T - 12, "tons a year", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T + 2, "per facility", size=11, fill=INK2, anchor="end"))
    body += halo(L + 10, T + 18, "few firms, huge each — a moat", size=10.5, fill=INK2)
    body += halo(L + PW - 10, T + PH - 44, "many firms, small each \u2014 a scrap",
                 size=10.5, fill=INK2, anchor="end")

    mx = max(p["t"] for p in pts)
    placed = []
    for p in sorted(pts, key=lambda p: -p["t"]):
        col = UP if (p["g"] or 0) > 0 else DOWN
        r = 4 + 16 * (p["t"] / mx) ** 0.5
        body.append(f'<circle cx="{lx(p["n"]):.1f}" cy="{ly(p["per"]):.1f}" r="{r:.1f}" fill="{col}" '
                    f'fill-opacity="0.26" stroke="{col}" stroke-opacity="0.85" stroke-width="1.1"/>')
    for p in sorted(pts, key=lambda p: -p["t"]):
        col = UP if (p["g"] or 0) > 0 else DOWN
        tx_, ty_ = lx(p["n"]) + 4 + 16 * (p["t"] / mx) ** 0.5 + 6, ly(p["per"]) + 4
        while any(abs(ty_ - q) < 14 and abs(tx_ - qx) < 150 for qx, q in placed):
            ty_ += 14
        placed.append((tx_, ty_))
        g = f"  {p['g']:+.0%}" if p["g"] is not None else ""
        body += halo(tx_, ty_, f"{p['lab']}{g}", size=10, fill=col)
    y0 = T + PH + 66
    for col, lab in ((UP, "grew since 2001"), (DOWN, "shrank")):
        body.append(f'<circle cx="{L+6:.1f}" cy="{y0-4:.1f}" r="5" fill="{col}" fill-opacity="0.32" '
                    f'stroke="{col}" stroke-width="1.1"/>')
        body.append(txt(L + 18, y0, lab, size=11, fill=col))
        y0 += 17
    body.append(txt(L + 150, T + PH + 66, "mark area is the tonnage of the whole route",
                    size=10, fill=MUTED))

    body.append(txt(RX, T - 46, "and the opening is a stream, not a route", size=12.5, fill=INK,
                    weight="600"))
    body += wrap(RX, T - 30, f"{disp_t/1e6:,.2f}M tons a year of metal-bearing waste is buried, burned "
                             f"or injected rather than recovered", size=10.5, fill=MUTED, chars=48,
                 leading=12)
    yy = T + 6
    top = met.most_common(8)
    m0 = top[0][1]
    for c, v in top:
        body.append(f'<rect x="{RX}" y="{yy-9:.1f}" width="{RW*v/m0:.1f}" height="13" fill="{DOWN}" '
                    f'fill-opacity="0.6"/>')
        w = RW * v / m0
        if w > 120:
            body.append(txt(RX + 5, yy + 1, f"{c}  {NAME.get(c,'')}", size=10, fill="#ffffff"))
            body.append(txt(RX + w + 7, yy + 1, f"{v/1e3:,.0f}k t", size=10, fill=MUTED))
        else:
            body.append(txt(RX + w + 7, yy + 1, f"{c}  {NAME.get(c,'')}   {v/1e3:,.0f}k t",
                            size=10, fill=INK2))
        yy += 24
    body += wrap(RX, yy + 10,
                 "These are tons of waste carrying the code, not tons of contained metal — the "
                 "register records what a waste is classified as, never its assay. A recovery case "
                 "needs a grade, and the grade is not here.",
                 size=10.5, fill=INK2, chars=48, leading=13)
    body += wrap(RX, yy + 76,
                 "Nothing in this file is priced. It cannot say what a facility costs to build, what "
                 "a gate fee is, or whether recovering a ton of this pays. EREF publishes tipping "
                 "fees; this register publishes quantities.",
                 size=10.5, fill=MUTED, chars=48, leading=13)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Nine facilities in America can inject hazardous waste underground",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="an entrant, an acquirer or a regulator assessing concentration",
                        decide="whether to expect competitive pricing in this market",
                        wrong="a tenth facility takes meaningful share")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    dw = next(p for p in pts if p["k"].startswith("DEEPWELL"))
    lf = next(p for p in pts if p["k"] == "LANDFILL")
    foot = [f"Deep-well injection: {dw['n']} facilities, {dw['per']/1e3:,.0f}k tons each, route up "
            f"{dw['g']:+.0%}. Landfill: {lf['n']} sites, {lf['per']/1e3:,.0f}k each, up {lf['g']:+.0%}. "
            f"Fuel blending and wastewater treatment are near 70 sites each and both shrinking.",
            "Concentration is not the same as opportunity. Few incumbents with huge throughput and "
            "rising demand is a moat; many small firms in a falling market is a scrap.",
            "Off-site receipts only — waste a facility took in from someone else, which is the part "
            "that is a market. On-site treatment is 91% of all tonnage and is not for sale."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for p in sorted(pts, key=lambda p: -p["t"])[:5]:
        print(f"    {p['lab']:<26}{p['n']:>4} sites{p['per']/1e3:>8,.0f}k each"
              f"{(p['g'] or 0):>+8.0%}")
    print(f"    unrecovered metal-bearing: {disp_t/1e6:,.2f}M tons")
    return 0


if __name__ == "__main__":
    sys.exit(main())
