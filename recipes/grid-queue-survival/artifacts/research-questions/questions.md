# Open questions

**The test for whether this recipe is finished:** would answering the question
change the decision it drives — compare grids before technologies, expect deaths
in year one and builds in year six, and treat intake and the facilities stage as
separate problems? A question that would not change that is recorded and does not
block.

By that test **no question is live.**

## 1. Is California unusual, or is the Midwest?

Two operators is one comparison. The gap is large and it holds across cohorts, but
nothing here says which end of it is the anomaly — and that changes who the
finding is aimed at. If CAISO is the outlier it is a California story; if MISO is,
it is a story about what a well-run queue looks like and every other grid should
be measured against it.

**How to settle it:** NYISO publishes a queue in the same shape (xlsx, ~470 KB)
and was reachable when last probed. One more parser, no new analysis.

**Status:** the highest-value extension and the cheapest. Not blocking, because
the advice — compare grids — holds whichever way it resolves.

## 2. Where does CAISO's 2018–2021 rate settle?

It reads 5.2%, against 16.6% for 2013–2017. But a quarter of that cohort is still
unresolved and withdrawals resolve years before builds do, so 5.2% is a floor and
will rise. How far is unknown.

**How to settle it:** re-harvest annually and watch the cohort close. `history.csv`
exists for this.

**Status:** the number is published as a floor and labelled as one.

## 3. Why do the two grids differ?

MISO has more transmission headroom and less congestion than California. The gap
is real and survives controlling for technology and entry year, but nothing here
separates *queue process* from *the grid being queued for*. A FERC-level reading
of this finding would need that separation and this data cannot provide it.

**Status:** stated as a limit rather than answered. It is the difference between
"CAISO should reform its process" and "California is a harder place to build",
and this recipe cannot choose between them.

## 4. What is inside the 173 unmapped active projects?

Almost all are MISO rows with a blank technology. They are printed on
`queue-exposure` rather than dropped silently, but if they are disproportionately
one family that chart understates it.

## 5. Geothermal on 31 projects

3.2% is the lowest build rate in the data and rests on the thinnest sample behind
any figure here. It is reported with its n everywhere it appears and should not be
quoted without it.

## Answered

* **Why do interconnection projects die?** 52% never reach any study, and they
  leave in a median of 0.8 years having consumed no study capacity.
* **How long from queue to withdrawal?** Median 1.0 year to a death against 6.1
  years to an energisation. The queue kills fast and builds slow.
* **Which technology survives best?** Age-matched, storage at 19.6% and
  simple-cycle gas at 10.0% — the reverse of what this recipe said in its first
  version, which was comparing 2007 rules to 2020 rules.
* **Does the operator matter more than the technology?** Yes. 1.9× pooled and
  2.8–3.4× per technology, against roughly 2× between technologies.
* **Was MISO's advantage a thin-sample artefact?** No. Its 2018–2021 cohort
  resolves at 31.9% on 1,187 projects against 31.2% on 253. The advantage held as
  the sample grew twentyfold.
* **Can MISO be included in the time-based charts?** No, and the attempt is
  instructive: it publishes no withdrawal dates, so every MISO family scored
  exactly 100% survival. A missing column rendering as a perfect result.
