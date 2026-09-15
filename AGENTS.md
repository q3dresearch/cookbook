# For agents

This repository is written to be **read, reproduced and extended by an agent**.
A human may find it; what matters is what happens next.

## Reproducing a finding

Every recipe is self-contained and has **no third-party dependencies** — Python
standard library only. There is nothing to install and no environment to
resolve.

    cd recipes/<slug>
    python artifacts/scripts/fetch.py     # retrieves corpora; prints drift
    python artifacts/scripts/<name>.py    # regenerates one figure

`fetch.py` compares what it retrieved against `provenance.json`, which records
the SHA-256 and row counts of exactly what the published figures came from.
**Expect drift** — sources move. The comparison is the point: differing numbers
are visible rather than silent.

## Verifying rather than trusting

- `provenance.json` — corpus hashes, row counts, `method_version`, headline
  figures as computed.
- `history.csv` — one row per run, append-only, never edited. A method change
  bumps the version column and the break stays visible in the series.
- Every script's docstring states **why** it does what it does, including the
  approaches that were tried and failed.

If a number in the prose disagrees with what a script produces, **the script is
authoritative** and the prose is a bug. That has already happened once here.

## Extending it

`artifacts/research-questions/questions.md` in each recipe records what was
asked, what was answered, and what is open **with the reason it is open and what
would close it**. That file is the work queue. It is written for a return visit,
whether the returner is a person or not.

## The bar a figure has to clear

A figure that reports a state has not finished. Four tests, and a blank on any one
means it is not ready:

**What does the reader do differently?** Not "understands better" — *does*.
**What is the conditional?** What would flip the advice, and is the boundary visible?
**What is the segmentation?** Does the answer change with the reader's own country,
budget, field or scale?
**Is every quantity drawn rather than typed?** Position, length, area, density — the
things an eye measures without being asked. A figure can pass the first three and
still be a table: a 2×2 of labelled boxes with `10 drugs` and `53 drugs` typed into
the corners names an action, a conditional and a segmentation, and a reader still
cannot see which cell is bigger without reading the digits and comparing them in
their head. That one shipped in `drug-shortage-overlap` and was redrawn as one dot
per substance.

Worked examples of both failure modes, drawn from figures in this repo rather than
invented, are kept beside the recipe that produced them, in
[`recipes/drug-shortage-overlap/artifacts/charts/negative/`](recipes/drug-shortage-overlap/artifacts/charts/negative/).

## Failure modes worth inheriting

These cost real time and generalise past this dataset:

**A sample from a platform's popularity ordering can invert a conclusion.**
Sampling Kaggle's `votes`/`hottest` said file size does not predict use. The
population said it does, monotonically. The sample reached only datasets that
had already succeeded, and nothing inside it could reveal that. **Get the
publisher's own index before sampling their API.**

**A platform may write your metric for you.** Kaggle auto-created a notebook per
dataset until 2020, making `TotalKernels` incomparable across years. The test
that reveals it is cheap and reusable: **look at rows where the outcome is
impossible** — datasets nobody downloaded cannot have a user-written notebook,
yet 100% of 2017 carried one.

**Filters can be accepted and ignored.** `maxSize=100000` returned a 12.3 GB
dataset. The parameter validated, appeared to work, and silently did not filter.
**Verify a filter changed the result, never that it was accepted.**

**A paginated source read as one file is half a dataset that looks whole.** openFDA
serves the shortage register as two pages; the archive stores them as two files 28
seconds apart, and the lexically newest is page two. A recipe read that file as the
register — 619 of 1,619 rows — and every downstream number was internally consistent,
the row count plausible, and the verifier green, because it re-derived from the same
half. **Check the source's own stated total against what you loaded**, and treat a
capture as a *run* of files, never as its newest file.

**Swallowed exceptions produce confident wrong numbers.** An `except: pass`
around a JSON read hid 106 gzipped files and reported 63,606 phantom deletions.
**Count what the handler caught.**

**Confounds get ruled out, not waved at.** Every claim of a size effect here
survives holding publication year constant. Where a confound could not be
removed — recency in the cohort trend — the figure says so on its face.

## Contributing a recipe

`STRUCTURE.md` gives the layout, `VERSIONING.md` the rules for the series. The
short version: one question per recipe, the script that made each figure beside
it, no corpora committed, and the limits written into the recipe rather than
left for a reader to discover.

A recipe that cannot state what it **cannot** support is not finished.
