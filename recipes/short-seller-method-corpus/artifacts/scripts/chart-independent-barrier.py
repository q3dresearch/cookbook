#!/usr/bin/env python3
"""How hard is it to be an independent financial forensic researcher?

    python tools/chart-independent-barrier.py

Reads the Hindenburg corpus and renders one figure answering one decision:
can a person with no budget, no travel and no sources do this work?

Sources are graded by the barrier they impose on an independent researcher —
an ORDERED scale, so the palette is an ordinal ramp (one hue, light to dark),
validated with the dataviz validator. A categorical palette was tried first
and failed: #d03b3b and #eb6834 sit at delta-E 10.8 for normal vision, below
the 15 floor.
"""
import html, json, re, sys

import corpuslib
from pathlib import Path
from xml.sax.saxutils import escape

REPO = Path(__file__).resolve().parents[1]
# The corpus path is resolved by corpuslib, which globs for the newest capture.
OUT = REPO / "charts" / "independent-forensic-barrier.svg"

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
# Ordinal ramp, validated: monotone lightness, single hue, light end clears surface.
RAMP = ["#7db0ea", "#4a8bdb", "#2361b0", "#123a68"]
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'

BLURB = {"free & remote": "anyone with a browser",
         "needs money": "terminal or data subscription",
         "needs presence": "a person who agrees to talk",
         "needs luck": "a source who comes to you"}
# Tiers are assembled from corpuslib so this figure and the control comparison
# cannot drift apart. They did: one copy listed Morningstar, the other did not.
P = corpuslib.probes()
TIERS = [(name, RAMP[i], BLURB[name], [P[k] for k in keys])
         for i, (name, keys) in enumerate(corpuslib.BARRIER.items())]


def body(p):
    return html.unescape(re.sub(r"<[^>]+>", " ", p["content"]["rendered"]))


def txt(x, y, s, *, size, fill, anchor="start", weight="normal", tab=False):
    st = "font-variant-numeric: tabular-nums;" if tab else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family=\'{FONT}\' font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
            f'style="{st}">{escape(s)}</text>')


def para(x, y, text, *, size, fill, chars, leading=17.0):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if len(t) > chars and cur:
            lines.append(cur); cur = w
        else:
            cur = t
    if cur: lines.append(cur)
    return [txt(x, y + i * leading, l, size=size, fill=fill) for i, l in enumerate(lines)], \
           len(lines) * leading


def bar(x, y, w, h, colour, r=4):
    r = min(r, max(w / 2, 0.1), h / 2)
    return (f'<path d="M{x:.1f},{y:.1f} h{w - r:.1f} q{r},0 {r},{r} v{h - 2*r:.1f} '
            f'q0,{r} -{r},{r} h-{w - r:.1f} z" fill="{colour}"/>')


