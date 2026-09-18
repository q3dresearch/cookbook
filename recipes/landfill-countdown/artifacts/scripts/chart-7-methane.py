#!/usr/bin/env python3
"""The buried waste nobody is collecting gas from, and where it sits.

    python3 chart-7-methane.py

Gas collection is the only field in this register that records somebody deciding a pile of
rubbish was worth something. It is a thin signal -- it says the methane was worth
capturing, not that the metals or plastics were -- but it is the only one, and the
question that started this line was which materials are worth mining back out.

Rows are size bands of buried waste. The left column is how often a landfill in that band
captures its gas, open sites against closed ones, because a closed landfill keeps emitting
for decades and the decision to cap it is a different decision. The right column is the
tonnage in that band that no one is capturing from, in absolute tons, because a percentage
cannot tell you where to go.

**Capture is near-universal above ten million tons and rare below half a million, and two
thirds of the uncaptured waste sits in the middle**, in the 500k-to-5M band where capture
is a coin flip. That is where the decision is live. The giants are done and the small
sites hold almost nothing.

A hypothesis that failed, kept because it was worth testing: the EPA's landfill rule
triggers at 2.5 million megagrams of design capacity, about 2.76 million short tons, so
the S-curve ought to show a step there. It does not. The bin just above the trigger
captures less often than the bin just below it, and the sharpest split anywhere in the
range sits at 1.5 million tons instead. Either the register's design capacity is not the
measure the rule turns on -- the rule also depends on emissions -- or the decision is
economic and the line is incidental.
"""
import math, os, sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmopdata import load, num
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plate                                                             # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "charts", "7-methane.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
OPEN, CLOSED, HOT = "#1b4f8a", "#8a8880", "#c07a1e"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
G, WIP = "LFG Collection System In Place?", "Waste in Place (tons)"
BANDS = ((0, 5e5, "under 500k"), (5e5, 2e6, "500k - 2M"), (2e6, 5e6, "2M - 5M"),
         (5e6, 1e7, "5M - 10M"), (1e7, 3e7, "10M - 30M"), (3e7, 1e12, "over 30M"))
