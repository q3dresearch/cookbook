# Versioning

A recipe that re-runs is a series, and a series is only worth anything if a
change in it is attributable. Two things move independently and both are
stamped on every run.

**`method_version`** — bumped only when the analysis changes: a band boundary,
a filter, a definition. Semantic: patch for a fix that does not move the
numbers, minor for an added measure, major for a redefinition that breaks
comparability with earlier rows.

**`retrieved`** — the date the corpus was pulled. Data moving does **not** bump
the method version.

That separation is the whole point. If both could change silently in one run,
a jump in the series would be unattributable — and an unattributable jump is
indistinguishable from a mistake.

## history.csv

One row per run, appended, **never edited**. Past rows stay as they were
computed, wrong or not. When the method changes, the version column changes
mid-series and the break is visible in the data rather than buried in a commit
message.

If a past row turns out to be wrong, add a new row and say so in the recipe.
Do not silently correct it — that is the failure that ends an index's
credibility permanently, and statistical agencies avoid it by publishing
revisions rather than edits.

## Repo releases

Each release tags the whole cookbook and gets a version in `CITATION.cff`. A
finding is cited as the release plus the recipe path, so a citation resolves to
the exact method and figures the author saw — not to whatever the recipe says
today.
