# What a public brain-imaging archive costs, checks, and is short of

Every dataset on OpenNeuro — 1,891 of them — joined to the NIH grants that paid for them.
6.6 MB of source, no API key anywhere, and the whole register fetches in under three minutes.

## The background

**OpenNeuro** is a public repository for brain imaging: MRI, EEG, MEG, iEEG, PET and fNIRS,
deposited in the BIDS layout, each dataset given a permanent accession like `ds002424`. It is
where a neuroimaging paper's data goes when a journal or a funder requires the data to go
somewhere. It publishes a keyless GraphQL API that returns, per dataset, the summary a
depositor filled in, the BIDS validator's verdict, and cumulative download and view counts.

That last part is why the archive is worth a recipe rather than a table. **Almost no research
data repository publishes its own reuse.** OpenNeuro does, which makes it possible to ask what
a deposit actually returns rather than assuming.

**NIH RePORTER** is the other half. 443 of the 1,891 datasets name a grant number in their
metadata. RePORTER turns a core project number into what that project was awarded, by fiscal
year. The join is what puts a price on the shelf.

## The thirteen figures

**1 — What a dataset *is* predicts its reuse; what is *in* it barely does.** Modality moves
downloads 2.4× between PET and MRI. Size, file count, subject count and task count move them
almost not at all. A recipe that started out expecting "bigger is more reused" found the
opposite of a finding: the thing a depositor spends most of their budget on is the thing that
predicts reuse least.

**2 — Reuse does not track spending.** 89 datasets resolve to a single-project research
grant. Median **$57,010 a download**, spanning $340 to $4.85m. The award explains none of that:
`corr(log award, log downloads) = −0.15`, t = −1.40. Three datasets have never been downloaded
at all; they have no position on a log axis and are drawn in a gutter rather than dropped,
because on a cost-per-download plate the zeros are the most expensive marks on it.

**3 — The archive's BIDS error rate did not fall; the validator changed.** Pooled, the share
of datasets carrying an error falls from 45% of 2023 deposits to 3% of 2026. Split by the
validator that produced the verdict, **v1 sits at 54-70% and v2 at 1-18%, and neither moves** —
what moved is the mix, from 36% v2 to 99%. The control: held at v1, the rate went **54% (2024)
to 70% (2025)**, up. And v2 reports *more* warnings than v1 (3,523 against 2,851), so it
reclassifies errors rather than missing them. **This archive cannot support a compliance trend
at all.**

This plate replaced an earlier one that was wrong in a different way — see below.

**4 — Nine in ten depositors remove the face, and it costs them nothing in reuse.** A
structural MRI is a photograph of a face, and there are two ways to publish one: deface it, or
keep it and record that the participants agreed. **736 of 795 deface, 51 keep the face with
consent, 8 record neither.** The standing objection to mandatory defacing is that it damages
the image and suppresses reuse — it does not: **13.4 downloads a year against 13.0, p = 0.90**,
and this design would have caught a 2× gap 85% of the time. A repository can require defacing
without paying for it. What it cannot see is a dataset withheld *because* of the requirement;
that one never enters the archive.

**5 — Datasets that name a patient population are reused about twice as often, and there
are far fewer of them.** Matched on modality and on publication era, MRI runs 10.6 downloads a
year for healthy controls against 24.5 for a named patient population — **2.31×, p = 0.010**,
on 174 against 23 datasets. EEG points the same way at 2.00× but does not reach significance
on 14. The supply ratio is **7.6 control datasets for every 1** that names a population. The
scarce thing is the wanted thing.

**6 — Nothing you can see at deposit forecasts reuse, so cost per download cannot be a
funding test.** The spread in cost per download splits exactly into **31% what was spent** and
**69% how often it was taken**, and the two are uncorrelated. The download side is nearly
unforecastable: every observable predictor is scored by ten-fold cross-validation, and on the
86 funded datasets "everything observable" reaches **0.193 in sample and −0.069 held out**. The
honest ceiling, on the full 1,429-dataset archive, is **0.107**. So **39% of the eventual cost
per download is knowable at the funding decision and 61% is a coin flip** — which makes
"screen out the expensive-per-download datasets" unimplementable, because at the moment of the
decision the $340 one and the $4.85m one look the same.

