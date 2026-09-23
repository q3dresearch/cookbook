# The grid record answers every question twice

US state energy 1960–2024, every US balancing authority's hourly demand and forecast
2019–2026, quarterly state electricity prices 2001–2026, the PeeringDB facility directory,
and NREL's cost baseline. 1.0 GB of source, 3.1 MB of committed receipts, no API key
anywhere.

## The background

Four registers, all reachable without a key, and they exist for different reasons — which is
why they disagree.

**SEDS** is EIA's State Energy Data System: every state's energy by fuel and sector, annually
since 1960. Federal energy policy needs a consistent denominator, and this is the only series
long enough to ask whether electrification is still happening.

**EBA** is the Hourly Electric Grid Monitor. Every balancing authority reports demand, a
day-ahead forecast of it, generation by fuel, interchange, and the carbon in the power its
customers consume — every hour. The obligation is operational, not statistical: the grid needs
these numbers to run. That is why they are hourly and timely, and also why they carry an
operator's boundaries rather than a state's.

**ELEC** is EIA's electricity series: average retail price, generation by fuel, retail sales,
fossil fuel cost and a modelled estimate of **rooftop solar**, by state and quarter since 2001. It is the only price in this recipe,
and it is a **regulated retail** price — set by a regulator, lagging its inputs, carrying
network charges that have nothing to do with generation.

**PeeringDB** is a voluntary directory of interconnection facilities. Nobody is obliged to
file, and what that does to it is most of figures 3, 4 and 7.

**ATB** is NREL's Annual Technology Baseline: capital cost, O&M, capacity factor and levelised
cost for twenty generation and storage technologies. **It is a model output, not a register** —
nobody paid these prices — and 2021–2023 are the vintage year's estimates while 2024–2050 are
projections, with nothing in the file marking the boundary.

## The question this set was built to answer

How much of the energy a civilization uses can be delivered as electricity, how much new
electricity is being absorbed by data centres and crypto mining, whether those loads run on
clean power, and what it costs to bring more capacity online.

**Most of it is answered. The compute question is not, and why it is not turned out to be the
most useful thing here.**

## What the figures found

**Electrification tripled and then stopped.** Electricity at the meter went from 6.0% of US
end-use energy in 1960 to 16.2% by 2000 — and 18.0% in 2024. Twenty-four years moved it 1.8
points. Counted on primary energy it looks like electrification has been *falling* since 2000.
It has not: generation got 32% more efficient, so the waste in the numerator shrank faster
than the useful part grew. Either basis alone supports a headline the other contradicts.

**A grid's published fuel mix is not what its customers consume.** Puget Sound Energy
generates 40% carbon-free and delivers at 133 kg CO₂ per MWh. Northwestern generates *more*
carbon-free — 43% — and delivers at 582, four times the carbon, because it exports the clean
part. Ten of forty grids generate under 75% of what they consume, so their advertised
renewable share describes a minority of what they deliver.

**Three independent proxies failed to find where compute load landed.**

- *Facility counts.* PeeringDB density against state electricity growth 2015–2024: **r = +0.03**.
  California holds the largest compute concentration in the country and its consumption **fell
  5.9%**. Pre-registered as a falsifier; it fired.
- *Load shape.* Flat 24/7 load must lift a grid's overnight trough faster than its peak. PJM,
  which contains Northern Virginia, shows exactly that: **+3.2 points, about 10 GW of implied
  flat load.** California shows **+5.8** on a grid whose consumption fell — rooftop solar
  suppresses the recorded peak and never appears in generation data at all. Among the 8 grids
  above 20 GW the whole range is −5.1 to +5.8.
- *Forecast surprise.* A grid absorbing unexpected load should under-forecast. 28 of 53 do,
  which is a coin toss.

**And the answer changes if you look at one year or seven.** California's skill fell from
**+0.69 in 2021 to −0.18 in 2025** — four consecutive years, the largest decline of any grid
above 5 GW — while its scope ratio slid 1.014 to 0.954. Its published forecast is drifting
further below its recorded demand every year, which is what behind-the-meter solar does to a
demand series. A single-year snapshot called it a bad forecaster; the series calls it a
diverging one. Meanwhile Duke Energy Florida's 0.766 offset is **flat for seven years** —
a permanent mismatch, not an instrument that changed — and LGEE and PNM both step in 2021,
which is what a reporting-standard change looks like rather than two coincidences. **In any
one year all three read as the same fault.**

