# What this register can still be asked, and two things it already answered no to

Written after the five figures. Everything here was measured or scoped against the fetched
data, not guessed from the API docs.

## Two negative controls, run and recorded

**The archive is not a handful of labs.** `seniorAuthor` is present on 1,451 of 1,462 datasets
(99%) and holds **970 distinct people**. The top ten hold 105 datasets between them — **7%**.
This matters because it rules out the failure where a national-looking series turns out to be
one firm: no finding in this recipe can be a property of one prolific lab, because no lab is
prolific enough. Largest single senior author is 14 datasets.

**`studyDomain` cannot support a "which fields are underserved" figure, and that is a finding
about the field.** 867 of 1,462 are blank, and the 595 that are filled are free text with no
vocabulary behind them. The most common value occurs **16 times**, and the list mixes domains
("cognitive neuroscience", "memory", "language"), modalities ("eeg", "fmri", "mri"),
conditions ("parkinson's disease", "epilepsy") and anatomy ("brain"). There is no way to count
how much of the archive studies language, because the archive does not record it. `dxStatus`
is the only population field with a dropdown behind it, which is why figure 5 uses it and not
this.

## ANSWERED 2026-09-24, then CORRECTED — deletion exists but is rare; capture is still not urgent

This was the recipe's only irreversible question. It is now closed, with a control.

**79% of the accession space is absent** — 1,891 datasets across ds000001 to ds008851 — and
that looked like deletion. It is not.

**The fill rate never approaches 100% anywhere**, which a deletion-eroded sequence would not
do. The oldest block, ds000001-000500, is **18%** filled; the peak is **41%** around 2023; the
newest blocks are **10-12%**. And **ds000501-ds001000 is 500 consecutive numbers, none ever
public** — a block that was never issued, not five hundred deletions. OpenNeuro assigns an
accession when a dataset is *created*, and roughly four in five drafts never publish.

**The API cannot answer this and the fourth probe is what proved it.** `ds000004` (a real gap
between two datasets published the same day), `ds009999` (never issued) and `ds999999zz`
(not an accession at all) **all return HTTP 200 with the identical string `"Dataset X does not
exist."`** One error for everything, so no amount of probing separates withdrawn from
never-existed.

**The Wayback Machine settles it, and the control is the load-bearing part.** A missing
accession having no captures means nothing unless live pages are crawled — so six live
datasets were sampled across the download distribution:

| dataset | downloads | captures |
| --- | --- | --- |
| ds000102 | 21,433 | 40 |
| ds000158 | 174 | 30 |
| ds005134 | 60 | 5 |
| ds003661 | 25 | 4 |
| **ds004271** | **0** | **5** |
| **ds003691** | **0** | **6** |

**Six of six are archived, including two that have never been downloaded at all.** Four of four
gap accessions — ds000004, ds000010, ds000230, ds009999 — have **zero** captures. Obscurity
does not buy a gap here, so the gaps are not withdrawn pages.

*What would still overturn it:* a dataset published and deleted before any crawler reached it.
Wayback's first capture of ds005134 is within months of its publication, so that window is
short, but it is not zero.

### CORRECTION, same day — terminal states exist and I had not fetched them

The conclusion above was reached from fields I had requested. Introspecting the schema
afterwards turned up two I had not, and both bear on it:

- **`Snapshot.deprecated`** carries `reason`, `timestamp` and `user`. **Three snapshots are
  deprecated**, with real reasons: *"wrongly changed by Co-I"* (ds003816), a blank one
  (ds004770), and *"Duplicate files"* (ds006222).
- **`Dataset.holdDeletion`** is set on **seven** datasets — ds002620, ds004663, ds004712,
  ds007283, ds007402, ds007544, ds007932. A flag named *hold deletion* only exists because
  deletion is a real process being held off.

So **ten of 1,893 datasets (0.5%) carry a terminal or pending-terminal state.** That does not
overturn the accession-gap finding — the gaps are still drafts — but it does overturn the
sentence "there is no deletion mechanism", which I had inferred rather than measured. The
honest position: **OpenNeuro deletes rarely and records it when it does.** Capture remains
unurgent, and the reason is now the rate rather than the absence of a mechanism.

**The lesson is the same one that falsified plate 3 an hour later:** I concluded from the
fields I happened to request. One introspection call would have shown both.

## MEASURED AND ABANDONED 2026-09-24 — the citation join, and why the instrument failed

Every figure in this recipe uses **downloads** as the outcome, and every one of them carries
the caveat that a download is not a citation. The obvious validation is OpenAlex, which is
keyless (`Allow: /` on both hosts) and indexes OpenNeuro. **It does not work, and the reason
is worth more than the answer would have been.**

**The key overlap check passed and the join was still wrong.** 38 of 40 sampled DatasetDOIs
resolved — **95%** — and the hit rate was flat across download quintiles (88, 88, 100, 100,
100%), so it was not a famous-records-only join. But the citations came back at a **median of
0, max 1**, while a hand-typed guess at *a different version* of one of those same datasets
returned **32**. The DOI names a dataset **version**; citations accrue to whichever version
each citing paper used. OpenAlex's own count gave it away: **5,756 works for 1,891 datasets**.

