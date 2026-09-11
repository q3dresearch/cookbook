#!/usr/bin/env python3
"""One number has a floor. Everything else about the method is firm preference.

    python chart-people-not-data.py

A hero row and a table under it, in that order, because the previous version buried
the finding.

That version drew twelve probe rows with six dots each, coloured by business model,
with the extreme firm labelled at both ends of every row and the summary row at the
bottom — 84 marks and 78 labels, competing for a reader who wanted one sentence.
Worse, colour carried the fire-once/campaign split, which the data says is NOT
distinguishable by method (P = 0.065): the most prominent encoding in the figure was
a finding that does not exist.

So: the headline is a single line at the top, large. The detail is a shaded table,
which reads twelve rows of six numbers far better than seventy-two dots do. Colour
is one sequential ramp meaning one thing — how much of a firm's work uses that kind
of evidence — and nothing else.
"""
import re, sys, statistics
from math import comb
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpuslib, ctrllib, palette

OUT = Path(__file__).resolve().parents[1] / "charts" / "people-not-data.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, RULE = "#e1e0d9", "#c3c2b7", "#ebeae3"
HERO = "#1b4f8a"
# Sequential ramp, one hue, light to dark — magnitude, not identity.
RAMP = ["#f2f5f9", "#dce6f0", "#bcd0e4", "#94b3d4", "#6690c0", "#3c6ba6", "#1b4f8a"]
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
FIRMS = [("Hindenburg", None), ("Fuzzy Panda", "fuzzypanda"), ("Night Market", "nightmarket"),
         ("Muddy Waters", "muddywaters"), ("J Capital", "jcapital"), ("Spruce Point", "sprucepoint")]


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


def shade(v):
    return RAMP[min(len(RAMP) - 1, int(v * len(RAMP)))]


def measure():
    corpora = {}
    for label, key in FIRMS:
        if key is None:
            corpora[label] = (corpuslib.load("initial"), corpuslib.probes(label), corpuslib.body)
        else:
            init, _ = ctrllib.first_look(key)
            corpora[label] = (init, corpuslib.probes(label), lambda d: d["text"])
    for w in ctrllib.audit_probes(corpora):
        print(f"    audit: {w}")
    P = corpuslib.probes()
    rows = []
    for lab in P:
        rows.append((lab, [sum(1 for d in ds if re.search(Pf[lab], g(d), re.I)) / len(ds)
                           for ds, Pf, g in corpora.values()]))
    PRIV = corpuslib.BARRIER["needs presence"] + corpuslib.BARRIER["needs luck"]
    hero = [sum(1 for d in ds if any(re.search(Pf[k], g(d), re.I) for k in PRIV)) / len(ds)
            for ds, Pf, g in corpora.values()]
    counts = [len(ds) for ds, _, _ in corpora.values()]
    rows.sort(key=lambda r: -statistics.median(r[1]))
    return rows, hero, counts


