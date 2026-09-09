# Questions this recipe asks

Status is honest, not aspirational. **Answered** means a figure in this recipe
supports it. **Partial** means the data constrains it but does not settle it.
**Open** means asked and not answered — the reason is stated, so a return visit
knows what changed rather than starting over.

Last reviewed 2026-09-09 · method 2.1.0

---

## Answered

**What happens to a typical dataset?**
Median 8 downloads; 69.5% never opened in a notebook; 0.4% pass ten thousand
downloads. Population of 737,729. → `what-happens-to-a-dataset.svg`

**Who publishes, and does it matter?**
267,376 distinct owners, top 1% account for 21% of datasets. Organisations
median 158 downloads against individuals at 8 — twentyfold.
→ `which-categories-get-used.svg`

**Are there categorical differences?**
Sixtyfold spread across the 65 tags with 2,000+ datasets. `classification` 244
median downloads; `research` 9; `pre-trained model` 4 across 43,589 datasets.
→ `which-categories-get-used.svg`

**Does size predict use?**
Yes, monotonically, and it survives holding age constant within the 2023
cohort. A sample drawn from the platform's popularity orderings reports the
opposite. → `size-predicts-use.svg`

**Is publication a maintained commitment?**
No. 86% of datasets are never revised after first upload.

**Is the organisation advantage causal?** *(answered 2026-09-09)*
Mostly not. The raw gap is 20×, but organisations published in 2018 (median)
and individuals in 2024. Matched on year and size band over 18 strata, it falls
to **2.8×**. A residual advantage remains and is not explained here.

**What explains the 2019 dip?** *(answered 2026-09-09)*
Kaggle auto-created a notebook per dataset until some point in 2020. Among
datasets with one download or fewer, 100% of 2017 and 89% of 2019 still carry a
notebook, against 8% of 2021. The dip was that feature at peak — 48.8% of 2019
datasets sit at exactly one notebook. **Consequence: `TotalKernels` is not
comparable across years before 2021**, and the cohort figure now starts there.

**How big is the graveyard, and who fills it?** *(answered 2026-09-09)*
412,935 datasets — 56% of all — have ten downloads or fewer, and the absolute
number grows faster than the catalogue. Not spam: 96.8% earn no medal, and
161,320 one-time publishers have a median of twelve downloads. The value to the
publisher is realised at publication, not at use.
→ `the-graveyard-is-growing.svg`

---

## Partial

**How has demand evolved over time?**
The share of each year's datasets never opened in a notebook rose from 32%
(2017) to 81% (2026) while annual publication grew fiftyfold. **But the curve
cannot be age-adjusted from a single snapshot** — Meta Kaggle publishes current
cumulative totals only, so newer cohorts are penalised by construction.

*What would settle it:* downloads at matched age, which needs Meta Kaggle
snapshots over time. `history.csv` in this recipe is the first row of that
series. Revisit after twelve monthly runs.

---

## Open

**What explains the residual 2.8× organisation advantage?**
Matching removed year and size. Promotion, audience and category choice remain.
*Would need:* matching on category as well, or a natural experiment where
individuals gained an organisation badge.

**When exactly did Kaggle stop auto-creating notebooks?**
Somewhere in 2020 — the ≤1-download signal runs 89% (2019), 67% (2020), 8%
(2021). A monthly rather than yearly cut would date it, and would say whether
2020 is usable with a partial-year restriction.

**Why does `fsboard` have 589,221 downloads and zero notebooks?**
The cleanest demonstration in the data that downloads and use differ. Likely a
competition dataset used offline. Not investigated.

**Does this shape hold on other platforms?**
Untested, and the recipe's own conclusion — that demand is a property of
audience — argues it may not. Hugging Face, Zenodo and figshare would each need
their own population index.

**Does the same graveyard shape appear in our own archives?**
Asked because the answer probably matters more than the Kaggle finding. 86 wss
sources, nothing published, no named consumer for any of them. The pattern that
predicts death — produced for the producer's benefit, specialist category, no
identified asker — currently describes the fleet. *Would need:* naming an asker
per source, which is now screen 9 in `deciding-what-to-build.md`.

**Have publishing methods gone out of date?**
Asked, not started. `DatasetVersions.csv` carries `LicenseName` and version
notes, which would support a licence-drift and format-drift analysis. Nothing
computed yet.

---

## Retired

**Does file size predict death?** — asked under method 1.x and answered *no*
from a 4,233-dataset sample. **That answer was wrong**; the sample reached only
already-successful datasets. Superseded by the population answer above. Kept
here because the failure mode is the transferable part.
