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
- **[Four ways a national register lies about who is concentrated](recipes/waste-route-concentration/)** —
  the route with the fewest firms turns out to be the least concentrated of them all, and
  the Gini is flat for twenty-two years only because firms are leaving the sample. Pin the
  count and seven of eight routes concentrate. A record count measures how finely activity
  was written down, not how much of it there was: one route filed 24× the rows on half the
  waste. And one plant in Texas is 17% of every ton the country manages.
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
- **[Corn-ethanol additives for livestock, then novel protein for pets](recipes/animal-feed-ingredients/)** —
  a programme that changed subject and audience while keeping the same name.
- **[The same share of food ingredients get pulled. Far fewer come back](recipes/gras-withdrawals/)** —
  the withdrawal rate is flat for 28 years; what it means broke in 2010.
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