def main():
    rows, hero, counts = measure()
    assert palette.check([RAMP[0], RAMP[3], RAMP[6]], label="sequential ramp ends")

    W = 940.0
    LBL, CELL, GAP = 210.0, 104.0, 2.0
    TOPH, ROWH = 250.0, 26.0
    H = TOPH + 96 + len(rows) * ROWH + 120
    def CX(i): return LBL + i * CELL

    el = [f'<rect width="{W}" height="{H:.0f}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "The barrier is people, not data", size=20, fill=INK, weight="600"))
    lead, dy = para(24, 58, "Share of each firm's first-look reports citing each kind of evidence. "
                    "Six firms, 273 reports, 2010 to 2026.", size=12.5, fill=INK2, chars=118)
    el += lead

    # ---- hero: one row, large
    hy = 58 + dy + 40
    lo, hi = min(hero), max(hero)
    el.append(txt(24, hy, "reports resting on a person who agreed to talk", size=13,
                  fill=INK, weight="600"))
    hx0, hx1 = LBL, W - 108
    def HX(v): return hx0 + v * (hx1 - hx0)
    hyy = hy + 56
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        el.append(f'<line x1="{HX(v):.1f}" y1="{hyy-24:.1f}" x2="{HX(v):.1f}" y2="{hyy+16:.1f}" '
                  f'stroke="{GRID}" stroke-width="1"/>')
        el.append(txt(HX(v), hyy + 30, f"{v:.0%}", size=10.5, fill=MUTED, anchor="middle", tab=True))
    el.append(f'<line x1="{HX(lo):.1f}" y1="{hyy:.1f}" x2="{HX(hi):.1f}" y2="{hyy:.1f}" '
              f'stroke="{BASELINE}" stroke-width="4" stroke-linecap="round"/>')
    # Four of the six sit within seven points of each other, so labelling each one
    # stacks four names on top of each other. The cluster gets a bracket and a count;
    # only the two firms outside it are named, which is also what a reader wants.
    order = sorted(range(len(hero)), key=lambda i: hero[i])
    med = statistics.median(hero)
    inner = [i for i in order if abs(hero[i] - med) <= 0.06]
    outer = [i for i in order if i not in inner]
    for i in order:
        el.append(f'<circle cx="{HX(hero[i]):.1f}" cy="{hyy:.1f}" r="9" fill="{HERO}" '
                  f'fill-opacity="0.9" stroke="{SURFACE}" stroke-width="2"/>')
    for i in outer:
        el.append(txt(HX(hero[i]), hyy - 32, FIRMS[i][0], size=11, fill=INK,
                      anchor="middle", weight="600"))
        el.append(txt(HX(hero[i]), hyy - 18, f"{hero[i]:.0%}", size=10.5, fill=INK2,
                      anchor="middle", tab=True))
    if inner:
        a, b = HX(min(hero[i] for i in inner)), HX(max(hero[i] for i in inner))
        el.append(f'<path d="M{a-9:.1f},{hyy-16:.1f} v-7 H{b+9:.1f} v7" fill="none" '
                  f'stroke="{MUTED}" stroke-width="1.3"/>')
        mid = (a + b) / 2
        el.append(txt(mid, hyy - 32, f"{len(inner)} firms", size=11, fill=INK,
                      anchor="middle", weight="600"))
        el.append(txt(mid, hyy - 18, f"{min(hero[i] for i in inner):.0%}-"
                      f"{max(hero[i] for i in inner):.0%}", size=10.5, fill=INK2,
                      anchor="middle", tab=True))

    # The headline, as a number. It was lost in a rewrite of this block and the
    # figure shipped once with the hero row and no hero.
    el.append(txt(24, hyy + 2, f"{lo:.0%} to {hi:.0%}", size=23, fill=HERO, weight="700", tab=True))
    el.append(txt(24, hyy + 22, "across six firms; none below", size=10.5, fill=MUTED))
    el.append(txt(hx1 + 12, hyy - 2, f"{med:.0%}", size=14, fill=INK, weight="600", tab=True))
    el.append(txt(hx1 + 12, hyy + 12, "median", size=10, fill=MUTED))

    # ---- table
    ty = hyy + 74
    el.append(txt(24, ty - 12, "every other measure, for comparison", size=12, fill=INK2, weight="600"))
    for i, (name, _) in enumerate(FIRMS):
        short = name.split()[0] if name != "Muddy Waters" else "Muddy"
        el.append(txt(CX(i) + CELL / 2 - GAP, ty + 4, short, size=10.5, fill=INK2,
                      anchor="middle", weight="600"))
        el.append(txt(CX(i) + CELL / 2 - GAP, ty + 16, f"n={counts[i]}", size=9.5,
                      fill=MUTED, anchor="middle", tab=True))
    ty += 28
    for r, (lab, vals) in enumerate(rows):
        y = ty + r * ROWH
        el.append(txt(LBL - 14, y + ROWH / 2 + 4, lab, size=11.5, fill=INK2, anchor="end"))
        for i, v in enumerate(vals):
            el.append(f'<rect x="{CX(i):.1f}" y="{y:.1f}" width="{CELL-GAP:.1f}" '
                      f'height="{ROWH-GAP:.1f}" fill="{shade(v)}"/>')
            el.append(txt(CX(i) + CELL / 2 - GAP, y + ROWH / 2 + 4, f"{v:.0%}", size=11,
                          fill="#ffffff" if v >= 0.57 else INK, anchor="middle", tab=True))

    by = ty + len(rows) * ROWH + 26
    el.append(txt(LBL - 14, by + 4, "share of that firm's reports", size=10.5, fill=MUTED, anchor="end"))
    for i, c in enumerate(RAMP):
        el.append(f'<rect x="{LBL + i*30:.1f}" y="{by-9:.1f}" width="28" height="13" fill="{c}"/>')
    el.append(txt(LBL, by + 18, "0%", size=10, fill=MUTED, tab=True))
    el.append(txt(LBL + len(RAMP) * 30 - 2, by + 18, "100%", size=10, fill=MUTED, anchor="end", tab=True))

    p = 2 / comb(len(FIRMS), 2)
    cap, _ = para(24, by + 52, "First-look reports only — a firm's first report on each target. "
                  "Follow-ups cite almost nothing and pooling them in reverses firm rankings. "
                  "Detection is keyword-based on what a report declares, so every cell is a floor: "
                  "a firm that uses a terminal without naming it is invisible. The fire-once and "
                  "campaign business models are NOT distinguishable on any of these measures "
                  f"(P = 0.065), which is why nothing here is coloured by them.",
                  size=11, fill=MUTED, chars=150, leading=15)
    el += cap
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print(f"  charts/people-not-data.svg — hero {lo:.0%}-{hi:.0%}, {len(rows)} rows x {len(FIRMS)} firms")


if __name__ == "__main__":
    main()
