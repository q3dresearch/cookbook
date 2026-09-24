#!/usr/bin/env python3
"""What a neuroimaging dataset IS predicts its reuse. What is in it barely does.

    python3 chart-1-modality.py

OpenNeuro holds 1,891 public datasets under CC0, deposited voluntarily. Scanner time costs
hundreds of dollars an hour, so the question worth asking of a voluntary archive is what
happens to a dataset after somebody publishes it -- and specifically, whether anything the
depositor controls predicts it.

**Almost nothing does.** A model of everything a depositor chooses -- subjects, sessions,
tasks, modality count, whether a paper DOI is attached, whether a funder is named -- explains
**R2 = 0.072** of the spread in downloads per year. Adding one variable the depositor does not
really choose, *what instrument produced the data*, takes it to **0.118**: two thirds more
explained variance from one column. EEG-against-MRI is the largest single coefficient at
**+0.22**, just ahead of subject count at +0.19.

**Total size and file count are left out of that model on purpose.** They correlate with each
other at **r = +0.74**, and fitted together they split one signal into a spurious opposing
pair -- +0.22 for files against -0.19 for size -- neither of which is separately
interpretable. Dropping both moves EEG only from +0.23 to +0.22.

**Age-matched, an EEG dataset is downloaded 2.2x as often as an MRI one and a PET dataset
2.4x**, at a median size of 18.0 GB against MRI's 12.1 -- so it is not that the smaller files
are cheaper to take. MEG, at 83.5 GB, sits with MRI.

**Why the age floor.** Downloads are front-loaded: the median dataset earns 37.1 a year in its
first three months and 11.8 a year after four. A per-year rate is therefore not age-invariant,
and a ranking that mixes ages ranks the calendar. Everything here is restricted to datasets at
least a year old, which is 1,462 of 1,859.

**Two things this is not.** It is not scarcity -- EEG deposits grew from 10 a year to 90 while
per-dataset downloads rose rather than fell, so the modality is not simply under-supplied.

**And it is not size, which predicts nothing at all.** Log size against log downloads per year
is **+0.11 across all modalities, +0.04 within MRI and +0.02 within EEG**; by decile the
medians run 13.0, 15.7, 22.3, 12.4, 12.2, 15.3, 13.1, 15.3, 13.6, 21.1 -- flat, with no trend
and no bend. An earlier version of this plate reported a **U-shape** from four quartiles, in
which the smallest and largest quarters out-downloaded the middle. At ten bins it dissolves,
and a quadratic fit buys R2 0.0014 to 0.0067: half a percent. Four bins invited a curve and
got one.

**The distributions overlap heavily and that is not a defect.** An EEG dataset at the tenth
percentile is downloaded less than an MRI dataset at the ninetieth; the claim is about where
the middle of each sits, not about separation. What would break it is the medians coinciding,
or a depositor-controlled variable carrying a larger coefficient than the instrument -- and
the largest of those is subject count at +0.19 against EEG's +0.22.

**A download is not a citation.** It counts somebody taking the data, including the depositor,
a crawler that OpenNeuro's analytics did not filter, and anyone who looked and discarded. It
is the only reuse signal this archive publishes and it is treated as a floor on interest
rather than a measure of scientific use.
"""
import math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import modality, plate                                                   # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "1-modality.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
XLO, XHI = 0.25, 4000.0


