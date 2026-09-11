#!/usr/bin/env python3
"""They find crime at four times the base rate — and not by reading the margins.

    python chart-two-jackpots.py

Two things are worth proving about a company: that its unit economics do not work, or
that a crime is happening. Both are checkable from SEC filings alone, which is what
makes them reachable without sources.

**The top band is the premise.** A short-seller target discloses a Wells notice, grand
jury, subpoena or formal order of investigation within three years at 13/59 = 22%,
against 6/108 = 6% for control filers given a report date drawn from the target
distribution so the exposure matches. That is 4.0x at Fisher p = 0.002 — the strongest
and best-powered result in this recipe. These firms find crime.

**The plot below is how they do not do it.** Targets that went on to disclose an
investigation had a median pre-report operating margin of +17%; those that did not,
-1%. Visibly broken economics led to an investigation 2/21 = 10% of the time,
economics that looked fine 5/20 = 25%. The sign is backwards from the intuition, and
it is backwards at every window from two to five years.

Three things this chart is careful about, each of which changed the answer.

**Exposure is matched, because it decides the result.** A target attacked in 2014 has
twelve years to disclose something; one attacked in 2025 has months. The
broken-economics targets have a median report year of 2022 against 2020 for the rest —
two years less at risk. Counting "ever disclosed after" gave 11% vs 33% at p = 0.09;
the fixed three-year window gives 10% vs 25% at p = 0.24. The first number was
flattered by the clock.

**The lower panel is not significant and is not presented as if it were.** Seven
investigated companies is far too few. What it has is a stable sign, shown across four
windows at the foot rather than asserted. The claim it supports is the negative one:
nothing here suggests bad numbers lead you to the crime.

**A short report can cause the investigation it appears to predict.** Regulators read
these. Nothing in this data separates "found a company already under investigation"
from "caused one", and that distinction matters enormously to anyone trying to do the
same thing. It would need the date a file was opened, which is not public.
"""
import json, statistics, sys
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import palette
from jackpot import broken, meaningful, enforced, enforced_at, WINDOW_YEARS
from selection import fisher

RAW = HERE.parent / "raw"
OUT = HERE.parent / "charts" / "two-jackpots.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, RULE = "#e1e0d9", "#ebeae3"
HOT, COOL = "#b03a2e", "#1b4f8a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
W, H = 980, 830


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


