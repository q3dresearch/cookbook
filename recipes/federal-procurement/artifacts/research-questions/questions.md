# USAspending: a register where the plan and the outcome sit in the same row

## The statute, read before the schema

**FFATA** — the Federal Funding Accountability and Transparency Act of 2006, amended by the
**DATA Act of 2014** — requires every federal award over $25,000 to be reported to a single
public site, with the agency, the recipient, the amount and the place of performance. The
**FAR** (Federal Acquisition Regulation) governs how the contract itself is competed, awarded
and modified.

**Two duties, and they are different in a way that matters here.** FFATA compels *disclosure*
of an award. The FAR governs the *conduct* of it. So this register records both what was
promised and what the promise became, which is rarer than it sounds.

**What the statute predicts about the schema.** A contract is not one number. The FAR
distinguishes:

- the **base** value — what was awarded at signature
- the **current** value — base plus exercised options and modifications
- the **potential** value — base plus every option if all are exercised

If all three are carried per award, then **contract growth is measured per row rather than
estimated**, and the plan-versus-outcome comparison that ClinicalTrials.gov destroys on
update is available here by construction. *That is the reason for picking this source and the
first thing to verify.*

**What else the FAR creates that should be visible.** Competition is a rule, not a habit: an
award records the extent it was competed and, where it was not, the **statutory authority for
that exception**. Sole-source awards must name the citation permitting them. A register that
carries the exception code is a register where "uncompeted" is a category with reasons
attached rather than a residual.

## Screens to run before building anything

Standard for this project, plus four specific to a money register:

- **The same query twice.** The register is updated daily and revised retroactively.
- **A nonsense field and a nonsense value.** Loud or silent? A silent unfiltered total has
  cost this project real findings.
- **Paging.** Send a nonsense page token and an out-of-range page. A truncated first page that
  looks complete is a sorted sample.
- **Does the API sort by the thing being modelled?** If the default order is by value, any
  prefix is a biased sample of exactly the variable under study.
- **Do the money fields mean what they say?** Obligated, current, potential, and the
  *change* fields. Test on a known large award where the answer is checkable.
- **Are modifications rows or revisions?** If a modification is a new row sharing a key, the
  key is not unique and a naive count of "awards" is a count of paperwork. **Count the key
  before diffing anything.**
- **Is a negative obligation a thing?** De-obligations are real and reduce the total. A sum
  that assumes non-negative is wrong in a way that never errors.
- **Fiscal year versus calendar year.** The US federal year starts 1 October. A series binned
  on the wrong one is shifted by a quarter and will still look plausible.

## Questions, before any data

**Q1. How much do contracts grow after award, and is growth a property of the contract or of
the buyer?** Current value against base value, per award. If the register carries both, this
is a subtraction rather than a model.

**Q2. Is growth concentrated, or is it the norm?** A median near zero with a long tail is a
different world from a uniform 10% drift, and they imply opposite interventions.

**Q3. Does competition predict growth?** The FAR records how an award was competed. If
uncompeted awards grow more, that is the register scoring its own rules. *Falsifier:*
competed and uncompeted awards grow alike.

**Q4. Who wins repeatedly, and does that change what they are paid?** Concentration by
recipient, and whether incumbency shows up in growth rather than in award count.

**Q5. What fraction of "awards" are actually modifications?** The key-uniqueness question,
asked before any total is quoted. In an earlier recipe a non-unique key manufactured a
dramatic finding out of two rows.

**Q6. Does agency explain more than contract type?** Both are available; a pooled growth rate
that averages over agencies with different missions is the same failure as a pooled reporting
rate averaging over sponsor classes.

**Q7. What is invisible?** Awards under the reporting threshold, classified work, and
anything a modification does not have to state a reason for. The register's own denominator
is not the volume of federal buying.

**Q8. The arbitrage question, asked early because the answer may be different here.** Unlike
every other recipe in this fleet, the actors are **companies, many of them listed**. Per
[`arbitrage-policy.md`](../../../webprobes/doctrine/arbitrage-policy.md) this may be the first
exit 2 or 3 rather than exit 1 — and if it is exit 3, that has to be decided before
publication, not after.

