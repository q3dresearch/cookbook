# Open questions

**The test:** would answering it change the decision — that age is the wrong screen
for picking rules to review, that the quadrant is a better one, that the genre
correction must not be carried across titles, and that eight expired rules can be
deleted with no policy argument? By that test **no question is live**.

One was live and was settled before publishing; it is recorded first because the
answer changed how every number here should be read.

## 0. SETTLED — Does uneven date coverage break the quadrant?

Only 35% of Title 12 sections carry their own Federal Register source note. If the
covered ones were a biased sample *within* their parts, the neighbourhood
comparison the whole quadrant rests on would be noise, and the decision would go
with it.

| restriction | n | Settled | Fossil |
| --- | --- | --- | --- |
| all parts | 2,440 | 9.1% | 40.7% |
| parts ≥10 dated sections | 1,719 | **9.7%** | 40.5% |
| parts ≥50% dated | 1,632 | 8.1% | 42.8% |
| parts ≥80% dated | 812 | **3.8%** | **59.7%** |

Demanding more *peers* — what actually makes a neighbourhood median mean anything
— leaves the populations flat. Demanding more *coverage* moves them hard, because
coverage tracks part **size**: parts at 80%+ hold a median of 7 sections against
14 for parts under 50%, and are older (12.8y vs 9.3y). Small old parts freeze
together and pile into Fossil. Composition shift, not method failure.

**Consequence, and it is carried through the whole recipe:** the *list* survives
and the *rate* does not. Every share published here is a share of the covered set,
not of the title. Settled is a **candidate list** — sections frozen while their
*known* neighbours moved. What the undated siblings did is unknowable by
construction, so an entry can be wrong.

## 1. Is the interpretation tail general, or a Federal Reserve habit?

Two titles is two. Banking puts 39% of its 30-year tail in a subject group the
publisher labels `Interpretations`; Labor returns 6% on the same detector and 12%
on a prose detector built for it. Whether either shape is typical of the other 48
titles is untested.

**How to settle it:** one `capture.py` run each for Title 46 (Shipping) and Title 7
(Agriculture), then `chart_control.py` with a third and fourth series. Roughly an
hour of unattended fetching per title. **Not live** because the finding it would
extend — verify the label per title, never assume it — already holds on the
evidence that Labor's differs from banking's. A third title agreeing with banking
would not restore a correction that demonstrably fails on Labor.

## 2. What is in the 65% of sections with no parsable date?

2,493 of 7,180 Title 12 sections carry their own source note. 3,175 inherit one
from their part and 1,250 have none. Inherited notes sit under *actively amended*
parts, so every old-section count here is a **floor**.

**How to settle it:** parse part-level source notes and treat them as an upper
bound on the sections beneath, then report each figure as a range rather than a
point. **Not live** because a floor moving up strengthens the case for the
quadrant rather than weakening it — more old text means age is an even worse
screen.

## 3. Eight expired rules in banking and zero in labour law — habit, or a sample of two?

Eight Title 12 sections have passed an expiry date set in their own text. Title 29
has none. That is either a real difference in drafting practice or two titles.

**How to settle it:** run `sunset.py` over more titles — it needs no new capture
beyond the raw store, and the scan takes seconds. **Not live** because the eight
are individually verified and individually actionable regardless of what the rate
turns out to be.

## 4. What do the 44 undated sunset clauses do?

53 sections set their own expiry; 44 give no date. Some are conditional on an
agency decision — "until the Board determines" — which may already have happened.

**How to settle it:** each one needs the text of its triggering action, which is a
Federal Register search per section, not a query. 44 is small enough to do by hand
and nobody has. **Not live**, but this is the most likely place a second batch of
dead letter is hiding.

## 5. A rule can be dead without saying so

`sunset.py` finds only rules that announce their own expiry. A rule whose enabling
statute was repealed is just as dead and silent about it.

**How to settle it:** a join from each section's authority citation to the US Code,
looking for repealed or superseded authority. That is a different dataset and a
much larger project — it is the "laws that should not be there" question in its
general form, and this recipe answers only the self-declaring corner of it.

