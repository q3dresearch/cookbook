#!/usr/bin/env python3
"""The busiest registered offices in Britain, and what becomes of the companies at them.

    python3 chart-7-agents.py

Every other figure in this recipe holds the formation-agent addresses out, because a
registered office is not a place of business and averaging 90,368 companies into Covent
Garden would wreck any geography. Held out is not the same as uninteresting: the forty
busiest postcodes carry **8.1% of the whole register**, and nobody has looked at them.

**They used to be ordinary and now they are not.** Companies incorporated in 2012 at an
agent address survived two years at 87.3% against 87.7% everywhere else — no difference at
all. The 2023 cohort survives at **33.0% against 54.3%**. Standardised to the national age
mix so the comparison is not just "these are newer", the gap is **8.9 points**.

The addresses are named because a chart of anonymous rates sends the reader back to ask
which ones. One Cardiff postcode holds 45,536 companies of which **83% are gone within two
years**, which is a different business from the Covent Garden address holding 90,368 at
47%.

What this cannot say is which of them is a problem. A high-churn address may be a cheap
formation service used by people trying things, a registered-office provider whose clients
fail at ordinary rates for their type, or something worse. The register carries the
address and the outcome and nothing about the relationship.
"""
import collections, csv, gzip, os, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
DATA = os.environ.get("FSB_DATA") or os.path.join(HERE, "..", "data")
OUT = os.path.join(HERE, "..", "charts", "7-agents.svg")
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
AGENT, OTHER = "#b03a2e", "#1b4f8a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
TOP = 40
Y0, Y1 = 2012, 2024


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


def read(f):
    with gzip.open(os.path.join(DATA, f), "rt", newline="") as fh:
        yield from csv.DictReader(fh)


