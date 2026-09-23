# The balancing authority cannot see compute either, and it fails differently

Measured 2026-09-23, on the successor test the falsifier note pre-registered: *"If BA-level
load growth is also uncorrelated with compute presence, then this register cannot see compute
at any resolution it publishes, and that becomes the finding."*

It does not fail by being uncorrelated. It fails by being **indistinguishable from something
else**, which is a different and more useful kind of failure, because it names what would have
to be measured instead.

## The test

A data centre is a flat 24/7 load. Add L megawatts of it to a grid whose overnight trough is
T and afternoon peak is P: both rise by L, so the trough grows by L/T and the peak by only
L/P. Since T < P always, the trough must grow faster. The gap between those two growth rates
is the signature, and it needs no facility directory at all -- only hourly demand, which every
US balancing authority is obliged to report.

Read from `EBA.{BA}-ALL.D.HL`, the **local-time** twin. In UTC an American calendar day begins
around 7pm local, which splits every night across two days and makes a daily minimum
meaningless. Trough and peak are the median daily minimum and maximum across the year.

## It fires where it should

| grid | peak growth 2019-2025 | trough growth | gap | implied flat load |
| --- | --- | --- | --- | --- |
| **PJM** (contains Northern Virginia) | +2.8% | **+6.0%** | **+3.2 pts** | **about 10 GW**, 9.6% of peak |
| ERCOT (Texas) | +28.4% | +30.5% | +2.1 pts | 2.6 GW |
| MISO (midwest) | +1.4% | +1.7% | +0.3 pts | 0.8 GW |

PJM's implied flat load is the largest of any American grid in absolute terms, and it is not
an artefact of the endpoints: the gap opens in 2023 and holds. Nor is it a utility joining
PJM, which would step both series in one year; PJM's is a slope.

## And it fires just as hard on a grid with no compute story

| grid | peak growth | trough growth | gap | what is actually happening |
| --- | --- | --- | --- | --- |
| **CISO** (California) | **+0.2%** | +6.0% | **+5.8 pts** | consumption **fell 5.9%** over the decade |

Rooftop solar never appears in generation data at all. It appears as demand that did not
happen, in the middle of the day, which suppresses the recorded peak and leaves the overnight
trough untouched. **From the shape alone, suppressed daytime demand and added flat load are
the same picture.** California's gap is larger than PJM's.

There is a partial discriminator -- flat load raises *both* halves of the day, so it moves a
grid right as well as up, while suppressed daytime demand moves it straight up -- and figure 3
draws exactly that. It is a reading of direction, not a correction, and it cannot be
quantified here, because the confounder is invisible in this dataset by construction.

## Size does not rescue it

Among the **8 US grids peaking above 20 GW, the whole range of gaps is -5.1 to +5.8 points**,
and PJM's +3.2 is the fourth largest in absolute value inside it, behind CISO, Southern and
Florida Power & Light. Handed the gap without the name, nobody picks PJM out.

The five largest gaps in the country belong to grids of 1.4 to 4.8 GW -- small enough for one
industrial customer or one metering change to move the whole number. But this is **not** a
clean "small is noisy" story: |gap| against log grid size is **r = -0.28**, and the spread is
28.9 points in the smallest band, 7.3 in the 6-to-20 GW band, and 11.0 points again above it.

## Two things checked and not confirmed

**Five grids have a year where trough and peak both rose over 10% at once.** A utility joining
the balancing authority would look exactly like that, so the obvious test is whether some
other authority lost matching load in the same year. **It did not.** WACM gained about 1.35 GW
across 2022-2023; the largest neighbouring fall is PSCO at roughly 0.35 GW, and WAUW, NWMT,
PACE and BPAT are flat. Santee Cooper's 2021 jump has no matching fall either. These are
marked in the figures and not explained.

ERCOT trips the same flag in 2022 on what is plainly real Texas growth, which is why the flag
marks a question rather than an answer.

**Utility-scale solar share does not stand in for the rooftop confounder.** Solar generation
share change correlates with the shape change at r = +0.47 across the 14 EIA *regions* but
only **+0.03** across the 52 balancing authorities -- because `NG.SUN` is metered generation
and the thing doing the work is not metered at all.

> **Correction, same day.** This note originally said rooftop solar was unavailable in this
> project's data. It is unavailable in **EBA**. EIA publishes a modelled estimate per state in
> **ELEC**, as `ELEC.GEN.DPV-{ST}-99.Q`, quarterly from 2016. It was then tested against the
> forecast-skill decline in `forecast-scope-and-skill.md` and figure 6, where it fails --
> California's five balancing authorities all carry the same 14.5% and their outcomes span
> 0.71. A state-level variable cannot resolve within-state variation, so it could not have
> rescued the load-shape test here either. The claim that it was unavailable was wrong; the
> conclusion that drew on it survives for a different and better reason.

## What this closes, and what it leaves

Two independent proxies have now failed on Q2: the facility directory at r = +0.03, and load
shape here. **The public US electricity record does not identify where compute load has
landed at any resolution it publishes.** That is the answer to Q2, and it is worth more than
a weak correlation would have been, because it is checkable and it tells the next person
where not to look.

What still predicts growth is **electricity per head at Pearson +0.64** -- a measure of how
electrified a place already was, not of what it attracted. See [q2-falsifier-fired.md].

**What would settle it** is a measure with the load attached to a customer rather than to a
grid: utility interconnection queues with load type, state industrial-rate filings, or a
single balancing authority publishing a data-centre class. Dominion Energy Virginia would be
the natural place, and **it is not a balancing authority in EBA at all** -- `EBA.DOM-ALL.D.H`
does not exist, and `SCEG` is Dominion Energy *South Carolina*, a different company in a
different state. The best available positive control for this test does not exist in the
dataset the test runs on.

## Receipts

- `artifacts/scripts/matched.py` -- one pass over the 691 MB archive for three hourly measures
- `artifacts/scripts/shape.py` -- the field, the size bands, the joint-jump flag
- `artifacts/charts/3-flatload.svg` -- peak growth against trough growth, with the diagonal
- `artifacts/charts/4-size.svg` -- the same gap against grid size, which is what closes it
