# Screens, run before anything was built

USAspending API v2, 2026-09-22. Every number here is from a probe, not from documentation.

## The one that matters

| screen | result |
| --- | --- |
| same query twice | **5,927,888** contract awards in FY2024, both times |
| a nonsense **filter value** | **HTTP 400**, and it *enumerates the valid values* |
| a nonsense **field name** | **HTTP 200 with `"Banana Amount": null`** |
| connection cost | **121–136 s to connect**, then 0.3–1.6 s per request |

**Asking for a field that does not exist returns success and a null.** Every row comes back
with the key present and empty, which is indistinguishable from a real field that happens to be
blank. There is no error, no warning, and no list of what was accepted.

**This is the second source in a row with that exact asymmetry** — ClinicalTrials.gov's filters
also failed loudly while its field paths failed silently. Two is a pattern worth designing
against rather than a coincidence: **prove every field non-null on a sample before using it,
and never infer a field is empty from a page of nulls.**

The check that does the proving, run on 20 rows:

| asked for | non-null in 20 | verdict |
| --- | --- | --- |
| `Award Amount` | 20 | real |
| `Awarding Agency`, `NAICS`, `PSC`, `Recipient UEI` | 20 | real |
| `Start Date`, `End Date`, `Last Modified Date` | 20 | real |
| `Base Obligation Date` | 20 | real |
| `Total Outlays` | 20 | real (often 0.0) |
| **`Base and All Options Value`** | **0** | not a search field |
| **`Base and Exercised Options`** | **0** | not a search field |
| **`Potential Award Amount`** | **0** | not a search field |
| `Total Obligation`, `Obligated Amount`, `Current Award Amount` | 0 | not search fields |
| `Parent Award ID` | 0 | not a search field |

## What that costs, and the route around it

The three values the FAR distinguishes — base, base-plus-exercised-options, and
base-plus-all-options — **do exist**, on the single-award detail endpoint:

    GET /api/v2/awards/{generated_internal_id}/
      total_obligation          7112.26
      base_exercised_options    7112.26
      base_and_all_options      7112.26

**But not in search.** So the plan-versus-outcome comparison this source was chosen for cannot
come from the search endpoint at any page size, and at 5,927,888 contracts in one fiscal year
it cannot come from per-award calls either.

**The route is the bulk download**, which builds a file server-side and hands back a URL:

    POST /api/v2/bulk_download/awards/   -> status_url + file_url
    GET  /api/v2/download/status?file_name=...

It returns *PrimeTransactions* — modification-level rows rather than one row per award — which
is what Q5 needs anyway: **a contract is not one row, and any count of "awards" that does not
say so is counting paperwork.**

## Connection cost, and a correction carried forward

121–136 s to open a connection, then 0.3–1.6 s per request. Same shape as the previous recipe,
and the same design consequence: **hold one connection open**. Measured through a client that
opens a fresh connection per call, every request reads as two minutes.

Three hosts now measured from this machine: `search.rcsb.org` 0.3 s, `clinicaltrials.gov`
~134 s, `aact.ctti-clinicaltrials.org` 180–240 s, `api.usaspending.gov` ~130 s. **The toll is a
property of the route, not of any API**, and a reproducer elsewhere may see none of it. What
holds everywhere is that it is charged per connection.

## Still to screen, before any figure

- **Is a modification a new row sharing a key?** Count the key before diffing anything.
- **Are negative obligations present?** De-obligations reduce totals and never error.
- **Fiscal versus calendar year.** The federal year starts 1 October; a series binned on the
  wrong one is shifted a quarter and still looks plausible.
- **Does the download default-sort by value?** If so, any truncation is a biased sample of the
  variable under study.

## The all-agency year does not build, measured

Requested: every agency, FY2024, contract transactions. **Failed after 4,611 seconds** — 77
minutes of server-side generation ending in `{"status": "failed", "message": "An error
occurred.", "total_rows": 0}`.

That is not a timeout on my side and not a rate limit; the job ran, reported `running` for
76 minutes with `rows=0` throughout, and then errored. **The bulk endpoint will accept a
request it cannot complete**, and it charges the full generation time before saying so.

**Generation cost, measured across four requests:**

| request | outcome |
| --- | --- |
| Commerce, one year | 15,810 rows, 6.3 MB, **139 s** |
| GSA, one month | 90,304 rows, 21 MB, **530 s** |
| DoD, one month | still running at 600 s, abandoned |
| **all agencies, one year** | **failed at 4,611 s** |

So the practical ceiling is somewhere between one agency-year and all-agency-year, and it is
discovered by hitting it rather than declared anywhere. **Request small, checkpoint, and never
put a decade in one call.**

**What this does to the population.** The register cannot be taken whole at this size, so:

1. The **civilian decade** (11 departments, FY2015–24, 8.5% of awards) is fetched year by year
   and is the longitudinal population.
2. **DoD is requested as a single quarter, as a control rather than a population** — enough to
   ask whether a civilian distribution looks like DoD's, which is a cross-sectional question a
   time slice can answer. It is not enough to ask about change over time in DoD, and no figure
   will.

That distinction is the difference between a control and a sample, and it is stated on any
plate that uses it.

