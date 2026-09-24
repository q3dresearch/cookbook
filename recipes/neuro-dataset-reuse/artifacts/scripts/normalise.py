#!/usr/bin/env python3
"""Turning four unusable free-text fields into countable ones, and saying what that buys.

    python3 normalise.py

Nine categorical fields exist on an OpenNeuro dataset and only three are usable as they stand:
modality (7 values), species (21, 93% human) and validator version (4). The rest are free text
with a long singleton tail -- `studyDomain` 537 distinct, `studyDesign` 337, `grantFunderName`
335, and `studyLongitudinal` **78** where the form plainly offers three.

Four of them are normalisable, because the tail is spelling and compounding rather than
genuine variety:

  studyLongitudinal  89% is already cross-sectional / longitudinal / other; the rest is
                     "single session", "repeated measures", "within-subject" and similar
  species            99% is human, mouse, rat, macaque or monkey -- and the tail contains
                     PHANTOMS ("meg dbs phantom", "synthetic fibre"), which are not a species
                     at all and get their own class rather than being dropped
  grantFunderName    the tail is multi-funder strings; substring matching to funder families
                     recovers most of it, and a dataset may legitimately match more than one
  studyDesign        "event-related", "event related" and "event-related design" are one thing

**Nothing is forced.** Anything a rule does not recognise stays `other`, and `main()` prints
the share each mapping recovers so the reader can see how much of the field was guessed at.
`studyDomain` is deliberately left alone: at 537 distinct values over 792 filled, with the most
common at 3%, there is no vocabulary underneath to recover.
"""
import collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fold                                                              # noqa: E402

DATA = os.path.join(HERE, "..", "data")

LONGITUDINAL = (
    (("longitudinal", "repeated measure", "repeated-measure", "follow-up", "followup",
      "multi-session", "multisession", "test-retest", "test retest", "pre-post"),
     "longitudinal"),
    (("cross-sectional", "cross sectional", "single session", "single-session",
      "one session", "single experiment", "single visit"), "cross-sectional"),
)
SPECIES = (
    (("phantom", "synthetic", "fibre", "fiber"), "phantom"),
    (("human", "homo sapiens", "participant"), "human"),
    (("mouse", "mice", "mus musculus", "b6/129"), "mouse"),
    (("rat", "rattus"), "rat"),
    (("macaque", "monkey", "primate", "rhesus", "marmoset"), "non-human primate"),
    (("pigeon", "canine", "dog", "sheep", "sus scrofa", "pig", "ferret", "zebra"),
     "other animal"),
)
FUNDER = (
    (("nihr", "mrc", "medical research council", "bbsrc", "epsrc", "ukri"),
     "UK councils"),
    (("nih", "national institutes of health", "nimh", "ninds", "nichd", "nia ", "nida",
      "niaaa", "nidcd", "nibib", "nci", "nhlbi", "national institute of",
      "national eye institute", "brain initiative"), "US NIH"),
    (("nsf", "national science foundation"), "US NSF"),
    (("darpa", "army research", "onr", "office of naval", "afosr", "navy", "dod",
      "department of defense"), "US defence"),
    (("erc", "european research council", "horizon", "h2020", "marie"), "EU / ERC"),
    (("wellcome",), "Wellcome"),
    (("dfg", "deutsche forschungsgemeinschaft", "max planck"), "Germany DFG"),
    (("nwo", "dutch research council"), "Netherlands NWO"),
    (("snsf", "swiss national science"), "Switzerland SNSF"),
    (("arc", "australian research council", "nhmrc"), "Australia"),
    (("jst", "jsps", "amed", "moonshot"), "Japan"),
    (("nsfc", "national natural science foundation of china", "cas "), "China NSFC"),
    (("cihr", "nserc", "brain canada"), "Canada"),
    (("anr", "inserm", "cnrs"), "France"),
)
DESIGN = (
    (("event-related", "event related", "rapid event"), "event-related"),
    (("block",), "block"),
    (("resting", "rest "), "resting-state"),
    (("within-subject", "within subject", "within-participant", "within participant",
      "repeated measure", "crossover", "cross-over"), "within-subject"),
    (("case-control", "case control", "between-subject", "between subject", "patient",
      "control group"), "between-subject"),
    (("observational", "naturalistic", "cohort"), "observational"),
)


