# ClinicalTrials.gov: a register with a statutory deadline on it

## The statute, read before the schema

Most registers in this project record a *choice*. This one records a **duty**, and the duty has
a date attached, which is what makes it different from everything else here.

**FDAAA 801** (Food and Drug Administration Amendments Act 2007, §801) and its Final Rule,
**42 CFR Part 11**, effective 18 January 2017:

- An **"applicable clinical trial"** (ACT) must be **registered within 21 days** of enrolling
  its first participant. Roughly: a controlled interventional study of a drug, biologic or
  device, other than phase 1 and small device feasibility studies, with at least one US site
  or conducted under a US IND/IDE.
- Summary **results must be submitted within 12 months of the Primary Completion Date** — the
  date of final data collection for the primary outcome measure, not the end of the study.
- Delay is available: a "good cause" certification, or up to two further years where the
  product is not yet approved for the studied use.
- The penalty is a civil monetary fine per day of non-compliance. **Enforcement was
  approximately zero for over a decade**; FDA issued its first Notices of Noncompliance in
  2021. That gap between a rule and its enforcement is itself measurable here.

Two other duties overlap and do not have the same scope:

- **NIH policy (2017)** requires results for every NIH-funded trial, which is broader than ACT.
- **ICMJE** has required prospective registration as a condition of publication since 2005,
  which is why registration rose sharply years before the statute bit.

**What the statute predicts about the schema, and what to check.** A 12-month clock from a
specific date means the register must carry that date (`primaryCompletionDate`) separately from
study completion, and must carry a results-submission date. If both exist per record, **the
compliance gap is computable per trial rather than estimated** — which is the whole reason to
pick this source.

## Screens to run before building anything

Standard for this project, plus three specific to a register with a deadline:

- **The same query twice.** The register is updated daily; every figure is one fetch.
- **A nonsense field and a nonsense value.** Does a bad filter fail loudly or silently return
  the unfiltered total? Four parameters did the latter in an earlier recipe.
- **Paging.** Send a nonsense page token and a nonsense page size. A truncated first page that
  looks complete is a sorted sample, not a sample.
