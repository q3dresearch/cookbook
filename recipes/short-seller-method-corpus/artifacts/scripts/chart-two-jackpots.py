#!/usr/bin/env python3
"""They find crimes at every size. Broken businesses are just what small looks like.

    python chart-two-jackpots.py

Two things are worth proving about a company: that a crime is happening, or that its
unit economics do not work. Both are checkable from SEC filings alone. Measured
against 139 filers nobody attacked, and plotted against size, the two behave in
opposite ways -- which is the whole finding, and it is invisible until size is on an
axis.

**Crime.** The control line is flat and low at every size: an untargeted company
discloses a Wells notice, grand jury, subpoena or formal order of investigation about
5-10% of the time whether it is worth $47m or $2.6bn. The target line sits above it.
Being targeted raises the rate; being large does not.

**Broken economics.** Both lines fall steeply with size and run close together. A
small company fails to cover its overhead or burns cash essentially always -- 10/10
targets and 5/6 controls -- and a large one about a quarter to a third of the time,
whether or not anybody shorted it. **Size explains this axis; being targeted barely
does.** Pooled across sizes it reads 49% against 33%, which looks like a finding and
is mostly the fact that targets skew large and controls skew small.

**Why filer class is the size axis.** `dei:EntityPublicFloat` is the obvious
continuous version and it fails here: foreign private issuers do not file it, which
removed 21 of 76 targets and left the control group with 25 usable companies and zero
enforcement events -- nothing to compare against. Filer class is the same measurement
banded by the regulator, with the coverage the raw field lacks, and it tracks float as
it should: median $47m, $217m and $2,600m across the three bands.

**The middle band is thin and is drawn thin.** Eleven targets and ten controls, so its
intervals swallow most of the panel. Do not read the dip; read the two ends.

**The two series are dodged apart, not jittered.** Stacked on one x position their
intervals overlapped and neither could be read. Random jitter would fix that by
asserting x positions that do not exist -- there is no company sitting between
"accelerated" and "large accelerated" -- so the offset is a fixed paired one and every
mark still sits at a real value. A faint separator groups each pair back into its band.

**Boxplots were the other candidate and do not survive the sample.** The crime axis is
binary per company, so there is no distribution to box at all. The economics axis has
one -- operating margin -- but four of its six cells hold between six and ten
companies, and quartiles drawn from six points assert a precision that is not there.
The tails make it worse: operating margin runs from -49x to +0.39 among small targets
and cash burn from -93x to +27x, so any box would need clipping before it could be
drawn. A rate with an interval says what the sample can support.

**One caution on the crime panel that does not go away.** A short report can cause the
investigation it appears to predict -- regulators read these, and a public allegation
is itself a reason to open a file. Nothing here separates "found a company already
under investigation" from "caused one". That needs the date a file was opened, which
is not public.

**What is not faceted here, and why.** The natural third cut is the report's declared
thesis -- crime, accounting, broken economics. It does not survive the arithmetic: 76
targets split three ways and then across three size bands is about eight companies a
cell, and the control group has no declared thesis at all to compare against.
"""
import json, random, sys
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import palette
from jackpot import broken, enforced, enforced_at
from selection import wilson, fisher

RAW = HERE.parent / "raw"
OUT = HERE.parent / "charts" / "two-jackpots.svg"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
RULE = "#ebeae3"
HOT, COOL = "#b03a2e", "#1b4f8a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
W, H = 960, 610
BANDS = [("non-accelerated", "under $75m float", "~$47m"),
         ("accelerated", "$75m - $700m", "~$217m"),
         ("large accelerated", "over $700m", "~$2.6bn")]


def txt(x, y, s, *, size, fill, anchor="start", weight="normal", tab=False):
    st = "font-variant-numeric: tabular-nums;" if tab else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family=\'{FONT}\' font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
            f'style="{st}">{escape(s)}</text>')


def para(x, y, s, *, size, fill, chars, leading=17.0):
    words, line, out, n = s.split(), [], [], 0
    for w in words:
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
            line, n = [], n + 1
        line.append(w)
    if line:
        out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
        n += 1
    return out, n * leading


def band_of(prof):
    f = [x.strip() for x in ((prof or {}).get("category") or "").split("<br>") if x.strip()]
    if not f:
        return None
    if "Large accelerated filer" in f:
        return "large accelerated"
    if "Accelerated filer" in f:
        return "accelerated"
    return "non-accelerated"


