# One short report in five is reproducible from public data. The rest needed someone to talk.

**Published 2026-09-11** · seven figures, fifteen scripts · source: six activist
short-selling firms, 273 first-look reports, 2.8M words · no key, no account ·
**the sources are private companies and can delete any of this tomorrow**, so a
capture manifest with a sha256 per resource ships alongside.

## What this is

An activist short seller publishes a report saying a listed company is worth less
than it trades for, having bet that it is. The obvious question for anyone building
screening tools is: **how much of that work is derivable from public structured
data?** If most of it is filings and court records, a tool can get close. If most of
it is a former employee agreeing to talk, no tool ever will.

Hindenburg Research answers it in unusual detail — it published 105 posts between
2017 and 2025 and then wound down, so the archive is closed, complete, and has no
survivorship in it. That is the deep source. Five more firms are here as controls,
because a single firm's habits will otherwise be mistaken for the practice, which is
exactly what happened on the first pass.

*Who has a stake:* a forensic analyst deciding what to examine first · a journalist
or regulator weighing a short report's evidence base · anyone building screening
tools who needs to know which half is automatable.

## The short version

- **Only 20% of reports rest on public sources alone.** 67% need something no
  database holds. The first version of this recipe said 50/43 — it never asked
  whether they talked to anyone.
- **The thing that cannot be automated is usually a phone call**, not a leak. 60% of
  reports cite someone interviewed; 31% have an interview as their *only*
  non-public evidence.
- **That floor holds across firms.** "Needs a person" never drops below 44% and the
  median firm sits at 70% — across six firms, sixteen years and two continents.
- **The field splits into two businesses and nothing sits between them.** Fire-once
  firms publish 5–14% follow-ups; campaigners publish 55–61%.
- **Follow-ups are rhetoric.** Field legwork and registry work fall to zero;
  interviews roughly halve. Pool them in and firm rankings reverse.
- **Hindenburg learned this.** Its interview rate went 21% → 75% across three eras
  while Muddy Waters' highest era was its first, in 2010.

## How hard is it to do alone

![What each tier of evidence demands](artifacts/charts/independent-forensic-barrier.svg)

Every source cited across 94 initial Hindenburg reports, graded by what it demands
of someone with no budget, no travel and no sources.

| | reports | share |
| --- | --- | --- |
| use at least one PUBLIC evidence type | 86 / 94 | **91%** |
| use ONLY public evidence | 19 / 94 | **20%** |
| need something no database holds | 63 / 94 | **67%** |

And the non-public half is not exotic:

| | reports | share |
| --- | --- | --- |
| someone they interviewed | 56 / 94 | **60%** |
| their own people on the ground | 29 / 94 | 31% |
| a whistleblower | 8 / 94 | 9% |

**For 31% of reports the only thing you cannot reproduce is a conversation.** That
is a cheaper barrier than travel and a less lucky one than a source walking in, and
it is the one a tool cannot cross.

## Does that hold anywhere else

![Where six firms agree and disagree](artifacts/charts/people-not-data.svg)

Twelve kinds of evidence, six firms, ordered by how much they disagree. Every
measure spreads 12–84 points. The share resting on a person is the one with a floor:
**44% at the lowest, 70% at the median.**

Read the greyed rows carefully — import records and whistleblowers have narrow
spreads because *nobody does them*, which is a floor, not a consensus.

**Spruce Point is the low end at 44% and does not explain away.** Its reports are as
prose-dense as everyone's (22 words a sentence, 96% prose); its own boilerplate says
it "frequently speaks with industry experts and former employees"; widening the
probe for its vocabulary moves it 4 points. Either it leans less on people or it
does the work without writing the sentence, and this corpus cannot tell which.

## Two businesses, not one practice

![Fire once, or campaign](artifacts/charts/two-camps.svg)

| | targets | reports | follow-up |
| --- | --- | --- | --- |
| Hindenburg | 98 | 103 | **5%** |
| Night Market | 23 | 26 | 12% |
| Fuzzy Panda | 25 | 29 | 14% |
| Spruce Point | 48 | 56 | 14% |
| J Capital | 97 | 215 | **55%** |
| Muddy Waters | 56 | 144 | **61%** |

**Nothing lands between 14% and 55%.** Hindenburg is a clean example of one model,
not an outlier from a single practice — which is what one control firm had
suggested, wrongly.

The camps do *not* predict method. Four of twelve evidence measures separate them
cleanly, 1.6 are expected by chance, P = 0.065. Suggestive, uncrossed.

## Why the pooled numbers lie

![Follow-ups are short and cite nothing](artifacts/charts/two-businesses.svg)

Counting all 144 Muddy Waters reports, 47% are desk-reachable against Hindenburg's
37% — it looks like the easier corpus. It is not. **61% of its output is follow-ups**,
which cite almost nothing and therefore score as "reachable from a desk". On
first-look reports the order flips to 4% against 20%.

Always split first-look from follow-up before comparing anything.

## One firm learned to interview people

![The turn to people](artifacts/charts/the-turn-to-people.svg)

