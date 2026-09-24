#!/usr/bin/env python3
"""Datasets with errors warn 12% more per file. Consistently, and far too little to use.

    python3 chart-13-warnings.py

One dot is one dataset, grouped by how many files it has, split by whether the validator also
raised an error.

**The first version of this plate was a scatter of warnings against files and a reader called
it random.** That was fair. Raw warnings track file count at **rho +0.81** -- the validator
emits a median 7.7 warnings per file -- so plotting one against the other draws that and buries
everything else. Both classes stacked on the same diagonal because the diagonal was the only
thing being drawn.

**Dividing by files removes the dominant term, and then the answer is visible.** In every file
band, datasets carrying an error warn slightly more per file: **1.11x, 1.11x, 1.15x, 1.25x**.
Four bands, unanimous in sign, on a pooled 1.12x at p = 0.013 -- and the file counts of the two
groups are the same (median 431 against 449), so it is not size in disguise.

**It is real and it is useless.** Warnings per file spans 2.5 at p10 to 20.6 at p90, an
eightfold spread, and the signal inside it is twelve percent. Ranking datasets by warning count
would sort them by size; ranking by warnings per file would sort them by noise. That is why the
raw correlation with errors reads **+0.034** -- not because nothing is there, but because what
is there cannot be acted on.

**The one thing the normalised form does earn.** Raw warning medians by validator generation
are noise -- v1 2,851, v2 3,602, v3 2,463. Per file they fall cleanly: **7.50, 6.31, 3.72**.
Like plate 3's error rates, the warning count is mostly telling you which validator ran.
"""
import hashlib, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bidsvalid, fold, plate                                            # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "13-warnings.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
YLO, YHI = 0.4, 120.0
COLW, GAPIN, GAPOUT = 56, 12, 38


def jx(did, n):
    h = int(hashlib.md5(did.encode()).hexdigest()[:8], 16)
    return ((h % 10000) / 10000.0 - 0.5) * COLW * min(0.8, 0.16 + 0.09 * math.sqrt(n))


