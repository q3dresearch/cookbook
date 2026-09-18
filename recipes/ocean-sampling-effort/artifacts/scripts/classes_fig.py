#!/usr/bin/env python3
"""Sea cucumbers live a kilometre down. Squid live in the Falkland Islands.

    python3 chart-6-classes.py

`statistics/env` takes a taxon filter, so the recorded depth and temperature distribution of
any animal class comes back directly. Sixteen classes, ordered by where in the water column
they were found.

**Some of it is the animals.** Sea cucumbers are the deepest class in the register by a wide
margin — a quarter of their records are below 1,000 m and their 75th percentile is 4,000 —
which is what you would expect of a group that dominates abyssal sediment. Corals and anemones
are the odd one out on both axes at once: 13.6% of their records are below a kilometre *and*
40% come from water above 25°C, which is two separate groups of animals sharing a class, reef
corals in the warm shallows and deep-sea corals on seamounts. Marine mammals have 22% of their
records in water below 0°C, more than any other class, because the ice edge is where the seals
and the baleen whales are.

**Some of it is one boat.** Squid and octopus look like the strangest class in the file: a
depth band of 130 to 200 m when everything else medians between 10 and 40, and **83% of records
from 5°C water**. They are not. **80% of all cephalopod records in OBIS come from a single
dataset** — three decades of trawl surveys around the Falkland Islands. The niche is a study
area.

**The test that separates them is the one figure 5 built.** A class whose largest dataset holds
a normal share, 13-27%, is describing itself. A class at 80% is describing a project. Sea
urchins at 55% and sea stars at 43% sit in between and are drawn with that said on the face of
the figure.

**A taxonomy trap, recorded because it nearly went in.** Reptilia returns 28.2M records against
Aves' 27.5M, and its top three datasets are European Seabirds At Sea and two herring gull
tracking studies. OBIS follows modern phylogeny, in which birds sit inside Reptilia. The two are
not disjoint classes and putting both on one axis would have double-counted seabirds and
labelled them reptiles. Reptilia is excluded.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "classes.svg")
RED, AMBER, GREEN, BLUE, DEEP, WARM = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#243b53", "#b0563a"


def pct(bins, key, q):
    tot = sum(r["records"] for r in bins)
    run = 0
    for r in bins:
        run += r["records"]
        if run >= tot * q:
            return r[key]
    return bins[-1][key] if bins else 0


def main():
    d = json.load(open(os.path.join(HERE, "..", "data", "classes.json")))
    rows = []
    for k, v in d.items():
        b = v["depth"]
        if not b:
            continue
        tot = sum(r["records"] for r in b)
        rows.append({"k": k, **v, "p25": pct(b, "from", .25), "med": pct(b, "from", .5),
                     "p75": pct(b, "from", .75), "p95": pct(b, "from", .95),
                     "deep": sum(r["records"] for r in b if r["from"] >= 1000) / tot})
    rows.sort(key=lambda r: (r["med"], r["p75"]))

    W, H = 1200, 1012
    s = plate.open_svg(W, H, "Sea cucumbers live a kilometre down. Squid live in the "
                             "Falkland Islands.")
    fr, _ = plate.frame(W, 62,
                        who="anyone reading a class's recorded range as its ecological niche",
                        decide="whether a class is describing itself or one survey's study area",
                        wrong="a class at 80% one dataset keeps its shape once that dataset is removed")
    s += fr

    AX, AY, AW, AH = 28, 222, 470, 560
    s.append(txt(AX, AY - 44, "where each class was found in the water column",
                 size=12.5, fill=INK, weight="600"))
    s.append(txt(AX, AY - 28, "quartiles and 95th percentile of recorded depth, log scale",
                 size=10.5, fill=MUTED))
    x0 = AX + 172
    px = lambda z: x0 + (AW - 172) * (math.log10(max(z, 1)) / math.log10(8000))
    for z, lab in ((1, "1 m"), (10, "10 m"), (100, "100"), (1000, "1,000"), (8000, "8,000")):
        s.append(f'<line x1="{px(z):.1f}" y1="{AY-4}" x2="{px(z):.1f}" y2="{AY+AH-30:.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(px(z), AY + AH - 14, lab, size=9, fill=MUTED, anchor="middle"))
    rh = (AH - 40) / len(rows)
    for i, r in enumerate(rows):
        y = AY + i * rh + rh / 2
        art = r["top_share"] and r["top_share"] > .5
        col = RED if art else (DEEP if r["deep"] > .1 else BLUE)
        s.append(txt(AX, y - 3, r["common"], size=10.5, fill=INK if not art else RED,
                     weight="600" if art else "normal"))
        s.append(txt(AX, y + 9, r["k"], size=8, fill=MUTED))
        s.append(f'<line x1="{px(max(r["p25"],1)):.1f}" y1="{y:.1f}" '
                 f'x2="{px(r["p95"]):.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="1.4" '
                 f'stroke-opacity="0.45"/>')
        s.append(f'<line x1="{px(max(r["p25"],1)):.1f}" y1="{y:.1f}" '
                 f'x2="{px(r["p75"]):.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="7"/>')
        s.append(f'<circle cx="{px(max(r["med"],1)):.1f}" cy="{y:.1f}" r="4.2" fill="{col}" '
                 f'stroke="#fcfcfb" stroke-width="1.2"/>')
        if r["deep"] > .05:
            s += halo(px(r["p95"]) + 8, y + 4, f"{r['deep']:.0%} below 1 km", size=9, fill=col)
    s += wrap(AX, AY + AH + 4,
              "Thick bar is the middle half of records, thin line runs to the 95th percentile, "
              "dot is the median. Red is a class whose largest dataset holds more than half of "
              "it — the shape is a study area, not a niche.",
              size=10.5, fill=INK2, chars=78)

    BX, BY, BW_ = 530, 230, 430
    s.append(txt(BX, BY - 52, "and in what water", size=12.5, fill=INK, weight="600"))
    s.append(txt(BX, BY - 36, "each class's records across sea surface temperature, "
                              "coldest-centred first", size=10.5, fill=MUTED))
    # A ridgeline rather than a grid of shaded cells: the shapes differ and a heatmap hides
    # that. Sorted by MEAN temperature, not mode — 14 of the 16 classes peak in the same 10C
    # bin, so a modal ordering would tie almost everything and carry no information.
    sstb = [b["sst"] for b in d["Actinopterygii"]["sst"]]
    def mean_t(r):
        t = sum(x["records"] for x in r["sst"]) or 1
        return sum(x["sst"] * x["records"] for x in r["sst"]) / t
    ridge = sorted(rows, key=mean_t)
    rw = (BW_ - 96) / (len(sstb) - 1)
    RH, STEP = 46, 34
    px2 = lambda i: BX + 96 + i * rw
    for i, r in enumerate(ridge):
        y = BY + i * STEP
        tot = sum(x["records"] for x in r["sst"]) or 1
        vals = [x["records"] / tot for x in r["sst"]]
        mx = max(vals) or 1
        art = r["top_share"] and r["top_share"] > .5
        col = RED if art else (WARM if mean_t(r) > 14 else (DEEP if mean_t(r) < 9 else BLUE))
        pts = [(px2(k), y + RH - RH * (v / mx) * 0.95) for k, v in enumerate(vals)]
        path = (f"M{pts[0][0]:.1f},{y+RH:.1f} "
                + " ".join(f"L{a:.1f},{b:.1f}" for a, b in pts)
                + f" L{pts[-1][0]:.1f},{y+RH:.1f} Z")
        s.append(f'<path d="{path}" fill="{col}" fill-opacity="0.30"/>')
        s.append(f'<path d="{" ".join((("M" if k==0 else "L") + f"{a:.1f},{b:.1f}") for k,(a,b) in enumerate(pts))}" '
                 f'fill="none" stroke="{col}" stroke-width="1.7"/>')
        m = mean_t(r)
        mxp = px2((m + 5) / 5)
        s.append(f'<line x1="{mxp:.1f}" y1="{y+RH-4:.1f}" x2="{mxp:.1f}" y2="{y+RH+3:.1f}" '
                 f'stroke="{col}" stroke-width="1.6"/>')
        s.append(txt(BX + 88, y + RH - 1, r["common"], size=9.5,
                     fill=RED if art else INK2, anchor="end",
                     weight="600" if art else "normal"))
        s += halo(px2(len(sstb) - 1) + 8, y + RH - 1, f"{m:.1f}°", size=9, fill=col)
    base = BY + len(ridge) * STEP + RH
    for k, t in enumerate(sstb):
        s.append(txt(px2(k), base + 4, f"{t}", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(BX + 96, base + 20, "°C at the surface · tick is each class's mean",
                 size=9, fill=MUTED))
    s += wrap(BX, base + 44,
              "Sorted by mean, because 14 of 16 classes peak in the same 10°C bin and a modal "
              "ordering would tie them. The shapes are the point: squid is one spike at 5° — the "
              "Falklands survey — while corals are bimodal, peaking at 10° and again at 25°, "
              "which is deep-sea corals and reef corals in one class. Marine mammals are the "
              "broadest of all and the only class with real weight below 0°.",
              size=10.5, fill=INK2, chars=68)

    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              "OBIS v3 statistics/env with a taxon filter, fetched 2026-09-18. This is where a "
              "class was RECORDED, not where it lives: 88% of all records come from the top 200 m "
              "and a class sampled by divers looks shallow whatever it does. The comparison is "
              "between classes, which largely share those biases, never against the ocean. "
              "Reptilia is excluded because OBIS places Aves inside it — 28.2M against Aves' "
              "27.5M, with seabird datasets at the top of both.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for r in rows:
        flag = "  <- one dataset" if r["top_share"] and r["top_share"] > .5 else ""
        print(f"    {r['common']:<22}median {r['med']:>6,} m   p75 {r['p75']:>6,}   "
              f"{r['deep']:>5.1%} below 1km   top ds {(r['top_share'] or 0):>4.0%}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