## The population problem, measured before it was chosen

**Contract awards, FY2024, by awarding agency:**

| agency | awards | share |
| --- | --- | --- |
| **Department of Defense** | **4,065,956** | **68.6%** |
| General Services Administration | 1,358,892 | 22.9% |
| Veterans Affairs | 95,454 | 1.6% |
| Justice | 62,634 | 1.1% |
| Health and Human Services | 59,302 | 1.0% |
| Agriculture | 54,712 | 0.9% |
| Homeland Security | 46,012 | 0.8% |
| Interior | 34,508 | 0.6% |
| Transportation | 19,839 | 0.3% |
| Commerce | 13,192 | 0.2% |
| NASA | 10,288 | 0.2% |
| Environmental Protection | 7,551 | 0.1% |
| Energy | 6,637 | 0.1% |
| **all agencies** | **5,927,888** | |

**Two agencies are 91.5% of the register.** Every other department combined is under 9%, and
the largest civilian department outside GSA is 1.6%.

**So "federal procurement" is a phrase that has to be qualified before it is used.** A recipe
that quietly excludes DoD — because it is large and awkward to fetch — is a recipe about the
31% tail presented as if it were the whole. That is the failure an earlier recipe in this
fleet recorded when a national waste series turned out to be 81% one firm.

**The decision, to be made against the download cost and stated on every plate:**

1. **Include DoD** if the fetch is affordable. It is the register.
2. **If it is not**, the population is *civilian agencies excluding GSA*, the share it
   represents is printed on every figure, and no claim is made about federal procurement as a
   whole — only about the departments in it.

A third option that looks attractive and is not: sampling DoD. The bulk endpoint filters by
agency and date, not by value or by random draw, so any DoD subset available cheaply is a
*time* slice, and a time slice of one agency is a seasonal artefact waiting to be mistaken for
a trend.

**Note also what the award count is counting.** Commerce FY2024 returned 13,192 *awards* from
the count endpoint and 15,810 *transactions* from the download — 1.2 rows per award, because
the download is keyed on action date and picks up modifications to older awards. The two
numbers answer different questions and neither is "how many contracts did Commerce sign".

## Second pass: what the screens changed

Four screens run on Commerce FY2024, 15,810 transactions. Each would have silently corrupted a
figure, and two of them killed a question as posed.

**The money columns do not mean what their names suggest.** `base_and_all_options_value` is a
**transaction-level** field — it equals that action's own obligation on 69% of rows and is
`0.00` on modifications. It is *not* the award's base value. Dividing
`current_total_value_of_award` by it produced a growth ratio with a **maximum of 4.8 billion**,
which is the tell. The two fields that are genuinely award-level and comparable are
`current_total_value_of_award` and `potential_total_value_of_award`, and they pass their own
sanity check: current exceeds potential on **0.0%** of awards, exactly as the FAR requires.

**So Q1 is re-posed.** "How much do contracts grow after award" cannot be asked as current
against base from a transaction file, because the base is not in it. It becomes **how much of
the potential value is actually exercised** — `current / potential`, which is a real quantity
with a real boundary at 1.0. On Commerce FY2024: median **1.00**, and **30% of awards leave
options unexercised**.

**12.4% of transactions carry a negative obligation.** De-obligations are ordinary. Summing
only positives overstates Commerce FY2024 by **6.9%**, and nothing errors.

**62% of rows are modifications.** Only 38% carry `modification_number == '0'`. Any count of
"awards" from a transaction file is a count of paperwork unless it collapses the key first.

**The key is sound, which was worth checking rather than assuming.** `award_id_piid` and
`contract_award_unique_key` both give 11,414 distinct on 15,810 rows, and **zero** piids map to
more than one award. Grouping on either is safe.

### The new question the screens created

**Q9. The award-level running total is not monotone, and that breaks the obvious estimator.**
With the correct key, `current_total_value_of_award` moves *backwards* between consecutive
modifications — 2,980,723 → 2,448,112 → 2,980,723 within days on the same award. Across
multi-transaction awards the potential value is non-decreasing on only **89%**. So **11% of
awards report a running total that goes down and comes back**.

