#!/usr/bin/env python3
"""What resolution to expect, and why the better-looking number is the one to distrust.

    python3 chart-9-expected-resolution.py

Cross resolution with size and method and the two methods behave completely differently.
**Crystallography pays a resolution penalty that scales with size** -- median 1.75 A below
50 kDa, climbing monotonically to 3.00 A above 1000. **Cryo-EM does not pay one at all**: 3.25,
3.00, 3.00, 3.25, 3.25, 3.25 A across the same six bands. It is size-indifferent.

**So the gap closes from 1.50 A to 0.25 A**, and on the median X-ray is ahead in every band,
including the largest.

**That last fact is a trap, and it is the point of the figure.** Above 1000 kDa the register
holds 701 X-ray structures and 5,040 cryo-EM ones, and figure 8 shows the field picks cryo-EM
there 97% of the time. Those 701 are not a sample of what crystallography does with a megadalton
complex. They are the ones that crystallised. Everything that did not is absent from the
register entirely, so the X-ray column at large size is a survivors' average and reads better
the harsher the filter that produced it.

**The prescriptive version.** Below about 100 kDa the X-ray median is a reasonable expectation,
because nearly everything of that size goes that route and the sample is barely filtered. Above
a few hundred, it is not an expectation of anything -- it is the score of the winners.

**One artefact to keep in view.** Resolution is histogrammed at 0.25 A, so every median here is
quantised to the bin, and the differences between adjacent bands are one or two bins wide.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdb as P, plate                                                   # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "9-expected-resolution.svg")
BANDS = ["0-50", "50-100", "100-200", "200-500", "500-1000", "1000-100000"]
MID = {"0-50": 25, "50-100": 70, "100-200": 141, "200-500": 316,
       "500-1000": 707, "1000-100000": 2000}
LAB = {"0-50": "under 50", "50-100": "50–100", "100-200": "100–200",
       "200-500": "200–500", "500-1000": "500–1000", "1000-100000": "over 1000"}
XR, EM = "X-RAY DIFFRACTION", "ELECTRON MICROSCOPY"
CXR, CEM, RED, GREEN = "#4a7fa8", "#8c2318", "#8c2318", "#1b7f5a"


def quant(h, q):
    pts = sorted((float(a), b) for a, b in h)
    n = sum(b for _, b in pts)
    if not n:
        return None
    c = 0
    for a, b in pts:
        c += b
        if c >= q * n:
            return a
    return pts[-1][0]


def main():
    d = P.load()
    sm = d["size_method"]
    st = {}
    for m in (XR, EM):
        st[m] = []
        for b in BANDS:
            h = sm[b]["resolution"].get(m)
            n = sum(x for _, x in h) if h else 0
            st[m].append({"band": b, "n": n,
                          "p10": quant(h, .10) if n else None,
                          "med": quant(h, .50) if n else None,
                          "p90": quant(h, .90) if n else None})

    W, H = 1200, 700
    s = plate.open_svg(W, H, "What resolution to expect, and why the better-looking "
                             "number is the one to distrust")
    fr, _ = plate.frame(W, 62,
                        who="anyone writing an expected resolution into a proposal",
                        decide="whether the median for your size and method is an expectation",
                        wrong="X-ray's median is flat across size the way cryo-EM's is")
    s += fr

    AX, AY, AH, AW = 28, 168, 430, 700
    lo, hi = 20, 2600
    x0, pw = AX + 46, AW - 86
    px = lambda v: x0 + pw * ((math.log10(v) - math.log10(lo))
                              / (math.log10(hi) - math.log10(lo)))
    rlo, rhi = 1.0, 7.0
    py = lambda r: AY + 8 + (AH - 76) * ((r - rlo) / (rhi - rlo))
    for r in (1, 2, 3, 4, 5, 6, 7):
        s.append(f'<line x1="{x0:.1f}" y1="{py(r):.1f}" x2="{px(hi):.1f}" y2="{py(r):.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(x0 - 8, py(r) + 3, f"{r}", size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, AY - 18, "resolution, ångström — the whole point is that lower is better",
                 size=11, fill=INK2))
    s += halo(x0 - 8, py(1.0) - 9, "better", size=8.5, fill=MUTED, anchor="end")
    s += halo(x0 - 8, py(7.0) + 15, "worse", size=8.5, fill=MUTED, anchor="end")
    for v in (25, 50, 100, 200, 500, 1000, 2000):
        s.append(f'<line x1="{px(v):.1f}" y1="{py(rhi):.1f}" x2="{px(v):.1f}" '
                 f'y2="{py(rhi)+5:.1f}" stroke="{MUTED}"/>')
        s.append(txt(px(v), py(rhi) + 18, f"{v:,}", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, py(rhi) + 36, "molecular weight of the deposited structure, kilodaltons "
                                   "(log scale)", size=10, fill=MUTED))

    for m, col, lab in ((EM, CEM, "cryo-EM"), (XR, CXR, "X-ray")):
        rows = [r for r in st[m] if r["n"]]
        band = ([f'{px(MID[r["band"]]):.1f},{py(r["p10"]):.1f}' for r in rows]
                + [f'{px(MID[r["band"]]):.1f},{py(r["p90"]):.1f}' for r in reversed(rows)])
        s.append(f'<polygon points="{" ".join(band)}" fill="{col}" fill-opacity="0.10"/>')
        pts = [(px(MID[r["band"]]), py(r["med"])) for r in rows]
        s.append('<path d="' + " ".join(("M" if i == 0 else "L") + f"{a:.1f},{b:.1f}"
                                        for i, (a, b) in enumerate(pts))
                 + f'" fill="none" stroke="{col}" stroke-width="2.8"/>')
        for (a, b), r in zip(pts, rows):
            s.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3.4" fill="{col}"/>')
        s += halo(pts[0][0] - 6, pts[0][1] + 3, lab, size=11, fill=col, anchor="end",
                  weight="700")
    s += halo(px(90), py(5.6), "shaded band is the 10th to 90th percentile",
              size=9.5, fill=MUTED)
    for b, dx in (("0-50", 0), ("1000-100000", 0)):
        i = BANDS.index(b)
        a, e = st[XR][i]["med"], st[EM][i]["med"]
        x = px(MID[b])
        s.append(f'<line x1="{x+dx:.1f}" y1="{py(a):.1f}" x2="{x+dx:.1f}" y2="{py(e):.1f}" '
                 f'stroke="{INK2}" stroke-width="1.2" stroke-dasharray="2 2"/>')
        s += halo(x + dx + 8, py((a + e) / 2) + 3, f"{e-a:.2f} Å apart",
                  size=9.5, fill=INK2, anchor="start", weight="700")

    BX, BY, BW = 790, 168, 382
    s.append(txt(BX, BY - 18, "the trap in the top band", size=12.5, fill=INK, weight="600"))
    y = BY + 12
    s += wrap(BX, y,
              "Above 1000 kDa X-ray's median reads better than cryo-EM's — 3.00 Å against "
              "3.25. Read straight, that says crystallise your megadalton complex.",
              size=11, fill=INK2, chars=52, leading=15)
    y += 62
    top = BANDS.index("1000-100000")
    rows = [("X-ray", st[XR][top]["n"], st[XR][top]["med"], CXR, "3.0%"),
            ("cryo-EM", st[EM][top]["n"], st[EM][top]["med"], CEM, "97.0%")]
    mxn = max(r[1] for r in rows)
    for name, n, med, col, sh in rows:
        s.append(txt(BX, y, name, size=10.5, fill=INK2, weight="600"))
        s.append(txt(BX + 62, y, f"{med:.2f} Å median", size=10.5, fill=col, weight="700"))
        w = (BW - 196) * n / mxn
        s.append(f'<rect x="{BX:.1f}" y="{y+7:.1f}" width="{max(w,2):.1f}" height="13" '
                 f'fill="{col}" fill-opacity="0.55"/>')
        s += halo(BX + max(w, 2) + 7, y + 17.5, f"{n:,} structures, {sh} of the band",
                  size=9.5, fill=col)
        y += 44
    y += 6
    s += wrap(BX, y,
              "Those 701 are not what crystallography does with a megadalton complex. They are "
              "the ones that crystallised. Nothing that failed is anywhere in the register, so "
              "the X-ray column is a survivors' average, and it reads better the harsher the "
              "filter behind it.",
              size=11, fill=INK, chars=52, leading=15)
    y += 92
    s.append(f'<rect x="{BX-10:.1f}" y="{y-16:.1f}" width="{BW+4:.1f}" height="86" '
             f'fill="{GREEN}" fill-opacity="0.07"/>')
    s.append(txt(BX, y, "so where is the median an expectation?", size=11, fill=GREEN,
                 weight="700"))
    s += wrap(BX, y + 18,
              "Below about 100 kDa, yes: nearly everything of that size goes the X-ray route, "
              "so the sample is barely filtered. Above a few hundred, no — it is the score of "
              "the winners, and cryo-EM's flat 3.25 Å is the more honest planning number.",
              size=10.5, fill=INK2, chars=54, leading=14)

    fy = H - 24 - 14 * 4
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"RCSB PDB search API, fetched {d['fetched']}; rcsb_entry_info.resolution_combined "
              f"against molecular_weight, {sum(r['n'] for m in (XR, EM) for r in st[m]):,} "
              f"structures carrying both. Resolution is histogrammed at 0.25 Å, so every median "
              f"here is quantised to the bin and adjacent bands differ by one or two bins. "
              f"Solution NMR is absent because it has no resolution: 4 of its 14,732 entries "
              f"carry the field at all, which is an annotation artefact rather than a "
              f"measurement. Points sit at each band's geometric midpoint, with the two open "
              f"ends placed at 25 and 2000 by hand.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for i, b in enumerate(BANDS):
        print(f"    {LAB[b]:>10} kDa   X-ray {st[XR][i]['med']} Å (n={st[XR][i]['n']:,})"
              f"   cryo-EM {st[EM][i]['med']} Å (n={st[EM][i]['n']:,})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