- **Which date is which.** `primaryCompletionDate` (the clock's start), `completionDate`,
  `studyFirstPostDate`, `resultsFirstSubmitDate`, `resultsFirstPostDate`, `lastUpdatePostDate`.
  Submit and post differ by QC review, which can take months — using the wrong one measures the
  reviewer, not the sponsor.
- **Date precision.** Many of these are month-precision, not day. A "within 365 days" test on
  a month-precision date has an inherent ±15 days, and the deadline is exactly the kind of
  threshold where that matters.
- **Is the record the current version or the whole history?** The register keeps every
  historical version of every study. If the default response is the current version only, then
  every "what was planned" question needs the version history and is a different fetch.

## Questions, before any data

**Q1. How far past the 12-month deadline does the register actually run?** Days from primary
completion to results submission, per trial. The statute puts a line at 365 days; the
distribution around that line is the finding, and no estimate is needed because both dates are
recorded.

**Q2. Is "never reported" a share or a population?** In the PDB, a 15.8% unpublished share
turned out to be two populations with structural genomics doing almost all of it. The same
question here: is the non-reporting concentrated in a sponsor class — industry, academic
centre, government — or spread thin? *Falsifier:* the sponsor-class shares sit on the overall
rate.

**Q3. Did the 2021 enforcement actually change behaviour?** The rule took effect in 2017 and
the first Notices of Noncompliance issued in 2021. Two candidate step changes with a known
date on each. This is the register's own natural experiment — and it needs a detrended,
out-of-sample test rather than a before-and-after difference, because registration volume was
already trending.

**Q4. `UNKNOWN` status: is it a status or an age?** The register marks a study "unknown" when
its completion date has passed and the sponsor has not updated it in over two years. That is
a staleness flag wearing a status field's clothes. *Test:* cross-tabulate status against
registration cohort. If `UNKNOWN` is overwhelmingly one era, it measures abandonment of the
*record*, not of the trial.

**Q5. Estimated versus actual enrollment.** The register carries both a planned and an achieved
enrollment. Almost no register in this project holds a plan and its outcome in the same row.
How large is the shortfall, does it differ by phase and sponsor, and is under-enrolment the
stated reason trials stop?

**Q6. What does `whyStopped` say, and does the reason predict anything?** Free text on
terminated and withdrawn studies. Categorising it is a declared judgement and must be written
into the script so it can be argued with — and, if possible, tested against something the text
does not contain.

**Q7. Does the register record what was planned, or what was found?** Every study has a full
version history. Comparing the primary outcome measure at registration against the one at
results submission is the outcome-switching question, and it is a silent-rewrite detector of
exactly the kind this project has built before. Cost unknown: it may need one request per
study, which decides whether it is answerable at all.

**Q8. What is invisible?** Unregistered trials. Registration is compelled for ACTs but not for
everything, so the register's own denominator is not the number of trials run. Whether the gap
is measurable against an outside count — FDA approvals, publications — is an open question and
probably the boundary of what this source supports.

## The population problem, decided before any figure

**The register carries no "applicable clinical trial" flag.** ACT status under 42 CFR 11.22 is
a legal determination made against the study's design, its product and its geography. It is not
a column, and no amount of querying produces one.

That matters because the headline this source invites — *"X% of trials broke the law"* — is not
computable, and a figure that implies it would be wrong in the way that is hardest to see:
every count in it correct, the denominator quietly the wrong population.

**What the rule actually requires, against what the register holds:**

| the statute's test | the register's field | usable? |
| --- | --- | --- |
| interventional, controlled | `studyType` | yes |
| not phase 1 (drugs) | `phases` | yes |
| product subject to FDA regulation | `isFdaRegulatedDrug` / `isFdaRegulatedDevice` | self-reported, and **223,770 studies leave it blank** |
| at least one US site, or under IND/IDE | location country | **not fetched**, and IND/IDE is not published at all |

Two of the four tests are clean, one is self-reported with a third of the register missing, and
one is partly unavailable in principle. So:

**The decision.** Figures about reporting behaviour will be drawn on a *declared operational
population* — interventional, not phase 1, FDA-regulated drug or device as self-reported —
written into the script so it can be argued with, and its size stated on the plate next to the
register total. The word "compliance" will not appear without that qualifier attached, and any
rate will be labelled as a rate within the approximation, not within the law.

**What that buys.** The interesting questions survive intact. *How long after finishing do
sponsors report* is a measurement, not a legal judgement, and so is *does the lag differ by
sponsor class* and *did it move in 2017 and 2021*. Only the prosecutorial framing is lost, and
it was never available.

**One open cost.** The US-site criterion needs `contactsLocationsModule`, which was not in the
walk. Whether to spend a second pass on it depends on how large the candidate population turns
out to be — if FDA-regulated-drug-or-device already narrows to something small, the geography
test may move few rows and can be recorded as untested rather than bought. That is a decision
to make against the counts, not before them.

## Second pass, written against the walked table

603,730 rows are local now, so these were checked cheaply before being written down. Each one
below has a number attached already; what is open is whether it survives a control.

### Answered

**Q1 — how far past the deadline does the register run?** *(answered, figure 3)* The deadline
is powerfully salient and changes almost nothing. Submissions in the 30 days before it run at
**5.8x the surrounding baseline**, but with non-reporters kept in the denominator, three-year
reporting sits at **~25% and has for fifteen years** — 20.5% for 2008 completions, 25.2% for
2013, 24.1% for 2017, 24.5% for 2023. One-year reporting tripled, 5.5% to 14.7%. The rule
moved the reporters earlier; it did not recruit new ones.

**Q3 — did 2017 or 2021 change behaviour?** *(answered inside figure 3, negatively)* Neither
the rule taking effect nor the first Notices of Noncompliance leaves a step in the series. The
one-year figure rises smoothly across both dates and the three-year figure is flat through
them.

**Q5 — estimated versus actual enrollment.** *(dead as posed)* The register carries **one**
enrollment number and a type flag: 62.1% ACTUAL, 35.0% ESTIMATED. When a trial finishes, the
actual **overwrites** the estimate. There is no plan-and-outcome pair in the current record.
Recovering it means diffing the version history, which is one request per study and a
different recipe. *Worth stating as a property of the source:* this register does not preserve
what was planned, only what is currently claimed.

### New, with a number already attached

**Q9. Registration is supposed to be prospective, and often is not.** ICMJE has required
registration before the first participant since 2005, and FDAAA requires it within 21 days of
first enrolment. Measured against the primary completion date: **23.1% of trials with an
ACTUAL completion date were registered after they had already finished**, and the 10th
percentile is **-385 days** — a tenth were registered more than a year after completion.
*What makes it a question rather than a number:* whether it is falling over time, and whether
it concentrates in the same sponsor class that does not report. *Falsifier:* if retrospective
registration is flat across cohorts, the 2005 ICMJE policy did nothing measurable.

**Q10. Does trial size predict reporting?** Completions 2015-2021, share reporting within
three years: 1-25 enrolled **22.5%**, 26-100 **20.1%**, 101-500 **27.5%**, 501-2000 **36.4%**,
2001+ **26.8%**. Non-monotonic, and the fall at the top is on 1,888 trials. *The control this
needs:* size is confounded with sponsor class and with phase, and figure 4 shows sponsor class
spans 1.8% to 36.9%. Size may be carrying sponsor entirely.

**Q11. Which phase stops early?** Interventional studies ending TERMINATED, WITHDRAWN or
SUSPENDED: **phase 2 is worst at 15.3%**, then phase 1 at 12.9%, phase 4 at 11.5%, phase 3 at
11.2%, and studies with no phase recorded at 6.7%. Phase 2 being worse than phase 3 is the
interesting part — it is where a drug is supposed to fail, so this may be the register
behaving correctly rather than a pathology. *Test:* separate WITHDRAWN (never enrolled) from
TERMINATED (stopped after enrolling); they are different events and averaging them hides which
is moving.

**Q12. `whyStopped` is 47,089 sentences, not a column.** 32,126 distinct normalised strings.
The top repeats are "sponsor decision" (598), "slow accrual" (561), "lack of funding" (502),
"low accrual" (386) — and the median entry is 41 characters. Hand-declaring categories is the
codebook approach `assay/` exists to argue against, and it fixes the schema before the second
question is asked. *Deliberately not attempted here.* Recorded as a candidate for that
workspace, with the note that the interesting cut — *did it stop for money or for science* —
is exactly the one a keyword rule gets wrong.

### Still open

**Q13. Is the flat three-year rate flat everywhere, or flat on average?** Figure 3 pools
sponsor classes whose one-year rates span 1.8% to 36.9%. A flat pooled series is consistent
with every class being flat, and also with industry improving while the dominant academic
group declines. *This is the next figure.*

**Q14. Does the deadline spike exist in every sponsor class?** If only industry piles up
against the line, the deadline is salient to the people with regulatory staff and invisible to
everyone else, which is a different claim from "the deadline works".

**Q15. What happens after a Notice of Noncompliance?** FDA published its first in 2021. The
recipients are named in public FDA records, not in this register, so the join is external and
the population is tiny. Recorded as blocked-unless-joined rather than attempted.

## Third pass: two figures overlapped, and fixing it produced the better finding

**Figures 3 and 4 were drawing the same picture.** Figure 3's right panel was a count of
submissions by lag with a red spike at 365 days; figure 1's left panel was a hazard with a red
spike at 365 days. Figure 4's right panel and figure 1's right panel both asked whether the
deadline registers for every sponsor class. Three panels, two questions.

The hazard version is the correct one in both cases — a count of submissions conflates *how
likely a sponsor is to report* with *how many are left who have not*, and the raw per-class
share of reports near the deadline penalises classes that rarely report at all. So figure 1
now owns the deadline and the other two panels were given questions that had been sitting in
prose.

**Q13 — is the flat three-year rate flat everywhere, or flat on average?** *(answered,
figure 4 right)* **Flat on average, and nowhere else.** Three-year reporting by completion
cohort, 2010 against 2022: **NIH 46.9% to 89.6% (+43 points)**, **industry 38.8% to 48.8%
(+10)**, university and hospital 14.6% to 18.0% (+3), other government 4.2% to 2.5% (**−2**).
The pooled line barely moves because the group that did not improve is three quarters of the
register. Figure 3's flat series is **composition, not stasis** — the improvement is real,
large, and confined to the sponsors who were already best.

**Q14 — does the deadline spike exist in every sponsor class?** *(answered, figure 1 right)*
No, and the range is wider than any other split here. Each class's deadline-window hazard
against its own baseline: **industry 82x**, NIH 28x, other federal 24x, network 21x,
university and hospital 9x, **other government 1.4x**. Measuring each against its own quiet
months means a class is not penalised for reporting rarely — this is purely whether the date
registers, and for one class it does not register at all.

### New questions this pass opened

**Q16. Does the hazard spike appear before the rule existed?** The 12-month clock has legal
force from 2017, but ICMJE and journal practice predate it. If completions from 2008-2012
already show a spike at exactly 365 days, the wall is not the statute — it is a convention the
statute later wrote down. *This is a clean falsifier and it is one line of code away.*

**Q17. Is the spike at 365 days or at 12 months?** Month-precision start dates are placed
mid-month here. If sponsors work to "a year after the month we finished" rather than to a day
count, the true spike is a monthly grid and the daily one is an artefact of that placement.
*Test:* the day-precision subset only, binned at 7 days rather than 30.

**Q18. Retrospective registration: 23.1% were registered after they had already finished.**
The 10th percentile is **−385 days**. ICMJE has required prospective registration since 2005
as a condition of publication. Is it falling, and does it concentrate in the same class that
does not report? *Figure 6.*

**Q19. Does a trial that registers late also report late?** Two duties, two dates, one row.
If the same sponsors fail both, the register is measuring one underlying thing — administrative
capacity — rather than two independent obligations. *Test:* reporting rate conditioned on
whether registration was prospective, within sponsor class so the class effect is held out.

**Q20. What happened to trials that stopped early?** 34,352 TERMINATED and 16,791 WITHDRAWN.
A terminated trial still has results worth reporting and the duty still applies; a withdrawn
one never enrolled anyone. Do terminated trials report at the same rate as completed ones?
*If they report far less, the register's silence is concentrated exactly where the negative
results are.*

## Fourth pass: the columns the first walk threw away

`ctg2.py` requested whole modules and then extracted only the paths its column map named.
Study **start date**, **intervention type**, **conditions** and **location country** were all
downloaded and discarded. The second walk (`ctg3.py`) cost one handshake and eight minutes and
**overturned the recipe's headline**.

**Q21. Does the statute's own scope explain the gap?** *(answered, figure 10 — and it does)*
FDAAA 801 applies two tests this register can now answer: a drug, biologic or device, and a US
site. Crossed:

| | US site | no US site |
| --- | --- | --- |
| drug, biologic or device | **67.1%** (31,934) | 13.3% (38,970) |
| everything else | 17.9% (18,275) | **3.4%** (31,805) |

**The tests do not interact.** US-site effect 5.0x among regulated products and 5.3x among
everything else; regulated-product effect 3.8x with a US site and 3.9x without. Two
independent multipliers, twentyfold across the diagonal.

**So the pooled quarter was measuring scope, not apathy.** Where the law applies, two trials in
three report. Where it does not, one in thirty. **Every figure before this one quotes a rate
near 25% and frames the gap as a compliance failure; that framing is wrong and the figures now
say so.**

**And it is not the sponsor effect from figure 4.** Inside university and hospital sponsors
alone, the two tests give **68.8% against 5.2%** for the same product type. A university
running a drug trial with a US site reports about as often as industry. Figure 4's twentyfold
class range is substantially a range in *what those sponsors study and where*.

**Q22. Does trial sample size predict reporting?** *(answered, figure 9, and the pooled answer
is a mirage)* Pooled, enrollment against three-year reporting makes a U: 31.7% at 1-10, 20.8%
at 51-100, 38.4% at 501-1,000, 26.0% above 5,000. Split by class the two halves point opposite
ways — **industry rises monotonically 36.7% to 68.6%, universities drift 29.6% down to
16.1%**. The U is the mixing ratio, because the industry share climbs with trial size. Sample
size is a proxy for who is running the trial and reverses sign once that is fixed.

**Q23. Intervention type.** Three-year reporting: biological **45.0%**, drug **41.0%**, device
27.4%, other 14.9%, behavioral 14.8%, procedure 13.0%, diagnostic test 11.4%, **dietary
supplement 7.0%**. The order tracks the statute's reach almost exactly, which is the same
finding as Q21 from the other side. Dietary supplements are the one type where industry does
*not* outperform universities — 6.4% against 6.6%.

### Answered as "no", which is also an answer

**Q24. Can this register identify profitable or unprofitable trials?** **No.** Checked rather
than assumed: there is no cost, price, revenue or funding-amount field anywhere in the schema.
Enrollment times phase is a cost proxy at best and says nothing about return. Any profit figure
from this source would be manufactured.

**Q25. Can it identify compounds rushed to market?** **Not alone.** No approval date, no NDC,
nothing linking a trial to a market. It needs a Drugs@FDA join. What is internal is development
*tempo* — how fast a compound moves between phases — which is a different question wearing the
same words.

**Q26. Can it identify problematic compounds?** **Partially, and weakly.** A declared keyword
rule over the 47,089 `whyStopped` entries gives recruitment 34.2%, money 17.0%, logistics 8.4%,
safety **5.5%**, futility 3.8% — but **37% match nothing** and 8.3% match two families at once.
Safety-flagged share by phase: phase 3 11.9%, phase 1 10.5%, phase 2 7.8%. The harder blocker
is that compound-level aggregation needs intervention *names*, and only *types* were fetched.
A keyword rule over free text is the codebook approach `assay/` argues against, and 37%
unmatched is the tell.

## Fifth pass: tempo, and a product key that works mechanically and fails semantically

**Q27. Have trials become more efficient?** *(answered, figure 11 — and the obvious
measurement is inverted)* Median days to primary completion among trials that finished runs
**853 days for 2006 starts down to 243 for 2024** — an apparent threefold speed-up. It is
survivorship: a 2024 start only enters that median if it has already finished, so recent
cohorts are a sample of their own fastest members.

Keeping every trial in the denominator reverses it. Share of a start cohort reaching primary
completion **within five years: 77% for 2008 starts, 64% for 2021**. Within three years,
61% to 54%. **Within one year it has not moved at all, 26% to 26%.** The slowdown is entirely
in the tail — quick trials are unchanged and slow ones got slower.

*Not size:* median actual enrollment is 57–60 participants in every start year from 2008 to
2022, and the 90th percentile drifted **down** from 415 to 340.

**Q28. Which phase is the bottleneck?** *(answered, figure 11 right)* Phase 2, at every
horizon. Reaching primary completion within a year: phase 1 **37%**, phase 2 **17%**, phase 3
19%, phase 4 21%. At five years phase 2 is still last, 69% against phase 1's 77%. Phase 3 runs
four times larger by median enrollment (204 against 55) and still finishes more often, so the
phase 2 delay is not size. Phase 2 also has the highest early-stop rate, 15.3%.

**Q29. Can trials of the same product be followed through their phases?** *(answered: no, and
the reason is structural)*

*The join works mechanically.* There is no compound identifier in this register — no NDC, no
UNII, no ChEMBL — so the only key is the free-text intervention name. Normalising DRUG and
BIOLOGICAL names and dropping placebo-like terms gives 132,790 keys, of which **16,676 span
two or more phases across 162,173 trials, 26.9% of the register**. Spot-checked raw the groups
collapse correctly: `cabazitaxel (XRP6258)`, `Cabazitaxel (XRP6258)`, `cabazitaxel`.

*The semantic fails.* The largest keys are cyclophosphamide (2,887 trials since 1976),
cisplatin, carboplatin, dexamethasone — **backbone agents that appear in other drugs' trials**,
at every phase, for fifty years. Within-key correlation between phase and time, across 7,553
keys with five or more trials, has a median of **+0.09**. Cyclophosphamide is **−0.30**.
Pembrolizumab, whose first trial is 2010, manages +0.11.

*And the reason is interesting rather than merely disappointing.* Split keys by how long they
have been in the register: median correlation **+0.22** under three years, **+0.25** at four
to seven, +0.12 at eight to fourteen, **−0.01** past fifteen. The share of keys whose earliest
trials are phase 1 falls from **49% to 19%** across the same split. **A drug that works
re-enters phase 1 as a combination partner**, and its own phase sequence stops being a
sequence. The ordering is legible only while a compound is young — exactly the keys with the
fewest trials and least follow-up.

*So the boundary is:* this register compares phases in aggregate, and cannot follow one
product through its own. "The same product" in an intervention list means *this molecule
appears*, not *this programme advanced*.

### What that leaves open

**Q30. Does the young-compound subset support a real progression study?** 2,524 keys have
r > +0.3. They are small, recent and under-followed, but they are the population where the
question is actually posed. Whether they carry enough trials each to say anything is untested.

**Q31. Would an external vocabulary rescue the product key?** RxNorm or UNII would collapse
brand, code and generic names, which the shallow rule here cannot. It would not fix the
backbone problem — cyclophosphamide would still appear in 2,887 trials — so it improves recall
and leaves the semantic failure untouched. Recorded as a join worth costing before attempting.


## Sixth pass: both deadline falsifiers run, both failed to kill it

**Q16 — does the hazard spike predate the rule?** *(answered, figure 2 right — yes)* Each era
measured against its own baseline: **2008–2012 spikes 22.1x**, 2013–2016 12.8x, 2017–2020
**22.1x**, 2021–2023 25.1x. FDAAA 801's results duty bit from 2008 and the Final Rule widened
the scope in January 2017; **the earliest measurable cohort already has the full effect**. The
rule did not create the wall and did not sharpen it, which matches figure 3 finding no step in
the reporting series at that date.

**Q17 — is the spike at 365 days or at 12 months?** *(answered, figure 2 left — days)*
Restricted to the 151,345 trials with a **day-precision** completion date, so nothing is
placed by hand, and binned at seven days: **1.23%** in the week ending day 357, **2.61%**
ending 364, **3.17%** in the week containing 365, then **0.43%** — a **7.4-fold drop in seven
days**. At day resolution the three most common lags across the whole 330–400 range are **364
(1,621 trials), 365 (1,420), 363 (870)**. It is a day-count deadline, not a monthly rhythm,
and removing the hand-placed dates makes it sharper rather than softer.

**Taken together these narrow the mechanism rather than confirming a rule works.** One day
wide, present from the first cohort, unchanged by the rule that widened its scope, and 82x
concentrated among sponsors with regulatory staff — that is a compliance function executing a
date, not a rule changing anyone's mind. It also explains why figure 3's three-year rate never
moves: **the register exerts force on one day and none on any other.**

**Q30 — does the advancing subset support a real progression study?** *(answered: no, and the
number is the answer)* 2,524 keys have phase-time correlation above +0.3, but the **median
carries 7 trials**: 855 have ten or more, 248 have twenty, 49 have fifty. They cover **23,997
trials, 4.0% of the register**. And of the 855 largest, only **240 (28%)** show median start
year rising monotonically across three or more phases — **even the subset selected for
advancing mostly does not ladder.**

The largest "advancing" keys explain why: semaglutide (411 trials, 117 of them **phase 1**),
liraglutide (317), colchicine (221). These are not programmes climbing a ladder; they are
successful drugs being tested in many indications at once, which produces a positive
phase-time correlation without any sequence at all. **Figure 12's conclusion holds on its own
best case.**

## Closed

The phase-progression thread is finished. Q29 said the register cannot follow one product
through its phases; Q30 checked the most favourable subset and found it too thin and mostly
not laddered. Q31 (an external vocabulary such as RxNorm or UNII) would improve recall on the
key and leave the semantic failure untouched — a backbone agent stays a backbone agent — so it
is recorded as **not worth costing** rather than open.