**And the western decline does not have the explanation it looks like it has.** Mountain is
the only census division with a clearly negative median skill change, at **−0.095**; every
other division improved. The obvious mechanism is rooftop solar, which turns recorded demand
into a net quantity the operator never metered — and the decliners are California, Oregon,
Arizona and Nevada. **It fails on an internal control.** EIA estimates rooftop PV per *state*,
so California's five balancing authorities all carry the same **14.5%** — and their skill
changes run from **−0.71 at CISO to −0.00 at Los Angeles**. Among grids above 2 GW that
within-state spread is **half the entire field's range**. A variable constant inside a state
cannot explain variation that large inside one, and in a joint model rooftop drops to −0.14,
and to +0.03 once CISO alone is removed. CISO is its own story, not a regional one.

**But the forecast data answered a different question well.** Differencing a published
day-ahead forecast against published demand mixes two faults that imply opposite remedies.
Duke Energy Florida forecasts **0.766 of its own demand in 100.0% of 2025's hours** — scored
raw that is −0.94 against a naive baseline, second worst in the country; rescaled to the right
level it is **+0.73, inside the top ten**. Raw scoring calls 9 of 53 grids worse than
repeating last week; corrected, 5. And **skill against difficulty is r = −0.02**: operators of
hard grids are not worse at forecasting them.

**The median hour tells you nothing about the bad hour.** Southern Company has the best typical
forecast hour of the 53 — **0.39%** — and a 99th percentile of 14.05%, a **36-fold** tail. SPP's
median is thirteen times worse and its tail is **3.6-fold**. The ratio runs 3.6× to 36.1× with
a median of 5.7×, a ten-fold spread the median cannot see.

**What makes a grid hard to forecast is one variable, and it is not the one people reach for.**
Taken alone, seasonal amplitude (+0.40), renewable share (−0.26) and grid size (−0.12) all look
relevant. In one model they go to +0.12, −0.14 and +0.05, while **load flatness keeps its whole
effect at −0.49** (−0.80 without the data-centre variable, on all 53). Generation mix does not
predict demand-forecast difficulty — the series being forecast is demand, not net load.

**And here compute finally shows up.** Data centres per million people holds **−0.36** alongside
flatness, correlated with it at only +0.42. Compute makes a grid easier to forecast, which is
what flat load should do. It rests on 41 single-state grids and a voluntary directory, and only
per capita — the raw facility count is **−0.03**. It is a lead, not a finding.

**On price, generation mix and demand mix answer different questions and do not cross over.**
Measured as Shapley shares of explained variance — averaged over every order the predictors
could enter in, which is the honest statistic when the shares sum to one — **gas owns 29% of
the price-volatility model** and coal 23%, with the generation mix taking **94%** of it
between them. On the price *level* it inverts: the **industrial share of retail sales owns
47%**, and the demand mix takes 55%. A state's own gas *cost* volatility predicts neither
(r = +0.03): gas is a national commodity, so what differs between states is exposure to it,
not the price they pay.

**And location settles the rest — but only half of it.** Adding eight census-division
indicators to a model already holding six generation features and two demand features lifts
**adjusted** R² from **0.373 to 0.805** on the price level. On volatility, measured over the same
matched window, it moves **0.213 to 0.182** — after paying for the eight parameters it makes
the model *worse*. Drawn as the two margins of one scatter, the regions occupy different
parts of the price axis and sit on top of each other on the swing axis. A regional term is
real work on the level and decoration on the swing.

**The joint view adds a third thing neither margin shows: there is almost nothing there.**
Price and swing correlate at **r = +0.18**, and inside each region at +0.09, +0.09, −0.06 and
−0.08. A state being expensive tells you close to nothing about whether its price is stable.

