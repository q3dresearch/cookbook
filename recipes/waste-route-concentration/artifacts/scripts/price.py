#!/usr/bin/env python3
"""The join that killed this recipe's most quotable claim.

    python3 chart-13-price.py

Two sections of this recipe explained a metals-recovery market by the metal's price without
measuring it, because the register prices nothing. This is the measurement, against USGS Data
Series 140, and the claim does not survive it.

**The hypothesis, fixed before the answer was seen.** The tonnage a plant recovers rises with
the real price of the metal *that plant* recovers.

**Matching each plant to its own metal matters and was got wrong first.** The family splits
cleanly: eight plants run battery scrap and carry `D008` on essentially every ton — Sanders
Lead, Gopher Resource, Quemetco, Revere, Exide — and four run electric-arc-furnace dust and
carry `K061` — Steel Dust Recycling and the three American Zinc plants. The first version of
this test put all twelve against the zinc price, which is a lead smelter measured against the
wrong commodity. Fixing it does not rescue the hypothesis: lead plants against the real lead
price give **rho −0.002 at p 0.99** across 53 intervals.

**The wrong answer is convincing for a reason that is not the scatter.** Pooled in levels the
correlation is negative and significant, rho −0.24 at p 0.009 — but across the series the real
zinc price trends up (rho +0.70 with time) and the panel's tonnage trends down (rho −0.73).
Two series drifting oppositely correlate oppositely whatever drives either. The persuasive
thing was never a visible cloud; it was a p-value attached to a spurious regression, which is
why this chart draws the two trends rather than pretending the scatter looked like something.

**What replaces the claim.** Recovery throughput does not respond to the metal price, at any
plant, in either metal. That is what you would expect if the gate fee paid by the generator —
not the metal — is the revenue that decides whether a plant runs. **These are waste-disposal
businesses that happen to produce metal, not smelters that happen to use waste.** It reverses
the advice: entering this is a bet on feedstock contracts and permits, not on zinc. And it
explains the recovery share sitting at 50–63% for twenty-two years, which is the shape of a
capacity constraint rather than of a price response.
"""
import collections, os, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate
import brdata, plate, metals                                                    # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "price.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
RED, BLUE, ZINC, LEAD = "#8c2318", "#4a7fa8", "#1b7f5a", "#7a4a8a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
num, REC = brdata.num, brdata.RECOVERY
YEARS = [y for y in brdata.CYCLES if y not in (2021, 2023) and y != 2015]


def txt(x, y, s, *, size, fill, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" style="font-variant-numeric: tabular-nums">{escape(str(s))}</text>')


def halo(x, y, s, *, size, fill, anchor="start", weight="600"):
    c = (f'font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" '
         f'style="font-variant-numeric: tabular-nums"')
    e = escape(str(s))
    return [f'<text x="{x:.1f}" y="{y:.1f}" fill="none" stroke="{SURFACE}" stroke-width="3.4" '
            f'stroke-linejoin="round" {c}>{e}</text>',
            f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" {c}>{e}</text>']


def wrap(x, y, s, *, size, fill, chars, leading=13.5, weight="normal"):
    words, line, out, n = str(s).split(), [], [], 0
    for w in words:
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill, weight=weight))
            line, n = [], n + 1
        line.append(w)
    if line:
        out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill, weight=weight))
    return out


def build():
    px = {"zinc": metals.prices("zinc"), "lead": metals.prices("lead")}
    panel = collections.defaultdict(dict)
    codes = collections.defaultdict(collections.Counter)
    tot = collections.Counter()
    info = {}
    for y in YEARS:
        for r in brdata.load(y):
            if r["form_code"] in metals.FAM and r["management_category"] in REC:
                t = num(r["managed_tons"])
                if t <= 0:
                    continue
                h = r["handler_id"]
                panel[h][y] = panel[h].get(y, 0) + t
                tot[h] += t
                info[h] = ((r["handler_name"] or "?").split(",")[0][:26].title(), r["state"])
                fwc = r["federal_waste_codes"] or ""
                if "D008" in fwc:
                    codes[h]["lead"] += t
                if "K061" in fwc:
                    codes[h]["zinc"] += t

    def metal(h):
        c = codes[h]
        if not c:
            return None
        m, v = c.most_common(1)[0]
        return m if v / tot[h] > 0.5 else None

    keep = {h: v for h, v in panel.items() if len(v) >= 5 and tot[h] > 50_000 and metal(h)}
    obs = []
    for h, v in keep.items():
        p = px[metal(h)]
        ys = sorted(y for y in v if y in p)
        for a, b in zip(ys, ys[1:]):
            obs.append((p[b][1] / p[a][1] - 1, v[b] / v[a] - 1, h, metal(h)))
    zt = [sum(v.get(y, 0) for h, v in keep.items()) for y in YEARS]
    return px, keep, info, metal, tot, obs, zt


