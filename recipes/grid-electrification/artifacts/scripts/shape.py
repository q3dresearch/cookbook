#!/usr/bin/env python3
"""Load shape as a compute detector, and the two things that imitate it.

    python3 shape.py

Not a chart. `chart-3-flatload.py` draws the field, `chart-4-trajectory.py` draws the
grids that make the distinction. Both read this.

**The idea.** A data centre is a flat 24/7 load. Add L megawatts of it to a grid whose
overnight trough is T and afternoon peak is P, and both rise by L -- so the trough grows by
L/T and the peak by only L/P. Since T < P, the trough must grow faster. The gap between the
two growth rates is the signature.

**A joint jump, cause unresolved.** Five grids have a year where the trough AND the peak
both rose over 10% at once. WACM's trough rose 37% and its peak 27% in 2023. A utility
joining the balancing authority would look exactly like that, so the obvious test is whether
some other balancing authority lost the same load in the same year. **It did not.** WACM
gained about 1.35 GW across 2022 and 2023; the largest neighbouring fall is PSCO at roughly
0.35 GW, and WAUW, NWMT, PACE and BPAT are flat. Santee Cooper's 2021 jump has no matching
fall either.

So `jump()` flags these and stops there. It is not an annexation detector and must not be
read as one -- the flag says the trough and peak moved together, which ordinary load growth
does not usually do, and that this dataset does not contain the reason. ERCOT trips the same
flag in 2022 on what is plainly real Texas growth, which is the reminder that the flag marks
a question and not an answer.

**Imitator two: behind-the-meter solar.** Rooftop solar never appears in generation at all;
it appears as demand that did not happen, in the middle of the day, which suppresses the
recorded peak and leaves the overnight trough untouched. CISO's peak grew 0.2% while its
trough grew 6.0%. This one cannot be removed from this dataset, because the thing doing it
is invisible in it -- so the chart separates it by shape instead: solar holds the peak flat,
flat load raises both.

**What the field looks like after that.** The largest raw gaps belong to small grids, where
one customer or one reporting change moves the whole number. Size is the covariate that eats
findings here, so `rows()` carries the peak in GW and the charts draw it.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "..", "data", "eba-hourly.json")

# Fourteen of the seventy codes in EBA are REGIONS, not balancing authorities: CAL contains
# CISO, TEX contains ERCO, US48 contains everything. Ranking a container against its own
# contents is not a ranking, so the regions are tagged and kept out of the field.
REGION = {"CAL", "CAR", "CENT", "FLA", "MIDA", "MIDW", "NE", "NW", "NY", "SE", "SW",
          "TEN", "TEX", "US48"}
JUMP_PCT = 0.10          # both series moving this much at once is a question, not a finding
MIN_PEAK = 1000          # MW; below this a single customer moves the whole grid
A, B = "2019", "2025"    # the same window for every grid, so the comparison is a comparison

NAMED = {
    "PJM": "contains Northern Virginia",
    "CISO": "California ISO",
    "ERCO": "ERCOT -- Texas",
    "AZPS": "Phoenix",
    "SOCO": "Georgia",
    "MISO": "midwest",
    "BPAT": "Bonneville",
    "SWPP": "SPP -- plains",
    "TVA": "Tennessee Valley",
    "DUK": "Duke Carolinas",
    "ISNE": "ISO New England",
    "NYIS": "New York ISO",
    "SC": "Santee Cooper",
    "WACM": "WAPA Rocky Mountain",
    "TEPC": "Tucson",
    "PSEI": "Puget Sound",
    "FPL": "Florida Power & Light",
    "PACE": "PacifiCorp East",
}


def jump(years):
    """The FIRST year a grid rose in both trough and peak at once, or None.

    Returns the first only; WACM has two, in 2022 and again in 2023. The charts use this to
    mark a grid as unexplained, never to exclude it -- see the module docstring for why the
    annexation reading did not survive its own test.
    """
    ks = sorted(years)
    for p, q in zip(ks, ks[1:]):
        a, b = years[p], years[q]
        if (b["trough"] / a["trough"] - 1 > JUMP_PCT
                and b["peak"] / a["peak"] - 1 > JUMP_PCT):
            return q
    return None


def rows(path=CACHE):
    """One record per balancing authority, over the same window, with its step flagged."""
    sh = json.load(open(path))["shape"]
    out = []
    for ba, y in sh.items():
        if ba in REGION or A not in y or B not in y:
            continue
        if y[B]["peak"] < MIN_PEAK:
            continue
        p = y[B]["peak"] / y[A]["peak"] - 1
        t = y[B]["trough"] / y[A]["trough"] - 1
        out.append({"ba": ba, "peak_growth": p, "trough_growth": t, "gap": t - p,
                    "peak_gw": y[B]["peak"] / 1000, "jump": jump(y),
                    "ratio_a": y[A]["ratio"], "ratio_b": y[B]["ratio"],
                    "note": NAMED.get(ba), "years": y})
    out.sort(key=lambda r: -r["gap"])
    return out


def main():
    r = rows()
    st = [x for x in r if x["jump"]]
    print(f"\n  {len(r)} balancing authorities, peak above {MIN_PEAK/1000:.0f} GW, "
          f"{A} to {B}")
    print(f"  {len(st)} have a year where trough AND peak both rose over "
          f"{JUMP_PCT:.0%} -- cause unresolved\n")
    print(f"  {'BA':<7}{'peak growth':>13}{'trough growth':>15}{'gap':>8}"
          f"{'peak GW':>10}  jump  what it is")
    for x in r:
        print(f"  {x['ba']:<7}{x['peak_growth']:>+13.1%}{x['trough_growth']:>+15.1%}"
              f"{x['gap']:>+8.1%}{x['peak_gw']:>10,.1f}  "
              f"{x['jump'] or '  . ':<5} {x['note'] or ''}")
    clean = [x for x in r if not x["jump"]]
    import statistics
    print(f"\n  median gap, all {len(r)}: {statistics.median(x['gap'] for x in r):+.1%}")
    print(f"  median gap, the {len(clean)} without a joint jump: "
          f"{statistics.median(x['gap'] for x in clean):+.1%}")
    top = sorted(clean, key=lambda x: -x["gap"])[:6]
    print(f"  largest gaps without a joint jump: "
          + ", ".join(f"{x['ba']} {x['gap']:+.1%}" for x in top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