**That number was wrong in a first version, because the two axes used different windows.** It
took the price level from 2022 onward and the swing from 2010 onward, and reported +0.32.
Matching both to 2018–2025 takes it to +0.18, and the change is in the swing axis: the full
window includes 2011–2014, when the dear Northeastern states also happened to be the moving
ones. **Two axes on different windows will find a relationship between the windows.**

**Collapsing time to one mark per state was then checked rather than assumed.** Volatility on
2011–2017 against 2018–2025 — disjoint halves — ranks the same states alike at **rho +0.62**,
which one shared national event cannot produce. But the *level* of that axis is
window-dependent: the median state moved 0.020–0.037 a year through 2020 and **0.086 in
2022**, and 2021–23 carries 34% of fifteen years of movement against an even share of 20%.
The ranking is durable; the number is a statement about a window containing a gas shock.

**There is no ATB cost of land-based wind. There are 120, spanning 23.5×** — $3.1 to $73.0 per
MWh in 2030, all correctly sourced. Biopower spans 1.2×. The spread is four explicit choices,
not a confidence interval, and **they do not rank the same way per technology**: wind moves
3.4× on siting and 1.2× on financing, nuclear 1.3× on financing and **1.02× on siting**.

**Nothing dispatchable has a levelised cost at all.** Natural gas publishes capital cost, O&M
and a heat rate — and **no LCOE and no capacity factor**. Neither does coal, nor either retrofit
family, nor any of the four storage technologies: **8 of 20, exactly the dispatchable ones**,
because both quantities need a dispatch assumption and a fuel price and ATB sets neither. Every
"solar is cheaper than gas" chart sourced here spliced the gas number in from elsewhere.

## Who it matters to

- **Anyone siting a load on a grid's advertised renewable share** — figure 2 says that number
  describes generation, and for ten of forty grids that is a minority of what they deliver.
- **Anyone about to quote a data-centre share of national electricity** — this recipe contains
  a written refusal to produce that number, and figures 3, 4 and 7 are what happens when you
  try to derive it honestly.
- **Anyone ranking grid operators on forecast error** — figures 5 and 6 say the published
  number confuses scope with skill, and that the median hour does not predict the bad one.
- **Anyone quoting a generation cost** — figure 8 says whether a single number is safe for that
  technology, and for wind and geothermal it is not.
- **Anyone comparing renewables against gas** — figure 10 says that comparison cannot be made
  inside the file it is usually sourced to.

## The figures, in order

| # | figure | what it settles |
| --- | --- | --- |
| 1 | `1-stall.svg` | Electrification tripled to 2000 and stalled; the apparent reversal since is generator efficiency |
| 2 | `2-imported.svg` | Own fuel mix against delivered carbon over matched hours — they disagree in both directions |
| 3 | `3-flatload.svg` | The flat-load signature fires at PJM and fires harder at California, where the cause is rooftop solar |
| 4 | `4-size.svg` | The same gap, one row per size band — PJM's +3.2 points is ordinary next to grids its own size |
| 5 | `5-forecast.svg` | Seven years of forecast skill and scope — California's four-year decoupling, and three faults that look identical in one year |
| 6 | `6-geography.svg` | Whether geography explains the decline — it is western, and rooftop solar is not the reason |
| 7 | `7-tail.svg` | The median hour against the 99th percentile — they rank operators differently |
| 8 | `8-drivers.svg` | What predicts forecast difficulty: flatness, and data-centre density independently |
| 9 | `9-cost-spread.svg` | How far apart the official cost numbers are — 23.5× for land-based wind |
| 10 | `10-cost-drivers.svg` | Which of the four cost choices moves the number, differently per technology |
| 11 | `11-cost-coverage.svg` | The eight technologies with no levelised cost, and why they are the dispatchable ones |
| 12 | `12-price.svg` | Shapley decomposition: what a state burns owns the volatility of its power price; what it sells owns the level |
| 13 | `13-location.svg` | Price against swing with both margins overlaid — location is nearly everything for the level and worse than nothing for the swing |

Figures 8 to 10 began as a separate recipe, `generation-cost`, and were merged here: they
serve the same objective and share the cost question with the buildout question.

## What is verified, and the bugs that shaped it

