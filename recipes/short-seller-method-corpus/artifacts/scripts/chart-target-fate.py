#!/usr/bin/env python3
"""Most short-seller targets are still trading. The ones that are not were not all killed.

    python chart-target-fate.py

Thirty-two targets whose ticker two independent routes agree on, and where each one
stands today. Read left to right: what a status check reports, then what reading the
thirteen exceptions actually finds.

The point of the figure is the gap between those two columns. A status check says 41%
of these targets no longer trade under the symbol their report named, which sounds
like a kill rate. Chase each one and five are simply quoted somewhere else — AKG on
the ASX, IRSA in London, PMET and WSP on the TSX, RINO on OTC — three are renames of
healthy companies, and one is an acquisition at a premium by Novartis. Three cannot
be found anywhere, and one is bankrupt.

**Four in thirty-two, not thirteen.** And even that is a floor on ambiguity rather
than a verdict: a company can be gutted and still trade, and an acquisition can be a
rescue or a bargain. Symbol persistence is not corporate survival, and this chart is
drawn to make that visible instead of averaging it away.
"""
import json, sys
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import palette

RAW = Path(__file__).resolve().parents[1] / "raw"
OUT = Path(__file__).resolve().parents[1] / "charts" / "target-fate.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, RULE = "#e1e0d9", "#ebeae3"
ALIVE, DEAD, AMBIG = "#1b4f8a", "#b03a2e", "#b8912a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'

# What the second pass found, per symbol. Recorded rather than inferred, because the
# status code alone cannot tell a rename from a delisting.
VERDICT = {
    "trading": ("still trading, same symbol", ALIVE),
    "trades elsewhere": ("still quoted, another venue", ALIVE),
    "symbol changed": ("renamed or acquired", AMBIG),
    "gone from this symbol": ("not found anywhere", DEAD),
    "bankrupt": ("bankrupt", DEAD),
}
NOTE = {"KDNY": "acquired by Novartis", "SQ": "Block, renamed", "AMEH": "Astrana Health, renamed",
        "XL": "Spruce Power, renamed", "ZYXI": "Chapter 11, trades as ZYXIQ",
        "RINO": "delisted fraud, still quoted OTC", "CIFS": "delisted",
        "FMCN": "went private, relisted in China", "APHQF": "merged into Tilray",
        "AKG": "ASX", "IRSA": "London", "PMET": "TSX", "WSP": "TSX"}


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
    d = json.loads((RAW / "target_fate.json").read_text())
    assert palette.check([ALIVE, DEAD, AMBIG], label="fate palette")
    n = len(d)
    naive_gone = sum(1 for v in d.values() if v["fate"] != "trading")
    real_gone = sum(1 for v in d.values() if VERDICT[v["fate"]][1] == DEAD)

    W = 940.0
    ROW, LEFT = 23.0, 250.0
    rows = sorted((s for s in d if d[s]["fate"] != "trading"),
                  key=lambda s: (VERDICT[d[s]["fate"]][1] != DEAD, d[s]["fate"], s))
    H = 300 + len(rows) * ROW + 190

    el = [f'<rect width="{W}" height="{H:.0f}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "Most targets are still trading. The rest were not all killed.",
                  size=19, fill=INK, weight="600"))
    lead, dy = para(24, 58, f"{n} targets whose ticker two independent routes agree on, years "
                    "after their report. Tickers here are confirmed WITHOUT SEC's registry on "
                    "purpose: that registry lists current filers, so using it would answer a "
                    "survival question with the survival assumption.",
                    size=12.5, fill=INK2, chars=118)
    el += lead
    y0 = 58 + dy + 24
    el.append(txt(24, y0, f"A status check reports {naive_gone} of {n} gone from their symbol "
                 f"({naive_gone/n:.0%}). Chasing each one leaves {real_gone}.",
                 size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, "Five are simply quoted on another exchange, three are renames of "
                 "healthy companies, and one was bought at a premium.", size=13, fill=INK2))

    # the two counts, side by side
    by = y0 + 56
    for i, (lab, val, col, sub) in enumerate((
            ("what a status check says", naive_gone, AMBIG, "no longer at that symbol"),
            ("what reading them finds", real_gone, DEAD, "cannot be found anywhere"))):
        x = 24 + i * 300
        el.append(txt(x, by + 26, f"{val}", size=34, fill=col, weight="700", tab=True))
        el.append(txt(x + (58 if val > 9 else 34), by + 26, f"of {n}", size=15, fill=MUTED, tab=True))
        el.append(txt(x, by + 44, lab, size=11.5, fill=INK, weight="600"))
        el.append(txt(x, by + 58, sub, size=10.5, fill=MUTED))

    ty = by + 92
    el.append(txt(24, ty, f"every one of the {len(rows)} that is not trading under its original symbol",
                  size=12, fill=INK2, weight="600"))
    ty += 16
    for i, s in enumerate(rows):
        v = d[s]
        lab, col = VERDICT[v["fate"]]
        y = ty + i * ROW
        if i % 2 == 0:
            el.append(f'<rect x="24" y="{y:.1f}" width="{W-48:.1f}" height="{ROW:.1f}" fill="{RULE}" fill-opacity="0.6"/>')
        el.append(txt(36, y + 16, s, size=12, fill=INK, weight="600", tab=True))
        el.append(txt(104, y + 16, v["firm"], size=11, fill=MUTED))
        el.append(txt(212, y + 16, str(v["date"])[:10], size=11, fill=MUTED, tab=True))
        el.append(f'<rect x="{LEFT+40:.1f}" y="{y+5:.1f}" width="9" height="{ROW-11:.1f}" fill="{col}"/>')
        el.append(txt(LEFT + 58, y + 16, lab, size=11.5, fill=col, weight="600"))
        if s in NOTE:
            el.append(txt(LEFT + 268, y + 16, NOTE[s], size=11, fill=INK2))

    ly = ty + len(rows) * ROW + 30
    el.append(txt(24, ly, "reading of the outcome", size=11.5, fill=INK, weight="600"))
    for i, (col, lab) in enumerate(((ALIVE, "the company is still quoted somewhere"),
                                    (AMBIG, "renamed or acquired — not a kill, not a clean survival"),
                                    (DEAD, "cannot be found on any venue checked"))):
        el.append(f'<rect x="24" y="{ly+14+i*18:.1f}" width="9" height="11" fill="{col}"/>')
        el.append(txt(40, ly + 24 + i * 18, lab, size=11, fill=INK2))

    cap, _ = para(24, ly + 86, "Venues checked for a missing symbol: TSX, TSXV, ASX, OTC and London. "
                  "A company gutted by a report can still trade, and an acquisition can be a rescue "
                  "or a bargain, so even the right-hand count is a floor on ambiguity rather than a "
                  "verdict. Telling a kill from a takeover needs merger, bankruptcy and "
                  "deregistration filings — SEC keeps them, including for companies that have since "
                  "deregistered, and this recipe does not yet read them.",
                  size=11, fill=MUTED, chars=150, leading=15)
    el += cap
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print(f"  charts/target-fate.svg — status check {naive_gone}/{n}, verified {real_gone}/{n}")
    for f, c in Counter(VERDICT[v["fate"]][0] for v in d.values()).most_common():
        print(f"    {f:<32}{c:>3}")


if __name__ == "__main__":
    main()
