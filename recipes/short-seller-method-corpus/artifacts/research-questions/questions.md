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
| 5 | **Which evidence types travel together?** | `answered` · *revised* | **Length is breadth, inside a firm.** r runs +0.79 at Fuzzy Panda and +0.73 at Hindenburg down to +0.19 at Spruce Point. **Pooled across all six it reads +0.29, which is an artefact** — the firms sit at different points on both axes, so between-firm spread swamps the within-firm slope | `length-is-breadth` |
| 6 | **Do follow-ups differ?** | `answered` | **They are rhetoric, not research.** 3 citations across 9 follow-ups against 1,024 across 94 reports. Zero field legwork, zero registry work, and interviews fall 60% → 22% | `two-businesses` |
| 7 | **Is length breadth or padding?** | `answered` | **Breadth.** Hindenburg's shorter half cites a median 2 kinds of evidence, its longer half 7. The relationship flattens past about 15,000 words, where a report already cites most of the twelve kinds that exist | `length-is-breadth` |
| 8 | Are the cited sources free or paid? | `tested and failed` | **Third attempt, same failure.** 67% of 1,024 citations remain unclassifiable. 89% of the 820 labels appear exactly once | — *(no figure: a failed classifier gets a note, not a chart)* |
| 9 | **What does the target's stock do around the report?** | `answered` · *unblocked* | **The fall lands on the day and then stops.** Median target: −5.6% over the month before, **−3.7% on the report**, −0.3% over the month after. 74% fell on the day. But it is an order of magnitude firm-dependent: Hindenburg −8.2% with 87% falling, Spruce Point −0.6% with 60%. **Survivors only** — the price source keys on a company's current symbol, so bankrupt targets are absent | `event-window` |
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
| 20 | **Can the target ticker be extracted automatically?** | `answered` | **For 23% of reports, verifiably.** 56% yield an exchange-prefixed symbol; of those 41% are foreign listings no free registry covers, and of the US-listed remainder **30% are contradicted by SEC's own registry** — the first symbol in a report is often a peer in a comparison table. Kratos returned Parrot SA, Progyny returned FIGS, Inpixon returned Kodak | — *(no figure: the answer is a four-step funnel — 273 reports, 153 with a symbol, 90 checkable, 63 verified — which is a table and does not become clearer as a chart)* |
| 21 | **How much of the corpus can reach a price at all?** | `answered` | **85 of 273 reports, 31%.** A report needs a date (free), a ticker SEC recognises (a third), and a price series spanning the window. J Capital contributes zero — its targets are Chinese and HK-listed. Stooq, Yahoo, Nasdaq and WSJ all refuse; stockanalysis.com serves 20 years of daily OHLCV with no key | `event-window` |
| 22 | **Is the −5.6% pre-drift leakage, or target selection?** | `open` | Targets are already falling a month before publication. Two readings: short sellers pick stocks the market is souring on, or positions and rumours move price before the report lands. Distinguishing them needs the firm's own disclosed position dates, which none of them publish | — |
| 23 | **Why does Hindenburg move stocks 8× more than Spruce Point?** | `answered` · *mostly size* | **Spruce Point's targets are 8× bigger** — median $10.1B against Hindenburg's $1.26B, and 52% of them are above $10B against Hindenburg's 7%. A company over $10B does not move on a short report at all. But size does not fully explain it: inside the $300M–2B band Hindenburg runs −22.1% (n=10) against Spruce Point's −1.6% (n=4), on numbers too thin to settle | `size-and-impact` |
| 25 | **Does impact vary by target size?** | `answered` | **Sharply, and not monotonically — a correlation misses it entirely (r = −0.08).** Over $10B: −0.8% on the day, 53% fall, +1.0% a month later. $300M–2B: **−7.1%, 85% fall.** $2–10B: −5.3%, **95% fall**. Under $300M: only −1.9% on the day but **−17.3% a month later with 91% falling** — too illiquid to reprice at once | `size-and-impact` |
| 26 | **Can the short seller's own position be triangulated?** | `answered — no, and the bound is drawn` | **The signal is real and the attribution is not identified.** Volume runs 1.08× baseline a month out, 1.57× three days before, 1.88× on the eve, 6.18× on the day — something trades before the report exists. But excess volume over the pre-month is a median **8.0% of shares outstanding**, so the implied position is 8% at full attribution and 0.08% at 1%, and nothing observable pins that share down. 13F is long-only; FINRA and Nasdaq publish aggregate short interest bi-monthly and ~1 year deep; the UK moved to aggregate-only in 2025; Germany still names holders above 0.5% but almost no target here is German-listed | `pre-positioning` |
| 28 | **What makes evidence "good", and does it predict the short's performance?** | `defined, and suggestive` | **Define it as exclusivity, not accuracy** — corpuslib's barrier tiers rank evidence by what it costs an outsider to obtain, and that axis existed before any price data, so it was not fitted to the answer. A leaked document can be false and an SEC filing is nearly always true; the filing is simply already in the price. **Under $2B, reports resting on access-gated evidence fell 21.6% against 1.1% — a 21-point gap, p = 0.022 on 8 vs 11 reports.** Over $2B: nothing (p = 0.63). Four comparisons were run, so Bonferroni asks for 0.013 and this does not clear it. Three cuts point the same way and none is significant alone | `evidence-quality` |
| 29 | **Is exclusivity the same as accuracy?** | `open — and it is the harder question` | Everything in Q28 measures how hard evidence was to GET. Whether the claim turned out to be TRUE is a different axis nobody here has built: it needs each report's allegations tracked to a regulatory finding, restatement, delisting or refutation. That is the study this corpus makes possible and does not contain | — |
| 30 | **What happened to the companies they targeted?** | `answered` · *revised* | **A status check says 13 of 32 are gone from their symbol (41%). Chasing each one leaves 4.** Five are simply quoted elsewhere — AKG on the ASX, IRSA in London, PMET and WSP on the TSX, RINO on OTC. Three are renames of healthy companies and one, KDNY to NVS, was **acquired by Novartis at a premium**. Three cannot be found on any venue checked; one is in Chapter 11. Symbol persistence is not corporate survival, and the gap between 41% and 12% is the whole finding | `target-fate` |
| 31 | **Can a kill be told apart from a takeover?** | `route found, not yet built` | **SEC's submissions API carries 8-K ITEM codes per filing**, and two of them are the outcome: **Item 4.02** is a company declaring its own financials cannot be relied on, **Item 3.01** is a delisting notice. Tested on 18 Hindenburg targets, 4 filed one after the report — PACS delisted 22 days later, SGLY 20, PureCycle restated after 33, TGLS delisted after 137. `data.sec.gov/submissions/CIK##########.json`, free, and it keeps the history of companies that have since deregistered. A lower bound on corroboration, not a truth verdict: a delisting can be for late filing, and absence is not exoneration | — |
| 32 | **What kind of company attracts a short seller?** | `blocked — a control-group problem, not a data problem` | Describing targets cannot identify what distinguishes them. That needs the same measurements on companies the firms passed over, and the SEC registry carries exchange and nothing else — no sector, no financials, no accounting flags. Targets sit at a median $2.17B with quartiles $0.87B to $10.12B, which describes the sample and explains nothing | — |
| 33 | **Why do short sellers ignore OTC?** | `answered — descriptively` | **24% of US filers are OTC-listed and 1.9% of targets are.** A 0.1× lift, the strongest exchange signal in the data, against 1.3× for both Nasdaq and NYSE. The mechanism is not in this corpus: plausibly that OTC stock cannot be borrowed to short, or that too little is held for a report to pay for itself | — |
| 27 | **Do the firms differ in pre-report volume?** | `open` | Hindenburg and Night Market both run 1.92× baseline in the final five days; Spruce Point 1.22×, Muddy Waters 1.16×. That tracks price impact and target size together, so it cannot yet separate "this firm positions harder" from "this firm shorts smaller, thinner companies" | `pre-positioning` |
| 24 | **Does the horizon change the answer?** | `answered` | **It changes the effect size and not the reliability.** The median abnormal return wanders non-monotonically — −3.4% at a day, −6.7% at a month, −2.9% at two, −8.3% at a year — so whichever window an author picks becomes their headline. The share underperforming decays cleanly from 78% to 55%, and that is the statistic worth quoting. 30 trading days, used in the first version here, is not a calendar period and sits near a local trough | `horizon-sensitivity` |

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
| **A price join for most of the corpus** | 31% of reports reach a price. stockanalysis.com serves 20 years of daily OHLCV with no key, but it keys on a company's CURRENT symbol — bankrupt targets moved to OTC under new ones (ZYXI→ZYXIQ, NKLA→NKLAQ) and foreign delistings are absent entirely. The targets where the thesis landed hardest are the ones you cannot price |
| **A pooled correlation that means anything** | Length-versus-breadth is +0.19 to +0.79 within firms and +0.29 pooled. Any cross-firm statistic on this corpus needs computing per firm first — the firms differ enough on both axes to invert the within-firm picture |
| **A stable effect size** | Pick your horizon, pick your number: the median abnormal return runs −2.7% to −8.3% depending only on the window. Quote the hit rate instead — it decays monotonically from 78% at a day to 55% at a year |
| **Whether a target died or was bought** | A status check says 41% of confirmed targets left their symbol; five of those simply trade on another exchange and one was acquired at a premium. The real not-found count is 3 of 32. Separating a kill from a takeover needs merger and bankruptcy filings |
| **What attracts a short seller** | Every measurement here is on companies that WERE targeted. Naming what distinguishes them needs a matched sample of companies that were not, and the free registries carry exchange and nothing else |
| **The short seller's position** | Volume before the report is measurably elevated and cannot be attributed. The implied position spans 0.08% to 8% of the company depending on a parameter no public source reports. Kyle (1985) is the standard inversion and does not apply: it assumes the trade moves the price, and here the report does |
| **A reason the camps exist** | Fire-once and campaign firms are not distinguishable by method. P = 0.065 across six firms — suggestive, uncrossed. Cadence looks like a business decision, not a research one |
| **Anything about abandoned work** | Every corpus is published reports. Investigations dropped when the thesis collapsed leave no trace anywhere |

