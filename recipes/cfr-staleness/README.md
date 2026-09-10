# When US regulation was last touched, and which of it already expired

**Published 2026-09-10** · nine figures, fifteen scripts · source: the free
[eCFR API](https://www.ecfr.gov/developers), no key, no account · everything here
re-derives from a local capture with no network access.

Ask when a US regulation was last changed and nobody publishes the answer. But
every section of the code carries a bracketed source note listing its first
Federal Register citation and every amendment since. Parse those and you get the
answer for the whole title at once.

We did it for two: **Title 12 (Banks and Banking)** and **Title 29 (Labor)**.

## The short version

- Banking's median rule is **9.8 years old**, but 194 sections have not been
  touched in 30 years and the oldest dates from **1946**.
- **Most of that old tail is not law.** 39% of it is a genre the publisher labels
  `Interpretations` — rulings that get superseded, never edited. Never being
  amended is what they are for.
- **That correction does not travel.** Labor uses the same genre and marks it
  differently, so the same detector returns 6% there. An empty field looks exactly
  like an absent thing.
- **Age is the wrong screen anyway.** Compare a section to its neighbours instead
  and you can separate *forgotten* from *deliberately left alone*. 226 sections
  are frozen inside parts their agency reopened.
- **Eight banking rules have passed an expiry date written in their own text and
  are still printed.** Three were amended *after* it.
- **Nobody prunes.** Routine removal runs at about 78 sections a year, and when it
  happens a whole part goes at once.

## How old is the code?

![When Title 12 was last touched](artifacts/charts/cfr-staleness-title12.svg)

Title 12 is 449 parts and 7,180 sections. The obvious guess — banking is
constantly re-regulated, so it should look young — is right about the bulk and
wrong about the shape. Median age 9.8 years, 1,853 sections amended in the 2010s
or later, and then a long thin tail. The oldest is § 220.101, on prompt settlement
by broker-dealer customers, published **7 December 1946**, opening "The Board has
recently considered…".

**That tail is mostly a genre, not neglect.** Those old sections sit in a subject
group the publisher itself labels `Interpretations`: Board and agency rulings that
get *superseded* by later rulings rather than edited in place.

| last amended | sections | share that are interpretations |
| --- | --- | --- |
| before 1980 | 60 | **77%** |
| 30 years or older | 194 | **39%** |
| in the 1940s | 4 | **100%** |

The label is a field in the XML, so the correction is mechanical. Skip it and you
overstate the tail by roughly a third — this recipe did, until the split was made.

## Who is old, and what is old

![Age by agency, with annotated outliers](artifacts/charts/cfr-age-by-agency.svg)

| agency | sections | median | oldest |
| --- | --- | --- | --- |
| Farm Credit Administration | 331 | 16.4 y | 54.2 y |
| Federal Reserve | 601 | 11.8 y | **79.7 y** |
| NCUA | 330 | 9.5 y | 47.0 y |
| FDIC | 396 | 8.5 y | 75.8 y |
| CFPB | 169 | 8.0 y | 14.7 y |
| OCC | 400 | 6.9 y | 32.2 y |

The Federal Reserve holds the deep tail because it is the agency that publishes
interpretations at volume. Farm Credit has the oldest median — a small regulator
with a large rulebook and little reason to reopen it.

**Read the CFPB row against the agency, not the rule.** Nothing it wrote can be
older than 14.7 years, because the bureau did not exist before 2011. A young
median can mean a diligent regulator or a new one, and the chart marks which.

![Age by functional category](artifacts/charts/cfr-age-by-category.svg)

Grouped by what a rule *does* rather than who wrote it, age separates the
categories sharply and amendment counts barely move at all.

| category | median age | mean amendments |
| --- | --- | --- |
| Interpretation | **44.1 y** | 0.7 |
| Disclosure & consumer | 12.7 y | 1.8 |
| Lending & credit | 11.3 y | 2.0 |
| Application & licensing | 8.2 y | 1.6 |
| **Capital & risk** | **6.6 y** | 1.8 |

Capital rules are the most rewritten thing in banking; consumer disclosure is the
stickiest. But every category sits between 1.3 and 2.0 amendments per section
except Interpretation at 0.7 — and that exception is just the genre defining
itself. **How often a rule is revised tells you much less than how long ago it
last was.**

**High churn is not dysfunction.** Seven of the twenty most-amended sections in
Title 12 are titled "Definitions"; across the title those average 2.5 amendments
against 1.6 overall. A definitions section is the header file of a regulation — it
gets touched whenever anything downstream changes a term.

## Does any of this travel? No.

![The genre correction is a Title 12 convention](artifacts/charts/cfr-control-title29.svg)

One title proves nothing, so we ran the same pipeline over Title 29 (Labor).

| | Banking | Labor |
| --- | --- | --- |
| dated sections | 2,493 | 2,386 |
| median age | 9.8 y | **14.4 y** |
| 30 years or older | 194 | **626** |
| of those, labelled `Interpretations` | **39%** | **6%** |

**The correction fails, and it fails silently.** `Interpretations` appears as a
subject group 12 times in Title 12 and once in Title 29. Run the detector on Labor
and it returns 6% — not because the genre is absent, but because the *label* is.

Labor marks the same genre in prose instead: six parts each carry a section headed
*"Interpretations made, continued, and superseded by this part"*, which is the FLSA
interpretive-bulletin series announcing itself. Using that raises Labor to **12%**
— still nowhere near 39%.

So Labor's 626 old sections really are mostly un-updated regulation: OSHA
construction standards, Wage and Hour overtime rules, EEOC recordkeeping. **In
banking the oldest text is not regulation. In labour law it is.**

The lesson is narrower and more useful than "it does not travel": the genre exists
in both, each publisher marks it somewhere different, so any cross-title measure
needs a per-title detector *and* a check that it actually fired.

## Frozen, or forgotten?

![Section age against its neighbourhood](artifacts/charts/cfr-settled-vs-fossil.svg)

A section nobody has amended looks identical whether it was deliberately left
alone or never reopened. Its neighbours tell you which — compare it to the other
dated sections in its part.

| | | share |
| --- | --- | --- |
| **Fossil** | frozen section, frozen part | 994 · 41% |
| **Live** | recent section, active part | 984 · 40% |
| **Problem child** | recent section, otherwise quiet part | 236 · 10% |
| **Settled** | frozen section, *active* part | 226 · 9% |

**The 226 settled sections are the interesting ones**: somebody reopened the part
and chose to leave this alone. § 333.1 — the FDIC's five categories of bank
business — has stood since 1950 while the rest of Part 333 was reworked around it.

Two things to know before using those numbers. **A third of sections (774) sit
exactly on the diagonal** because their whole part was amended in one action, so
"as stale as its neighbourhood" is true by construction — that inflates Fossil and
Live, and cannot touch Settled or Problem child. And **53 sections are the only
dated section in their part**, so they have no neighbourhood at all and are
excluded rather than compared to themselves.

## Eight rules say they expired

![Rules that say they are dead, and the edits made afterwards](artifacts/charts/cfr-dead-letter.svg)

Some rules set their own end date — *this section expires on X*. That is a promise
the code makes to itself, and it is checkable.

| section | says it expires | last amended | |
| --- | --- | --- | --- |
| **12 CFR 208.23** Agricultural loan loss amortization | 1 Jan 1999 | **11 Oct 2013** | edited 14 years after it died |
| **12 CFR 238.86** Exemptions | 31 Dec 2012 | **2 Mar 2020** | edited 7 years after |
| **12 CFR 205.3** Coverage | 31 Dec 2009 | 1 Apr 2010 | |
| **12 CFR 217.303 / 3.304 / 324.304** Temporary leverage exclusions | 31 Mar 2021 | 6 Jan 2021 | one rule, three agencies |
| **12 CFR 1005.32** Estimates | 21 Jul 2020 | 5 Jun 2020 | |
| **12 CFR 217.306** Building Block Approach | 31 Mar 2026 | 27 Nov 2023 | |

§ 208.23's own paragraph (f) reads *"The terms of this section will no longer be in
effect as of January 1, 1999"* — and the Federal Reserve amended it in 2013. The
2021 entry is one rule issued in parallel by the Fed, OCC and FDIC; all three
expired, none removed, which makes the omission structural rather than one slow
office. **Title 29 has none.**

**A sunset clause here is not a mechanism, it is a sentence.** Of 14,451 sections,
53 set their own expiry — under half a percent — and 44 of those give no date, so
nothing can be computed about them.

## Why nobody catches them

![Parts are not pruned, they are opened once and closed](artifacts/charts/cfr-removal-shape.svg)

The obvious guess is that expired text survives in parts nobody visits. It is
wrong. **§ 208.23 expired in 1999, and in 2019 the Federal Reserve deleted eight
*other* sections from part 208 and left it standing.** § 238.86 expired in 2012;
part 238 lost seven sections in 2024; it survived.

Removal is a part-level event. 752 routine removals fall in just 96 of 449 parts,
the top ten parts account for half of them, and **of the 55 parts that lost three
or more sections, 43 lost every one on a single day.** A rulemaking opens a part,
deletes what it came for, and closes it.

So there is no attrition to predict. *"Which section is removed next"* has no
answer. *"Which part is about to be opened"* does, and it is a rulemaking
calendar, not this dataset. What this dataset can do is hand that rulemaking a
list of what to delete while the part is open.

![Creation against removal](artifacts/charts/cfr-growth-vs-removal.svg)

1,588 sections have been removed since the version record opens in 2017, and
**836 of them went on a single day** — 11 October 2018, the Office of Thrift
Supervision's entire rulebook, cleared seven years after Dodd-Frank abolished the
agency. Strip that and removal runs at about **78 sections a year**.

The two halves of that chart are not a balance and it says so: up counts survivors
by birth decade, down counts deaths by death decade and only from 2017. A true net
is not recoverable at all, because the version feed opens with a 2016–17 baseline
load.

## What gets written, and what gets abandoned

![What the code keeps writing, and what it stops touching](artifacts/charts/cfr-lifecycle.svg)

- **Capital & risk** is the outlier both ways: 84% written since 2010, only 24%
  stale. That is Dodd-Frank and Basel III arriving as text.
- **Consumer disclosure** is the mirror — 53% new *and* 62% stale. New products get
  new rules while the old regime is never reopened, so the category grows at one
  end and rots at the other.
- **Interpretation** is the abandoned corner, 2% new and 95% stale. Expected, and
  it calibrates reading the rest.
- **Labour law barely rewrites itself.** Its most-renewed category is *Procedure &
  appeals* at 40%, against banking's 84%. What changes in Title 29 is how you file,
  not what the rule says.

**So new regulation appears where a statute just landed, not where the problem is
worst.** To guess what the code adds next, read the last major act of Congress in
that domain.

## What to do with it

**If you are picking rules to review, repeal or re-read, do not screen on age.** It
fails both ways at once: it surfaces 1946 interpretations that are inert by design,
and it misses the 226 settled sections where an agency actively chose to leave
something standing. Age finds text nobody has typed on. You want text nobody has
**chosen**.

**Start with the eight rules that already said they expired.** Every other removal
candidate needs someone to argue a rule is unnecessary. These need someone to read
the rule's own sentence. No constituency, no notice-and-comment case the drafters
did not already make — and finding them is one regular expression.

**Then use the quadrant, not the calendar.** *Settled* is where a live agency made
a choice that is now decades old, the highest yield per section read. *Problem
child* is usually a definition doing structural work. *Fossil* is the pile age
alone would have handed you, and it is 41% of the title.

**And do not carry the genre correction to another title** without checking that
the label exists there.

*Who this is for:* an agency running a retrospective review; a policy shop building
a deregulation list; a compliance function choosing what to re-read this year; a
researcher who wants regulatory stock rather than restriction counts.

## What not to trust

**Coverage is 35%, and it is the binding limit.** Only 2,493 of 7,180 Title 12
sections carry their own source note; the rest inherit one from their part or have
none. Inherited notes sit under actively amended parts, so **every old-section
count here is a floor**, and every share is a share of the covered set rather than
of the title.

**Some figures cannot be read alone:**

- The age chart needs the control. Its genre split is a Title 12 convention.
- The agency chart needs its founding-date marks — CFPB's box ends because the
  bureau does. FHFA is *not* marked: it is 19 years old and holds 26-year-old rules
  inherited from OFHEO.
- The quadrant needs the co-amendment note above. Settled and Problem child carry
  the conclusion; Fossil and Live are inflated.
- The removal chart is not a net, and the dead-letter chart is eight hits out of
  fourteen thousand — trustworthy only because every one was read by hand.
- The category chart's categories are ours, not the publisher's. Only
  `Interpretation` comes from the source; 28% of sections match none of them, and
  `Other` is excluded from the plot rather than ranked.

**Other things worth carrying:**

- **Source notes only describe current text.** Republishing a section replaces its
  citation history, so "never amended" means never amended *since last republished*
  — and that undercounts exactly the sections rewritten most.
- **Last-amended is not severity.** A 1946 interpretation may be perfectly sound; a
  2024 technical correction may have fixed nothing. This tells you where to look,
  not what you will find.
- **Removals are only visible from 2017.** Earlier decades are unmeasured, not zero.
- **Two titles is not the CFR.**

*Every question this recipe asked — answered, partial and open, with what would
close each one — is in
[`artifacts/research-questions/questions.md`](artifacts/research-questions/questions.md).*

## Nothing here is perishable

You do not need to hurry and you do not need to trust our snapshot. The eCFR
archives itself: the versions API goes back to 2017, govinfo keeps annual CFR
editions as bulk XML to 1996, and the
[List of CFR Sections Affected](https://www.govinfo.gov/app/collection/lsa) has
recorded every amended section monthly for decades. Run `capture.py` and you have
your own copy.

What nobody appears to have done is invert that monthly *flow* into a *stock* — a
per-section last-touched date for the whole code, with the interpretation genre
split out. RegData/QuantGov counts restrictions ("shall", "must", "may not") by
industry; the LSA records what moved last month. Neither answers "when did each
rule last move".

## Run it

An afternoon for one title once the traps are known: capture is about 50 minutes
unattended for Title 12 (9.8 MB gzipped, resumable), the derive takes seconds. All
50 titles is roughly a day of fetching.

```sh
export CFR_WORK=./work
python artifacts/scripts/capture.py 12 2026-09-01   # ~50 min, resumable
python artifacts/scripts/derive.py   12
python artifacts/scripts/versions.py 12             # removal events
python artifacts/scripts/capture.py 29 2026-09-01   # the control
python artifacts/scripts/derive.py   29

python artifacts/scripts/chart_decades.py
python artifacts/scripts/chart_box.py agency
python artifacts/scripts/chart_box.py category
python artifacts/scripts/chart_quadrant.py
python artifacts/scripts/chart_growth.py
python artifacts/scripts/chart_control.py
python artifacts/scripts/chart_removal_shape.py
python artifacts/scripts/chart_lifecycle.py

python artifacts/scripts/sunset.py $CFR_WORK/raw/ecfr/title-12/2026-09-01 > $CFR_WORK/sunset12.csv
python artifacts/scripts/sunset.py $CFR_WORK/raw/ecfr/title-29/2026-09-01 > $CFR_WORK/sunset29.csv
python artifacts/scripts/chart_deadletter.py $CFR_WORK/sunset12.csv $CFR_WORK/sunset29.csv
```

**Four API traps**, all of which will catch you out silently:

- `--compressed` is mandatory on the full-text endpoint or you get HTTP 406.
- The versions endpoint **truncates at 1,000 records** while reporting the true
  count in `meta.result_count`. Paginate with `page=N`; it rejects `per_page`.
- `amendment_date` in that feed clusters on a 2016–17 baseline load. It is a floor,
  not history — real dates live in the XML source notes.
- `removed: true` is an **event**, not a status. A section removed in 2017 may be
  in force today; current status comes from `reserved` in the structure JSON.

`sectext.py 220.101 333.1` prints a section's text and its enclosing subpart from
the raw store — the tool for checking what an outlier actually says before
believing a chart about it.
