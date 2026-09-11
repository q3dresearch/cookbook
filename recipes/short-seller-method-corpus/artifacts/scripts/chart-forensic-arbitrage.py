#!/usr/bin/env python3
"""The reports most likely to be vindicated are the ones the market moves least on.

    python chart-forensic-arbitrage.py

Two axes, both free and both knowable on the morning a report drops: how big the
target is, and whether it had already filed a restatement or a delisting notice
before the report existed. Each cell shows how often that combination went on to
file another one — and what the stock did on the day.

    small target, already flagged     9 of 9 later filed again      -0.5% on the day
    small target, clean history       3 of 16                       -2.7%
    large target, already flagged     2 of 6                        varies
    large target, clean history       2 of 26                       varies

Fisher exact on the small-cap row is p = 0.0001. **And the market moves LESS for the
cell that is nine for nine.** It treats an already-troubled company as old news,
which is precisely where the filing record says the allegation is most likely to be
conceded in writing later.

**Is it just persistence?** Partly: six of the nine filed the same kind of document
again. Three did not — COCP and LOOP went from a restatement to a delisting, RIOT
from a delisting to a restatement. The distress changes form rather than repeating.

**What this is not.** Nine reports. A delisting notice can be for a late filing or a
share price under a dollar, not fraud. "Filed something" is corroboration, not proof
the short seller was right about what they alleged. And every target whose price
could not be recovered — the bankrupt ones — is missing, which if anything understates
the bad-outcome side.
"""
import json, statistics, sys
from math import comb
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import palette

RAW = Path(__file__).resolve().parents[1] / "raw"
OUT = Path(__file__).resolve().parents[1] / "charts" / "forensic-arbitrage.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, RULE = "#e1e0d9", "#ebeae3"
HOT, COOL, MKT = "#b03a2e", "#1b4f8a", "#b8912a"
RAMP = ["#f4f1ef", "#ecd9d4", "#e0b8af", "#d2948a", "#c26e62", "#b03a2e"]
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
BAD = {"restatement", "delisting notice", "bankruptcy"}


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


def fisher(a, b, c, d):
    n = a + b + c + d
    obs = comb(a + b, a) * comb(c + d, c) / comb(n, a + c)
    p = 0.0
    for i in range(0, min(a + b, a + c) + 1):
        j, k = a + b - i, a + c - i
        l = n - i - j - k
        if j < 0 or k < 0 or l < 0:
            continue
        pr = comb(a + b, i) * comb(c + d, k) / comb(n, a + c)
        if pr <= obs + 1e-12:
            p += pr
    return p


def load():
    out = json.loads((RAW / "target_outcomes.json").read_text())
    size = {s["ticker"]: s for s in json.loads((RAW / "size_events.json").read_text())}
    rows = []
    for t, v in out.items():
        s = size.get(t)
        if not s:
            continue
        rows.append({"t": t, "firm": v["firm"],
                     "bad": any(l in BAD for l, _ in v["after"]),
                     "hard": any(l in BAD for l, _ in v["before"]),
                     "cap": s["cap"], "r1": s["r1"]})
    return rows


