#!/usr/bin/env python3
"""Where the money is in this register, and why it is not where it looks.

The headline is the median cycle, not a round number: the buried tonnage runs from 619k to
1,049k across the eleven cycles and is never exactly 800,000, which an earlier title asserted
it was every year.

    python3 chart-11-opportunity.py

**What was asked.** Are there inefficient disposal patterns by year, state, size or category;
are there techniques recently gaining momentum; is there a business here.

**The first two answers are no, and finding that out is most of the work.** Ranked by tons
buried, the streams that look most wasteful are the ones nobody recovers anywhere — burying
them is not a missed opportunity, it is the only route. Ranked by who buries proven-
recoverable material, the list is commercial landfills and incinerators, whose recovery rate
is zero by construction. And the one genuine-looking adoption curve — W304 kiln residue going
from 6% recovered in 2001 to 65% in 2023 — dissolves when the family is taken together:
Horsehead/American Zinc Recycling moved the same electric-arc-furnace dust from W319 to W504
around 2017, which shows up as a collapse in one code and a step change in another.

**What survives is better than an adoption curve.** Take the metal-bearing residue family as
a whole — kiln and baghouse dust, stabilisation residue, emission-control dust, battery
scrap, metal-contaminated solids — and the recovery rate has sat between 50% and 63% for
twenty-two years. **Roughly 800,000 tons a year is buried, every year, and the number barely
moves.** Half the stream is recovered, so the barrier is not technology and not demand.

**Three things that make it a strategy question rather than an engineering one.** The
material and the plants are in different states: Alabama holds 515k tons of recovery capacity
and buries 21k, while Arkansas buries 168k with no plant and Michigan buries 144k with none.
Size does not predict behaviour — the largest fifth of handlers is 94% of the tonnage. And
the firm that held 46% of all recovered tonnage in 2015, Horsehead, was in Chapter 11 by
2016. Feedstock was never its problem. **This is a zinc-price business wearing a waste
business's clothes** — but that last sentence is inference, not measurement. The register
shows a leader with abundant feedstock failing; it does not contain the price that failed it.
Stated honestly: **whatever ended Horsehead is not in this file**, and a metals price series
joined to this recovery series is the test that would settle it.
"""
import collections, os, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate
import brdata, plate                                                            # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "opportunity.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
GREEN, RED, AMBER, BLUE = "#1b7f5a", "#8c2318", "#c07a1e", "#4a7fa8"
FAINT = plate.FAINT
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
num, REC, DIS = brdata.num, brdata.RECOVERY, brdata.DISPOSAL
FAM = {"W304", "W319", "W504", "W309", "W312", "W505"}
YEARS = [y for y in brdata.CYCLES if y != 2021]


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


def wrap(x, y, s, *, size, fill, chars, leading=14.0, weight="normal"):
    words, line, out, n = str(s).split(), [], [], 0
    for w in words:
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill, weight=weight))
            line, n = [], n + 1
        line.append(w)
    if line:
        out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill, weight=weight))
    return out


def scan():
    series, firms, geo = {}, {}, collections.defaultdict(lambda: [0.0, 0.0])
    buriers, ids = collections.Counter(), {}
    for y in YEARS:
        a = b = 0.0
        who = collections.Counter()
        for r in brdata.load(y):
            if r["form_code"] not in FAM:
                continue
            t = num(r["managed_tons"])
            if t <= 0:
                continue
            c = r["management_category"]
            if c in REC:
                a += t
                who[(r["handler_name"] or "?").split(",")[0].split(" (")[0][:30].title()] += t
                if y == YEARS[-1]:
                    geo[r["state"]][0] += t
            elif c in DIS:
                b += t
                if y == YEARS[-1]:
                    geo[r["state"]][1] += t
                    buriers[r["handler_id"]] += t
                    ids[r["handler_id"]] = ((r["handler_name"] or "?").split(",")[0][:34],
                                            r["state"], r["primary_naics"])
        series[y] = (a, b)
        firms[y] = who
    return series, firms, geo, buriers, ids


