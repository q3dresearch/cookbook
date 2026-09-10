# Questions this recipe asks

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

## 9. What caused the break after 2007?

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

## 10. Where do the vanished filings go?

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

## 11. Who are the successful notifiers? `answered`

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

## 12. Does a withdrawal predict a later refusal? `tested and failed`

20 filings were ever refused outright and 2 of those came from a firm that had
previously pulled one. The cells are empty and no amount of care fixes that.
Recorded so it is not re-asked.

## 13. Does a withdrawal predict the firm's NEXT withdrawal? `answered`

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

## 14. Does a multi-substance filing behave differently? `tested and failed`

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

## What each answer is FOR

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

## Known weaknesses in what is here

* The pre-2008 cohorts are thin: 5, 11 and 15 withdrawals. The pooled pre-2010
  figure (n=47) is the evidence; the early points on the chart are shape, not
  proof.
* A comeback is counted only where FDA records a resubmission link, so every
  comeback rate here is a floor.
* Substance categories are ours, inferred from the notice's own substance name.
  `Other` is the largest group at 454 and is not a residue — it is the
  conventional additives, which is why it sits at the bottom of the risk chart.
