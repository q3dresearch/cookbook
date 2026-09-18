#!/usr/bin/env python3
"""The parts every chart in this recipe shares, and the frame it has to declare.

    python3 plate.py        # print the frame each chart declares

**Why this exists.** The charts drifted. The first eight carried about 1,400 characters of
text each; by the fourteenth it was 3,244 characters against 27 drawn marks — a hundred and
twenty characters of prose per thing on the page. They had become essays with a graphic
attached, and the prose was method: how the null was built, which control was added, why a
figure was discarded. **That belongs in the recipe, which is long-form by design. The plate
has to carry the finding and what to do about it.**

They had also stopped saying who they were for. A reader could not tell from the page whether
a chart was addressed to a regulator, an entrant, or someone about to quote a number, nor what
they were supposed to do differently having read it.

So every chart now declares four things, and `frame()` puts three of them under the title in
the space the descriptive paragraph used to occupy:

- **for** — the reader it is addressed to, named as a role, not "the reader"
- **decide** — the choice in front of that reader, phrased as a choice and not a topic
- **wrong if** — the observation that would falsify it

The fourth is the title, which states the finding as a sentence rather than a subject.

**`wrong if` is the one that does the work.** A chart that cannot name what would falsify it is
usually describing rather than claiming, and that is worth discovering before it is published
rather than after someone asks.
"""
import os
import re
import sys
from xml.sax.saxutils import escape

SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"

# De-emphasised bars are drawn in FAINT, never in RULE or GRID. RULE was written to mean
# "hairline between blocks" and got reused as a bar fill for values that were real but not
# the point -- a circular predictor, an earlier period, a remainder. Against a GRID track
# that is a contrast ratio of **1.13:1**, so an 86% bar and a 0% bar looked identical and a
# reader reasonably read the data as zero. FAINT is 2.07:1 on the track: clearly secondary
# to a series colour at 3-4.3:1, and unmistakably present.
FAINT = "#aca89a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def txt(x, y, s, *, size, fill, anchor="start", weight="normal", spacing=None):
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}"{sp} style="font-variant-numeric: tabular-nums">'
            f'{escape(str(s))}</text>')


def halo(x, y, s, *, size, fill, anchor="start", weight="600"):
    """Two passes, because cairosvg ignores paint-order."""
    c = (f'font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" '
         f'style="font-variant-numeric: tabular-nums"')
    e = escape(str(s))
    return [f'<text x="{x:.1f}" y="{y:.1f}" fill="none" stroke="{SURFACE}" stroke-width="3.4" '
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


def frame(width, y, *, who, decide, wrong, x=28):
    """The three-cell strip under the title. Returns SVG and the y to carry on from."""
    cells = [("FOR", who, INK2), ("DECIDE", decide, INK2), ("WRONG IF", wrong, MUTED)]
    avail = width - 2 * x
    cw = avail / 3
    out, deepest = [], 0
    for i, (lab, body, col) in enumerate(cells):
        cx = x + i * cw
        out.append(txt(cx, y, lab, size=8.5, fill=MUTED, weight="700", spacing="0.9"))
        lines = wrap(cx, y + 15, body, size=11.5, fill=col, chars=int(cw / 6.1), leading=13.5)
        out += lines
        deepest = max(deepest, len(lines))
    end = y + 15 + deepest * 13.5
    out.append(f'<line x1="{x}" y1="{end-4:.1f}" x2="{width-x}" y2="{end-4:.1f}" stroke="{RULE}"/>')
    return out, end + 10


def open_svg(width, height, title, *, subtitle=None):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
         f'viewBox="0 0 {width} {height}" font-family=\'{FONT}\'>'
         f'<rect width="{width}" height="{height}" fill="{SURFACE}"/>',
         txt(28, 40, title, size=19, fill=INK, weight="600")]
    if subtitle:
        s.append(txt(28, 60, subtitle, size=12, fill=INK2))
    return s


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    pat = re.compile(r"plate\.frame\(\s*W,\s*\d+,\s*\n?\s*who=(.*?),\s*\n?\s*decide=(.*?),"
                     r"\s*\n?\s*wrong=(.*?)\)", re.S)
    for f in sorted(os.listdir(here)):
        if not f.startswith("chart-") or not f.endswith(".py"):
            continue
        m = pat.search(open(os.path.join(here, f)).read())
        n = f[len("chart-"):-len(".py")]
        if not m:
            print(f"  {n:<22} NO FRAME DECLARED")
            continue
        clean = lambda t: " ".join(re.findall(r'"([^"]*)"', t)) or "?"
        print(f"  {n}")
        for lab, g in (("for", 1), ("decide", 2), ("wrong if", 3)):
            print(f"      {lab:<9}{clean(m.group(g))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