def main():
    vr = {r["id"]: r for r in bidsvalid.rows()}
    rs = []
    for r in fold.load()["rows"]:
        v = vr.get(r["id"])
        if v and r["files"]:
            rs.append(dict(v, files=r["files"], wpf=v["warnings"] / r["files"]))
    cells = bidsvalid.warn_rate(rs)
    for c in cells:
        lo, hi = next((a, b) for a, b, lab in bidsvalid.FILE_BANDS if lab == c["band"])
        c["rows_c"] = [r for r in rs if lo <= r["files"] <= hi and r["errors"] == 0]
        c["rows_e"] = [r for r in rs if lo <= r["files"] <= hi and r["errors"] > 0]
    allw = sorted(r["wpf"] for r in rs)
    p10, p90 = allw[len(allw) // 10], allw[-len(allw) // 10]

    W, H = 1180, 770
    s = plate.open_svg(
        W, H, "Datasets with errors warn 12% more per file — consistently, and far too "
              "little to use",
        subtitle=f"{len(rs):,} OpenNeuro datasets. One dot is one dataset. Warnings are "
                 f"divided by file count, because raw warnings track files at rho +0.81 and "
                 f"draw nothing else.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone building a dataset quality score from validator output, or ranking "
            "deposits by how much the validator complained",
        decide="whether a warning count can separate a sound dataset from a broken one",
        wrong="the gap between the pairs is large relative to the spread within them, or it "
              "changes sign across file bands")
    s += fr

    AX, AY, AH = 232, y0 + 62, 382
    ay = lambda v: (AY + AH - (AH - 34) * (math.log10(min(max(v, YLO), YHI))
                                           - math.log10(YLO))
                    / (math.log10(YHI) - math.log10(YLO)))
    right = AX + len(cells) * (2 * COLW + GAPIN) + (len(cells) - 1) * GAPOUT
    for v in (1, 3, 10, 30, 100):
        s.append(f'<line x1="{AX-14:.1f}" y1="{ay(v):.1f}" x2="{right:.1f}" '
                 f'y2="{ay(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(AX - 22, ay(v) + 3, str(v), size=9, fill=MUTED, anchor="end"))
    s.append(f'<text x="{AX-54}" y="{ay(YLO):.1f}" font-size="10" fill="{INK2}" '
             f'transform="rotate(-90 {AX-54} {ay(YLO):.1f})">'
             f'warnings per file (log scale)</text>')
    s.append(f'<rect x="{AX-14:.1f}" y="{ay(p90):.1f}" width="{right-AX+14:.1f}" '
             f'height="{ay(p10)-ay(p90):.1f}" fill="{SLATE}" fill-opacity="0.07"/>')
    s += halo(AX - 14, ay(p90) - 8, f"shaded: p10 to p90 of every dataset, "
              f"{p10:.1f} to {p90:.1f} — an {p90/p10:.0f}x spread", size=9.5, fill=MUTED,
              weight="700")

    x = AX
    for c in cells:
        pair = []
        for key, col, lab in (("rows_c", SLATE, "no error"), ("rows_e", RED, "has an error")):
            g = c[key]
            med = c["med_c"] if key == "rows_c" else c["med_e"]
            cx = x + COLW / 2
            for r in g:
                s.append(f'<circle cx="{cx + jx(r["id"], len(g)):.1f}" '
                         f'cy="{ay(r["wpf"]):.1f}" r="2.3" fill="{col}" '
                         f'fill-opacity="0.38" stroke="none"/>')
            s.append(f'<line x1="{x:.1f}" y1="{ay(med):.1f}" x2="{x+COLW:.1f}" '
                     f'y2="{ay(med):.1f}" stroke="{col}" stroke-width="2.6"/>')
            s += halo(cx, ay(med) - 9, f"{med:.1f}", size=10.5, fill=col, anchor="middle",
                      weight="700")
            s.append(txt(cx, ay(YLO) + 22, f"{len(g)}", size=10, fill=col, anchor="middle",
                         weight="700"))
            if c is cells[0]:
                s.append(txt(cx, ay(YLO) + 36, lab, size=9, fill=col, anchor="middle"))
            pair.append((cx, ay(med)))
            x += COLW + (GAPIN if key == "rows_c" else GAPOUT)
        (x1, y1), (x2, y2) = pair
        top = min(y1, y2) - 24
        s.append(f'<path d="M{x1:.1f},{y1-5:.1f} L{x1:.1f},{top:.1f} L{x2:.1f},{top:.1f} '
                 f'L{x2:.1f},{y2-5:.1f}" fill="none" stroke="{INK2}" stroke-width="1"/>')
        s += halo((x1 + x2) / 2, top - 7, f"{c['ratio']:.2f}x", size=11, fill=INK,
                  anchor="middle", weight="700")
        s += halo((x1 + x2) / 2, ay(YLO) + 56, c["band"], size=9.5, fill=INK2,
                  anchor="middle", weight="700")
    s.append(txt(AX, ay(YLO) + 76, "files in the dataset", size=10, fill=INK2))

    TX, ty = right + 34, AY - 16
    for head, body, col in (
            ("the gap is real and unanimous",
             "Every file band points the same way — 1.11x, 1.11x, 1.15x, 1.25x — on a "
             "pooled 1.12x at p = 0.013, with the two groups having the same file counts.",
             INK),
            ("and it is unusable",
             f"The shaded band is p10 to p90 of every dataset: {p10:.1f} to {p90:.1f}. A "
             f"twelve percent signal inside an {p90/p10:.0f}x spread cannot rank anything.",
             RED),
            ("why the raw plot failed",
             "The first version drew warnings against files. That is rho +0.81 and nothing "
             "else, so both classes stacked on one diagonal and a reader called it random. "
             "Dividing out the dominant term is the whole job.", AMBER),
            ("what warnings do measure",
             "Which validator ran. Raw medians by generation are noise (2,851 / 3,602 / "
             "2,463); per file they fall cleanly, 7.50 / 6.31 / 3.72.", INK2)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        w = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=28, leading=12.5)
        s += w
        ty += 12.5 * len(w) + 14

    foot = (
        f"OpenNeuro GraphQL API, no key, fetched 2026-09-24; latestSnapshot.validation and "
        f"summary.totalFiles. A band is drawn only where both groups hold at least 15 "
        f"datasets, which excludes the over-10,000-file band. Ratios are of medians; p from "
        f"a seeded permutation test on the pooled difference. CAVEAT: a warning is not "
        f"designed as a quality score, and this plate does not claim the validator is wrong "
        f"— only that its warning count cannot be used as one.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for c in cells:
        print(f"    {c['band']:<14}clean {len(c['rows_c']):>4} @ {c['med_c']:>5.2f}   "
              f"err {len(c['rows_e']):>4} @ {c['med_e']:>5.2f}   {c['ratio']:.2f}x")
    print(f"    spread p10 {p10:.2f} p90 {p90:.2f} = {p90/p10:.0f}x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
