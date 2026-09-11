#!/usr/bin/env python3
"""Check every extracted ticker against SEC's registry, by company NAME.

    python validate_tickers.py

Hand-ruling thirteen extractions put the "first exchange-prefixed symbol" method at
10/13, and all three failures were the same thing: the report opened with a peer
comparison table, and the first symbol in it belonged to a comparable. Kratos
returned Parrot SA, Progyny returned FIGS, Cielo returned Chesapeake. Picking the
most FREQUENT symbol instead changes nothing — the peer is named as often as the
target.

What does catch it is asking a registry who the symbol belongs to. SEC publishes
ticker -> company -> exchange for 10,407 issuers. If the report is filed under a
slug saying "kratos-defense" and the symbol resolves to "Parrot SA", the extraction
is wrong and can be said so automatically.

The limit is the registry's own: SEC lists US issuers. A Chinese company on HKEX or
an Australian miner is simply absent, and absence here is NOT evidence the ticker is
wrong. Those are reported as unverifiable rather than failed, because the difference
matters to anyone repeating this on a firm that shorts outside the US.
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEC = HERE.parent / "raw" / "sec" / "company_tickers_exchange.json"
sys.path.insert(0, str(HERE))
import ctrllib, corpuslib, tickers

STOP = {"inc", "corp", "corporation", "co", "company", "ltd", "limited", "plc", "llc",
        "holdings", "holding", "group", "the", "sa", "nv", "ag", "se", "spa", "ab",
        "technologies", "technology", "international", "global", "and", "of", "trust",
        "enterprises", "industries", "systems", "solutions", "partners", "capital"}


def words(s):
    return {w for w in re.split(r"[^a-z0-9]+", s.lower()) if w and w not in STOP and len(w) > 2}


def registry():
    d = json.loads(SEC.read_text())
    idx = {}
    for cik, name, tick, exch in d["data"]:
        if tick:
            idx[tick.upper()] = {"name": name, "exchange": exch, "cik": cik}
    return idx


def main():
    reg = registry()
    print(f"  SEC registry: {len(reg):,} tickers\n")
    firms = [("Hindenburg", None), ("Night Market", "nightmarket"), ("Fuzzy Panda", "fuzzypanda"),
             ("Spruce Point", "sprucepoint"), ("Muddy Waters", "muddywaters"), ("J Capital", "jcapital")]
    print(f"  {'firm':<14}{'ticker':>8}{'in SEC':>8}{'name agrees':>13}{'contradicts':>13}{'not listed':>12}")
    tot = dict(n=0, sym=0, insec=0, agree=0, bad=0, absent=0)
    bad_examples = []
    for label, key in firms:
        if key is None:
            docs, get = corpuslib.load("initial"), corpuslib.body
        else:
            docs, _ = ctrllib.first_look(key)
            get = lambda x: x["text"]
        n = sym = insec = agree = bad = absent = 0
        for d in docs:
            n += 1
            s, _, _ = tickers.extract(get(d))
            if not s:
                continue
            sym += 1
            base = s.split(".")[0]
            hit = reg.get(s) or reg.get(base)
            if not hit:
                absent += 1
                continue
            insec += 1
            # Two ways the registry can agree, and both are needed.
            #
            # By name: the slug and the registry name share a distinctive word.
            # By symbol: the slug IS the ticker. Night Market files BYSI under
            # "bysi", and a name check alone called that a contradiction against
            # "BeyondSpring Inc." — the extraction was right and the test was wrong.
            #
            # What neither catches is a rename. Marathon Patent Group is "MARA
            # Holdings" in today's registry, so a 2021 report reads as contradicted.
            # The registry holds the CURRENT name; reports hold the name at the time.
            slug_clean = re.sub(r"^research-", "", d["slug"])
            slug_w = words(slug_clean)
            head = slug_clean.split("-")[0].upper()
            if words(hit["name"]) & slug_w or head == s or head == base:
                agree += 1
            else:
                bad += 1
                if len(bad_examples) < 8:
                    bad_examples.append((label, d["slug"][:30], s, hit["name"][:28]))
        for k, v in zip(("n", "sym", "insec", "agree", "bad", "absent"), (n, sym, insec, agree, bad, absent)):
            tot[k] += v
        print(f"  {label:<14}{sym:>8}{insec:>8}{agree:>13}{bad:>13}{absent:>12}")
    print(f"  {'ALL':<14}{tot['sym']:>8}{tot['insec']:>8}{tot['agree']:>13}{tot['bad']:>13}{tot['absent']:>12}")

    checkable = tot["agree"] + tot["bad"]
    print(f"\n  Of {tot['sym']} extracted symbols, {tot['insec']} are US-listed and checkable.")
    print(f"  {tot['agree']}/{checkable} = {tot['agree']/checkable:.0%} name-match their report; "
          f"{tot['bad']} contradict it outright.")
    print(f"  {tot['absent']} are not in SEC at all — foreign listings, not errors.")
    print("\n  contradictions the registry catches that a human would have to:")
    for lab, slug, s, name in bad_examples:
        print(f"    {lab[:12]:<12} {s:<7} resolves to {name:<30} but the report is {slug}")


if __name__ == "__main__":
    main()
