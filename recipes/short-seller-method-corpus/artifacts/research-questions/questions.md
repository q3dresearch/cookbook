# Questions this recipe asks

## What the source is

**Hindenburg Research published 105 posts between August 2017 and January 2025,
then wound down.** The archive is closed, complete, and fetchable: the site's
WordPress REST API returns every post with full text, 737,421 words in total.

That makes it a rare thing — an activist short seller's entire body of work, with
no survivorship in it, because the firm stopped rather than the archive being
pruned.

**It is one firm — and the claim that it had to be was wrong.** The first sweep
asked every other firm for `/wp-json/wp/v2/posts`, got nothing, and concluded they
"block scraping or publish only PDFs". That was a fact about the probe. Muddy
Waters keeps its reports in a WordPress custom post type at
`/research/<company>/<slug>/`, which `wp/v2/posts` never returns and which only the
sitemap reveals: 146 reports across 56 targets, back to 2010.

Sitemap-first, four firms yield a usable corpus and they yield it in three
different shapes:

| firm | reports | where the text is |
| --- | --- | --- |
| Hindenburg | 94 initial, 9 follow-ups | HTML, via the REST API |
| Muddy Waters | 55 initial, 87 follow-ups | a ~350-word teaser page linking a PDF |
| Night Market | 23 initial, 3 follow-ups | HTML, in an `entry-content` block |
| J Capital | 97 targets, 215 reports | a ~530-word teaser page linking dated PDFs |

Plus The Bear Cave on Substack (505 posts, 2020-01 to 2026-09) — a recurring
newsletter rather than standalone reports, so a different genre and not pooled in
here. So Hindenburg is the deepest single source, not the only one.

*Who has a stake:* a forensic analyst deciding what to examine first · a
journalist or regulator assessing a short report's evidence base · anyone
building screening tools who needs to know which evidence is derivable from
public structured data.

| # | question | status | answer | figure |
| --- | --- | --- | --- | --- |
| 1 | **What is the denominator?** | `answered` | **94 initial reports**, not 105. Plus 9 follow-ups and 2 admin posts. Every pilot percentage was computed against the wrong base | `independent-forensic-barrier` |
| 2 | **Which evidence types recur?** | `answered` · *revised* | **Original interviews, at 60%, are the biggest single type** — and were missing from the probe list until another firm's zeros exposed it. Then SEC filings 70%, court/litigation 62%, social media 68%, paid terminal 39%, field legwork 31% | `people-not-data` |
| 3 | **How much is public structured data?** | `answered` · *revised* | **91% use at least one public type, but only 20% use ONLY public evidence and 67% need something no database holds.** The first answer said 50% and 43% — it never asked whether they talked to anyone | `independent-forensic-barrier` |
| 4 | **Did the method change?** | `answered` · *revised* | **It became human.** Original interviews went 21% → 84% → 75% across the three eras — the largest move of any evidence type. Paid terminal 18→67%, field legwork 12→46%, court records 45→79%. It started as a desk operation | `the-turn-to-people` |
| 5 | Which evidence types travel together? | `answered` | Length is breadth: the shorter half of reports uses a median 2 evidence types, the longer half 5 | `length-is-breadth` |
| 6 | **Do follow-ups differ?** | `answered` | **They are rhetoric, not research.** 3 citations across 9 follow-ups against 1,024 across 94 reports. Zero field legwork, zero registry work, and interviews fall 60% → 22% | `two-businesses` |
| 7 | Is length breadth or padding? | `answered` | Breadth. Median 2 evidence types in the shorter half, 5 in the longer | `length-is-breadth` |
| 8 | Are the cited sources free or paid? | `tested and failed` | **Third attempt, same failure.** 67% of 1,024 citations remain unclassifiable. 89% of the 820 labels appear exactly once | — *(no figure: a failed classifier gets a note, not a chart)* |
| 9 | **Does public-record-heavy evidence predict the price move?** | `blocked` | Needs a price series. Stooq now serves a JS proof-of-work challenge and Yahoo returns 429 from shared addresses; an Alpha Vantage or Tiingo key is the route | — *(blocked)* |
| 10 | **Is Hindenburg representative of the practice?** | `answered` · *revised twice* | **It is a clean example of one of two models, not an outlier.** Six firms, and nothing lands between them. Fire-once: Hindenburg 5%, Night Market 12%, Fuzzy Panda 14%, Spruce Point 14%. Campaign: J Capital 55%, Muddy Waters 61%. With Muddy Waters alone I had concluded Hindenburg was the odd one — one control is still an anecdote | `two-camps` |
| 11 | **Is the method itself the same across firms?** | `answered` · *revised twice* | **Nothing agrees; one thing has a floor.** Across six firms every measure spreads 12–84 points. The share resting on a person never falls below **44%** and the median firm is at 70% — a floor, not a consensus. The tightest spreads (import records 0–12%) are tight only because nobody does them | `people-not-data` |
| 12 | **Is Hindenburg's work easier to reproduce than its peers'?** | `answered` · *revised* | **Yes, and the pooled number says the opposite.** Desk-reachable on first-look reports: Hindenburg 20%, Night Market 30%, Muddy Waters **9%**. Pooled across all reports Muddy Waters reads 47% — diluted by 87 thin follow-ups | `two-businesses` |
| 13 | **Are follow-ups rhetoric at every firm, or only at Hindenburg?** | `answered` | **Every firm.** Hindenburg follow-ups: 0% field legwork, 0% registry, interviews 60% → 22%. Muddy Waters follow-ups fall the same way. This is the one place pooling reverses a ranking, so it is also a warning about every other firm comparison | `two-businesses` |
| 14 | **Who can be studied at all?** | `answered` | **Publishing format decides, and it is not a detail.** Of 17 firms, 4 refuse connection outright, several publish only a teaser, and the rest split between HTML and PDF. Any "study of the practice" is a study of the firms that publish in a readable shape | `who-can-be-studied` |

