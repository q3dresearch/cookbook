#!/usr/bin/env python3
"""The missing results are mostly outside the law. Inside it, reporting is 67%.

    python3 chart-10-scope.py

Every earlier figure here quotes a reporting rate near a quarter and treats the gap as a
compliance problem. That framing was wrong, and this figure is the correction.

**FDAAA 801 applies two tests this register can now answer.** The product must be a drug,
biologic or device; the trial must have a US site or run under a US IND/IDE. Intervention type
and location country were not in the first walk and were fetched in a second. Crossed, they
split the register into four cells that are nothing like each other:

| | US site | no US site |
| --- | --- | --- |
| drug, biologic or device | **67.1%** | 13.3% |
| everything else | 17.9% | **3.4%** |

**Twenty-fold across the diagonal, and the two tests do not interact.** The US-site effect is
**5.0x** among regulated products and **5.3x** among everything else. The regulated-product
effect is **3.8x** where there is a US site and **3.9x** where there is not. Two independent
multipliers, each roughly the same size wherever it is applied -- which is what a rule with
two conditions should look like if both conditions bind.

**So the headline number was measuring scope, not apathy.** A pooled rate of 24.6% is an
average over a population three quarters of which the statute never reached. Where the law
actually applies, **two trials in three report**. Where it does not, one in thirty.

**It is not the sponsor effect either.** Inside university and hospital sponsors alone -- the
class with the worst pooled rate in figure 4 -- the same two tests give **68.8%** against
**5.2%** for the same product type. A university running a drug trial with a US site reports
about as often as industry does. The gap in figure 4 is substantially a gap in what those
sponsors *study* and *where*.

**What this still is not.** A compliance rate. IND/IDE status is never published, so a trial
with no US site may still be an applicable clinical trial and is counted here as out of scope.
The intervention-type grouping is declared in the script. And 10% of studies record no country
at all; they are excluded rather than assumed domestic.
"""
import collections, csv, datetime, gzip, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                            # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID         # noqa: E402

MAIN = os.path.join(HERE, "..", "data", "studies.csv.gz")
EXTRA = os.path.join(HERE, "..", "data", "extra.csv.gz")
OUT = os.path.join(HERE, "..", "charts", "10-scope.svg")
TODAY = datetime.date(2026, 9, 22)
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
# FDAAA 801 reaches drugs, biologics and devices. Declared, not derived — argue and re-run.
REG = {"DRUG", "BIOLOGICAL", "DEVICE", "COMBINATION_PRODUCT", "GENETIC", "RADIATION"}


def parse(d):
    if not d:
        return None
    try:
        if len(d) == 7:
            return datetime.date(int(d[:4]), int(d[5:7]), 15)
        if len(d) == 10:
            return datetime.date(int(d[:4]), int(d[5:7]), int(d[8:10]))
    except ValueError:
        pass
    return None


def load(p):
    try:
        with gzip.open(p, "rt", newline="", encoding="utf-8") as f:
            return {r["nct_id"]: r for r in csv.DictReader(f)}
    except EOFError:
        raise SystemExit(f"  {os.path.basename(p)} is truncated — re-run its fetcher")