The one lever that does move is what kind of data it is: holding subject count fixed, every
modality beats MRI (PET 2.53×, EEG 2.13×, fNIRS 1.89×, iEEG 1.68×, MEG 1.18×), and MRI is 66%
of the archive. Scale is not a lever — the slope of downloads on subjects is **+0.22**, so
doubling a cohort returns about **16%** more downloads.

**7 — Ten minutes of rest doubles a dataset's reuse, and it is the cheapest block in the
session.** Split by whether any listed paradigm is resting state: **MRI 7.8 downloads a year
for task-only against 17.7 where rest is present — 2.28×, p < 0.0001** on 396 against 187
datasets; **EEG 21.1 against 43.5, 2.06×, p = 0.006**. Larger and better-evidenced than either
modality or patient population, and the only finding here whose cost side is near zero: a
resting run needs no paradigm design, no task training, no behavioural pilot and no response
hardware.

It is presence and not dose — rest-only (19.0) and rest-plus-task (17.5) are indistinguishable
in MRI, and among task-only datasets the correlation between paradigm count and reuse is
**+0.049, t = 1.27**. And it is not the lottery: this archive is **Gini 0.761 with its top 1%
holding 26.5% of all downloads**, so every cell median was rechecked after dropping its two
most-downloaded datasets — 2.28× and 2.05×, unchanged.

**8 — Neuroimaging studies did not get bigger; a few got enormous.** The one plate here that
is about neuroscience rather than about the repository. The median MRI dataset went from **23
participants to 31** over a decade — a real trend at 1.84x per decade, t = +4.42 — but ranked
by percentile the growth is **perfectly monotone and almost all of it is in the tail**: p10
1.25x, **p25 1.00x**, median 1.35x, p75 1.67x, p90 2.02x, p99 3.56x. The floor did not move.

Against the field's own benchmark — Marek et al. (*Nature*, 2022), that reproducible
brain-wide association studies need thousands of participants — **0.9% of 2025-26 deposits
clear a thousand** and 13% clear a hundred. The distribution stretched rather than shifted: a
handful of consortium deposits carry the entire trend while the typical lab collects the same
thirty people it collected in 2016.

**9 — A dataset ships in days and then keeps changing for years.** Two durations from one
dataset's life on a single axis. By day 7, **60% have published but only 27% have stopped
revising**; by day 365, 95% against 71%. Median draft 3 days, median revision span 119. A
dataset accession is not a version, and roughly a third of revised datasets are still changing
more than a year after they went public. The plate also carries the pipeline's one real loss:
**8,851 accessions issued, 1,891 public — 79% never ship.**

**10 — Two kinds of effort after the data is collected, and neither one pays.** Polishing
before publication: median downloads a year run 17.7, 20.8, 20.6, 16.4, 13.8, 13.6, **8.2** by
draft length, fitting **−0.077 at t = −4.54** — a hundredfold longer draft for about 30% fewer
downloads. Revising after publication: the error rate at exact snapshot counts runs 31, 33, 41,
35, 38, 31, 48, 33%, fitting **+0.028 at t = +0.77**, flat. Neither is causal, but neither
predicts the outcome it is spent on.

**11 — A brain model trained on this archive would represent a 24-year-old.** The largest
measurement in the recipe, from a field that sat unused since the first fetch: **52,970
individual participants across 945 datasets**. Median age 24. **18-25 year olds are 41.9% of
everyone ever scanned against roughly 9.5% of the population — 4.4×.** Over-65s are 7.6%
against 18.2% — 0.4× — and they carry most of the neurodegeneration. Only **13% of datasets
contain a single person over 65**. Not an artifact of big cohorts: dropping the five largest
(12% of all people) moves the median from 24 to 23 and pushes the 18-30 share *up*. It is
turning, though — over-65s are 3.7% of 2024's people, 7.0% of 2025's and **20.3% of 2026's**,
still 16.6% without that year's largest deposit.

