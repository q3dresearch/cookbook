#!/usr/bin/env python3
"""What America sends abroad, where it goes, and what happens to it there.

    python3 chart-5-exports.py

`receiver_state` carries `FC` for a foreign country — a value that is not a state and will
silently corrupt any state-level total that does not handle it. Handled instead, it is the
most surprising thing in the register.

**Exports rose from 90,000 tons in 2001 to 160,000 in 2023 while total shipped waste fell.**
Mexico takes two thirds of it and Canada most of the rest, identifiable because the
receiver ids are literal: `FCMEXICO`, `FCC…`.

**And 53% of it is one waste code.** K061 is electric-arc-furnace dust — what a steel mill's
baghouse catches, and zinc, lead and cadmium by definition. **70% of all exports go to
metals recovery.** America ships its steel-mill dust abroad to have the zinc taken out of
it, and the volume has doubled in twenty years.

The other 11% goes abroad to be **landfilled**, which is a different transaction: not a
material with value in it, just somewhere else to put it.

The basket is all twelve management categories. Waste exported for incineration would not
appear here, so the export total is a floor. An earlier caption said six, long after the
basket was widened.
"""
import collections, csv, glob, gzip, os, re, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
CACHE = os.environ.get("HWF_CACHE") or os.path.join(DATA, "br-cache")
sys.path.insert(0, HERE)
import plate
import brdata, plate                                                            # noqa: E402

# Declared, not discovered. An earlier version globbed the cache and summed whatever a
# background pull had finished writing, so the same code gave 30.8M tons for 2001 one hour
# and 226M the next. The basket now travels with the number.
BASKET = brdata.REQUIRED