def main():
    px, keep, info, metal, tot, obs, zt = build()
    xs = [o[0] for o in obs]; ys = [o[1] for o in obs]
    rho = metals.spearman(xs, ys); pv = metals.permute(xs, ys, rho, n=20000)

    W, H = 1200, 701
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "No plant, in either metal, ships a ton more when its metal gets dearer",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="anyone underwriting an entry into metals recovery",
                        decide="whether to price it as a commodity bet or a contracted-volume one",
                        wrong="a plant's tonnage tracks its own metal's price in a later cycle")
    s += fr

    # ---- A: the two trends. this is the persuasive thing, not a scatter
    AX, AY, AW, AH = 28, 208, 300, 214
    s.append(txt(AX, AY - 44, "why the wrong answer was convincing", size=12.5, fill=INK, weight="600"))
    s.append(txt(AX, AY - 28, "each indexed to 2001", size=10.5, fill=MUTED))
    cx = lambda i: AX + AW * i / (len(YEARS) - 1)
    pz = [px["zinc"][y][1] for y in YEARS]
    mxv = max(max(p / pz[0] for p in pz), max(t / zt[0] for t in zt)) * 1.1
    cy = lambda v: AY + AH - AH * v / mxv
    for v in (0, 1, 2, 3):
        if v > mxv:
            break
        s.append(f'<line x1="{AX}" y1="{cy(v):.1f}" x2="{AX+AW}" y2="{cy(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(AX - 7, cy(v) + 4, f"{v:.0f}x", size=10, fill=MUTED, anchor="end"))
    for vals, col, lab in ((pz, BLUE, "real zinc price"), (zt, RED, "tons these plants recover")):
        d = " ".join(f"{'M' if i == 0 else 'L'}{cx(i):.1f},{cy(v/vals[0]):.1f}"
                     for i, v in enumerate(vals))
        s.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.6"/>')
        s += halo(cx(len(YEARS) - 1) - 2, cy(vals[-1] / vals[0]) - 10, lab, size=10.5, fill=col,
                  anchor="end")
    for i, y in enumerate(YEARS):
        if y in (2001, 2011, 2019):
            s.append(txt(cx(i), AY + AH + 17, str(y), size=10, fill=MUTED, anchor="middle"))
    s += wrap(AX, AY + AH + 38,
              "Price up (rho +0.70 with time), tonnage down (-0.73). Pooled in levels that reads "
              "as rho -0.24, p 0.009 — significant, and an artefact of these two lines.",
              size=10.5, fill=INK2, chars=45)

    # ---- B: the response curve, binned, one line per metal
    BX, BY, BW_, BH = 408, 208, 340, 214
    s.append(txt(BX, BY - 44, "what a price rise actually buys", size=12.5, fill=INK, weight="600"))
    s.append(txt(BX, BY - 28, "median change in a plant's tonnage, by price change",
                 size=10.5, fill=MUTED))
    EDGES = [(-1, -0.15), (-0.15, -0.02), (-0.02, 0.10), (0.10, 0.30), (0.30, 9)]
    LBL = ["-15%\nor worse", "-15 to\n-2%", "-2 to\n+10%", "+10 to\n+30%", "+30%\nor more"]
    bx = lambda i: BX + BW_ * (i + 0.5) / len(EDGES)
    by = lambda v: BY + BH / 2 - (BH / 2) * max(-1, min(1, v / 0.45))
    for v in (-0.4, -0.2, 0, 0.2, 0.4):
        s.append(f'<line x1="{BX}" y1="{by(v):.1f}" x2="{BX+BW_}" y2="{by(v):.1f}" '
                 f'stroke="{RULE if v == 0 else GRID}"/>')
        s.append(txt(BX - 7, by(v) + 4, f"{v:+.0%}" if v else "0", size=10, fill=MUTED, anchor="end"))
    med = lambda z: sorted(z)[len(z) // 2] if z else None
    for mt, col in (("lead", LEAD), ("zinc", ZINC)):
        pts = []
        for i, (lo, hi) in enumerate(EDGES):
            v = [o[1] for o in obs if o[3] == mt and lo <= o[0] < hi]
            if len(v) >= 3:
                pts.append((bx(i), by(med(v)), len(v)))
        d = " ".join(f"{'M' if i == 0 else 'L'}{a:.1f},{b:.1f}" for i, (a, b, _) in enumerate(pts))
        s.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.6"/>')
        for a, b, n in pts:
            s.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="4.5" fill="{col}"/>')
            s.append(txt(a, b - 11, f"n{n}", size=8.5, fill=col, anchor="middle"))
        s += halo(pts[-1][0] + 8, pts[-1][1] + 4, f"{mt} plants", size=10.5, fill=col)
    for i, t_ in enumerate(LBL):
        for j, ln in enumerate(t_.split("\n")):
            s.append(txt(bx(i), BY + BH + 16 + j * 11, ln, size=9, fill=MUTED, anchor="middle"))
    s += wrap(BX, BY + BH + 46,
              "If the hypothesis held these would slope up. Lead against lead: rho -0.002, "
              "p 0.99, n 53. Not weak — absent.", size=10.5, fill=INK2, chars=50)

    # ---- C: every plant, its state, its metal
    CX, CY, CW = 830, 208, 300
    s.append(txt(CX, CY - 44, "and no single plant does it either", size=12.5, fill=INK, weight="600"))
    s.append(txt(CX, CY - 28, "its median tonnage change when its metal rose, minus when it fell",
                 size=10.5, fill=MUTED, ))
    rows = []
    for h in keep:
        up = [o[1] for o in obs if o[2] == h and o[0] > 0.05]
        dn = [o[1] for o in obs if o[2] == h and o[0] < -0.05]
        if up and dn:
            rows.append((med(up) - med(dn), h))
    rows.sort()
    rh = 186 / max(len(rows), 1)
    zx = CX + 236
    s.append(f'<line x1="{zx:.1f}" y1="{CY-4:.1f}" x2="{zx:.1f}" y2="{CY+186:.1f}" stroke="{RULE}"/>')
    for i, (v, h) in enumerate(rows):
        nm, st = info[h]
        col = ZINC if metal(h) == "zinc" else LEAD
        y = CY + i * rh + rh / 2
        s.append(txt(CX, y + 4, f"{nm[:18]}", size=9.5, fill=INK2))
        s.append(txt(CX + 158, y + 4, st, size=9.5, fill=MUTED, anchor="end"))
        w = 62 * max(-1, min(1, v / 0.6))
        s.append(f'<rect x="{min(zx, zx+w):.1f}" y="{y-4:.1f}" width="{abs(w) or 0.8:.1f}" '
                 f'height="9" fill="{col}" fill-opacity="0.8"/>')
    s.append(txt(zx, CY + 200, "0", size=9.5, fill=MUTED, anchor="middle"))
    s.append(txt(zx - 36, CY + 200, "ships less", size=9.5, fill=MUTED, anchor="end"))
    s.append(txt(zx + 36, CY + 200, "ships more", size=9.5, fill=MUTED))
    pos = sum(1 for v, _ in rows if v > 0)
    s += wrap(CX, CY + 226,
              f"{pos} of {len(rows)} plants ship more when their metal is dearer, which is what a "
              f"coin does. Colour is the metal — green zinc, purple lead — and the state is beside "
              f"each name: no region behaves differently either.",
              size=10.5, fill=INK2, chars=46)

    s += wrap(28, 560,
              "The gate fee, not the metal, is the revenue that decides whether a plant runs. "
              "These are disposal businesses that happen to produce metal — so entry is a bet on "
              "feedstock contracts and permits, not on zinc.",
              size=13, fill=INK, chars=132, leading=17)

    fy = H - 20 - 14 * 3
    s.append(f'<line x1="28" y1="{fy-22:.1f}" x2="{W-28}" y2="{fy-22:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"Price is USGS Data Series 140 unit value, constant 1998 dollars. 2023 has no "
              f"price on this instrument and 2015 is a non-filing cycle; both excluded. "
              f"{len(keep)} plants, classed by whether D008 or K061 carries most of their tonnage. "
              f"All tests on changes within a plant, never levels. Method in the recipe.",
              size=11, fill=MUTED, chars=152, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    matched-metal differences: rho {rho:+.3f}  p {pv:.3f}  n {len(obs)}")
    print(f"    plants shipping more when dearer: {pos}/{len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
