#!/usr/bin/env python3
"""How many papers were actually adopted by someone who did not write them.

    python adoption.py

An `arxiv:` tag on a Hugging Face model is supposed to say "this model implements
that paper". Counted naively it says almost nothing, and this script is the chain of
filters that gets from the naive number to a defensible one. Every step throws work
away, and the size of each step is the finding.

    1,000 models in the top-downloads listing
      522 carry at least one arxiv tag
      430 distinct papers referenced
       87 referenced by MORE THAN ONE org          <- 80% are one org citing itself
       29 still multi-org once derivative models are removed
       ~20 after same-company aliases and template boilerplate

**Step 1, the denominator.** Counting models rewards release cadence: YaRN reads 34
models, of which 32 are Qwen. Counting distinct orgs asks how many independent
parties chose the idea, which is the question.

**Step 2, derivatives.** 251 of the 1,000 models declare `base_model:` pointing at
ANOTHER org's model — 242 quantizations, 142 finetunes. A quantized re-upload
inherits the original's whole model card, arxiv tags included, so it votes again for
every paper the original cited. One user republishing Google's Gemma models carries
Google's entire benchmark citation list with it, and that single account is
responsible for roughly thirty of the 87 "cross-org" papers. `base_model:` states
the relation outright, which is far better than inferring it: an earlier attempt
compared tag sets by Jaccard similarity and could not separate "same model
redistributed" from "same architecture, different language" — every wav2vec2
language finetune looked like a copy of every other.

**Step 3, and this one is not automated.** Same company under two namespaces
(`amazon`/`autogluon`, `google`/`google-t5`, `CompVis`/`stable-diffusion-v1-5`) and
template boilerplate still survive step 2. `1910.09700`, *Quantifying the Carbon
Emissions of Machine Learning*, reaches 12 orgs because it is the emissions field of
Hugging Face's model-card template — it is not an implementation of anything, and it
tops every ranking until it is named and removed. These are listed as hand-ruled
exclusions rather than guessed at, the same way the short-seller corpus hand-ruled
its disputed legwork cases.

**What absence does not prove.** 611 models declare no `base_model:` at all, so step 2
removes derivatives that say they are derivatives and keeps any that stay quiet.
The 29 is therefore an upper bound on independent adoption, not a count of it.

**And the population is a popularity filter.** This is the top 1,000 by downloads:
adoption among already-popular models, not across the ecosystem. Four other model
listings were capturing no tags at all until 2026-09-12; once they accrue, `newest`
and `trending` are the ones that would show a technique winning first.

**Every capture is run, not just the newest, because one capture's answer is not
stable.** The survivor count reads 25 on 2026-08-31 and 20 on 2026-09-08, and only 18
papers clear the bar in all eleven. The reason is mechanical: **16% of model ids were
not present in all eleven captures**, and every unstable paper sits at exactly two
orgs, so one model leaving the top 1,000 drops it to one. GPT-3, RoPE, The Pile and
Florence-2 all flip inside nine days. A number computed from a single capture of a
churning listing should not be quoted, so this reports the stable core and the
fragile band separately.
"""
import collections
import glob
import gzip
import json
from pathlib import Path

import paperlib as P

HF = P.ARCHIVE  # resolved by paperlib: $WSS_HUGGING_FACE or artifacts/data/

# Hand-ruled, with the reason, because no rule in the data separates these.
ALIASES = {
    "autogluon": "amazon", "google-t5": "google", "google-bert": "google",
    "stable-diffusion-v1-5": "CompVis", "stabilityai": "CompVis",
    "pysentimiento": "finiteautomata",
}
BOILERPLATE = {
    "1910.09700": "HF model-card template's carbon-emissions field",
    "2205.05198": "same, older template revision",
}


def latest(source="hf.models.top-downloads"):
    files = sorted(glob.glob(str(HF / "raw" / source / "*" / "*" / "*")))
    if not files:
        raise SystemExit(f"no captures for {source}")
    p = files[-1]
    return p, json.load((gzip.open if p.endswith(".gz") else open)(p, "rt"))


def papers_of(model):
    return {t.split(":", 1)[1] for t in model.get("tags", []) if t.startswith("arxiv:")}


