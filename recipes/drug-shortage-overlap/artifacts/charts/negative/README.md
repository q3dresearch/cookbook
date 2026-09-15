# Worked failures, kept on purpose

These five are **not** figures this recipe ships. They are kept as negative examples
because a merely bad chart is clutter but a *convincing* bad chart is a teaching case.
Four are correct, legible, and answer nothing a reader can act on. The fifth answered
something — on half the data.

| figure | what it does | why it fails |
| --- | --- | --- |
| `1-three-registers` | names the drugs short in all three countries in a grid | **a pretty table.** The reader is handed the join to do by eye, which was the one job supposed to be done for them |
| `2-string-vs-code` | shows the string key against the code key | **a pretty table.** Correct and legible, and it makes the reader compare `mesalamin` against `mesalazin` themselves |
| `3-suppliers` | counts firms per shared substance | **a single axis.** It reports a count and stops — no action, no conditional, no segmentation |
| `4-inspection-null` | three near-identical OAI-rate bars | **a single axis**, and a null that does not say what it closes. "So stop looking at compliance" is left to be inferred, and most readers will not |
| `5-dilute` | concentration in mg/mL against years on the list, chronic injectables | **half the register.** Shipped as a finding at p = 0.0025, computed on one page of a two-page feed. On all 1,619 rows it is p = 0.047, and p = 0.079 without four bulk-load dates. It had a mechanism, a control and a censoring caveat drawn on its face, which is exactly why it was believed |

The first four were replaced by one figure, [`../1-what-to-do.svg`](../1-what-to-do.svg).
Nothing was added to the data: figures 1 and 3 each spent a whole chart on one column,
and crossing those same two columns partitions every substance into populations with
different correct responses.

The fifth was replaced by nothing. Its text is computed, not typed, so it stays an
honest record of what the full register says rather than a frozen copy of the wrong
version.

Regenerate them with `python3 negative/chart-N-*.py` from `artifacts/scripts/`. They
read the same archive as everything else and are re-derived, not frozen — a negative
example that has drifted from the data is no longer an example of anything.
