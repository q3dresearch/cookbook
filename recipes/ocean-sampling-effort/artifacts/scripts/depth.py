#!/usr/bin/env python3
"""What we know about ocean life, we know about the top two hundred metres.

    python3 chart-2-depth.py

118 million OBIS records carry a depth. **88.0% of them are from the top 200 metres**, 37.4%
from the top ten, and 2.99% from below a thousand.

**The mean depth of the ocean is about 3,700 metres.** The median record comes from nine.
Below four thousand metres — which is most of the sea floor — there are 701,449 records, 0.59%
of the total, describing a majority of the habitable volume on this planet.

| depth | records | share |
| --- | --- | --- |
| 0–10 m | 44,274,791 | **37.4%** |
| 10–200 m | 59,757,400 | 50.6% |
| 200–1,000 m | 10,658,632 | 9.0% |
| 1,000–4,000 m | 2,835,524 | 2.4% |
| below 4,000 m | 701,449 | **0.59%** |
| below 6,000 m | 41,302 | 0.03% |

**This is not a criticism of anyone.** Reaching 4,000 metres needs a ship, a winch and a week;
reaching ten metres needs a snorkel. The distribution is what oceanography costs. It matters
because the same records are used to say where life is, and a map built from a snorkel will
always find the most life at snorkel depth.

**Temperature carries the same signature.** The record peaks at 10°C, and the bins spanning
5 to 20°C — temperate and subpolar water, which is where the research fleets are based — hold
64.2% of everything. Water above 25°C holds 15.6%, and the warmest bin holds 7,573 records in
a register of 229 million.

**What this cannot say.** OBIS reports the depth a record was taken at, not the depth of the
sea beneath it, so a shallow record over an abyssal plain counts as shallow. And 111 million
records carry no depth at all and are excluded entirely, which is 48% of the register.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import obis, plate                                                       # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "depth.svg")
RED, AMBER, GREEN, BLUE, DEEP = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#243b53"
BANDS = [(0, 10, "0-10 m"), (10, 50, "10-50"), (50, 200, "50-200"), (200, 1000, "200-1,000"),
         (1000, 4000, "1,000-4,000"), (4000, 11000, "below 4,000")]


def main():
    env = obis.load("env.json")
    st = obis.load("statistics.json")
    d = env["depth"]
    tot = sum(r["records"] for r in d)
    sst = env["sst"]
    tsst = sum(r["records"] for r in sst)
    run, med = 0, None
    for r in d:
        run += r["records"]
        if med is None and run >= tot / 2:
            med = r["from"]

    W, H = 1200, 800
    s = plate.open_svg(W, H, "What we know about ocean life, we know about the top two "
                             "hundred metres")
    fr, _ = plate.frame(W, 62,
                        who="anyone reading a marine distribution map as a map of the ocean",
                        decide="whether a species is absent from the deep or absent from the record",
                        wrong="the share of records below 1,000 m rises materially in a later fetch")
    s += fr

    AX, AY, AW, AH = 28, 218, 300, 400
    s.append(txt(AX, AY - 44, "every record, by the depth it came from", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(AX, AY - 28, "log depth; bar length is share of records", size=10.5, fill=MUTED))
    dy = lambda z: AY + AH * (math.log10(max(z, 1)) / math.log10(11000))
    for z, lab in ((1, "1 m"), (10, "10"), (100, "100"), (1000, "1,000"), (10000, "10,000")):
        s.append(f'<line x1="{AX+62}" y1="{dy(z):.1f}" x2="{AX+AW}" y2="{dy(z):.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(AX + 56, dy(z) + 4, lab, size=9, fill=MUTED, anchor="end"))
    mx = max(r["records"] for r in d)
    for r in d:
        z0 = max(r["from"], 1)
        nxt = [x["from"] for x in d if x["from"] > r["from"]]
        z1 = nxt[0] if nxt else 11000
        y0, y1 = dy(z0), dy(z1)
        w = (AW - 70) * (r["records"] / mx) ** 0.4
        col = BLUE if r["from"] < 200 else (AMBER if r["from"] < 1000 else DEEP)
        s.append(f'<rect x="{AX+62}" y="{y0:.1f}" width="{max(w,0.8):.1f}" '
                 f'height="{max(y1-y0-0.6,1.2):.1f}" fill="{col}"/>')
    s.append(f'<line x1="{AX+56}" y1="{dy(200):.1f}" x2="{AX+AW}" y2="{dy(200):.1f}" '
             f'stroke="{RED}" stroke-dasharray="4 3"/>')
    s += halo(AX + AW, dy(200) - 6, "200 m — 88% of records above here", size=9.5, fill=RED,
              anchor="end")
    s.append(f'<line x1="{AX+56}" y1="{dy(3700):.1f}" x2="{AX+AW}" y2="{dy(3700):.1f}" '
             f'stroke="{GREEN}" stroke-dasharray="4 3"/>')
    s += halo(AX + AW, dy(3700) - 6, "3,700 m — the ocean's mean depth", size=9.5, fill=GREEN,
              anchor="end")
    s += wrap(AX, AY + AH + 26,
              f"The median record comes from {med} metres. The median cubic metre of ocean is "
              f"nearer four thousand. Bar length is a fourth-root scale or the deep bars vanish.",
              size=10.5, fill=INK2, chars=50)

    BX, BY, BW_ = 376, 218, 380
    s.append(txt(BX, BY - 44, "and the deep is almost absent", size=12.5, fill=INK, weight="600"))
    s.append(txt(BX, BY - 28, "share of the 118 million records carrying a depth",
                 size=10.5, fill=MUTED))
    for i, (lo, hi, lab) in enumerate(BANDS):
        n = sum(r["records"] for r in d if lo <= r["from"] < hi)
        y = BY + i * 58
        sh = n / tot
        col = BLUE if lo < 200 else (AMBER if lo < 1000 else DEEP)
        s.append(txt(BX, y, lab, size=11, fill=INK))
        s.append(txt(BX + BW_, y, f"{n:,}", size=9, fill=MUTED, anchor="end"))
        s.append(f'<rect x="{BX}" y="{y+8:.1f}" width="{BW_}" height="22" fill="{GRID}"/>')
        s.append(f'<rect x="{BX}" y="{y+8:.1f}" width="{max(BW_*sh,1.5):.1f}" height="22" '
                 f'fill="{col}"/>')
        s += halo(BX + max(BW_ * sh, 1.5) + 7, y + 24,
                  f"{sh:.1%}" if sh >= .01 else f"{sh:.2%}", size=11, fill=col)
    s += wrap(BX, BY + len(BANDS) * 58 + 4,
              "Reaching four thousand metres needs a ship, a winch and a week; reaching ten needs "
              "a snorkel. This is what oceanography costs, not a failing — but the same records "
              "are read as a map of where life is, and a map built from a snorkel finds the most "
              "life at snorkel depth.", size=10.5, fill=INK2, chars=64)

    CX, CY, CW, CH = 800, 218, 370, 250
    s.append(txt(CX, CY - 44, "temperature says it too", size=12.5, fill=INK, weight="600"))
    s.append(txt(CX, CY - 28, "records by sea surface temperature", size=10.5, fill=MUTED))
    mxs = max(r["records"] for r in sst)
    bw = CW / len(sst)
    for i, r in enumerate(sst):
        h = (CH - 30) * r["records"] / mxs
        col = BLUE if r["sst"] < 20 else AMBER
        s.append(f'<rect x="{CX+i*bw:.1f}" y="{CY+CH-30-h:.1f}" width="{bw*0.74:.1f}" '
                 f'height="{max(h,1):.1f}" fill="{col}"/>')
        s.append(txt(CX + i * bw + bw * .37, CY + CH - 14, f"{r['sst']}", size=9, fill=MUTED,
                     anchor="middle"))
        if r["records"] / tsst > .03:
            s += halo(CX + i * bw + bw * .37, CY + CH - 36 - h, f"{r['records']/tsst:.0%}",
                      size=9, fill=col, anchor="middle")
    s.append(txt(CX, CY + CH, "°C", size=9, fill=MUTED))
    warm = sum(r["records"] for r in sst if r["sst"] >= 25) / tsst
    temp = sum(r["records"] for r in sst if 5 <= r["sst"] < 20) / tsst
    s += wrap(CX, CY + CH + 20,
              f"The 5-to-20°C bins — temperate and subpolar water, where the research fleets are "
              f"based — holds {temp:.1%} of everything. Water above 25°C holds {warm:.1%}. The "
              f"warmest bin, above 30°C, holds 7,573 records in a register of 229 million.",
              size=10.5, fill=INK2, chars=58)

    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"OBIS v3 statistics/env, fetched 2026-09-18. {tot:,} records carry a depth of the "
              f"{st['records']:,} in the register, so 48% are excluded entirely. OBIS reports the "
              f"depth a record was taken at and not the depth of sea beneath it, so a surface tow "
              f"over an abyssal plain counts as shallow. The 3,700 m line is the ocean's accepted "
              f"mean depth and is the only number on this figure not from OBIS.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for lo, hi, lab in BANDS:
        n = sum(r["records"] for r in d if lo <= r["from"] < hi)
        print(f"    {lab:<14}{n:>12,}{n/tot:>9.2%}")
    print(f"    median record depth {med} m; {tot:,} of {st['records']:,} carry a depth")
    return 0


if __name__ == "__main__":
    sys.exit(main())