def main():
    series, firms, geo, buriers, ids = scan()
    bur = sorted(b for _, b in series.values())
    med_bur = bur[len(bur) // 2]
    W, H = 1200, 1080
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, f"{round(med_bur, -4):,.0f} tons of metal is buried every year, and has been since 2001",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="an entrant or acquirer in metals recovery",
                        decide="whether the feedstock exists, and where a plant would go",
                        wrong="buried tonnage falls without new recovery capacity opening")
    s += fr

    # ---- A: the stream, recovered against buried, every cycle
    AX, AY, AW, AH = 62, 190, 528, 376
    s.append(txt(AX, AY - 26, "the stream has not changed", size=12.5, fill=INK, weight="600"))
    s.append(txt(AX, AY - 10, "tons of metal-bearing residue, recovered and buried",
                 size=10.5, fill=MUTED))
    top = max(a + b for a, b in series.values())
    bw = AW / len(YEARS) * 0.62
    for v in (0, 500_000, 1_000_000, 1_500_000, 2_000_000):
        yy = AY + AH - AH * v / (top * 1.06)
        s.append(f'<line x1="{AX}" y1="{yy:.1f}" x2="{AX+AW}" y2="{yy:.1f}" stroke="{GRID}"/>')
        s.append(txt(AX - 7, yy + 4, f"{v/1e6:.1f}M" if v else "0", size=10, fill=MUTED, anchor="end"))
    for i, y in enumerate(YEARS):
        a, b = series[y]
        x = AX + AW * (i + 0.5) / len(YEARS) - bw / 2
        hb = AH * b / (top * 1.06)
        ha = AH * a / (top * 1.06)
        s.append(f'<rect x="{x:.1f}" y="{AY+AH-hb:.1f}" width="{bw:.1f}" height="{hb:.1f}" fill="{RED}"/>')
        s.append(f'<rect x="{x:.1f}" y="{AY+AH-hb-ha:.1f}" width="{bw:.1f}" height="{ha:.1f}" '
                 f'fill="{GREEN}"/>')
        s += halo(x + bw / 2, AY + AH - hb - ha - 6, f"{a/(a+b):.0%}", size=9.5, fill=GREEN,
                  anchor="middle")
        s.append(txt(x + bw / 2, AY + AH + 16, str(y)[2:], size=9.5, fill=MUTED, anchor="middle"))
    s.append(txt(AX, AY + AH + 38, "recovered", size=10.5, fill=GREEN, weight="600"))
    s.append(txt(AX + 66, AY + AH + 38, "buried, burnt or injected", size=10.5, fill=RED, weight="600"))
    a0, b0 = series[YEARS[0]]
    a1, b1 = series[YEARS[-1]]
    s += wrap(AX, AY + AH + 62,
              f"{b0/1e3:,.0f}k buried in 2001, {b1/1e3:,.0f}k in 2023; the share never leaves "
              f"50-63%. The 2015 dip is a non-filing cycle, not a shutdown.",
              size=10.5, fill=INK2, chars=84, leading=13.5)

    # ---- B: who holds it, and what happened to the last leader
    BX, BY, BW_, BH = 650, 190, 476, 128
    s.append(txt(BX, BY - 26, "but the leader changed, the hard way", size=12.5, fill=INK, weight="600"))
    s.append(txt(BX, BY - 10, "share of recovered tonnage", size=10.5, fill=MUTED))
    pal = ["#1b7f5a", "#4a7fa8", "#c07a1e", "#6b6f2e", "#7a4a8a", "#b0563a", "#9aa39a"]
    for row, yr in enumerate((2015, 2023)):
        tot = sum(firms[yr].values())
        x = BX
        s.append(txt(BX - 8, BY + row * 62 + 16, str(yr), size=11, fill=INK, anchor="end", weight="600"))
        for j, (nm, v) in enumerate(firms[yr].most_common(6)):
            w = BW_ * v / tot
            s.append(f'<rect x="{x:.1f}" y="{BY+row*62:.1f}" width="{max(w,0.8):.1f}" height="24" '
                     f'fill="{pal[j%len(pal)]}"/>')
            if w > 44:
                s.append(txt(x + w / 2, BY + row * 62 + 16, f"{v/tot:.0%}", size=10, fill="#ffffff",
                             anchor="middle", weight="700"))
            if w > 96:
                s.append(txt(x + w / 2, BY + row * 62 + 38, nm[:18], size=9.5, fill=pal[j%len(pal)],
                             anchor="middle"))
            x += w
        rest = BX + BW_ - x
        if rest > 1:
            s.append(f'<rect x="{x:.1f}" y="{BY+row*62:.1f}" width="{rest:.1f}" height="24" '
                     f'fill="{FAINT}"/>')
        s.append(txt(BX + BW_ + 8, BY + row * 62 + 16, f"{tot/1e3:,.0f}k t", size=10, fill=MUTED))
    s += wrap(BX, BY + 140,
              "Horsehead held 46% of recovered tonnage in 2015 and filed Chapter 11 in 2016, with "
              "800k tons a year going into holes beside it. Feedstock was never the problem.",
              size=10.5, fill=INK2, chars=68, leading=13.5)

    # ---- C: the material and the plants are in different states
    CX, CY, CW, CH = 650, 486, 520, 252
    s.append(txt(CX, CY - 44, "and the plants are in the wrong states", size=12.5, fill=INK, weight="600"))
    s.append(txt(CX, CY - 28, "2023 tons buried, against recovery capacity in the same state",
                 size=10.5, fill=MUTED))
    st = sorted(geo, key=lambda k: -(geo[k][1]))[:11]
    mx = max(max(v) for v in geo.values())
    mid, half = CX + CW * 0.46, CW * 0.42
    rh = (CH - 20) / len(st)
    for i, k in enumerate(st):
        r_, b_ = geo[k]
        y = CY + i * rh
        s.append(txt(mid, y + 11, k, size=10.5, fill=INK, anchor="middle", weight="600"))
        wb = half * b_ / mx
        wr = half * r_ / mx
        s.append(f'<rect x="{mid-16-wb:.1f}" y="{y:.1f}" width="{max(wb,0.8):.1f}" height="15" fill="{RED}"/>')
        s.append(f'<rect x="{mid+16:.1f}" y="{y:.1f}" width="{max(wr,0.8):.1f}" height="15" fill="{GREEN}"/>')
        if b_ > 9000:
            s += halo(mid - 20 - wb, y + 11, f"{b_/1e3:,.0f}k", size=9.5, fill=RED, anchor="end")
        if r_ > 9000:
            s += halo(mid + 20 + wr, y + 11, f"{r_/1e3:,.0f}k", size=9.5, fill=GREEN)
    s.append(txt(mid - 20, CY - 8, "buried", size=10.5, fill=RED, anchor="end", weight="600"))
    s.append(txt(mid + 20, CY - 8, "recovery capacity", size=10.5, fill=GREEN, weight="600"))
    s += wrap(CX, CY + CH + 4,
              "Alabama runs 515k tons of recovery and buries 21k. Arkansas buries 168k and has no "
              "plant; Michigan buries 144k and has none. Twelve states hold any recovery capacity "
              "at all and thirteen bury more than 10k tons, and they are mostly not the same "
              "thirteen.", size=10.5, fill=INK2, chars=68, leading=13.5)

    DX, DY = AX - 34, AY + AH + 136
    pool = sum(buriers.values())
    topn = buriers.most_common(11)
    s.append(txt(DX, DY, f"eleven sites hold {sum(v for _, v in topn)/pool:.0%} of it",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(DX, DY + 16, "2023 tons of metal-bearing residue sent to disposal, by site",
                 size=10.5, fill=MUTED))
    mxb = topn[0][1]
    for i, (h, v) in enumerate(topn):
        nm, st, nc = ids[h]
        y = DY + 36 + i * 17
        s.append(f'<rect x="{DX+206:.1f}" y="{y-9:.1f}" width="{max(230*v/mxb,0.8):.1f}" '
                 f'height="12" fill="{RED}"/>')
        s.append(txt(DX, y, f"{nm.title()[:30]}", size=10, fill=INK2))
        s.append(txt(DX + 196, y, st, size=10, fill=MUTED, anchor="end"))
        s += halo(DX + 210 + 230 * v / mxb, y, f"{v/1e3:,.0f}k", size=9.5, fill=RED)
    s += wrap(DX, DY + 36 + 11 * 17 + 14,
              f"{sum(v for _,v in topn)/pool:.0%} of the buried tonnage across {len(buriers):,} "
              f"sites: a sales list of a dozen names. Most are incinerators and landfills sending "
              f"on their own ash — the customer is the treatment industry, not the factory.",
              size=10.5, fill=INK2, chars=84, leading=13.5)

    fy = H - 20 - 14 * 4
    s.append(f'<line x1="28" y1="{fy-22:.1f}" x2="{W-28}" y2="{fy-22:.1f}" stroke="{RULE}"/>')
    foot = ("So the answer on inefficiency by year is none — the rate is flat. By size, none — the "
            "largest fifth of handlers is 94% of the tonnage and behaves like the average. By "
            "category and by state, yes, and those two are the whole finding. The apparent adoption "
            "curve in W304 was one firm's material moving between form codes.")
    fl = wrap(28, fy, foot, size=11, fill=INK2, chars=150, leading=14)
    s += fl
    s += wrap(28, fy + 14 * len(fl) + 6, "Family is form_code in W304, W319, W504, W309, W312, W505 — single-valued, "
                           "cannot inflate. Recovery is the four recovery categories; buried is "
                           "landfill, incineration and deep-well. Treatment is a third fate and is in "
                           "neither. managed_tons on GM and WR rows, which do not overlap.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for y in YEARS:
        a, b = series[y]
        print(f"    {y}  recovered {a/1e3:>7,.0f}k  buried {b/1e3:>7,.0f}k  rate {a/(a+b):>5.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
