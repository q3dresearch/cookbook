#!/usr/bin/env python3
"""What happens to the methane a landfill makes: escape, burn, or use.

    python3 chart-8-gas.py

Figure 7 asks who collects gas at all. This asks what they do with it once collected, which
is the difference between controlling a pollutant and harvesting a resource. The register
carries three numbers per site -- gas generated, gas collected, gas flared -- and the
arithmetic between them is the whole answer.

**Two fifths escapes, a third is burned off, and under a third is actually used.** 57% of
the landfills here put essentially none of their gas to work. Flaring is not nothing -- it
turns methane into carbon dioxide and is roughly thirty times better for the climate than
venting -- but it is disposal, not recovery, and it is the majority of what gets captured.

A caveat that limits every number here: **generation is modelled, not measured.** The
field is labelled "Estimated" and 75% of its variance is explained by waste-in-place
alone, so it is a decay model over the stock rather than an instrument reading. Collection
and flaring are reported quantities. That makes the split between flared and used solid,
and the escape share only as good as EPA's model.
"""
import math, os, sys
from xml.sax.saxutils import escape as esc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmopdata import load, num
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plate                                                             # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "charts", "8-gas.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
ESCAPE, FLARE, USE, OPEN, CLOSED = "#8c2318", "#c07a1e", "#1b7f5a", "#1b4f8a", "#9a988f"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
GEN, COL, FLR, WIP = ("LFG Generated (mmscfd)", "LFG Collected (mmscfd)",
                      "LFG Flared (mmscfd)", "Waste in Place (tons)")
XLO, XHI = 0.02, 20.0