**So the join was re-run the other way — pull the whole source, aggregate by accession.** 990
works, 554 distinct accessions, joined to 490 of 1,891 datasets (26%), **20 with any citation,
28 citations in total**.

**And then the numbers stopped agreeing with each other.**

| statement | value |
| --- | --- |
| the source record's own `works_count` | **5,756** |
| `locations.source.id:S7407052830` | 990 |
| `primary_location.source.id:S7407052830` | 954 |
| `repository:S7407052830` | 990 |
| `type:dataset` + source | 959 |
| **ds000030, confirmed in that source** | **32 citations** |

Every filter form agrees at roughly 990, so the query was not too narrow. But **ds000030 alone
carries more citations than the 28 counted across all 554 accessions, and it is not in the
990.** A known member of the source is absent from every queryable view of it.

**The conclusion is about the instrument, not about neuroimaging.** Nothing here says OpenNeuro
datasets are rarely cited. It says OpenAlex's coverage of this source is internally
inconsistent by a factor of nearly six, and a citation total drawn from it measures the index.
`artifacts/data/openalex.json` is kept as the receipt for that inconsistency and **must not be
used as a citation table**.

**The caveat therefore stands, unresolved, on all seven figures.** Downloads remain unvalidated
as a measure of use.

*What would actually work:* enumerating every version DOI per accession rather than trusting
the source listing, which needs a version index this API does not expose; or a citation service
that resolves in-text dataset mentions rather than DOI-to-DOI edges — DataCite Event Data and
scite are the candidates, neither screened. Either is a new source and belongs in the
catalogue before it belongs here.

## CLOSED 2026-09-25 — derivatives, and it is empty

`Dataset.derivatives` was the last unfetched field and the best remaining candidate for a
reuse signal stronger than a download: a derived dataset is somebody *building* on the data.

**It returns `[]` for all 1,899 datasets.** Not null, not an error — an empty list, every
time, including for the archive's most-downloaded (`ds000102`), its largest (`ds005752`) and
its most-cited (`ds000030`). The type exists and is documented: `DatasetDerivatives` with
`dataladUrl`, `local`, `name` and `s3Url`, which is a mirror record rather than a derived
output in any case.

**Two counting attempts disagreed before the raw dump settled it** — one said 30.4% had
content, the next said 0.0%, and both were my own logic, not the API. Printing twelve raw
responses ended it in one call. That is the third time in this recipe that reading the values
would have been faster than reasoning about them.

So: no plate, and the question is closed rather than open. A reuse signal stronger than a
download would have to come from outside OpenNeuro entirely, and the two routes tried —
OpenAlex and `Snapshot.related` — are both recorded above as failed.

## Four the data can answer, none of them run

**1. Which NIH institute buys the most reuse per dollar?** `costjoin.rows()` already carries
`ic` (the funding institute) and `award` for 89 datasets. Grouping by institute is one
`collections.defaultdict` away and is the most directly prescriptive thing in the recipe —
a programme officer can act on it the week they read it.

*Falsifier:* 89 datasets across ~20 institutes is 4-5 each. If no institute clears n = 8 the
answer is that the question cannot be asked at this sample size, and that gets written down
rather than dressed up with a ranking of medians on n = 3.

**2. Does attaching a paper DOI raise reuse, once modality and era are matched?**
`associatedPaperDOI` is already folded as `paper_doi`. The prescriptive version is about
*timing*: a depositor choosing between publishing data with the paper or before it.

*Falsifier:* the direction is confounded in a way figure 5 is not. A dataset gets a paper DOI
because somebody wrote a paper, and a dataset with a paper attached is a dataset somebody
cared enough about to finish. A null here would be informative; a positive would not
establish much.

**3. Can the 819 unvalidated datasets be validated locally?** Figure 3's whole finding is that
the recent half of the archive has no published validator verdict. The BIDS validator is open
source and the data is public, so the gap the archive will not fill can be filled from
outside, on a sample.

*Falsifier and the real obstacle:* this needs the data, not the metadata. Figure 3 runs on
5.3 MB; validating even a 50-dataset sample means downloading tens of gigabytes. The honest
first step is to measure the download toll on **one** dataset and multiply, then decide —
and if the answer is that a representative sample costs more than the finding is worth, that
is a result and belongs in the recipe. See the connection-toll measurements in `provenance.json`.

**4. Do revised datasets get reused more than static ones?** `versions` (snapshot count) is
folded and unused. A dataset that is corrected after deposit is a dataset somebody is
maintaining.

*Falsifier:* revisions accumulate with age exactly as downloads do, so an unmatched comparison
measures the calendar twice. This needs the same era matching figure 5 uses, and probably
needs revisions-per-year rather than a count.

## One the register cannot answer, stated so it is not attempted again

**Why the 2025-26 datasets stopped getting validator verdicts.** Figure 3 measures the
collapse — 63% of 2024 deposits, 7% of 2025, 1% of 2026 — and deliberately does not explain
it. `issuesStatus` being empty is consistent with the validator not being run, with a new
validator version whose output is not written to this field, and with a backfill that has not
reached recent snapshots. **The API returns the same null for all three.** Separating them
needs OpenNeuro's changelog or a maintainer, not more querying, and that is a contact question
rather than a derivation.
