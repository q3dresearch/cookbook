# cookbook

**Data analysis cookbook — reproducible recipes that turn public records into findings.**

Each recipe is one question, one method, one figure, and a written account of
what the answer cannot support. The script that produced the figure sits beside
it, and the limits are in the recipe rather than left for the reader to find.

Companion to the archives at [q3dresearch](https://github.com/q3dresearch),
which capture public records their publishers overwrite. This is the reasoning
built on those and on sources that keep their own history.

## Recipes

Ten, most recent first. Each links its own write-up.

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
