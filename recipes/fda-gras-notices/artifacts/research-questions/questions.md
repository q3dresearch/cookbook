# Asked, answered, died, open

Two questions on one dataset. Part I is what happens to a GRAS filing; part II is the
animal-food side of the same inventory. Kept separate below because the two lines of enquiry
had different dead ends.

---

## Part I — what happens to a filing

Working document, edited every time a status changes. Statuses come from the
webprobes vocabulary: `answered`, `not observable`, `tested and failed`,
`blocked`, `needs ~N months`.

**The decision they serve:** anyone doing ingredient diligence — a retailer or
brand vetting a supplier, an investor pricing an ingredient company, a journalist
or regulator auditing the pipeline — should stop reading "withdrawn" as a
resolved status and date it instead.

| # | question | status | answer |
| --- | --- | --- | --- |
| 1 | How often is a filing withdrawn rather than refused? | `answered` | 225 of 1,336 (16.8%), eleven times more often than FDA's only outright no |
| 2 | Is withdrawal getting more common? | `answered` | No. 10–21% a year across 28 years, mean 17.2%, no trend |
| 3 | Do withdrawn filings come back? | `answered` | The pooled "a third" is the average of two regimes: **51% before 2010, 29% from 2010–2022**, z = 2.78 |
| 4 | Is that fall censoring? | `tested and failed` | No. Comebacks take a median 1 year, 94% within 3, so every cohort to 2022 has had time |
| 5 | Is it a change in who files? | `tested and failed` | No. One-time filers were 35% of withdrawals before 2008 and 38% after |
| 6 | Is it a change in the mix of filer types? | `tested and failed` | No. The drop holds inside each: repeat 75%→39%, one-time 27%→15% |
| 7 | Did the substance mix shift? | `tested and failed` | No. Splitting the never-refiled at 2015 moves every category by 3–5 points, which is noise on 53 and 102 |
| 8 | Which kinds of ingredient get dropped for good? | `answered` | Synthetic or defined chemicals, 38% against an 11.6% base — 3.3× |
| 9 | What caused the break after 2007? | **open, narrowed** | Not FDA speed (flat), not composition, not one category (5 of 6 fell), not one filer type (both fell). Broad and simultaneous — so exogenous |
| 10 | Where do the vanished filings go? | **partly answered** | **At least 16 of the 155 are still permitted in food today** — 3 via food additive petition. A floor, hand-verified |
| 11 | Who are the successful notifiers, and who is not? | `answered` | Experienced filers clear **86%** against **76%** for one-and-done firms, z = +3.94 — but see the control below |
| 12 | Does a withdrawal predict a later refusal? | `tested and failed` | 20 refusals ever, 2 from a firm that had pulled one. Cells too thin |
| 13 | Does a withdrawal predict the firm's NEXT withdrawal? | `answered` | **Yes, 3.2×.** After a pull, 29% of the firm's next filings are also pulled; after a clearance, 9% |
| 14 | Does a multi-substance filing behave differently? | `tested and failed` | No. 20 of 1,336 cover several substances; 10% dropped against 12%, z = -0.23 |

### 9. What caused the break after 2007?

The comeback rate falls off a cliff between the 2004–07 and 2008–11 cohorts and
never recovers. The candidates are all outside this dataset:

* FDA's GRAS notification programme ran as a **proposed** rule from 1997 and was
  only finalised in **2016** — the whole break happens inside that limbo.
* The **2010 GAO review** of FDA's GRAS oversight.
* **NRDC's 2014 report** on undisclosed self-determinations.

**Four internal explanations tested, all dead:**

| tested | result |
| --- | --- |
| FDA got slower, so refiling got dearer | **No.** Median days from filing to closure: 177 (2004–06), 181 (2007–09), 178 (2010–12). Flat through the break |
| The substance mix shifted | **No.** Already tested at Q7 |
| One category drove it | **No.** 5 of 6 categories with enough data fell |
| One kind of filer drove it | **No.** Repeat filers 75%→36%, one-and-done 27%→13%. Both |

So the break is **broad and simultaneous** — every kind of substance, every kind
of filer, at a moment when FDA's own throughput did not move. That is the
signature of something exogenous, and it is now the only shape left standing.

