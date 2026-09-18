#!/usr/bin/env python3
"""Who holds America's remaining landfill room — as two populations, not one.

    python3 chart-2-owners.py

A first version put every owner on one scatter of sites held against room held. Of the 540
owners whose sites report both a capacity and a stock, 510 hold exactly one, so they
stacked into a single column at x=1 and the figure was a wall with five dots beside it.

Worse than ugly: it mixed two categories and let the reader read a trend across the join.
**Single-site owners are 9% private. Multi-site owners are 43% private, and the five
owners of twenty sites or more are 93% private.**
So a line drawn through the whole cloud is mostly measuring counties turning into
companies, not scale doing anything. That is a category effect wearing a trend's clothes.

So the tail is drawn as its own study, on a shared vertical axis: the 30 multi-site owners
as a scatter on the left, the 510 single-site owners as a distribution on the right. The
comparison the chart is actually for — is a big owner big because it has many holes or
big ones — is answerable on the left, and the right says what the typical county holds.
"""
import collections, math, os, random, sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmopdata import load, num, owner_key
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plate                                                             # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "charts", "2-owners.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
PRIV, PUB = "#b03a2e", "#1b4f8a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
SEED = 20260916


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


def main():
    b = load("2024")
    cap, sites, priv, label = collections.Counter(), collections.Counter(), {}, {}
    for r in b.values():
        if str(r.get("Current Landfill Status") or "").strip() != "Open":
            continue
        c, w = num(r.get("Landfill Design Capacity (tons)")), num(r.get("Waste in Place (tons)"))
        if c is None or w is None:
            continue
        k = owner_key(r.get("Landfill Owner Organization(s)"))
        if not k:
            continue
        cap[k] += max(c - w, 0)
        sites[k] += 1
        priv[k] = str(r.get("Ownership Type") or "").strip() == "Private"
        label.setdefault(k, str(r.get("Landfill Owner Organization(s)") or "")[:26])
    tot = sum(cap.values())
    multi = [k for k in cap if sites[k] >= 2]
    solo = [k for k in cap if sites[k] == 1]
    mtot, stot = sum(cap[k] for k in multi), sum(cap[k] for k in solo)
    mpriv = sum(priv[k] for k in multi) / len(multi)
    spriv = sum(priv[k] for k in solo) / len(solo)

    W, H, T, PH = 1060, 720, 182, 372
    L, PW = 118, 430           # left panel: multi-site owners
    SL, SW = 600, 118          # right panel: the single-site tail
    lx = lambda v: L + PW * (math.log10(max(v, 2)) - math.log10(2)) / (math.log10(200) - math.log10(2))
    ly = lambda v: T + PH - PH * (math.log10(max(v, 1e4)) - 4) / (math.log10(6e9) - 4)
    body = []
    for t, lab in ((1e4, "10k"), (1e5, "100k"), (1e6, "1M"), (1e7, "10M"), (1e8, "100M"), (1e9, "1bn")):
        body.append(f'<line x1="{L}" y1="{ly(t):.1f}" x2="{SL+SW}" y2="{ly(t):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ly(t) + 4, lab, size=11, fill=MUTED, anchor="end"))
    body.append(txt(L - 10, T - 36, "tons of permitted", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - 22, "room left", size=11, fill=INK2, anchor="end"))
    for t in (2, 5, 10, 25, 50, 100, 200):
        body.append(f'<line x1="{lx(t):.1f}" y1="{T}" x2="{lx(t):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
        body.append(txt(lx(t), T + PH + 20, t, size=11, fill=MUTED, anchor="middle"))
    body.append(txt(L + PW / 2, T + PH + 48, "open landfills held", size=12, fill=INK2, anchor="middle"))

    # equal-average-site-size diagonals: the many-vs-big question, which only the left
    # panel can answer because the right panel has one site by construction.
    for per, lab in ((1e5, "100k tons per site"), (1e7, "10M per site")):
        body.append(f'<line x1="{lx(2):.1f}" y1="{ly(per*2):.1f}" x2="{lx(200):.1f}" '
                    f'y2="{ly(per*200):.1f}" stroke="{MUTED}" stroke-width="0.9" stroke-dasharray="3,4"/>')
        # Anchored at whichever end of its own line is empty: the 10M line runs through
        # the cluster of small public owners on the left, the 100k line through nothing.
        at, side = ((200, "end") if per == 1e7 else (2.6, "start"))
        body.append(txt(lx(at) + (0 if side == "end" else 0), ly(per * at) + 15, lab,
                        size=10, fill=MUTED, anchor=side))

    named, placed = 0, []
    for k in sorted(multi, key=lambda k: -cap[k]):
        x, y, v = lx(sites[k]), ly(cap[k]), cap[k]
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.4" fill="{PRIV if priv[k] else PUB}" '
                    f'fill-opacity="0.6"/>')
        if named < 7 and v / tot > 0.012:
            right = x < L + PW * 0.5
            ty = y + 4
            while any(abs(ty - q) < 15 and abs(x - qx) < 240 for qx, q in placed):
                ty += 15
            placed.append((x, ty))
            if abs(ty - (y + 4)) > 2:
                body.append(f'<path d="M{x + (6 if right else -6):.1f} {y:.1f} '
                            f'L{x + (11 if right else -11):.1f} {ty-4:.1f}" stroke="{MUTED}" stroke-width="0.8"/>')
            body.append(txt(x + (12 if right else -12), ty, f"{label[k]}  {v/tot:.0%}", size=11,
                            fill=PRIV if priv[k] else PUB, anchor="start" if right else "end", weight="600"))
            named += 1

    # The tail, as its own panel. Jitter is seeded so the figure is reproducible.
    body.append(f'<line x1="{SL-22}" y1="{T-8}" x2="{SL-22}" y2="{T+PH+8}" stroke="{RULE}"/>')
    body.append(f'<rect x="{SL}" y="{T}" width="{SW}" height="{PH}" fill="{GRID}" fill-opacity="0.45"/>')
    rng = random.Random(SEED)
    for k in solo:
        x = SL + SW / 2 + rng.uniform(-SW * 0.42, SW * 0.42)
        body.append(f'<circle cx="{x:.1f}" cy="{ly(cap[k]):.1f}" r="2.4" '
                    f'fill="{PRIV if priv[k] else PUB}" fill-opacity="0.42"/>')
    med = sorted(cap[k] for k in solo)[len(solo) // 2]
    body.append(f'<line x1="{SL-4}" y1="{ly(med):.1f}" x2="{SL+SW+4}" y2="{ly(med):.1f}" '
                f'stroke="{INK}" stroke-width="1.4"/>')
    body.append(txt(SL + SW + 10, ly(med) + 4, f"median {med/1e6:.1f}M", size=10.5, fill=INK))
    body.append(txt(SL + SW / 2, T + PH + 20, "one site each", size=11, fill=MUTED, anchor="middle"))
    body.append(txt(SL + SW / 2, T + PH + 48, f"{len(solo)} owners", size=12, fill=INK2, anchor="middle"))
    body.append(txt(SL + SW / 2, T - 14, "the tail, as its own study", size=11, fill=INK2,
                    anchor="middle", weight="600"))

    top = sorted((cap[k] for k in multi), reverse=True)
    ly0 = T + PH - 52
    for col, lab in ((PRIV, "private owner"), (PUB, "public owner")):
        body.append(f'<circle cx="{L+14:.1f}" cy="{ly0-4:.1f}" r="4.5" fill="{col}" fill-opacity="0.7"/>')
        body.append(txt(L + 26, ly0, lab, size=11, fill=col))
        ly0 += 17

    top2 = sorted((cap[k] for k in multi), reverse=True)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Half of America's remaining landfill room belongs to two companies",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="a municipality negotiating a disposal contract",
                        decide="whether you are negotiating in a competitive market or with a duopoly",
                        wrong="a third owner reaches a double-digit share of remaining room")
    s += fr
    s += body
    fy = H - 22 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    foot = ["A county negotiating disposal is negotiating with one of two firms in much of the country, "
            "and its alternative is capacity it does not own and cannot build quickly.",
            f"The {len(multi)} multi-site owners hold {mtot/tot:.0%} of the room; the {len(solo)} "
            f"single-site owners hold {stot/tot:.0%} of it, a median {med/1e6:.1f}M tons each.",
            "Owner names are normalised first. Raw, the register reports 304 ownership changes between "
            "its two editions; 250 are one firm renaming itself to WM, and regional suffixes split a fourth."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"  {len(multi)} multi-site owners hold {mtot/tot:.1%}; {len(solo)} single-site hold {stot/tot:.1%}")
    print(f"  private share: multi-site {mpriv:.0%}, single-site {spriv:.0%}  <- the category effect")
    return 0


if __name__ == "__main__":
    sys.exit(main())
