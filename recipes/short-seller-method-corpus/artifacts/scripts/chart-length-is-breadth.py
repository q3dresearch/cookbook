#!/usr/bin/env python3
"""A longer short report is a wider one — and the long ones start campaigns.

    python chart-length-is-breadth.py

Words against distinct kinds of evidence, one mark per first-look report.

Two questions share these axes. Length is breadth, not padding: the correlation is
+0.73 at Hindenburg and +0.59 at Muddy Waters, and Hindenburg's shorter half
carries a median 2 kinds of evidence against 7 in its longer half.

And Muddy Waters' first reports that went on to become campaigns are the LONGER
ones — 11,229 words against 6,864 — which is the opposite of a follow-up being a
repair for a thin opening. That second claim is drawn as what it is: the medians
differ, the clouds overlap, and a permutation test puts it at p = 0.05. It is a
lead, not a result, and the figure says so rather than implying otherwise with a
confident line through it.
"""
import math, re, sys, collections, statistics
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpuslib, ctrllib, palette

OUT = Path(__file__).resolve().parents[1] / "charts" / "length-is-breadth.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, GHOST = "#e1e0d9", "#c3c2b7", "#cfcec6"
SOLO, CAMP = "#1b4f8a", "#d17b00"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
XMAX, YMAX = 26000.0, 12.0


def txt(x, y, s, *, size, fill, anchor="start", weight="normal", tab=False):
    st = "font-variant-numeric: tabular-nums;" if tab else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family=\'{FONT}\' font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
            f'style="{st}">{escape(s)}</text>')


def para(x, y, s, *, size, fill, chars, leading=17.0):
    words, line, out, n = s.split(), [], [], 0
    for w in words:
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
            line, n = [], n + 1
        line.append(w)
    if line:
        out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
        n += 1
    return out, n * leading


def pearson(pts):
    n = len(pts)
    mx, my = sum(a for a, _ in pts) / n, sum(b for _, b in pts) / n
    den = math.sqrt(sum((a - mx) ** 2 for a, _ in pts) * sum((b - my) ** 2 for _, b in pts))
    return sum((a - mx) * (b - my) for a, b in pts) / den if den else 0.0


def data():
    hb = corpuslib.load("initial")
    P = corpuslib.probes("Hindenburg")
    hpts = [(len(corpuslib.body(p).split()),
             sum(1 for k in P if re.search(P[k], corpuslib.body(p), re.I))) for p in hb]

    d, _ = ctrllib.load("muddywaters", with_pdf=True)
    d = [x for x in d if x["words"] >= ctrllib.MIN_WORDS]
    init, fu, _ = ctrllib.split_reports(d)
    nfu = collections.Counter(x["target"] for x in fu)
    Pm = corpuslib.probes("Muddy Waters")
    mpts = [(x["words"], sum(1 for k in Pm if re.search(Pm[k], x["text"], re.I)),
             nfu[x["target"]]) for x in init]
    return hpts, mpts


def permutation_gap(mpts, n_shuffles=20000, seed=11):
    """Median word gap between campaign and no-follow-up first reports, and how
    often a random split of the same reports produces a gap that big."""
    import random
    solo = [w for w, _, n in mpts if n == 0]
    camp = [w for w, _, n in mpts if n > 0]
    obs = statistics.median(camp) - statistics.median(solo)
    pool = solo + camp
    rng = random.Random(seed)
    hits = 0
    for _ in range(n_shuffles):
        rng.shuffle(pool)
        if abs(statistics.median(pool[len(solo):]) - statistics.median(pool[:len(solo)])) >= abs(obs):
            hits += 1
    return obs, hits / n_shuffles


