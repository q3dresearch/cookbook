#!/usr/bin/env python3
"""Where Norway's licensed sites actually went: deleted, not added.

    python chart-consolidation.py <licences.csv>

Between 2006 and 2025 Norway cleared 1,104 new aquaculture sites and deleted
2,462. The licensed site count fell by 1,358 — more sites were struck off the
register than are on it today. Output rose anyway, because the sites leaving had
a median capacity of 780 tonnes and the ones arriving 1,560 rising to 3,600.
This was consolidation, not expansion, and it stopped: from 2016 the two flows
balance and the net turns slightly positive.

Three axes plus colour: year across, the median capacity of the sites moving up,
the number of them as area, and the direction of travel as hue.

WHAT THIS CHART DELIBERATELY DOES NOT SHOW is site lifespan. The register's
earliest clearance is 1991-06-24, so a site deleted in 2006 could be at most 15
years old in this data, one deleted in 2014 at most 23. Median age at deletion
duly climbs from 5.0 to 21.0 years, almost exactly one year per calendar year,
and the observed maximum tracks the truncation ceiling to within a year
(2014: max 23.1, ceiling 23.0). That is the register filling up, not sites
living longer. Left truncation, same trap as an unadjusted survival rate.

Capacity for sites still active is as recorded today, not at clearance. Sites
gain capacity over their life, so older clearance cohorts are flattered — which
makes the rising trend in cleared capacity a conservative reading, not an
inflated one.
"""
from __future__ import annotations

import collections
import csv
import statistics
import sys
from pathlib import Path

RECIPE = Path(__file__).resolve().parents[2]
OUT = RECIPE / "artifacts" / "charts" / "consolidation.svg"

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880"
RULE, GRID = "#e3e2db", "#efeee8"
IN_, OUT_ = "#2361b0", "#b5651d"          # OKLab dE 28.2 normal, 23.2 protanope
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'

Y0, Y1 = 2006, 2025                        # 2026 is a part year; the register
                                           # before 2006 is digitisation backfill
CAP_MAX = 4000.0


