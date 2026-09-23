# Scoring a forecast, and what predicts how hard the grid is

Measured 2026-09-23. Every US balancing authority publishes a day-ahead demand forecast
(`DF`) beside the demand it recorded (`D`), hourly, 2019 to 2026 at about 99% coverage.
Anyone can difference them. Almost every way of doing so is wrong.

## The first attempt was wrong, and a reader said why

The first version scored each operator by the **inter-quartile range** of forecast-over-actual.
Two objections, both correct:

- **The IQR is the middle 50% of hours.** It ignores the tail, which is the entire operational
  point of a demand forecast. A grid that is tight four days in five and catastrophically
  wrong on the fifth scores well.
- **It does not normalise for difficulty.** A grid whose load swings wildly is genuinely harder
  to forecast, so a raw error spread partly measures the grid rather than the forecaster.

## What replaced it

**Skill against a naive baseline.** The baseline is persistence at a 168-hour lag — the same
hour one week earlier — which carries the weekday and the time of day for free.

    skill = 1 - MAE(forecast) / MAE(same hour last week)

1.0 perfect, 0.0 no better than repeating last week, negative worse than doing nothing. This
normalises difficulty automatically and needs no separate volatility index: a volatile grid
has a large baseline error, so beating it is what counts.

**Difficulty** is then the baseline's own error as a share of mean demand — **4.5% to 34.1%**
across 53 grids, median 9.4%.

## Scope is separated from skill, not averaged with it

Every statistic is computed twice: once on the published forecast, once on the forecast
rescaled by that year's median actual-over-forecast ratio. The gap is the **scope penalty**.

| grid | scope ratio | raw skill | corrected skill |
| --- | --- | --- | --- |
| Duke Energy Florida (FPC) | 0.766, in 100.0% of hours | **−0.94** | **+0.73** |
| WAPA Rocky Mountain (WACM) | 0.842 | −1.34 | +0.40 |
| Puget Sound (PSEI) | 0.690 | −3.37 | −1.45 |
| Arizona Public Service | 0.917 | −0.05 | +0.07 |

**Raw scoring calls 9 of 53 grids worse than persistence. Corrected, it is 5.** Duke Energy
Florida is not an inaccurate forecaster; it publishes a precise forecast of a different
quantity beside a series it was never meant to match.

**Skill against difficulty is r = −0.02.** Operators of hard grids are not worse at forecasting
them. Skill is a property of the forecaster.

**California is the one that survives correction.** CISO sits on the second easiest grid in the
country (baseline error 6.10%) and scores **−0.18 corrected**. Unresolved here; the likeliest
candidate is a different published product, which is Duke Energy Florida's fault in a form no
single scale factor removes.

## Tails

The median hour and the 99th percentile hour rank operators differently. The ratio p99/p50 runs
**3.6× to 36.1×**, median 5.7×.

| grid | p50 | p99 | ratio |
| --- | --- | --- | --- |
| Southern (SOCO) | **0.39%**, best of 53 | 14.05% | **36.1×** |
| Southwest Power Pool | 5.33% | 19.22% | **3.6×** |
| CISO | 4.75% | 27.58% | 5.8× |
| PJM | 2.74% | 10.50% | 3.8× |

**The peak, with the size split that stops it being overclaimed.** After correcting each
forecast to be right on the median hour, **44 of 53 still come in low across the top 5% of
demand hours** — the operationally dangerous direction. But: **13 of 13 grids under 1 GW, and
4 of 6 above 20 GW**, with median bias falling from −3.05% to −0.24%. PJM is −0.46%, ERCOT
−0.12%. At the sizes that matter it is close to nothing.

## What predicts difficulty

Asked: does grid mix, renewable share, temperature, industry mix, population or data-centre
presence predict forecast volatility? Marginal correlations first, then all five in one
standardised model (n=41, R² 0.65).

| predictor | source | marginal r | in the joint model |
| --- | --- | --- | --- |
| load flatness, trough over peak | EBA | −0.72 | **−0.49** |
| data centres per million people | PeeringDB + SEDS | −0.60 | **−0.36** |
| wind + solar share of generation | EBA | −0.26 | −0.14 |
| seasonal amplitude (temperature proxy) | EBA | +0.40 | +0.12 |
| grid size, log GW | EBA | −0.12 | +0.05 |
| industrial share of state electricity | SEDS | −0.34 | not carried, +0.67 with flatness |
| industrial electricity price | SEDS | +0.03 | — |
| state population, log | SEDS | +0.25 | — |
| **raw** PeeringDB facility count, log | PeeringDB | **−0.03** | — |

Without the data-centre variable, on all 53 grids: **flatness −0.80, nothing else above 0.09,
R² 0.63.**

**Generation mix does not predict demand-forecast difficulty**, and that is the right answer
rather than a disappointing one — the series forecast is *demand*, not net load, and does not
know what is generating it.

**The temperature proxy is the instructive failure.** Seasonal amplitude is a real
temperature-sensitivity measure with a respectable +0.40 marginal correlation, and it
contributes nothing once flatness is in: a weather-driven grid *is* a peaky grid, and flatness
measures that with less noise.

**Data centre density is the one that survives**, correlated with flatness at only +0.42. It is
the first time in this recipe that PeeringDB predicts anything, after r = +0.03 against state
electricity growth and nothing in figures 3 and 4.

**And it gets the strongest caveat on the page.** 41 single-state balancing authorities, a
directory nobody is obliged to file into, and only per capita — the raw count is −0.03.
Facilities per million may be reading urbanisation or economic structure rather than compute.
**It is a lead, not a finding**, and the way to settle it is a measure with load attached to a
customer rather than to a grid.

## What was not fetched

No temperature series. NOAA station data would need a station-to-balancing-authority mapping
and a fetch; the seasonal-amplitude proxy is computed from demand itself and is named as a
proxy everywhere it appears. If the proxy had survived the joint model this would be the next
thing to do — it did not, so it is recorded rather than pursued.

## Receipts

- `artifacts/scripts/skill.py` — the fold: seven years, persistence baseline, scope
  correction, percentiles, peak bias, per year
- `artifacts/scripts/predict.py` — the predictor join and the standardised model
- `artifacts/charts/5-forecast.svg`, `6-tail.svg`, `7-drivers.svg`
