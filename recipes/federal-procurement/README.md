# Which number did you mean?

Federal civilian contracting, FY2016, at the award level. 554,171 awards, $125.75bn net.

## The background

Every contract action a US federal agency takes gets filed by its contracting officer into a
reporting system, and USAspending republishes that filing. The duty is the point: nobody
volunteers this. It exists because a transparency statute obliged agencies to report awards,
and the columns in it are the columns someone was *required* to fill in — which is why they
are uneven, why some are near-perfect and others are decorative, and why the shape of what is
missing is itself evidence. (The specific statutory citation is not verified in this recipe;
what is verified is the filing behaviour visible in the data.)

This register is the source for essentially every public sentence about how the US government
buys things. "Small business gets half of federal contracts." "X% of contracts are competed."
"$N billion flowed to this state." All of it comes from here.

## Why it matters

**For five of the six questions below, this register offers two defensible ways to count the
same thing, and they give materially different answers.** Not rounding-different. Different by
a factor of two, or opposite in sign.

Almost nobody quoting one of those numbers tells you which base they used, and the honest
reason is usually that they did not know there was a choice. The register does not warn you.
Both counts run without error and both produce a clean percentage.

That is the story this figure set tells. It is not six findings about procurement. It is one
finding about the instrument, shown six times on different questions, plus one question the
instrument cannot answer at all.

## Who it matters to

- **Anyone about to publish a procurement statistic** — reporters, advocacy groups,
  congressional staff. Figures 1, 2 and 3 will change a number you were about to print.
- **Oversight picking targets** — GAO, inspectors general. Figure 5 says the competition
  label you would screen on is inherited rather than earned, so a ranking built on it ranks
  paperwork.
- **Firms deciding whether to chase federal work** — figure 1 says the ceiling for a small
  business is real and locatable, and figure 5 says where the actual gate is.
- **The register's stewards** — the coverage note says one of these columns has stopped being
  filled in, and the figures here are a record of what it could answer while it still worked.

## The figures, in order

Twenty plates in four acts. Every one declares FOR / DECIDE / WRONG IF on its face, and
`verify.py` recomputes the numbers behind them from the source.

### I. The base you pick changes the answer (1-4)

**1. Small business takes half the awards and a quarter of the dollars** -- 52.4% against
26.1%. The gap is not that small firms do small work: the median small-business award is
*larger*, $8,555 against $7,314. There is simply no tail. **0 of the 35 awards above $316m**,
and those 35 hold 23.7% of all the money.

**2. Where that gap lands.** Below the line in **11 of 11** departments, and leaving any one
out moves the headline only between 24.6% and 32.2%. **10 of 11** reserved programmes have a
median award *above* the register's own $7,978 while taking less than a proportionate share of
dollars.

**3. Ranked by dollars and by awards, the register names different firms.** Half the dollars
go to 74 recipients and half the awards to 994. At rank 100 the same data says **25% or 54%**.

**4. Two geographies that disagree on two awards in five.** 40.8% are performed outside the
recipient's state. The capital region is 19.4% of awards by address and 20.3% by performance
-- but 31.7% and 29.3% of the dollars. And what a state's competition rate says about it is
*durable*: r **+0.72** from FY2015 to FY2017, still **+0.67** with agency mix removed.

### II. Competition is not what the label says (5-11)

**5. A third of awards are labelled competed and drew exactly one bid** -- 180,868, which is
**45% of everything labelled competed**. When the label says NOT competed it is near-certain
(99.8% single-bid). When it says competed it is close to a coin toss.

**6. It is nobody's habit.** The gap is positive in 11 of 11 departments and runs **17.9 to
43.3 points**, so the label is neither a usable rate nor a correctable one. And restricting who
may bid *raises* the count in 11 of 11 -- the size confound runs against that finding.

**7. What predicts a single bid is the procedure run.** Orders against an already-competed
vehicle draw one bid 59.9% of the time; a sealed bid draws one 6.5% of the time. **74.7%** of
awards carrying the strongest label are vehicle orders -- the label is inherited, not earned.