# Short acronyms MUST match on a word boundary. Plain substring matching sent 117 datasets
# to Australia because "research" contains "arc", and would have sent the UK's NIHR to the
# US NIH because "nihr" contains "nih". Anything under five characters gets \b...\b.
_CACHE = {}


def _hit(key, text):
    if len(key.strip()) <= 4:
        pat = _CACHE.get(key)
        if pat is None:
            pat = _CACHE[key] = re.compile(r"\b" + re.escape(key.strip()) + r"\b")
        return bool(pat.search(text))
    return key in text


def _map(value, rules, default="other"):
    s = str(value or "").strip().lower()
    if not s:
        return None
    for keys, label in rules:
        if any(_hit(k, s) for k in keys):
            return label
    return default


def _funders(value):
    """A grant string may name several bodies; return every family it matches."""
    s = str(value or "").strip().lower()
    if not s:
        return None
    hits = [lab for keys, lab in FUNDER if any(_hit(k, s) for k in keys)]
    return hits or ["other"]


def rows():
    raw = json.load(open(os.path.join(DATA, "datasets.json")))["datasets"]
    md = {n["id"]: (n.get("metadata") or {}) for n in raw}
    out = []
    for r in fold.load()["rows"]:
        m = md.get(r["id"], {})
        out.append(dict(
            r,
            longitudinal=_map(m.get("studyLongitudinal"), LONGITUDINAL),
            species=_map(m.get("species"), SPECIES),
            design=_map(m.get("studyDesign"), DESIGN),
            funders=_funders(m.get("grantFunderName")),
            raw_long=m.get("studyLongitudinal"), raw_species=m.get("species"),
            raw_design=m.get("studyDesign"), raw_funder=m.get("grantFunderName")))
    return out


FIELDS = (("longitudinal", "raw_long"), ("species", "raw_species"),
          ("design", "raw_design"))


def coverage(rs):
    """How much of each field a mapping recovered, and how much stayed 'other'."""
    out = []
    for norm, rawk in FIELDS:
        filled = [r for r in rs if r[rawk]]
        distinct = len({str(r[rawk]).strip().lower() for r in filled})
        oth = sum(1 for r in filled if r[norm] == "other")
        out.append({"field": norm, "filled": len(filled), "distinct_before": distinct,
                    "distinct_after": len({r[norm] for r in filled}),
                    "other": oth, "recovered": 1 - oth / len(filled) if filled else 0})
    f = [r for r in rs if r["raw_funder"]]
    oth = sum(1 for r in f if r["funders"] == ["other"])
    out.append({"field": "funders", "filled": len(f),
                "distinct_before": len({str(r["raw_funder"]).strip().lower() for r in f}),
                "distinct_after": len({x for r in f for x in r["funders"]}),
                "other": oth, "recovered": 1 - oth / len(f) if f else 0})
    return out


def main():
    rs = rows()
    print(f"\n  {len(rs):,} datasets\n")
    print(f"  {'field':<14}{'filled':>8}{'before':>9}{'after':>7}{'other':>8}{'recovered':>11}")
    for c in coverage(rs):
        print(f"  {c['field']:<14}{c['filled']:>8}{c['distinct_before']:>9}"
              f"{c['distinct_after']:>7}{c['other']:>8}{c['recovered']:>11.0%}")
    for norm, _ in FIELDS:
        c = collections.Counter(r[norm] for r in rs if r[norm])
        print(f"\n  {norm}: " + "  ".join(f"{k} {v}" for k, v in c.most_common(8)))
    c = collections.Counter(x for r in rs for x in (r["funders"] or []))
    print(f"\n  funders: " + "  ".join(f"{k} {v}" for k, v in c.most_common(10)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
