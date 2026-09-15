# Questions this recipe asks

Status is honest, not aspirational. Every number here is re-derived by
`../scripts/verify.py`; the signals that failed are re-derived by `../scripts/sweep.py`
so a "failed" stays a measurement rather than a memory.

The rule for sorting: *a recipe is finished when no open question would change the
decision it drives.*

## Answered, and carried by a figure

| # | question | answer | figure |
| --- | --- | --- | --- |
| 1 | **Is a listing on the FDA shortage list a shortage?** | Usually not. 137 of 196 substances are permanent discontinuances. One reporting firm predicts an exit at 95% (127 of 133), two or more at 16% (10 of 63). A threshold, not a gradient. | `1-what-to-do` |
| 2 | **Does the reader's situation change which problem they have?** | Yes, three ways. A drug carrying the paediatric flag is never an exit (0 of 12, 8.6 expected). An injectable is a real shortage 44% of the time, an oral solid 13%. An anaesthesia listing is 77% real, a cardiology one 29%. | `2-paediatric` |
| 3 | **How long does a shortage last?** | About a year. Only Australia can say: Kaplan-Meier over every shortage open in the last twelve months puts the median at 387 days and one in four past 1,209. The register's own resolved rows say 62 days, because they are the survivors of a purge. | `3-duration` |
| 4 | **Can any register show whether shortages are getting longer?** | No, and none ever will. All three delete resolved rows at about twelve months; FDA kept seven, France never recorded a start date. Only a capture archive can answer it, in about a year. | `4-memory` |
| 5 | **Are the same drugs short in three countries at once?** | Twenty-three are, joined on RxNorm ingredient sets: old, cheap, mostly injectable. Descriptive — no action turns on the count. Stated in the README, not drawn. | — |

## Answered against us, and recorded so nobody repeats the day

| # | question | what the archive says |
| --- | --- | --- |
| 6 | **Do dilute injectables stay short longer?** | Direction consistent, evidence gone. On the full register the gap is 7.6 against 4.1 years at p = 0.037; without four bulk-load dates, p = 0.079 on 35 substances. Kept as `negative/5-dilute` because it shipped as a finding on half the feed. |
| 7 | **Does supplier depth predict a shortage?** | No. Among the 131 top injectable generics chosen on product count, the share on the list runs 36%, 23%, 37%, 46% across 1-5, 6-10, 11-20 and 21+ marketed products. More products means more chances for one to file a notice, not more risk. Attrition (share of a molecule's approvals discontinued) separates nothing: 35% against 39%. |
| 8 | **Do enforcement records mark the firms behind shortages?** | Warning letters: 8 of 520 lettered firms are on the list against 0.5% of the rest, and 11 of the 13 letters came *after* the firm's first listing. Import alert 66-40: three firms. Recalls: 34% of shortage firms recalled something in 2026 against 0.5% of other inspected firms — and it is size. Within the most-inspected stratum it is 56% against 12%, and inspection count is a weak size proxy; a product count per firm would settle it and is not in the archive. Not drawn. |
| 9 | **Does TGA's severity class predict duration?** | No. KM medians 544, 128 and 387 days for Low, Medium and Critical — not monotonic, 16 events in the Critical group. Injectables do resolve faster than oral solids (182 against 394 days), stated in the figure footer, not drawn. |
| 10 | **Are Australia's pre-announced shortages already short elsewhere?** | No. TGA publishes 93 shortages a median 50 days before they begin; 1 of the 60 coded ones is a real US shortage now and 12 are on the French list — no more than current Australian shortages are. The US list does not lead the Australian one. |
| 11 | **Does the reason code, the availability field or the age of a row say anything?** | Reason codes cluster on chronic substances at median ages of 3.6 to 6.4 years whatever the reason. Availability: 4 of 59 real shortages have every package `Available`. Age separates exits from shortages almost perfectly — 1 of 137 exits is older than two years, 53 of 59 shortages are — but that is retention (notices are purged), not prediction. |
| 12 | **Are shortage firms worse operators?** | No. OAI rate 6% against 7% for every other inspected firm, on 39,988 inspections. The null is load-bearing: it closes "look at compliance" and leaves "look upstream". |
| 13 | **Is a drug short because it is cheap?** | Untestable here. CMS NADAC joins 18% of injectable NDCs because it prices retail pharmacy, not hospital contracts. |
| 14 | **Does the register rewrite its own past?** | No. 3 of 842 substantive changes across four capture intervals moved no `update_date`, all three cosmetic. A draft said 12, with 55 rewrites of `initial_posting_date`: every one was the diff comparing a package's shortage row against its discontinuance row. |

## Open, and what each is blocked on

| # | question | blocked on |
| --- | --- | --- |
| 15 | **Is the three-country overlap growing, and do shortages resolve together?** | ~12 months of capture. Nothing a buyer does today changes on the answer. |
| 16 | **Does the twelve-month horizon roll, or did a purge run once?** | A second capture a season later. A rolling window keeps the oldest resolved year pinned a year behind; a one-off purge lets the gap grow. Two rows of `history.csv` settle it. |
| 17 | **Would capturing rescue FDA's durations?** | A month of captures. 25 keys left the list in eight days and none was marked `Resolved` first; if rows leave silently, capture yields departures, a weaker inference than a stated resolution. The seven survivors are four drugs with a median duration of 1,402 days, so whatever kept them kept old shortages. |
| 18 | **Is ANSM's start date recoverable from its per-product pages?** | One request. Cheapest open question here; France would join Australia. |
| 19 | **What are the twin packages?** | One join. 26 packages carry both a shortage row and a discontinuance row, on 10 substances, all of them chronic multi-firm shortages — a firm leaving a molecule that stays short. Whether the shortage row disappears and the notice stays in later captures is answerable from the archive as it accrues. |
| 20 | **Does the manufacturing tier explain the shared shortages?** | `fda.decrs.registrations`, which has captured nothing. What exists: 30 registrant-to-distributor pairs in the free-text field, Jiangsu Hengrui behind five US distributors. Zero of the 13 three-country multi-firm substances share an establishment across their firms. |
| 21 | **Do revision bursts follow enforcement events?** | ~12 months. The archive holds recalls, inspections, import alerts and warning letters beside the register; every one is days old. |
| 22 | **Discovery latency — who lists first?** | Observation. FDA's `initial_posting_date` makes its own side reconstructable; ANSM and TGA do not expose when a row first appeared. ANSM entered the archive on 2026-09-10; nothing before that is recoverable by anyone. |
| 23 | **Canada, the UK, the EU?** | More width, same decisions. Each is a capture entry and a parser. |

## How this recipe was wrong, in order

1. **Two pretty tables and two single axes** shipped first; they are `negative/1-4`.
2. **A 2×2 of labelled boxes** replaced them and was still a table; redrawn as one dot per substance.
3. **The dots prescribed re-tendering for 96 substances**, 84 of which were companies leaving.
4. **The paediatric finding was first banded by specialty**, comparing a flag with a field.
5. **The combination-product key** collapsed `acetaminophen oxycodone` onto `acetaminophen`.
6. **Every FDA number was computed on page two of a two-page feed** — 619 of 1,619 rows — and the verifier passed because it re-derived from the same half. The sibling draft this recipe absorbed had documented the exact trap a day earlier.
7. **That sibling's own headline** — the register silently rewriting its dates — was a non-unique business key comparing twin rows to each other.
8. **Its duration prescription** — "use TGA, median 62 days" — was the median of survivors; corrected, 387.

Each is a line in `verify.py` or `sweep.py` now.
