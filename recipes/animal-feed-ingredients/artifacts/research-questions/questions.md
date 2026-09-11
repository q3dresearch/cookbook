# Questions this recipe asks

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


## Round two: the evolution of the programme

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


## Round three: what the schema itself suggests

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

## The two findings from round three worth acting on

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

## What the evolution adds up to

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

## The paired control, which is the strongest thing here

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

## What each answer is FOR

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

## Known weaknesses before starting

* **94 notices is small.** Any split of it is smaller. Every rate here needs an
  interval and most category counts will be single digits.
* **No bulk export.** The source is a rendered table, so the parse is
  structural and will break when FDA restyles the page.
* **The purpose categories are ours**, read off each notice's stated use — and
  they are becoming unreadable: a quarter of recent notices have no stated use
  because FDA declined to evaluate it.
* **Q6's control is 21 animal notices.** Direction is unambiguous, magnitude is
  not.
