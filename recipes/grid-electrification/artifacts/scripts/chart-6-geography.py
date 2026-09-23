#!/usr/bin/env python3
"""California's five grids share one rooftop-solar number and nothing else.

    python3 chart-6-geography.py

Figure 5 found forecast skill falling hardest in the West, and the decliners looked like a
mechanism: CISO, PacifiCorp West, Arizona Public Service and Nevada Power are California,
Oregon, Arizona and Nevada. **Rooftop solar** is the obvious candidate -- it never passes a
meter the operator reads, so it turns recorded demand into a net quantity that is
increasingly weather-driven and increasingly unlike whatever the forecast was built for.

**The geography is real.** Mountain is the only census division with a clearly negative median
skill change at **-0.095**, Pacific is flat at -0.001, and every other division improved --
South Atlantic +0.059, East South Central +0.113. The worsening is a western phenomenon.

**The mechanism is not.** EIA estimates rooftop PV by **state**, and California's five
balancing authorities therefore all carry the same 14.5%. Their skill changes run from
**-0.71 at CISO to -0.00 at Los Angeles**, with BANC, Imperial and Turlock in between. Same
number on the horizontal axis a state-level variable can supply; a 0.71 spread in the outcome.
**A variable that is constant within a state cannot explain variation that large inside one.**

**And California is not the extreme case, it is the tidy one.** Washington's seven authorities
all sit at 0.8% rooftop and span **1.41**, which is 76% of the entire field's range -- though
its two extremes are grids of 0.2 and 0.3 GW, where a single customer moves the number.
Restricted to authorities above 2 GW, California leads: three grids, one state figure, a
spread of 0.71 that is **half the whole field's range**. Florida's four span 0.51, Arizona's
two 0.37.

**And it does not survive the controls either.** Rooftop's correlation with the skill change
is -0.31, falling to **-0.18 without CISO alone**. In a joint model with utility-scale solar,
a West indicator and grid size, it drops to **-0.14**, and to **+0.03** once CISO is removed.
Utility-scale solar holds up better at -0.27 to -0.35 -- but it is state-level too, and
inherits exactly the same objection.

**Which leaves CISO as its own story rather than a regional one.** It is the steepest decline
in the country by a factor of one and a half, one grid in a state whose four other authorities
barely moved.

**The rooftop estimate is a model, not a measurement.** EIA derives small-scale PV from
capacity filings and assumed yields; nobody meters it. A strong relationship here would have
been partly a relationship with EIA's model, which is one more reason the within-state control
matters more than the correlation.
"""
import collections, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geo, plate                                                        # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "6-geography.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
XLO, XHI = -0.82, 1.26
YLO, YHI = -0.004, 0.164
LAB = {"CISO": (-1, 4), "LDWP": (1, 4), "AZPS": (-1, 4), "TEPC": (1, 4), "NEVP": (-1, 4),
       "PSCO": (-1, 4), "FMPP": (-1, 4), "CHPD": (1, 4), "PSEI": (-1, 13), "SC": (1, 4),
       "ERCO": (-1, 13), "TVA": (1, 13)}