def main():
    T = json.loads((RAW / "jackpot_targets.json").read_text())
    C = json.loads((RAW / "jackpot_controls.json").read_text())
    P = json.loads((RAW / "profiles.json").read_text())
    tprof = P["targets"]
    cprof = {str(v["cik"]): v for v in P["controls"].values() if v.get("cik")}

    dates = sorted(v["as_of"] for v in T.values())
    rnd = random.Random(20260912)

    def series(items, profs, measure, ctrl=False):
        out = []
        for b, _, _ in BANDS:
            vals = [measure(v, rnd) for k, v in items.items() if band_of(profs.get(k)) == b]
            vals = [x for x in vals if x is not None]
            out.append((sum(vals), len(vals)))
        return out

    crime_t = series(T, tprof, lambda v, r: enforced(v))
    crime_c = series(C, cprof, lambda v, r: enforced_at(v, r.choice(dates)))
    econ_t = series(T, tprof, lambda v, r: broken(v["economics"]))
    econ_c = series(C, cprof, lambda v, r: broken(v["economics"]))

    panels = [("A crime is being investigated",
               "disclosed a Wells notice, grand jury, subpoena or formal order within 3 years",
               crime_t, crime_c),
              ("The business does not work",
               "does not cover its overhead, or burns cash, at the last annual before the report",
               econ_t, econ_c)]

    L, R, GAP, TOP = 52, 40, 58, 196
    pw = (W - L - R - GAP) / 2
    ph = 236
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    s.append(txt(L, 44, "They find crimes at every size. Broken businesses are what small looks like.",
                 size=20, fill=INK, weight="600"))
    body, _ = para(L, 72, "Short-seller targets against 139 filers nobody attacked, by SEC filer class "
                   "— the regulator's own public-float bands. Bars are 95% intervals.",
                   size=13, fill=INK2, chars=112)
    s += body
    # Legend on the title row. Below it, it landed on the left panel's subtitle.
    for i, (lab, col) in enumerate((("targets", HOT), ("controls", COOL))):
        lx = W - R - 200 + i * 104
        s.append(f'<circle cx="{lx + 5:.1f}" cy="{68}" r="5.5" fill="{col}"/>')
        s.append(txt(lx + 16, 72, lab, size=12, fill=INK2))

    for pi, (title, sub, st, sc) in enumerate(panels):
        x0 = L + pi * (pw + GAP)
        sy = lambda v: TOP + ph - v * ph
        s.append(txt(x0, TOP - 66, title, size=14, fill=INK, weight="600"))
        sw, _ = para(x0, TOP - 48, sub, size=11, fill=MUTED, chars=int(pw / 5.6), leading=13)
        s += sw
        for g in (0, 0.25, 0.5, 0.75, 1.0):
            y = sy(g)
            s.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + pw:.1f}" y2="{y:.1f}" '
                     f'stroke="{RULE}" stroke-width="1"/>')
            if pi == 0:
                s.append(txt(x0 - 10, y + 4, f"{g:.0%}", size=11, fill=MUTED,
                             anchor="end", tab=True))
        # Targets and controls are DODGED, not jittered. Random jitter on an ordinal
        # axis asserts x positions that do not exist -- there is no company "between"
        # accelerated and large accelerated. A fixed paired offset separates the two
        # series and every mark still sits at a real value.
        bx = [x0 + pw * (j + 0.5) / 3 for j in range(3)]
        DODGE = 15
        for j, (b, thresh, med) in enumerate(BANDS):
            if j:
                sep = x0 + pw * j / 3
                s.append(f'<line x1="{sep:.1f}" y1="{TOP - 4}" x2="{sep:.1f}" '
                         f'y2="{TOP + ph + 8:.1f}" stroke="{RULE}" stroke-width="1"/>')
            s.append(txt(bx[j], TOP + ph + 22, b.replace(" ", "\n").split("\n")[0],
                         size=11, fill=INK2, anchor="middle"))
            s.append(txt(bx[j], TOP + ph + 36, med, size=11, fill=MUTED,
                         anchor="middle", tab=True))
        # Lines connect because the x-axis is ordered by size: the connector asserts a
        # trend across size, which is exactly the claim each panel makes.
        for (ser, col, side) in ((sc, COOL, +1), (st, HOT, -1)):
            px = [b + side * DODGE for b in bx]
            pts = [(px[j], sy(k / n)) for j, (k, n) in enumerate(ser) if n]
            s.append(f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" '
                     f'fill="none" stroke="{col}" stroke-width="2" stroke-opacity="0.5"/>')
            for j, (k, n) in enumerate(ser):
                if not n:
                    continue
                lo, hi = wilson(k, n)
                s.append(f'<line x1="{px[j]:.1f}" y1="{sy(lo):.1f}" x2="{px[j]:.1f}" '
                         f'y2="{sy(hi):.1f}" stroke="{col}" stroke-width="3" '
                         f'stroke-opacity="0.3" stroke-linecap="round"/>')
                s.append(f'<circle cx="{px[j]:.1f}" cy="{sy(k / n):.1f}" r="6" fill="{col}" '
                         f'stroke="{SURFACE}" stroke-width="2"/>')
                # With the series dodged apart the labels follow them outward, so the
                # count sits on the same side as its own track at every band.
                lx = px[j] + (11 if side > 0 else -11)
                s.append(txt(lx, sy(k / n) + 4, f"{k}/{n}", size=10.5, fill=col,
                             anchor="start" if side > 0 else "end", tab=True))
        s.append(txt(x0 + pw / 2, TOP + ph + 56, "public float band", size=11.5,
                     fill=INK2, anchor="middle"))

    fy = TOP + ph + 92
    s.append(f'<line x1="{L}" y1="{fy - 22}" x2="{W - R}" y2="{fy - 22}" stroke="{RULE}" stroke-width="1"/>')
    foot, _ = para(L, fy, "Controls sit at 5-10% on crime at every size, and targets sit above them — "
                   "being targeted raises the rate, being large does not. On economics both lines fall "
                   "with size and run together: small companies burn cash whether or not anybody shorts "
                   "them. The middle band is 11 and 10 companies; read the ends, not the dip.",
                   size=12, fill=INK2, chars=116)
    s += foot
    s.append("</svg>")
    OUT.write_text("\n".join(s))
    for title, _, st, sc in panels:
        print(f"  {title}")
        for j, (b, _, med) in enumerate(BANDS):
            (a, na), (c, nc) = st[j], sc[j]
            print(f"    {b:<18}{med:>8}  targets {a}/{na}={a/na if na else 0:>4.0%}   "
                  f"controls {c}/{nc}={c/nc if nc else 0:>4.0%}")


if __name__ == "__main__":
    main()