## The central quantity's coverage moves 99% to 30% in one year

This is the finding that would have been invisible in a finished chart, and it probably kills
the longitudinal question as posed.

`potential_total_value_of_award` — the denominator of the exercised share, the quantity this
source was chosen for — is populated on **25.3%** of civilian FY2015 awards and **29.0%** of
FY2016. The other three quarters are blank, not zero. Broken out by `award_type`:

| FY2015 | transactions | potential populated |
| --- | --- | --- |
| `DO` | 250,448 | **0.0%** |
| `PO` | 216,721 | **0.0%** |
| `DELIVERY ORDER` | 87,068 | **99.0%** |
| `DCA` | 50,875 | 0.0% |
| `BPA` | 47,496 | 0.0% |
| `PURCHASE ORDER` | 47,292 | **99.8%** |
| `BPA CALL` | 40,861 | 98.3% |
| `DEFINITIVE CONTRACT` | 10,323 | 98.6% |

**`DO` and `DELIVERY ORDER` are the same award type written two ways**, and the money field is
populated in one and never in the other — within the same fiscal year, across the same months.
So it is not a vintage effect and not a property of the award type. Two systems are writing
into one file.

**And then the encoding resolves while the coverage collapses:**

| `DELIVERY ORDER` | transactions | potential populated |
| --- | --- | --- |
| FY2015 | 87,068 | **99.0%** |
| FY2016 | 333,553 | **29.7%** |

FY2016 has four award types instead of eight — the codes are gone, everything is a label — and
population falls to 20–49% across all of them. **Same award type, same column, 99% to 30% in
twelve months.**

### What that does to the questions

**Any year-over-year comparison of the exercised share is measuring the reporting system.** A
series built on this would be smooth, plausible and entirely an artefact — the same failure as
an earlier recipe where filtering on a self-reported flag drew that flag's rollout and called
it behaviour.

So, before any figure:

1. **Measure the population rate per year and print it beside every point.** A quantity
   defined on 25% of awards is not the same quantity as one defined on 99%.
2. **Test whether the populated subset is special.** If awards with a ceiling recorded are
   systematically larger, or more often competed, then the 25% is not a sample of the 100%
   and no amount of caveat rescues a trend.
3. **Expect the longitudinal question to be answerable only across years whose coverage
   matches**, and possibly not at all. If so, that is the finding: *the register cannot
   support a time series of contract ceilings because it changed how it records them.*

**The cross-sectional question survives** — within one year, with coverage stated, "how much of
the authorised ceiling gets exercised" is still a real measurement. It is the *change* that is
in doubt.

## The missingness is not random, and it runs along both variables of interest

Civilian FY2016, 554,171 awards, 30% with a ceiling recorded. The question was whether that 30%
is a sample of the whole. **It is not.**

**By how the award was competed:**

| extent_competed | awards | has a ceiling |
| --- | --- | --- |
| FULL AND OPEN COMPETITION | 207,997 | **35%** |
| COMPETED UNDER SAP | 139,301 | 30% |
| NOT COMPETED UNDER SAP | 69,975 | 25% |
| **NOT COMPETED** | 61,788 | **19%** |

**By agency:**

| agency | awards | has a ceiling |
| --- | --- | --- |
| **Veterans Affairs** | 166,056 | **10%** |
| Justice | 91,340 | 17% |
| Commerce | 26,015 | 33% |
| Agriculture | 53,843 | 54% |
| **Homeland Security** | 61,028 | **58%** |

Size is not the explanation: median obligation is 15,000 where a ceiling exists and 11,565
where it does not, which is not a gap that produces a sixfold difference in coverage.

**So Q3 and Q6 are confounded at the root.** "Does competition predict how much of the ceiling
gets used" cannot be answered by comparing competed and uncompeted awards when the competed
ones are **twice as likely to have a ceiling on file**. The comparison would be between two
different populations wearing one label. The same applies to any agency comparison across a
10%-to-58% coverage range.

## So the recipe turns over: the coverage is the finding

The exercised share was the plan. It is measurable only where a ceiling exists, and where a
ceiling exists is **not a fact about the contract — it is a fact about who bought it and how**.

That inverts the recipe. The question worth asking is no longer *how much of the ceiling gets
used*, it is:

> **A transparency statute produces a register in which the contract's own ceiling is recorded
> for one award in ten at Veterans Affairs and six in ten at Homeland Security — and less often
> when the award was not competed.**

That is a measurable, checkable claim about the instrument rather than about procurement, and
it is the kind this fleet exists to make. It also stands on the data that is already on disk,
where the original plan needs a decade that may never be comparable.

**What still has to be nailed down before it is a figure:**

- **Is it agency practice or system?** FY2015 had two encodings of the same award type, one
  never populated. If the 10%-vs-58% split tracks which filing system an agency uses rather
  than agency behaviour, the finding is about software and should say so.
- **Does coverage within an agency move over the decade?** If VA goes 10% to 60%, the register
  is converging; if it stays at 10%, it is not.
- **Is the competition gradient real once agency is held fixed?** VA is 10% covered and files a
  lot of uncompeted work; the pooled competition gradient may be an agency effect in disguise.
  **That control has to run before the gradient is shown.**