### Raised by the control corpus, still open

| # | question | status | answer | figure |
| --- | --- | --- | --- | --- |
| 15 | **Is the turn to interviews one firm's habit or the industry's?** | `answered` | **One firm's.** Hindenburg 21% → 75%, and its intervals separate. Muddy Waters' *highest* era is its first — 73% in 2010-13 — and every interval overlaps every other. Night Market the same. Hindenburg was learning a method the others already had | `the-turn-to-people` |
| 16 | **Do the two camps differ in method, or only in cadence?** | `answered — a null` | **Still not, but the case is strengthening as firms are added.** 4 of 12 measures separate the camps cleanly. With 2 firms a side that was P = 0.37, with 5 firms P = 0.21, with 6 firms (4 fire-once, 2 campaign) P = 0.065 — close, not crossed. The direction: fire-once firms lean on court records and social media, campaign firms on their own fieldwork. Two more firms would settle it | `people-not-data` |
| 17 | **Does a campaign mean the first report was weaker?** | `suggestive, not established` | **The opposite, and it is worth predicting on.** Muddy Waters first reports that drew follow-ups run 10,813 words against 6,864, with 59% citing interviews against 42%. But the clouds overlap: permutation p = 0.073 on length, 0.178 on interviews, at n=56. The direction is consistent across two independent signals; neither clears a bar alone. J Capital's reports are the way to settle it | `length-is-breadth` |
| 18 | **What would the blocked price join (Q9) actually change?** | `open` | This is the terminator test. If the Q3 decision — which fifth is reproducible — stands without it, the recipe ships and Q9 becomes a separate one | — |
| 19 | **Does a firm's publishing format track what it is willing to be checked on?** | `open` | Four firms refuse connection entirely and several publish only a teaser. Whether the teaser-only firms differ in anything measurable — target size, claim type, survival — cannot be answered from a teaser, which is itself the point | `who-can-be-studied` |
| 20 | **Can the target ticker be extracted automatically?** | `answered` | **For 23% of reports, verifiably.** 56% yield an exchange-prefixed symbol; of those 41% are foreign listings no free registry covers, and of the US-listed remainder **30% are contradicted by SEC's own registry** — the first symbol in a report is often a peer in a comparison table. Kratos returned Parrot SA, Progyny returned FIGS, Inpixon returned Kodak | — |
| 21 | **Why is the price join (Q9) really blocked?** | `answered` | **Not just the API.** Stooq now serves a JS challenge, Yahoo 429s, Nasdaq returns empty, SEC needs a declared User-Agent. But even with prices the join key is the problem: a verified ticker exists for 23% of reports, so 3 of 4 rows would be hand-built or wrong | — |

## If you run this on another firm

The point of doing six firms rather than one is that the method transfers and the
findings mostly do not. This is what to expect.

### What should replicate

| finding | how firm-dependent |
| --- | --- |
| **Two business models, nothing in between** | Held across all six. Fire-once 5–14% follow-ups, campaign 55–61%. Expect a new firm to land in one camp, not between them |
| **Follow-ups are rhetoric** | Held at both firms testable. Field legwork and registry work go to zero; interviews roughly halve |
| **Length is breadth, not padding** | r = +0.73 and +0.59. A long report cites more KINDS of evidence, not more of one |
| **Someone had to talk to them** | Never below 44%, median firm 70%. This is a floor, not a constant — the range is wide |
| **Pooling reverses rankings** | Guaranteed wherever a firm campaigns. Always split first-look from follow-up before comparing anything |

### What technique to use, in this order

