# cookbook

**Data analysis cookbook — reproducible recipes that turn public records into findings.**

Each recipe is one question, one method, one figure, and a written account of
what the answer cannot support. The script that produced the figure sits beside
it, and the limits are in the recipe rather than left for the reader to find.

Companion to the archives at [q3dresearch](https://github.com/q3dresearch),
which capture public records their publishers overwrite. This is the reasoning
built on those and on sources that keep their own history.

## Recipes

Fifteen, most recent first. Each links its own write-up.

- **[The register publishes its survivors and drops its dead. That is measurable anyway.](recipes/uk-company-survival/)** —
  Companies House never populates its dissolution column and every status it carries is one a
  live company holds, so the file cannot measure survival directly. Three dated snapshots that
  nothing links to make it measurable: a company is dead when it stops appearing. Two-thirds
  are gone within five years; 449,461 companies sit at forty addresses whose two-year survival
  is 37% against 56% elsewhere, and 8.9 points of that survive standardising for age.
- **[America is not running out of landfill room. Eight states are.](recipes/landfill-countdown/)** —
  permitted room went up 14.5bn to 14.8bn tons while a billion was buried, because new capacity
  was permitted where the clock was shortest. Eight states have a median site under twenty
  years and half the country's remaining room belongs to two companies. Half the evidence no
  longer exists at source: the register overwrites itself and the 2021 edition returns 404, so
  both workbooks are committed under the rule's own exception.
- **[Almost every apparent behaviour in a trial register turns out to be structure](recipes/clinical-trial-reporting/)** —
  twelve figures on ClinicalTrials.gov's 603,730 registered studies, walked in full three
  times. FDAAA 801 requires results within 12 months of primary completion, and the register
  obeys on exactly one day: the reporting hazard runs 0.23% a month, spikes to **4.6% in the
  deadline month — twenty times baseline — and collapses to 1.25% the month after, never
  recovering**. On day-precision dates it is sharper still, a 7.4-fold drop across one week,
  with 364 days the single most common lag. But **2008–2012 completions already spike 22.1x**,
  the same as 2017–2020, so the Final Rule neither created the wall nor sharpened it. Three-year
  reporting has been flat near 25% for fifteen years while one-year reporting tripled — the rule
  moved the reporters earlier and recruited nobody. **And the pooled quarter was measuring scope,
  not apathy**: crossed with the statute's own two tests, reporting is **67.1% for a regulated
  product with a US site against 3.4% outside both**, two independent multipliers, and inside
  university sponsors alone the same tests give 68.8% against 5.2%. Also here: a status field
  that is a two-year timer (UNKNOWN is 0.0% of 2026 registrations), a fifth of trials registered
  *after* they finished which predicts non-reporting 3–5x inside every sponsor class, terminated
  trials reported **more** than completed ones, sample size that reverses sign between industry
  and universities, and trials that look three times faster since 2008 and are slower.
- **[The Protein Data Bank is a record of what people chose to solve](recipes/pdb-deposition-choices/)** —
  nine figures on 260,089 solved protein structures, from about two hundred faceted queries. A
  sixth cites "To be published" and it is not neglect: structural-genomics consortia run
  74–86% against a 15.8% baseline, and depositor *size* explains nothing at rho +0.16. The
  cleanest exponential in the register is the only forecast that is wrong — cryo-EM growth
  fitted at **R² 0.99 over-predicts 2025 by 74%**, because the rate itself fell from +65% a
  year to +10%; six scenarios that respect the deceleration all cross in 2026–2028. The weight
  at which the field switches from crystallography to cryo-EM moved **1,530 → 315 → 133 kDa**
  in ten years. Above 1,000 kDa X-ray still *reads* better, 3.00 Å against 3.25 — from 701
  survivors against 5,040, which is the register showing its own survivorship with a count on
  each side. A hand-declared ligand classification is confirmed by a method that never had a
  crystallisation drop, but only once host size (rho +0.94) is conditioned on **and** the share
  is fitted in log-odds: a linear fit predicts negative shares and manufactures a null.
- **[What a presence-only marine register can and cannot tell you](recipes/ocean-sampling-effort/)** —
  fourteen figures on OBIS's 229 million marine records, in five parts. 27 of 27,168 grid cells
  hold a third of everything and the median cell is 45% one dataset. For plants and single
  cells, recorded depth is the *gear*: rho +0.97 against DNA-sequencing share. A within-bin
  composition ratio cancels that, and what survives is one biological cliff — seagrass gone by
  20 m, kelp by 30, while nothing that does not photosynthesise moves at all. A saturating
  accumulation fit under-predicts 16 classes out of 16, so species never run out, they get
  priced: 100 more sponge species cost 83,000 records and 100 more seabird species 63.5 million.
  And four of IUCN's five criteria are unreachable from occurrence data, with the fifth ruled
  out for 81% of Critically Endangered species.
- **[What America's hazardous waste register counts, and what it hides](recipes/waste-route-concentration/)** —
  eighteen figures in four parts. A record count measures filing granularity, not activity: one
  route filed 24× the rows on half the waste. A priority-chemical flag fell 94% → 13% while
  `D008` went 100% → 16% — lead did not stop being lead. The route with the fewest firms has the
  lowest Gini, and the flat 22-year inequality trend is flat only because firms leave the
  sample: pin the count and seven of eight routes concentrate. 95–97% of managed tonnage is
  liquid and 96% of it never leaves the plant. Price is not the lever — levels give rho −0.24,
  first differences −0.07 at p 0.49 — procurement is, at +8 points of recovery rate.
- **[Most of the FDA shortage list is not a shortage](recipes/drug-shortage-overlap/)** —
  137 of 196 substances are products being discontinued, not products in short supply.
  One reporting firm predicts an exit at 95% against 16% for two or more; nothing
  carrying the paediatric flag is being discontinued. And a shortage lasts about a
  year, not the two months a register's own resolved rows suggest, because all three
  registers delete resolutions after twelve months. Every join the archive supports
  was tried; supplier depth, enforcement records and severity classes predict nothing.
- **[Twenty-one papers in the whole of Hugging Face are adopted by someone who did not write them](recipes/hf-paper-adoption/)** —
  what the daily-papers feed predicts about adoption, what it does not, and four
  answers retracted by the promotion audit.
- **[One short report in five is reproducible from public data. The rest needed someone to talk](recipes/short-seller-method-corpus/)** —
  273 activist short reports across six firms, joined to daily prices. The biggest
  single evidence type is a conversation, and it was invisible to the first probe
  list because nobody thinks to grep for "told us". A report is worth about 3% on
  the day — unless the target is over $10B, where it is worth nothing.
- **[Three ways to measure an AI lab, and they disagree](recipes/openrouter-lab-share/)** —
  tokens, spend and model count rank the same firms differently, and the market
  grew 170× underneath all three.
- **[What FDA's GRAS inventories say about ingredients that do not make it](recipes/fda-gras-notices/)** —
  one filing in six is pulled by the company, not refused, and the rate is flat for 28 years —
  but 51% of pulled filings came back before 2010 against 29% after. The animal-food side of
  the same inventory clears 51% to human food's 79%, and eight firms filing on both sides
  clear 84% human and 57% animal: the programme, not the companies.
- **[When US regulation was last touched, and which of it already expired](recipes/cfr-staleness/)** —
  eight banking rules say outright that they have lapsed, and are still printed.
- **[Norway's aquaculture regulator processes modifications and holds new capacity](recipes/norway-aquaculture-queue/)** —
  what sits on the approval table forever, and why the mean hides it.
- **[Which grid you queue in matters more than what you are building](recipes/grid-queue-survival/)** —
  interconnection survival by region against technology.
- **[A GDPR fine tracks how many things went wrong, not which thing](recipes/gdpr-enforced-articles/)** —
  the article count is a severity proxy nobody documented as one.
- **[Five ways a public-records dataset lies to you, and one thing it says outright](recipes/foia-response-times/)** —
  a methods recipe: the failure modes matter more than the answer.
- **[The median dataset published on Kaggle is downloaded eight times](recipes/dataset-demand-shape/)** —
  across all 737,729 datasets ever published, 56% never pass ten downloads and
  69.5% are never opened in a notebook. The 412,935-dataset graveyard is not made
  by spammers — it is 161,320 people who published once and were ignored.

## How to read one

Every recipe folder is self-contained: the write-up, the script, the figure,
and any data the script cannot re-fetch. Copy the folder and
`python chart.py` reproduces the figure.

Palette constants are duplicated across recipes on purpose. The unit of use is
one folder, and a shared library would save a few dozen lines while breaking
that.

## What is not here

Candidates that have not been run. Those live in a private drafting workspace
until someone has checked the result, written it for a stranger, and looked at
what the data contains. **Publication here is a deliberate act on named files,
never a directory push.**

## Licence

Code MIT. Text and figures CC-BY-4.0. Captured third-party material stays under
whatever terms its original publisher set — each recipe names its sources.