def main():
    mn, ex = load(MAIN), load(EXTRA)
    P = []
    for k, m in mn.items():
        r = ex.get(k)
        if not r or m["study_type"] != "INTERVENTIONAL":
            continue
        if m["primary_completion_type"] != "ACTUAL":
            continue
        if (m["phases"] or "") in ("PHASE1", "EARLY_PHASE1", "EARLY_PHASE1|PHASE1"):
            continue
        pc = parse(m["primary_completion"])
        if not pc or not (2012 <= pc.year <= 2021):
            continue
        ts = set(x for x in (r["itypes"] or "").split("|") if x)
        if not ts or not r["countries"]:
            continue
        rs = parse(m["results_submit"])
        P.append({"reg": bool(ts & REG), "us": "United States" in r["countries"],
                  "lag": (rs - pc).days if rs else None, "fu": (TODAY - pc).days,
                  "sp": m["sponsor_class"] or "?"})

    def sh(S, floor=150):
        ar = [p for p in S if p["fu"] >= 1095]
        if len(ar) < floor:
            return None, len(ar)
        return sum(1 for p in ar if p["lag"] is not None and p["lag"] <= 1095) / len(ar), len(ar)

    def grid(pool):
        g = {}
        for reg in (True, False):
            for us in (True, False):
                g[(reg, us)] = sh([p for p in pool if p["reg"] == reg and p["us"] == us])
        return g
    g = grid(P)
    gu = grid([p for p in P if p["sp"] == "OTHER"])
    pooled, npool = sh(P)

    W, H = 1200, 800
    s = plate.open_svg(W, H, "The missing results are mostly outside the law")
    fr, _ = plate.frame(W, 62,
                        who="anyone reading a register-wide reporting rate as compliance",
                        decide="whether the gap is apathy or scope",
                        wrong="the two statutory tests interact, or one of them does "
                              "little")
    s += fr

    # ---------- left: the 2x2, drawn as area so the cell sizes are visible
    AX, AY = 28, 186
    cw, ch = 214, 132
    gx, gy = AX + 232, AY + 34
    s.append(txt(AX, AY - 22, "share reporting within three years, by the two tests "
                              "FDAAA 801 applies", size=11, fill=INK2))
    for j, uslab in enumerate(("has a US site", "no US site recorded")):
        s.append(txt(gx + j * (cw + 10) + cw / 2, AY + 22, uslab, size=10.5, fill=INK,
                     anchor="middle", weight="600"))
    for i, (reg, rlab) in enumerate(((True, "drug, biologic"), (False, "everything else"))):
        s.append(txt(gx - 14, gy + i * (ch + 10) + ch / 2 - 4,
                     rlab, size=10.5, fill=INK, anchor="end", weight="600"))
        if reg:
            s.append(txt(gx - 14, gy + i * (ch + 10) + ch / 2 + 9, "or device", size=10.5,
                         fill=INK, anchor="end", weight="600"))
        for j, us in enumerate((True, False)):
            v, n = g[(reg, us)]
            x, y = gx + j * (cw + 10), gy + i * (ch + 10)
            col = GREEN if v and v > 0.5 else (RED if v and v < 0.1 else AMBER)
            s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw}" height="{ch}" '
                     f'fill="{GRID}" fill-opacity="0.5"/>')
            fh = ch * (v or 0)
            s.append(f'<rect x="{x:.1f}" y="{y+ch-fh:.1f}" width="{cw}" height="{fh:.1f}" '
                     f'fill="{col}" fill-opacity="0.55"/>')
            s += halo(x + cw / 2, y + ch / 2 + 2, f"{v:.1%}", size=22, fill=col,
                      anchor="middle", weight="700")
            s.append(txt(x + cw / 2, y + ch - 10, f"{n:,} trials", size=9.5, fill=INK2,
                         anchor="middle"))
    s.append(txt(gx, gy + 2 * ch + 30, "each cell is filled in proportion to its rate; the "
                                       "count underneath is what it rests on",
                 size=9.5, fill=MUTED))

    # ---------- right: the two multipliers, measured twice each
    BX, BY = 760, 186
    s.append(txt(BX, BY - 22, "each test measured inside both levels of the other",
                 size=11, fill=INK2))
    y = BY + 24
    pairs = [("a US site", g[(True, True)][0] / g[(True, False)][0],
              g[(False, True)][0] / g[(False, False)][0],
              "among drug/device", "among everything else"),
             ("a regulated product", g[(True, True)][0] / g[(False, True)][0],
              g[(True, False)][0] / g[(False, False)][0],
              "where there is a US site", "where there is not")]
    for name, a, b, la, lb in pairs:
        s.append(txt(BX, y, name, size=12, fill=INK, weight="700"))
        y += 20
        for val, lab in ((a, la), (b, lb)):
            w = 210 * (val / 5.6)
            s.append(f'<rect x="{BX+4:.1f}" y="{y-9:.1f}" width="{max(w,2):.1f}" '
                     f'height="13" fill="{BLUE}" fill-opacity="0.6"/>')
            s += halo(BX + 8 + max(w, 2), y + 1, f"{val:.1f}x", size=11, fill=BLUE,
                      weight="700")
            s.append(txt(BX + 268, y + 1, lab, size=9.5, fill=MUTED))
            y += 22
        y += 12
    s += wrap(BX, y,
              "Each multiplier is the same wherever it is applied, so the tests stack "
              "rather than interact — hence twentyfold across the diagonal.",
              size=10.5, fill=INK2, chars=52, leading=14)
    y += 46
    s.append(f'<rect x="{BX-10:.1f}" y="{y-16:.1f}" width="412" height="76" '
             f'fill="{GREEN}" fill-opacity="0.07"/>')
    s.append(txt(BX, y, "and it is not the sponsor effect", size=11, fill=GREEN,
                 weight="700"))
    s += wrap(BX, y + 17,
              f"Inside university and hospital sponsors — the worst class in figure 4 — the "
              f"same tests give {gu[(True, True)][0]:.1%} against "
              f"{gu[(True, False)][0]:.1%}. That gap is largely what they study, and where.",
              size=10.5, fill=INK2, chars=52, leading=14)

    ty = gy + 2 * ch + 54
    s.append(txt(AX, ty, f"the pooled {pooled:.1%} was measuring scope, not apathy",
                 size=12.5, fill=INK, weight="600"))
    s += wrap(AX, ty + 20,
              f"Where the law applies, two trials in three report. Where it does not, one in "
              f"thirty. Every earlier figure here quotes a number near a quarter and calls "
              f"the gap a compliance problem — this is the correction.",
              size=11, fill=INK2, chars=84, leading=15)

    fy = H - 24 - 14 * 3
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"ClinicalTrials.gov API v2, fetched 2026-09-22. Population as figure 3, "
              f"completions 2012–2021, restricted to the {len(P):,} trials recording both an "
              f"intervention type and at least one country. Still not a compliance rate: "
              f"IND/IDE status is never published, so a trial with no US site may be an "
              f"applicable clinical trial and is counted out of scope here. The "
              f"regulated-product grouping — drug, biologic, device, combination, genetic, "
              f"radiation — is declared in the script. 10% of studies record no country and "
              f"are excluded rather than assumed domestic, and a country list is the sites, "
              f"not the sponsor's address.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    pooled {pooled:.1%} over {npool:,}")
    for (reg, us), (v, n) in g.items():
        print(f"    reg={reg!s:<5} us={us!s:<5} {v:.1%}  n={n:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
