#!/usr/bin/env python3
"""A chart that would have been published, and the test that kills it.

    python3 chart-2-priority.py     [fetches its own full-schema slices on first run]

The Biennial Report carries `priority_chemical`, a Y/N flag on every record. Trend it
across the metals-recovery stream and it says the share of tonnage containing an EPA
priority chemical fell from **94% in 2001 to 13% in 2023** — an 87% collapse, which would
be a triumph of chemical substitution and a genuinely publishable claim.

**It is false, and one test kills it.** Hold the waste code fixed. `D008` is the RCRA
toxicity-characteristic code for **lead**: a waste carries it because it leaches lead. In
2001 and 2011, 100% of D008 records were flagged as containing a priority chemical. In
2023, **16%** are. Lead did not stop being lead. `F006` electroplating sludge runs 100% to
18%; `K061` electric-arc-furnace dust, which is zinc, lead and cadmium by definition, runs
100% to 64%.

**And it is not a blanket data failure, which is what makes it dangerous.** Deep-well
injection over the same years is stable — 35% of D002 records flagged in 2001, 30% in 2023
— so a spot-check on the wrong category would have confirmed the field as healthy. The
decay is specific to the metal-bearing codes, exactly the ones a recycling story would be
built on.

Whether EPA revised its National Priority Chemicals list or the flag simply stopped being
maintained for metals, this figure does not say. It says only that the field cannot carry a
trend, which is enough to stop the chart on the left from being drawn as fact.

The left panel is kept rather than deleted **because it is convincing**. A merely bad chart
teaches nothing; one that would have been believed is the whole lesson.
"""
import csv, collections, gzip, io, math, os, shutil, subprocess, sys, tempfile, time
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate                                                             # noqa: E402
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(HERE, "..", "charts", "priority.svg")
# This figure needs `priority_chemical`, which the main extract does not carry, so it keeps
# its own small cache of full-schema slices -- beside the recipe, never in /tmp. A first
# version read them out of a scratchpad directory and stopped working the moment the
# machine cleared it.
SRC = os.environ.get("HWF_RAW") or os.path.join(DATA, "priority-cache")
BASE = "https://data.epa.gov/efservice/BR_REPORTING"
AGENT = "public-record-research/1.0 (hazardous waste flows recipe; contact dl.eeee.nv@gmail.com)"
FILT = {"mr": "MANAGEMENT_CATEGORY/METALS%20RECOVERY",
        "dw": "MANAGEMENT_CATEGORY/BEGINNING/DEEPWELL"}


def ensure(prefix, cycle):
    """Fetch one full-schema slice if it is not already cached. Returns its path or None."""
    os.makedirs(SRC, exist_ok=True)
    path = os.path.join(SRC, f"{prefix}{cycle}.csv.gz")
    if os.path.exists(path) and os.path.getsize(path) > 500:
        return path
    curl = shutil.which("curl")
    if not curl:
        return None
    url = f"{BASE}/{FILT[prefix]}/REPORT_CYCLE/{cycle}/CSV"
    fd, tmp = tempfile.mkstemp(suffix=".part")
    os.close(fd)
    try:
        r = subprocess.run([curl, "-sS", "--compressed", "--fail", "--max-time", "600",
                            "-H", f"User-Agent: {AGENT}", url, "-o", tmp],
                           capture_output=True, text=True)
        if r.returncode != 0 or os.path.getsize(tmp) < 500:
            print(f"    {prefix}{cycle}: fetch failed ({r.returncode})", flush=True)
            return None
        with open(tmp, "rb") as f, gzip.open(path + ".tmp", "wb") as g:
            shutil.copyfileobj(f, g)
        os.replace(path + ".tmp", path)
        print(f"    {prefix}{cycle}: fetched", flush=True)
        return path
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
SURFACE, INK, INK2, MUTED, RULE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8880", "#e3e2db", "#f0efe9"
WRONG, OK = "#b03a2e", "#1b4f8a"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
YEARS = (2001, 2011, 2013, 2015, 2017, 2019, 2023)
CODES = [("D008", "D008  lead", "#8c2318"), ("F006", "F006  plating sludge", "#b03a2e"),
         ("K061", "K061  furnace dust", "#c07a1e"), ("D007", "D007  chromium", "#6b6f2e"),
         ("D009", "D009  mercury", "#9a5a2e")]
