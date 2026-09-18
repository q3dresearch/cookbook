#!/usr/bin/env python3
"""The aqueous market is tiny by weight and enormous by customer count.

    python3 chart-15-aqueous.py

The solids study found a standing pool of buried metal and a named list of customers. Asking
the same question of the aqueous stream — the 95% of this register by tonnage — returns almost
nothing, and the reason is the most useful thing in it.

**The answer depends entirely on whether you count tons or firms, and the two point opposite
ways.** 96.4% of aqueous tonnage is managed on the site that made it — but that is **410
generators out of 7,887**, and the top hundred sites hold 99% of it. **7,477 firms, 94.8% of
everyone with aqueous waste, ship every drop of it away** because they have no treatment at
all. The median shipper sends **three tons**.

So the merchant market is 1.7M tons — flat for twenty-two years while total aqueous tonnage
fell from 220M to 48M — spread across nearly eight thousand customers. **It is not a plant
business, it is a collection-route business**, and anyone sizing it off either number alone
gets it wrong in a different direction.

**It is not that water travels shorter distances.** When aqueous waste does ship, 44% of it
crosses a state line, which is in the same band as everything else. The decision is binary and
it is settled before freight is considered: you build the treatment plant, or you do not.

**Deep-well injection looks like a moat and is mostly captive.** Thirty sites inject, the top
three hold 41%, and Texas and Louisiana are 79% of the tonnage — but the names are Valero,
Cornerstone, Rubicon, Chemours, INEOS, Sasol, Oxy, Lyondell. These are chemical plants
injecting their own process water. Only about nine take waste from anyone else, which is the
figure the market chart reports.

**So the opportunity in aqueous is real and the wrong shape.** Not a treatment plant chasing
47 million tons, and not nothing either: a collection business serving thousands of small
generators who will never build their own capacity. What the register cannot see is the route
economics that decide whether serving three tons at a time pays.
"""
import collections, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brdata, plate                                                     # noqa: E402
from plate import (txt, halo, wrap, SURFACE, INK, INK2, MUTED, RULE, GRID,   # noqa: E402
                   FAINT, FONT)

OUT = os.path.join(HERE, "..", "charts", "aqueous.svg")
BLUE, RED, GREEN, AMBER = "#4a7fa8", "#8c2318", "#1b7f5a", "#c07a1e"
num = brdata.num
YEARS = [y for y in brdata.CYCLES if y != 2021]
PH = {100: "aqueous liquid", 200: "organic liquid", 300: "inorganic solid",
      400: "organic solid", 500: "inorganic sludge", 600: "organic sludge",
      0: "lab packs & other", 800: "gas"}


