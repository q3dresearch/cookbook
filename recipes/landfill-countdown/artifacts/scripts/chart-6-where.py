#!/usr/bin/env python3
"""Where America's landfill room runs out, and where it is getting worse.

    python3 chart-6-where.py

Question 2 of this recipe -- where does the room run out first -- had an answer and no
figure for three revisions, which is the failure mode of writing prose about a geography.

Left: every open landfill that reports a countdown, placed by its own coordinates on an
Albers equal-area conic, coloured by how long it has left and sized by how much room is
in it. Equal-area matters for a map of a physical stock: a projection that inflates the
north would inflate Minnesota's share of the country's remaining room by eye.

Right: the twelve states with the shortest median countdown, each drawn as the move from
its 2021 median to its 2024 median across a fixed basket of the same landfills. A state
can be short and recovering or short and sinking, and those are opposite instructions.

**New York is both the shortest and among the fastest sinking: a median of 16 years in
2021 and 10 in 2024.** Pennsylvania started at the same 16 and is now at 24, so the
difference is not geology. Arizona went from 55 to 80.

Territories are not projected onto the map. Puerto Rico alone has 22 open landfills and
putting them in an inset box at a made-up scale would assert a geography that is not
there, so they are drawn as a labelled strip with the same colour scale.
"""
import collections, math, os, statistics as st, sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmopdata import load, num, countdown
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plate                                                             # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "charts", "6-where.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
CAP, WIP, YR = "Landfill Design Capacity (tons)", "Waste in Place (tons)", "Waste in Place Year"
CLASSES = ((0, 5, "#8c2318", "under 5 years"), (5, 15, "#c96a1b", "5 to 15"),
           (15, 40, "#7fa8c4", "15 to 40"), (40, 1e12, "#1b4f8a", "over 40"))
P1, P2, P0, L0 = 29.5, 45.5, 23.0, -96.0


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


def albers(lat, lon):
    """Albers equal-area conic. Equal-area because the marks stand for a physical stock."""
    r = math.radians
    n = (math.sin(r(P1)) + math.sin(r(P2))) / 2
    C = math.cos(r(P1)) ** 2 + 2 * n * math.sin(r(P1))
    rho0 = math.sqrt(C - 2 * n * math.sin(r(P0))) / n
    theta = n * r(lon - L0)
    rho = math.sqrt(max(C - 2 * n * math.sin(r(lat)), 0)) / n
    return rho * math.sin(theta), rho0 - rho * math.cos(theta)


def colour(y):
    for lo, hi, c, _ in CLASSES:
        if lo <= y < hi:
            return c
    return CLASSES[-1][2]