num = lambda v: float(v) if v not in ("", "None", None) else 0.0


def txt(x, y, s, *, size, fill, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" style="font-variant-numeric: tabular-nums">{escape(str(s))}</text>')


def halo(x, y, s, *, size, fill, anchor="start", weight="600"):
    c = (f'font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" '
         f'style="font-variant-numeric: tabular-nums"')
    e = escape(str(s))
    return [f'<text x="{x:.1f}" y="{y:.1f}" fill="none" stroke="{SURFACE}" stroke-width="3" '
            f'stroke-linejoin="round" {c}>{e}</text>',
            f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" {c}>{e}</text>']


def wrap(x, y, s, *, size, fill, chars, leading=15.0):
    words, line, out, n = str(s).split(), [], [], 0
    for w in words:
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill)); line, n = [], n + 1
        line.append(w)
    if line:
        out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
    return out


def load(prefix, y):
    p = ensure(prefix, y)
    if not p:
        return None
    with gzip.open(p, "rt", encoding="latin-1", newline="") as f:
        return list(csv.DictReader(f))


def main():
    tempting, bycode, deep = {}, collections.defaultdict(dict), {}
    for y in YEARS:
        rows = load("mr", y)
        if rows:
            t = sum(num(r["managed_tons"]) + num(r["generation_tons"]) for r in rows)
            tp = sum(num(r["managed_tons"]) + num(r["generation_tons"]) for r in rows
                     if r.get("priority_chemical") == "Y")
            tempting[y] = tp / t if t else 0
            for c, _, _ in CODES:
                g = [r for r in rows if c in (r.get("federal_waste_codes") or "")]
                if len(g) >= 20:
                    bycode[c][y] = sum(1 for r in g if r.get("priority_chemical") == "Y") / len(g)
        dw = load("dw", y)
        if dw:
            g = [r for r in dw if "D002" in (r.get("federal_waste_codes") or "")]
            if len(g) >= 20:
                deep[y] = sum(1 for r in g if r.get("priority_chemical") == "Y") / len(g)
    if not tempting:
        print(f"  no full-schema slices in {SRC}"); return 1

    W, H, T, PH = 1060, 720, 216, 384
    L, PW = 92, 400
    RX, RW = 600, 292
    lx = lambda base, w, y: base + w * (y - YEARS[0]) / (YEARS[-1] - YEARS[0])
    ly = lambda v: T + PH - PH * v
    body = []
    for base, w, lab in ((L, PW, "left"), (RX, RW, "right")):
        for v in (0, 0.25, 0.5, 0.75, 1.0):
            body.append(f'<line x1="{base}" y1="{ly(v):.1f}" x2="{base+w}" y2="{ly(v):.1f}" '
                        f'stroke="{GRID}"/>')
        for y in (2001, 2011, 2023):
            body.append(txt(lx(base, w, y), T + PH + 20, str(y), size=11, fill=MUTED, anchor="middle"))
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        body.append(txt(L - 10, ly(v) + 4, f"{v:.0%}", size=11, fill=MUTED, anchor="end"))
        body.append(txt(RX - 10, ly(v) + 4, f"{v:.0%}", size=11, fill=MUTED, anchor="end"))

    body.append(txt(L, T - 46, "the chart that would have been published", size=13, fill=WRONG,
                    weight="700"))
    body += wrap(L, T - 30, "share of metals-recovery tonnage recorded as containing an EPA "
                            "priority chemical", size=10.5, fill=MUTED, chars=56, leading=12)
    ks = sorted(tempting)
    p = " ".join(f"{'M' if i==0 else 'L'}{lx(L,PW,y):.1f},{ly(tempting[y]):.1f}"
                 for i, y in enumerate(ks))
    body.append(f'<path d="{p}" fill="none" stroke="{WRONG}" stroke-width="3"/>')
    for y in ks:
        body.append(f'<circle cx="{lx(L,PW,y):.1f}" cy="{ly(tempting[y]):.1f}" r="3.5" fill="{WRONG}"/>')
    body += halo(lx(L, PW, ks[0]) + 8, ly(tempting[ks[0]]) - 10, f"{tempting[ks[0]]:.0%}",
                 size=13, fill=WRONG, weight="700")
    body += halo(lx(L, PW, ks[-1]) - 8, ly(tempting[ks[-1]]) - 12, f"{tempting[ks[-1]]:.0%}",
                 size=13, fill=WRONG, anchor="end", weight="700")
    body += wrap(L + 10, ly(0.62),
                 "“Priority-chemical waste in metals recovery fell 87% in twenty years.” "
                 "Publishable, quotable, and false.", size=11.5, fill=WRONG, chars=40, leading=14)

    body.append(txt(RX, T - 46, "the test that kills it", size=13, fill=OK, weight="700"))
    body += wrap(RX, T - 30, "share of records flagged, holding the waste code fixed — the same "
                             "physical material throughout", size=10.5, fill=MUTED, chars=56, leading=12)
    placed = []
    for c, lab, col in CODES:
        d = bycode.get(c, {})
        ks2 = sorted(d)
        if len(ks2) < 3:
            continue
        p = " ".join(f"{'M' if i==0 else 'L'}{lx(RX,RW,y):.1f},{ly(d[y]):.1f}"
                     for i, y in enumerate(ks2))
        body.append(f'<path d="{p}" fill="none" stroke="{col}" stroke-width="2"/>')
        ty = ly(d[ks2[-1]]) + 4
        while any(abs(ty - q) < 13 for q in placed):
            ty += 13
        placed.append(ty)
        body += halo(lx(RX, RW, ks2[-1]) + 7, ty, f"{lab}  {d[ks2[-1]]:.0%}", size=10, fill=col)
    if deep:
        kd = sorted(deep)
        p = " ".join(f"{'M' if i==0 else 'L'}{lx(RX,RW,y):.1f},{ly(deep[y]):.1f}"
                     for i, y in enumerate(kd))
        body.append(f'<path d="{p}" fill="none" stroke="{OK}" stroke-width="2.6" '
                    f'stroke-dasharray="5 3"/>')
        ty = ly(deep[kd[-1]]) + 4
        while any(abs(ty - q) < 13 for q in placed):
            ty += 13
        body += halo(lx(RX, RW, kd[-1]) + 7, ty, f"D002 in deep-well  {deep[kd[-1]]:.0%}",
                     size=10, fill=OK)
    body += wrap(RX + 6, ly(0.26),
                 "Deep-well injection is flat across the same years, so a spot-check on the wrong "
                 "category would have confirmed the field as healthy.",
                 size=10.5, fill=OK, chars=44, leading=13)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f"font-family='{FONT}'><rect width='{W}' height='{H}' fill='{SURFACE}'/>",
         txt(28, 40, "Lead did not stop being lead", size=19, fill=INK, weight="600")]
    fr, _y = plate.frame(W, 62,
                        who="a regulator tracking whether a priority chemical is being phased out",
                        decide="whether a falling record count means the hazard fell",
                        wrong="lead tonnage falls while its record count holds")
    s += fr
    s += body
    fy = H - 20 - 15 * 2
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    d8 = bycode.get("D008", {})
    foot = [f"D008 is the code a waste carries because it leaches lead. It was flagged as a priority "
            f"chemical on {max(d8.values()):.0%} of records at its peak and "
            f"{d8[max(d8)]:.0%} in {max(d8)}.",
            "The left panel is kept because it is convincing. A merely bad chart teaches nothing; one "
            "that would have been believed is the entire lesson.",
            "Metals recovery and deep-well injection, all cycles with a full-schema extract. Whether "
            "EPA revised its priority list or the flag decayed, this cannot say — only that it cannot "
            "carry a trend."]
    for i, line in enumerate(foot):
        s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"  tempting: {tempting[min(tempting)]:.0%} -> {tempting[max(tempting)]:.0%}")
    for c, _, _ in CODES:
        d = bycode.get(c, {})
        if d:
            print(f"    {c}: {d[min(d)]:.0%} -> {d[max(d)]:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
