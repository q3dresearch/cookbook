# cookbook

**Data analysis cookbook — reproducible recipes that turn public records into findings.**

Each recipe is one question, one method, one figure, and a written account of
what the answer cannot support. The script that produced the figure sits beside
it, and the limits are in the recipe rather than left for the reader to find.

Companion to the archives at [q3dresearch](https://github.com/q3dresearch),
which capture public records their publishers overwrite. This is the reasoning
built on those and on sources that keep their own history.

## Recipes

- **[The median dataset published on Kaggle is downloaded eight times](recipes/dataset-demand-shape/)** —
  across all 737,729 datasets ever published, 56% never pass ten downloads and
  69.5% are never opened in a notebook. Bigger datasets do worse, the
  organisation advantage turns out to be a head start rather than a badge, and
  the 412,935-dataset graveyard is not made by spammers — it is made by 161,320
  people who published once and were ignored.

- **[A register that both forgets and flickers, and the two look identical](recipes/publishers-destroy-history/)** —
  380 notifications vanished from Sweden's harvest register in two days. 318
  returned the next day and every one was a 2025 case; 62 did not and 61 were
  2021, aging out of a five-year window. The split is exact, and a single query
  to the register cannot tell you which is which.

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