def ph(fc):
    fc = fc or ""
    return PH.get(int(fc[1:]) // 100 * 100) if fc.startswith("W") and fc[1:].isdigit() else None


def build():
    stay = collections.defaultdict(lambda: [0.0, 0.0])
    onsite, shipped = collections.Counter(), collections.Counter()
    for r in brdata.load(2023):
        t = num(r["managed_tons"])
        if t > 0 and (p := ph(r["form_code"])):
            stay[p][0 if r["br_form"] == "GM" else 1] += t
        if (r["form_code"] or "").startswith("W1") and r["br_form"] == "GM":
            m, sh = num(r["managed_tons"]), num(r["shipped_tons"])
            if m > 0:
                onsite[r["handler_id"]] += m
            if sh > 0:
                shipped[r["handler_id"]] += sh
    series = {}
    for y in YEARS:
        on = off = 0.0
        for r in brdata.load(y):
            if not (r["form_code"] or "").startswith("W1"):
                continue
            t = num(r["managed_tons"])
            if t > 0:
                if r["br_form"] == "GM":
                    on += t
                else:
                    off += t
        series[y] = (on + off, off)
    dw, dwname = collections.Counter(), {}
    for r in brdata.load(2023):
        t = num(r["managed_tons"])
        if t > 0 and "DEEPWELL" in r["management_category"] and ph(r["form_code"]) == "aqueous liquid":
            dw[r["handler_id"]] += t
            dwname[r["handler_id"]] = ((r["handler_name"] or "?").split(",")[0][:26].title(),
                                       r["state"])
    allg = set(onsite) | set(shipped)
    counts = (sum(onsite.values()), sum(shipped.values()), len(onsite),
              len(set(shipped)), len(allg))
    med = sorted(shipped.values())[len(shipped) // 2]
    only_ship = len(set(shipped) - set(onsite))
    return stay, series, dw, dwname, counts, med, only_ship


def main():
    stay, series, dw, dwname, counts, med_ship, n_only_ship = build()
    W, H = 1200, 730
    s = plate.open_svg(W, H, "Almost no water leaves the plant. Almost every firm ships all of theirs.")
    fr, _ = plate.frame(W, 62,
                        who="anyone sizing an aqueous waste business, by tonnage or by customer count",
                        decide="whether to build treatment capacity or a collection route",
                        wrong="off-site aqueous tonnage breaks out of its 22-year band")
    s += fr

    AX, AY, AW = 28, 208, 300
    s.append(txt(AX, AY - 42, "97% of what, though", size=12.5, fill=INK, weight="600"))
    s.append(txt(AX, AY - 26, "aqueous waste, 2023, on two bases", size=10.5, fill=MUTED))
    T_on, T_sh, n_on, n_sh, n_all = counts
    bars = [("of the tonnage", T_on / (T_on + T_sh), f"{T_on/1e6:,.1f}M tons stay",
             f"{T_sh/1e6:,.1f}M ships"),
            ("of the generators", n_on / n_all, f"{n_on:,} firms treat",
             f"{n_sh:,} ship something")]
    for i, (lab, f, l_, r_) in enumerate(bars):
        y = AY + i * 78
        s.append(txt(AX, y, lab, size=11, fill=INK, weight="600"))
        s.append(f'<rect x="{AX}" y="{y+8:.1f}" width="{AW}" height="22" fill="{AMBER}"/>')
        s.append(f'<rect x="{AX}" y="{y+8:.1f}" width="{max(AW*f,0.8):.1f}" height="22" '
                 f'fill="{BLUE}"/>')
        if f > 0.12:
            s.append(txt(AX + AW * f / 2, y + 24, f"{f:.0%}", size=11, fill="#ffffff",
                         anchor="middle", weight="700"))
        if 1 - f > 0.12:
            s.append(txt(AX + AW * (1 + f) / 2, y + 24, f"{1-f:.0%}", size=11, fill="#ffffff",
                         anchor="middle", weight="700"))
        s.append(txt(AX, y + 44, l_, size=9.5, fill=BLUE, weight="600"))
        s.append(txt(AX + AW, y + 44, r_, size=9.5, fill=AMBER, anchor="end", weight="600"))
    s.append(txt(AX, AY + 164, "kept on site", size=10, fill=BLUE, weight="700"))
    s.append(txt(AX + AW, AY + 164, "leaves the site", size=10, fill=AMBER, anchor="end",
                 weight="700"))
    s += wrap(AX, AY + 186,
              f"Both true, pointing opposite ways: a hundred plants hold 99% of the tonnage, "
              f"while the median shipper sends {med_ship:,.0f} tons and {n_only_ship/n_all:.0%} "
              f"have no treatment at all.", size=10.5, fill=INK2, chars=50)

    BX, BY, BW_, BH = 380, 208, 330, 240
    s.append(txt(BX, BY - 26, "the merchant slice never grew", size=12.5, fill=INK, weight="600"))
    s.append(txt(BX, BY - 10, "all aqueous tonnage, and the part that goes off-site",
                 size=10.5, fill=MUTED))
    top = max(t for t, _ in series.values())
    cx = lambda y: BX + BW_ * (y - YEARS[0]) / (YEARS[-1] - YEARS[0])
    cy = lambda v: BY + BH - BH * (v / top) ** 0.5
    for v in (0, 10e6, 50e6, 100e6, 200e6):
        s.append(f'<line x1="{BX}" y1="{cy(v):.1f}" x2="{BX+BW_}" y2="{cy(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(BX - 7, cy(v) + 4, f"{v/1e6:.0f}M" if v else "0", size=9.5, fill=MUTED,
                     anchor="end"))
    for idx, col, lab in ((0, MUTED, "all aqueous"), (1, BLUE, "goes off-site")):
        d = " ".join(f"{'M' if i == 0 else 'L'}{cx(y):.1f},{cy(series[y][idx]):.1f}"
                     for i, y in enumerate(YEARS))
        s.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.6"/>')
        s += halo(cx(YEARS[-1]) - 4, cy(series[YEARS[-1]][idx]) - 9,
                  f"{lab} {series[YEARS[-1]][idx]/1e6:,.1f}M", size=10, fill=col, anchor="end")
    for y in (2001, 2011, 2023):
        s.append(txt(cx(y), BY + BH + 16, str(y), size=9.5, fill=MUTED, anchor="middle"))
    s += wrap(BX, BY + BH + 38,
              f"Total fell {series[YEARS[0]][0]/1e6:,.0f}M to "
              f"{series[YEARS[-1]][0]/1e6:,.0f}M; the off-site slice went "
              f"{series[YEARS[0]][1]/1e6:,.2f}M to {series[YEARS[-1]][1]/1e6:,.2f}M — flat "
              f"through all of it. Square-root scale.", size=10.5, fill=INK2, chars=52)

    CX, CY, CW = 790, 208, 250
    s.append(txt(CX, CY - 26, "and injection is captive", size=12.5, fill=INK, weight="600"))
    s.append(txt(CX, CY - 10, "aqueous tonnage injected underground, by site",
                 size=10.5, fill=MUTED))
    tot = sum(dw.values())
    mx = max(dw.values())
    for i, (hid, v) in enumerate(dw.most_common(8)):
        n, st_ = dwname[hid]
        y = CY + i * 29
        s.append(txt(CX, y, n[:24], size=10, fill=INK2))
        s.append(txt(CX + CW, y, st_, size=10, fill=MUTED, anchor="end"))
        s.append(f'<rect x="{CX}" y="{y+4:.1f}" width="{max(CW*v/mx,0.8):.1f}" height="8" '
                 f'fill="{AMBER}"/>')
        s += halo(CX + CW * v / mx + 6, y + 12, f"{v/1e6:,.2f}M", size=9, fill=AMBER)
    s += wrap(CX, CY + 8 * 29 + 16,
              f"{len(dw)} sites inject, top three {sum(v for _, v in dw.most_common(3))/tot:.0%}, "
              f"Texas and Louisiana 79%. They are chemical plants injecting their own process "
              f"water — only about nine take waste from anyone else.",
              size=10.5, fill=INK2, chars=44)

    s += wrap(28, 600,
              "So it is a collection-route business, not a plant business: 1.7M tons spread over "
              "nearly eight thousand customers at a median of three tons each. The tonnage is "
              "captive and the customers are not, and which of those two facts you size the "
              "opportunity on decides what you build.",
              size=13, fill=INK, chars=132, leading=17)
    fy = H - 20 - 14 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              "Both bases are the generator's own GM rows: managed_tons is what it treats on "
              "site, shipped_tons what it sends away, and no row carries both. The merchant series "
              "counts receipts at the far end, hence 1.37M against 1.7M shipped. 2021 publishes no "
              "tonnage. Method in the recipe.",
              size=11, fill=MUTED, chars=152, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    T_on, T_sh, n_on, n_sh, n_all = counts
    print(f"    tonnage on-site {T_on/(T_on+T_sh):>6.1%}   generators treating on-site "
          f"{n_on/n_all:>6.1%} ({n_on:,} of {n_all:,})")
    print(f"    median shipper sends {med_ship:,.1f} t; {n_only_ship:,} firms ship everything")
    return 0


if __name__ == "__main__":
    sys.exit(main())