Hindenburg goes 21% → 75% across three eras and the confidence intervals separate.
Muddy Waters' highest era is its first — 73% in 2010–13 — and every one of its
intervals overlaps every other. Night Market the same.

So this is not the practice changing. It is one firm growing into a method the
others already had, and "the method got richer over time" was a Hindenburg
biography read as industry history.

## Longer means wider, not padded

![Length is breadth](artifacts/charts/length-is-breadth.svg)

r = +0.73 at Hindenburg, +0.59 at Muddy Waters. The shorter half of Hindenburg's
reports carries a median 2 kinds of evidence; the longer half, 7.

And Muddy Waters' first reports that went on to become campaigns are the **longer**
ones — 10,813 words against 6,864 — which is the opposite of a follow-up repairing a
thin opening. Permutation p = 0.073 on length, 0.178 on interviews. Two signals, same
direction, neither conclusive.

## Who can be studied at all

![The selection this sits inside](artifacts/charts/who-can-be-studied.svg)

**4 of 17 firms refuse the connection outright.** Several more publish a teaser and
nothing else. Every finding above is a finding about the firms that publish
readably, and that is a smaller set than the field.

## What to do with it

**Build the tool for the fifth that is reachable, and staff the rest.**

- A screening tool over filings, court records, registries and archives reconstructs
  the evidence base of **one report in five**. That is real and worth building.
- Two in three need a person. Half of *those* need only a phone call, not travel and
  not luck — which is a hiring decision, not an engineering one.
- **Date the claim before trusting a method inventory.** Hindenburg's pre-2020 work
  is a different operation from its post-2020 work.
- **Check the firm's cadence before reading any rate.** A campaigner's pooled
  numbers are dominated by rebuttals that cite nothing.

## What not to trust

- **This counts what a report DECLARES.** A firm that uses a terminal without naming
  it, or interviews someone without writing the sentence, is invisible. Every share
  here is a floor.
- **Published reports only.** Investigations abandoned when the thesis collapsed
  leave no trace anywhere, at any firm.
- **The probe list was written by reading Hindenburg** and therefore measured
  Hindenburg. Night Market scored zero on original sourcing while filing FOIA
  requests and interviewing at trade conferences. Three widenings followed, each
  forced by a firm that scored strangely — and the next firm would probably force a
  fourth.
- **Field legwork is hand-ruled, not detected.** The regex was wrong in both
  directions: loose, it counted the firm calling itself "professional fraud
  researchers" and a state regulator's investigators; tight, it missed "an
  investigator sent to the exact site". All 12 disputed reports were read and the
  verdicts recorded in `corpuslib.py`.
- **Spruce Point and Viceroy are samples**, 45 of 134 and 9 of 331. Every other firm
  is its whole archive.
- **A verified ticker exists for 23% of reports.** The first exchange-prefixed symbol
  is wrong roughly 30% of the time, because reports open with peer comparison tables
   — Kratos returns Parrot SA, Inpixon returns Kodak.
- **There is no price join.** Four free sources tested cold: Stooq serves a JS
  challenge, Yahoo 429s, Nasdaq returns empty, SEC needs a declared User-Agent and
  has no prices. Even given one, three rows in four would be hand-built.

*Every question this recipe asks — with its status, what would settle it, and which
answers describe, predict or prescribe — is the working document at
[`artifacts/research-questions/questions.md`](artifacts/research-questions/questions.md),
including a section on what to expect if you run this on a firm not covered here.*

## Why hasn't anyone

Plenty have studied short sellers — the academic literature on activist short
campaigns and price impact is large, and it works from campaign databases like
Activist Insight, which record *that* a campaign happened and what the stock did.

What I could not find is the corpus read as text: counting what the reports say they
looked at, then asking which of it a machine could have found. That is a small,
mechanical cut and worth being honest that it is small. Its one durable contribution
is probably the negative: **the single biggest evidence type is a conversation, and
it was invisible to the first probe list because nobody thinks to grep for "told
us".**

## Run it

No key, no account. Capture is slow and polite; everything after it is instant.

```sh
python artifacts/scripts/capture_control.py            # six firms, sitemap-first
python artifacts/scripts/capture_access.py             # the 17-firm access census
python artifacts/scripts/build_manifest.py             # url + sha256 per resource
python artifacts/scripts/chart-people-not-data.py
python artifacts/scripts/chart-two-camps.py
python artifacts/scripts/tickers.py                    # + validate_tickers.py
```

**Four traps, all silent:**

- **`/wp-json/wp/v2/posts` is the wrong question.** Muddy Waters keeps 146 reports in
  a custom post type that endpoint cannot return. Ask the sitemap first, always.
- **The page is often not the report.** Three of six firms publish a ~350-word teaser
  over a linked PDF. Counting the page gives 319 words where the report is 4,406.
- **Boilerplate needs removing twice, two different ways.** HTML: the shared
  prefix/suffix across pages (Spruce Point appends 9,525 words). PDF: that returns
  zero, because `pdftotext` scatters the legal block through the body — match
  repeated *sentences* instead, after collapsing whitespace.
- **A probe matching ~100% is matching the template.** Night Market read as 100%
  social-media citation because its navigation bar contains a link saying "Twitter".
