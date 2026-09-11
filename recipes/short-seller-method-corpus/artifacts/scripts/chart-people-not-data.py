#!/usr/bin/env python3
"""Where activist short sellers agree, and where they do not.

    python chart-people-not-data.py

One row per kind of evidence, one dot per firm. Rows where the dots cluster are
the practice; rows where they spread are a firm's signature.

The row that matters is the bottom one. Every other measure splits the firms —
Hindenburg lives in court records, Muddy Waters buys terminal data, Night Market
does neither — but the share of reports resting on a person who agreed to talk is
67%, 71% and 70%. Three firms, different targets, different decades, opposite
publishing models.

The "original interviews" row did not exist until the control corpus forced it.
The probe list was written by reading Hindenburg, so it named Hindenburg's habits;
Night Market scored zero on original sourcing while its reports described FOIA
requests and interviews at trade conferences. That omission is why the recipe
previously reported that half of a short report is reproducible from public data.
It is one fifth.
"""
import re, sys
from math import comb
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpuslib, ctrllib, palette

OUT = Path(__file__).resolve().parents[1] / "charts" / "people-not-data.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, BAND, GHOSTPP = "#e1e0d9", "#c3c2b7", "#ebeae3", "#b3b2aa"
# Four firms, and four categorical hues do not survive the CVD check — the best
# four-set tested fails tritanopia at delta-E 3.5. So hue carries the CAMP, which is
# the comparison this figure exists for, and fill separates the two firms inside
# each camp. Two hues, validated; identity never rests on colour alone because
# every row is also labelled in the legend.
ONESHOT, CAMPAIGN = "#1b4f8a", "#d17b00"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
# Five firms, two hues. Fill separates firms inside a camp: solid, open, and open
# with a centre dot. Identity never rests on the fill alone — the legend names each.
# Six firms. Fill stopped working as an encoding at four-per-hue, and the camps
# turned out not to predict method anyway (see the caption), so colour carries the
# camp and the two EXTREME firms on each row are labelled by initials. Identity
# where it matters — at the ends of the range — instead of six lookups.
FIRMS = [("Hindenburg", None, "fire-once", "HB"),
         ("Night Market", "nightmarket", "fire-once", "NM"),
         ("Fuzzy Panda", "fuzzypanda", "fire-once", "FP"),
         ("Spruce Point", "sprucepoint", "fire-once", "SP"),
         ("Muddy Waters", "muddywaters", "campaign", "MW"),
         ("J Capital", "jcapital", "campaign", "JC")]
CAMP_COL = {"fire-once": ONESHOT, "campaign": CAMPAIGN}


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


def mark(el, x, y, r, colour, fill, surface):
    """solid / open / open-with-a-centre-dot, so one hue can carry three firms."""
    inner = colour if fill == "solid" else surface
    el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{inner}" '
              f'stroke="{colour}" stroke-width="2.5"/>')
    if fill == "dot":
        el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r*0.42:.1f}" fill="{colour}"/>')


def measure():
    corpora = {}
    for label, key, camp, solid in FIRMS:
        if key is None:
            corpora[label] = (corpuslib.load("initial"), corpuslib.probes(label), corpuslib.body)
            continue
        # One definition of "first look", in ctrllib, because each firm's site
        # needs a different rule and having those rules loose in the chart scripts
        # is how a 94-report set was once compared against a 76-report one that
        # included rebuttals.
        init, _ = ctrllib.first_look(key)
        corpora[label] = (init, corpuslib.probes(label), lambda d: d["text"])

    warn = ctrllib.audit_probes(corpora)
    for w in warn:
        print(f"    audit: {w}")

    rows = []
    for lab in corpuslib.probes():
        shares = [(n, sum(1 for d in ds if re.search(P[lab], g(d), re.I)) / len(ds))
                  for n, (ds, P, g) in corpora.items()]
        rows.append((lab, shares))
    # A summary row: does the report need a human at all?
    PRIV = corpuslib.BARRIER["needs presence"] + corpuslib.BARRIER["needs luck"]
    summary = [(n, sum(1 for d in ds if any(re.search(P[k], g(d), re.I) for k in PRIV)) / len(ds))
               for n, (ds, P, g) in corpora.items()]
    counts = {n: len(ds) for n, (ds, P, g) in corpora.items()}
    rows.sort(key=lambda r: -(max(s for _, s in r[1]) - min(s for _, s in r[1])))
    return rows, ("NEEDS A PERSON AT ALL", summary), counts


