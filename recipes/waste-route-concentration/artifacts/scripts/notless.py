#!/usr/bin/env python3
"""Whether a 71% fall in reported tonnage means America makes less hazardous waste. It does not.

    python3 chart-8-notless.py

Every other figure here reports that the tonnage fell. The obvious reading is that industry
cleaned up. Three counts in the same file say otherwise.

**The generators did not leave.** 17,360 facilities filed a generation record in 2001 and
**17,111 in 2023** — a 1% change over twenty-two years.

**They did not file less.** Generation records went from 192,737 to **237,063**, up 23%.

**They reported a quarter of the tonnage.** 239 million tons to 63 million, down 74%.

Same plants, more paperwork, a quarter of the waste. That is a reporting boundary moving,
not behaviour changing, and the individual filings show where it moved: in 2001 the six
largest generators reported **100% "wastewater treatment"** each. In 2023 Dow files 94
records reporting **0.00 million tons** and Motiva's successor files three. They did not
close; their wastewater stopped being counted here.

**EPA says so itself.** Its own guidance on the 1997 cycle notes that the reporting
requirements for wastewaters — which are regulated under the Clean Water Act rather than
RCRA — were changed, and that "cursory comparisons of the 1997 National Biennial Report to
earlier National Reports could produce misleading results". This recipe spans 2001 to 2023
and the same caution applies with more force.

**So what can be said?** That the *non-wastewater* tonnage fell 22% while wastewater fell
83%; that the count of firms handling hazardous waste is flat; and that any headline of the
form "American hazardous waste fell by X%" is a statement about a definition.
"""
import collections, os, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate
import brdata, plate                                                            # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "notless.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
GEN, REC, TON = "#1b7f5a", "#c07a1e", "#b03a2e"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
num = brdata.num


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
    ser = {}
    top01, nm = collections.Counter(), {}
    for y in brdata.CYCLES:
        gm = [r for r in brdata.load(y) if r["br_form"] == "GM"]
        t = sum(num(r["generation_tons"]) for r in gm)
        if not t:
            continue
        ser[y] = {"gen": len({r["handler_id"] for r in gm}), "rec": len(gm), "ton": t}
        ww = sum(num(r["generation_tons"]) for r in gm
                 if r["management_category"] == "WASTEWATER TREATMENT")
        ser[y]["ww"] = ww
        ser[y]["rest"] = t - ww
        if y == 2001:
            for r in gm:
                top01[r["handler_id"]] += num(r["generation_tons"])
                nm[r["handler_id"]] = r["handler_name"]
    ys = sorted(ser)
    now = {}
    for r in brdata.load(ys[-1]):
        if r["br_form"] == "GM":
            now[r["handler_id"]] = now.get(r["handler_id"], 0) + num(r["generation_tons"])

    W, H, L, T, PW, PH = 1060, 740, 100, 226, 500, 384
    RX, RW = 646, 330
    lx = lambda y: L + PW * (y - ys[0]) / (ys[-1] - ys[0])
    ly = lambda v: T + PH - PH * min(v, 1.35) / 1.35
    body = []
    body.append(txt(L, T - 48, "three counts from the same records, each indexed to 2001",
                    size=12.5, fill=INK, weight="600"))
    for v in (0, 0.25, 0.5, 0.75, 1.0, 1.25):
        body.append(f'<line x1="{L}" y1="{ly(v):.1f}" x2="{L+PW}" y2="{ly(v):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ly(v) + 4, f"{v:.0%}", size=11, fill=MUTED, anchor="end"))
    for y in ys[::2]:
        body.append(txt(lx(y), T + PH + 20, str(y), size=10.5, fill=MUTED, anchor="middle"))
    body.append(f'<line x1="{L}" y1="{ly(1.0):.1f}" x2="{L+PW}" y2="{ly(1.0):.1f}" '
                f'stroke="{INK}" stroke-width="1" stroke-dasharray="3 3"/>')
    for k, col, lab in (("gen", GEN, "facilities filing"), ("rec", REC, "records filed"),
                        ("ton", TON, "tons reported")):
        base = ser[ys[0]][k]
        p = " ".join(f"{'M' if i==0 else 'L'}{lx(y):.1f},{ly(ser[y][k]/base):.1f}"
                     for i, y in enumerate(ys))
        body.append(f'<path d="{p}" fill="none" stroke="{col}" stroke-width="2.6"/>')
        body.append(f'<circle cx="{lx(ys[-1]):.1f}" cy="{ly(ser[ys[-1]][k]/base):.1f}" r="4" fill="{col}"/>')
        body += halo(lx(ys[-1]) + 8, ly(ser[ys[-1]][k] / base) + 4,
                     f"{lab}  {ser[ys[-1]][k]/base-1:+.0%}", size=11, fill=col)

    body.append(txt(RX, T - 48, "the six largest generators of 2001", size=12.5, fill=INK, weight="600"))
    body.append(txt(RX, T - 32, "all six reported 100% wastewater treatment that year",
                    size=10.5, fill=MUTED))
    yy = T - 4
    mx = max(v for _, v in top01.most_common(6))
    for h, v in top01.most_common(6):
        n2 = now.get(h)
        body.append(txt(RX, yy, (nm[h] or "")[:28], size=10.5, fill=INK, weight="600"))
        yy += 15
        body.append(f'<rect x="{RX}" y="{yy-9:.1f}" width="{RW*v/mx:.1f}" height="11" fill="{TON}" '
                    f'fill-opacity="0.75"/>')
        body.append(txt(RX + RW * v / mx + 6, yy, f"{v/1e6:,.1f}M in 2001", size=9.5, fill=MUTED))
        yy += 14
        if n2 is None:
            body.append(txt(RX, yy, "absent from 2023 entirely", size=9.5, fill=INK2))
        else:
            w = RW * n2 / mx
            body.append(f'<rect x="{RX}" y="{yy-9:.1f}" width="{max(w,1.2):.1f}" height="11" '
                        f'fill="{GEN}" fill-opacity="0.75"/>')
            body.append(txt(RX + max(w, 1.2) + 6, yy, f"{n2/1e6:,.2f}M in 2023", size=9.5, fill=MUTED))
        yy += 21

    body += wrap(RX, yy + 6,
                 "They did not close. Dow files 94 records in 2023 reporting 0.00 million tons. Their "
                 "wastewater stopped being counted here, and EPA's own guidance warns that comparing "
                 "across the wastewater reporting changes “could produce misleading results”.",
                 size=10.5, fill=INK2, chars=48, leading=13)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "The waste did not go away. It stopped being counted.",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="anyone quoting a cross-cycle tonnage trend from this file",
                        decide="whether to use the tonnage series at all",
                        wrong="generator counts fall alongside the tonnage")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    a, b = ser[ys[0]], ser[ys[-1]]
    foot = [f"Facilities filing {a['gen']:,} to {b['gen']:,} ({b['gen']/a['gen']-1:+.0%}); records "
            f"{a['rec']:,} to {b['rec']:,} ({b['rec']/a['rec']-1:+.0%}); tons {a['ton']/1e6:,.0f}M to "
            f"{b['ton']/1e6:,.0f}M ({b['ton']/a['ton']-1:+.0%}).",
            f"Wastewater fell {b['ww']/a['ww']-1:+.0%} and everything else "
            f"{b['rest']/a['rest']-1:+.0%}. Hazardous wastewater is regulated under the Clean Water "
            f"Act as well as RCRA, and what it is counted as has changed.",
            "So no headline of the form \"American hazardous waste fell by X%\" survives this file. "
            "What survives is the composition, the geography and the network — all within-cycle."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"  generators {a['gen']:,}->{b['gen']:,}, records {a['rec']:,}->{b['rec']:,}, "
          f"tons {a['ton']/1e6:,.0f}M->{b['ton']/1e6:,.0f}M")
    print(f"  wastewater {a['ww']/1e6:,.0f}M->{b['ww']/1e6:,.0f}M, rest {a['rest']/1e6:,.0f}M->{b['rest']/1e6:,.0f}M")
    return 0


if __name__ == "__main__":
    sys.exit(main())
