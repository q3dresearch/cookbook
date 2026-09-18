#!/usr/bin/env python3
"""Which route is concentrated, which is merely small.

    python3 chart-17-hands.py

One Lorenz curve per management route, 2023. Firms in a route are ranked largest first, and
the curve is the share of **that route's** tonnage held by the largest share of **that route's**
firms — both axes normalised within the category, so routes with 31 firms and 367 firms can be
laid over each other honestly.

**This inverts the answer an earlier version of this figure gave.** That one plotted firm count
against share of *national* tonnage, which measures the average size of a firm in each route
and not how unequally the route is divided. By that reading deep-well injection looked like the
most concentrated thing in the register: thirty-one companies, 666,000 tons each. It is the
opposite. **Deep-well is the most equal route in the file** — Gini 0.63, its largest firm takes
18%, and its largest tenth take 38%. Thirty-one comparable plants, not a monopoly.

**The concentrated ones are the ones with plenty of firms.** Other treatment has seventy-seven
companies and a Gini of 0.98, because one of them — Ascend Performance Materials at Chocolate
Bayou — is 86% of it. Solvents recovery has 242 firms and a Gini of 0.96. Wastewater treatment
has 367 firms, the largest share of the country's waste, and its top tenth hold 95% of it.

**So a count of firms says nothing about concentration, and can point the wrong way.** Scarcity
of participants and inequality among them are separate facts, and this register has a route
that is extreme on one and unremarkable on the other in each direction.
"""
import collections, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brdata, plate                                                     # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "hands.svg")
num = brdata.num
SUF = re.compile(r"\b(LLC|INC|INCORPORATED|CORP|CORPORATION|COMPANY|LTD|PLANT|FACILITY|"
                 r"SITE|WORKS|PLT|DIVISION|THE)\b")
PAL = {"DEEPWELL / UNDERGROUND INJECTION": ("#7a4a8a", "deep-well injection"),
       "WASTEWATER TREATMENT": ("#4a7fa8", "wastewater treatment"),
       "OTHER TREATMENT": ("#8c2318", "other treatment"),
       "LANDFILL": ("#b0563a", "landfill"),
       "INCINERATION": ("#c0562e", "incineration"),
       "METALS RECOVERY": ("#1b7f5a", "metals recovery"),
       "SOLVENTS RECOVERY": ("#5aa17f", "solvents recovery"),
       "OTHER RECOVERY": ("#9ac4a8", "other recovery"),
       "ENERGY RECOVERY": ("#c07a1e", "energy recovery"),
       "FUEL BLENDING": ("#d9a441", "fuel blending"),
       "SLUDGE TRTMNT / STAB / ENCAP": ("#6b6f2e", "sludge treatment")}
DRAW = ["OTHER TREATMENT", "SOLVENTS RECOVERY", "WASTEWATER TREATMENT", "METALS RECOVERY",
        "INCINERATION", "LANDFILL", "ENERGY RECOVERY", "DEEPWELL / UNDERGROUND INJECTION"]


def company(n):
    """handler_id is a gate, not an owner: Clean Harbors holds 21 of them."""
    n = (n or "?").upper().replace(",", " ").replace(".", " ").replace("-", " ")
    n = re.sub(r"\bU\s*S\s+ECOLOGY\b", "US_ECOLOGY", n)
    n = SUF.sub(" ", n)
    n = re.sub(r"[^A-Z0-9_ ]", " ", n)
    t = [x for x in n.split() if x]
    return " ".join(t[:2]) if t else "?"


def gini(v):
    v = sorted(v)
    n, tot = len(v), sum(v)
    return (2 * sum((i + 1) * x for i, x in enumerate(v)) / (n * tot) - (n + 1) / n) if tot else 0