**8. And the variation lives at the individual vehicle.** 688 vehicles with 50+ competed
awards run **p10 0%, median 47%, p90 99%**. Raise the floor tenfold and the tails survive: six
vehicles ordered against 500+ times each have **never once** drawn a second bidder. Their
product mix explains about 14% of it.

**9. What is bought predicts competition better than who buys it** -- 14.6% (construction) to
64.8% (medical and lab equipment). The department explains 34%, the vehicle procedure 18%.

**10. Two candidate explanations, both misread at the pooled level.** Public notice reads -4.3
points pooled and **-7.4** with product family held fixed. The commercial-item flag reads +8.4
pooled and **+0.7** controlled, against a detectable effect of 0.59 -- that eight points was
composition.

**11. And the commercial-item zero is a cancellation, not a null.** Per family it runs -21.8 to
+16.8, with **23 of 26 families** distinguishable from zero in both directions and a *larger*
median gap than the notice column. A pooled mark cannot tell a small effect from two large ones
that cancel.

### III. The rules bite, and it can be proved (12-14)

**12. Award values bunch below the competition threshold, and the bunching moved when the
threshold did.** The simplified acquisition line was $150,000 through FY2017 and $250,000 from
FY2018. FY2017 peaks at $150,000 (+29.1%); FY2025 peaks at $250,000 (+37.4%) while $150,000
falls to +4.8%. Visible raw, before any model: the step below each year's own line is **1.36x**
and **1.34x**.

**13. It is broad, not concentrated -- and the displacement is not there.** 14 of 27 subgroups
exceed the null band, so it is a population habit with a gradient rather than a few bad actors.
Only HHS and medical equipment replicate across both years, at 2-3x the register rate. And
there is **no deficit above the line**: the ratio is -0.25 in both years, so at most a fifth of
the excess is displacement.

**14. Four FAR dollar lines, and two more of them follow.** Cost or pricing data moves +7.0 and
+9.7 at $750,000, then **+14.2 at $2,000,000**. The subcontracting-plan control, whose value
moved 7% against the others' 167-186%, stays within six points of zero. **The micro-purchase
line runs backwards** -- a deficit, because below it a purchase goes on a card and is never
filed. A rule can shape a distribution by changing behaviour or by changing what is written
down, and only the first is worth screening for.

### IV. What the register cannot tell you (15-20)

**15. The contract's own ceiling is recorded for about a third of awards**, and coverage is not
flat across agencies -- so the awards with a value on file are a sample, not a census.

**16. A quantity nobody reports.** 16.7% of awards can be extended past their current end date,
and that authority is issued in whole years: 365, 730, 1,096, 1,461 days, a clean comb. Only
visible by differencing two date columns.

**17. Who holds it, and a measured null.** How often a group holds option time and how much it
holds are different rankings. Competition does not explain it -- competed awards lead in 8 of
11 departments by a median 1.1 points against intervals half a point wide, so a three-point
effect could not have hidden.

**18. 60.2% of the money arrives on a modification** -- but 87.7% of that is funding actions
and option exercises against work already agreed. Change orders and additional work are
**2.58%**. Meanwhile 41.3% of modification *transactions* are closeouts carrying 1.1% of the
money, so a modification-count screen measures administration.

**19. Winning ten thousand times pays the same per award as winning once.** 50.4% of firms won
exactly once. The median award moves x1.023 per tenfold rise in awards won, against a
detectable effect of +/-5.3%. What *does* move is the instrument: vehicle share runs 12.1% to
66.1%, and survives standardising on value and product family.

**20. And the register changed underneath all of it.** FY2025 has 41% fewer awards and 84% more
dollars than FY2016. **78% of the loss is awards under $10,000**, because the micro-purchase
threshold tripled. Every band above $316k grew. Any figure here that counts awards or takes a
median cannot cross FY2018 without cutting both years at $10,000 first.

## The sting: the column is dying

