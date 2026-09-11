#!/usr/bin/env python3
"""Hindenburg and Muddy Waters run the same trade as different businesses.

    python chart-two-businesses.py

Four marks: each firm's initial reports and its follow-ups, placed by how long
they are and how many kinds of evidence they carry, sized by how many there are.

The figure exists because the pooled comparison of these two firms is wrong. 61%
of Muddy Waters' output is follow-ups, which cite almost nothing; averaged in, they
make the firm look like the easier corpus to reproduce. The sizes here are the
reason, and they are the third dimension — a two-axis plot of the same four points
would hide that one bubble is 87 reports and another is 9.
"""
import re, sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpuslib, ctrllib, palette

OUT = Path(__file__).resolve().parents[1] / "charts" / "two-businesses.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
HB, MW = "#1b4f8a", "#d17b00"        # validated: worst pair dE 29.8 across all CVD types
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def txt(x, y, s, *, size, fill, anchor="start", weight="normal", tab=False, op=1.0):
    st = "font-variant-numeric: tabular-nums;" if tab else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family=\'{FONT}\' font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
            f'opacity="{op}" style="{st}">{escape(s)}</text>')


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


def stats():
    """(label, firm, median words, median evidence types, n) for four groups."""
    import statistics
    hb_i, hb_f = corpuslib.load("initial"), corpuslib.load("follow-up")
    Ph = corpuslib.probes("Hindenburg")
    docs, _ = ctrllib.load("muddywaters", with_pdf=True)
    for d in docs:
        m = re.search(r"/research/([^/]+)/", d["url"])
        d["target"] = m.group(1) if m else None
    have = [d for d in docs if d["target"] and d["date"] and d["words"] >= ctrllib.MIN_WORDS]
    first = {}
    for d in sorted(have, key=lambda x: x["date"]):
        first.setdefault(d["target"], d)
    mw_i = list(first.values())
    mw_f = [d for d in have if d not in mw_i]
    Pm = corpuslib.probes("Muddy Waters")

    def row(label, firm, docs, P, get):
        w = statistics.median(len(get(d).split()) for d in docs)
        e = statistics.median(sum(1 for k in P if re.search(P[k], get(d), re.I)) for d in docs)
        return dict(label=label, firm=firm, words=w, ev=e, n=len(docs))

    return [row("initial reports", "HB", hb_i, Ph, corpuslib.body),
            row("follow-ups", "HB", hb_f, Ph, corpuslib.body),
            row("initial reports", "MW", mw_i, Pm, lambda d: d["text"]),
            row("follow-ups", "MW", mw_f, Pm, lambda d: d["text"])]