**How to settle it:** a date-matched read of FDA guidance and Federal Register
notices around 2007–09, which is a different corpus. Nothing in the inventory
records why a company chose not to refile. But the shape above tells you what to
look for: a single change that reached everybody at once.

### 10. Where do the vanished filings go?

155 of 225 withdrawals have no recorded resubmission. Three fates, only one
benign:

1. **abandoned** — the product or the science did not survive
2. **refiled by another route** — FDA has noted notices it ceased to evaluate
   were later resubmitted as *food additive petitions*, a separate pathway this
   file does not track
3. **marketed anyway** — a GRAS determination requires no notice to FDA at all.
   NRDC identified 275 chemicals from 56 companies apparently sold on undisclosed
   self-determinations, including substances withdrawn more than once that stayed
   on sale.

Branch 3 is `not observable` by construction: a substance that never gets a notice
never appears anywhere. **Branch 2 has now been tested** against FDA's
"Substances Added to Food" inventory (formerly EAFUS), 3,971 permitted substances
with the 21 CFR section that allows each.

**At least 16 of the 155 are still permitted in food today**, so they did not
vanish:

| route | n | examples |
| --- | --- | --- |
| listed, no CFR section | 8 | theobromine, L-carnitine, trehalose, L-arabinose, GABA (twice) |
| GRAS by regulation (182/184) | 5 | caffeine, menhaden oil, gum arabic, grapefruit extract |
| **food additive petition (172.x)** | 3 | **polydextrose, allyl isothiocyanate, 1,3-butanediol** |

Those three are the other door working exactly as FDA described it: pulled from
the GRAS route, admitted through the petition route instead.

**The join is weak and is deliberately not used as a rate.** Both sides are
free-text chemical names. Exact matching finds 11 of 155; loosening to token
containment finds 27, of which **11 are wrong on inspection** — *White mulberry
leaf extract* matched *MUSTARD, YELLOW, EXTRACT*, and three Bacillus species
matched enzymes merely derived from them. Precision 59%. So the fuzzy pass
proposes and a human disposes; `other_door.py` carries both the accepted and the
rejected list so the judgement can be argued with.

**16 is a floor.** A substance listed under a different name is still missed.

**And the bucket is growing:** the share of withdrawals that vanish went from 49%
to 71%, so whatever is in it, there is more of it than there used to be.

### 11. Who are the successful notifiers? `answered`

744 distinct firms after normalising (843 raw strings; only trailing legal
suffixes are stripped, so "AB Enzymes GmbH" and "AB Enzymes, Inc." merge but a
leading "AB" is never eaten).

| filings by that firm | firms | filings | cleared |
| --- | --- | --- | --- |
| 1 | 502 | 502 | 78% |
| 2–3 | 184 | 413 | 73% |
| 4–9 | 50 | 264 | 81% |
| **10+** | **8** | **157** | **92%** |

Eight firms account for 157 filings and clear 92%. Novozymes North America (32),
DSM Food Specialties (17), Glycom (15) and GLG Life Tech (12) each clear 100%.
Overall, experienced filers (4+) clear 86% against 76%, z = +3.94.

**But the control cuts it down.** Experienced firms file in the easy categories,
so some of that gap is the ingredient, not the filer. Within a single category:

| category | experienced | first-timers |
| --- | --- | --- |
| Enzyme preparation | 89% (65) | 79% (43) |
| Probiotic, culture or phage | 91% (66) | 82% (100) |
| Botanical extract | 67% (12) | 62% (85) |
| Microbial or algal biomass | 54% (24) | **59% (51)** |

A 10-point headline gap becomes 5–9 points inside a category, and **reverses**
for microbial biomass. So: *both* matter, and the firm effect is real but smaller
than the raw split implies. The honest version of the advice is "who filed it
matters, and what it is matters more."

### 12. Does a withdrawal predict a later refusal? `tested and failed`

20 filings were ever refused outright and 2 of those came from a firm that had
previously pulled one. The cells are empty and no amount of care fixes that.
Recorded so it is not re-asked.

### 13. Does a withdrawal predict the firm's NEXT withdrawal? `answered`

It does, and this is the more useful version of Q12. Looking at every consecutive
pair of filings by the same firm:

| the firm's previous filing | n | next cleared | next pulled |
| --- | --- | --- | --- |
| was pulled | 112 | 69% | **29%** |
| was cleared | 459 | 90% | **9%** |

**A firm that just pulled a filing is 3.2× more likely to pull the next one.**
Withdrawal is sticky at the company level, which is what you would expect if the
binding constraint is the firm's ability to fund and defend a dossier rather than
any property of the ingredient.

### 14. Does a multi-substance filing behave differently? `tested and failed`

A filing is almost always one substance, not a formulated product with
components. Only 20 of 1,336 cover several at once — semicolon lists like
*"Chromium picolinate; Ginkgo biloba leaf extract; and Ginseng extract"* — and
they are dropped at 10% against 12% for single-substance filings, z = -0.23.

Separately, **14% of filings match more than one category rule**, but that is
description overlap rather than multiple ingredients: *"alpha-Amylase derived
from Bacillus licheniformis"* hits both the enzyme and the bacterium rule. The
classifier keeps the first match, which moves category SIZES a lot — recombinant
protein runs 85 or 18 depending on rule order — but not the slope: across 200
random rule orders the filings-to-dropout correlation stays between -0.68 and
-0.53.

---

### What each answer is FOR

Sorting per the sequence's step 9, because a recipe that only describes has
produced knowledge and no leverage.

**Describes** — Q1, Q2, Q7, Q14. True and inert.

**Predicts** — Q3, Q8, Q11, Q13. A withdrawal filed today is about half as likely
to come back as one filed in 2005; a synthetic chemical is 3.3× more likely to
vanish than the average filing; a firm that just pulled one is 3.2× more likely
to pull the next. Falsifiable: if the 2024–27 cohort's comeback rate recovers
above 40% once it matures, Q3 is wrong.

**Prescribes** — Q3 and Q10 together: *date the withdrawal before you read it.*
An old one is usually a stale record of something since settled; a recent one is
an open question, and one of the answers is "on sale under a self-determination
nobody filed".

And Q11 with Q13: *check the filer's history, not just the ingredient.* A firm
with a prior pull is three times more likely to pull again, and the eight firms
that file at volume clear 92%. But the category control says this is the second
question to ask, not the first.

### Known weaknesses in what is here

* The pre-2008 cohorts are thin: 5, 11 and 15 withdrawals. The pooled pre-2010
  figure (n=47) is the evidence; the early points on the chart are shape, not
  proof.
* A comeback is counted only where FDA records a resubmission link, so every
  comeback rate here is a floor.
* Substance categories are ours, inferred from the notice's own substance name.
  `Other` is the largest group at 454 and is not a residue — it is the
  conventional additives, which is why it sits at the bottom of the risk chart.

---

## Part II — the animal-food side

Working document, edited every time a status changes. Written **before** the
charts, which is the point: the last recipe had its questions reconstructed
afterwards from memory and lost two of them.

**The source:** FDA runs a separate GRAS notification programme for *animal*
food — feed and pet food. A company decides its ingredient is safe, tells FDA,
and FDA replies. 94 notices since 2010, published as a rendered HTML table with
no bulk export. Its human-food sibling has 1,336 and is a downloadable CSV.

**Who has a stake:** feed formulators and integrators choosing ingredients ·
investors in feed-tech and alternative-protein companies · anyone modelling
livestock nitrogen and phosphorus runoff · regulators comparing the two
programmes.

| # | question | status | answer |
| --- | --- | --- | --- |
| 1 | What is the industry actually trying to put into feed? | `answered` | **It changed.** Efficiency was 72% of 2010–14 and 10% of 2025–29. What replaced it is alternative protein |
| 2 | Do animal notices clear at a lower rate than human ones? | `answered` | **51% against 79%** |
| 3 | Is the gap refusal, or withdrawal? | `answered` | **Both, and pending too.** Withdrawn 34% vs 16.8%, refused 6.4% vs 1.5%, pending 8.5% vs 2.6%. Every failure mode elevated |
| 4 | Does the post-2007 comeback collapse appear here? | `not observable` | The programme opens in 2010. There is no "before" to compare against |
| 5 | Is 51% a small-n artifact? | `tested and failed` | No. 95% CI 41–61% against human 77–81%. The intervals do not touch |
| 6 | Do the same companies file on both sides? | `answered` | 8 do. **They clear 84% on human food and 57% on animal.** It is the programme, not the firms |
| 7 | What is "utility information not evaluated"? | `answered` | FDA clearing on safety while declining to say if it works. **0% before 2016, 23–24% now** |
| 8 | Is the programme really about ethanol co-products? | `answered` | It **was**: 77% of 2008–11. It is now 0%, and ethanol notices cleared only 33% |
| 9 | Is "efficiency not new inputs" still true? | `answered` | **No — and it is the recipe's headline.** 72% → 53% → 21% → 10% |


