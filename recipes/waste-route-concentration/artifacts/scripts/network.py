#!/usr/bin/env python3
"""Where hazardous waste goes when it leaves the place that made it, and who takes it.

    python3 chart-6-network.py

The landfill recipe established that ordinary municipal waste does **not** travel — when a
landfill closes, the sites within 40 km do not measurably speed up, and the waste goes
somewhere the register cannot see. That register has no shipments in it, so the question
died there.

This one does. Every generator's return names the facility it shipped to and the state that
facility is in, so the whole network is in the file.

**Hazardous waste travels.** 57% of shipped tonnage crosses a state line and 3% leaves the
country; only 40% is handled in the state that made it. South Carolina receives 200,000
tons and sends out 9,000 — a pure sink. California ships out 760,000 and takes 438,000.

**And the receiving end is consolidating even though the record-level concentration is
not.** The number of facilities accepting waste fell from **398 in 2001 to 290 in 2023**
while the tonnage stayed roughly flat, so the top fifty went from 71% of it to **82%**.
That is a different fact from figure 3, which found the *record* concentration steady: the
paperwork is as lumpy as it ever was, and the industry taking the waste is not.

Both panels are the six-category question answered on all twelve. Interstate flows on the
partial basket read 56% crossing; the complete basket says 57%, which is the rare case here
of a number that did not move.
"""
import collections, math, os, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate
import brdata, plate                                                            # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "network.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
SINK, SOURCE, EVEN = "#b03a2e", "#1b4f8a", "#8a8880"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
num = brdata.num
LO, HI = 2_000.0, 1_400_000.0


