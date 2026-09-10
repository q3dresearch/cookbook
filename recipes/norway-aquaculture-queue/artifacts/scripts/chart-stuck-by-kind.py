#!/usr/bin/env python3
"""What the queue processes, and what it holds.

    python chart-stuck-by-kind.py <applications.csv>

Four dimensions: how much of each family is still waiting (y), how fast that
family is being resolved relative to what arrives (x), how many applications it
represents (area), and whether granting it would create capacity that did not
exist before (fill).

The split is the finding. Families that modify something already licensed clear —
co-location resolves in a median 80 days with 15% of its applications waiting, and
changes to existing sites are decided faster than they arrive. Families that add
new capacity sit at half to two thirds outstanding.

Clear rate is decisions divided by arrivals since 2025, not a share of a fixed
total, so it can exceed 100%: a family decided faster than it received that year
is working through its own backlog.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import math
import statistics
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from families import adds_capacity, family_of                  # noqa: E402

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "stuck-by-kind.svg"
MIN_N, SINCE = 25, dt.date(2025, 1, 1)

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE, NEWCAP, MODIFY = "#e3e2db", "#a8324a", "#2361b0"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
D = lambda s: dt.date.fromisoformat(s) if s else None          # noqa: E731


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
    today = max(D(r["submitted"]) for r in rows if r["submitted"])

    agg = collections.defaultdict(lambda: {"n": 0, "p": 0, "arr": 0, "dec": 0, "wait": []})
    for r in rows:
        fam = family_of(r["application_type"])
        if not fam:
            continue
        a = agg[fam]
        a["n"] += 1
        s, d = D(r["submitted"]), D(r["decided"])
        if s and s >= SINCE:
            a["arr"] += 1
        if d and d >= SINCE:
            a["dec"] += 1
        if r["layer"] == "pending":
            a["p"] += 1
            if s:
                a["wait"].append((today - s).days)

    pts = []
    for fam, a in agg.items():
        if a["n"] < MIN_N or not a["arr"]:
            continue
        pts.append({"fam": fam, "n": a["n"], "stuck": a["p"] / a["n"],
                    "clear": a["dec"] / a["arr"],
                    "wait": statistics.median(a["wait"]) if a["wait"] else 0,
                    "new": adds_capacity(fam)})
    if not pts:
        print("  nothing to plot")
        return 1

    W, H, L, R, T, B = 1000, 640, 96, 210, 208, 150
    x1 = max(p["clear"] for p in pts) * 1.12
    y1 = max(p["stuck"] for p in pts) * 1.15
    rmax = max(p["n"] for p in pts)

    def sx(v):
        return L + v / x1 * (W - L - R)

    def sy(v):
        return H - B - v / y1 * (H - T - B)

    def rad(n):
        # Small. Area still encodes count, but the bubbles were large enough to
        # overlap each other and swallow their own labels.
        return 6 + 15 * math.sqrt(n / rmax)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'The queue processes modifications and holds new capacity</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Share of each family still waiting, against how fast it is being resolved. '
             f'Area is the number of applications; fill is</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'whether granting it would create capacity that did not exist before.</text>')
    o.append(f'<circle cx="42" cy="116" r="7" fill="{NEWCAP}" fill-opacity="0.34" '
             f'stroke="{NEWCAP}" stroke-width="2"/>')
    o.append(f'<text x="56" y="120" font-size="12.5" fill="{NEWCAP}" font-weight="600">'
             f'creates new capacity</text>')
    o.append(f'<circle cx="242" cy="116" r="7" fill="{MODIFY}" fill-opacity="0.34" '
             f'stroke="{MODIFY}" stroke-width="2"/>')
    o.append(f'<text x="256" y="120" font-size="12.5" fill="{MODIFY}" font-weight="600">'
             f'modifies an existing site</text>')

    o.append(f'<line x1="{sx(1.0):.1f}" y1="{T}" x2="{sx(1.0):.1f}" y2="{H-B}" '
             f'stroke="{MUTED}" stroke-width="1.3" stroke-dasharray="4 3"/>')
    o.append(f'<text x="{sx(1.0)-8:.1f}" y="{T+14}" font-size="11.5" fill="{MUTED}" '
             f'text-anchor="end">keeping up</text>')
    for g in (0.25, 0.5, 0.75, 1.0, 1.25):
        if g > x1:
            continue
        o.append(f'<line x1="{sx(g):.1f}" y1="{T}" x2="{sx(g):.1f}" y2="{H-B}" '
                 f'stroke="{RULE}"/>')
        o.append(f'<text x="{sx(g):.1f}" y="{H-B+21}" font-size="11.5" fill="{MUTED}" '
                 f'text-anchor="middle">{g:.0%}</text>')
    for g in (0.2, 0.4, 0.6):
        if g > y1:
            continue
        o.append(f'<line x1="{L}" y1="{sy(g):.1f}" x2="{W-R}" y2="{sy(g):.1f}" '
                 f'stroke="{RULE}"/>')
        o.append(f'<text x="{L-10}" y="{sy(g)+4:.1f}" font-size="11.5" fill="{MUTED}" '
                 f'text-anchor="end">{g:.0%}</text>')
    o.append(f'<text x="36" y="{T-14}" font-size="11.5" fill="{MUTED}">'
             f'share of that family still waiting</text>')
    o.append(f'<text x="{(L+W-R)/2:.0f}" y="{H-B+42}" font-size="11.5" fill="{MUTED}" '
             f'text-anchor="middle">decisions per application received, since 2025</text>')

    for p in pts:
        p["x"], p["y"] = sx(p["clear"]), sy(p["stuck"])
        p["r"] = rad(p["n"])
        c = NEWCAP if p["new"] else MODIFY
        o.append(f'<circle cx="{p["x"]:.1f}" cy="{p["y"]:.1f}" r="{p["r"]:.1f}" fill="{c}" '
                 f'fill-opacity="0.32" stroke="{c}" stroke-width="2.2"/>')

    # One short label per bubble, nudged apart. The previous version carried the
    # family name AND a count AND a median wait on two lines per marker, which
    # collided into an unreadable stack in the top-left cluster. The numbers live
    # in the README; the chart carries the name and the position.
    # Two markers a few pixels apart cannot both carry a centred label above them:
    # Land-based and New licence sit at nearly the same point, and stacking their
    # labels ran each one's leader line straight through the other's text. So
    # colliding pairs are pushed SIDEWAYS, one left of its bubble and one right,
    # and the leader goes to the near edge of the text rather than its middle.
    lab = sorted(pts, key=lambda p: (p["y"], p["x"]))
    for d in lab:
        d["lx"], d["ly"], d["side"] = d["x"], d["y"] - d["r"] - 10, 0
        d["w"] = len(d["fam"]) * 6.6
    for _ in range(400):
        moved = False
        for i in range(len(lab)):
            for j in range(i + 1, len(lab)):
                a_, b_ = lab[i], lab[j]
                if abs(a_["ly"] - b_["ly"]) >= 16:
                    continue
                gap = abs(a_["lx"] - b_["lx"])
                if gap >= (a_["w"] + b_["w"]) / 2 + 12:
                    continue
                if a_["side"] == 0 and b_["side"] == 0:
                    lo, hi = (a_, b_) if a_["x"] <= b_["x"] else (b_, a_)
                    lo["side"], hi["side"] = -1, 1
                    lo["lx"] = lo["x"] - lo["r"] - 8 - lo["w"] / 2
                    hi["lx"] = hi["x"] + hi["r"] + 8 + hi["w"] / 2
                else:
                    a_["ly"] -= 9
                    b_["ly"] += 9
                moved = True
        if not moved:
            break
    for d in lab:
        c = NEWCAP if d["new"] else MODIFY
        edge = d["lx"] + (d["w"] / 2 if d["side"] < 0 else -d["w"] / 2 if d["side"] > 0 else 0)
        if d["side"] or abs(d["ly"] - (d["y"] - d["r"] - 10)) > 3:
            o.append(f'<line x1="{d["x"] + (-d["r"]-2 if d["side"] < 0 else d["r"]+2 if d["side"] > 0 else 0):.1f}" '
                     f'y1="{d["y"] if d["side"] else d["y"]-d["r"]-2:.1f}" '
                     f'x2="{edge + (4 if d["side"] < 0 else -4 if d["side"] > 0 else 0):.1f}" '
                     f'y2="{d["ly"]-4 if not d["side"] else d["ly"]-4:.1f}" '
                     f'stroke="{c}" stroke-width="0.7"/>')
        o.append(f'<text x="{d["lx"]:.1f}" y="{d["ly"]:.1f}" font-size="12.5" '
                 f'font-weight="600" fill="{INK}" text-anchor="middle">'
                 f'{escape(d["fam"])}</text>')

    yb = H - 74
    new = [p for p in pts if p["new"]]
    mod = [p for p in pts if not p["new"]]
    o.append(f'<line x1="36" y1="{yb-16}" x2="{W-36}" y2="{yb-16}" stroke="{RULE}"/>')
    if new and mod:
        o.append(f'<text x="36" y="{yb+6}" font-size="13" fill="{INK}">'
                 f'<tspan font-weight="600">New capacity averages '
                 f'{statistics.mean([p["stuck"] for p in new]):.0%} outstanding; '
                 f'modifications {statistics.mean([p["stuck"] for p in mod]):.0%}.</tspan> '
                 f'The two groups do not overlap on either axis.</text>')
    o.append(f'<text x="36" y="{yb+28}" font-size="12.5" fill="{INK2}">'
             f'Land-based is the most outstanding family of all at 62%, having previously been '
             f'described in this recipe as close to automatic.</text>')
    o.append(f'<text x="36" y="{H-13}" font-size="11.5" fill="{MUTED}">'
             f'Clear rate is decisions over arrivals since 2025 and can exceed 100% when a '
             f'family is working through its own backlog. Families under {MIN_N} applications '
             f'omitted.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name} — {len(pts)} families")
    for p in sorted(pts, key=lambda p: -p["stuck"]):
        print(f"    {p['fam']:<26}{'new' if p['new'] else 'mod':<5}"
              f"stuck {p['stuck']:>4.0%}  clear {p['clear']:>5.0%}  n={p['n']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