def main():
    rows = stats()
    assert palette.check([HB, MW], label="firm palette"), "palette failed CVD check"

    W, H = 980.0, 640.0
    L, R, T, B = 92.0, 268.0, 214.0, 108.0
    xmax, ymax = 10000.0, 5.0
    # The y domain starts below zero. Hindenburg's follow-ups cite a median of ZERO
    # evidence types, so on a 0-anchored axis that bubble sits half under the
    # baseline. The floor is padding, not data: gridlines still run 0..5.
    ymin = -0.5
    def X(v): return L + (v / xmax) * (W - L - R)
    def Y(v): return H - B - ((v - ymin) / (ymax - ymin)) * (H - B - T)
    def RAD(n): return max(7.0, (n ** 0.5) * 3.4)

    el = [f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "The same trade, run as two different businesses", size=19, fill=INK, weight="600"))
    lead, dy = para(24, 58, "Every report from Hindenburg Research (2017-2025) and Muddy "
                    "Waters (2010-2026), grouped into the first report on a target and "
                    "everything published about that target afterwards. Bubble area is "
                    "the number of reports.", size=12.5, fill=INK2, chars=118)
    el += lead
    y0 = 58 + dy + 26
    el.append(txt(24, y0, "Muddy Waters publishes 87 follow-ups against 55 first reports — 61% of its "
                 "output. Hindenburg publishes 9 against 94 — 9%.", size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, "Follow-ups are short and cite little at both firms, so pooling them in makes "
                 "a campaigning firm look like an easy corpus.", size=13, fill=INK2))

    # grid
    for v in range(0, int(ymax) + 1):
        el.append(f'<line x1="{L}" y1="{Y(v):.1f}" x2="{W-R}" y2="{Y(v):.1f}" stroke="{GRID}" stroke-width="1"/>')
        el.append(txt(L - 12, Y(v) + 4, str(v), size=11, fill=MUTED, anchor="end", tab=True))
    for v in range(0, int(xmax) + 1, 2000):
        el.append(f'<line x1="{X(v):.1f}" y1="{T}" x2="{X(v):.1f}" y2="{H-B}" stroke="{GRID}" stroke-width="1"/>')
        el.append(txt(X(v), H - B + 20, f"{v:,}" if v else "0", size=11, fill=MUTED, anchor="middle", tab=True))
    el.append(f'<line x1="{L}" y1="{H-B}" x2="{W-R}" y2="{H-B}" stroke="{BASELINE}" stroke-width="1.5"/>')
    el.append(f'<line x1="{L}" y1="{T}" x2="{L}" y2="{H-B}" stroke="{BASELINE}" stroke-width="1.5"/>')
    el.append(txt(L, H - B + 42, "median words per report", size=12, fill=INK2))
    el.append(f'<text x="{-(T + (H - B - T) / 2):.1f}" y="30" transform="rotate(-90)" '
              f'font-family=\'{FONT}\' font-size="12" fill="{INK2}" text-anchor="middle">'
              "median kinds of evidence cited</text>")

    for r in rows:
        c = HB if r["firm"] == "HB" else MW
        x, y, rad = X(r["words"]), Y(r["ev"]), RAD(r["n"])
        el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad:.1f}" fill="{c}" fill-opacity="0.22" '
                  f'stroke="{c}" stroke-width="2"/>')
        name = "Hindenburg" if r["firm"] == "HB" else "Muddy Waters"
        # Both firms' initial reports sit at the same height; centred labels would
        # overlap, so each is anchored on the side away from the other bubble.
        side = "end" if r["firm"] == "HB" else "start"
        ax = x - rad - 10 if side == "end" else x + rad + 10
        if ax + 140 > W - R:          # would run into the legend gutter
            ax, side = x, "middle"
            ly_, ly2 = y - rad - 22, y - rad - 7
        else:
            ly_, ly2 = y - 4, y + 12
        el.append(txt(ax, ly_, f"{name}", size=12.5, fill=INK, weight="600", anchor=side))
        el.append(txt(ax, ly2, f"{r['label']} — {r['n']}", size=11.5, fill=MUTED, anchor=side, tab=True))

    # legend: bubble area
    lx, ly = W - R + 26, T + 24
    el.append(txt(lx, ly, "bubble area = reports", size=12, fill=INK2, weight="600"))
    cy = ly + 30
    for n in (9, 55, 87):
        cy += RAD(n) + 12
        el.append(f'<circle cx="{lx+34:.1f}" cy="{cy:.1f}" r="{RAD(n):.1f}" fill="none" stroke="{MUTED}" stroke-width="1.5"/>')
        el.append(txt(lx + 78, cy + 4, f"{n}", size=11.5, fill=MUTED, tab=True))
        cy += RAD(n) + 12
    # The two firms are classified by different rules, so the claim was checked
    # against both. Applying Muddy Waters' structural rule to Hindenburg finds 5
    # repeat-target reports rather than 9 titled rebuttals — 5% against 9%. Either
    # way it is nowhere near 61%, so the finding does not rest on the definition.
    note, _ = para(lx, cy + 26, "A follow-up is any report on a target the firm had already "
                   "covered — from Muddy Waters' URL structure, from Hindenburg's "
                   "titles. Under the structural rule Hindenburg has 5, not 9; the "
                   "gap holds either way.", size=11, fill=MUTED, chars=30)
    el += note

    cap, _ = para(24, H - 46, f"Hindenburg initial reports carry a median {rows[0]['ev']:.0f} kinds of evidence "
                  f"in {rows[0]['words']:,.0f} words; its follow-ups {rows[1]['ev']:.0f} in {rows[1]['words']:,.0f}. "
                  f"Muddy Waters: {rows[2]['ev']:.0f} in {rows[2]['words']:,.0f} against "
                  f"{rows[3]['ev']:.0f} in {rows[3]['words']:,.0f}.", size=11.5, fill=MUTED, chars=150)
    el += cap
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print(f"  charts/two-businesses.svg")
    for r in rows:
        print(f"    {r['firm']} {r['label']:<16} n={r['n']:<4} {r['words']:>7,.0f}w  {r['ev']:.0f} evidence types")


if __name__ == "__main__":
    main()
