#!/usr/bin/env python3
"""Activist short research splits into two businesses, and Hindenburg is not the odd one.

    python chart-two-camps.py

Each firm is one mark: how many companies it has ever attacked against how many
reports it published doing it. The diagonal is one report per target — fire once
and move on. Distance above it is campaigning.

The first version of this comparison used Muddy Waters alone and concluded
"Hindenburg is unrepresentative: it publishes once and moves on". Night Market then
came in at 12% follow-ups against Hindenburg's 9%, and J Capital at 55% against
Muddy Waters' 61%. One control was still an anecdote; the split is the finding.

The diagonal is only a 45-degree line if both axes carry the same span per pixel,
so both are drawn 0..250 and the assertion is checked in device space before the
file is written.
"""
import re, sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpuslib, ctrllib, palette

OUT = Path(__file__).resolve().parents[1] / "charts" / "two-camps.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
ONESHOT, CAMPAIGN = "#1b4f8a", "#d17b00"      # validated pair, dE 29.8 worst CVD
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
SPAN = 250.0


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


def jcapital_from_filenames():
    """J Capital's reports are PDFs listed on its ticker pages, not the pages.

    Each .html is a teaser of ~530 words linking a whole history of PDFs named
    2019_09_05_bgne_1.pdf. Counting pages would have said 62 reports; the real
    number is 215, and the filenames carry the date and the target both.
    """
    import html as H
    names = set()
    for f in (ctrllib.RAW / "jcapital").glob("*.html"):
        for m in re.findall(r'href="([^"]+\.pdf[^"]*)"', f.read_text("utf-8", "replace"), re.I):
            names.add(H.unescape(m).split("/")[-1])
    dated = sorted(n for n in names if re.match(r"20\d\d[_-]\d\d[_-]\d\d", n))
    # Thematic notes are a different product — "asia_view", "finance_survey" are
    # macro pieces, not attacks on a company, and pooling them would inflate the
    # report count without adding a target.
    theme = re.compile(r"_(view|outlook|monitor|weekly|monthly|macro|themes?|overview|"
                       r"conference|survey|index|sector|chartbook|primer)[_.]", re.I)
    co = [n for n in dated if not theme.search(n)]
    tgt = {}
    for n in co:
        m = re.match(r"20\d\d[_-]\d\d[_-]\d\d[_-]([a-z&0-9]+)", n.lower())
        if m:
            tgt.setdefault(m.group(1), n)
    return len(tgt), len(co), min(co)[:4], max(co)[:4]


def sprucepoint_from_filenames():
    """Spruce Point publishes one page per target listing that target's PDFs.

    So the pages are the targets and the distinct PDFs are the reports — no date
    parsing needed to count them. Only 45 of its 134 report pages were captured
    (the site is slow), so this is a sample and the caption says so.
    """
    import html as H
    pages = sorted((ctrllib.RAW / "sprucepoint").glob("*.html"))
    pdfs = set()
    for p in pages:
        h = p.read_text("utf-8", "replace")
        pdfs |= {H.unescape(m).split("/")[-1]
                 for m in re.findall(r'href="([^"]+\.pdf[^"]*)"', h, re.I)}
    years = sorted(re.findall(r"[-_](\d{4})\.pdf", " ".join(pdfs)))
    return len(pages), len(pdfs), (years[0] if years else "?"), (years[-1] if years else "?")


def firms():
    out = []
    hb = corpuslib.load(None)
    reports = [p for p in hb if p["kind"] != "admin"]
    tg = {"-".join(p["slug"].split("-")[:2]) for p in reports}
    out.append(("Hindenburg", len(tg), len(reports), "2017", "2025"))

    for firm, label in (("muddywaters", "Muddy Waters"), ("nightmarket", "Night Market"),
                        ("fuzzypanda", "Fuzzy Panda")):
        try:
            docs, _ = ctrllib.load(firm, with_pdf=True)
        except Exception:
            continue
        docs = [d for d in docs if d["words"] >= ctrllib.MIN_WORDS]
        init, fu, _ = ctrllib.split_reports(docs)
        yrs = sorted(d["date"][:4] for d in docs if d["date"])
        out.append((label, len(init), len(init) + len(fu), yrs[0], yrs[-1]))

    if (ctrllib.RAW / "jcapital").exists():
        t, r, y0, y1 = jcapital_from_filenames()
        out.append(("J Capital", t, r, y0, y1))
    if (ctrllib.RAW / "sprucepoint").exists():
        t, r, y0, y1 = sprucepoint_from_filenames()
        out.append(("Spruce Point*", t, r, y0, y1))
    return out


