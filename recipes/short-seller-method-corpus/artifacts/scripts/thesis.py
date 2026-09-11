#!/usr/bin/env python3
"""Where the report says, in its own words, why it is short.

    python thesis.py

`claims.py` asks what a report alleges, across ten categories. This asks a coarser and
more useful question: of the two things worth finding -- a crime, or a business that
mathematically cannot work -- which is this report claiming? And it pulls the sentence
where the firm says so, because a category is an assertion and a quote is evidence.

The split matters because the two demand completely different work. A crime is proved
by a document or a person: a court record, a filing, someone who was there. Broken unit
economics is proved by arithmetic on numbers the company already published -- which
means it is the half a careful outsider can actually reproduce without sources. Anyone
deciding where to spend effort needs to know which half of the corpus they are looking
at.

**Extraction is deliberately narrow.** A thesis sentence must be declarative and
first-person: the firm saying "we believe X", "our investigation found X", "X is a
fraud". Sentences describing what the company claims, what analysts think, or what a
lawsuit alleged are not the firm's thesis and are excluded. That narrowness costs
recall, and the miss rate is printed rather than hidden -- same discipline as
`claims.py` reporting its own 26% gap. A classifier that cannot say how often it
fails cannot carry a percentage.

Two known limits. Reports routinely allege both -- "they are losing money on every
car AND they lied about it" -- so the categories are not exclusive and are counted as
overlapping. And a firm's declared reason is what it chose to lead with, which is a
marketing decision as much as an analytical one; it is evidence of what the firm
thought would land, not necessarily of what it actually found.
"""
import json, re, sys, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw"
sys.path.insert(0, str(HERE))
import corpuslib, ctrllib

# The two jackpots, in the firms' own vocabulary.
CRIME = re.compile(
    r"\b(fraud|fraudulent|defraud|criminal|felon|convicted|indict(ed|ment)|"
    r"grand jury|subpoena|Wells notice|money launder|embezzl|bribery|FCPA|"
    r"forg(ed|ery)|fabricat(ed|ing) (documents|invoices|contracts)|"
    r"falsif(y|ied)|undisclosed related[- ]party|self[- ]dealing|"
    r"securities violation|misappropriat)", re.I)

# Aggressive accounting that the report does NOT call a crime. Equinix -- "manipulation
# of maintenance CapEx ... a $3 billion boost to AFFO" -- is the type case: a specific,
# quantified accounting allegation that never uses the word fraud, because the firm is
# alleging a choice that is arguably legal. Folding it into CRIME would overstate what
# was claimed; leaving it out lost 16 Hindenburg reports to "neither".
ACCOUNTING = re.compile(
    r"\b(manipulat(e|ed|ing|ion) (of )?(the )?(earnings|capex|revenue|reserves|margins|"
    r"depreciation|amortization)|non[- ]GAAP|adjusted (EBITDA|earnings) (excludes|omits|"
    r"masks)|channel stuffing|capitaliz(e|ed|ing) (what|costs|expenses)|"
    r"aggressive (accounting|revenue recognition|capitalization)|"
    r"understat(e|ed|ing) (costs|expenses|liabilities)|overstat(e|ed|ing) "
    r"(earnings|assets|margins|EBITDA)|off[- ]balance[- ]sheet|restat(e|ed|ement))", re.I)

BROKEN = re.compile(
    r"\b(unit economics|business model (is|does not|cannot|has never)|"
    r"loses money on (every|each)|negative (gross|unit) margin|"
    r"structurally unprofitab|never (been |)profitable|cannot be profitable|"
    r"cash burn|burning (through |)cash|going concern|"
    r"unsustainable|no path to profitab|dilut(ion|ive) (spiral|treadmill)|"
    r"funded by (equity|dilution)|insolven|zero terminal value)", re.I)

# Declarative and first-person. "The company believes" is not the firm's thesis;
# "we believe" is. "Plaintiffs alleged" is someone else's claim being reported.
SAYS = re.compile(
    r"(?:^|(?<=[.!?]\s))((?:[^.!?]{0,400}?)\b(?:we (?:believe|found|conclude|allege|"
    r"estimate|think|are short|have uncovered|uncovered|document|show)|"
    r"our (?:investigation|research|analysis|review|findings?) (?:found|shows?|"
    r"reveal(?:s|ed)?|indicates?|concludes?)|"
    r"today we (?:reveal|expose|publish|report))\b(?:[^.!?]{0,400}))[.!?]", re.I)