**Two different columns, two different rates, and they were conflated above on first
writing.** Measured separately on Commerce FY2024's 2,584 multi-transaction awards:

| column | behaviour |
| --- | --- |
| `potential_total_value_of_award` | non-decreasing on **89%** — 11% fall and recover |
| `current_total_value_of_award` | goes backwards at least once on **30%** |

The one this recipe uses as the numerator is `current`, so **30%** is the rate that matters,
not 11%. That matters because "growth = last minus first" is a coin flip on nearly a third of
multi-transaction awards. The estimator has to be a stated choice — the loader takes the
**maximum** observed value rather than the last — and the share it is protecting against gets
reported rather than smoothed.
*Falsifier:* if the non-monotone awards are concentrated in one agency or one contract type,
it is a reporting practice rather than a register-wide property.

**Q10. Does the negative-obligation share differ by agency or competition?** A de-obligation is
money taken back. If uncompeted awards de-obligate more, that is the register scoring its own
rules from the other direction — and it is the same measurement as Q3 with the sign flipped.

**Q11. What is a "contract" for counting purposes?** Three defensible units live in one file:
transactions (15,810), awards (11,414), and base actions (6,022). Every headline in this recipe
has to name which, and the three differ by more than a factor of two.

## The fetch plan, and why it is two files

| file | scope | job | cost |
| --- | --- | --- | --- |
| all-agency FY2024 | every agency, one year, **includes DoD** | cross-sectional | generating over 50 minutes |
| civilian FY2015–24 | 11 departments, ten years, **8.5% of awards** | longitudinal | one request per year |

Generation time is the binding cost, not bytes: GSA for one month took **530 s** to build and
is 21 MB; one month of DoD did not finish in ten minutes. Requesting a decade as a single range
would mean a failed generation costs ten years of waiting, so the civilian file is fetched year
by year and checkpointed.

**Neither file alone can carry a claim about federal procurement.** The first has DoD and no
time; the second has time and 8.5% of the awards. Every figure names which it used and what
share of the register that is.

## Third pass: the deep dive, with numbers attached

Civilian FY2016, 554,171 awards. Each of these was measured before being written down.

**Q12. Three in five awards receive exactly one offer.** `number_of_offers_received`:
**59.4%** got one, 9.6% two, 21.2% three to five, 9.6% six or more, 0.3% blank. This is a
competition measure **independent of `extent_competed`**, which is a procedural category — an
award can be "competed" and still draw a single bid. *What predicts a single offer, and does
the procedural label agree with the bid count?* Single-offer awards have 27% ceiling coverage
against 30% overall.

**Q13. The schedule has a plan-versus-outcome pair, and it is fully populated.** Every award
carries both a current end date and a **potential** end date, the second being where the
performance period reaches if every option is exercised. Both present on **554,148 of 554,171
awards — 100.0%**, against 30% for the money ceiling. **17% have a potential end later than
the current one**; **0.0%** have the impossible reverse.

*This is the recipe's escape route.* The money question is crippled by missingness that
correlates with the variables of interest. **The time question is not.** Median current
duration is 73 days, p25 30, p90 383.

**Q14. Awards and dollars concentrate on different scales.** 78,615 distinct recipients. The
top 100 hold **22.2% of awards but 48.3% of dollars**; the top 1,000 hold 45.9% of awards and
**78.0% of dollars**. Any "concentration" claim has to say which base — the two answers differ
by more than two to one, which is the same trap an earlier recipe recorded as *tons or firms*.

**Q15. Set-asides vary in documentation by more than they vary in use.** 22 distinct values.
No set-aside 408,843 awards at 29% coverage; small-business total 96,215 at 31%; service
disabled veteran owned 12,222 at **21%**; 8(a) sole source 9,902 at **38%**. *Is a reserved
award documented differently, and does that survive holding agency fixed?*

