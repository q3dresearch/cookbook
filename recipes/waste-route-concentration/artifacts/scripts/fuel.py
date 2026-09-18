#!/usr/bin/env python3
"""Whether anything became worth burning that was not worth burning before.

    python3 chart-12-fuel.py

Incineration and energy recovery are the same physical act. The waste burns either way; the
only difference is whether someone pays for the heat. That makes the split between them a
clean economic test with no technology barrier in it — so if a material ever crossed from
"costs money to destroy" to "worth money as fuel", it should show here.

**It does not.** Across everything burned, the share from which value was captured — solvent
reclamation, fuel blending, energy recovery — was 60% in 2001 and 66% in 2023, and never left
the 64–71% band in between. Every form code that appeared to cross over failed a check:
`W001` gained 71 points while its tonnage grew sixteenfold, which is a code being reused, not
a material being adopted. Only four streams have both a stable denominator and no dominant
firm, and the largest of them moved six points.

**What did change is who buys the heat.** In 2001, waste-derived fuel went to a broad
industrial base: chemical plants, petroleum refineries, mines, lightweight-aggregate kilns,
and about 198 assorted energy-recovery sites. By 2023 refineries take 1% of what they took,
mining takes none, aggregate kilns take 12%, and **cement kilns have gone from 21% of the
market to 46%** — nine to eleven facilities throughout, so this is share taken, not capacity
built. The number of generators shipping to them in a single cycle went from 190 to 1,242.

**And one material went the other way.** `W202`, chlorinated bottoms from vinyl chloride
production, was 52% recovered for value in 2001 and is 7% now; it is 93% straight
incineration. Every class of buyer dropped it, not one. The obvious explanation — that the
surviving buyer is a cement kiln and kilns avoid chlorine — is not supported here: kilns'
halogen-coded intake share is *higher* than everyone else's. So the fact is solid and the
cause is not in this file.
"""
import collections, os, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate
import brdata, plate                                                            # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "fuel.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
GREEN, RED, AMBER, BLUE, PLUM = "#1b7f5a", "#8c2318", "#c07a1e", "#4a7fa8", "#7a4a8a"
FAINT = plate.FAINT
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
num = brdata.num
VALUE = {"ENERGY RECOVERY", "FUEL BLENDING"}
BURN = {"INCINERATION", "ENERGY RECOVERY", "FUEL BLENDING", "SOLVENTS RECOVERY"}
CAPTURE = {"ENERGY RECOVERY", "FUEL BLENDING", "SOLVENTS RECOVERY"}
YEARS = [y for y in brdata.CYCLES if y != 2021]
EARLY, LATE = [2001, 2003, 2005], [2019, 2023]
IND = {"32731": "cement kilns", "562": "waste-management sites", "325": "chemical plants",
       "324": "petroleum refineries", "327": "other mineral kilns", "212": "mining",
       "493": "warehousing", "561": "support services", "339": "misc manufacturing"}


def bucket(nc):
    nc = nc or ""
    if nc.startswith("32731"):
        return "cement kilns"
    return IND.get(nc[:3], "everything else")


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


def scan():
    buyers = {}
    rates = {}
    for y in YEARS:
        b = collections.Counter()
        burn = collections.Counter()
        w202 = collections.Counter()
        ship = set()
        for r in brdata.load(y):
            t = num(r["managed_tons"])
            if t <= 0:
                continue
            c = r["management_category"]
            if c in VALUE:
                b[bucket(r["primary_naics"])] += t
                if (r["primary_naics"] or "").startswith("32731") and r["shipper_id"]:
                    ship.add(r["shipper_id"])
            if c in BURN:
                burn[c in CAPTURE] += t
                if r["form_code"] == "W202":
                    w202[c in CAPTURE] += t
        buyers[y] = (b, len(ship))
        tb = sum(burn.values())
        tw = sum(w202.values())
        rates[y] = (burn[True] / tb, b["cement kilns"] / sum(b.values()),
                    w202[True] / tw if tw > 500 else None, tb)
    return buyers, rates