def main():
    # 94 initial reports, not the 105 posts the API returns. Follow-ups answer a
    # denial and cite almost nothing; counting them deflates every share here.
    posts = corpuslib.load("initial")
    n = len(posts)
    per = {}
    for p in posts:
        t = body(p)
        per[p["slug"]] = {name for name, _, _, pats in TIERS
                          if any(re.search(pat, t, re.I) for pat in pats)}

    gated_names = {"needs money", "needs presence", "needs luck"}
    dist = [0, 0, 0, 0]
    for h in per.values():
        dist[len(h & gated_names)] += 1
    # A report that matches NO probe is unclassified, not "reachable from a desk".
    # Counting the two together is how the follow-ups made Muddy Waters look like
    # the easy corpus, and four early accounting-only reports were doing the same
    # thing here — they name no source of any kind.
    silent = sum(1 for h in per.values() if not h)
    solo = dist[0] - silent

    W, left, right = 980.0, 250.0, 150.0
    body_el = [txt(24, 34, "How hard is it to do this alone?", size=19, fill=INK, weight="600")]
    lead, dy = para(24, 58, f"Every source cited across {n} initial Hindenburg Research reports "
                    "(2017-2025), graded by what it demands of an independent "
                    "researcher. The decision this supports: whether this work is "
                    "reachable without a budget, travel, or sources of your own.",
                    size=12.5, fill=INK2, chars=112)
    body_el += lead

    # HERO — the one number the figure exists for.
    hy = 58 + dy + 44
    body_el.append(txt(24, hy + 26, f"{solo/n:.0%}", size=58, fill=RAMP[2], weight="700", tab=True))
    # The closing sentence is derived, not typed. It said "two in five" while the
    # bars said 37% — prose that stops tracking the data is how a caption starts lying.
    share = solo / n
    phrase = ("Two in five" if share >= 0.385 else "Just over a third" if share >= 0.34
              else "A third" if share >= 0.30 else "One in four" if share >= 0.225
              else "One in five" if share >= 0.175 else f"{share:.0%}")
    hero, hdy = para(150, hy - 2, f"of reports — {solo} of {n} — cite free, remotely-available "
                     "sources and nothing else. No terminal, no interview, no site visit, "
                     f"no whistleblower. {phrase} were reachable from a desk. A further "
                     f"{silent} name no source of any kind and are left out.",
                     size=13, fill=INK, chars=76)
    body_el += hero

    # Tier reach
    top = hy + 76
    body_el.append(txt(24, top, "What each tier demands, and how many reports need it",
                       size=12, fill=INK2, weight="600"))
    top += 22
    span, rowh, gap = W - left - right, 26.0, 14.0
    for i, (name, colour, demand, pats) in enumerate(TIERS):
        k = sum(1 for h in per.values() if name in h)
        y = top + i * (rowh + gap)
        w = max(2.0, k / n * span)
        body_el.append(bar(left, y, w, rowh, colour))
        body_el.append(txt(left - 12, y + rowh - 8, name, size=12.5, fill=INK2, anchor="end"))
        body_el.append(txt(left - 12, y + rowh + 8, demand, size=10, fill=MUTED, anchor="end"))
        body_el.append(txt(left + w + 10, y + rowh - 8, f"{k}  ({k/n:.0%})",
                           size=12.5, fill=INK, weight="600", tab=True))
    plot_bottom = top + len(TIERS) * (rowh + gap) + 14  # clear the last sublabel
    body_el.append(f'<line x1="{left}" y1="{top - 8}" x2="{left}" y2="{plot_bottom - gap + 4}" '
                   f'stroke="{BASELINE}" stroke-width="1"/>')

    # Gated-tier distribution
    dy2 = plot_bottom + 20
    body_el.append(txt(24, dy2, "How many gated tiers a single report needs",
                       size=12, fill=INK2, weight="600"))
    dy2 += 16
    x = left
    # The "none" segment held both the 19 reports that cite only free sources and
    # the 4 that cite nothing at all. Shown together it contradicted the hero above
    # it, which counts only the 19.
    segs = [solo] + dist[1:] + [silent]
    labels = ["free only", "one gate", "two gates", "three gates", "no source named"]
    ramp = [RAMP[0], RAMP[1], RAMP[2], RAMP[3], BASELINE]
    for i, count in enumerate(segs):
        if not count: continue
        w = count / n * span
        body_el.append(bar(x, dy2, max(1.5, w - 2), 30, ramp[i], r=3))
        # A segment narrower than its label gets the count outside, above.
        if w > 46:
            body_el.append(txt(x + w / 2 - 1, dy2 + 20, f"{count}", size=12,
                               fill="#ffffff" if 2 <= i <= 3 else INK, anchor="middle",
                               weight="600", tab=True))
        else:
            body_el.append(txt(x + w / 2 - 1, dy2 - 6, f"{count}", size=11, fill=INK,
                               anchor="middle", weight="600", tab=True))
        body_el.append(txt(min(x + w / 2 - 1, W - right + 96), dy2 + 46, labels[i],
                           size=11, fill=INK2, anchor="middle"))
        x += w
    dy2 += 62

    foot, _ = para(24, dy2 + 14,
                   "Reads DECLARED sources, so it undercounts: a report may use a "
                   "terminal without naming it, and a citation is not effort — a "
                   "desk-only report can still take six months. Published reports "
                   "only, so investigations abandoned when the thesis collapsed are "
                   f"invisible. Detection is keyword-based over {n} reports; treat "
                   "these as orders of magnitude, not decimals.",
                   size=10, fill=MUTED, chars=142, leading=14)
    body_el += foot
    H = dy2 + 92

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" '
           f'viewBox="0 0 {W:.0f} {H:.0f}" role="img" aria-label="Barrier to independent '
           f'forensic research">\n<title>How hard is it to do this alone?</title>\n'
           f'<desc>Bars showing what share of 105 Hindenburg reports cite sources in each '
           f'access tier, and how many gated tiers a report needs.</desc>\n'
           f'<rect width="{W:.0f}" height="{H:.0f}" fill="{SURFACE}"/>\n'
           + "\n".join(body_el) + "\n</svg>\n")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"{OUT.relative_to(REPO)} — hero {solo}/{n} = {solo/n:.0%}")


if __name__ == "__main__":
    main()