1. **Sitemap first. Never the REST API.** `/wp-json/wp/v2/posts` returned nothing at
   Muddy Waters and the sitemap returned 146 reports — they live in a custom post
   type that endpoint cannot see. Asking the API first is how this recipe spent its
   first pass concluding, wrongly, that five firms "block scraping".
2. **Find the report tier by measuring, not guessing.** "Deeper than four path
   segments" picked per-company index pages. "The deepest tier" picked category
   pages and read Hindenburg's 737,000-word archive as 33 words. Sample every depth
   and keep whichever carries text.
3. **Subtract boilerplate twice, two different ways.** HTML: shared prefix/suffix
   across pages — Muddy Waters appends 1,613 words of terms-of-use, Spruce Point
   9,525. PDF: the same trick returns zero because pdftotext scatters the legal block
   through the body, so match repeated SENTENCES instead, after collapsing
   whitespace.
4. **Decide what "the report" is before counting words.** Three of six firms publish
   a teaser page over a linked PDF. Counting the page gives 319 words where the
   report is 4,406.
5. **Write the probe list from more than one firm.** Ours was built by reading
   Hindenburg and therefore measured Hindenburg. Night Market scored zero on
   original sourcing while filing FOIA requests and interviewing at trade
   conferences. Every probe widening since came from a firm that scored strangely.
6. **Tickers: exchange-prefixed only, then validate against SEC.** `(ABC)` in
   parentheses matches 84–96% of reports and is an acronym detector — Carvana
   returns ABS, FOIA, LTV. Take the first `NASDAQ: XYZ`, then look it up in SEC's
   `company_tickers_exchange.json` and check the registry's company name against the
   report. That catches the peer-table failures nothing else does.

### What you will not get

| | |
| --- | --- |
| **A complete field** | 4 of 17 firms refuse the connection outright (403 or no route). Several more publish a teaser and nothing else. Any study of "the practice" is a study of who publishes readably |
| **A reliable ticker** | 23% verified, 23% plausible-but-unverifiable, the rest nothing. Foreign listings are 41% of extractions and no free registry covers them |
| **A price join** | Four free sources tested cold: Stooq serves a JS challenge, Yahoo 429s, Nasdaq returns empty rows, SEC needs a declared User-Agent and has no prices anyway |
| **A reason the camps exist** | Fire-once and campaign firms are not distinguishable by method. P = 0.065 across six firms — suggestive, uncrossed. Cadence looks like a business decision, not a research one |
| **Anything about abandoned work** | Every corpus is published reports. Investigations dropped when the thesis collapsed leave no trace anywhere |

## The decision this settles

**One activist short report in five is reproducible from public sources. Two in
three rest on a person who agreed to talk, and no amount of tooling fixes that.**

The first version of this recipe said half and half. It was measuring a probe list
written by reading one firm, which had no name for an interview.

| | reports | share |
| --- | --- | --- |
| use at least one PUBLIC evidence type | 86 / 94 | **91%** |
| use ONLY public evidence | 19 / 94 | **20%** |
| need something no database holds | 63 / 94 | **67%** |

And the thing that cannot be reproduced is usually not exotic:

| the non-public half | reports | share |
| --- | --- | --- |
| someone they interviewed | 56 / 94 | **60%** |
| their own people on the ground | 28 / 94 | 30% |
| a whistleblower | 8 / 94 | 9% |

For **31%** of reports the only non-public evidence is a conversation — no site
visit, no leak. That is a cheaper barrier than travel and a less lucky one than a
source walking in, and it is the one a tool cannot cross.

**Across six firms, the floor is 44% and the median firm is at 70%.** "Needs a
person" runs 84% at Fuzzy Panda, 74% at J Capital, 70% at Night Market and Muddy
Waters, 67% at Hindenburg, 44% at Spruce Point. That is a 40-point range — not the
convergence three firms suggested, but a floor no firm goes under.

**Spruce Point is the low end, at 44%**, and it does not explain away. Its
reports are not slide decks in any way the text shows: 22 words per sentence and
96% of words in prose, the same as everyone. Widening the probe for its own
vocabulary — "channel checks", "industry contacts" — moves it from 36% to 40% and
moves nobody else at all. Either it really does lean less on people, or it does
the same work without writing the sentence, and this corpus cannot tell which.

A related caution: the measures with the *tightest* spreads are import records
(0–11%) and whistleblowers (0–11%), and those are tight because nobody does them.
A narrow range near zero is a floor, not a consensus.

So a screening tool built on filings, court records, registries and archives
reconstructs the evidence base of **one report in five**, not one in two. Two in
three rest on something no database holds, and in half of those cases that
something is a former employee who agreed to talk.

