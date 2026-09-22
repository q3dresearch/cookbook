#!/usr/bin/env python3
"""Option time is authorised in whole years, not negotiated in days.

    python3 chart-16-schedule.py

The register carries a contract's current end date and the furthest end it could reach if
every option were exercised. Differencing them gives a quantity nobody reports: authority
issued but not yet taken. Both dates are present on 99.999% of awards, against 30% for the
money ceiling, which is the only reason these groups can be compared at all.

**16.7% of awards carry some**, and the gaps are not smooth. 35% fall within five days of a
whole year, 10% are exactly 365, and 16% are one month. The histogram is a comb at 365, 730,
1,095 and 1,460 -- option time is authorised in contract units.

**Two thirds of the days sit on contracts currently running 9 to 24 months.** The share
rises to a ridge there and collapses past three years. The collapse is partly mechanical:
99% of potential performance periods end within five years of the start.

**The linear summary is the wrong summary.** Point-biserial r between log duration and
carrying any gap is -0.02 on 493,763 awards -- a near-null that describes a ridge as nothing.
The size of a gap does track duration, at +0.48.

**Who carries it, and what fails to explain it, is figure 17.** This plate was one canvas with
four panels until a reader said it was too loaded; two panels is the ceiling here.

**What this cannot show.** Current duration is measured after exercise, so a long current
term may be a long base period or a short one whose options were taken. The duration panel
drops the 10.9% of awards whose recorded start falls after their own current end, and those
carry a gap less often (11.6% against 17.4%), so its levels sit about 0.6 points high.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate, sched                                                      # noqa: E402
from sched import load_year, nlines, step, CAP, SHORT, ATYPE             # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402
RED, AMBER, GREEN, BLUE, PLUM = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#6b4a80"

OUT = os.path.join(HERE, "..", "charts", "16-schedule.svg")


def main():
    a = load_year("2016")
    b = load_year("2015")

    W, H = 1240, 850
    s = plate.open_svg(
        W, H,
        "Option time is authorised in whole years, and two thirds of the days sit on "
        "contracts of 9 to 24 months",
        subtitle=f"{a['pos']/a['both']:.1%} of {a['both']:,} civilian FY2016 awards carry "
                 f"some. Both schedule dates are present on {a['both']/a['awards']:.3%} of "
                 f"awards, against 30% for the money ceiling — which is why these groups can "
                 f"be compared at all.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone measuring how much contract is authorised but not yet taken",
        decide="whether to measure unexercised authority in dollars or in schedule days",
        wrong="the ridge at 9 to 24 months is Veterans Affairs composition, or does not "
              "repeat in FY2015")
    s += fr

    # ---------------------------------------------------------------- A: the ridge
    AX, AY, AW, AH = 28, y0 + 46, 600, 296
    lx = lambda d: AX + 58 + (AW - 82) * (math.log10(max(d, 1)) / math.log10(3650))
    ly = lambda f: AY + AH - (AH - 30) * (f / 0.32)
    for f in (0, .08, .16, .24, .32):
        s.append(f'<line x1="{lx(1):.1f}" y1="{ly(f):.1f}" x2="{lx(3650):.1f}" '
                 f'y2="{ly(f):.1f}" stroke="{GRID}"/>')
        s.append(txt(lx(1) - 8, ly(f) + 3, f"{f:.0%}", size=9, fill=MUTED, anchor="end"))
    for d in (1, 7, 30, 90, 365, 730, 1825, 3650):
        s.append(f'<line x1="{lx(d):.1f}" y1="{ly(0):.1f}" x2="{lx(d):.1f}" '
                 f'y2="{ly(0)+4:.1f}" stroke="{MUTED}"/>')
        s.append(txt(lx(d), ly(0) + 16, f"{d:,}", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, AY - 28, "share of awards whose potential end is later than their "
                              "current end", size=11.5, fill=INK2))
    s.append(txt(AX, AY - 13, "against how long the contract currently runs", size=10,
                 fill=MUTED))
    s.append(txt(lx(1), ly(0) + 32, "current period of performance, days (log)", size=10,
                 fill=MUTED))

    # the ridge, named on the page rather than in the caption
    rx1, rx2 = lx(275), lx(731)
    s.append(f'<rect x="{rx1:.1f}" y="{ly(0.32):.1f}" width="{rx2-rx1:.1f}" '
             f'height="{ly(0)-ly(0.32):.1f}" fill="{AMBER}" fill-opacity="0.07"/>')
    s += halo((rx1 + rx2) / 2, ly(0.32) + 12, "9 to 24 months", size=10, fill=AMBER,
              anchor="middle", weight="700")

    pooled = a["pos"] / a["both"]
    s.append(f'<line x1="{lx(1):.1f}" y1="{ly(pooled):.1f}" x2="{lx(3650):.1f}" '
             f'y2="{ly(pooled):.1f}" stroke="{FAINT}" stroke-width="1.1" '
             f'stroke-dasharray="4 4"/>')
    s += halo(lx(3650), ly(pooled) - 6, f"all awards, {pooled:.1%}", size=9.5, fill=MUTED,
              anchor="end")

    for r15 in b["bands"]:
        s.append(f'<circle cx="{lx(max(r15["mdur"],1)):.1f}" cy="{ly(r15["any"]):.1f}" '
                 f'r="3.4" fill="none" stroke="{FAINT}" stroke-width="1.5"/>')
    s += step([(r["lo"], r["hi"], r["any"]) for r in a["bands_nova"]], lx, ly, BLUE, 1.2,
              dash="3 2.4")
    s += step([(r["lo"], r["hi"], r["any"]) for r in a["bands"]], lx, ly, BLUE, 3.4)
    for r, rn in zip(a["bands"], a["bands_nova"]):
        x1, x2 = lx(max(r["lo"], 1)), lx(r["hi"])
        s.append(f'<circle cx="{lx(max(r["mdur"],1)):.1f}" cy="{ly(r["any"]):.1f}" r="3.4" '
                 f'fill="{BLUE}"/>')
        s += halo((x1 + x2) / 2, min(ly(r["any"]), ly(rn["any"])) - 7, f"{r['n']:,}",
                  size=8, fill=MUTED, anchor="middle", weight="400")
    # Both bases, because they disagree: the count base and the day base pick different
    # bands as the biggest, and a plate that names only one of them is misleading.
    tn = sum(r["np"] for r in a["bands"]) or 1
    td = sum(r["nd"] for r in a["bands"]) or 1
    sh, rg = a["bands"][0], a["bands"][4:7]
    for i, line in enumerate((
            f"awards under a month are {sh['np']/tn:.0%} of every",
            f"award with a gap but {sh['nd']/td:.0%} of the days;",
            f"the 9-to-24-month band is "
            f"{sum(r['np'] for r in rg)/tn:.0%} of the",
            f"awards and {sum(r['nd'] for r in rg)/td:.0%} of the days.")):
        s += halo(lx(1.12), ly(0.288) + i * 13, line, size=9.5, fill=INK2)

    ky = AY + 4
    for col, lab, dash in (
            (BLUE, "FY2016, eleven departments; dot is the band's median duration", None),
            (BLUE, "the same bands with Veterans Affairs removed", "3 2.4")):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        s.append(f'<line x1="{lx(1):.1f}" y1="{ky-4:.1f}" x2="{lx(1)+16:.1f}" '
                 f'y2="{ky-4:.1f}" stroke="{col}" stroke-width="{2.8 if not dash else 1.2}"{d}/>')
        s.append(txt(lx(1) + 22, ky, lab, size=9.5, fill=INK2))
        ky += 14
    s.append(f'<circle cx="{lx(1)+8:.1f}" cy="{ky-4:.1f}" r="3.4" fill="none" '
             f'stroke="{FAINT}" stroke-width="1.5"/>')
    s.append(txt(lx(1) + 22, ky, "FY2015, plotted at its own band median", size=9.5,
                 fill=INK2))

    # ---------------------------------------------------------------- A': what A means
    TY = AY + AH + 62
    s.append(txt(AX, TY, "the ridge is not composition; the collapse is partly a hard line",
                 size=12.5, fill=INK, weight="600"))
    nova = {r["lo"]: r for r in a["bands_nova"]}
    s += wrap(AX, TY + 20,
              f"With Veterans Affairs removed — {a['va_share_dur']:.0%} of these awards — the "
              f"share still climbs from {nova[31]['any']:.1%} at one to three months to "
              f"{nova[550]['any']:.1%} at eighteen to twenty-four, and still falls to "
              f"{nova[1096]['any']:.1%} past three years. What that department does drive is "
              f"the short end: under a month it is {a['bands'][0]['any']:.1%} of all awards "
              f"and {nova[0]['any']:.1%} without it. The far end is partly mechanical — 99% of "
              f"potential performance periods end within {CAP:,} days of the start, and past a "
              f"three-year current term the median room left to that line is "
              f"{a['bands'][8]['room']:,} days. The linear summary a reader reaches for, "
              f"{a['r_any']:+.2f}, is the wrong summary for this shape — though the size of a "
              f"gap does track duration, at {a['r_size']:+.2f}.",
              size=10.5, fill=INK2, chars=112, leading=14)

    # ---------------------------------------------------------------- B: the comb
    BX, BY, BW, BH = 668, AY, 544, AH
    hist = {int(k): v for k, v in a["hist"].items()}
    hmax = max(hist.values())
    hx = lambda d: BX + 54 + (BW - 66) * (d / 1904)
    hy = lambda c: BY + BH - (BH - 30) * (c / hmax)
    for c in range(0, hmax + 1, 4000):
        s.append(f'<line x1="{hx(0):.1f}" y1="{hy(c):.1f}" x2="{hx(1904):.1f}" '
                 f'y2="{hy(c):.1f}" stroke="{GRID}"/>')
        s.append(txt(hx(0) - 8, hy(c) + 3, f"{c:,}", size=9, fill=MUTED, anchor="end"))
    for d in (0, 365, 730, 1095, 1460, 1825):
        s.append(f'<line x1="{hx(d):.1f}" y1="{hy(0):.1f}" x2="{hx(d):.1f}" '
                 f'y2="{hy(0)+4:.1f}" stroke="{MUTED}"/>')
        s.append(txt(hx(d), hy(0) + 16, f"{d:,}", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(BX, BY - 28, "awards, by how many days of option time they hold",
                 size=11.5, fill=INK2))
    s.append(txt(BX, BY - 13,
                 f"the {a['pos']:,} awards with a gap, in 7-day bins: p25 "
                 f"{a['gapq']['0.25']} days, median {a['gapq']['0.5']}, p75 "
                 f"{a['gapq']['0.75']}, p90 {a['gapq']['0.9']:,}", size=10, fill=MUTED))
    s.append(txt(hx(0), hy(0) + 32, "potential end minus current end, days", size=10,
                 fill=MUTED))
    bw = (BW - 66) / (1904 / 7) - 0.5
    for k, v in sorted(hist.items()):
        d0 = k * 7
        near = min(abs(d0 + 3 - 365 * j) for j in range(1, 6)) <= 3
        col = AMBER if near else (PLUM if d0 < 35 else BLUE)
        s.append(f'<rect x="{hx(d0):.1f}" y="{hy(v):.1f}" width="{max(bw,1.2):.1f}" '
                 f'height="{max(hy(0)-hy(v),0.6):.1f}" fill="{col}" fill-opacity="0.9"/>')
    my = hy(hist.get(4, 0))
    s += halo(hx(60), my + 4, f"28 to 31 days, {a['month_share']:.0%} of all gaps:",
              size=9.5, fill=PLUM, weight="700")
    s += halo(hx(60), my + 17, "one more month on a purchase order", size=9.5, fill=PLUM,
              weight="700")
    for d, lab in ((365, "365"), (730, "730"), (1095, "1,095"), (1460, "1,460")):
        k = (d - 1) // 7
        top = min(hy(hist.get(k, 0)), hy(hist.get(k + 1, 0)))
        s += halo(hx(d), top - 7, lab, size=9.5, fill=AMBER, anchor="middle", weight="700")
    ay0 = hy(hmax * 0.76)
    for i, t in enumerate((f"{a['year_share']:.0%} of gaps fall within five days of a",
                           f"whole year and {a['exact365']:.0%} are exactly 365.",
                           "Option time is authorised in contract years,",
                           "not negotiated in days.")):
        s += halo(hx(430), ay0 + i * 13, t, size=10, fill=INK2)


    # ---------------------------------------------------------------- footer
    # Trimmed from the plate per doctrine/what-a-footnote-carries.md; kept here because it is method: f
    # oot = (USAspending API v2 bulk download, fetched 2026-09-22; contract transactions with
    # an action date in FY2016, eleven civilian departments, collapsed to {a['awards']:,}
    # awards on contract_award_unique_key, with FY2015 ({b['awards']:,} awards) as the
    # replication — the two date columns were checked for comparability across the years
    # before they were used together, which the money columns in this file fail. Both period-
    # of-performance end dates are present on {a['both']:,} awards —
    # {a['both']/a['awards']:.4%}, measured at award level, and still
    # {a['every']/a['awards']:.3%} under the stricter test that every transaction of the award
    # carries both — and {a['neg']} award has a potential end BEFORE its current end. Dates
    # are the maximum seen across an award's transactions, because the running fields move
    # backwards between modifications; scored by last transaction instead, the share with a
    # gap on multi-transaction awards is {a['multi_last']:.1%} rather than
    # {a['multi_max']:.1%}. The duration panel uses the {a['with_dur']:,} awards whose start
    # is not recorded after their own current end: a start date is never blank at award level,
    # but on {1-a['with_dur']/a['both']:.1%} of awards it falls after the end date, and those
    # awards carry a gap less often ({a['drop_any']:.1%} against {a['kept_any']:.1%}), so the
    # ridge is measured on a subset that is not a random one. Current duration is measured
    # after exercise, so a long current term may be a long base period or a short one whose
    # options were taken — the ridge cannot separate those. {a['far_n']} awards carry a
    # potential end after 2040, as far as {a['far_year']}, holding
    # {a['far_days']/(a['far_days']+a['optdays']):.1%} of all option-days; they are keying
    # errors and are excluded from day totals. These eleven departments are 8.5% of federal
    # contract awards — Defense is 68.6% and General Services 22.9%, and neither could be
    # fetched at this size, so nothing here is a claim about federal procurement as a whole.)
    # fy = H - 22 - 14 * (nlines(foot, 170) - 1) s.append(f'<line x1=28 y1={fy-18:.1f}
    # x2={W-28} y2={fy-18:.1f} stroke={RULE}/>') s += wrap(28, fy, foot, size=10.5,
    # fill=MUTED, chars=170, leading=14)
    foot = (
        "USAspending API v2 bulk download, fetched 2026-09-22; FY2016 with FY2015 as the "
        "replication. CAVEAT: current duration is measured after exercise, so a long term "
        "may be a long base period or a short one whose options were taken; the duration "
        "panel drops the 10.9% of awards whose start falls after their own end. These "
        "eleven civilian departments are 8.5% of federal contract awards; Defense (68.6%) "
        "is absent, so this is not federal procurement as a whole.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=170, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=170, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    both ends {a['both']:,}/{a['awards']:,} = {a['both']/a['awards']:.4%}  "
          f"gap>0 {a['pos']:,} = {a['pos']/a['both']:.2%}  reverse {a['neg']}")
    print(f"    gap days p25 {a['gapq']['0.25']}  median {a['gapq']['0.5']}  "
          f"p75 {a['gapq']['0.75']}  p90 {a['gapq']['0.9']}")
    print(f"    within 5d of a whole year {a['year_share']:.1%}  28-31d "
          f"{a['month_share']:.1%}  r_any {a['r_any']:+.3f}  r_size {a['r_size']:+.3f}")
    for r, rn in zip(a["bands"], a["bands_nova"]):
        print(f"    {r['lo']:>5}-{r['hi']:<6}{r['n']:>8,}{r['any']:>8.1%}"
              f"  no-VA {rn['any']:>6.1%}  med gap {r['med']:>6,}  room {r['room']:>6,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