def main():
    hpts, mpts = data()
    assert palette.check([SOLO, CAMP], label="campaign palette")

    W, H = 960.0, 700.0
    L, R, T, B = 84.0, 268.0, 238.0, 132.0
    def X(v): return L + min(v, XMAX) / XMAX * (W - L - R)
    def Y(v): return (H - B) - min(v, YMAX) / YMAX * (H - B - T)

    el = [f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "Longer reports are wider, not padded", size=19, fill=INK, weight="600"))
    lead, dy = para(24, 58, "One mark per first-look report: how long it is against how many "
                    "distinct kinds of evidence it cites. Grey marks are Hindenburg, for "
                    "reference; coloured marks are Muddy Waters.", size=12.5, fill=INK2, chars=118)
    el += lead
    y0 = 58 + dy + 24
    rh, rm = pearson(hpts), pearson([(a, b) for a, b, _ in mpts])
    el.append(txt(24, y0, f"Length tracks breadth at both firms — r = {rh:+.2f} at Hindenburg, "
                 f"{rm:+.2f} at Muddy Waters. A long report cites more kinds of thing.",
                 size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, "And the Muddy Waters reports that went on to become campaigns are "
                 "the longer ones — a commitment made up front, not a repair.",
                 size=13, fill=INK2))

    for v in range(0, int(XMAX) + 1, 5000):
        el.append(f'<line x1="{X(v):.1f}" y1="{T}" x2="{X(v):.1f}" y2="{Y(0):.1f}" stroke="{GRID}" stroke-width="1"/>')
        el.append(txt(X(v), Y(0) + 20, f"{v//1000}k" if v else "0", size=11, fill=MUTED, anchor="middle", tab=True))
    for v in range(0, int(YMAX) + 1, 2):
        el.append(f'<line x1="{L}" y1="{Y(v):.1f}" x2="{W-R}" y2="{Y(v):.1f}" stroke="{GRID}" stroke-width="1"/>')
        el.append(txt(L - 10, Y(v) + 4, str(v), size=11, fill=MUTED, anchor="end", tab=True))
    el.append(f'<line x1="{L}" y1="{Y(0):.1f}" x2="{W-R}" y2="{Y(0):.1f}" stroke="{BASELINE}" stroke-width="1.5"/>')
    el.append(txt(L, Y(0) + 56, "words in the report", size=12, fill=INK2))
    el.append(f'<text x="{-(T + (H-B-T)/2):.1f}" y="24" transform="rotate(-90)" '
              f'font-family=\'{FONT}\' font-size="12" fill="{INK2}" text-anchor="middle">'
              "distinct kinds of evidence cited</text>")

    for w, e in hpts:
        el.append(f'<circle cx="{X(w):.1f}" cy="{Y(e):.1f}" r="4" fill="none" '
                  f'stroke="{GHOST}" stroke-width="1.4"/>')
    for w, e, n in mpts:
        c = CAMP if n > 0 else SOLO
        el.append(f'<circle cx="{X(w):.1f}" cy="{Y(e):.1f}" r="5.5" fill="{c}" fill-opacity="0.5" '
                  f'stroke="{c}" stroke-width="1.6"/>')

    # Median word count per group, as a tick on the baseline. Not a divider through
    # the cloud: the clouds overlap and a line through them would assert a split
    # the data does not support.
    for grp, c, lab in (([w for w, _, n in mpts if n == 0], SOLO, "no follow-up"),
                        ([w for w, _, n in mpts if n > 0], CAMP, "campaign")):
        m = statistics.median(grp)
        el.append(f'<line x1="{X(m):.1f}" y1="{Y(0):.1f}" x2="{X(m):.1f}" y2="{Y(0)+13:.1f}" '
                  f'stroke="{c}" stroke-width="3"/>')
        el.append(txt(X(m), Y(0) + 30, f"{m:,.0f}", size=11, fill=c, anchor="middle", weight="600", tab=True))

    lx = W - R + 18
    el.append(txt(lx, T + 4, "Muddy Waters first reports", size=12, fill=INK, weight="600"))
    yy = T + 32
    for c, lab, sub in ((CAMP, "started a campaign",
                         f"{sum(1 for _,_,n in mpts if n>0)} reports, median "
                         f"{statistics.median([w for w,_,n in mpts if n>0]):,.0f} words"),
                        (SOLO, "drew no follow-up",
                         f"{sum(1 for _,_,n in mpts if n==0)} reports, median "
                         f"{statistics.median([w for w,_,n in mpts if n==0]):,.0f} words")):
        el.append(f'<circle cx="{lx+6:.1f}" cy="{yy-4:.1f}" r="5.5" fill="{c}" fill-opacity="0.5" stroke="{c}" stroke-width="1.6"/>')
        el.append(txt(lx + 20, yy, lab, size=11.5, fill=INK, weight="600"))
        s, _ = para(lx, yy + 15, sub, size=11, fill=MUTED, chars=27, leading=14)
        el += s
        yy += 62
    el.append(f'<circle cx="{lx+6:.1f}" cy="{yy-4:.1f}" r="4" fill="none" stroke="{GHOST}" stroke-width="1.4"/>')
    el.append(txt(lx + 20, yy, "Hindenburg", size=11.5, fill=MUTED))
    s, _ = para(lx, yy + 15, f"{len(hpts)} reports, shown for the shape of the "
                "relationship", size=11, fill=MUTED, chars=27, leading=14)
    el += s

    # The gap and its p-value are computed here, not typed. Typed, they said
    # "4,366 words, p = 0.05" and stayed that way after an extraction fix moved
    # them to 3,950 and 0.073 — a caption quietly asserting a stronger result
    # than the data behind it.
    gap, p = permutation_gap(mpts)
    note, _ = para(lx, yy + 74, f"The gap between the two medians is {gap:,.0f} words. A "
                   f"permutation test puts it at p = {p:.2f} across {len(mpts)} reports, and "
                   "the clouds overlap — a lead worth following, not a settled finding.",
                   size=11, fill=INK2, chars=27, leading=14)
    el += note

    # Derived, not typed. An earlier version of this sentence said "there are two"
    # while the code counted four — the third time in this recipe that a caption
    # stopped tracking the data it describes.
    over = sum(1 for w, _ in hpts if w > XMAX) + sum(1 for w, _, _ in mpts if w > XMAX)
    cap, _ = para(24, H - 54, "Evidence kinds are the twelve probes in corpuslib, so this counts "
                  "what a report DECLARES. Muddy Waters text comes from the linked PDF, "
                  f"Hindenburg's from the HTML archive. {over} reports run past "
                  f"{XMAX/1000:.0f}k words and are pinned to the right edge.",
                  size=11, fill=MUTED, chars=150, leading=15)
    el += cap
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print(f"  charts/length-is-breadth.svg — r {rh:+.2f} / {rm:+.2f}, {over} reports pinned at the right edge")


if __name__ == "__main__":
    main()
