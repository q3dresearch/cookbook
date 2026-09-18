#!/usr/bin/env python3
"""Which American counties take the hazardous waste, and what happens to it there.

    python3 chart-4-where.py

The generating end is barely spread at all: **basic chemicals alone makes 60% of American
hazardous waste** and petroleum refining another 17%, so three quarters of it comes from
two industries. The receiving end is narrower still.

**121 counties receive any of it, and ten of them take 58%.** In 2001 it was 188 counties
and 44%. The tonnage did not grow; it gathered.

And five of the top eight counties host **exactly one facility**. Lamar County, Alabama
takes 344,000 tons a year through a single site, all of it metals recovery. Kern, Kings and
Major counties each have one landfill and nothing else. That is a different kind of fact
from a share: it is a specific place with a specific business in it.

The bar is split by what actually happens to the waste on arrival, because "receives
hazardous waste" covers a county whose site recovers metals from it and a county whose site
buries it, and those are not the same thing to live next to.

All twelve management categories. An earlier version of this figure ran on six and its caption
said so long after the basket was widened — the numbers were right and the note described a
previous version of itself.
"""
import collections, csv, glob, gzip, os, sys
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

OUT = os.path.join(HERE, "..", "charts", "where.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
COL = {"DEEPWELL / UNDERGROUND INJECTION": ("#4a4a8a", "deep-well injection"),
       "LANDFILL": ("#8c2318", "landfill"),
       "METALS RECOVERY": ("#1b7f5a", "metals recovery"),
       "SOLVENTS RECOVERY": ("#5aa17f", "solvents recovery"),
       "OTHER RECOVERY": ("#9ac4a8", "other recovery"),
       "ENERGY RECOVERY": ("#c07a1e", "energy recovery")}
num = lambda v: float(v) if v not in ("", "None", None) else 0.0


def txt(x, y, s, *, size, fill, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" style="font-variant-numeric: tabular-nums">{escape(str(s))}</text>')


def wrap(x, y, s, *, size, fill, chars, leading=15.0):
    words, line, out, n = str(s).split(), [], [], 0
    for w in words:
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill)); line, n = [], n + 1
        line.append(w)
    if line:
        out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
    return out


def load(y):
    return [r for r in brdata.load(y, BASKET) if r["br_form"] == "WR"]


def county_stats(y):
    wr = load(y)
    tons, mix, sites = collections.Counter(), collections.defaultdict(collections.Counter), \
        collections.defaultdict(set)
    for r in wr:
        k = (r["state"], (r["county_name"] or "").title())
        t = num(r["managed_tons"])
        if t <= 0:
            continue
        tons[k] += t
        mix[k][r["management_category"]] += t
        sites[k].add(r["handler_id"])
    return tons, mix, sites


def main():
    hist = {}
    for y in (2001, 2009, 2017, 2023):
        t, _, _ = county_stats(y)
        v = sorted(t.values(), reverse=True)
        hist[y] = (len(t), sum(v[:10]) / sum(v), sum(v))
    tons, mix, sites = county_stats(2023)
    total = sum(tons.values())
    top = tons.most_common(12)

    W, H = 1060, 852
    LBL, BX, BW = 28, 258, 520
    T, RH = 236, 36
    body = []
    body.append(txt(LBL, T - 44, "tons of hazardous waste received in 2023, and what happens to it there",
                    size=12.5, fill=INK, weight="600"))
    mx = top[0][1]
    for i, tick in enumerate((0, 100_000, 200_000, 300_000, 400_000)):
        x = BX + BW * tick / (mx * 1.05)
        body.append(f'<line x1="{x:.1f}" y1="{T-22}" x2="{x:.1f}" y2="{T+RH*len(top)-10}" stroke="{GRID}"/>')
        body.append(txt(x, T - 28, f"{tick//1000:,}k" if tick else "0", size=10, fill=MUTED, anchor="middle"))
    for i, (k, v) in enumerate(top):
        y = T + i * RH
        n = len(sites[k])
        body.append(txt(LBL, y + 4, f"{k[1]}, {k[0]}"[:26], size=11.5, fill=INK, weight="600"))
        body.append(txt(LBL, y + 18, f"{n} site{'s' if n != 1 else ''}", size=10,
                        fill=INK if n == 1 else MUTED, weight="600" if n == 1 else "normal"))
        x = BX
        for cat, ct in mix[k].most_common():
            w = BW * ct / (mx * 1.05)
            col = COL.get(cat, ("#9a988f", cat.lower()))[0]
            body.append(f'<rect x="{x:.1f}" y="{y-8:.1f}" width="{max(w,0.7):.1f}" height="20" fill="{col}"/>')
            x += w
        body.append(txt(x + 8, y + 6, f"{v/1e3:,.0f}k   {v/total:.0%}", size=10.5, fill=INK2))

    y0 = T + RH * len(top) + 20
    xp = BX
    for cat, (col, lab) in COL.items():
        if not any(cat in mix[k] for k, _ in top):
            continue
        body.append(f'<rect x="{xp:.1f}" y="{y0-9:.1f}" width="13" height="11" fill="{col}"/>')
        body.append(txt(xp + 18, y0, lab, size=10.5, fill=col))
        xp += 24 + len(lab) * 6.0
        if xp > BX + BW - 60:
            xp = BX; y0 += 16

    body.append(txt(LBL, T + RH * len(top) + 20, "how many counties take any at all",
                    size=11.5, fill=INK, weight="600"))
    yy = T + RH * len(top) + 40
    for y_ in (2001, 2009, 2017, 2023):
        n, sh, tot = hist[y_]
        body.append(txt(LBL, yy, f"{y_}", size=10.5, fill=MUTED))
        body.append(txt(LBL + 38, yy, f"{n} counties", size=10.5, fill=INK))
        body.append(txt(LBL + 120, yy, f"top 10 = {sh:.0%}", size=10.5, fill=INK2))
        yy += 15

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "One site in Lamar County, Alabama takes 344,000 tons a year",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="siting, emergency planning and environmental-justice review",
                        decide="which counties are worth a site visit",
                        wrong="the top county's tonnage turns out to be spread over many sites")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    foot = ["Receiving a county's worth of hazardous waste is not one thing: Lamar recovers metals "
            "from it, Kern and Kings bury it, Harris injects 97% of it underground.",
            f"188 counties received waste in 2001 and {hist[2023][0]} in 2023, while the tonnage did "
            f"not grow. The top ten went from 44% to {hist[2023][1]:.0%}. It gathered rather than spread.",
            "All twelve management categories. An earlier version ran on six. "
            "remove them, so this concentration is a floor, not a ceiling."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"  {hist[2023][0]} counties, top10 {hist[2023][1]:.0%}; "
          f"single-site among top 8: {sum(1 for k,_ in top[:8] if len(sites[k])==1)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
