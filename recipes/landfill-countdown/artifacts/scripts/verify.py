#!/usr/bin/env python3
"""Recompute every number this recipe publishes, from the workbooks rather than the derived JSON.

    python3 verify.py

**Why this exists.** Eleven figures and a README share the same facts, and prose drifts from
code silently. Re-reading `landfill.json` would only re-read what `measure.py` wrote, so this
goes back to the two workbooks and recomputes.

It exists because two published numbers had already drifted when it was written:

* The README said 250 of the 304 apparent ownership changes were one company renaming itself.
  The rebrand is **248**; the gap between raw string changes and real ones is **255**, of
  which 7 are other normalisation effects. Neither reading gave 250.
* The README said **eight** states have a median landfill with under twenty years left.
  `measure.py` counts a state only once it has eight measurable sites, and on that basis it is
  **seven** -- Tennessee's median is 20.17. Eight is the answer at a minimum of five sites.
  The threshold decides the headline and the README had not stated one.

Both are the same failure: a number that no shipped script produces. If a number here
disagrees with the README, **this script is authoritative and the prose is a bug**, per the
repo's own rule.
"""
import collections, glob, json, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lmopdata as L                                                     # noqa: E402

num = L.num
DATA = L.DATA
GEN, COL, FLR = "LFG Generated (mmscfd)", "LFG Collected (mmscfd)", "LFG Flared (mmscfd)"
OWNER = "Landfill Owner Organization(s)"
MIN_SITES = 8          # measure.py's own threshold for naming a state


def stale():
    """A figure older than the script that draws it is a caption describing a past version."""
    out = []
    for py in sorted(glob.glob(os.path.join(HERE, "chart-*.py"))):
        stem = os.path.basename(py)[len("chart-"):-3]
        svg = os.path.join(HERE, "..", "charts", f"{stem}.svg")
        if not os.path.exists(svg):
            out.append((stem, "no figure built"))
        elif os.path.getmtime(svg) < os.path.getmtime(py):
            out.append((stem, "figure is older than its script"))
    return out


def workbooks():
    """The two editions must be the exact bytes provenance recorded: they cannot be refetched."""
    import hashlib
    p = os.path.join(HERE, "..", "..", "provenance.json")
    if not os.path.exists(p):
        return [("provenance.json", "absent, workbooks unchecked")]
    with open(p) as f:
        want = json.load(f)
    rec = {}
    for block in (want.get("sources"), want.get("corpus")):
        if isinstance(block, dict):
            for k, v in block.items():
                if isinstance(v, dict) and "sha256" in v:
                    rec[os.path.basename(str(v.get("path") or k))] = v["sha256"]
    out = []
    for name in L.EDITIONS.values():
        path = os.path.join(DATA, name)
        if not os.path.exists(path):
            out.append((name, "missing -- the 2021 edition cannot be refetched from EPA"))
            continue
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        for k, v in rec.items():
            if name in k and v != h:
                out.append((name, f"sha256 {h[:12]}, provenance says {v[:12]}"))
    return out


def countdowns(ed, fresh=None):
    out, why = {}, collections.Counter()
    for k, r in ed.items():
        v, reason = L.countdown(r, fresh)
        if v is None:
            why[reason] += 1
        else:
            out[k] = v
    return out, why


