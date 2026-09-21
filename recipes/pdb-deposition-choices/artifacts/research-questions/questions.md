# Questions, written before anything was charted

Source: the RCSB Protein Data Bank search API, `search.rcsb.org/rcsbsearch/v2/query`. No key.
**260,089 experimentally determined structures** as of the first probe, 2026-09-19.

The PDB is the record of every protein structure anyone has solved. It is read as a map of what
is known about protein shape. Like every register this project has touched, it is first a record
of **what people chose to work on**, and the interesting questions are where those two come
apart.

**Why this source and not a bulk download.** The search API does server-side faceting — terms,
date histograms and numeric histograms — so counts by method, year, organism, journal, author
and resolution come back in one request each. A recipe that would otherwise need 260,089 rows
needs a few dozen queries.

## Already visible from the screen, before any chart

- **41,156 entries — 15.8% — carry the citation "To be published".** Deposited into the
  permanent record and never written up, or written up without the deposition being updated.
- **The four most prolific depositing authors are one consortium**: von Delft 5,638,
  Arrowsmith 4,224, Bountra 3,988, Krojer 2,993 — the Structural Genomics Consortium.
- **Cryo-EM went from 65 entries in 2012 to 5,780 in 2024.** X-ray still holds 207,603 of
  260,089 all-time.
- **The second most common "source organism" is `synthetic construct`**, 12,412 entries.

## The questions

**Q1. What share of the PDB was never published, and is that share changing?**
15.8% cite "To be published". If that is stable it is a filing convention; if it is growing it
is a literature problem. *Falsifier:* the share is a fixed artefact of old entries that were
never back-updated, in which case it falls monotonically with age and says nothing about now.

**Q2. Does "To be published" ever get corrected?** A deposition is permanent; a citation is
metadata. If entries from 2005 still say "To be published", the field records the state at
deposition and not the truth, and no share computed from it means what it says.

**Q3. Did cryo-EM replace X-ray, or add to it?** The counts rise together or they do not.
*Decision:* anyone choosing a method for a new target.

**Q4. What did cryo-EM make possible that was not possible before?** Resolution and size
distributions by method and era. If cryo-EM is solving the same things at worse resolution it is
a substitute; if it is solving bigger things, it is a different instrument.

**Q5. How concentrated is the PDB by depositor?** Four SGC people are on ~18,000 entries
between them. What share of the record comes from how few groups, and does the concentration
curve look like OBIS's datasets-per-cell?

**Q6. How much of it is the same protein again?** Lysozyme, HIV protease and carbonic anhydrase
are famously re-solved thousands of times. A count of entries is not a count of proteins.

**Q7. What happened after AlphaFold?** AlphaFold DB released July 2021 and expanded to 214M
predictions in July 2022. Did experimental deposition fall, shift method, or shift target?
*Falsifier, and the one that matters:* deposition volume has trended for thirty years, so a
level comparison across 2021 will find an effect whether or not one exists. This needs the
pre-trend removed before anything is claimed.

**Q8. Is `synthetic construct` a real category or a filing shortcut?** 12,412 entries. If it
grows with the rise of designed proteins it is a subject; if it is spread evenly through time it
is a way of not answering the organism question.

**Q9. Does the register say where the work happened?** There is an author facet but no country
field seen yet. If institution or country is not recoverable, every "who does structural
biology" claim is blocked and should be recorded as such rather than approximated by author
surname.

**Q10. What does the resolution distribution say about what gets deposited?** 72,018 entries sit
in the 1.5–2.0 Å bin and 3,396 beyond 4.0 Å. Is the floor a limit of the methods or a threshold
of what people think is worth depositing?

## Answered so far

**Q1 — what share was never published, and is it changing?** *(answered, figure 1)* 15.8%
overall. By deposition year it is a U: 1.2% in 1995, **26.2% in 2007**, 11.5% in 2018, then
apparently rising again. The 2007 bulge is structural genomics. The recent rise is
right-censoring and is drawn dashed — Q12 below now measures it rather than reasoning about it.

**Q2 — does "To be published" get corrected?** *(answered — no)* If it did, the share would
decay with cohort age. It does not: a 28-year-old cohort sits near 2% and a 19-year-old one
near 26%. The driver is the era the work was done in. **The field records the state at
deposition and nobody revisits it**, which means no share computed from it is a statement about
what is in the literature today.

**Q3 — did cryo-EM replace X-ray?** *(answered — no)* X-ray deposited 7,544 in 2010 and 10,130
in 2024, through the whole period cryo-EM grew from 53 to 7,067. A share rose to 42% and
displaced nothing. NMR is the one method that fell, 557 to 271.