def main():
    rows = load()
    assert palette.check([RAMP[0], RAMP[3], RAMP[5]], label="outcome ramp")
    cells = {}
    for small in (True, False):
        for hard in (True, False):
            g = [r for r in rows if (r["cap"] < 2e9) == small and r["hard"] == hard]
            cells[(small, hard)] = g
    sa, sb = cells[(True, True)], cells[(True, False)]
    ka, kb = sum(1 for r in sa if r["bad"]), sum(1 for r in sb if r["bad"])
    p = fisher(ka, len(sa) - ka, kb, len(sb) - kb)

    W, H = 940.0, 790.0
    CW, CH, GX, GY = 250.0, 132.0, 14.0, 14.0
    LX, TY = 268.0, 292.0

    el = [f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "The reports most likely to be proved right move the stock least",
                  size=19, fill=INK, weight="600"))
    lead, dy = para(24, 58, f"{len(rows)} short-report targets, split on two things knowable the "
                    "morning a report drops: the target's size, and whether it had ALREADY filed a "
                    "restatement or delisting notice before the report existed. Each cell shows how "
                    "often it went on to file another one.", size=12.5, fill=INK2, chars=118)
    el += lead
    y0 = 58 + dy + 22
    el.append(txt(24, y0, f"A small target with a flagged filing history went on to file again "
                 f"{ka} times out of {len(sa)}. Fisher p = {p:.4f}.",
                 size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, "That is the cell the market discounts — it falls 0.5% on the day "
                 "against 2.7% for the clean-history targets beside it.", size=13, fill=INK2))

    el.append(txt(LX, TY - 30, "had already filed a restatement or delisting notice",
                  size=11.5, fill=INK2, weight="600"))
    for j, hard in enumerate((True, False)):
        el.append(txt(LX + j * (CW + GX) + CW / 2, TY - 12, "yes" if hard else "no",
                      size=12, fill=INK, anchor="middle", weight="600"))
    for i, small in enumerate((True, False)):
        y = TY + i * (CH + GY)
        el.append(txt(LX - 16, y + CH / 2 - 6, "target under $2B" if small else "target over $2B",
                      size=12, fill=INK, anchor="end", weight="600"))
        for j, hard in enumerate((True, False)):
            g = cells[(small, hard)]
            x = LX + j * (CW + GX)
            if not g:
                continue
            rate = sum(1 for r in g if r["bad"]) / len(g)
            el.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{CW:.1f}" height="{CH:.1f}" '
                      f'fill="{RAMP[min(len(RAMP)-1,int(rate*len(RAMP)))]}"/>')
            dark = rate >= 0.5
            el.append(txt(x + 18, y + 52, f"{rate:.0%}", size=34,
                          fill="#ffffff" if dark else INK, weight="700", tab=True))
            el.append(txt(x + 18, y + 74, f"{sum(1 for r in g if r['bad'])} of {len(g)} later filed"
                          " again", size=11.5, fill="#ffffff" if dark else INK2, tab=True))
            mv = [r["r1"] for r in g if r["r1"] is not None]
            if mv:
                el.append(txt(x + 18, y + 104, f"{statistics.median(mv):+.1%} on the day",
                              size=13, fill="#ffffff" if dark else MKT, weight="600", tab=True))

    ly = TY + 2 * (CH + GY) + 34
    el.append(txt(24, ly, "is it just the same filing repeating?", size=12, fill=INK, weight="600"))
    same = sum(1 for r in sa if r["bad"])
    note, _ = para(24, ly + 18, "Six of the nine filed the same kind of document again. Three did "
                   "not — COCP and LOOP went from a restatement to a delisting, RIOT from a "
                   "delisting to a restatement. The distress changes form rather than repeating, "
                   "which is not what pure persistence looks like.",
                   size=11.5, fill=INK2, chars=110, leading=15)
    el += note

    cap, _ = para(24, H - 82, "Nine reports in that cell. A delisting notice can follow a late "
                  "filing or a share price under a dollar rather than fraud, and 'filed something' "
                  "is corroboration rather than proof the allegation was right. Targets whose price "
                  "could not be recovered — the bankrupt ones — are absent entirely, which understates "
                  "the bad-outcome side. Item codes come from SEC's submissions API, which returns "
                  "only the most recent ~1000 filings, so older history is truncated for frequent "
                  "filers.", size=11, fill=MUTED, chars=150, leading=15)
    el += cap
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print(f"  charts/forensic-arbitrage.svg — small+flagged {ka}/{len(sa)}, "
          f"small+clean {kb}/{len(sb)}, Fisher p={p:.4f}")
    for (small, hard), g in cells.items():
        mv = [r["r1"] for r in g if r["r1"] is not None]
        print(f"    {'small' if small else 'large':<6}{'flagged' if hard else 'clean':<9}"
              f"n={len(g):<3} bad {sum(1 for r in g if r['bad'])/len(g):>4.0%}  "
              f"day+1 {statistics.median(mv):+.1%}" if mv else "")


if __name__ == "__main__":
    main()