That is a sharper answer than "automate it" or "you can't": it says **which
fifth**, and it names the barrier as access to people rather than access to data.

## What the control corpus changed

The Hindenburg-only findings survive as *Hindenburg* findings. As claims about the
practice, the ones about evidence mix break and the one about people holds.

| measure | Hindenburg (94) | Muddy Waters (55) | Night Market (23) | spread |
| --- | --- | --- | --- | --- |
| court / litigation | **62%** | 20% | 43% | 42pp |
| foreign/state registry | 52% | 51% | 13% | 39pp |
| paid terminal | 39% | **51%** | 13% | 38pp |
| social media | **68%** | 40% | 43% | 28pp |
| own field legwork | 30% | 36% | 13% | 23pp |
| original interviews | 60% | 53% | **70%** | 17pp |
| SEC filings | 70% | 67% | 61% | 9pp |
| expert network | 22% | 25% | 17% | 8pp |
| **needs a person at all** | **67%** | **71%** | **70%** | **4pp** |
| desk-reachable | 20% | 4% | 26% | 22pp |
| median words | 6,648 | 9,124 | 3,655 | |

Three traps had to be walked through to get there.

**The pooled rate reverses the ranking.** Counting all 142 Muddy Waters reports,
47% are desk-reachable against Hindenburg's 37% — Muddy Waters looks like the
easier corpus. It is not. 61% of its output is follow-ups, which cite almost
nothing and therefore score as "reachable from a desk". On first-look reports the
order flips to 4% against 20%. Same shape as the GRAS comeback rate and the CFR
interpretation genre: **a pooled average of two regimes.**

**Era is not the explanation.** Muddy Waters starts in 2010 and social-media
citation rose across the decade, so the gap could have been the calendar.
Restricting both to 2017–2025 moves social media by 8 points and SEC filings by 7
— real, but nowhere near the 30-to-50 point gaps, which survive intact.

**The probe list was written by reading one firm.** Night Market scored zero on
every original-sourcing probe, which read like a finding about a small desk shop.
It was a finding about the probes: that firm confirms claims through FOIA requests
and interviews companies at trade conferences, and there was no probe named for
either. Every widening since came from reading a firm that scored strangely —
which is the argument for a control corpus in one sentence.

## Corrections to the pilot

1. **The denominator was wrong.** 105 posts are 94 initial reports, 9 follow-ups
   and 2 admin notes. Every pilot percentage was computed against 105.
2. **The inventory had a hole.** Its eight probes missed court and litigation
   records entirely — at 66% of reports, the second-biggest evidence type in the
   corpus.
3. **The method got richer, not different.** Reading the pooled shares as "what
   short sellers do" hides that field legwork went 15% → 50% and paid terminals
   18% → 67% across three eras. Reports in 2023–25 do more of everything.

## Corrections found while building the control

These are bugs in figures this recipe had already published. All three ran in the
same direction — overstating how reachable the work is.

4. **The chart divided by 105 while the text said 94.** The denominator was
   answered in Q1 and then lived only as a sentence here, so
   `chart-independent-barrier.py` kept using every post. The 11 extra are
   rebuttals and house notes that cite nothing, so they counted as
   "desk-reachable": the hero read 41% and should have read **37%**. The
   definition is now code (`corpuslib.py`), not prose.
5. **`UCC` matched the "ucc" inside "success".** The registry probe had a bare
   acronym under a case-insensitive match. It scored 69 of 94 reports as having
   searched a state lien registry. The real figure is 7, and the probe as a whole
   fell from **73% to 20%**.
6. **The field-legwork probe was wrong in both directions.** Loose, it counted the
   firm calling itself "professional fraud researchers", a state regulator's
   investigators, and a line quoted from the target's own press release — 38%.
   Tight, it missed "our local investigator", "an investigator sent to the exact
   site" and "the Indian investigator in front of Next Gen's offices" — 28%. The
   12 disputed reports were read and ruled by hand, with the quote recorded as the
   evidence: **31%**.
7. **The probes had drifted into three copies.** One listed Morningstar and another
   did not, so the same corpus reported 39% and 41% for paid terminals in two
   places. Worse, the legwork probe named "Hindenburg" outright — run on any other
   firm it can only score zero, which would have manufactured the finding that
   Hindenburg does more fieldwork than anyone.

## Known before starting

* **Keyword-bucketing the citation strings failed once already**, leaving 60%
  unclassified and nearly producing confident wrong percentages. Frequency-ranking
  the raw labels was both honest and more informative — Instagram and LinkedIn
  were invisible to every bucket written in advance. Any classification here
  gets its unmatched share reported.
* **Q9 is the recipe's second half and it is blocked, not open.** Whether the
  recipe can be published without it depends on whether the decision in Q3 needs
  it, which is the terminator test.