**Q4 — what did cryo-EM make possible?** *(answered — bigger objects)* Two axes disagree and
the disagreement is the answer. Resolution: X-ray median 2.00 Å with 2.0% beyond 3.5 Å, cryo-EM
3.25 Å with **37.4%** beyond. Size: X-ray median 50 kDa with 1.3% over 500 kDa, cryo-EM
**250 kDa** with **28.6%** over, p90 1,300 against 150. The resolution is the price of the
object, not a compromise on the same object.

## Added after the first two figures

**Q11. What did COVID do to the target list?** The two most-solved proteins in the entire PDB
are both SARS-CoV-2 — `P0DTD1` replicase polyprotein at 3,722 entries and `P0DTC2` spike at
2,267. Beta-2-microglobulin is third at 1,401. A pandemic is visible in a structural target
list, and the question is how much of 2020–2023 it is. *Decision:* anyone reading deposition
volume over those years as a measure of the field's capacity rather than its subject.

**Q12. How long after deposition does the paper appear?** `rcsb_primary_citation.year` is
facetable inside a deposition-year cohort, so the lag distribution is measurable. This replaces
the reasoning in figure 1 with a number: if the median paper lands one year out, a 2023 cohort
is essentially complete and a 2025 one is half-resolved, and the censored band can be drawn
where the data says rather than where it looked right. *Falsifier:* the lag is itself changing
over time, in which case a single correction is wrong and each cohort needs its own.

**Q13. How concentrated is the target list?** 200 accessions are fetched. If the PDB looks like
OBIS — a median cell that is 45% one dataset — then a count of entries is a count of *attention*
and not of proteins, and every "we know N structures" claim needs the distinct-protein
denominator instead.

**Q14. Is a depositor-name facet usable at all?** `Edwards, A.` has 2,698 entries and
`Edwards, A.M.` has 2,331 — **the same person, split by the register**. Any concentration curve
over depositors must normalise first, and the size of the correction is itself worth reporting
because it bounds how wrong an un-normalised version would be. *This is the same class of error
as joining on a name in the last recipe, which matched 0 of 7,517 rows.*

**Q15. Are the 7,839 entries with 20 deposited models a different kind of object?** NMR
produces ensembles, not single structures. If model count separates cleanly by method then
"one entry" means two different things and every count in this recipe is mixing them.

## Added after the target and AlphaFold figures

**Q16. Are the PDB's most common ligands biology, or what was in the drop?** The top four are
`MG` 28,821, `SO4` 28,264, `ZN` 27,910 and `GOL` 26,231 — magnesium, sulfate, zinc and
glycerol. Sulfate and glycerol are a buffer component and a cryoprotectant. `EDO` 17,821 is
ethylene glycol, also cryoprotectant; `NI` 2,431 is nickel left over from His-tag purification.
*The complication that makes this a question rather than a joke:* magnesium and zinc are **both**
buffer components and genuine catalytic metals, and nothing in the entry says which this one is.
So the honest output is three buckets — clearly additive, ambiguous metal, clearly biological —
with the ambiguity sized rather than resolved. *Decision:* anyone mining PDB ligands for
binding-site statistics or drug discovery.

**Q17. How many structures have no ligand at all?** 63,155 entries — 24% — carry zero
non-polymer entities. An apo structure is a legitimate result, but a "fraction of proteins with
a known bound partner" computed off this register needs that denominator stated.

**Q18. Is structural biology a methodological monoculture?** 173,631 of 200,289 entries with a
recorded temperature were collected at **100 K** — 87%. 34,197 of 36,700 cryo-EM entries are
**single particle** — 93%. Crystallography's top three space groups take about half of it, with
`P 21 21 21` alone at 46,922. A field with one way of doing things has a correlated failure
mode, and none of the three shares is visible from any single entry. *Falsifier:* the
concentration is a property of what is *solvable* rather than of practice, in which case it
should be stable over time rather than tightening.

**Q19. Does resolution improve, or does the field attempt harder things?** Methods have
improved for thirty years. If median resolution is flat anyway, the gains were spent on harder
targets rather than better pictures — which would be the same shape as the retired cryo-EM figure's size finding,
on a different axis.

**Q20. How long is the embargo?** Deposit and release dates are both available and differ by up
to 2,203 entries a year. The gap per entry is the hold period a depositor chose. If it varies by
depositor type, "open data" means different things to different filers.

**Q21. What happened to NMR?** It is the one method that actually fell — 557 depositions in 2010
to 271 in 2025. Displaced by what, and for which targets? It solves small things in solution,
which is exactly the niche cryo-EM did *not* take.