The bid count that figure 5 rests on was 99.7% populated in FY2016 civilian data. In FY2024
Defense data it is **83.1% blank**, and the blankness sits exactly on the award type the
finding is about — 94.6% blank on delivery orders, 0.0% on standalone contracts. A Commerce
FY2024 probe separates era from agency and both effects are real: civilian delivery orders went
0.3% blank to 29.7% over the same period.

**So figure 5 was answerable in FY2016 and is not answerable on a fresh fetch today.** Full
working in [`offers-coverage-decay.md`](artifacts/research-questions/offers-coverage-decay.md).

## Arbitrage: mostly exit 1, one seat-shaped edge, and a thesis this recipe kills

Per [`arbitrage-policy`](../../../webprobes/doctrine/arbitrage-policy.md), re-asked now that
the figure set is complete rather than inherited from the draft.

**Exit 1, no instrument -- figures 1, 2, 3, 4, 9, 11, 15, 16, 17, 18, 20.** The base-choice
findings, the product-family spread, the option-time comb, the modification decomposition and
the comparability warning change what a journalist or an oversight body should print. Nothing
trades on them. Stated and dropped, which is the honest default.

**Exit 4, survives disclosure -- figures 7 and 8, and this is the real one.** Figure 8 is the
sharpest finding in the recipe: whether anyone competes is a property of the *specific vehicle*,
not of the agency, the market or the product, and six vehicles ordered against 500+ times each
have never drawn a second bidder. For a firm the binding question is therefore **whether you
hold a seat**, not whether you can write a better proposal. Publishing that transfers nothing:
vehicles are recompeted on multi-year cycles, so the constraint is a position and elapsed time.
The qualifier is that vehicle intelligence is a product several vendors already sell, which
makes much of it **exit 2, already priced** -- the test is not "could this be traded" but "what
does the incumbent product already contain", and for named vehicles it contains this.

**A thesis this recipe removes, which is worth more than one it creates.** Figure 19 measures
what a repeat winner is paid and finds **nothing**: the median award moves x1.023 per tenfold
rise in awards won, against a detectable effect of +/-5.3%. The intuitive short thesis --
entrenched incumbents extracting a premium -- is not in this data at the award level. A null
that kills a story is a result, and it is the kind most likely to be quietly dropped.

**The one that looks tradable and is not.** Unexercised option time (figure 16) is forward
revenue visibility and is not in a 10-K at per-contract granularity. But the firms with tickers
are overwhelmingly Defense primes, and **Defense is precisely where the bid and schedule
columns have gone blank** -- 83.1% blank overall, 94.6% on the delivery orders that carry the
whole phenomenon. The edge and the coverage collapse are the same fact seen twice.

**Figures 12, 13 and 14 are exit 1 with a caveat about who reads them.** A distribution that
tracks a rule is oversight evidence, not a signal: it identifies no award, the displacement is
absent, and the excess is broad rather than concentrated. It is a reason to audit a category,
not to take a position.

**Saturation clock.** Vendor packaging has already happened for the part worth packaging.
Reflexivity is weak: contracting officers do not read this and change, though a *regulator*
might -- figure 14 shows three thresholds moving and the distribution following, which is the
clearest reflexivity risk here and is a reason the threshold findings are published as
distribution-level rather than as a screen. The summary stands: **this recipe is for people who
publish numbers and people who oversee spending, not for people who trade.**

## Three layers, and why the middle one exists

**Source.** A civilian fiscal year is a ~300 MB zip that USAspending *generates on request*.
The generation is the cost, not the transfer: FY2025 took over 50 minutes of server-side work
before a byte moved. These are not kept in the repo and not committed.

**Condensed.** `condense.py` folds each year once into `condensed-fy<Y>.json` — **22 KB, about
12,000x smaller than its source**. It holds counters, cross-tabs and sampled cumulative curves,
never records. This is the layer worth keeping, and it is what makes the recipe portable: a
reader with no zip and no hour to spare can still rebuild the figures and check the claims.