**Every figure rebuilds byte-identical across two separate processes** (`determinism.py`) and
passes `plateaudit.py`. All ten redraw from committed caches with the 1.0 GB of source absent.

**A coverage check caught a silent fold bug.** An earlier regex read fuel codes as exactly
three characters, dropping natural gas — a two-character code — from every balancing authority
and inflating every carbon-free share. The tell was ERCOT reporting 288 TWh of generation
against 488 TWh of demand. Generation total against demand total is now a standing check.

**A matched-hours bug survived one review.** Consumption-based CO₂ covers 87.5% of 2025's hours
while demand covers all of them. Dividing annual totals understated every grid's intensity by
**10.8% to 14.6%** — unevenly, so it moved the ranking too. `matched.py` sums both over their
intersection instead.

**Fourteen of the seventy EBA codes are regions, not balancing authorities.** `CAL` contains
`CISO`, `TEX` contains `ERCO`, `US48` contains everything, and nothing in the identifier says
so. A ranking that includes them compares containers against their own contents. They are
tagged in `shape.py` and excluded from every field.

**Abandoned rather than caveated.** `CO2.EM.{fuel}` would have given own-generation intensity
directly; ERCOT's coal series carries 4,436 hourly points in an 11,000-hour window and
intensities from it came out roughly twenty times too low. It is not used.

**Figure 5 has been rebuilt twice on reader criticism.** It first scored forecasts on
inter-quartile range — the middle 50% of hours, which ignores the tail and does not normalise
for difficulty. That was replaced by a skill score against persistence. It was then a scatter
of skill against difficulty for one year, and those two are uncorrelated at **r = −0.02**:
worth knowing, not worth an axis. Spending that axis on time instead is what surfaced the
four-year California decline, the undated Duke Energy Florida offset and the shared 2021 step.

**A claim in this recipe was wrong and is corrected rather than quietly fixed.** Figures 3 and
7 said behind-the-meter solar was absent from the data by construction. It is absent from
**EBA**. EIA publishes a modelled estimate per state in **ELEC**, `ELEC.GEN.DPV-{ST}`, and
figure 6 now uses it. The conclusion it supported survives, for a better reason: a state-level
variable cannot resolve within-state variation, so it could not have rescued the load-shape
test either.

**A coverage check caught a second silent fold bug, in the price data.** ELEC's fuel codes
overlap: `AOR` is *other renewables total* and already contains wind, solar, geothermal and
wood; `TSN` is all solar and equals `SUN` plus `DPV`; and `ALL` sits in the same namespace as
its own parts. Summing every code present gave a denominator **roughly 2.3× the real one, by
a different factor in each state** — so it distorted every share unevenly rather than scaling
them all alike. The fix is a declared non-overlapping basket checked against the published
total, and `price.py` prints that ratio on every run: median **0.9996**.

**Figure 12 was rebuilt on a reader's question — "can I read this as a Shapley plot?"** It
could not: it showed standardised regression coefficients. With the full set of generation
shares those coefficients blow up into nonsense — gas −1.13, coal −1.52, hydro −1.19, every
one large and negative — because the shares sum to one and the algebra has nothing to anchor
on. The exact Shapley decomposition over all 256 subsets is stable and sums to R² by
construction. The cost is the sign, which is printed beside each bar instead.

**Rooftop solar is excluded from the price models, and the reason is causal.** Included, it
takes 56% of the level model. But electricity price is enormously persistent (2010–14 against
2022+, **r = +0.93**), expensive states adopted more rooftop (**+0.69**), and controlling for
the earlier price collapses rooftop's effect on volatility from +0.24 to **+0.06**. It is a
consequence of dear electricity at least as much as a cause.

**Figure 4 was rebuilt too.** It plotted the gap against log grid size with three overlapping
layers and a y-axis only readable if you had memorised figure 3. One row per size band shows
the same thing directly: the spread collapses from 28.9 points in the smallest band to 11.0
in the largest.

## The figures these replaced