def main():
    d = geo.load()
    rows = [r for r in d["rows"] if r.get("dpv_share") is not None]
    by_state = collections.defaultdict(list)
    for r in rows:
        by_state[r["state"]].append(r)
    multi = {k: v for k, v in by_state.items() if len(v) > 1}
    spreads = sorted(((max(x["d_skill"] for x in v) - min(x["d_skill"] for x in v), k)
                      for k, v in multi.items()), reverse=True)
    div = collections.defaultdict(list)
    for r in d["rows"]:
        if r["division"]:
            div[r["division"]].append(r["d_skill"])
    worst = min(div, key=lambda k: statistics.median(div[k]))
    best = max(div, key=lambda k: statistics.median(div[k]))

    W, H = 1160, 880
    s = plate.open_svg(
        W, H, "California's five grids share one rooftop-solar number and nothing else",
        subtitle=f"{len(rows)} single-state balancing authorities. Horizontal: the change in "
                 f"forecast skill, 2019 to 2025. Vertical: EIA's estimate of rooftop solar "
                 f"as a share of that state's retail sales.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone explaining a grid's worsening demand forecast by where it is",
        decide="whether rooftop solar accounts for the western decline",
        wrong="grids in the same state move together, so a state-level variable could "
              "carry the explanation")
    s += fr

    AX, AY, AW, AH = 246, y0 + 46, W - 568, 500
    lx = lambda v: AX + AW * (min(max(v, XLO), XHI) - XLO) / (XHI - XLO)
    ay = lambda v: AY + AH - 40 - (AH - 66) * (min(max(v, YLO), YHI) - YLO) / (YHI - YLO)

    for g in (-0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 1.25):
        zero = abs(g) < 1e-9
        s.append(f'<line x1="{lx(g):.1f}" y1="{ay(YHI):.1f}" x2="{lx(g):.1f}" '
                 f'y2="{ay(YLO):.1f}" stroke="{RULE if zero else GRID}" '
                 f'stroke-width="{1.5 if zero else 1}"/>')
        s.append(txt(lx(g), ay(YLO) + 17, f"{g:+.2f}" if not zero else "0", size=9,
                     fill=MUTED, anchor="middle"))
    for v in (0.0, 0.04, 0.08, 0.12, 0.16):
        s.append(f'<line x1="{lx(XLO):.1f}" y1="{ay(v):.1f}" x2="{lx(XHI):.1f}" '
                 f'y2="{ay(v):.1f}" stroke="{GRID}"/>')
        s.append(txt(lx(XLO) - 8, ay(v) + 3, f"{v*100:.0f}%", size=9, fill=MUTED,
                     anchor="end"))
    s += halo(lx(0.005), ay(YHI) + 12, "skill unchanged", size=9.5, fill=INK2,
              weight="700")
    s.append(txt(AX, ay(YLO) + 36, "change in forecast skill, 2019 to 2025  -- left is "
                                   "worse", size=10, fill=INK2))
    s.append(f'<text x="{AX-44}" y="{ay(YLO):.1f}" font-size="10" fill="{INK2}" '
             f'transform="rotate(-90 {AX-44} {ay(YLO):.1f})">'
             f'rooftop solar, share of the STATE\'s retail sales</text>')

    # the rows that make the argument: every state with more than one authority in it
    for sp, st in spreads[:4]:
        g = by_state[st]
        y = ay(g[0]["dpv_share"])
        s.append(f'<line x1="{lx(min(x["d_skill"] for x in g)):.1f}" y1="{y:.1f}" '
                 f'x2="{lx(max(x["d_skill"] for x in g)):.1f}" y2="{y:.1f}" '
                 f'stroke="{RED if st == "CA" else FAINT}" '
                 f'stroke-width="{7 if st == "CA" else 5}" stroke-opacity="0.24"/>')

    for r in sorted(rows, key=lambda x: -x["gw"]):
        ca = r["state"] == "CA"
        col = RED if ca else SLATE
        rad = max(3.4, math.sqrt(max(r["gw"], 0.05)) * 1.5)
        x, y = lx(r["d_skill"]), ay(r["dpv_share"])
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad:.1f}" fill="{col}" '
                 f'fill-opacity="{0.30 if ca else 0.16}" stroke="{col}" '
                 f'stroke-width="{1.9 if ca else 1.3}"/>')
        if r["ba"] in LAB:
            sx_, dy = LAB[r["ba"]]
            s += halo(x + sx_ * (rad + 5), y + dy, r["ba"], size=9.5, fill=col,
                      anchor="start" if sx_ > 0 else "end", weight="700")

    ca = by_state["CA"]
    fld = (max(x["d_skill"] for x in rows) - min(x["d_skill"] for x in rows))
    caspr = max(x["d_skill"] for x in ca) - min(x["d_skill"] for x in ca)
    # The callout goes in the empty upper right: no state has both high rooftop and an
    # improving forecast, so nothing is covered there.
    for v, body, wt in (
            (0.158, f"{len(ca)} California authorities, one state figure of "
                    f"{ca[0]['dpv_share']:.1%}", "700"),
            (0.148, f"outcomes {min(x['d_skill'] for x in ca):+.2f} to "
                    f"{max(x['d_skill'] for x in ca):+.2f}: a spread of {caspr:.2f}, "
                    f"{caspr/fld:.0%} of this chart", "700"),
            (0.136, "a variable that is constant inside a state", "normal"),
            (0.126, "cannot explain a spread that big inside one", "normal"),
            (0.108, "every horizontal row is one state, and any", "normal"),
            (0.098, "state-level predictor can only draw a line", "normal")):
        s.append(txt(lx(0.13), ay(v), body, size=9.5, fill=RED, weight=wt))

    TX, ty = W - 238, AY + 26
    for head, body, col in (
            ("the geography is real", f"{worst} is the only census division with a clearly "
                                      f"negative median skill change, at "
                                      f"{statistics.median(div[worst]):+.3f}. "
                                      f"{best} is {statistics.median(div[best]):+.3f}.",
             INK),
            ("the mechanism is not", "Rooftop correlates at -0.31 with the skill change, "
                                     "-0.18 without CISO alone, and -0.14 in a joint model "
                                     "with utility solar, a West indicator and size.", RED),
            ("the horizontal rows", "Each is one state's authorities sharing its single "
                                    "estimate. Any state-level predictor can only ever "
                                    "place them in a line. Washington's span is wider "
                                    "still, on two grids under 0.3 GW.", MUTED),
            ("what is left", "CISO is the steepest decline in the country by half again, "
                             "in a state whose four other authorities barely moved. Its own "
                             "story, not a regional one.", INK2)):
        s.append(txt(TX, ty, head, size=10.5, fill=col, weight="700"))
        ty += 15
        w = wrap(TX, ty, body, size=9.5, fill=MUTED, chars=33, leading=12.5)
        s += w
        ty += 12.5 * len(w) + 16

    foot = (
        "Skill from EIA's Hourly Electric Grid Monitor (EBA); rooftop solar from EIA ELEC, "
        "ELEC.GEN.DPV-{state}, against ELEC.SALES. Both fetched 2026-09-23, no key. CAVEAT: "
        "small-scale PV is MODELLED by EIA from capacity filings and assumed yields -- "
        "nobody meters it -- and it is published per state, not per balancing authority. "
        "Multi-state RTOs carry no state value and are not drawn.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    {len(rows)} single-state authorities; {len(multi)} states hold more than one")
    for sp, st in spreads[:4]:
        g = by_state[st]
        print(f"      {st}  {len(g)} grids at {g[0]['dpv_share']:.1%} rooftop, skill change "
              f"{min(x['d_skill'] for x in g):+.2f} to {max(x['d_skill'] for x in g):+.2f} "
              f"(spread {sp:.2f})")
    print(f"    worst division {worst} {statistics.median(div[worst]):+.3f}; "
          f"best {best} {statistics.median(div[best]):+.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
