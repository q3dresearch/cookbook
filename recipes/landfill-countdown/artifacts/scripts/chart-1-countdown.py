#!/usr/bin/env python3
"""How long each open American landfill has left, against how much room is in it.

    python3 chart-1-countdown.py

One mark per landfill. Position on both axes, so the reader compares distances rather
than reading digits. Colour separates who owns the hole, because that is the segmentation
with a decision attached: a county that owns its own capacity is in a different position
from one buying it from a firm that holds a quarter of the country's.

Both axes are logarithmic and say so. Remaining capacity spans five orders of magnitude
and years-to-full four, so a linear axis would put nine tenths of the register in a
corner.
"""
import json, math, os, sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmopdata import DATA, load, num, owner_key, countdown
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plate                                                             # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "charts", "1-countdown.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
PRIV, PUB, HOT = "#b03a2e", "#1b4f8a", "#c07a1e"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


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
    pts = []
    for k, r in b.items():
        yrs, _ = countdown(r)
        if yrs is None:
            continue
        cap, wip = num(r.get("Landfill Design Capacity (tons)")), num(r.get("Waste in Place (tons)"))
        rem = max((cap or 0) - (wip or 0), 1)
        # Clamped to the drawn range rather than left to float outside it: a mark beyond
        # the axis asserts a position the axis does not define. The clamped ones are
        # labelled on the figure so the reader knows they are a floor, not a value.
        pts.append({"y": min(max(yrs, 0.25), 200), "rem": min(max(rem, 1e4), 4e8),
                    "clamped": yrs > 200,
                    "priv": str(r.get("Ownership Type") or "").strip() == "Private",
                    "owner": owner_key(r.get("Landfill Owner Organization(s)")),
                    "state": str(r.get("State") or "").strip(),
                    "name": str(r.get("Landfill Name") or "")[:40]})
    W, H, L, T, PW, PH = 1020, 680, 96, 160, 600, 380
    lx = lambda v: L + PW * (math.log10(v) - math.log10(0.25)) / (math.log10(200) - math.log10(0.25))
    ly = lambda v: T + PH - PH * (math.log10(v) - 4) / (math.log10(4e8) - 4)
    body = []
    for t in (0.25, 1, 5, 10, 25, 50, 100, 200):
        body.append(f'<line x1="{lx(t):.1f}" y1="{T}" x2="{lx(t):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
        body.append(txt(lx(t), T + PH + 20, f"{t:g}", size=11, fill=MUTED, anchor="middle"))
    for t in (1e4, 1e5, 1e6, 1e7, 1e8):
        body.append(f'<line x1="{L}" y1="{ly(t):.1f}" x2="{L+PW}" y2="{ly(t):.1f}" stroke="{GRID}"/>')
        lab = {1e4: "10k", 1e5: "100k", 1e6: "1M", 1e7: "10M", 1e8: "100M"}[t]
        body.append(txt(L - 10, ly(t) + 4, lab, size=11, fill=MUTED, anchor="end"))
    body.append(txt(L + PW / 2, T + PH + 46, "years until full, at the rate it is currently accepting waste",
                    size=12, fill=INK2, anchor="middle"))
    body.append(txt(L - 10, T - 36, "tons of room", size=11, fill=INK2, anchor="end"))
    body.append(txt(L - 10, T - 22, "left, permitted", size=11, fill=INK2, anchor="end"))
    # the five-year zone: the part with a decision in it
    body.append(f'<rect x="{lx(0.25):.1f}" y="{T}" width="{lx(5)-lx(0.25):.1f}" height="{PH}" '
                f'fill="{HOT}" fill-opacity="0.07"/>')
    under5 = sum(1 for p in pts if p["y"] < 5)
    body.append(txt(lx(5) - 8, T + 16, f"{under5} landfills full within five years", size=11.5,
                    fill=HOT, anchor="end", weight="600"))
    for p in sorted(pts, key=lambda p: -p["rem"]):
        body.append(f'<circle cx="{lx(p["y"]):.1f}" cy="{ly(p["rem"]):.1f}" r="3.2" '
                    f'fill="{PRIV if p["priv"] else PUB}" fill-opacity="0.5"/>')
    ly0 = T + 22
    for col, lab, n in ((PRIV, "privately owned", sum(1 for p in pts if p["priv"])),
                        (PUB, "publicly owned", sum(1 for p in pts if not p["priv"]))):
        body.append(f'<circle cx="{L+PW+22:.1f}" cy="{ly0-4:.1f}" r="4.5" fill="{col}" fill-opacity="0.7"/>')
        body.append(txt(L + PW + 34, ly0, f"{lab}  {n}", size=11, fill=col))
        ly0 += 18
    body += wrap(L + PW + 22, T + 78,
                 "Each mark is one landfill that reports a design capacity, a dated stock and an "
                 "acceptance rate: 863 of 1,266 open sites.",
                 size=10.5, fill=MUTED, chars=28, leading=13)
    nclamp = sum(1 for p in pts if p["clamped"])
    if nclamp:
        body.append(txt(lx(200), T + PH - 8, f"{nclamp} sites sit past 200 years", size=10.5,
                        fill=MUTED, anchor="end"))
    body += wrap(L + PW + 22, T + 168,
                 "Up and to the right is a big hole filling slowly. Bottom left is a small one "
                 "about to close. The band is where a county has to have already started "
                 "planning.",
                 size=10.5, fill=MUTED, chars=28, leading=13)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Eighty American landfills are full within five years", size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="a waste authority or hauler planning where capacity goes after 2030",
                        decide="whether to secure alternative capacity now or wait for the market",
                        wrong="the sites named revise their remaining capacity upward")
    s += fr
    s += body
    fy = H - 22 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    foot = ["If you are a county in the shaded band, the decision is already live: siting takes longer "
            "than the capacity you have left.",
            "The countdown assumes today's acceptance rate holds. Tested against the 29 closures "
            "between the two editions: neighbours within 40 km did not accelerate (figure 3, followup.py).",
            "Computable for 863 of 1,266 open sites. 288 report no design capacity and 32 report a "
            "stock older than 2020, which cannot be divided by a current flow."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}  ({len(pts)} landfills)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