**Q16. Small business is half the awards — what share of the dollars?** 52.4% of awards are to
a small business by the contracting officer's own determination, 47.6% are not, and ceiling
coverage barely differs (31% against 29%). The award share is known; the dollar share is the
question, and the answer decides whether "half of contracts go to small business" is a
meaningful sentence.

**Q17. Place of performance is complete and usable.** 60 distinct state codes, **0.0% blank**,
led by CA, MD, VA, DC, TX, FL. Rare in this fleet: a geography field with no missingness. *Does
where the work happens differ from where the recipient is, and does either predict competition
or documentation?*

### What the deep dive settles about the recipe's shape

The money ceiling is **30% populated and missing-not-at-random**. The schedule pair is **100%
populated**. So the plan-versus-outcome question this source was chosen for survives — **in
time rather than in money** — and the money version becomes a figure about the register itself
rather than about procurement.

## Fourth pass: the columns the recipe never opened

The file carries **242 columns**. The eight figures use 29. A coverage sweep of the rest, on a
60,000-transaction sample, found **213 above 25% populated** -- the sub-award and
executive-compensation blocks are the sparse remainder. Three of the untouched ones speak
directly to questions figures 5 and 9 left open, so they were measured before being written up.

**Q18. The variation lives at the vehicle, and the recipe has been measuring proxies for it.**
`parent_award_id_piid` is the actual parent contract, populated on **67.9%** of competed
awards: **35,346 distinct vehicles**, of which 688 carry fifty or more awards. Their single-bid
rates run **p10 0%, median 47%, p90 99%** -- and **132 of the 688 never draw a single bid while
63 always do**. Figure 5 used `solicitation_procedures` as a stand-in for "is this an order
against a vehicle"; that proxy accounts for 18% of the between-family spread and this does not
look like a 18%-of-variance quantity. *The claim to test:* competitive behaviour is a property
of the specific vehicle -- a management artefact -- rather than of the department, the product
family, or the market. *Falsified if* vehicle-level rates collapse toward the family mean once
each vehicle's product mix and size are held fixed, or if the 0% and 100% tails are small-n
artefacts. Check the n distribution before believing either tail.

**Q19. Public advertisement barely moves the bid count, which is not what the statute assumes.**
`fed_biz_opps` (90.4% populated) records whether the opportunity was posted publicly. Among
competed awards: posted **39.8%** single-bid, not posted **44.0%**, "not applicable" 47.1%.
Roughly **four points** separates advertised from unadvertised. The whole architecture of public
notice exists to produce bidders; this says it produces about four points of them. *Before
believing it:* posting is required above a threshold, so the two groups differ in size and kind
-- this must be re-run within size band and product family before it is a finding rather than a
composition effect. The blank group at 64.4% is a third population and needs identifying first.

**Q20. Commercial items draw fewer bidders, not more.** `commercial_item_acquisition_procedures`
(98.5%) is the closest thing the register has to the commodity-versus-bespoke axis that figure 9
named as its missing variable. It runs the wrong way: commercial items **46.4%** single-bid,
commercial procedures not used **38.0%**. Eight points, reversed. *So the catalogue-price
hypothesis for figure 9's unexplained spread is not supported by the one column that encodes
it*, and that residual stays unexplained rather than being quietly attributed.

**Q21. Two more thresholds to test alongside the $150,000 one.** `subcontracting_plan` (49.3%)
is required above a dollar threshold, and `cost_or_pricing_data` (33.9%) above the
truth-in-negotiations threshold. Both give the same natural experiment as figure 9's simplified
acquisition line: if bunching below a threshold is caused by the rule, it moves when the rule
moves and appears at each rule's own value. Three thresholds agreeing is an argument; one is a
round number.

**Q22. Does the register know the same firm across the DUNS-to-UEI transition?**
`recipient_duns` (87.1%) and `recipient_uei` (100%) overlap in this file. UEI is already known
to be an establishment identifier here -- 1,299 names carry two or more. Whether DUNS partitions
the same way, and whether the crosswalk is one-to-one, decides if any multi-year identity claim
in this recipe survives the 2022 changeover.