## Screens to run before building

- Does the same query return the same counts twice? The PDB grows weekly; every figure is a
  statement about one fetch and must say so.
- Does a nonsense attribute return an error or a silent unfiltered total? Four parameters in the
  last recipe returned the unfiltered total without complaint.
- Is the year field the deposition date or the release date? They differ by months to years, and
  a figure about "when work happened" that uses release date is measuring the embargo.

## The prescriptive round, and the boundary it ran into

Everything above is descriptive. Asking what the register can tell someone to *do* hits one wall
immediately, and it is worth writing down because it kills a whole family of questions at once.

**The PDB contains only successes.** No protein that resisted every method is in it. So *success
rate by method* is not computable here at any quality, and **"will this work on my target" is
not a question this register can answer** — not badly, not at all. Three questions survive that
boundary because they ask about practice rather than outcome.

**Q22. At what size does the field switch method, and has that moved?** — **answered, figure 8.**
Cryo-EM's share crosses 50% at **1,530 kDa in 2012–2016, 315 kDa in 2017–2021, 133 kDa in
2022–2026**, and in 2005–2011 it never crosses at all (X-ray held 79.5% even above 1000 kDa).
Eleven-fold in ten years. The *bottom* end did not move: below 50 kDa X-ray is at 90.9% and
cryo-EM at 4.0%, about where they were twenty years ago. The boundary swept down through the
middle and stopped.

**Q23. Does cryo-EM's growth curve support a crossover forecast?** — **answered, and the answer
is no, informatively.** Fitted 2012–2019 the growth is +57.2% a year at **R² 0.99**, and that
fit **over-predicts 2025 by 74%** (25,147 against 6,453). The rate is itself decaying by about
half every three years: +65%/yr over 2015–2018, +56% over 2018–2021, **+22% over 2021–2024**. A
constant-rate model cannot represent that and fails in the same direction every time. Three fit
windows give "already happened", "2027" and "never", and the spread between them is the
forecast. *Confound separated:* 2025 is down register-wide (all −13%, X-ray −14%, cryo-EM −9%),
so the deceleration was checked at the 2024 peak too, where the fit still over-predicts by 56%.

**Q24. What resolution should someone expect for a given size and method?** — **answered, figure
9, with the register showing its own survivorship.** X-ray's median degrades monotonically with
mass, 1.75 → 3.00 Å; **cryo-EM's is flat at about 3.25 Å across a fifty-fold range**. X-ray leads
on the median in *every* band including the largest — and that is the trap. Above 1000 kDa there
are **701** X-ray structures against **5,040** cryo-EM ones, so the X-ray figure is a survivors'
average that reads better the harsher the filter behind it. The median is a fair expectation
below about 100 kDa and is the score of the winners above a few hundred.

### What these three opened

**Q25. Is the crossover weight a property of the instruments or of the queue?** The boundary
moved 133-fold-to-11-fold down while cryo-EM's *resolution* stayed flat at 3.25 Å. If the
instrument had improved, resolution at a fixed size should have improved with it. It did not, so
the boundary may be moving because of access and cost rather than capability. *Test:* median
cryo-EM resolution in the 100–200 kDa band, by year. Flat means the switch was economic.

**Q26. Does the 2021 deceleration appear in facility count?** The growth decay is measured in
depositions. If the number of distinct depositing institutions flattened at the same time, the
constraint is instruments; if institutions kept growing while depositions per institution fell,
it is something else. The depositor facet exists and was used for figure 2.

**Q27. How filtered is the X-ray column, really?** Figure 9 argues the 701 large X-ray
structures are survivors, but argues it from a count, not a measurement. Deposited-model count,
ligand count and space group are all available per entry — if the large X-ray survivors are
systematically the *most symmetric* ones, that is the filter made visible rather than inferred.

**Q19 is half-answered and the remaining half is sharper.** Figure 9 did resolution against
size. Resolution against *time at a fixed size* is the version that separates better instruments
from harder targets, and Q25 is that question with a specific band attached.

**Q21 is mostly answered.** NMR's surviving share is entirely below 50 kDa — 57 entries in the
whole 50–100 band, 4 above 200. Cryo-EM never took that niche. NMR did not lose ground to
cryo-EM; it held a band nothing else entered, and that band stopped growing. Why it stopped is
still open.

## The redundancy pass, and what re-encoding turned up