Five earlier versions were superseded while this recipe was built, and they are recorded in
[`artifacts/superseded/`](artifacts/superseded/) with what replaced each and why. **One is
kept as a file**: the mismatched-window version of figure 13, because nothing about it looks
broken — real states, correct counts, correctly computed regressions, and a correlation
correctly computed from two axes that covered different years. It reports **r = +0.32** where
the matched version reports **+0.18**. A persuasive wrong chart is the only kind worth
keeping; the other four are described rather than preserved, because one was unreadable, two
used a bad statistic, and one cannot be rebuilt without re-introducing a fixed bug.

## What this cannot answer

**Where compute load landed.** Three proxies failed. The public US electricity record does not
identify it at any resolution it publishes. **Dominion Energy Virginia — the obvious positive
control, and the densest data-centre region on earth — is not a balancing authority in EBA at
all**; `SCEG` is Dominion Energy *South Carolina*, a different company in a different state.

**Cost by location.** ATB's utility solar capex in 2030 is **$1,038 per kW in resource class 1
and $1,038 in class 10** — identical across every class and both financing cases. Location does
not change what you pay to build, only what comes out, and the whole location effect reaches
the cost through the capacity factor. Regional capex is not modelled.

**Cost by country.** ATB is United States only.

**What anyone actually paid.** ATB is a baseline, not a transaction record.

**Lead times**, which live in `cookbook/recipes/grid-queue-survival` — time from queue entry to
outcome by study stage, for CAISO and MISO. Not duplicated here.

**Wholesale price.** Figure 11 uses regulated retail price. A weak relationship there is not
evidence that generation mix fails to move wholesale prices — it is evidence that it reaches
the bill slowly. Hourly locational marginal prices live with the ISOs and need a separate
fetch; ERCOT already returns 403 to an honest bot.

**Why CISO's forecast is declining.** Figure 6 rules out the obvious mechanism and does not
supply a replacement. The likeliest remaining candidate is that CAISO's published day-ahead
series is a different product from the demand series beside it — the same fault as Duke Energy
Florida's, in a form no single scale factor removes — and settling that needs CAISO's own
documentation, not this file.

**Temperature directly.** No temperature series is fetched. Figure 7's seasonal amplitude is a
proxy computed from demand itself, and it is named as one everywhere it appears.

## Not reachable, and why

EIA's v2 API returns 403 without a key; ENTSO-E returns 401; IRENA returns 403. ERCOT returns
403 with a ROBOTS meta to an honest bot user-agent. EIA-860M archive vintages — where generator
lead times live — sit under `/electricity/data/eia860m/archive/xls/`, and robots.txt disallows
`archive` three separate ways. Python's `urllib.robotparser` reads that as allowed because it
does not implement wildcards; the Google specification reads it as disallowed. **Treated as
disallowed.** The files return HTTP 200, and that is not the question.

**The connection toll dominates everything except one host.** Latency is charged on connection
setup per host-pair, not payload: `api.eia.gov` cost 270.7 seconds for the first request and
0.3 for the next on the same connection; PeeringDB cost 816.8 then 0.7. All three EIA bulk
archives — 988 MB — came down in 405 seconds on one held connection. `api.eia.gov` also
301-redirects to `www.eia.gov` and urllib follows silently, so an early probe paid the toll on
both hosts. **NREL's S3 lake charges nothing**: 0.6 seconds to first byte.

## Receipts

`artifacts/data/` holds the committed derived caches — `eba-skill.json` (200 KB, seven years of
forecast scoring), `atb-folded.json` (776 KB), `peeringdb-fac.json` (1.7 MB),
`seds-electrification.json` (368 KB), `eba-annual.json` (116 KB), `eba-hourly.json` (64 KB),
`price.json` (32 KB), `predictors.json` (24 KB), `geo.json` (16 KB). The source — `eia-eba.zip` 660 MB,
`eia-elec.zip` 275 MB, `atb-2023.csv` 85 MB, `eia-seds.zip` 9.1 MB — is **not** committed.

`artifacts/research-questions/` holds the screens and the negative results, which are the part
most worth reading: `screens.md`, `questions.md` (including the written refusal to produce a
single data-centre share), `q2-falsifier-fired.md` and `q2-load-shape.md`.