### Round two: the evolution of the programme

Asked after the first nine were closed, and written down before any of them was
run. The dataset has seven fields — AGRN, notifier, substance, intended use,
intended species, date of filing, FDA's letter — and the **species** field is
the one nothing has touched: 42 distinct strings across 94 notices.

| # | question | status | answer |
| --- | --- | --- | --- |
| 10 | Is the programme growing? | `answered` | **Growing.** 15 → 10 → 29 → 34 notices per four-year block |
| 11 | Pet food or livestock, and has the mix moved? | `answered` | **Moved hard.** Pet food was 1 of 18 in 2010–14 and is **11 of 21** in 2025–29 |
| 12 | Do pet notices clear differently? | `answered` | Yes, better. Pet **60% cleared / 15% withdrawn**; food-producing **53% / 35%** |
| 13 | Narrower or broader in species? | `answered` | Narrower. Broad claims were the early ethanol cohort; 62 of 69 post-2018 notices name 1–3 species |
| 14 | Does breadth cost you? | `answered` | Yes. Narrow **54%** cleared, broad **41%** — and it survives dropping ethanol (55/45) and pre-2018 (55/43) |
| 15 | Foreign or domestic filers? | `tested and failed` | 7 of 94 carry a foreign suffix. Cleared 29% against 53%, but n=7. Direction only, no claim |
| 16 | Is the withdrawal rate moving? | `tested and failed` | No trend: 33%, 24%, 47%, 19%. The last block is likely censored — 8 notices are still pending |
| 17 | Is filing concentrating? | `answered` | **The opposite.** Top-3 share fell 56% → 47% → 34% → 29%; firms per block went 10 → 9 → 23 → 18 |
| 18 | Do repeat filers do better here? | `answered` | Yes, same direction. Filed once **38%**, filed 2–3 **57%**, filed 4+ **54%** |
| 19 | How long does FDA take? | `not observable` | The table has a filing date and no closure date. Not computable from this source |
| 20 | Which species get the alternative protein? | `answered` | **Pets.** 7 of 13 protein notices, and **4 of the 6 filed since 2024** |


### Round three: what the schema itself suggests

Read off three sample rows rather than off the analysis so far. Written before
any were run.

| # | question | status | answer |
| --- | --- | --- | --- |
| 21 | AGRN is sequential — are there gaps? | `tested and failed` | **No gaps.** 1 to 94, complete. No invisible attrition |
| 22 | Does stating a dose predict a better outcome? | `tested and failed` | Looked like 39% vs 57%. The whole gap was the "utility not evaluated" group; removing it gives 39% vs 43% |
| 23 | Can refiling be detected without the field? | `answered` | **Yes.** Normalising substance names finds **18 substances filed more than once**, 41 notices |
| 24 | The animal comeback rate after a pull? | `answered` | **31%** — identical to human food's 31%. 8 of those 10 eventually cleared (human: 93%) |
| 25 | Is the engineered share growing? | `tested and failed` | Flat at 11–14% across every era. And they clear fine — 67–100%, small n |
| 26 | Organism or chemical? | `answered` | Organism-derived 57% cleared (n=44), chemical 46% (n=50). Modest and unsurprising |
| 27 | Does a more specific use statement do better? | `answered` | **Yes, and it survives three controls.** Short 31%, long 52%; livestock-only 22% vs 52%; z = +1.96 |
| 28 | Are pending notices a backlog? | `tested and failed` | No. All 8 were filed 2025 or later. Recency, not a queue |

### The two findings from round three worth acting on