def main():
    rows, (sumlab, summary), counts = measure()
    assert palette.check([ONESHOT, CAMPAIGN], label="camp palette")

    L, R, TOP = 214.0, 118.0, 266.0
    RH, W = 30.0, 940.0
    H = TOP + (len(rows) + 3) * RH + 96
    def X(v): return L + v * (W - L - R)

    el = [f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "The barrier is people, not data", size=19, fill=INK, weight="600"))
    lead, dy = para(24, 58, "Share of each firm's first-look reports citing each kind of evidence. "
                    "Rows are ordered by how much the firms disagree — widest spread at the top, "
                    "closest agreement at the bottom.", size=12.5, fill=INK2, chars=118)
    el += lead
    y0 = 58 + dy + 24
    vals = sorted(s for _, s in summary)
    el.append(txt(24, y0, f"No firm goes below {vals[0]:.0%} on the share of reports resting on a "
                 f"person who agreed to talk. The median firm is at {vals[len(vals)//2]:.0%}.",
                 size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, "That is a floor, not a consensus — the range is wide. But every firm "
                 "here needs a person for at least two reports in five.", size=13, fill=INK2))

    for v in (0, 0.25, 0.5, 0.75, 1.0):
        el.append(f'<line x1="{X(v):.1f}" y1="{TOP-14:.1f}" x2="{X(v):.1f}" '
                  f'y2="{TOP + (len(rows)+2.2)*RH:.1f}" stroke="{GRID}" stroke-width="1"/>')
        el.append(txt(X(v), TOP - 22, f"{v:.0%}", size=11, fill=MUTED, anchor="middle", tab=True))

    for i, (lab, shares) in enumerate(rows):
        y = TOP + i * RH
        if i % 2 == 0:
            el.append(f'<rect x="{L-190:.1f}" y="{y-RH/2:.1f}" width="{W-R-L+190:.1f}" '
                      f'height="{RH:.1f}" fill="{BAND}" fill-opacity="0.5"/>')
        el.append(txt(L - 16, y + 4, lab, size=12, fill=INK2, anchor="end"))
        lo, hi = min(s for _, s in shares), max(s for _, s in shares)
        # A range bar, not a connector: it asserts the extent of disagreement
        # between firms on one measure, which is the thing the row is ordered by.
        el.append(f'<line x1="{X(lo):.1f}" y1="{y:.1f}" x2="{X(hi):.1f}" y2="{y:.1f}" '
                  f'stroke="{BASELINE}" stroke-width="3" stroke-linecap="round"/>')
        order = sorted(range(len(shares)), key=lambda j: shares[j][1])
        for j, (name, s) in enumerate(shares):
            mark(el, X(s), y, 6, CAMP_COL[FIRMS[j][2]], "solid", SURFACE)
        # A minimum near zero has no room on its left — the code lands on the row
        # label. Those go above the dot instead.
        for j, dx, anc in ((order[0], -12, "end"), (order[-1], 12, "start")):
            px = X(shares[j][1])
            if anc == "end" and px + dx < L + 16:
                el.append(txt(px, y - 11, FIRMS[j][3], size=9.5,
                              fill=CAMP_COL[FIRMS[j][2]], anchor="middle", weight="600"))
            else:
                el.append(txt(px + dx, y + 4, FIRMS[j][3], size=9.5,
                              fill=CAMP_COL[FIRMS[j][2]], anchor=anc, weight="600"))
        # A narrow spread near zero is not agreement, it is a floor: nobody does
        # the thing, so nobody can differ about it. Marked, because sorting by
        # spread otherwise puts "import records, 0-11%" next to a real consensus.
        rare = hi < 0.25
        el.append(txt(W - R + 12, y + 4, f"{(hi-lo)*100:.0f}pp", size=11,
                      fill=GHOSTPP if rare else MUTED, tab=True))
        if rare:
            el.append(txt(W - R + 48, y + 4, "rare", size=9.5, fill=GHOSTPP))

    ys = TOP + (len(rows) + 0.9) * RH
    el.append(f'<line x1="{L-190:.1f}" y1="{ys-RH*0.62:.1f}" x2="{W-R:.1f}" y2="{ys-RH*0.62:.1f}" '
              f'stroke="{BASELINE}" stroke-width="1.5"/>')
    el.append(txt(L - 16, ys + 5, sumlab, size=12.5, fill=INK, anchor="end", weight="600"))
    lo, hi = min(s for _, s in summary), max(s for _, s in summary)
    el.append(f'<line x1="{X(lo):.1f}" y1="{ys:.1f}" x2="{X(hi):.1f}" y2="{ys:.1f}" '
              f'stroke="{BASELINE}" stroke-width="3" stroke-linecap="round"/>')
    order = sorted(range(len(summary)), key=lambda j: summary[j][1])
    for j, (name, s) in enumerate(summary):
        mark(el, X(s), ys, 7.5, CAMP_COL[FIRMS[j][2]], "solid", SURFACE)
    for j, dx, anc in ((order[0], -14, "end"), (order[-1], 14, "start")):
        el.append(txt(X(summary[j][1]) + dx, ys + 5, FIRMS[j][3], size=10.5,
                      fill=CAMP_COL[FIRMS[j][2]], anchor=anc, weight="600"))
    el.append(txt(W - R + 12, ys + 5, f"{(hi-lo)*100:.0f}pp", size=11, fill=INK, weight="600", tab=True))

    lg = TOP - 62
    for j, (name, _, camp, code) in enumerate(FIRMS):
        x = 24 + (j % 3) * 200
        yy2 = lg + (j // 3) * 26
        mark(el, x + 6, yy2 - 4, 5.5, CAMP_COL[camp], "solid", SURFACE)
        el.append(txt(x + 18, yy2, f"{code}  {name} ({counts[name]})", size=10.5,
                      fill=INK2, tab=True))
    el.append(txt(24 + 3 * 200 + 4, lg, "fire-once", size=10.5, fill=ONESHOT, weight="600"))
    el.append(txt(24 + 3 * 200 + 4, lg + 26, "campaign", size=10.5, fill=CAMPAIGN, weight="600"))
    # "spread" sat on the 100% tick label; it belongs a line above the axis.
    el.append(txt(W - R + 12, TOP - 28, "spread", size=11, fill=MUTED, weight="600"))
    el.append(txt(W - R + 12, TOP - 14, "greyed = rare everywhere", size=9, fill=GHOSTPP))

    # Colour marks the camp so the rows can be read for it, but five rows separate
    # the camps cleanly and with two firms each that is what chance produces:
    # one split in three separates, so four of twelve are expected. The figure
    # names that here rather than letting a reader find a pattern in the noise.
    # The chance rate is computed for the actual split, not assumed. It was written
    # for two firms a side and did not follow when a third fire-once firm arrived.
    n_camp = sum(1 for _, _, c, _ in FIRMS if c == "campaign")
    n_all = len(FIRMS)
    chance = 2 / comb(n_all, n_camp)
    clean = sum(1 for _, shares in rows
                if (max(s for (nm, s), (_, _, c, _) in zip(shares, FIRMS) if c == "fire-once")
                    < min(s for (nm, s), (_, _, c, _) in zip(shares, FIRMS) if c == "campaign"))
                or (max(s for (nm, s), (_, _, c, _) in zip(shares, FIRMS) if c == "campaign")
                    < min(s for (nm, s), (_, _, c, _) in zip(shares, FIRMS) if c == "fire-once")))
    cap, _ = para(24, H - 58, "First-look reports only — a firm's first report on each target. "
                  "Follow-ups cite almost nothing and pooling them in reverses the ranking. "
                  "Detection is keyword-based on declared sources, so every row undercounts. "
                  f"{clean} rows put one camp entirely above the other — with {n_all-n_camp} "
                  f"firms against {n_camp}, {len(rows)*chance:.1f} of {len(rows)} are expected "
                  f"by chance and P({clean} or more) = "
                  f"{sum(comb(len(rows), i) * chance**i * (1-chance)**(len(rows)-i) for i in range(clean, len(rows)+1)):.2f}. "
                  "Suggestive, not yet a finding.",
                  size=11, fill=MUTED, chars=150, leading=15)
    el += cap
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print("  charts/people-not-data.svg")
    for lab, sh in rows[:3] + rows[-2:]:
        print(f"    {lab:<24}" + "  ".join(f"{n[:4]} {s:.0%}" for n, s in sh))
    print(f"    {sumlab:<24}" + "  ".join(f"{n[:4]} {s:.0%}" for n, s in summary))


if __name__ == "__main__":
    main()
