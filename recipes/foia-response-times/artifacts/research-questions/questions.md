# Open questions

**The test for whether this recipe is finished:** would answering the question
change the decision it drives — count open-past-due requests as missed, and check
coverage and composition before reading any aggregate? A question that would not
change that is recorded and does not block.

By that test **no question is live.** The four traps are each demonstrated on
data in hand, and every question below sharpens or extends the recipe without
altering what a reader should do.

## 1. Does the closed-only measure hide a decline everywhere, or only where backlogs grow?

New York City is one city. The mechanism is general — dropping open requests
from the denominator removes exactly the late ones — but its *size* depends on
how fast a backlog builds, and NYC's went from 1% to 29% open in six years. A
jurisdiction with a stable backlog would show the two measures tracking.

**How to settle it:** New Orleans has due dates and is already harvested, but its
coverage break makes the series unusable after 2024. Chicago, Seattle and
Washington DC publish comparable logs; two more with due dates would establish
whether the gap scales with backlog growth as predicted.

**Status:** the strongest extension, and it makes the finding a rule rather than
a case study. Not blocking, because the arithmetic fix is correct regardless.

## 2. Why did New York City's backlog triple?

Open-past-due went from 1% of requests in 2019 to 29% in 2025. Volume rose
57% over the same window (56,886 to 89,779 received), which does not by itself
explain it — a system keeping pace would absorb that.

**How to settle it:** the log carries `agency`, so the growth can be attributed.
If it concentrates in a few agencies it is a capacity story; if it is uniform it
is a policy or process story. This is one query against data already harvested.

**Status:** cheap, and interesting, but it does not change the measurement advice.

## 3. Is the Oregon requester mix unusual?

62% environmental consultants is the finding most likely to be quoted, and it
rests on one agency in one state — and an agency whose subject matter
(contaminated land) invites exactly that traffic. A state environmental regulator
is close to a worst case for "records regime as title-search subsidy".

**How to settle it:** Oregon DEQ is the only source here that types its
requesters natively. Finding a second agency that does, ideally outside
environmental regulation, would show whether this is a property-diligence
phenomenon or a general one.

**Status:** the claim is currently stated about one agency and should stay that
way until a second exists.

## 4. What happens to requests that are never closed?

The recipe counts a request open past its due date as missed, which is the right
call for a compliance measure. It does not ask what eventually becomes of them —
whether they are fulfilled very late, quietly abandoned, or withdrawn.

**How to settle it:** re-harvest in six months and follow the 2025 cohort by
`request_id`. Four of the five sources publish the agency's own case number;
Oregon publishes none and cannot be followed.

**Status:** possible as of method 1.2.0 and not before. The first harvester
discarded the case number, which made this question unanswerable while
`history.csv` sat here claiming to support exactly it. The 2026-09-10 keyed
harvest is the baseline; the earliest this can be answered is roughly 2027-03.

## 5. Do agencies game the due date?

New Orleans Fire halved its allowed window from 15 days to 7 while its on-time
rate tripled, which reads as a genuine process improvement. The opposite
manoeuvre — extending the statutory clock rather than answering faster — would
look identical in an on-time rate and opposite in days-to-close.

**How to settle it:** both fields are present. Track median days *allowed*
alongside median days *to close*, per agency per year. An agency whose allowed
window grows while its closing time is flat is buying compliance.

**Status:** not started, and it is the natural fifth trap for this recipe.

## Answered
* **Do agencies extend the clock rather than answer faster?** Yes, and it became
  the fifth trap. New York's median allowed window went 53 days to 136 while days
  actually taken went 29 to 28.
* **Is the backlog system-wide or concentrated?** Two agencies. The police
  department holds 61% of every request open past its deadline and the fire
  department 31%; the top five hold 99% and 32 of 60 agencies have none.
* **How old is the backlog?** The median request open past due is 393 days past
  it. 52% are more than a year past, 32% more than two, and the oldest is 8.8
  years. "Late" is the wrong word for it.
* **Did the window grow everywhere?** No, and this corrected the fifth trap. The
  citywide extension is almost entirely the police department, 55 to 139 days.
  The fire department, holding a third of the backlog, went 35 to 38 and simply
  stopped closing. The Department of Education *shortened* its window to seven
  days and leaves 87% of its own requests open past it. Two failure modes, and a
  cap on the allowed window would reach only one.
* **Is the extension drift or policy?** Steps, not drift: +30 days in 2018Q3,
  +42 in 2021Q1, +34 in 2022Q3, then flat at ~136 since 2023. That shape is a
  decision being taken three times, not a queue slowly lengthening.
* **Do the failure modes appear in New Orleans?** No — a clean negative control.
  79 requests open past due out of 10,369, and windows steady at 5 to 7 days.
  Whatever is happening in New York is not what a records system does by nature.
* **Does the filing channel matter?** Yes, and it survives holding the agency
  fixed. Inside the police department, in-person requests close in 5 days at 98%
  on time with 6% still open; portal requests, 91% of its volume, take 27 days at
  78% with 30% still open.


* **Do the numbers survive a fresh harvest?** Yes, exactly. Re-fetched
  2026-09-10 at 730,312 rows against 729,605; New York City compliance is 82% to
  56% on both measures in both runs.
* **Can the figures be re-derived?** They could not, for a fortnight. Three of
  four scripts imported a shared helper from a deleted path while the recipe read
  as finished with four figures. Fixed by vendoring, and a pre-publication check
  now fails any recipe whose scripts cannot import.
* **Does the recipe key on anything?** It did not, and nobody noticed until the
  build sequence asked. Four of five sources publish a case number and the
  harvester dropped all of them, so the only longitudinal question here could not
  be answered and the recipe still read as finished. Adding the column also
  needed the disclosure check narrowed rather than loosened: a numeric case
  number matches the postcode pattern, and relaxing the pattern to tolerate it
  would have stopped it catching a real postcode. The case-number column is
  excluded from the scan instead.
* **Is the requester classification trustworthy?** No. Name-format classification
  reports 94% "person" for New Orleans where Oregon's native typing gives 8%
  "general public". It is kept, labelled unreliable, and no claim rests on it.