def main():
    T = json.loads((RAW / "jackpot_targets.json").read_text())
    pts = []
    for sym, v in T.items():
        e = v["economics"]
        om = e.get("operating_margin")
        # enforced() returns None when the three-year window has not closed, and such a
        # company is dropped rather than counted as a no. Using "ever disclosed after"
        # instead gives an older target twelve years of exposure against a recent one's
        # months -- and the split is not random, so that alone moves the answer.
        hit = enforced(v)
        if not meaningful(e) or om is None or hit is None:
            continue
        pts.append({"sym": sym, "firm": v["firm"], "om": om, "enf": hit,
                    "n_enf": len(v["enforcement"]["after"])})
    if not pts:
        raise SystemExit("no plottable targets")

    # Margins run from about -1 to +0.5 with a long negative tail; clip the tail to a
    # gutter rather than letting one company set the scale for everyone else.
    LO, HI = -1.0, 0.5
    for p in pts:
        p["clip"] = p["om"] < LO
        p["x"] = max(LO, min(HI, p["om"]))

    yes = [p for p in pts if p["enf"]]
    no = [p for p in pts if not p["enf"]]
    a, b, c, d = len(yes), len(no), 0, 0
    # Fisher on the actual 2x2: broken/not x investigated/not.
    bb = [p for p in pts if broken(T[p["sym"]]["economics"])]
    gg = [p for p in pts if not broken(T[p["sym"]]["economics"])]
    A = sum(p["enf"] for p in bb); B = len(bb) - A
    C = sum(p["enf"] for p in gg); D = len(gg) - C
    p_val = fisher(A, B, C, D)

    # Row labels sit ABOVE each row, not beside it: right-anchored labels in a left
    # margin were clipped at every width that left room for the plot.
    L, R, TOP = 56, 56, 280
    pw = W - L - R
    sx = lambda v: L + (v - LO) / (HI - LO) * pw
    rows = [(f"Disclosed an investigation within {WINDOW_YEARS} years", yes, HOT, TOP + 74),
            ("No investigation disclosed", no, COOL, TOP + 232)]

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    s.append(txt(L, 46, "You cannot find the crime by screening for bad numbers",
                 size=21, fill=INK, weight="600"))
    body, dy = para(L, 72, "Every short-seller target whose last annual figures before the report can be read "
                    f"and whose {WINDOW_YEARS}-year window has closed, placed by operating margin. The "
                    "companies that went on to disclose a Wells notice, grand jury, subpoena or formal "
                    "order of investigation sit to the RIGHT — their margins looked better, not worse.",
                    size=13, fill=INK2, chars=104)
    s += body

    # The premise band. Without it the chart reads as "short sellers find nothing",
    # which is the opposite of what the control comparison says: they find crime at
    # nearly four times the base rate. What they do not do is find it in the margins.
    import random
    CTRL = json.loads((RAW / "jackpot_controls.json").read_text())
    dates = sorted(v["as_of"] for v in T.values())
    rnd = random.Random(20260912)
    tk = [x for x in (enforced(v) for v in T.values()) if x is not None]
    ck = [x for x in (enforced_at(v, rnd.choice(dates)) for v in CTRL.values()) if x is not None]
    bands = [("short-seller targets", sum(tk), len(tk), HOT),
             ("matched control filers", sum(ck), len(ck), COOL)]
    by = 78 + dy + 26
    s.append(txt(L, by - 12, f"They do find crime. Share disclosing an investigation within "
                 f"{WINDOW_YEARS} years:", size=12, fill=INK, weight="600"))
    # Bars run a stated 0-30% scale, not a silent multiplier. A bar whose length is not
    # proportional to its number is the one chart lie that is never worth telling.
    BAR_MAX, bw, x0 = 0.30, 300, L + 170
    for i, (lab, k, n, col) in enumerate(bands):
        yy = by + i * 26
        s.append(txt(L, yy + 11, lab, size=11.5, fill=INK2))
        s.append(f'<rect x="{x0}" y="{yy}" width="{bw}" height="14" rx="3" fill="{RULE}"/>')
        s.append(f'<rect x="{x0}" y="{yy}" width="{bw * (k / n) / BAR_MAX:.1f}" height="14" '
                 f'rx="3" fill="{col}"/>')
        s.append(txt(x0 + bw + 12, yy + 11, f"{k}/{n} = {k/n:.0%}", size=11.5, fill=col,
                     weight="600", tab=True))
    s.append(txt(x0, by + 2 * 26 + 12, "0%", size=10, fill=MUTED, anchor="middle"))
    s.append(txt(x0 + bw, by + 2 * 26 + 12, f"{BAR_MAX:.0%}", size=10, fill=MUTED, anchor="middle"))
    lift = (sum(tk) / len(tk)) / (sum(ck) / len(ck))
    pv = fisher(sum(tk), len(tk) - sum(tk), sum(ck), len(ck) - sum(ck))
    s.append(txt(x0 + bw + 110, by + 24, f"{lift:.1f}x,  Fisher p = {pv:.4f}",
                 size=12, fill=INK, weight="600", tab=True))
    s.append(f'<line x1="{L}" y1="{TOP - 22}" x2="{W - R}" y2="{TOP - 22}" stroke="{RULE}" stroke-width="1"/>')
    s.append(txt(L, TOP - 2, "But not by reading the margins.", size=13, fill=INK, weight="600"))

    # Zero line: the whole claim is about which side of it the dots fall on.
    z = sx(0)
    BOT = TOP + 330
    s.append(f'<line x1="{z:.1f}" y1="{TOP + 20}" x2="{z:.1f}" y2="{BOT}" '
             f'stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="4 3"/>')
    s.append(txt(z, TOP + 12, "break-even", size=11, fill=MUTED, anchor="middle"))
    # Typographic minus (U+2212) and <= (U+2264) render as tofu boxes under cairosvg's
    # fallback font, so the axis uses ASCII. Checked by looking at the PNG, not assumed.
    for v, lab in ((-1.0, "-100% or worse"), (-0.5, "-50%"), (0.0, "0%"), (0.5, "+50%")):
        x = sx(v)
        if v:
            s.append(f'<line x1="{x:.1f}" y1="{TOP + 20}" x2="{x:.1f}" y2="{BOT}" '
                     f'stroke="{RULE}" stroke-width="1"/>')
        s.append(txt(x, BOT + 20, lab, size=11, fill=MUTED, anchor="middle", tab=True))
    s.append(txt(L + pw / 2, BOT + 42, "operating margin at the last annual report filed before the short report",
                 size=12, fill=INK2, anchor="middle"))

    for label, group, col, y in rows:
        s.append(txt(L, y - 40, label, size=13, fill=col, weight="600"))
        s.append(txt(L, y - 24, f"{len(group)} companies", size=11, fill=MUTED, tab=True))
        # Dodge overlapping dots vertically instead of letting them hide each other.
        placed = []
        for p in sorted(group, key=lambda q: q["x"]):
            x, lane = sx(p["x"]), 0
            while any(abs(x - px) < 11 and lane == pl for px, pl in placed):
                lane += 1
            placed.append((x, lane))
            cy = y + lane * 13
            s.append(f'<circle cx="{x:.1f}" cy="{cy:.1f}" r="5.5" fill="{col}" '
                     f'fill-opacity="0.85" stroke="{SURFACE}" stroke-width="2"/>')
            if p["clip"]:
                s.append(f'<path d="M{x - 9:.1f} {cy - 5} l-5 5 l5 5" fill="none" '
                         f'stroke="{col}" stroke-width="1.5"/>')
        med = statistics.median([p["x"] for p in group])
        mx = sx(med)
        s.append(f'<line x1="{mx:.1f}" y1="{y - 18}" x2="{mx:.1f}" y2="{y + 30}" '
                 f'stroke="{col}" stroke-width="2.5"/>')
        s.append(txt(mx, y - 24, f"median {med:+.0%}", size=11, fill=col,
                     anchor="middle", weight="600", tab=True))

    # Name a few of the investigated companies -- the reader needs entities, not counts.
    # Labels are placed left to right and any that would collide is dropped rather than
    # drawn on top of its neighbour; four tickers previously overprinted into "EQDFH".
    ny, last = rows[0][3] + 46, -1e9
    for p in sorted(yes, key=lambda q: q["x"]):
        x = sx(p["x"])
        if x - last < 46:
            continue
        last = x
        s.append(txt(x, ny, p["sym"], size=10.5, fill=HOT, anchor="middle", weight="600"))

    fy = BOT + 76
    s.append(f'<line x1="{L}" y1="{fy - 20}" x2="{W - R}" y2="{fy - 20}" stroke="{RULE}" stroke-width="1"/>')
    foot, h = para(L, fy, f"Visibly broken economics: {A}/{A + B} investigated. Economics that looked "
                   f"fine: {C}/{C + D}. Fisher p = {p_val:.2f} — NOT significant, and {A + C} "
                   f"investigated companies in total is far too few to be. What the chart supports is "
                   f"the negative: nothing here suggests bad numbers lead to the crime, and the sign "
                   f"runs the other way in every window tested. A company losing money in public is not "
                   f"hiding anything; fraud has to look healthy.",
                   size=12, fill=INK2, chars=112)
    s += foot

    # Show the window sensitivity rather than asserting the choice was safe. The reader
    # can see the direction is stable and that none of it reaches significance.
    wy = fy + h + 14
    s.append(txt(L, wy, "Same comparison at other windows — direction stable, none significant:",
                 size=11, fill=MUTED))
    # Same sample as the panel above -- requiring operating margin, not margin-or-burn --
    # so the 3-year cell reproduces the footer exactly instead of quietly differing.
    cells = []
    for w in (2, 3, 4, 5):
        rr = [v for v in T.values() if meaningful(v["economics"])
              and v["economics"].get("operating_margin") is not None
              and broken(v["economics"]) is not None and enforced(v, w) is not None]
        a2 = sum(1 for v in rr if broken(v["economics"]) and enforced(v, w))
        b2 = sum(1 for v in rr if broken(v["economics"]) and not enforced(v, w))
        c2 = sum(1 for v in rr if not broken(v["economics"]) and enforced(v, w))
        d2 = sum(1 for v in rr if not broken(v["economics"]) and not enforced(v, w))
        if not (a2 + b2) or not (c2 + d2):
            continue
        cells.append(f"{w}y: broken {a2/(a2+b2):.0%} vs fine {c2/(c2+d2):.0%}  "
                     f"p={fisher(a2, b2, c2, d2):.2f}")
    for i, c in enumerate(cells):
        s.append(txt(L + i * 215, wy + 20, c, size=11, fill=INK2, tab=True))
    s.append("</svg>")
    OUT.write_text("\n".join(s))
    print(f"  {OUT.name}: {len(pts)} targets ({len(yes)} investigated, {len(no)} not)")
    print(f"  broken {A}/{A + B} = {A/(A+B):.0%} investigated  |  fine {C}/{C + D} = {C/(C+D):.0%}"
          f"  |  Fisher p = {p_val:.4f}")
    print(f"  median operating margin: investigated {statistics.median([p['x'] for p in yes]):+.0%}"
          f"  not {statistics.median([p['x'] for p in no]):+.0%}")


if __name__ == "__main__":
    main()