**12 — The field fixed sex balance and left age alone.** Median **53.8% female within a
dataset**, 68% of 716 datasets inside a 35-65% band, holding across every modality (iEEG 49%
to MRI 55%). The same community that evidently answered the sex-balance critique has not
touched the age distribution — so plate 11 is not general carelessness about who gets scanned.
The sting: of 101,536 subject records, **44,309 have no sex recorded at all** and 3,980 are
bare numbers whose meaning lives in a per-dataset convention absent from the record.

**13 — Datasets with errors warn 12% more per file: consistently, and far too little to use.**
The BIDS validator emits two numbers and one of them is a file count — raw warnings track
`totalFiles` at **rho +0.81**, a median 7.7 warnings per file. Dividing that out leaves the
actual question, and the answer is a real but tiny gap: **1.11×, 1.11×, 1.15×, 1.25×** across
file bands, unanimous in sign, pooled 1.12× at p = 0.013 — inside a p10-to-p90 spread of **2.5
to 20.6, eightfold**. Real, and unrankable. The one thing the normalised form does earn is the
instrument: raw warning medians by validator generation are noise (2,851 / 3,602 / 2,463) while
per-file they fall cleanly (7.50 / 6.31 / 3.72), the same story plate 3 found for errors.

## The plate that was wrong twice

An earlier figure 3 said *"BIDS errors fell from 62% to nearly none, and then the checking
stopped"*, reporting an 819-dataset validation backlog. Both halves were false and both are
kept in `artifacts/superseded/` with the full account.

**It was built on a deprecated field.** `latestSnapshot.issuesStatus` is populated on 57% of
datasets, and that 57% was read as *validation coverage*. The live field,
`latestSnapshot.validation`, is populated on **1,893 of 1,893 — 100%, every year — and not one
dataset has both empty.** Where both exist they disagree on whether errors are present for
**450 of 1,072**, and in **431** of those the live field finds errors the deprecated one did
not. A deprecated GraphQL field does not error; it returns a well-formed null forever, and an
absence in a register has exactly the shape of a finding.

**And a third field misread, this time by assuming its shape.** `metadata.ages` was taken for
a `[min, max]` pair and an age table was computed from it — on the fifteen datasets that happen
to have exactly two subjects. It holds **one entry per participant**. Read correctly it is
52,970 people and the single largest measurement here. Printing six raw values would have
caught it; the assumption was never tested against the data.

**And a fifth, caught by a reader saying a scatter looked random.** Plate 13's first version
drew warnings against files — which is rho +0.81 and nothing else, so both classes stacked on
one diagonal and the reader was right to call it noise. Dividing warnings by files removes the
dominant term, and the same data then shows a clean unanimous gap across four bands. The
reading also corrected an overstatement: the plate had said the two outputs were "unrelated"
and the dots "scattered, not raised". They are raised, by 12%, at p = 0.013.

**And a fourth, caught by a reader asking a layout question.** Figures 9 and 10 measure the same
kind of quantity — a duration — and were drawn two different ways, one a cumulative curve and
one five bars. Asked why, the answer was that there was no reason. Redrawing the bars as a
bin-free curve refuted their claim: revision spans had been called **bimodal, two populations**,
on the strength of a dip at 8-30 days. The ECDF's slope per log-decade rises monotonically
(+0.13, +0.14, +0.10, +0.16, +0.21, +0.30, +0.42) — one right-skewed mode. The dip survives
every binning scheme but is modest at log2 resolution; the five-bin version exaggerated it.

The same question surfaced a second error: figure 9 had annotated a long draft as "friction
with no yield" on a comparison of 14.7 against 12.7 downloads. The continuous fit is **−0.077
at t = −4.54**. Not neutral — negative.

**This is the second time in one recipe.** `grantIdentifier` reported 0% for the same reason —
it was never requested. Seven figures were built on a guessed field list and the schema was
never introspected, which costs one request.

## Three things that changed the recipe while it was being built

**A field reported at 0% that was never requested.** `grantIdentifier` came back empty for
every dataset, which looked like a finding about metadata discipline. It was absent from the
GraphQL query. Re-fetched, it is present on **443 of 1,891** — and figure 2 exists only
because of it. A zero from an instrument you did not point at the thing is not a measurement.