def main():
    lag = stale()
    print("  stale figures:", "none" if not lag else "")
    for stem, why in lag:
        print(f"    {stem}: {why}")
    bad = workbooks()
    print("  workbooks vs provenance:", "match" if not bad else "")
    for n, why in bad:
        print(f"    {n}: {why}")

    a, b = L.load("2021"), L.load("2024")
    both = set(a) & set(b)
    print(f"\n  == the register ==")
    print(f"  {'sites, 2021 edition':<38}{len(a):>10,}")
    print(f"  {'sites, 2024 edition':<38}{len(b):>10,}")
    print(f"  {'same id in both':<38}{len(both):>10,}")

    c24, why24 = countdowns(b)
    openn = sum(1 for r in b.values()
                if str(r.get("Current Landfill Status") or "").strip() == "Open")
    print(f"\n  == the countdown ==")
    print(f"  {'open landfills':<38}{openn:>10,}")
    print(f"  {'countdown computable':<38}{len(c24):>10,}")
    print(f"  {'not computable':<38}{openn - len(c24):>10,}")
    print(f"  {'full within five years':<38}{sum(1 for v in c24.values() if v < 5):>10,}")
    print(f"  {'median years left':<38}{st.median(c24.values()):>10.1f}")

    bys = collections.defaultdict(list)
    for k, v in c24.items():
        s = str(b[k].get("State") or "").strip()
        if s:
            bys[s].append(v)
    named = sorted(((s, st.median(v), len(v)) for s, v in bys.items() if len(v) >= MIN_SITES),
                   key=lambda r: r[1])
    u20 = [r for r in named if r[1] < 20]
    print(f"\n  == states, counting only those with {MIN_SITES}+ measurable sites ==")
    print(f"  {'states with a median under twenty':<38}{len(u20):>10}")
    for s, m, n in named[:9]:
        print(f"    {s:<4}{m:>8.2f}  n={n}")
    # The threshold decides the headline, so it is printed rather than assumed.
    print("  sensitivity, states under twenty by minimum site count:")
    print("   ", "  ".join(f"n>={n}:{sum(1 for s, v in bys.items() if len(v) >= n and st.median(v) < 20)}"
                           for n in (3, 4, 5, 6, 8, 10)))

    print(f"\n  == who owns the remaining room ==")
    cap, sites = collections.Counter(), collections.Counter()
    for r in b.values():
        if str(r.get("Current Landfill Status") or "").strip() != "Open":
            continue
        c, w = num(r.get("Landfill Design Capacity (tons)")), num(r.get("Waste in Place (tons)"))
        if c is None or w is None or c - w <= 0:
            continue
        key = (L.owner_key(r.get(OWNER)), str(r.get("Landfill Ownership Type") or "").strip())
        cap[key] += c - w
        sites[key] += 1
    tot = sum(cap.values())
    top = cap.most_common(2)
    print(f"  {'remaining permitted capacity':<38}{tot/1e9:>9.1f}bn tons")
    print(f"  {'across sites reporting both':<38}{sum(sites.values()):>10,}")
    print(f"  {'held by the largest two owners':<38}{sum(v for _, v in top)/tot:>10.1%}")
    for (k, t), v in top:
        print(f"    {k[:26]:<28}{t:<9}{v/1e9:>7.2f}bn  {sites[(k, t)]:>4} sites")
    one = [(k, t) for (k, t), n in sites.items() if n == 1]
    print(f"  {'owners holding exactly one site':<38}{len(one):>10,}")
    print(f"  {'   their share of the room':<38}{sum(cap[k] for k in one)/tot:>10.1%}")
    print(f"  {'   median tons each':<38}{st.median([cap[k] for k in one])/1e6:>9.1f}M")

    print(f"\n  == what changed between the editions ==")
    raw = [k for k in both if str(a[k].get(OWNER)) != str(b[k].get(OWNER))]
    real = [k for k in both if L.owner_key(a[k].get(OWNER)) != L.owner_key(b[k].get(OWNER))]
    wm = [k for k in raw
          if L.owner_key(a[k].get(OWNER)) == L.owner_key(b[k].get(OWNER)) == "wm"]
    print(f"  {'owner string changed':<38}{len(raw):>10,}")
    print(f"  {'actually changed hands':<38}{len(real):>10,}")
    print(f"  {'the Waste Management -> WM rebrand':<38}{len(wm):>10,}")
    print(f"  {'other normalised-away differences':<38}{len(raw)-len(real)-len(wm):>10,}")

    print(f"\n  == the three-year interval, matched basket ==")
    # chart-5's basket exactly: computable in BOTH editions, each judged by its own calendar,
    # and a stock year that advanced by exactly three. Dropping the countdown requirement
    # gives 883 and a different pair of totals, which is how this check first disagreed.
    basket = []
    for k in both:
        y0, _ = L.countdown(a[k], fresh=2017)
        y1, _ = L.countdown(b[k], fresh=2020)
        ya = num(a[k].get("Waste in Place Year"))
        yb = num(b[k].get("Waste in Place Year"))
        if y0 is not None and y1 is not None and ya and yb and yb - ya == 3:
            basket.append(k)
    def room(ed, keys):
        t = 0.0
        for k in keys:
            r = ed[k]
            c, w = num(r.get("Landfill Design Capacity (tons)")), num(r.get("Waste in Place (tons)"))
            if c is not None and w is not None and c - w > 0:
                t += c - w
        return t
    print(f"  {'sites whose stock advanced 3 years':<38}{len(basket):>10,}")
    print(f"  {'room in 2021, that basket':<38}{room(a, basket)/1e9:>9.1f}bn")
    print(f"  {'room in 2024, that basket':<38}{room(b, basket)/1e9:>9.1f}bn")

    # The headline sentence of this recipe. It was a hardcoded string in chart-5's footer for
    # the recipe's whole life -- 14.5bn/14.8bn/1.3bn -- and no basis below reproduces it. The
    # direction is robust to every basis; the digits were not, so every basis is printed.
    def room_all(ed, keys=None):
        t = 0.0
        for k in (keys if keys is not None else ed):
            r = ed[k]
            if str(r.get("Current Landfill Status") or "").strip() != "Open":
                continue
            c, w = num(r.get("Landfill Design Capacity (tons)")), num(r.get("Waste in Place (tons)"))
            if c is not None and w is not None and c - w > 0:
                t += c - w
        return t
    print(f"  {'':<38}{'2021':>10}{'2024':>10}")
    print(f"  {'room, all open sites':<38}{room_all(a)/1e9:>9.2f}{room_all(b)/1e9:>9.2f}")
    print(f"  {'room, the matched basket':<38}{room(a, basket)/1e9:>9.2f}{room(b, basket)/1e9:>9.2f}")
    added = sum(max(0.0, (num(b[k].get("Landfill Design Capacity (tons)")) or 0)
                    - (num(a[k].get("Landfill Design Capacity (tons)")) or 0)) for k in basket)
    dug = sum(max(0.0, (num(b[k].get("Waste in Place (tons)")) or 0)
                  - (num(a[k].get("Waste in Place (tons)")) or 0)) for k in basket)
    print(f"  {'new capacity permitted, that basket':<38}{added/1e9:>9.2f}bn")
    print(f"  {'buried, that basket':<38}{dug/1e9:>9.2f}bn")

    # The two percentages the figure prints on its face, which its own docstring got wrong.
    GAP = 3
    pts = []
    for k in basket:
        y0, _ = L.countdown(a[k], fresh=2017)
        y1, _ = L.countdown(b[k], fresh=2020)
        pts.append((y0, y1))
    above = lambda p: p[1] > max(p[0] - GAP, 0.01)
    for lab, grp in (("under 10 years left in 2021", [p for p in pts if p[0] < 10]),
                     ("over 50 years left in 2021", [p for p in pts if p[0] >= 50])):
        print(f"  {'gained room, ' + lab:<38}{sum(above(p) for p in grp)/len(grp):>10.0%}  n={len(grp)}")

    # Hardcoded in chart-5's side note, unlike its footer this one is correct -- checked here
    # so it stays that way.
    shorts = [k for k in basket if (L.countdown(a[k], fresh=2017)[0] or 0) < 10]
    addk = lambda k: max(0.0, (num(b[k].get("Landfill Design Capacity (tons)")) or 0)
                         - (num(a[k].get("Landfill Design Capacity (tons)")) or 0))
    print(f"  {'nearly-out sites, share of basket':<38}{len(shorts)/len(basket):>10.0%}")
    print(f"  {'   their share of new tonnage':<38}{sum(addk(k) for k in shorts)/added:>10.0%}")

    print(f"\n  == the gas ==")
    rows = []
    for r in b.values():
        s = str(r.get("Current Landfill Status") or "").strip()
        g, c, f = num(r.get(GEN)), num(r.get(COL)), num(r.get(FLR))
        if s not in ("Open", "Closed") or not g or c is None or f is None or g <= 0:
            continue
        c = min(c, g); f = min(f, c)
        rows.append({"g": g, "use": c - f, "flare": f, "esc": g - c})
    G = sum(r["g"] for r in rows)
    for k, lab in (("esc", "escapes"), ("flare", "burned off"), ("use", "put to use")):
        print(f"  {lab:<38}{sum(r[k] for r in rows)/G:>10.1%}")
    print(f"  {'sites using essentially none of it':<38}"
          f"{sum(1 for r in rows if r['use'] <= 0.01*r['g'])/len(rows):>10.1%}")

    fp = os.path.join(DATA, "features.json")
    if os.path.exists(fp):
        print(f"\n  == what happens after closure ==")
        with open(fp) as f:
            feats = json.load(f)
        withyear = [r for r in feats if not r["open"] and r.get("closure_year")]
        cl = [r for r in feats if not r["open"] and r.get("closure_year") and r.get("wip")
              and 1940 <= r["closure_year"] <= 2024 and r["wip"] > 0]
        print(f"  {'closed sites with a closure year':<38}{len(withyear):>10,}")
        print(f"  {'   of those, plotted (dated size too)':<38}{len(cl):>10,}")
        dec = collections.defaultdict(list)
        for r in cl:
            dec[int(r["closure_year"]) // 10 * 10].append(bool(r.get("has_gas")))
        for d in sorted(dec):
            if d >= 1980 and len(dec[d]) >= 20:
                print(f"    {d}s{'':<32}{sum(dec[d])/len(dec[d]):>10.0%}  n={len(dec[d])}")

    return 1 if (lag or bad) else 0


if __name__ == "__main__":
    sys.exit(main())
