# The register publishes its survivors and drops its dead. That is measurable anyway.

**Status: proven** · method 1.0.0 · computed 2026-09-17 from three Companies House bulk
snapshots a year apart, checked against ONS business demography and against the Colorado and
Norwegian registers. No data is committed — 1.5 GB, retrieved by
[`artifacts/scripts/fetch.py`](artifacts/scripts/fetch.py).

**Two-thirds of UK companies are gone within five years.** Whether that is alarming depends
entirely on what you thought a company was, and the recipe's first result is that the register
cannot tell you directly.

## The premise was wrong, and the correction is the method

This was built on an explicit argument: *these are legal records with dates attached, so the
history is in the data*. **It is not.** In the first 73,146 rows of the bulk file:

| | |
| --- | --- |
| rows carrying a `DissolutionDate` | **0** |
| statuses present | Active · Proposal to Strike off · Liquidation · In Administration · Receiver · Voluntary Arrangement |

Every one of those is a status a company holds **while still on the register**. The
dissolution column exists and is never populated. The register publishes its survivors and
drops its dead — the same shape as the drug registers elsewhere in this repo, arrived at from
the opposite direction.

**What rescued it is that the publisher keeps a back-catalogue nobody links to.** The monthly
file lives at a dated URL and old months keep resolving. Three snapshots a year apart give a
death definition the register does not provide: **a company is dead when it stops appearing.**

## The decision it changes

**If you are comparing a company against a survival benchmark, check which death the benchmark
counts.** The register and the ONS series disagree on level in 11 of 14 sectors and agree on
ordering at rho = +0.79. They are measuring different populations with different definitions
of death over different periods. Ordering is the thing that should agree; level is not.

*Who acts on this:* anyone publishing a business-survival statistic; a lender or insurer
scoring company age; a development agency comparing regions; a due-diligence team reading a
registered address.

## Seven figures, each with its decision on its face

- **[Two-thirds of UK companies are gone within five years](artifacts/charts/1-survival.svg)**
- **[The register agrees with the official series about the order, not the level](artifacts/charts/2-official.svg)** —
  the external check, run before anything was built on the numbers.
- **[Manufacturing halved. Retail doubled. Nobody stopped starting companies.](artifacts/charts/3-entry.svg)**
- **[Scotland's companies trade. London's and Harrogate's hold things.](artifacts/charts/4-place.svg)**
- **[Dudley buries a tenth more of its companies than anything about them explains](artifacts/charts/5-excess.svg)** —
  excess mortality after industry, age and size are held constant.
- **[Survive a strike-off proposal and you are back to an ordinary company's risk](artifacts/charts/6-warning.svg)** —
  the registrar warns about one death in five, and the warning stops meaning anything the
  moment it is withdrawn.
- **[Forty addresses hold a twelfth of Britain's companies, and they have gone bad](artifacts/charts/7-agents.svg)** —
  449,461 companies at forty addresses. Two-year survival there is 37% against 56% elsewhere,
  and **8.9 points of that gap survive standardising for age**, so it is not just that those
  companies are newer. In 2012 the two groups were indistinguishable.

## What this cannot say

**Not a lifespan.** Disappearing between two annual snapshots is the only death this register
admits, so everything here is an interval-censored survival measured at one-year resolution. A
company that incorporated and dissolved between snapshots was never observed at all.

**Not a cause, anywhere.** The agent-address finding is the sharpest case: the register carries
the address and the outcome and **nothing about the relationship**. A high-churn address may be
a cheap service used by people trying things, or something else. The figure says so on its face.

**Three points, and the third is the newest.** Any trend here rests on 2024, 2025 and 2026
snapshots. Cohort recency is a confound that could not be removed for the entry-mix figure, and
that figure says so rather than adjusting it away.

**The controls are controls, not comparisons.** Colorado records six kinds of death and still
cannot measure lifespan, because nothing compels a dead company to say so. Norway is the
closest matched register and its own definitions differ. Both are in the recipe to bound the
UK claim, not to extend it.

## Reproducing

    cd recipes/uk-company-survival
    python3 artifacts/scripts/fetch.py            # 1.5 GB across four sources, resumable
    python3 artifacts/scripts/extract.py          # compact each snapshot to what is used
    python3 artifacts/scripts/survive.py          # the survival curves
    python3 artifacts/scripts/compare_ons.py      # the external check
    python3 artifacts/scripts/extract_geo.py      # addresses, for the place and agent figures
    python3 artifacts/scripts/location.py
    for f in artifacts/scripts/chart-*.py; do python3 "$f"; done

`fetch.py --verify` hashes what is present against `provenance.json`; `fetch.py ch ons` takes
named sources only. `FSB_DATA` points the scripts at an existing corpus. Standard library
only — verified by AST walk, with the ONS workbook read by a sixty-line xlsx reader that was
checked cell for cell against openpyxl.