**Q23. `other_than_full_and_open_competition` names the statutory exception actually cited.**
25.7% populated -- which should be close to the share of awards that are not fully competed.
Each value is a specific legal authority. A cross-tab of the cited authority against the bid
count tests whether the exceptions are used as written, and the rulemaking publishes the
criteria, so the categories can be read against their own source rather than guessed at.

**Q24. `multi_year_contract` (43.6%) is the other half of figures 15 and 16.** Option time was
measured by differencing two date columns because nothing reports it directly. This flag
records whether the contract is multi-year by statute. Whether it predicts the whole-year comb,
or is orthogonal to it, says whether that comb is a legal artefact or a habit.

**Q25. `place_of_manufacture` (98.5%) and `domestic_or_foreign_entity` (92.8%).** Where a thing
is made against who is registered to sell it. The geography figure showed the recipient's
address and the place of performance disagree on two awards in five; this is a third geography
and there is no reason to assume it agrees with either.

**Q26. `action_type` (45.8%) classifies what a modification does.** 46.1% of rows are
modifications and the recipe currently treats them as one undifferentiated mass. Separating a
funding action from a scope change from an administrative correction is the difference between
"contracts grow" and "contracts get re-scoped", which are different findings with the same
number attached.

**Q27. `recipient_parent_name_raw` against the cleaned name (98.9%).** The concentration figure
ranks on the cleaned parent name. The raw field is what the filer typed. Measuring how much
normalisation moves the top of that ranking says whether figure 3's concentration is a property
of the market or of the cleaning -- the rebrand trap, on a register with 81,330 entities.

**Q28. `evaluated_preference` (98.8%) and `local_area_set_aside` (98.6%).** Price preferences
and disaster-area reservations. Both near-complete, both untouched, and both sit directly on the
set-aside finding in figure 1, which showed reserved awards are *less* single-bid than open ones.

### What this pass changes about the recipe

The recipe has been explaining single bids with variables that explain very little of it:
department 23-34%, vehicle *procedure* 18%, supplier concentration ~2%, public posting ~4
points, commercial-item status ~8 points reversed. **Q18 is the first candidate that is the
right shape for the size of the effect**, and it is the one column that identifies the actual
contracting instrument rather than a category it belongs to. It should be measured next, and it
should be measured with the n distribution printed beside the tails.

## Fifth pass: what the threshold experiment opened

FY2025 arrived, and with it the natural experiment figure 12 rests on. Running it raised more
than it settled.

**Q29. The register halved its award count and doubled its money, and nobody asked why.**
FY2016: 554,171 awards, $125.8bn. FY2025: **327,763 awards, $231.8bn** -- from the same eleven
departments, on the same collapse rule. Awards down 41%, dollars up 84%, so the median award
has moved by something like a factor of three. *Every cross-year claim in this recipe sits on
top of that*, including the threshold result, and none of the eight figures built on FY2016
have been re-run on FY2025. Candidate explanations, each testable and none yet tested:
consolidation onto fewer vehicles (which Q18 says is where behaviour lives), the micro-purchase
threshold tripling from $3,500 to $10,000 and removing the smallest awards from the count,
inflation, or a change in what USAspending treats as a distinct award. **The last of those
would invalidate the comparison rather than explain it, so it is the one to rule out first.**

**Q30. Does the bunching sit with particular buyers, vehicles or product families?** Figure 12
is a distribution-level result and deliberately identifies no award. The next question is
whether the excess is spread thinly across the register or concentrated -- the same excess-mass
estimator, run within department, within product family, and within vehicle. A pattern that is
uniform is a population habit; one that is concentrated in a handful of vehicles is a
management finding, and Q18 makes that the likelier shape.

**Q31. The other thresholds, now that the method is validated.** The estimator survived a
placebo sweep, so it can be pointed at the rest of the FAR's dollar lines: the micro-purchase
threshold ($3,500 to FY2017, $10,000 after -- itself a moving target, so a second natural
experiment), the subcontracting-plan threshold, the truth-in-negotiations threshold, and the
commercial-item ceiling. Three thresholds agreeing would make this a property of how rules are
obeyed rather than a fact about one line.