UMAX = 620e6


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
    b = load("2024")
    rows = []
    for r in b.values():
        s = str(r.get("Current Landfill Status") or "").strip()
        w = num(r.get(WIP))
        if s in ("Open", "Closed") and w and w > 0:
            rows.append((w, str(r.get(G) or "").strip() == "Yes", s == "Open"))
    unc_all = sum(w for w, g, _ in rows if not g)

    band = []
    for lo, hi, lab in BANDS:
        g = [(w, x, o) for w, x, o in rows if lo <= w < hi]
        op = [x for _, x, o in g if o]
        cl = [x for _, x, o in g if not o]
        band.append({"lab": lab, "n": len(g), "unc": sum(w for w, x, _ in g if not x),
                     "op": (sum(op) / len(op), len(op)) if op else None,
                     "cl": (sum(cl) / len(cl), len(cl)) if cl else None})

    W, H = 1020, 636
    LBL, AX, AW = 28, 196, 292
    BX, BW = 606, 300
    R0, RH = 208, 54
    ax = lambda v: AX + AW * v
    bx = lambda v: BX + BW * min(v, UMAX) / UMAX
    body = []
    body.append(txt(LBL, R0 - 52, "tons already", size=11, fill=INK2))
    body.append(txt(LBL, R0 - 38, "buried there", size=11, fill=INK2))
    body.append(txt(AX, R0 - 52, "how often the gas is collected", size=12, fill=INK, weight="600"))
    body.append(txt(AX, R0 - 36, "open landfills against closed ones in the same size band",
                    size=10.5, fill=MUTED))
    body.append(txt(BX, R0 - 52, "waste nobody is collecting from", size=12, fill=INK, weight="600"))
    body.append(txt(BX, R0 - 36, "tons buried under sites with no gas system", size=10.5, fill=MUTED))
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        body.append(f'<line x1="{ax(v):.1f}" y1="{R0-24}" x2="{ax(v):.1f}" y2="{R0+RH*len(band)-16}" '
                    f'stroke="{GRID}"/>')
        body.append(txt(ax(v), R0 - 12, f"{v:.0%}", size=10, fill=MUTED, anchor="middle"))
    for v in (0, 2e8, 4e8, 6e8):
        body.append(f'<line x1="{bx(v):.1f}" y1="{R0-24}" x2="{bx(v):.1f}" y2="{R0+RH*len(band)-16}" '
                    f'stroke="{GRID}"/>')
        body.append(txt(bx(v), R0 - 12, f"{v/1e6:.0f}M" if v else "0", size=10, fill=MUTED, anchor="middle"))

    for i, d in enumerate(band):
        y = R0 + i * RH + 16
        if i % 2 == 0:
            body.append(f'<rect x="{LBL-6}" y="{y-20:.1f}" width="{W-2*LBL+12}" height="{RH-6}" '
                        f'fill="{GRID}" fill-opacity="0.5"/>')
        body.append(txt(LBL, y + 1, d["lab"], size=12, fill=INK, weight="600"))
        body.append(txt(LBL, y + 16, f"{d['n']} landfills", size=10, fill=MUTED))
        if d["op"] and d["cl"]:
            body.append(f'<line x1="{ax(d["op"][0]):.1f}" y1="{y:.1f}" x2="{ax(d["cl"][0]):.1f}" '
                        f'y2="{y:.1f}" stroke="{MUTED}" stroke-width="1.6" stroke-opacity="0.7"/>')
        for col, key, lab in ((OPEN, "op", "open"), (CLOSED, "cl", "closed")):
            if not d[key]:
                continue
            rate, n_ = d[key]
            r = 3.0 + 6.0 * (n_ / 350) ** 0.5
            body.append(f'<circle cx="{ax(rate):.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{col}" '
                        f'fill-opacity="0.85"/>')
            body.append(txt(ax(rate), y + (-12 if lab == "open" else 20), f"{rate:.0%}", size=9.5,
                            fill=col, anchor="middle"))
        body.append(f'<rect x="{BX}" y="{y-9:.1f}" width="{max(bx(d["unc"])-BX, 0.8):.1f}" height="16" '
                    f'fill="{HOT}" fill-opacity="{0.9 if d["unc"] > 3e8 else 0.6}"/>')
        body.append(txt(bx(d["unc"]) + 7, y + 4,
                        f"{d['unc']/1e6:,.0f}M tons   {d['unc']/unc_all:.0%}", size=10, fill=INK2))

    y0 = R0 + len(band) * RH + 6
    for col, lab in ((OPEN, "open landfill"), (CLOSED, "closed landfill")):
        body.append(f'<circle cx="{AX+6:.1f}" cy="{y0-4:.1f}" r="5" fill="{col}" fill-opacity="0.85"/>')
        body.append(txt(AX + 18, y0, lab, size=11, fill=col if col == OPEN else INK2))
        y0 += 17
    body.append(txt(AX + 140, R0 + len(band) * RH + 6, "dot area is how many sites",
                    size=10, fill=MUTED))
    mid = sum(d["unc"] for d in band[1:3]) / unc_all
    body += wrap(BX, R0 + len(band) * RH + 6,
                 f"{mid:.0%} of the uncaptured waste is in the two middle bands, where capture is a "
                 f"coin flip. The giants are already done and the small sites hold almost nothing.",
                 size=11, fill=INK, chars=58, leading=15)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "The methane nobody is collecting is in the middle-sized landfills",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="a climate programme choosing where to fund gas capture",
                        decide="which size band of landfill to target first",
                        wrong="uncaptured methane turns out to concentrate in the largest sites")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    n_big = sum(1 for w, g, _ in rows if not g and w > 5e6)
    t_big = sum(w for w, g, _ in rows if not g and w > 5e6)
    foot = [f"If you are looking for a site to harvest, {n_big} landfills hold over five million tons "
            f"each with no collection at all — {t_big/1e9:.2f}bn tons between them.",
            f"{unc_all/1e9:.2f}bn of {sum(w for w,_,_ in rows)/1e9:.2f}bn buried tons sit under sites with "
            f"no gas system. Closed sites keep emitting for decades and only {sum(1 for w,g,o in rows if g and not o)/sum(1 for w,g,o in rows if not o):.0%} of them capture.",
            "The EPA rule triggers at 2.5 million megagrams of design capacity and the curve shows no "
            "step there; the sharpest split sits at 1.5 million tons instead. The line is not doing the work."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"  {unc_all/1e9:.2f}bn tons uncaptured; {mid:.0%} of it in the two middle bands")
    return 0


if __name__ == "__main__":
    sys.exit(main())