def tonnes(r) -> float | None:
    """Capacity only where the licence states tonnes. See chart-constraint.py:
    the same field also carries STK (fish counts) and DA (dekar)."""
    if (r.get("capacity_unit") or "").strip().upper() != "TN":
        return None
    try:
        v = float(r["capacity"])
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
    if not rows or "withdrawn" not in rows[0]:
        print("licences.csv must carry cleared/withdrawn dates", file=sys.stderr)
        return 1

    added, removed = collections.defaultdict(list), collections.defaultdict(list)
    for r in rows:
        c = tonnes(r)
        if r["cleared"]:
            added[r["cleared"][:4]].append(c)
        if r["state"] == "deleted" and r["withdrawn"]:
            removed[r["withdrawn"][:4]].append(c)

    pts = []                               # (year, series, n, median capacity)
    for y in range(Y0, Y1 + 1):
        for series, src in (("in", added), ("out", removed)):
            g = src.get(str(y), [])
            caps = [c for c in g if c]
            if not g or not caps:
                continue
            pts.append((y, series, len(g), statistics.median(caps)))

    n_in = sum(p[2] for p in pts if p[1] == "in")
    n_out = sum(p[2] for p in pts if p[1] == "out")
    nmax = max(p[2] for p in pts)

    W, L, R, T, PH = 1040, 76, 210, 200, 372
    H = T + PH + 214
    span = Y1 - Y0

    # PAD keeps the final year clear of the legend rail, so a centred endpoint
    # label has room without covering Y1-1 (the years are only ~40px apart).
    PAD = 78

    def sx(y):
        return L + (y - Y0) / span * (W - L - R - PAD)

    def sy(v):
        return T + PH - min(v, CAP_MAX) / CAP_MAX * PH

    def sr(n):
        return 4.0 + (n / nmax) ** 0.5 * 15.0   # area-proportional, floor for legibility

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family=\'{FONT}\'>',
         f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    o.append(f'<text x="36" y="42" font-size="20" font-weight="600" fill="{INK}">'
             f'Norway grew salmon by deleting sites, not adding them</text>')
    o.append(f'<text x="36" y="68" font-size="13.5" fill="{INK2}">'
             f'Every licensed site entering or leaving the register, {Y0}&#8211;{Y1}. '
             f'Height is the median capacity of the sites moving that year;</text>')
    o.append(f'<text x="36" y="87" font-size="13.5" fill="{INK2}">'
             f'area is how many. {n_out:,} sites were struck off against {n_in:,} '
             f'cleared &#8212; a net loss of {n_out-n_in:,} sites.</text>')
    o.append(f'<text x="36" y="112" font-size="12" fill="{MUTED}">'
             f'The ones leaving were small and the ones arriving were not, so capacity '
             f'rose while the site count fell. After 2016 both flows go quiet.</text>')

    for v in range(0, int(CAP_MAX) + 1, 1000):
        y = sy(v)
        o.append(f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" stroke="{GRID}"/>')
        o.append(f'<text x="{L-12}" y="{y+4:.1f}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="end">{v:,}</text>')
    o.append(f'<text x="{L-12}" y="{sy(CAP_MAX)-16:.0f}" font-size="11" fill="{MUTED}" '
             f'text-anchor="end">tonnes</text>')
    for y in range(Y0, Y1 + 1):
        if y % 2:
            continue
        o.append(f'<text x="{sx(y):.1f}" y="{T+PH+24}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="middle">{y}</text>')

    for series, col in (("in", IN_), ("out", OUT_)):
        ln = [(sx(y), sy(c)) for y, s, n, c in pts if s == series]
        o.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in ln) +
                 f'" fill="none" stroke="{col}" stroke-width="1.5" stroke-opacity="0.35"/>')
    for y, series, n, c in sorted(pts, key=lambda p: -p[2]):
        col = IN_ if series == "in" else OUT_
        o.append(f'<circle cx="{sx(y):.1f}" cy="{sy(c):.1f}" r="{sr(n):.1f}" '
                 f'fill="{col}" fill-opacity="0.5" stroke="{col}" stroke-width="1.5"/>')

    # Direct-label only the extremes; every other count is read off the area.
    for y, series, n, c in pts:
        lab = None
        if series == "out" and n == max(p[2] for p in pts if p[1] == "out"):
            lab = f"{n} deleted in {y}"
            o.append(f'<text x="{sx(y):.1f}" y="{sy(c)+sr(n)+18:.1f}" font-size="11.5" '
                     f'fill="{INK2}" text-anchor="middle">{lab}</text>')
        elif y == Y1:
            # Above for the upper series, below for the lower one. Sideways would
            # cover Y1-1, which sits only 40px away.
            lab = f"{n} deleted" if series == "out" else f"{n} cleared"
            dy = sr(n) + 18 if series == "out" else -sr(n) - 10
            o.append(f'<text x="{sx(y):.1f}" y="{sy(c)+dy:.1f}" font-size="11.5" '
                     f'fill="{INK2}" text-anchor="middle">{lab}</text>')

    lx, ly = W - R + 16, T + 176
    for i, (lab, col) in enumerate((("Cleared in", IN_), ("Deleted out", OUT_))):
        o.append(f'<circle cx="{lx+9}" cy="{ly+i*26-4}" r="7" fill="{col}" '
                 f'fill-opacity="0.5" stroke="{col}" stroke-width="1.5"/>')
        o.append(f'<text x="{lx+26}" y="{ly+i*26}" font-size="12.5" fill="{INK}">{lab}</text>')
    o.append(f'<text x="{lx}" y="{ly+72}" font-size="11" fill="{MUTED}">Area = sites</text>')
    for i, n in enumerate((25, 100, 372)):
        cy = ly + 100 + i * 34
        o.append(f'<circle cx="{lx+30}" cy="{cy}" r="{sr(n):.1f}" fill="none" '
                 f'stroke="{MUTED}" stroke-width="1.2"/>')
        o.append(f'<text x="{lx+68}" y="{cy+4}" font-size="11" fill="{MUTED}">{n}</text>')

    yb = T + PH + 52
    o.append(f'<line x1="36" y1="{yb-16}" x2="{W-36}" y2="{yb-16}" stroke="{RULE}"/>')
    o.append(f'<text x="36" y="{yb+6}" font-size="13" fill="{INK}">'
             f'<tspan font-weight="600">The register shed {n_out-n_in:,} net sites while '
             f'national output rose.</tspan> Capacity came from replacing 780-tonne sites '
             f'with 3,000-tonne ones,</text>')
    o.append(f'<text x="36" y="{yb+26}" font-size="13" fill="{INK}">'
             f'not from opening ground. That lever is spent: the deletion flow has fallen '
             f'from 372 sites a year to 19.</text>')
    o.append(f'<text x="36" y="{yb+54}" font-size="11.5" fill="{MUTED}">'
             f'Read with constraint.svg. Consolidation explains how output grew without new '
             f'sites; the idle 37% explains why the queue is not what binds growth now.</text>')
    o.append(f'<text x="36" y="{yb+76}" font-size="11.5" fill="{MUTED}">'
             f'No lifespan is plotted, deliberately. The register starts 1991-06-24, so age '
             f'at deletion is left-truncated: it rises 5.0 to 21.0 years at almost exactly '
             f'one year per calendar year and the</text>')
    o.append(f'<text x="36" y="{yb+94}" font-size="11.5" fill="{MUTED}">'
             f'observed maximum tracks the truncation ceiling. Sites are not living longer; '
             f'the register is filling up. Capacity of active sites is as recorded today, '
             f'not at clearance.</text>')
    o.append(f'<text x="36" y="{yb+118}" font-size="11.5" fill="{MUTED}">'
             f'Years before {Y0} are register digitisation, not clearances (604 dated 2001 '
             f'alone) and are excluded. Source: Fiskeridirektoratet Akvakulturregisteret, '
             f'layers 0 and 1, paged.</text>')
    o.append("</svg>")
    OUT.write_text("\n".join(o))
    print(f"  {OUT.name}")
    print(f"    cleared in {n_in:,} | deleted out {n_out:,} | net {n_in-n_out:+,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