A read-through of all ten figures asked a different question from the usual one: not *is this
true* but *is this drawn*. Five of them were ranked bar lists with the counts printed beside
the bars — a table with a slow rendering step. Re-encoding them was supposed to be
presentation work. It was not: four of the five produced a new finding, one produced a
correction, and one figure turned out to be redundant and was retired.

**The cryo-EM figure was cut.** Its left panel drew the same per-year method series as the forecast figure and its
right panel was two one-axis strips — a resolution median and a mass median, per method —
asserting "different objects" by printing two numbers side by side. The crossover and resolution
figures cross those axes instead, and the resolution one found the survivorship trap that was
invisible while they were separate. The retired plate and the reason stay in the drafting
workspace, which is not published.

**Q18 is answered, and the question had three subjects.** Faceting each dominated field by
deposition year: 100 K went 80.1% to 89.1% (+9.0 pts), single-particle 80.3% to 93.5%
(+13.2 pts), and `P 21 21 21` **did not move** — 21.7% to 22.2%, wandering 19.6% to 27.2% with
no trend across twenty years. Two are practice and one is a property of crystals. Reading all
three as one "monoculture" claim merged a fixable habit with a fact about proteins.

**Q22 (new, answered). Can a declared classification be tested rather than asserted?** Yes,
where the world supplies a mechanism. Crystallisation additives are artefacts of growing a
crystal, so they should be scarce in cryo-EM entries. They are — but so is everything found in
small proteins, and cryo-EM does big ones: rho **+0.94** between a component's cryo-EM share
and the share of its host entries over 200 kDa. Conditioned on that, **15 of 16 declared
additives fall below prediction by a median 27.7x**. The test also corrected four labels:
potassium, sodium, chloride and phosphate were filed as additives and behave like the
physiological ions they also are, sitting at 0.9x to 2.4x.

**Q23 (new, answered, and it is a methods finding). Does the functional form decide it?**
Here, completely. Fitted **linearly**, the additive residuals average **+0.5 points with mixed
signs** — the classification tests negative. The linear fit predicts a *negative* cryo-EM share
for eight components, which cannot happen, and the positive residuals it manufactures against
that floor are its entire null. Fitted in **log-odds**, the shape a bounded share actually has,
the effect is 27.7x and one-directional. Both fits are on the plate.

**A correction to the forecast, kept visible.** Figure 7 previously offered three scenarios and
argued the spread between them *was* the forecast, including one where the deceleration
continues and cryo-EM "levels off below X-ray". **That scenario was asserted and never
computed, and it is wrong** — the decay model still compounds to about 4.2x the 2024 level.
Computing it properly gives six scenarios (two cryo-EM models x three X-ray trajectories) that
all cross in **2026, 2027 or 2028**. The honest finding was the opposite of the one written
down: respecting the deceleration *narrows* the forecast, and the only disagreement left is
between the falsified R² 0.99 fit and everything else.

**A defect in the register's own ordering.** The terms facet returns the top 200 accessions by
count but **not in count order** — 35 of 200 arrive out of sequence. Figure 3 had been plotting
facet order on an axis labelled "rank" since it was built. Sorting first moves the rank-size
fit from R² 0.77 to **0.88**, so part of the shape being described was the API's ordering. And
once sorted the finding changes: the target list is an **ordinary power law** and the replicase
sits only **1.6x above the fitted line**, so what is notable about the head is which proteins
are in it, not how far they stand out.

**Figure 2's axis was spent on a rule-out.** The old panel sorted 40 depositors by unpublished
share on one axis. Plotting entry count against it gives **rho +0.16** — size explains nothing,
and the pile is one programme rather than prolific depositors. Bubble area carries a second
question the rate cannot answer: JCSG has the highest *rate* at 86.4% and owns about 1,386
unwritten entries, while von Delft runs 48.7% and owns **2,760**, twice the pile at half the
rate.

### What the pass opened

**Q28. Does the space group's flatness survive stratification?** It did not move in aggregate,
but the register's *targets* changed enormously over the same twenty years. If the flat line is
two moving populations cancelling — say membrane proteins rising while soluble enzymes fall —
the "property of crystals" reading is wrong. *Test:* the same series split by molecular weight
band.

**Q29. Is the cryo-EM deceleration visible in facility count?** The rolling rate fell from +65%
to +9.8%. If distinct depositing institutions flattened at the same time, the constraint is
instruments; if institutions kept growing while depositions per institution fell, it is not.

**Q30. Do the four reclassified ions behave like cofactors on a second axis?** Potassium,
sodium, chloride and phosphate sit on the size line. That is one test. A genuine cofactor
should also track its host's *function*, not just its mass — the organism facet or an EC-number
field would be an independent axis, if one exists.