def main():
    buyers, rates = scan()
    W, H = 1200, 755
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Nothing became worth burning. The people willing to pay for the heat changed.",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="a generator of burnable hazardous waste, and its procurement team",
                        decide="how exposed you are to a buyer base that has narrowed to eleven kilns",
                        wrong="non-kiln energy recovery regains share of the fuel market")
    s += fr

    # ---- A: who buys the heat, then and now
    AX, AY, AW, AH = 28, 200, 500, 300
    s.append(txt(AX, AY - 26, "who burns waste for its heat", size=12.5, fill=INK, weight="600"))
    s.append(txt(AX, AY - 10, "tons per cycle, averaged over 2001–05 and 2019–23",
                 size=10.5, fill=MUTED))
    e = collections.Counter(); l = collections.Counter()
    for y in EARLY:
        for k, v in buyers[y][0].items():
            e[k] += v / len(EARLY)
    for y in LATE:
        for k, v in buyers[y][0].items():
            l[k] += v / len(LATE)
    keys = sorted(set(e) | set(l), key=lambda k: -max(e[k], l[k]))[:7]
    mx = max(max(e[k], l[k]) for k in keys)
    rh = AH / len(keys)
    for i, k in enumerate(keys):
        y = AY + i * rh
        s.append(txt(AX, y + 12, k, size=11, fill=INK, weight="600" if k == "cement kilns" else "normal"))
        for j, (v, col) in enumerate(((e[k], FAINT), (l[k], GREEN if l[k] > e[k] else RED))):
            bw = (AW - 186) * v / mx
            s.append(f'<rect x="{AX+186:.1f}" y="{y+2+j*13:.1f}" width="{max(bw,0.8):.1f}" '
                     f'height="11" fill="{col}"/>')
            s += halo(AX + 190 + bw, y + 11 + j * 13, f"{v/1e3:,.0f}k", size=9, fill=MUTED if j == 0 else col)
    s.append(txt(AX + 186, AY + AH + 6, "2001–05", size=10, fill=FAINT, weight="600"))
    s.append(txt(AX + 240, AY + AH + 6, "2019–23", size=10, fill=INK2, weight="600"))
    s += wrap(AX, AY + AH + 28,
              f"Cement kilns are nine to eleven facilities in every cycle, so this is share taken, "
              f"not capacity built. The generators shipping to them went from {buyers[EARLY[0]][1]:,} "
              f"to {buyers[LATE[-1]][1]:,}. Refineries take 1% of what they once took and mining "
              f"takes none.", size=10.5, fill=INK2, chars=76)

    # ---- B: three rates, one axis
    BX, BY, BW_, BH = 640, 200, 430, 300
    s.append(txt(BX, BY - 26, "and the economics did not move", size=12.5, fill=INK, weight="600"))
    s.append(txt(BX, BY - 10, "share of burnt tonnage that someone paid for", size=10.5, fill=MUTED))
    cx = lambda y: BX + BW_ * (y - YEARS[0]) / (YEARS[-1] - YEARS[0])
    cy = lambda v: BY + BH - BH * v
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        s.append(f'<line x1="{BX}" y1="{cy(v):.1f}" x2="{BX+BW_}" y2="{cy(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(BX - 7, cy(v) + 4, f"{v:.0%}", size=10, fill=MUTED, anchor="end"))
    for y in (2001, 2011, 2023):
        s.append(txt(cx(y), BY + BH + 17, str(y), size=10, fill=MUTED, anchor="middle"))
    lines = [(0, "value captured, all burnt waste", INK, 2.8),
             (1, "cement kilns' share of the fuel market", BLUE, 2.4),
             (2, "W202 chlorinated bottoms, value captured", RED, 2.4)]
    for idx, lab, col, wdt in lines:
        pts = [(cx(y), cy(rates[y][idx])) for y in YEARS if rates[y][idx] is not None]
        d = " ".join(f"{'M' if i == 0 else 'L'}{a:.1f},{b:.1f}" for i, (a, b) in enumerate(pts))
        s.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{wdt}"/>')
        s += halo(pts[-1][0] - 4, pts[-1][1] - 11, f"{rates[YEARS[-1]][idx]:.0%}", size=11,
                  fill=col, anchor="end")
    ly = BY + BH + 36
    for idx, lab, col, _ in lines:
        s.append(f'<rect x="{BX}" y="{ly-9:.1f}" width="12" height="3" fill="{col}"/>')
        s.append(txt(BX + 18, ly, lab, size=10.5, fill=col))
        ly += 16
    s += wrap(BX, ly + 6,
              "Flat black line: nothing became newly viable. Red: the one material that lost its "
              "fuel market, dropped by every class of buyer at once.",
              size=10.5, fill=INK2, chars=64)

    fy = H - 20 - 14 * 4
    s.append(f'<line x1="28" y1="{fy-22:.1f}" x2="{W-28}" y2="{fy-22:.1f}" stroke="{RULE}"/>')
    f1 = wrap(28, fy, "Every apparent crossover failed a check — W001 gained 71 points while its "
                      "tonnage grew sixteenfold, a code reused rather than a material adopted. The "
                      "buyer shift is only visible measured by receiving industry, because a NAICS "
                      "code cannot migrate the way a waste code does. Method in the recipe.",
              size=11, fill=INK2, chars=150, leading=14)
    s += f1
    s += wrap(28, fy + 14 * len(f1) + 6,
              "Cement kilns are NAICS 32731. Burnt waste is incineration, energy recovery, fuel "
              "blending and solvent reclamation; value captured is the last three. managed_tons on "
              "GM and WR rows, which do not overlap. 2021 publishes no tonnage and is omitted.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for y in YEARS:
        v, k, w, tb = rates[y]
        print(f"    {y}  burnt {tb/1e3:>7,.0f}k  value {v:>5.0%}  kiln share {k:>5.0%}  "
              f"W202 {('%.0f%%' % (w*100)) if w is not None else '  —':>5}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