**A compliance rate read backwards.** `affirmedConsent` is false on 646 of 795 MRI datasets,
which reads as 79% non-compliance and would have been a headline. Reading OpenNeuro's own
wording turned it over: consent here means consent to publish **without** defacing, so a false
usually means the stricter thing was done instead. The real problem cell is 8 datasets. The
error and the correction are both in the plate, because the plate's job is to stop the next
reader making it.

**A clinical premium that was half calendar.** Unmatched, MRI datasets naming a patient
population looked 4.83× more reused than controls. Downloads per year falls with age, and the
two groups sat in different parts of the archive's life; matched on publication era the effect
is 2.31×. Pooling across modalities instead reads 3.18×, which is composition — patient
datasets skew toward EEG and iEEG, which are more reused whatever they study.

**A ratio that was its own denominator.** Cost per subject correlated with reuse at −0.36,
which read as "expensive data is underused" and would have been a headline. Fitting the two
sides free showed the opposite: subject count carries it at **+0.31** and the award does
nothing at **−0.19**. A ratio `X/Y` correlates negatively with anything `Y` correlates
positively with, and iEEG looks expensive per subject mostly because it has four subjects
rather than thirty-four.

**A cost figure four times too large.** Summing every activity code a dataset names reached
$1,017.7m, including a $112m award to an entire Clinical and Translational Science Institute.
Centres, program projects and core facilities fund buildings and cohorts, not studies.
Restricted to single-project grants — R01, R21, K-series and similar — the total is $246.7m.

## What this cannot answer

**A download is not a citation.** It counts anyone taking the data, including the depositor and
any crawler OpenNeuro's analytics did not filter. As a denominator it flatters the cost.

**An award funds a project, not a dataset.** Every dollar figure in figure 2 is an upper bound,
overstated by the same kind of amount for every mark, so the comparison holds where the level
does not.

**What the field has actually discovered.** This is a deposit archive: it records what data
was *collected*, never what was *found*. There is no field for a study's conclusion, and both
routes to the papers failed — OpenAlex is internally inconsistent by a factor of six, and
`Snapshot.related` is populated on 1.7%. A "are we in a dry spell" question needs a findings
corpus, not a data corpus.

**Paradigm diversity.** `tasksCompleted` looks like a paradigm vocabulary and is not: 79% of
its 2,513 normalised values are used exactly once, and the twenty most common include `hw`,
`test`, `main`, `sess` and `cmrrmbep2dbold2iso` — a Siemens pulse sequence. It is whatever
string went into the BIDS `task-` filename slot.

**Whether BIDS compliance actually improved.** 803 datasets carry no validator version stamp
at all, and their 54% error rate merely resembles v1's 55%. Figure 3 establishes that the
trend cannot be measured here, not that the field failed to improve.

**The consent fields are assertions, not inspections.** A ticked box is not proof a scan was
defaced, and an unticked one is not proof consent was never obtained on paper.

**The archive is a lottery and figure 6 is the right answer to one.** Gini 0.761; the top
1% (14 datasets) hold 26.5% of all downloads and the top 5% hold 53%. The winners are not big —
median 28 subjects against 25 archive-wide — they are canonical: `ds000102` (a flanker task, 26
subjects) alone is **7% of every download in the archive**, and `ds000001` and `ds000002` are
literally the first two accessions ever made. Predicting reuse means predicting which dataset
becomes a teaching example, which is why the honest ceiling is R² 0.107.

**Nothing here can measure a dataset that was never deposited.** Figure 4 shows what the
defacing requirement costs the datasets that *were* published. If the requirement deterred
anyone from depositing at all, that dataset is absent from the archive by construction and
absent from this recipe with it. MRI deposits did fall from 153 in 2020 to 101 and 81 in
2021-2022 before recovering — but in-person scanning stopped in those years for reasons that
had nothing to do with consent forms, and nothing here separates the two.

**Figure 5 establishes no direction.** A lab able to recruit patients may also be a lab that
promotes its data, and a patient cohort costs more to collect than the figure knows. It says
the archive is thin where reuse is highest, not that collecting patients is cheap.

**`studyDomain` cannot say which research areas are underserved.** 867 of 1,462 are blank and
the rest are uncontrolled free text whose most common value occurs sixteen times. That is
recorded in `artifacts/research-questions/questions.md` as a property of the register rather
than worked around.