FIRMS = [("Hindenburg", None), ("Fuzzy Panda", "fuzzypanda"), ("Night Market", "nightmarket"),
         ("Muddy Waters", "muddywaters"), ("J Capital", "jcapital"), ("Spruce Point", "sprucepoint")]


# Every one of these firms closes with the same legal disclaimer, and it contains the
# words "we believe" -- so it extracts as a thesis and buries the real one. It is not
# caught by the shared-boilerplate stripper because it is not shared ACROSS firms, only
# within each. Match it by content, not position.
DISCLAIMER = re.compile(
    r"to the best of our (ability|knowledge)|obtained from public sources we believe to be|"
    r"accurate and reliable|should not be (taken |)as investment advice|"
    r"we (are|may be) (short|long)[^.]{0,40}(and (stand|may) to (realize|profit))", re.I)


def theses(text, limit=6):
    """First-person declarative sentences, longest first -- short ones are throat-clearing."""
    out = []
    for m in SAYS.finditer(text):
        s = " ".join(m.group(1).split())
        if 40 <= len(s) <= 400 and not DISCLAIMER.search(s):
            out.append(s)
    out.sort(key=len, reverse=True)
    return out[:limit]


def main():
    rows = []
    for label, key in FIRMS:
        if key is None:
            docs, get = corpuslib.load("initial"), corpuslib.body
        else:
            docs, _ = ctrllib.first_look(key)
            get = lambda d: d["text"]
        for d in docs:
            t = get(d)
            quotes = theses(t)
            joined = " ".join(quotes)
            rows.append({
                "firm": label, "slug": d["slug"],
                # Category from the whole report; the quote is the receipt, not the test.
                "crime": bool(CRIME.search(t)),
                "accounting": bool(ACCOUNTING.search(t)),
                "broken": bool(BROKEN.search(t)),
                # Did the firm say it in the first person, or does it only show up
                # in the body? A declared thesis is a stronger signal than a mention.
                "declared_crime": bool(CRIME.search(joined)),
                "declared_broken": bool(BROKEN.search(joined)),
                "quotes": quotes,
            })
    (RAW / "thesis.json").write_text(json.dumps(rows, indent=1))

    n = len(rows)
    noquote = sum(1 for r in rows if not r["quotes"])
    print(f"  {n} first-look reports, three overlapping axes\n")
    for k, lab in (("crime", "alleges a crime"), ("accounting", "alleges accounting manipulation"),
                   ("broken", "alleges broken unit economics")):
        v = sum(r[k] for r in rows)
        print(f"    {lab:<36}{v:>4}  {v/n:>5.0%}")
    jack = sum(1 for r in rows if r["crime"] or r["accounting"])
    only_b = sum(1 for r in rows if r["broken"] and not (r["crime"] or r["accounting"]))
    neither = sum(1 for r in rows if not (r["crime"] or r["accounting"] or r["broken"]))
    print(f"\n    crime OR accounting (the provable-wrongdoing half)  {jack:>4}  {jack/n:>5.0%}")
    print(f"    broken economics and nothing else                  {only_b:>4}  {only_b/n:>5.0%}")
    print(f"    none of the three                                  {neither:>4}  {neither/n:>5.0%}")
    print(f"\n    no first-person thesis sentence extracted: {noquote} ({noquote/n:.0%}) "
          f"-- the extractor's own gap")
    print("\n  by firm (share alleging a crime / broken economics):")
    for label, _ in FIRMS:
        f = [r for r in rows if r["firm"] == label]
        if not f:
            continue
        print(f"    {label:<14}{len(f):>4} reports   crime {sum(r['crime'] for r in f)/len(f):>4.0%}"
              f"   accounting {sum(r['accounting'] for r in f)/len(f):>4.0%}"
              f"   broken {sum(r['broken'] for r in f)/len(f):>4.0%}")
    print("\n  sample declared theses:")
    for r in rows:
        if r["quotes"] and (r["declared_crime"] or r["declared_broken"]):
            tag = "crime" if r["declared_crime"] else "broken"
            print(f"    [{tag}] {r['firm']} / {r['slug'][:40]}")
            print(f"       \"{r['quotes'][0][:180]}\"")
            if sum(1 for x in rows[:rows.index(r) + 1] if x["quotes"]) >= 4:
                break


if __name__ == "__main__":
    main()