**Figures.** Built from the condensed layer.

### The rule that licenses deleting the source

`verify.py` is authoritative — it re-folds the 300 MB zip and settles disagreements.
`verify-cached.py` asks the *same* questions of the 22 KB file and runs in **0.026 seconds**
against roughly four minutes. Both currently pass on all claims.

That equivalence is not a convenience, it is a test. **If a claim cannot be re-derived from the
condensed file, the condensed layer is not a summary of the source but a lossy selection of it**
— and the figure making that claim silently depends on data nobody keeps. So a new figure is
only finished when `verify-cached.py` can check it.

### What a cache must say about itself

Every condensed file carries a provenance block: the source filename, its byte count and
**SHA-256**, the fiscal year, the date it was condensed, and the two rules that are easy to get
wrong — how an award's value is taken from its transactions, and what counts as a bid. An
atomic write prevents a half-written file; it does nothing about a stale one. The hash is how
you tell a cache that matches its source from one that merely claims to.

*Still to migrate:* figures 1–5 re-fold the zip at build time; 6, 7 and 8 already read caches
only. Nothing is wrong with their numbers — they are just slower than they need to be, and they
keep the source mandatory when it should be optional.

## What ships, and what you have to refetch

The zips are ~1.3 GB and USAspending generates each one on request -- FY2025 took over fifty
minutes of server-side work before a byte moved. They are not committed. What is committed is
**2.4 MB of receipts**: counters, cross-tabs and sampled curves, never records.

**`verify-cached.py` passes from the receipts alone**, with no zip present, in 0.026 seconds
against roughly four minutes for the authoritative `verify.py`. That equivalence is the test
that licenses shipping without the source; see
[`condensed-receipts`](../../../webprobes/doctrine/condensed-receipts.md).

**13 of the 20 figures redraw from what is committed.** Seven do not, and they are named
rather than left to be discovered:

| figure | why |
| --- | --- |
| 1, 2, 3, 4, 15 | they fold the zip on every build and have no cache module, unlike the later figures. The fix is the `cats.py` pattern, one module each. |
| 13 | its receipt is 7.0 MB -- a window of raw values rather than a summary, and it wants shrinking before it ships |
| 19 | its receipt is 28 MB, which is a corpus and not a receipt |

Running `python3 artifacts/scripts/usa2.py 2016` (and `2015 2017 2025` for the cross-year
figures) refetches what those seven need. Everything else, including every number
`verify-cached.py` checks, is here.

**One receipt is argued for rather than let through.** `notice-fy2016.json` is 2.0 MB, above
the 512 KB bar the rest clear, and it is the only evidence for two figures. It ships because
the alternative is two plates nobody can check.

## Reproducing

`artifacts/scripts/` — `usa.py` (session, held-open connection), `usa2.py` (civilian fetch;
takes years on the command line, newest first when that is what the question needs), `grab.py`
(resuming chunked download), `load.py` (shared loader: collapses transactions to awards on
`contract_award_unique_key`, takes the running-total **maximum**, not the last), `agg.py`
(streaming per-year summaries), `sched.py` (the award-level fold the two schedule figures
share), and `chart-*.py`, one per figure.

**One chart per plate, two at most** — see
[`one-chart-per-plate`](../../../webprobes/doctrine/one-chart-per-plate.md). Figures 15 and 16
were one plate with four panels, and so were figures 1 and 2. Both were split by subject, which
is why `sched.py` and `sbiz.py` exist: two figures sharing an expensive fold is an argument for
sharing code, never a canvas. In both cases the block that made the plate crowded was **prose**
— a failed control written out as a column — and prose belongs here.

Two traps the loader exists to avoid: 13.17% of transactions are negative (de-obligations), so
keeping only positives overstates the net by 4.8%; and 46.1% of rows are modifications, so
transaction counts are not award counts.

The host charges a **~135 second connection toll** and about 0.3s per request after that. Hold
the connection open. See [`find-what-the-toll-is-charged-on`](../../../webprobes/doctrine/).