OUT = os.path.join(HERE, "..", "charts", "exports.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
MX, CA_, OTH, HOT = "#b03a2e", "#c07a1e", "#9a988f", "#1b7f5a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
CYCLES = list(range(2001, 2024, 2))
num = lambda v: float(v) if v not in ("", "None", None) else 0.0


def txt(x, y, s, *, size, fill, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" style="font-variant-numeric: tabular-nums">{escape(str(s))}</text>')


def halo(x, y, s, *, size, fill, anchor="start", weight="600"):
    c = (f'font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" '
         f'style="font-variant-numeric: tabular-nums"')
    e = escape(str(s))
    return [f'<text x="{x:.1f}" y="{y:.1f}" fill="none" stroke="{SURFACE}" stroke-width="3" '
            f'stroke-linejoin="round" {c}>{e}</text>',
            f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" {c}>{e}</text>']


def wrap(x, y, s, *, size, fill, chars, leading=15.0):
    words, line, out, n = str(s).split(), [], [], 0
    for w in words:
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill)); line, n = [], n + 1
        line.append(w)
    if line:
        out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
    return out


def dest(rid):
    s = (rid or "").upper().replace(" ", "")
    if s.startswith("FCM"):
        return "Mexico"
    if s.startswith("FCC"):
        return "Canada"
    return "elsewhere"


def load(y):
    return [r for r in brdata.load(y, BASKET) if r["br_form"] == "GM"]


def main():
    series, shipped = {}, {}
    latest_codes, latest_cat = collections.Counter(), collections.Counter()
    for y in CYCLES:
        gm = load(y)
        if not gm:
            continue
        shipped[y] = sum(num(r["shipped_tons"]) for r in gm)
        c = collections.Counter()
        for r in gm:
            if (r["receiver_state"] or "").strip() != "FC":
                continue
            t = num(r["shipped_tons"])
            c[dest(r["receiver_id"])] += t
            if y == CYCLES[-1]:
                cs = re.findall(r"[A-Z]\d{3}", r["federal_waste_codes"] or "")
                latest_codes[cs[0] if cs else "(none)"] += t
                latest_cat[r["management_category"]] += t
        series[y] = c
    ys = [y for y in CYCLES if y in series]
    tot = {y: sum(series[y].values()) for y in ys}
    hi = max(tot.values()) * 1.12

    W, H, L, T, PW, PH = 1040, 724, 96, 208, 500, 386
    RX, RW = 646, 300
    lx = lambda y: L + PW * (y - ys[0]) / (ys[-1] - ys[0])
    ly = lambda v: T + PH - PH * v / hi
    body = []
    body.append(txt(L, T - 44, "tons sent out of the United States", size=12.5, fill=INK, weight="600"))
    for t in (0, 50_000, 100_000, 150_000):
        body.append(f'<line x1="{L}" y1="{ly(t):.1f}" x2="{L+PW}" y2="{ly(t):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ly(t) + 4, f"{t//1000}k" if t else "0", size=11, fill=MUTED, anchor="end"))
    for y in ys[::2]:
        body.append(f'<line x1="{lx(y):.1f}" y1="{T}" x2="{lx(y):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
        body.append(txt(lx(y), T + PH + 20, str(y), size=10.5, fill=MUTED, anchor="middle"))
    order = [("Mexico", MX), ("Canada", CA_), ("elsewhere", OTH)]
    base = {y: 0.0 for y in ys}
    for name, col in order:
        pts_top, pts_bot = [], []
        for y in ys:
            v = series[y].get(name, 0.0)
            pts_top.append((lx(y), ly(base[y] + v)))
            pts_bot.append((lx(y), ly(base[y])))
            base[y] += v
        d = ("M" + "L".join(f"{x:.1f},{y_:.1f}" for x, y_ in pts_top) + "L"
             + "L".join(f"{x:.1f},{y_:.1f}" for x, y_ in reversed(pts_bot)) + "Z")
        body.append(f'<path d="{d}" fill="{col}" fill-opacity="0.82"/>')
        mid = ys[len(ys) // 2]
        v = series[mid].get(name, 0.0)
        if v > hi * 0.06:
            body += halo(lx(mid), ly(base[mid] - v / 2) + 4, name, size=11.5,
                         fill=INK, anchor="middle", weight="700")
    body += halo(lx(ys[0]) + 6, ly(tot[ys[0]]) - 10, f"{tot[ys[0]]/1e3:,.0f}k", size=12.5, fill=INK)
    body += halo(lx(ys[-1]) - 6, ly(tot[ys[-1]]) - 10, f"{tot[ys[-1]]/1e3:,.0f}k", size=12.5,
                 fill=INK, anchor="end")
    ex_g = tot[ys[-1]] / tot[ys[0]] - 1
    sh_g = shipped[ys[-1]] / shipped[ys[0]] - 1
    body += wrap(L + 10, T + 26,
                 f"Exports grew {ex_g:+.0%} against {sh_g:+.0%} for waste shipped anywhere, so the "
                 f"share going abroad rose from {tot[ys[0]]/shipped[ys[0]]:.1%} to "
                 f"{tot[ys[-1]]/shipped[ys[-1]]:.1%}.",
                 size=11.5, fill=INK, chars=42, leading=14)

    tl = sum(latest_codes.values())
    body.append(txt(RX, T - 44, f"what left in {ys[-1]}", size=12.5, fill=INK, weight="600"))
    body.append(txt(RX, T - 28, "by the first waste code on the record", size=10.5, fill=MUTED))
    yy = T
    for k, v in latest_codes.most_common(6):
        w = RW * v / tl
        body.append(f'<rect x="{RX}" y="{yy:.1f}" width="{max(w,1):.1f}" height="17" fill="{MX}" '
                    f'fill-opacity="{0.9 if k=="K061" else 0.45}"/>')
        lab = "K061  electric-arc-furnace dust" if k == "K061" else k
        if w > 120:
            body.append(txt(RX + 5, yy + 13, lab, size=10, fill="#ffffff"))
            body.append(txt(RX + w + 7, yy + 13, f"{v/tl:.0%}", size=10, fill=INK2))
        else:
            body.append(txt(RX + max(w, 1) + 7, yy + 13, f"{lab}   {v/tl:.0%}", size=10, fill=INK2))
        yy += 24
    yy += 18
    body.append(txt(RX, yy, "and what happens to it there", size=12.5, fill=INK, weight="600"))
    yy += 16
    tc = sum(latest_cat.values())
    for k, v in latest_cat.most_common(5):
        w = RW * v / tc
        col = HOT if "RECOVERY" in k else ("#8c2318" if k == "LANDFILL" else OTH)
        body.append(f'<rect x="{RX}" y="{yy:.1f}" width="{max(w,1):.1f}" height="17" fill="{col}"/>')
        if w > 110:
            body.append(txt(RX + 5, yy + 13, k.lower()[:26], size=10, fill="#ffffff"))
            body.append(txt(RX + w + 7, yy + 13, f"{v/tc:.0%}", size=10, fill=INK2))
        else:
            body.append(txt(RX + max(w, 1) + 7, yy + 13, f"{k.lower()[:24]}   {v/tc:.0%}",
                            size=10, fill=INK2))
        yy += 24
    body += wrap(RX, yy + 16,
                 "Seven tons in ten leave for metals recovery. One in ten leaves to be buried, which "
                 "is a different transaction: not a material with value in it, just somewhere else to "
                 "put it.", size=10.5, fill=INK2, chars=46, leading=13)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "America sends its steel-mill dust to Mexico to have the zinc taken out",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="anyone sizing domestic recovery capacity from this register",
                        decide="whether exported tonnage counts as recovered at home",
                        wrong="export tonnage reverses when domestic capacity opens")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    foot = [f"Exports grew {tot[ys[-1]]/tot[ys[0]]-1:+.0%} — {tot[ys[0]]/1e3:,.0f}k tons in {ys[0]} to "
            f"{tot[ys[-1]]/1e3:,.0f}k in {ys[-1]} — while the tonnage managed in every category fell.",
            "K061 is what a steel mill's baghouse catches: zinc, lead and cadmium by definition. It is "
            "worth recovering, and the recovery increasingly happens elsewhere.",
            "All twelve management categories. Waste exported for incineration would not appear here, so the "
            "export total is a floor."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"  {tot[ys[0]]/1e3:,.0f}k -> {tot[ys[-1]]/1e3:,.0f}k tons; "
          f"K061 {latest_codes['K061']/tl:.0%} of exports")
    return 0


if __name__ == "__main__":
    sys.exit(main())