### Predict and prescribe

| # | question | status | answer | figure |
| --- | --- | --- | --- | --- |
| 34 | **What does a company that ends badly look like at the time of the report?** | `answered` | **Small and already flagged.** The 20 of 76 targets that later filed a restatement, delisting notice or bankruptcy had a median market cap of **$0.56B against $1.98B**, and 2.4 prior red-flag 8-Ks per 100 filings against 0.0. They also file LESS overall (669 vs 851 indexed), so it is not a longer-history artefact. Vindication is slow: median **441 days**, only 5 of 20 inside 90 | `forensic-arbitrage` |
| 35 | **What attracts a short seller's attention?** | `answered` · *revised — the null was on the wrong attributes* | **Not distress, and not the exchange — size, and as an avoidance.** Every prior-distress ratio against 140 controls is 1.0×, which stands. But the first revision measured the exchange a target trades on, which is a fact about borrowability rather than about the company, and promoted a clean null to an answer. On the regulator's own attributes: an **emerging growth company is attacked at 0.2×** (6/74 vs 43/123, p<0.0001) and a **non-accelerated filer at 0.4×** (12/74 vs 52/123, p=0.0001), both surviving Bonferroni at 19 comparisons. Short sellers skip small and young companies rather than hunting them | `two-jackpots` |
| 36 | **Why are they short — do they declare a preference?** | `answered` | **They do, in the text, and it is not mostly accounting.** Across 273 reports: undisclosed related party **29%**, paid promotion **26%**, accounting fraud 21%, auditor concerns 17%, executive history 15%, China-based fraud 13%, product does not work 12%. The two largest are about *who is behind the company*, not what the numbers say. 26% match no category, so the taxonomy has gaps | — |
| 37 | **Is there a rule an activist investor could act on?** | `answered — and it is the strongest result here` | **Two axes, both free and both knowable the morning a report drops.** A target under $2B that had ALREADY filed a restatement or delisting notice before the report went on to file another one **9 times out of 9**; a clean-history small cap, 3 of 16. Fisher exact **p = 0.0001**. And the market discounts exactly that cell — it falls **0.5% on the day against 2.7%** for the clean-history targets beside it. Six of the nine repeated the same filing type, but three escalated into a different one | `forensic-arbitrage` |
| 39 | **Do the corroborated and uncorroborated targets follow different paths?** | `answered` | **Yes, on a matched clock, and they never converge.** From the report: 1 month −8.6% vs +1.3%, 1 quarter −19.9% vs +3.1%, **1 year −33.4% vs +5.2%**, 2 years −63.1% vs −4.6%. The uncorroborated group is flat against the market for two years | `right-vs-wrong` |
| 40 | **Does the research METHOD predict which calls land?** | `answered — a null, and it points the wrong way` | **Almost nothing.** SEC filings 92% vs 90%, interviews 75% vs 69%, court records 58% vs 62%; kinds of evidence 5 vs 6 at p = 0.75. Where it does move it inverts: uncorroborated reports used **paid terminal data 71% against 33%**, ran **4,000 words longer** (p = 0.088) and did more field legwork (31% vs 17%). More expensive research, no better hit rate. Carried by 12 corroborated against 48, so this is a null rather than a measurement | `right-vs-wrong` |
| 41 | **Then what does separate them?** | `answered` | **The company, not the report.** 67% of corroborated targets had already filed a restatement or delisting notice before anyone wrote anything, against 17%. Market cap leans the same way — $0.90B vs $3.06B — at p = 0.267. Allegation type leans too: accounting-fraud claims were corroborated 8% of the time against 27% for those that were not | `right-vs-wrong` |
| 42 | **What does a convincing wrong chart look like?** | `answered — kept on purpose` | **`before-and-after`.** It has a fifteen-point gap between its medians, a plausible mechanism, and a caption that reads like a finding — and it is measuring a thirty-day window for an event that arrives at a median 454 days. The point cloud is random because it is random; the medians part because a few fast outcomes drag them. A chart that is obviously wrong teaches nothing. This is the kind that ships | `before-and-after` |
| 38 | **Is that rule just persistence dressed up?** | `partly, and the part that is not is the interesting part` | Six of nine filed the same kind of document again, which is mechanical. Three did not: COCP and LOOP went restatement → delisting, RIOT delisting → restatement. Distress changing form is not the same claim as distress repeating, and only the second is trivially predictable | `forensic-arbitrage` |
| 43 | **Why do the firms say they are short, in their own words?** | `answered` | **Wrongdoing, not bad business models.** First-person declarative sentences — "we believe", "our investigation found", "today we reveal" — recovered from 96% of reports, against `claims.py`'s 74%, because a firm stating its own position writes in a far more predictable register than one describing an allegation. **78% allege a crime or accounting manipulation; 5% rest on broken unit economics alone.** If the goal is proving a business cannot work, this corpus offers 13 worked examples, not 273 | — |
| 44 | **Do the firms differ in what they allege, not just how they work?** | `answered — the sharpest firm split found` | **Spruce Point is an accounting shop; Hindenburg is a fraud shop.** On accounting manipulation not called a crime: Spruce Point **69%**, Muddy Waters 43%, J Capital 30%, Fuzzy Panda 20%, Hindenburg **17%**, Night Market 9%. A wider separation than any evidence-type measurement produced, and visible only because the firms declare it themselves | — |
| 45 | **Can you screen for the crime using the numbers?** | `answered — a stable direction, not a significant one` | **No, and the sign is backwards.** Of 41 targets whose pre-report annuals can be read and whose three-year window has closed, those that went on to disclose a Wells notice, grand jury, subpoena or formal order of investigation had a median operating margin of **+17%**; those that did not, **−1%**. Visibly broken → investigated 2/21 = 10%; looked fine → 5/20 = 25%; Fisher p = 0.24. **Exposure had to be matched first** — counting "ever disclosed after" gave 11% vs 33% at p = 0.09, but broken-economics targets have a median report year of 2022 against 2020, so two years less time at risk. The sign holds at every window from 2 to 5 years; none of them is significant | — *(deliberately not drawn: a stable sign at p = 0.24 on 7 companies would look like a result, which is the `before-and-after` mistake)* |
| 46 | **Does the allegation predict whether the company concedes it?** | `answered — a null` | **No.** Reports alleging a crime were followed by a disclosed investigation 26% of the time; reports not alleging one, 28%. Reports alleging broken economics: 17%, *lower* than the 35% for those that did not — because those are different companies, not worse research. What a report claims tells you nothing about whether it is later conceded | — |
| 47 | **Which jackpot do they actually hit — the crime or the broken business model?** | `answered — and the answer changes once size is on an axis` | **The crime, at every size; the business model, not at all.** Pooled against 139 exposure-matched controls: investigation disclosed within three years **13/59 = 22% vs 6/108 = 6%, 4.0× at p = 0.0021**; economics composite 30/61 = 49% vs 19/58 = 33%, 1.5× at p = 0.093. **Split by SEC filer class — the regulator's own public-float bands, median $47m / $217m / $2.6bn — the control rate is FLAT on crime (6%, 10%, 5%) and COLLAPSES on economics (83%, 75%, 20%).** Being large does not get you investigated; being small is most of what "the business does not work" measures. Targets sit above the control line on crime at both ends (21% vs 6%, 28% vs 5%) and run together with it in every economics band, none significant. So the pooled 1.5× is the size mix, not the targeting. Targets even have **better gross margins** than random filers, +41% vs +28%, negative gross margins rarer (2% vs 6%) | `two-jackpots` |
| 48 | **Can public float give a continuous size axis for the control group?** | `tested and failed` | **No, and the failure is not random.** `dei:EntityPublicFloat` is the obvious continuous market-cap stand-in and single-concept requests are 2-4 KB, so it is cheap to try. But foreign private issuers on 20-F/40-F do not file it: 21 of 76 targets return 404, and requiring it leaves the control group with 25 usable companies and **zero enforcement events** — nothing left to compare against. The Canadian and Chinese filers it removes are exactly the ones this corpus is full of. SEC filer class is the same measurement banded by the regulator, with the coverage the raw field lacks | — *(the failure is the finding; `two-jackpots` uses filer class instead)* |

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