def build():
    cat = collections.defaultdict(collections.Counter)
    top = {}
    for r in brdata.load(2023):
        t = num(r["managed_tons"])
        if t > 0:
            c = (r["management_category"] or "").replace("/ STAG /", "/ STAB /")
            cat[c][company(r["handler_name"])] += t
    out = {}
    for c, fc in cat.items():
        tot = sum(fc.values())
        if tot < 1000:
            continue
        v = sorted(fc.values(), reverse=True)
        n = len(v)
        cum, run = [(0.0, 0.0)], 0.0
        for i, x in enumerate(v):
            run += x
            cum.append(((i + 1) / n, run / tot))
        out[c] = {"curve": cum, "n": n, "tons": tot, "gini": gini(v),
                  "top1": v[0] / tot, "d10": sum(v[:max(1, round(n * .1))]) / tot,
                  "name": max(fc, key=fc.get)}
    return out


def main():
    d = build()
    nat = sum(v["tons"] for v in d.values())
    W, H = 1200, 838
    s = plate.open_svg(W, H, "The route with the fewest firms is the least concentrated of them all")
    fr, _ = plate.frame(W, 62,
                        who="a regulator or entrant asking which route is in the fewest hands",
                        decide="whether a route is a near-monopoly or just a small industry",
                        wrong="a route's Gini falls while its firm count falls too")
    s += fr

    AX, AY, AW, AH = 92, 232, 500, 414
    s.append(txt(AX, AY - 44, "how unequally each route is divided", size=12.5, fill=INK,
                 weight="600"))
    s.append(txt(AX, AY - 28, "share of a route's firms, largest first, against share of its tonnage",
                 size=10.5, fill=MUTED))
    px = lambda v: AX + AW * v
    py = lambda v: AY + AH - AH * v
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        s.append(f'<line x1="{px(v):.1f}" y1="{AY}" x2="{px(v):.1f}" y2="{AY+AH}" stroke="{GRID}"/>')
        s.append(txt(px(v), AY + AH + 17, f"{v:.0%}", size=9.5, fill=MUTED, anchor="middle"))
        s.append(f'<line x1="{AX}" y1="{py(v):.1f}" x2="{AX+AW}" y2="{py(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(AX - 8, py(v) + 4, f"{v:.0%}", size=9.5, fill=MUTED, anchor="end"))
    s.append(f'<line x1="{px(0):.1f}" y1="{py(0):.1f}" x2="{px(1):.1f}" y2="{py(1):.1f}" '
             f'stroke="{FAINT}" stroke-dasharray="4 4"/>')
    s += halo(px(0.66), py(0.62), "every firm equal", size=9.5, fill=MUTED, anchor="middle",
              weight="normal")
    s.append(f'<line x1="{px(0.1):.1f}" y1="{AY}" x2="{px(0.1):.1f}" y2="{AY+AH}" '
             f'stroke="{RULE}"/>')
    s.append(txt(AX, AY + AH + 38, "share of the route's firms, largest first",
                 size=10.5, fill=MUTED))
    s.append(txt(AX - 42, AY - 10, "share of its tonnage", size=10.5, fill=MUTED))
    for c in DRAW:
        if c not in d:
            continue
        col, _ = PAL[c]
        pts = d[c]["curve"]
        path = " ".join(f"{'M' if i == 0 else 'L'}{px(a):.1f},{py(b):.1f}"
                        for i, (a, b) in enumerate(pts))
        s.append(f'<path d="{path}" fill="none" stroke="{col}" stroke-width="2.4"/>')
    # No labels on the curves. Eight of them bunch against the top edge and any annotation
    # there needs leader lines, which are marks that assert nothing. The ranked panel beside
    # the plot carries the same colours in the same order and does the job of a legend.
    for c in DRAW:
        if c in d:
            s.append(f'<circle cx="{px(0.1):.1f}" cy="{py(d[c]["d10"]):.1f}" r="3.4" '
                     f'fill="{PAL[c][0]}"/>')
    s += wrap(AX, AY + AH + 58,
              f"The vertical rule is the largest tenth of a route's firms; the dots are where each "
              f"curve crosses it and the panel beside reads them off. The closer a curve runs to the dashed diagonal, the more evenly the work "
              f"is shared; routes drawn faintly in the panel are omitted here to keep the plot "
              f"legible and are otherwise identical.", size=10.5, fill=INK2, chars=82)

    BX, BY = 636, 232
    s.append(txt(BX, BY - 44, "and the same thing as one number", size=12.5, fill=INK, weight="600"))
    s.append(txt(BX, BY - 10, "Gini of tonnage across a route's firms", size=10.5, fill=MUTED))
    rank = sorted(d.items(), key=lambda x: -x[1]["gini"])
    x0, x1 = BX + 240, BX + 452
    for v in (0, 0.5, 1.0):
        s.append(f'<line x1="{x0+(x1-x0)*v:.1f}" y1="{BY-6}" x2="{x0+(x1-x0)*v:.1f}" '
                 f'y2="{BY+len(rank)*34-14:.1f}" stroke="{GRID}"/>')
        s.append(txt(x0 + (x1 - x0) * v, BY + len(rank) * 34 + 2, f"{v:.1f}", size=9.5,
                     fill=MUTED, anchor="middle"))
    for i, (c, v) in enumerate(rank):
        col, lab = PAL.get(c, (FAINT, c[:18].title()))
        y = BY + i * 34
        drawn = c in DRAW
        s.append(f'<rect x="{BX}" y="{y-4:.1f}" width="15" height="9" fill="{col}" '
                 f'fill-opacity="{1 if drawn else 0.35}"/>')
        s.append(txt(BX + 22, y + 4, lab, size=10.5, fill=INK2 if drawn else MUTED))
        s.append(txt(BX + 178, y + 4, f"{v['n']}", size=9.5, fill=MUTED, anchor="end"))
        s.append(txt(BX + 226, y + 4, f"{v['d10']:.0%}", size=9.5,
                     fill=col if drawn else MUTED, anchor="end", weight="600"))
        s.append(f'<rect x="{x0}" y="{y-5:.1f}" width="{max((x1-x0)*v["gini"],1):.1f}" height="11" '
                 f'fill="{col}" fill-opacity="{1 if drawn else 0.35}"/>')
        s += halo(x0 + (x1 - x0) * v["gini"] + 7, y + 4, f"{v['gini']:.2f}", size=9.5, fill=col)
    s.append(txt(BX + 178, BY - 10, "firms", size=9, fill=MUTED, anchor="end"))
    s.append(txt(BX + 226, BY - 10, "top 10%", size=9, fill=MUTED, anchor="end"))
    s += wrap(BX, BY + len(rank) * 34 + 22,
              f"Deep-well is last on this list and first on a count of firms. A route can be "
              f"scarce and fairly shared, or crowded and owned by one company: other treatment "
              f"has 77 firms and {d['OTHER TREATMENT']['top1']:.0%} of it is Ascend Performance "
              f"Materials' Chocolate Bayou plant, which with its deep-well tonnage is "
              f"{(d['OTHER TREATMENT']['tons']*d['OTHER TREATMENT']['top1']+0.18*d['DEEPWELL / UNDERGROUND INJECTION']['tons'])/nat:.0%} "
              f"of every ton managed in America.", size=10.5, fill=INK2, chars=62)

    fy = H - 20 - 14 * 3
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              "2023 cycle, managed_tons on GM and WR rows which do not overlap. Both axes are "
              "normalised within the route, so a route with 31 firms and one with 367 are "
              "comparable. handler_id is a facility, not a company: names are normalised to an "
              "owner first, which takes Clean Harbors' 21 sites to one firm. An earlier version of "
              "this figure plotted firm count against share of national tonnage, which measures "
              "average firm size rather than concentration and ranked deep-well first instead of "
              "last. Method and limits in the recipe README.", size=11, fill=MUTED, chars=152, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for c, v in rank:
        print(f"    {PAL.get(c,('',c))[1]:<22}{v['n']:>5} firms  gini {v['gini']:.2f}  "
              f"top1 {v['top1']:>4.0%}  top decile {v['d10']:>4.0%}  {v['tons']/1e6:>6.1f}M")
    return 0


if __name__ == "__main__":
    sys.exit(main())
