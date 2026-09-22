# The bid-count column is dying, and it is dying where the finding lives

Measured 2026-09-22 on four award-level folds. Cells are the share of awards of that
type whose `number_of_offers_received` is **blank**.

| file | awards | overall | delivery order | purchase order | definitive contract | BPA call |
|---|---|---|---|---|---|---|
| civilian FY2016 | 554,171 | 0.3% | 0.3% | 0.0% | 0.0% | 1.3% |
| civilian FY2017 | 606,348 | 1.3% | 2.5% | 0.0% | 0.0% | 1.5% |
| Commerce FY2024 | 11,414 | 22.6% | 29.7% | 0.0% | 0.0% | 49.6% |
| DoD FY2024Q2 | 1,065,017 | 83.1% | **94.6%** | 0.0% | 0.0% | 26.1% |

## Two effects, not one

The Defense file is FY2024 and the civilian file is FY2016, so the first reading —
"Defense does not report bid counts" — is confounded with the calendar. The Commerce
FY2024 probe separates them, and **both effects are real**:

- **Era.** Civilian delivery orders go 0.3% blank (FY2016) to 29.7% (FY2024). The column
  decayed inside the civilian half of the register too.
- **Agency.** In the *same* fiscal year, Defense delivery orders are 94.6% blank against
  Commerce's 29.7%. Defense is worse than civilian by a further wide margin.

## Why this is not a nuisance

The blankness is **not random, and not orthogonal to the question**. It lands almost
exactly on the population figure 5 is about:

- `DELIVERY ORDER` — the orders-against-a-vehicle that carry the whole inheritance
  finding — 94.6% blank in Defense.
- `PURCHASE ORDER` and `DEFINITIVE CONTRACT` — standalone awards, the *complement* of the
  finding — **0.0% blank in all four files, both eras, both halves of the register.**
- By label, `FULL AND OPEN COMPETITION` is 96.1% blank in Defense.

So a Defense single-bid rate is computable only on the 16.9% of awards that are standalone
contracts, which is precisely the population where vehicle inheritance cannot occur. The
resulting 38.9% is not a weaker version of the civilian 59.5%; it is a different quantity.
Reporting it as a control would be the classic error of reading a survivors' sample.

## What this licenses and forbids

- **Licensed:** the figure 5 measurement on civilian FY2016, where coverage is 99.7%.
- **Forbidden:** any Defense comparison on this column; any trend in single-bid rates
  across years, because the denominator's composition moves with the coverage.
- **Forbidden:** treating the FY2024 files as a refresh of this figure. They cannot answer
  it. The question was answerable in FY2016 and is not answerable now.

## The general shape

A field can be near-perfectly populated, stay in the schema, keep its name and its
enumeration, and quietly stop being filled in for one award type. Nothing errors. The
column still returns 200 and a value, and the value is `''`. Checking overall coverage
(83.1% blank) would have flagged it; checking coverage *crossed with the award type the
finding is about* is what makes the Defense number unusable rather than merely thin.

Related: [silence is not data], [check the instrument changed],
[capture is the only irreversible step] -- the FY2016 answer is not reconstructable from a
2026 fetch, which is the argument for the capture existing at all.