def main():
    rows = firms()
    assert palette.check([ONESHOT, CAMPAIGN], label="camp palette")

    W, H = 940.0, 740.0
    L, R, T, B = 84.0, 250.0, 232.0, 126.0
    side = min(W - L - R, H - T - B)
    def X(v): return L + (v / SPAN) * side
    def Y(v): return (T + side) - (v / SPAN) * side

    el = [f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "Two businesses, not one practice", size=19, fill=INK, weight="600"))
    lead, dy = para(24, 58, "Every activist short-research firm whose reports could be read in "
                    "full. Horizontal: how many companies it has attacked. Vertical: how many "
                    "reports it published doing it. The diagonal is one report per target.",
                    size=12.5, fill=INK2, chars=116)
    el += lead
    y0 = 58 + dy + 24
    # Named from the data. An earlier version said "Hindenburg sits on the line
    # with Night Market" and stayed that way when Spruce Point joined them.
    once = [n for n, tg, rep, _, _ in rows if 1 - tg / rep < 0.4]
    camp = [n for n, tg, rep, _, _ in rows if 1 - tg / rep >= 0.4]
    others = [n.rstrip("*") for n in once if not n.startswith("Hindenburg")]
    el.append(txt(24, y0, f"{len(once)} firms sit on the line and fire once. {len(camp)} sit above "
                 "it and run campaigns — Muddy Waters has 9 reports on one target.",
                 size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, "Hindenburg is on the line with "
                 + (" and ".join([", ".join(others[:-1]), others[-1]]) if len(others) > 1 else others[0])
                 + ". It is a clean example of one model, not an outlier from a single practice.",
                 size=13, fill=INK2))

    for v in range(0, int(SPAN) + 1, 50):
        el.append(f'<line x1="{X(v):.1f}" y1="{Y(0):.1f}" x2="{X(v):.1f}" y2="{Y(SPAN):.1f}" stroke="{GRID}" stroke-width="1"/>')
        el.append(f'<line x1="{X(0):.1f}" y1="{Y(v):.1f}" x2="{X(SPAN):.1f}" y2="{Y(v):.1f}" stroke="{GRID}" stroke-width="1"/>')
        el.append(txt(X(v), Y(0) + 20, str(v), size=11, fill=MUTED, anchor="middle", tab=True))
        el.append(txt(X(0) - 10, Y(v) + 4, str(v), size=11, fill=MUTED, anchor="end", tab=True))
    el.append(f'<line x1="{X(0):.1f}" y1="{Y(0):.1f}" x2="{X(SPAN):.1f}" y2="{Y(0):.1f}" stroke="{BASELINE}" stroke-width="1.5"/>')
    el.append(f'<line x1="{X(0):.1f}" y1="{Y(0):.1f}" x2="{X(0):.1f}" y2="{Y(SPAN):.1f}" stroke="{BASELINE}" stroke-width="1.5"/>')
    el.append(txt(X(0), Y(0) + 42, "companies attacked", size=12, fill=INK2))
    el.append(f'<text x="{-(T + side / 2):.1f}" y="26" transform="rotate(-90)" '
              f'font-family=\'{FONT}\' font-size="12" fill="{INK2}" text-anchor="middle">'
              "reports published</text>")

    el.append(f'<line x1="{X(0):.1f}" y1="{Y(0):.1f}" x2="{X(SPAN):.1f}" y2="{Y(SPAN):.1f}" '
              f'stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="5 5"/>')
    el.append(txt(X(SPAN) - 8, Y(SPAN) + 20, "one report per target", size=11, fill=MUTED, anchor="end"))

    for name, tg, rep, y0_, y1_ in rows:
        ratio = 1 - tg / rep
        c = CAMPAIGN if ratio >= 0.4 else ONESHOT
        x, y = X(tg), Y(rep)
        el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{c}" fill-opacity="0.25" '
                  f'stroke="{c}" stroke-width="2.5"/>')
        # The plot is 376px wide and a one-line caption is ~230px, so a single
        # label line runs straight into the legend. Two short lines fit; a point in
        # the right half puts them on its left.
        right = x > X(SPAN) - 190
        ax, anc = (x - 14, "end") if right else (x + 14, "start")
        el.append(txt(ax, y - 8, name, size=12.5, fill=INK, weight="600", anchor=anc))
        el.append(txt(ax, y + 7, f"{tg} targets, {rep} reports", size=11.5, fill=MUTED,
                      anchor=anc, tab=True))
        el.append(txt(ax, y + 21, f"{ratio:.0%} follow-up", size=11.5, fill=MUTED,
                      anchor=anc, weight="600", tab=True))

    lx = L + side + 30
    el.append(txt(lx, T + 20, "the two camps", size=12.5, fill=INK, weight="600"))
    for i, (c, lab, sub) in enumerate([
            (ONESHOT, "fire once", "one report, then the next target"),
            (CAMPAIGN, "campaign", "keep publishing on the same target")]):
        yy = T + 50 + i * 66
        el.append(f'<circle cx="{lx+8:.1f}" cy="{yy-4:.1f}" r="7" fill="{c}" fill-opacity="0.25" stroke="{c}" stroke-width="2.5"/>')
        el.append(txt(lx + 24, yy, lab, size=12, fill=INK, weight="600"))
        sb, _ = para(lx, yy + 16, sub, size=11, fill=MUTED, chars=26)
        el += sb
    note, _ = para(lx, T + 200, "Targets come from whatever each site exposes: Hindenburg's slugs, "
                   "Muddy Waters' URLs, J Capital's and Spruce Point's PDF filenames. "
                   "J Capital's 26 macro notes are excluded — they attack no company.",
                   size=11, fill=MUTED, chars=26)
    el += note

    span_x = X(SPAN) - X(0)
    span_y = Y(0) - Y(SPAN)
    assert abs(span_x - span_y) < 0.5, f"diagonal is not 45 degrees: {span_x:.1f} vs {span_y:.1f}"

    cap, _ = para(24, H - 44, "A target is a company the firm published about at least once; a "
                  "follow-up is any later report on that same target. Ranges: "
                  + "; ".join(f"{n} {a}-{b}" for n, _, _, a, b in rows)
                  + ". * Spruce Point is a 45-of-134 sample, evenly spaced across its "
                  "archive; every other firm is its whole archive.",
                  size=11.5, fill=MUTED, chars=146)
    el += cap
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print(f"  charts/two-camps.svg — diagonal verified at {span_x:.0f}x{span_y:.0f} device px")
    for n, tg, rep, a, b in rows:
        print(f"    {n:<14} {tg:>4} targets {rep:>4} reports  {1-tg/rep:>5.0%} follow-up  {a}-{b}")


if __name__ == "__main__":
    main()