def main():
    a, b = load("2021"), load("2024")
    conus, off = [], collections.defaultdict(list)
    for r in b.values():
        if str(r.get("Current Landfill Status") or "").strip() != "Open":
            continue
        y, _ = countdown(r)
        la, lo = num(r.get("Latitude")), num(r.get("Longitude"))
        if y is None or not la or not lo:
            continue
        cap, wip = num(r.get(CAP)), num(r.get(WIP))
        d = {"y": y, "rem": max((cap or 0) - (wip or 0), 1e4),
             "st": str(r.get("State") or "").strip(), "la": la, "lo": lo}
        if 24 < la < 50 and -126 < lo < -66:
            conus.append(d)
        else:
            off[d["st"]].append(d)

    pair = collections.defaultdict(list)
    for k in sorted(set(a) & set(b)):
        y0, _ = countdown(a[k], fresh=2017)
        y1, _ = countdown(b[k], fresh=2020)
        t0, t1 = num(a[k].get(YR)), num(b[k].get(YR))
        if y0 is None or y1 is None or not t0 or not t1 or t1 - t0 != 3:
            continue
        pair[str(b[k].get("State") or "").strip()].append((y0, y1))
    states = sorted(((st.median([q for _, q in v]), st.median([q for q, _ in v]), s, len(v))
                     for s, v in pair.items() if len(v) >= 10))[:12]

    W, H = 1060, 760
    MX, MY, MW, MH = 34, 186, 626, 356
    SX, SW, SY, SRH = 712, 250, 208, 27
    xs = [albers(d["la"], d["lo"]) for d in conus]
    x0, x1 = min(p[0] for p in xs), max(p[0] for p in xs)
    y0_, y1_ = min(p[1] for p in xs), max(p[1] for p in xs)
    sc = min(MW / (x1 - x0), MH / (y1_ - y0_))
    ox = MX + (MW - (x1 - x0) * sc) / 2
    oy = MY + (MH - (y1_ - y0_) * sc) / 2
    px = lambda x: ox + (x - x0) * sc
    py = lambda y: oy + (y1_ - y) * sc
    rmax = max(d["rem"] for d in conus)
    body = []

    for d, (x, y) in sorted(zip(conus, xs), key=lambda t: -t[0]["rem"]):
        r = 1.7 + 6.4 * (d["rem"] / rmax) ** 0.5
        body.append(f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="{r:.1f}" fill="{colour(d["y"])}" '
                    f'fill-opacity="0.62"/>')
    # State letters at the centroid of that state's own marks: orientation without
    # borrowing a boundary file, and it only names states the figure is about.
    cen = collections.defaultdict(list)
    for d, (x, y) in zip(conus, xs):
        cen[d["st"]].append((px(x), py(y)))
    for _, _, s, _ in states:
        if s in cen and len(cen[s]) >= 4:
            body.append(txt(sum(p[0] for p in cen[s]) / len(cen[s]),
                            sum(p[1] for p in cen[s]) / len(cen[s]) + 4, s, size=12,
                            fill=INK, anchor="middle", weight="700"))

    ly = MY + MH + 26
    body.append(txt(MX + 4, ly, "years of room left", size=11, fill=INK2, weight="600"))
    lxp = MX + 130
    for lo, hi, c, lab in CLASSES:
        n = sum(1 for d in conus if lo <= d["y"] < hi)
        body.append(f'<circle cx="{lxp:.1f}" cy="{ly-4:.1f}" r="5" fill="{c}" fill-opacity="0.75"/>')
        body.append(txt(lxp + 11, ly, f"{lab}  {n}", size=10.5, fill=c))
        lxp += 118
    body.append(txt(MX + 4, ly + 18, "mark area is the room left in that landfill", size=10, fill=MUTED))

    # the territories, as a strip rather than a fake inset
    ty = ly + 58
    body.append(txt(MX + 4, ty - 12, f"off the map, at no scale", size=10.5, fill=INK2, weight="600"))
    tx = MX + 4
    for s in sorted(off, key=lambda s: -len(off[s])):
        body.append(txt(tx, ty + 4, s, size=10, fill=MUTED))
        for i, d in enumerate(sorted(off[s], key=lambda d: d["y"])):
            body.append(f'<circle cx="{tx+24+i*7.5:.1f}" cy="{ty:.1f}" r="3.1" fill="{colour(d["y"])}" '
                        f'fill-opacity="0.75"/>')
        tx += 34 + len(off[s]) * 7.5 + 16

    body.append(txt(SX, SY - 42, "the twelve shortest states", size=13, fill=INK, weight="600"))
    body += wrap(SX, SY - 26, "median years left, 2021 to 2024, over the same landfills in both editions",
                 size=10.5, fill=MUTED, chars=44, leading=12)
    sx0, sx1 = SX + 44, SX + SW
    vmax = max(max(m0, m1) for m1, m0, _, _ in states) * 1.08
    sxp = lambda v: sx0 + (sx1 - sx0) * min(v, vmax) / vmax
    for t in (0, 10, 20, 30, 40):
        if t <= vmax:
            body.append(f'<line x1="{sxp(t):.1f}" y1="{SY-4}" x2="{sxp(t):.1f}" '
                        f'y2="{SY+SRH*len(states)-4:.1f}" stroke="{GRID}"/>')
            body.append(txt(sxp(t), SY + SRH * len(states) + 10, f"{t}", size=9.5,
                            fill=MUTED, anchor="middle"))
    body.append(txt((sx0 + sx1) / 2, SY + SRH * len(states) + 26, "median years of room left",
                    size=10.5, fill=INK2, anchor="middle"))
    for i, (m1, m0, s, n) in enumerate(states):
        y = SY + i * SRH + 6
        body.append(txt(SX, y + 4, s, size=11.5, fill=INK, weight="600"))
        worse = m1 < m0
        body.append(f'<line x1="{sxp(m0):.1f}" y1="{y:.1f}" x2="{sxp(m1):.1f}" y2="{y:.1f}" '
                    f'stroke="{"#8c2318" if worse else "#1b7f5a"}" stroke-width="2" stroke-opacity="0.75"/>')
        body.append(f'<circle cx="{sxp(m0):.1f}" cy="{y:.1f}" r="3" fill="{MUTED}"/>')
        body.append(f'<circle cx="{sxp(m1):.1f}" cy="{y:.1f}" r="4.6" '
                    f'fill="{"#8c2318" if worse else "#1b7f5a"}"/>')
        body.append(txt(sxp(m1) + (9 if m1 >= m0 else -9), y + 4, f"{m1:.0f}", size=10,
                        fill=INK2, anchor="start" if m1 >= m0 else "end"))
    ey = SY + SRH * len(states) + 52
    body.append(f'<circle cx="{SX+6:.1f}" cy="{ey-4:.1f}" r="3" fill="{MUTED}"/>')
    body.append(txt(SX + 16, ey, "2021", size=10, fill=MUTED))
    body.append(f'<circle cx="{SX+62:.1f}" cy="{ey-4:.1f}" r="4.6" fill="#8c2318"/>')
    body.append(txt(SX + 72, ey, "2024, worse", size=10, fill="#8c2318"))
    body.append(f'<circle cx="{SX+152:.1f}" cy="{ey-4:.1f}" r="4.6" fill="#1b7f5a"/>')
    body.append(txt(SX + 162, ey, "better", size=10, fill="#1b7f5a"))
    body += wrap(SX, ey + 26,
                 "New York is the shortest and among the fastest sinking. Pennsylvania started at the "
                 "same 16 years and is now at 24, so the difference is policy, not geology.",
                 size=11, fill=INK, chars=42, leading=14)

    s_ = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
          f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
          txt(28, 40, "Whether your landfill is nearly full is mostly a question of which state you are in",
              size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="anyone comparing landfill scarcity across operators",
                        decide="whether to compare sites nationally or only within a state",
                        wrong="within-state variation comes to exceed between-state")
    s_ += fr
    s_ += body
    fy = H - 20 - 15 * 2
    s_.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    noff = sum(len(v) for v in off.values())
    foot = ["If you are siting a replacement, the state is the unit that matters: New York's median site "
            "has 10 years and Arizona's has 86, and permits are issued by the state.",
            f"{len(conus):,} landfills are drawn on the map and {noff} territorial sites in the strip "
            f"below it. The state medians use only sites computable in both editions, "
            f"{min(n for _, _, _, n in states)} to {max(n for _, _, _, n in states)} of them per state.",
            "Equal-area conic, standard parallels 29.5N and 45.5N. No boundary file is used: the state "
            "letters sit at the centroid of that state's own landfills."]
    for i, line in enumerate(foot):
        s_.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s_.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s_))
    print(f"  wrote {os.path.abspath(OUT)}  ({len(conus)} mapped, {noff} off-map)")
    print(f"  shortest: " + ", ".join(f"{s} {m1:.0f}" for m1, m0, s, n in states[:5]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
