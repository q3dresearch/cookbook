#!/usr/bin/env python3
"""What each report ALLEGES, as opposed to what evidence it used to allege it.

    python claims.py

`corpuslib.probes` asks what a report looked AT. This asks what it says is wrong,
which turns out to be a different and more surprising picture: the two largest
categories are not accounting at all.

    undisclosed related party   29%      accounting fraud            21%
    paid promotion              26%      auditor concerns            17%

The first two are claims about WHO IS BEHIND a company — a hidden owner, a paid
promoter — rather than about its numbers. That matters for anyone trying to screen
for the next target, because neither is in any filing's metadata. It is the same wall
as the finding that two reports in three rest on a person who agreed to talk.

**The patterns were written by reading report titles and openings first**, and every
widening since has come from reading a firm that scored strangely — the same
discipline as the evidence probes, for the same reason. **26% of reports still match
no category**, which is reported here rather than hidden, because a classifier that
misses a quarter of its corpus cannot carry a confident percentage.
"""
import json, re, sys, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw"
sys.path.insert(0, str(HERE))
import corpuslib, ctrllib

CLAIM = {
    "accounting / fraud": r"accounting (fraud|irregularit|manipulat)|inflat(ed|ing) (revenue|sales|earnings)|"
                          r"cook(ed|ing) the books|fictitious (revenue|sales|customer)|round[- ]trip",
    "undisclosed related party": r"undisclosed related[- ]party|related[- ]party transaction|self[- ]dealing|"
                                 r"secretly (owned|controlled)",
    "product does not work": r"does not work|never worked|vaporware|smoke and mirrors|staged (demo|video)|"
                             r"faked? (a )?(demo|test|trial)|technology does not",
    "executive history": r"convicted|felon|prior (fraud|conviction)|barred by the SEC|"
                         r"history of (fraud|securities)|recidivis",
    "paid promotion": r"paid (stock )?promot|stock promot|pump[- ]and[- ]dump|promotional campaign",
    "overstated demand": r"overstate[d]? (demand|backlog|orders|pipeline)|phantom (orders|backlog)|"
                         r"non[- ]?binding (orders|LOI)",
    "regulatory exposure": r"FDA (warning|rejection)|clinical (failure|hold)|DOJ (probe|investigation)|"
                           r"SEC (subpoena|investigation)|criminal (probe|investigation)",
    "China-based fraud": r"SAIC filing|Chinese (subsidiar|entity|regulator)|VIE structure|"
                         r"onshore (revenue|entity)",
    "auditor concerns": r"auditor (resigned|dismissed|concerns)|going concern|material weakness|"
                        r"small(er)? audit firm|PCAOB (inspect|sanction)",
    "insider selling": r"insider(s)? (sold|selling|dumped)|unloaded (shares|stock)|Rule 10b5-1",
}
FIRMS = [("Hindenburg", None), ("Fuzzy Panda", "fuzzypanda"), ("Night Market", "nightmarket"),
         ("Muddy Waters", "muddywaters"), ("J Capital", "jcapital"), ("Spruce Point", "sprucepoint")]


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
            rows.append({"firm": label, "slug": d["slug"],
                         "claims": [c for c, p in CLAIM.items() if re.search(p, t, re.I)]})
    (RAW / "claim_types.json").write_text(json.dumps(rows, indent=1))
    c = collections.Counter(x for r in rows for x in r["claims"])
    print(f"  {len(rows)} first-look reports classified by allegation\n")
    for k, v in c.most_common():
        print(f"    {k:<28}{v:>4}  {v/len(rows):>5.0%}")
    none = sum(1 for r in rows if not r["claims"])
    print(f"\n  matching no category: {none} ({none/len(rows):.0%}) — the taxonomy's own gap, "
          f"reported rather than hidden")


if __name__ == "__main__":
    main()