def main():
    rows = modality.rows()
    by = {}
    for r in rows:
        by.setdefault(r["mod"], []).append(r)
    base = statistics.median(x["dl_yr"] for x in by["mri"])
    order = sorted(by, key=lambda k: -statistics.median(x["dl_yr"] for x in by[k]))

    W = 1160
    H = 300 + 66 * len(order) + 132
    s = plate.open_svg(
        W, H, "What a neuroimaging dataset IS predicts its reuse. What is in it barely does.",
        subtitle=f"{len(rows):,} OpenNeuro datasets at least a year old. Each mark is one "
                 f"dataset; the rule is the modality's median. Downloads per year since "
                 f"publication.")
    fr, y0 = plate.frame(
        W, 86,
        who="anyone about to collect and deposit a neuroimaging dataset, or a funder asking "
            "what reuse a deposit mandate buys",
        decide="whether anything you control at deposit changes how much the data gets used",
        wrong="the modality medians sit on top of each other, or dropping the instrument "
              "from the model costs no explained variance")
    s += fr

    AX, AW = 244, W - 470
    lx = lambda v: AX + AW * (math.log10(min(max(v, XLO), XHI)) - math.log10(XLO)) / (
        math.log10(XHI) - math.log10(XLO))
    top = y0 + 78
    bot = top + 66 * len(order) - 26
    for g in (1, 10, 100, 1000):
        s.append(f'<line x1="{lx(g):.1f}" y1="{top-22:.1f}" x2="{lx(g):.1f}" '
                 f'y2="{bot:.1f}" stroke="{GRID}"/>')
        s.append(txt(lx(g), top - 30, f"{g:,}", size=9, fill=MUTED, anchor="middle"))
    s.append(f'<line x1="{lx(base):.1f}" y1="{top-22:.1f}" x2="{lx(base):.1f}" '
             f'y2="{bot:.1f}" stroke="{RULE}" stroke-width="1.4" stroke-dasharray="4 3"/>')
    s.append(txt(AX - 4, top - 50, "downloads per year since publication  (log scale)",
                 size=10, fill=INK2))

    for i, k in enumerate(order):
        g = by[k]
        y = top + 66 * i + 16
        med = statistics.median(x["dl_yr"] for x in g)
        lead = k in ("eeg", "pet")
        col = RED if lead else (SLATE if k == "unknown" else BLUE)
        s.append(txt(AX - 20, y + 4, modality.NICE.get(k, k), size=12,
                     fill=INK if lead else INK2, anchor="end", weight="600"))
        s.append(txt(AX - 20, y + 19, f"{len(g):,} datasets", size=9, fill=MUTED,
                     anchor="end"))
        v = sorted(x["dl_yr"] for x in g)
        s.append(f'<line x1="{lx(v[0]):.1f}" y1="{y:.1f}" x2="{lx(v[-1]):.1f}" '
                 f'y2="{y:.1f}" stroke="{FAINT}" stroke-width="5" stroke-opacity="0.28"/>')
        for x_ in g:
            s.append(f'<circle cx="{lx(x_["dl_yr"]):.1f}" cy="{y:.1f}" r="2.6" '
                     f'fill="{col}" fill-opacity="0.22"/>')
        s.append(f'<line x1="{lx(med):.1f}" y1="{y-13:.1f}" x2="{lx(med):.1f}" '
                 f'y2="{y+13:.1f}" stroke="{col}" stroke-width="2.6"/>')
        s.append(txt(W - 196, y + 4, f"{med:,.1f}", size=11.5, fill=col, weight="700"))
        s.append(txt(W - 152, y + 4, f"{med/base:,.1f}x", size=11, fill=col,
                     weight="700" if lead else "normal"))
        s.append(txt(W - 108, y + 4, f"{statistics.median(x['size'] for x in g)/1e9:,.0f} GB",
                     size=9.5, fill=MUTED))
    s.append(txt(W - 196, top - 30, "median", size=9, fill=MUTED))
    s.append(txt(W - 152, top - 30, "vs MRI", size=9, fill=MUTED))
    s.append(txt(W - 108, top - 30, "median size", size=9, fill=MUTED))
    s += halo(lx(base) + 6, top - 40, "MRI median", size=9, fill=MUTED)

    s += halo(AX - 20 - 200, bot + 32, "everything a depositor chooses, together, explains "
              "R2 = 0.072 of this spread; adding the instrument takes it to 0.118",
              size=10.5, fill=INK2, weight="700")
    s += halo(AX - 20 - 200, bot + 47, "downloads are front-loaded -- 37.1 a year in the "
              "first three months against 11.8 after four years -- so everything here is "
              "age-matched at a year", size=10.5, fill=INK2)
    s += halo(AX - 20 - 200, bot + 65, "the unresolved row has a median size of 0.0 GB and 0 "
              "subjects: those are mostly empty deposits, not mislabelled ones", size=10.5,
              fill=SLATE)

    foot = (
        "OpenNeuro GraphQL API, no key, fetched 2026-09-23; robots.txt permits everything. "
        "1,891 of a reported 1,897 datasets -- six return null through four retries and are "
        "counted, not dropped. Modality is rebuilt from the modalities list because "
        "primaryModality holds a BIDS suffix or nothing on 93 rows. CAVEAT: a download is not "
        "a citation; it counts anyone taking the data, including the depositor and unfiltered "
        "crawlers.")
    ln = len(wrap(0, 0, foot, size=10.5, fill=MUTED, chars=174, leading=14))
    fy = H - 20 - 14 * ln
    s.append(f'<line x1="28" y1="{fy-18:.1f}" x2="{W-28}" y2="{fy-18:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy, foot, size=10.5, fill=MUTED, chars=174, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    for k in order:
        g = by[k]
        print(f"    {modality.NICE.get(k,k):<12}{len(g):>5}  "
              f"{statistics.median(x['dl_yr'] for x in g):>7,.1f} dl/yr  "
              f"{statistics.median(x['dl_yr'] for x in g)/base:>5,.1f}x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
