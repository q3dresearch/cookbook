# A plate that was wrong twice, kept because it was persuasive

`3-validity-deprecated-field.svg` shipped on 2026-09-24 and said:

> **BIDS errors fell from 62% of datasets to nearly none, and then the checking stopped.**

Both halves are false, for two independent reasons, and neither is visible from inside the
figure. It is kept rather than deleted because it was clean, it passed the plate audit, it
rebuilt byte-identically, and a reader found its *annotations* wanting long before anyone
doubted its data.

## Wrong the first time: the field was deprecated

It was built on `latestSnapshot.issuesStatus`, which is populated on **1,072 of 1,891 (57%)**
— and the plate read that 57% as *validation coverage*, concluding that the archive stopped
checking recent deposits and had an 819-dataset backlog.

`issuesStatus` is superseded by `latestSnapshot.validation`, which is populated on **1,893 of
1,893 — 100%, every single year.** **Not one dataset has both empty.** The backlog never
existed. Where both fields exist they disagree on whether errors are present for **450 of
1,072** datasets, and in **431** of those the live field finds errors the deprecated one did
not. They are not the same measurement: ds000001 reports 3,950 warnings under `validation`
and 4 under `issuesStatus`.

**A deprecated GraphQL field does not error. It returns a well-formed null, forever** — and an
absence in a register has exactly the shape of a real finding. One introspection request would
have caught it, and the recipe was declared complete without ever making one.

## Wrong the second time: the instrument changed

Rebuilding on the live field still shows a fall, from ~41% of 2024 deposits carrying an error
to 3% in 2026. That is also an artifact. The BIDS validator changed major version, and the two
versions disagree by an order of magnitude **on the same datasets in the same year**:

| year | v1 error rate | v2 error rate |
| --- | --- | --- |
| 2023 | 56% (n=70) | 14% (n=36) |
| 2024 | 54% (n=158) | 18% (n=90) |
| 2025 | 70% (n=20) | 1% (n=277) |

Pooled: **v1 55%, v2 5%, v3 1%.** v2's share of runs went 38% (2024) to 94% (2025) to 99%
(2026), which is the whole of the apparent improvement.

**The control that settles it:** holding the validator fixed at v1, the error rate from 2024
to 2025 went **54% to 70%** — up, not down. And v2 is not merely quieter: it reports *more*
warnings than v1 (median 3,587 against 2,851), so it reclassifies errors rather than missing
them.

## What replaced it

`charts/3-validator.svg` draws the error rate per year **split by validator version**, with
the pooled line falling between two flat components. The finding is no longer about
neuroimaging practice; it is that this archive cannot support a compliance trend at all,
because the instrument moved underneath it.