def txt(x, y, s, *, size, fill, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" style="font-variant-numeric: tabular-nums">{escape(str(s))}</text>')


def halo(x, y, s, *, size, fill, anchor="start", weight="600"):
    c = (f'font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" '
         f'style="font-variant-numeric: tabular-nums"')
    e = escape(str(s))
    return [f'<text x="{x:.1f}" y="{y:.1f}" fill="none" stroke="{SURFACE}" stroke-width="3" '
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
    gm = [r for r in brdata.load(2023) if r["br_form"] == "GM" and num(r["shipped_tons"]) > 0]
    out_, inn = collections.Counter(), collections.Counter()
    same = cross = abroad = 0.0
    for r in gm:
        t, a, b = num(r["shipped_tons"]), r["state"], (r["receiver_state"] or "").strip()
        if not a or not b:
            continue
        if b == "FC":
            abroad += t
            continue
        if a == b:
            same += t
            continue
        cross += t
        out_[a] += t
        inn[b] += t
    tot = same + cross + abroad
    states = sorted(set(out_) | set(inn))

    conc = {}
    for y in (2001, 2005, 2009, 2013, 2017, 2019, 2023):
        wr = [r for r in brdata.load(y) if r["br_form"] == "WR"]
        rec = collections.Counter()
        for r in wr:
            rec[r["handler_id"]] += num(r["managed_tons"])
        v = sorted((x for x in rec.values() if x > 0), reverse=True)
        t = sum(v)
        conc[y] = {"n": len(v), "t": t, 10: sum(v[:10]) / t, 25: sum(v[:25]) / t,
                   50: sum(v[:50]) / t}

    W, H, L, T, PW, PH = 1060, 824, 104, 216, 460, 420
    RX, RW, RH = 664, 300, 300
    lx = lambda v: L + PW * (math.log10(min(max(v, LO), HI)) - math.log10(LO)) / (math.log10(HI) - math.log10(LO))
    ly = lambda v: T + PH - PH * (math.log10(min(max(v, LO), HI)) - math.log10(LO)) / (math.log10(HI) - math.log10(LO))
    body = []
    body.append(txt(L, T - 46, "every state, by what it sends away and what it takes in",
                    size=12.5, fill=INK, weight="600"))
    body.append(txt(L, T - 30, "tons crossing a state line in 2023 — in-state movement excluded "
                            "from both axes", size=10.5, fill=MUTED))
    for t, lab in ((2e3, "2k"), (1e4, "10k"), (1e5, "100k"), (1e6, "1M")):
        body.append(f'<line x1="{lx(t):.1f}" y1="{T}" x2="{lx(t):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
        body.append(txt(lx(t), T + PH + 20, lab, size=10.5, fill=MUTED, anchor="middle"))
        body.append(f'<line x1="{L}" y1="{ly(t):.1f}" x2="{L+PW}" y2="{ly(t):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ly(t) + 4, lab, size=10.5, fill=MUTED, anchor="end"))
    body.append(txt(L + PW / 2, T + PH + 46, "tons sent out of the state", size=12, fill=INK2, anchor="middle"))
    body.append(txt(L - 10, T - 12, "tons received", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T + 2, "from other states", size=11, fill=INK2, anchor="end"))
    body.append(f'<line x1="{lx(LO):.1f}" y1="{ly(LO):.1f}" x2="{lx(HI):.1f}" y2="{ly(HI):.1f}" '
                f'stroke="{INK}" stroke-width="1.3"/>')
    body += halo(lx(6e5), ly(6e5) - 9, "takes as much as it sends", size=10, fill=INK, anchor="end")

    placed = []
    for s in states:
        o, i = out_.get(s, 0.0), inn.get(s, 0.0)
        net = i - o
        col = SINK if net > 0 else SOURCE
        r = 2.2 + 7.5 * ((o + i) / max((out_[x] + inn[x]) for x in states)) ** 0.5
        body.append(f'<circle cx="{lx(max(o,LO)):.1f}" cy="{ly(max(i,LO)):.1f}" r="{r:.1f}" '
                    f'fill="{col}" fill-opacity="0.34" stroke="{col}" stroke-opacity="0.8" '
                    f'stroke-width="0.9"/>')
    named = sorted(states, key=lambda s: -abs(inn.get(s, 0) - out_.get(s, 0)))[:10]
    for s in named:
        o, i = max(out_.get(s, 0.0), LO), max(inn.get(s, 0.0), LO)
        net = inn.get(s, 0) - out_.get(s, 0)
        col = SINK if net > 0 else SOURCE
        tx_, ty_ = lx(o) + 9, ly(i) + 4
        while any(abs(ty_ - q) < 13 and abs(tx_ - qx) < 90 for qx, q in placed):
            ty_ += 13
        placed.append((tx_, ty_))
        body += halo(tx_, ty_, f"{s} {net/1e3:+,.0f}k", size=10, fill=col)
    y0 = T + PH + 66
    for col, lab in ((SINK, "net importer"), (SOURCE, "net exporter")):
        body.append(f'<circle cx="{L+6:.1f}" cy="{y0-4:.1f}" r="5" fill="{col}" fill-opacity="0.45" '
                    f'stroke="{col}" stroke-width="0.9"/>')
        body.append(txt(L + 18, y0, lab, size=11, fill=col))
        y0 += 17
    body.append(txt(L + 150, T + PH + 66, "mark area is total traffic", size=10, fill=MUTED))

    body.append(txt(RX, T - 46, "and the receiving end is consolidating", size=12.5, fill=INK, weight="600"))
    body.append(txt(RX, T - 30, "share of all received tonnage held by the largest facilities",
                    size=10.5, fill=MUTED))
    ys = sorted(conc)
    cx = lambda y: RX + RW * (y - ys[0]) / (ys[-1] - ys[0])
    cy = lambda v: T + RH - RH * v
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        body.append(f'<line x1="{RX}" y1="{cy(v):.1f}" x2="{RX+RW}" y2="{cy(v):.1f}" stroke="{GRID}"/>')
        body.append(txt(RX - 8, cy(v) + 4, f"{v:.0%}", size=10, fill=MUTED, anchor="end"))
    for y in (2001, 2011, 2023):
        body.append(txt(cx(y), T + RH + 20, str(y), size=10.5, fill=MUTED, anchor="middle"))
    for k, col, lab in ((50, "#8c2318", "top 50"), (25, "#c07a1e", "top 25"), (10, "#1b4f8a", "top 10")):
        p = " ".join(f"{'M' if i==0 else 'L'}{cx(y):.1f},{cy(conc[y][k]):.1f}" for i, y in enumerate(ys))
        body.append(f'<path d="{p}" fill="none" stroke="{col}" stroke-width="2.4"/>')
        body += halo(cx(ys[-1]) + 7, cy(conc[ys[-1]][k]) + 4,
                     f"{lab}  {conc[ys[-1]][k]:.0%}", size=10.5, fill=col)
    body += wrap(RX, T + RH + 44,
                 f"{conc[ys[0]]['n']} facilities accepted waste in {ys[0]} and {conc[ys[-1]]['n']} in "
                 f"{ys[-1]}, while the tonnage barely moved. Figure 3 found record-level "
                 f"concentration flat over the same years — the paperwork is as lumpy as ever and the "
                 f"industry is not.", size=10.5, fill=INK2, chars=44, leading=13)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Hazardous waste travels; municipal waste does not",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="a planner who assumes waste is a local problem",
                        decide="whether to model catchments as local at all",
                        wrong="the in-state share rises toward municipal levels")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    sc = inn.get("SC", 0) - out_.get("SC", 0)
    foot = [f"{same/tot:.0%} of shipped tonnage stays in the state that made it, {cross/tot:.0%} "
            f"crosses a line, {abroad/tot:.0%} leaves the country. Axes are interstate only: "
            f"California's 332k out excludes the 428k it handles at home.",
            "The landfill recipe found no spillover to sites within 40 km of a closure, against a 55% "
            "effect a full redistribution would have made. Entirely different geography.",
            f"{len(gm):,} shipment records in 2023, all twelve management categories. In-state "
            f"movement is counted as staying; only the destination state is known, not the distance."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"  {same/tot:.0%} in-state, {cross/tot:.0%} interstate, {abroad/tot:.0%} abroad; "
          f"receivers {conc[ys[0]]['n']} -> {conc[ys[-1]]['n']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