## 6. Which part is about to be opened?

Removal is a one-shot part-level event: 43 of the 55 parts that lost three or more
sections lost every one on a single day. So "which section will be removed next"
has no answer. "Which part is about to be opened" does, and it would make the
dead-letter list actionable on a schedule rather than opportunistically.

**How to settle it:** the Unified Agenda of Regulatory and Deregulatory Actions
publishes planned rulemakings by agency and part. Joining it to this would say
*which* dead text is about to have someone standing next to it. **Not live** — the
list is worth handing over regardless — but it is the highest-value next join.

## 7. Do the functional categories mean anything outside our own keywords?

Only `Interpretation` comes from the publisher. The other thirteen categories are
keyword rules over section headings, 28% of sections match none of them, and
institution names had to be stripped first — "Farm Credit" and "credit union" were
22% of the *Lending & credit* bucket before that.

**How to settle it:** score the classifier against a hand-labelled sample, or
replace it with the industry classification RegData already publishes. **Not live**
for the age findings, which do not depend on the categories; it *is* load-bearing
for the lifecycle chart, which is why that chart names its own construct in the
caption.

---

## Answered, and what answered them

| question | answer | figure |
| --- | --- | --- |
| When was each rule last changed? | Title 12 median 9.8y; 194 sections at 30y+; oldest 79.7y (§ 220.101, 1946) | `cfr-staleness-title12` |
| Is the old tail neglect? | Not in banking — 39% of it is the `Interpretations` genre, superseded not edited | `cfr-staleness-title12` |
| Does that correction travel? | No, and it fails silently. Labor: 6% on the shipped detector, 12% on a prose one, against banking's 39% | `cfr-control-title29` |
| Can frozen be told from forgotten? | Yes, by the part neighbourhood — 226 sections are frozen inside parts their agency reopened | `cfr-settled-vs-fossil` |
| Does high churn mean a broken rule? | No — 7 of the 20 most-amended sections are titled "Definitions"; that is coupling | (prose) |
| Is a young median a diligent regulator? | Not necessarily — CFPB cannot hold a rule older than 2011 and its box ends there | `cfr-age-by-agency` |
| Is the code pruned? | Barely. 1,588 removals since 2017, 836 on one day; routine removal is ~78 a year | `cfr-growth-vs-removal` |
| Do rules set their own expiry? | 53 of 14,451 — under half a percent — and 44 of those give no date | `cfr-dead-letter` |
| Are any past it and still in force? | 8, all in banking, 3 of them amended *after* their own death date | `cfr-dead-letter` |
| Why does nobody catch them? | Removal is a one-shot part-level act; § 208.23 survived part 208 losing 8 other sections in 2019 | `cfr-removal-shape` |
| Can you predict which section is removed next? | No — there is no attrition to fit. The predictable unit is the part, and its trigger is a rulemaking calendar | `cfr-removal-shape` |
| What does the code add? | Whatever a statute just ordered — Capital & risk is 84% written since 2010 | `cfr-lifecycle` |
| What does it abandon? | Interpretation (95% stale) by design; consumer disclosure (53% new *and* 62% stale) by accretion | `cfr-lifecycle` |

## Retracted before publishing

* **"Settled: 178 sections."** `part_activity` claimed to compare a section to
  "the other sections in its part" and included the section itself, dragging every
  point toward the diagonal. The real figure is **226**, understated by 27%.
* **"The code accretes; it is almost never pruned."** The chart's own bars showed
  1,588 removed against 1,215 surviving creations in the measured window. Retitled
  to a claim the geometry supports, and a true net was found to be unrecoverable —
  the version feed opens with a 2016–17 baseline load.
* **33, then 211, then 9 expiry hits.** The detector read dates out of source-note
  citations, treated "shall be effective" as a sunset, and matched "shall not
  apply", which is scope. The real number is **8**. Believe the list, not the
  count — it is short enough to read, and it was read.