def foreign_base(model):
    """The org this model is derived FROM, if that org is not its own."""
    me = model["id"].split("/")[0]
    for t in model.get("tags", []):
        if not t.startswith("base_model:"):
            continue
        ref = t.split(":")[-1]
        if "/" in ref and ref.split("/")[0] != me:
            return ref.split("/")[0]
    return None


def captures(source="hf.models.top-downloads"):
    for p in sorted(glob.glob(str(HF / "raw" / source / "*" / "*" / "*"))):
        yield p, json.load((gzip.open if p.endswith(".gz") else open)(p, "rt"))


def score(models):
    """One capture -> (papers by model count, orgs seen, non-derivative orgs, n derived)."""
    by_model, all_orgs, own_orgs, derived = collections.Counter(), \
        collections.defaultdict(set), collections.defaultdict(set), 0
    for m in models:
        org = m["id"].split("/")[0]
        src = foreign_base(m)
        derived += bool(src)
        for a in papers_of(m):
            by_model[a] += 1
            all_orgs[a].add(org)
            if not src:
                own_orgs[a].add(ALIASES.get(org, org))
    return by_model, all_orgs, own_orgs, derived


def main():
    titles = json.loads((HF / "examples" / "paper-titles.json").read_text())
    runs = [(Path(p).name[:8], *score(ms)) for p, ms in captures()]
    if not runs:
        raise SystemExit("no captures")
    print(f"  {len(runs)} captures, {runs[0][0]} to {runs[-1][0]}\n")

    survivors = [{a for a in own if len(own[a]) > 1 and a not in BOILERPLATE}
                 for _, _, _, own, _ in runs]
    core = set.intersection(*survivors)
    ever = set.union(*survivors)
    print(f"  {'capture':<10}{'papers':>8}{'>1 org':>8}{'derived':>9}{'survivors':>11}")
    for (d, bym, allo, own, der), s in zip(runs, survivors):
        print(f"  {d:<10}{len(bym):>8}{sum(1 for a in allo if len(allo[a])>1):>8}{der:>9}{len(s):>11}")
    print(f"\n  stable core (in every capture): {len(core)}"
          f"   ever a survivor: {len(ever)}"
          f"   stability {len(core)/len(ever):.0%}")
    print(f"  fragile band (some captures only): {len(ever - core)} — each sits at exactly")
    print( "  two orgs, so one model leaving the top 1,000 drops it to one.\n")

    path, models = list(captures())[-1]
    by_model, all_orgs, own_orgs, derived = runs[-1][1], runs[-1][2], runs[-1][3], runs[-1][4]
    tagged = sum(1 for m in models if papers_of(m))
    multi_all = [a for a in all_orgs if len(all_orgs[a]) > 1]
    multi_own = [a for a in own_orgs if len(own_orgs[a]) > 1]

    print(f"  newest capture in detail:")
    print(f"  {len(models):>5}  models in the listing")
    print(f"  {tagged:>5}  carry an arxiv tag ({tagged/len(models):.0%})")
    print(f"  {len(by_model):>5}  distinct papers referenced")
    print(f"  {len(multi_all):>5}  referenced by more than one org "
          f"({len(multi_all)/len(by_model):.0%} — the rest are one org citing itself)")
    print(f"  {derived:>5}  models derive from another org's model (excluded next)")
    print(f"  {len(multi_own):>5}  still multi-org once derivatives and aliases are removed")
    print(f"  {len(core):>5}  survive in EVERY capture (the number worth quoting)\n")

    for a in BOILERPLATE:
        if a in all_orgs:
            print(f"  excluded: {a} on {len(all_orgs[a])} orgs — {BOILERPLATE[a]}")

    print(f"\n  stable cross-organisation adoption ({len(core)} papers):")
    for a in sorted(core, key=lambda x: (-len(own_orgs.get(x, ())), x)):
        t = (titles.get(a) or "— uncached")[:50]
        print(f"   {len(own_orgs.get(a, ())):>1}o {by_model.get(a,0):>3}m  {a:<11}{t:<52}"
              f"{','.join(sorted(own_orgs.get(a, ())))[:34]}")
    print(f"\n  fragile band ({len(ever - core)} papers, in some captures only):")
    for a in sorted(ever - core):
        print(f"        {a:<11}{(titles.get(a) or '— uncached')[:50]}")


if __name__ == "__main__":
    main()