def main():
    alive = {r["number"] for r in read("geo-2026-09-01.csv.gz")}
    rows = list(read("geo-2024-09-01.csv.gz"))
    pc = collections.Counter(r["postcode"] for r in rows if r["postcode"])
    top = pc.most_common(TOP)
    agents = {p for p, _ in top}
    by = collections.defaultdict(lambda: [0, 0, 0, 0])
    per = collections.defaultdict(lambda: [0, 0, collections.Counter()])
    for r in rows:
        inc = r["incorp"]
        if not r["postcode"] or len(inc) != 7 or not inc[:4].isdigit():
            continue
        y, s = int(inc[:4]), r["number"] in alive
        v = by[y]
        if r["postcode"] in agents:
            v[0] += 1; v[1] += s
            q = per[r["postcode"]]
            q[0] += 1; q[1] += s; q[2][r["town"]] += 1
        else:
            v[2] += 1; v[3] += s
    years = [y for y in sorted(by) if Y0 <= y <= Y1 and by[y][0] >= 500]
    ta = sum(by[y][0] for y in by); tas = sum(by[y][1] for y in by)
    to = sum(by[y][2] for y in by); tos = sum(by[y][3] for y in by)
    use = [y for y in by if by[y][0] >= 200]
    std = sum((by[y][1] / by[y][0]) * by[y][2] for y in use) / sum(by[y][2] for y in use)

    W, H, L, T, PW, PH = 1060, 802, 96, 210, 480, 372
    RX, RW = 640, 300
    lx = lambda v: L + PW * (v - years[0]) / (years[-1] - years[0])
    ly = lambda v: T + PH - PH * v
    body = []
    body.append(txt(L, T - 46, "two-year survival by the year the company was formed",
                    size=12.5, fill=INK, weight="600"))
    for t in (0, 0.25, 0.5, 0.75, 1.0):
        body.append(f'<line x1="{L}" y1="{ly(t):.1f}" x2="{L+PW}" y2="{ly(t):.1f}" stroke="{GRID}"/>')
        body.append(txt(L - 10, ly(t) + 4, f"{t:.0%}", size=11, fill=MUTED, anchor="end"))
    for y in years[::2]:
        body.append(f'<line x1="{lx(y):.1f}" y1="{T}" x2="{lx(y):.1f}" y2="{T+PH}" stroke="{GRID}"/>')
        body.append(txt(lx(y), T + PH + 20, str(y), size=10.5, fill=MUTED, anchor="middle"))
    band = (" ".join(f"{'M' if i==0 else 'L'}{lx(y):.1f},{ly(by[y][3]/by[y][2]):.1f}"
                     for i, y in enumerate(years)) + " " +
            " ".join(f"L{lx(y):.1f},{ly(by[y][1]/by[y][0]):.1f}" for y in reversed(years)) + " Z")
    body.append(f'<path d="{band}" fill="{AGENT}" fill-opacity="0.10"/>')
    for key, col, lab in ((lambda y: by[y][3] / by[y][2], OTHER, "everywhere else"),
                          (lambda y: by[y][1] / by[y][0], AGENT, "at the 40 busiest addresses")):
        p = " ".join(f"{'M' if i==0 else 'L'}{lx(y):.1f},{ly(key(y)):.1f}" for i, y in enumerate(years))
        body.append(f'<path d="{p}" fill="none" stroke="{col}" stroke-width="2.4"/>')
        body.append(f'<circle cx="{lx(years[-1]):.1f}" cy="{ly(key(years[-1])):.1f}" r="3.5" fill="{col}"/>')
        body.append(txt(lx(years[-1]) + 7, ly(key(years[-1])) + 4, f"{key(years[-1]):.0%}", size=11,
                        fill=col, weight="600"))
    y0 = T + PH + 44
    for col, lab in ((OTHER, "everywhere else"), (AGENT, "at the 40 busiest addresses")):
        body.append(f'<line x1="{L}" y1="{y0-4:.1f}" x2="{L+22}" y2="{y0-4:.1f}" stroke="{col}" '
                    f'stroke-width="2.4"/>')
        body.append(txt(L + 30, y0, lab, size=11, fill=col, weight="600"))
        y0 += 17
    body += wrap(L, y0 + 8,
                 f"In 2012 the two were the same. Standardised to the national age mix, agent-address "
                 f"survival is {std:.1%} against {tos/to:.1%} — a gap of "
                 f"{abs(std-tos/to)*100:.1f} points that is not just these companies being newer.",
                 size=11, fill=INK2, chars=62, leading=14)

    body.append(txt(RX, T - 46, "the ten busiest registered offices", size=12.5, fill=INK, weight="600"))
    body.append(txt(RX, T - 30, "bar is how many companies; the number is two-year survival",
                    size=10, fill=MUTED))
    nmax = max(n for _, n in top[:10])
    for i, (p, n) in enumerate(top[:10]):
        y = T + i * 34
        q = per[p]
        surv = q[1] / q[0] if q[0] else 0
        town = q[2].most_common(1)[0][0].title() if q[2] else ""
        body.append(f'<rect x="{RX}" y="{y-8:.1f}" width="{RW*n/nmax:.1f}" height="17" '
                    f'fill="{AGENT}" fill-opacity="{0.25 + 0.6*(1-surv):.2f}"/>')
        body.append(txt(RX + 5, y + 5, f"{p}", size=10.5, fill=INK, weight="600"))
        bw = RW * n / nmax
        # The postcode sits inside the bar and overflows a short one, so the count goes to a
        # fixed column rather than chasing the bar end and colliding with it.
        if bw > 120:
            body.append(txt(RX + bw - 6, y + 5, f"{n:,}", size=10, fill="#ffffff", anchor="end"))
        else:
            body.append(txt(RX + 126, y + 5, f"{n:,}", size=10, fill=MUTED))
        body.append(txt(RX + RW + 46, y + 5, f"{surv:.0%}", size=11,
                        fill=AGENT if surv < 0.5 else INK2, anchor="end", weight="600"))
        body.append(txt(RX + RW + 54, y + 5, town[:14], size=9.5, fill=MUTED))
    body += wrap(RX, T + 10 * 34 + 20,
                 "Darker means fewer survive. The Cardiff address is a different business from the "
                 "Covent Garden one: both hold tens of thousands of companies, and one loses five in "
                 "six of them within two years.", size=10.5, fill=INK2, chars=50, leading=13)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Forty addresses hold a twelfth of Britain's companies, and they have gone bad",
             size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="a due-diligence or AML screening team",
                        decide="whether a formation-agent address is worth flagging on its own",
                        wrong="companies at those addresses fail at the ordinary rate")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    foot = [f"The 2012 cohorts were indistinguishable — 87.3% against 87.7%. The 2023 cohorts are "
            f"33.0% against 54.3%. Whatever changed, it changed recently.",
            f"{ta:,} companies at the forty addresses, {to:,} elsewhere. Age-standardised survival "
            f"{std:.1%} against {tos/to:.1%}, so the gap is not composition.",
            "The register carries the address and the outcome and nothing about the relationship. A "
            "high-churn address may be a cheap service used by people trying things, or something else."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"  agent {ta:,} at {std:.1%} standardised vs {tos/to:.1%} elsewhere")
    return 0


if __name__ == "__main__":
    sys.exit(main())