**Q32. What happens just *above* a threshold?** The estimator only reads the two bins below.
If awards are being held under the line, the deficit above should mirror the excess below, and
the ratio of the two bounds how much of the bunching is displacement rather than genuine
smaller work. A missing deficit would mean the excess is new awards, not moved ones.

**Q33. $100,000 in FY2025 reads +9% and should be explained or dismissed.** Every other placebo
value sits within a few points of zero in every year. $100,000 is the only one that does not,
and only in the newest year. Either a rule sits near it that this recipe has not read, or it is
the noise floor -- and the honest way to tell is to check the FAR rather than to argue from the
number.

**Q34. FY2016's peak is not identified, and that is worth understanding rather than dropping.**
It reaches +18% at its own threshold and the same +18% at $310,000, where no rule exists.
FY2017, one year later under the identical rule, peaks cleanly at +29%. Whether FY2016 is
noisier, or something specific happened at $310,000 that year, decides whether the FY2016 line
belongs in the figure at all.

### The shape of the recipe after this pass

Ten figures, eight of them built on a single fiscal year that is now nine years old. **Q29 is
the load-bearing question**: until the FY2016-to-FY2025 gap is explained, every finding here is
a statement about FY2016 rather than about federal procurement, and the recipe should say so in
those words.

## Where each question landed

Twenty figures, in reading order. A question marked *settled in method* was answered by the
loader or the footers rather than by a plate, and one marked *stated, not drawn* was measured
and deliberately left off a plate.

| question | answered by |
| --- | --- |
| Q1-Q3 contract growth | **18** in aggregate (60.2% of money is post-award, change orders 2.58%); the per-award ratio is **not recoverable** from one file, which is filtered on action date |
| Q4 who wins repeatedly, and what they are paid | **19** -- a measured null at +/-5.3% |
| Q5 modifications | **18**; 46.1% of rows, and 41.3% of them are closeouts carrying 1.1% of the money |
| Q6 agency against contract type | **9** -- what is bought beats who buys it |
| Q7 what is invisible | footers throughout, and **20** |
| Q8 arbitrage | README, re-asked at completion |
| Q9-Q11 the award unit | settled in method: `load.py`, maximum running total, first non-blank |
| Q12 single offers | **5** |
| Q13 the schedule pair | **16**, **17** |
| Q14 concentration | **3** |
| Q15 set-aside documentation | **2**, and the control came back empty -- reported in the README |
| Q16 small business | **1** |
| Q17 place of performance | **4** |
| Q18 the vehicle | **8** -- the largest effect in the recipe |
| Q19 public notice | **10**, **11** -- doubles under control rather than vanishing |
| Q20 commercial items | **10**, **11** -- the pooled reversal was composition |
| Q21 / Q31 other FAR dollar lines | **14** -- two follow their rule, one runs backwards, one control flat |
| Q22 DUNS to UEI | **19** in part: parent UEI reproduces the cleaned ranking to two decimals |
| Q23 statutory authority cited | *stated, not drawn* -- near-deterministic on bids, and a fifth "two bases" plate |
| Q24 multi-year contracts | **open** |
| Q25 place of manufacture | **open** |
| Q26 action type | **18** |
| Q27 name normalisation | **19** -- 960 of the top 1,000 survive the raw filer-typed name |
| Q28 preferences and local set-asides | **open** |
| Q29 FY2016 against FY2025 | **20** -- a reporting change, and it forbids most cross-year comparison |
| Q30 is the bunching concentrated | **13** -- broad, and the vehicle cut cannot be scored |
| Q32 displacement above the line | **13** -- the deficit is absent |
| Q33 $100,000 in FY2025 | **open** -- the only placebo that misbehaves, in one year |
| Q34 FY2016's unidentified peak | stated on **12**; its raw step points the right way where its fitted peak does not |

**Three questions are open and none of them looks like a figure.** Q24, Q25 and Q28 are
one-line answers about columns nobody has cross-tabbed yet. Q33 is a single placebo reading in
a single year and wants a rulemaking search, not a plate.