def txt(x, y, s, *, size, fill, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" style="font-variant-numeric: tabular-nums">{esc(str(s))}</text>')


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
    b = load("2024")
    rows = []
    for r in b.values():
        s = str(r.get("Current Landfill Status") or "").strip()
        g, c, f = num(r.get(GEN)), num(r.get(COL)), num(r.get(FLR))
        if s not in ("Open", "Closed") or not g or c is None or f is None or g <= 0:
            continue
        c = min(c, g); f = min(f, c)
        rows.append({"g": g, "use": c - f, "flare": f, "esc": g - c, "open": s == "Open",
                     "wip": num(r.get(WIP)) or 0, "nm": str(r.get("Landfill Name") or "")[:30],
                     "st": str(r.get("State") or "").strip()})
    G = sum(r["g"] for r in rows)
    E, F, U = (sum(r[k] for r in rows) for k in ("esc", "flare", "use"))
    none_used = [r for r in rows if r["use"] <= 0.01 * r["g"]]

    W, H, L, T, PW, PH = 1020, 726, 104, 268, 588, 336
    BT = 186                                   # the national split, drawn above the scatter
    lx = lambda v: L + PW * (math.log10(min(max(v, XLO), XHI)) - math.log10(XLO)) / (math.log10(XHI) - math.log10(XLO))
    ly = lambda v: T + PH - (PH - 26) * v - 26
    body = []

    body.append(txt(L, BT - 12, "all the methane these 801 landfills make, by what happens to it",
                    size=12, fill=INK, weight="600"))
    x = L
    for val, col, lab in ((E, ESCAPE, "escapes"), (F, FLARE, "flared off"), (U, USE, "put to use")):
        w = PW * val / G
        body.append(f'<rect x="{x:.1f}" y="{BT:.1f}" width="{w:.1f}" height="26" fill="{col}"/>')
        body.append(txt(x + w / 2, BT + 17, f"{val/G:.0%}", size=12.5, fill="#ffffff",
                        anchor="middle", weight="700"))
        body.append(txt(x + w / 2, BT + 40, lab, size=10.5, fill=col, anchor="middle"))
        x += w

    for t, lab in ((0.02, "0.02"), (0.1, "0.1"), (0.5, "0.5"), (2, "2"), (5, "5"), (20, "20")):
        body.append(f'<line x1="{lx(t):.1f}" y1="{T}" x2="{lx(t):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
        body.append(txt(lx(t), T + PH + 20, lab, size=11, fill=MUTED, anchor="middle"))
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        body.append(f'<line x1="{L}" y1="{ly(v):.1f}" x2="{L+PW}" y2="{ly(v):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ly(v) + 4, f"{v:.0%}", size=11, fill=MUTED, anchor="end"))
    body.append(txt(L + PW / 2, T + PH + 46, "methane the site generates, million cubic feet a day (logarithmic)",
                    size=12, fill=INK2, anchor="middle"))
    body.append(txt(L - 10, T - 36, "share of it put", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - 22, "to use", size=11, fill=INK2, anchor="end"))

    # 57% of sites sit at exactly zero, so the zero row gets its own labelled band rather
    # than a line of marks piled on the axis pretending to be a distribution.
    zb = T + PH - 22
    body.append(f'<rect x="{L}" y="{zb:.1f}" width="{PW}" height="22" fill="{ESCAPE}" fill-opacity="0.07"/>')
    # Above the band, not inside it: 453 marks sit in that strip and would print over it.
    body.append(txt(L + 6, zb - 7, f"none of it used — {len(none_used)} landfills, "
                                   f"{len(none_used)/len(rows):.0%} of them", size=11,
                    fill=ESCAPE, weight="600"))

    wmax = max(r["wip"] for r in rows) or 1
    for r in sorted(rows, key=lambda r: -r["wip"]):
        share = r["use"] / r["g"]
        y = (zb + 11) if share <= 0.01 else ly(min(share, 1.0))
        rad = 1.7 + 5.8 * (r["wip"] / wmax) ** 0.5
        body.append(f'<circle cx="{lx(r["g"]):.1f}" cy="{y:.1f}" r="{rad:.1f}" '
                    f'fill="{OPEN if r["open"] else CLOSED}" fill-opacity="0.45"/>')

    # Name the biggest wasted opportunities: that is the decision this figure supports.
    placed = []
    for r in sorted(none_used, key=lambda r: -r["g"])[:5]:
        tx_, ty_ = lx(r["g"]), zb - 8
        while any(abs(ty_ - q) < 14 and abs(tx_ - qx) < 210 for qx, q in placed):
            ty_ -= 14
        placed.append((tx_, ty_))
        body.append(txt(tx_ - 8, ty_, f"{r['nm']} ({r['st']})", size=10, fill=INK2, anchor="end"))
        body.append(f'<line x1="{tx_-6:.1f}" y1="{ty_-4:.1f}" x2="{tx_:.1f}" y2="{zb+4:.1f}" '
                    f'stroke="{MUTED}" stroke-width="0.7"/>')

    y0 = T + 20
    for col, lab, n in ((OPEN, "open landfill", sum(r["open"] for r in rows)),
                        (CLOSED, "closed landfill", sum(not r["open"] for r in rows))):
        body.append(f'<circle cx="{L+PW+30:.1f}" cy="{y0-4:.1f}" r="5" fill="{col}" fill-opacity="0.6"/>')
        body.append(txt(L + PW + 42, y0, f"{lab}  {n}", size=11, fill=col if col == OPEN else INK2))
        y0 += 18
    body.append(txt(L + PW + 30, y0 + 12, "mark area is waste in place", size=10, fill=MUTED))
    body += wrap(L + PW + 30, y0 + 44,
                 "Right and low is the waste: a landfill making a lot of methane and using none of "
                 "it. Those sites already have the collection system — the gas is being burned at "
                 "the flare instead of sold.", size=10.5, fill=INK2, chars=30, leading=13.5)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Most captured landfill gas is burned off, not used", size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="an energy developer or a climate funder",
                        decide="whether the opportunity is capture or utilisation of what is captured",
                        wrong="the flared share falls without new capture capacity being built")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    foot = [f"The named sites each generate over 11 million cubic feet a day, already collect most of "
            f"it, and put none of it to use. They are the cheapest harvest in the country.",
            f"Open sites use {sum(r['use'] for r in rows if r['open'])/sum(r['g'] for r in rows if r['open']):.0%} "
            f"of what they generate, closed sites {sum(r['use'] for r in rows if not r['open'])/sum(r['g'] for r in rows if not r['open']):.0%}. "
            f"A closed landfill keeps generating for decades and has less reason to have built an offtake.",
            "Generation is modelled, not measured: the field says \"Estimated\" and waste-in-place alone "
            "explains 75% of it. The flared-against-used split is reported; the escape share is EPA's model."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}  ({len(rows)} landfills)")
    print(f"  escapes {E/G:.1%}, flared {F/G:.1%}, used {U/G:.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
