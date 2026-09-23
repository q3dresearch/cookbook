# Superseded figures

Kept, not deleted: the larder is not under version control, so a removed figure is gone. Each
entry says what replaced it and why, because "we cut this" is only useful with the reason.

**Only the persuasive ones get a file.** A chart that was merely hard to read is clutter and
is described here without being preserved. A chart that looked completely sound and was wrong
is the one worth being able to open.

---

## `chart-13-mismatched.py` / `13-location-mismatched.svg`  — kept, with a file

**Replaced by `scripts/chart-13-location.py`.** This is the only figure in this recipe
preserved as an artifact, because nothing about it looks broken.

The marks are real states. The histograms are the real counts. The regression numbers are
correctly computed. The correlation is correctly computed **from what it was given** — and
what it was given was two axes measured over different periods:

| axis | window it used |
| --- | --- |
| average retail price | **2022 onward** |
| year-over-year swing in that price | **2010 onward** |

Neither window is wrong on its own, and the mismatch is invisible in the drawing.

**What it cost.** It reported **r = +0.32** between price and swing, 33 of 49 states on the
cheap-and-steady to dear-and-swingy diagonal, and a between-region story built on top:
Northeast +0.30, Midwest +0.24, South +0.16, West −0.03.

Matched to 2018–2025 on both axes it is **+0.18**, and within each region +0.09, +0.09, −0.06
and −0.08 — nothing anywhere. Moving only the swing axis accounts for most of it:

| x | y | r |
| --- | --- | --- |
| price 2022+ | swing 2010+ | **+0.32** |
| price 2022+ | swing 2018+ | +0.22 |
| price 2018+ | swing 2010+ | +0.28 |
| price 2018+ | swing 2018+ | **+0.18** |

The long swing window includes 2011–2014, when the expensive Northeastern states also
happened to be the moving ones. **Two axes on different windows will find a relationship
between the windows.**

**Its title was false too.** *The Northeast pays double and swings hardest* — on matched years
the South swings 0.065 against the Northeast's 0.064.

**What survived the fix**, unchanged or stronger: the location result (adjusted R² 0.346 →
0.803 on price, 0.213 → **0.182** on the swing, where it now makes the model *worse*), the
Shapley split, and every region's price ordering.

**How it was caught.** A reader asked what a marker was: *"is each marker every region by
every timing? is this a good comparison or should we isolate the time component?"* Nothing in
the audit tooling looks at whether two axes cover the same period.

---

## The stacked-marginal version of the same plate — described only

**Replaced in the same file.** The marginal histograms stacked the four census regions
instead of overlaying them at 0.3 opacity.

Not wrong, but it answered the wrong question. A stack moves every group's baseline, so a
reader can see each region's **share of a bin** and cannot see its **distribution**. The claim
on the plate is about where each region *lives* along an axis, which is a statement about its
own shape. Overlaid from a shared baseline, the Northeast's spread across the upper half of
the price range became legible; stacked, only its slice of each bar was.

No file kept: it is the same data and the same script with one branch changed, and the defect
is a design point rather than a wrong number.

---

## The first two versions of figure 5 — described only

**Both replaced by `scripts/chart-5-forecast.py`.**

**Version one scored forecasts on inter-quartile range.** The IQR is the middle 50% of hours,
so it ignores the tail — the entire operational point of a demand forecast — and does not
normalise for how hard the grid is. Replaced by a skill score against a same-hour-last-week
persistence baseline, which does both.

**Version two was a scatter of skill against difficulty for one year.** The two are
uncorrelated at **r = −0.02**, so it spent a whole axis saying "no relationship". Spending
that axis on time instead surfaced California's four-year decline, Duke Energy Florida's
undated offset and the shared 2021 step in LGEE and PNM — none of which a single year can
show.

Neither is preserved: the first was a bad statistic and the second was an empty axis, and both
are fully described by the numbers above.

---

## The log-size scatter version of figure 4 — described only

**Replaced in `scripts/chart-4-size.py`.** It plotted the trough-versus-peak gap against log
grid size with three overlapping layers — per-grid dots, per-band p10–p90 bars and a dashed
box — and a y-axis only readable if you had memorised figure 3. A reader said *"dont
understand 4."*

Redrawn as one row per size band it reads directly: the spread collapses from 28.9 points in
the smallest band to 11.0 in the largest. Not preserved — it was unreadable rather than
convincing, which is the test.

---

## The pre-Shapley version of figure 12 — described only, and it carried a real bug

**Replaced by the Shapley decomposition in `scripts/chart-12-price.py`.** Two separate faults.

**It showed standardised regression coefficients**, which answer "move this one standard
deviation and hold the rest still" — an effect, not an importance. Generation shares sum to
one, so with the full set the coefficients blow up: gas −1.13, coal −1.52, hydro −1.19, every
one large and negative.

**And its denominator was wrong.** ELEC's fuel codes overlap — `AOR` already contains wind,
solar, geothermal and wood, `TSN` is `SUN` plus `DPV`, and `ALL` sits in the same namespace as
its own parts. Summing every code present gave a denominator roughly **2.3× the real one, by a
different factor in each state**, so it distorted every share unevenly rather than scaling them
alike. Every percentage it printed was plausible and none was right.

Not preserved as a file, because reproducing it would mean re-introducing the bug into
`price.py`. The fix is a declared non-overlapping basket checked against the published total,
and `price.py` now prints that ratio on every run: median **0.9996**.

---

## Rebuilding any of these

`chart-13-mismatched.py` imports the live modules in `../scripts` and writes beside itself:

    python3 chart-13-mismatched.py

It reads the same `artifacts/data/price.json` as the live figure, so if that cache is rebuilt
this plate changes with it. That is deliberate — it is a record of a *reading*, not of a
frozen dataset.