**Refiling is recoverable even though FDA does not publish it.** The animal table
has no `Resubmitted` column, but normalising substance names recovers 18 chains.
Some are long: *Methylococcus capsulatus* runs 2020 pulled → 2022 cleared → 2025
pulled, all one firm. Alpha-lipoic acid was refused in 2011 and cleared in 2022,
eleven years later. Serine endopeptidase was pulled in 2024 and pulled again in
2025.

The rate that falls out is **31% come back, and 8 of 10 of those clear** — the
same comeback rate as human food. So the animal programme's first attempt fails
far more often (51% against 79%) while the *retry* behaviour is identical. What
is different is the first pass, not the persistence.

**A vague use statement predicts a worse outcome.** Splitting at the median
length of the stated use, 103 characters: short clears **31%**, long clears
**52%**. It survives dropping the ethanol cohort (31/56), dropping everything
before 2018 (29/58), and restricting to food-producing animals (22/52). z =
+1.96, which is borderline, and length is a crude proxy for specificity — but
every control points the same way.

And use statements are getting **shorter**: median 128 characters in 2010–14, 56
in 2025–29. Claims are getting vaguer at the same time FDA is increasingly
declining to assess whether they work.

### What the evolution adds up to

The programme has not just grown, it has changed subject and audience:

| | 2010–14 | 2025–29 |
| --- | --- | --- |
| notices | 18 | 21 |
| efficiency / waste-reduction | 72% | 10% |
| pet food | 1 | **11** |
| firms filing | 10 | 18 |
| top-3 share of filings | 56% | 29% |
| FDA declined to assess utility | 0 | 3 |

**It started as a corn-ethanol processing-aid channel for livestock and is now an
alternative-protein channel for pets.** Those are different industries with
different economics, and a recipe describing the first says nothing useful about
the second.

The alternative-protein beachhead is the part worth saying out loud: crickets,
black soldier fly larvae, yeast expressing an ovine protein, methanotroph
single-cell protein — **4 of the 6 protein notices filed since 2024 are for dogs
and cats, not livestock.** Pet food is also the easier door (60% cleared against
53%, and 15% withdrawn against 35%), which is a plausible reason it is being used
as one.

### The paired control, which is the strongest thing here

Eight firms file on both sides of FDA's wall. Same companies, broadly the same
dossier-writing capability, two programmes:

| firm | animal | human |
| --- | --- | --- |
| CJ CheilJedang | 43% (7) | 100% (3) |
| DSM Nutritional Products | 80% (5) | 100% (5) |
| BASF | 67% (3) | 80% (5) |
| **AB Enzymes** | **0% (2)** | **76% (25)** |
| Danisco US | 0% (1) | 100% (5) |
| Intralytix | 100% (1) | 100% (5) |
| Kemin | 100% (1) | 100% (1) |
| Kerry | 100% (1) | 0% (1) |
| **total** | **57% (21)** | **84% (50)** |

**27 points worse on the animal side, holding the company fixed.** n is small —
21 animal notices — but a within-firm comparison is the strongest design
available here, and it rules out the obvious explanation that animal filers are
simply less capable.

### What each answer is FOR

**Describes** — Q3, Q5, Q8.

**Predicts** — Q7. If "utility not evaluated" keeps climbing, "FDA has no
questions" on an animal ingredient will increasingly mean *"we checked it is
safe and said nothing about whether it does anything"*. Falsifiable: if the share
falls back under 10%, this is wrong.

**Prescribes** — Q1, Q6 and Q9 together. *Do not price an animal-food GRAS
notice off human-food base rates, and do not read this programme's history as its
present.* A feed ingredient faces roughly half the clearance odds of a human one
from the same company, and the sector the programme serves has changed
underneath the recipe that described it.

### Known weaknesses before starting

* **94 notices is small.** Any split of it is smaller. Every rate here needs an
  interval and most category counts will be single digits.
* **No bulk export.** The source is a rendered table, so the parse is
  structural and will break when FDA restyles the page.
* **The purpose categories are ours**, read off each notice's stated use — and
  they are becoming unreadable: a quarter of recent notices have no stated use
  because FDA declined to evaluate it.
* **Q6's control is 21 animal notices.** Direction is unambiguous, magnitude is
  not.
