#!/usr/bin/env python3
"""Getting the target ticker out of a short report, three ways, and what each costs.

    python tickers.py

This is the part of the recipe meant to transfer. Anyone repeating this on a
different firm's site has to answer "which company is this report about?" before
anything else, and the answer is not one technique — it is three, with very
different yields depending on how the firm writes.

    exchange-prefixed   "NASDAQ: RIOT"      precise, and absent at some firms entirely
    parenthesised caps  "(CDXC)"            high recall, catches CEO and EBITDA too
    url or filename     /research/nq/       free, but only if the firm encodes it

The two text methods are checked against each other and against the slug, because
a ticker extractor that is never validated is how a price join gets built on
"(CEO)". Where two independent methods agree, the ticker is taken as confirmed;
the disagreement rate is the precision estimate and it is printed, not hidden.
"""
import re, sys, collections, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctrllib, corpuslib

EXCHANGES = (r"NASDAQ|NYSE|NYSEAMERICAN|NYSEARCA|AMEX|OTC|OTCMKTS|OTCQB|OTCQX|LSE|TSX|TSXV|"
             r"ASX|HKEX|SEHK|NSE|BSE|SGX|EPA|ETR|FRA|BIT|STO|CPH|OSL|AMS|SWX|JSE|KRX|TSE")
PREFIXED = re.compile(rf"\b(?:{EXCHANGES})\s*[:\-]\s*([A-Z]{{1,6}}(?:\.[A-Z]{{1,2}})?)\b")
PARENS = re.compile(r"\(([A-Z]{2,5})\)")

# Words that look like tickers in parentheses and are not. Built by reading the
# most frequent PARENS matches across all six corpora — every one of these
# outranked the actual ticker in at least one report.
NOT_TICKERS = {
    "CEO", "CFO", "COO", "CTO", "CIO", "EBITDA", "GAAP", "IPO", "SEC", "IRS", "FDA",
    "USD", "EUR", "GBP", "RMB", "CNY", "HKD", "AUD", "CAD", "JPY", "SGD", "INR",
    "LLC", "LLP", "LTD", "INC", "PLC", "GMBH", "SPAC", "REIT", "ETF", "IPR", "IP",
    "ROI", "ROE", "ROA", "EPS", "PE", "PS", "PB", "YOY", "QOQ", "CAGR", "TAM", "SAM",
    "SOM", "ARR", "MRR", "GMV", "AUM", "NAV", "NPL", "KPI", "SKU", "SAAS", "AI", "ML",
    "API", "SDK", "OEM", "ODM", "SOE", "VIE", "PRC", "USA", "UK", "EU", "UAE", "US",
    "AGM", "EGM", "BOD", "SPV", "MOU", "LOI", "NDA", "DOJ", "FBI", "FTC", "FCC", "EPA",
    "OSHA", "GDPR", "ESG", "CSR", "R&D", "RD", "QC", "QA", "HR", "IT", "PR", "TV",
    "DTC", "B2B", "B2C", "COGS", "SGA", "CAPEX", "OPEX", "FCF", "DCF", "WACC", "NPV",
    "IRR", "LBO", "MA", "PIPE", "ATM", "SPA", "APA", "ASC", "IFRS", "PCAOB", "AICPA",
}


def slug_ticker(doc, firm):
    """Whatever the URL or PDF filename encodes, if anything."""
    if firm == "muddywaters":
        m = re.search(r"/research/([^/]+)/[^/]", doc["url"])
        return m.group(1).upper() if m and len(m.group(1)) <= 6 else None
    if firm in ("jcapital", "sprucepoint"):
        s = re.sub(r"[-_]?html$", "", doc["slug"]).strip("-_")
        s = re.sub(r"^research-", "", s)
        head = s.split("-")[0]
        return head.upper() if 1 < len(head) <= 6 else None
    head = doc["slug"].split("-")[0]
    return head.upper() if 1 < len(head) <= 6 else None


def extract(text):
    """Candidate target ticker, by the only method that survived validation.

    Parenthesised caps was tried as an equal partner and abandoned. It matches 84-96%
    of reports at every firm, which reads like success until the matches are read:
    Carvana returns ABS, FOIA, LTV; Temenos returns DSO, APRA, FIS. It is an acronym
    detector. A blocklist was tried and is unwinnable — every report invents new ones.
    So it is demoted to a CONFIRMER: it can vouch for a symbol another method already
    proposed, and it can never propose one.

    Position does the rest. A report names its target in the headline and its
    comparables in the body, so the EARLIEST exchange-prefixed symbol is the target.
    """
    hits = [(m.start(), m.group(1)) for m in PREFIXED.finditer(text)]
    if not hits:
        return None, collections.Counter(), 0.0
    first_pos, first = hits[0]
    counts = collections.Counter(t for _, t in hits)
    # How early, as a share of the document — near 0 is the headline.
    return first, counts, first_pos / max(1, len(text))


def confirms(text, symbol):
    """Does the report also write the symbol in bare parentheses?"""
    return symbol is not None and bool(re.search(rf"\({re.escape(symbol)}\)", text))


def main():
    firms = [("Hindenburg", None), ("Night Market", "nightmarket"), ("Fuzzy Panda", "fuzzypanda"),
             ("Spruce Point", "sprucepoint"), ("Muddy Waters", "muddywaters"), ("J Capital", "jcapital")]
    print(f"  {'firm':<14}{'n':>4}{'prefixed':>10}{'+slug':>8}{'total':>8}"
          f"{'confirmed':>11}{'median pos':>12}")
    table, tot_n, tot_hit, tot_conf = {}, 0, 0, 0
    for label, key in firms:
        if key is None:
            docs = corpuslib.load("initial")
            get, fkey = corpuslib.body, "hindenburg"
        else:
            docs, _ = ctrllib.first_look(key)
            get, fkey = (lambda x: x["text"]), key
        n = len(docs)
        pre_hits = conf = slug_used = 0
        positions, found = [], {}
        for d in docs:
            text = get(d)
            sym, counts, pos = extract(text)
            if sym:
                pre_hits += 1
                positions.append(pos)
            else:
                sl = slug_ticker(d, fkey)
                # A slug is only a ticker if the report writes it as one.
                if sl and re.search(rf"\b{re.escape(sl)}\b", text):
                    sym, slug_used = sl, slug_used + 1
            if sym:
                found[d["slug"]] = sym
                if confirms(text, sym):
                    conf += 1
        med = sorted(positions)[len(positions) // 2] if positions else float("nan")
        print(f"  {label:<14}{n:>4}{pre_hits/n:>9.0%}{slug_used/n:>8.0%}{len(found)/n:>8.0%}"
              f"{conf/max(1,len(found)):>10.0%}{med:>11.1%}")
        table[label] = found
        tot_n += n
        tot_hit += len(found)
        tot_conf += conf

    print(f"\n  {tot_hit}/{tot_n} reports ({tot_hit/tot_n:.0%}) yield a target ticker.")
    print(f"  {tot_conf}/{tot_hit} of those ({tot_conf/tot_hit:.0%}) are independently confirmed "
          f"by the report also writing the symbol in parentheses.")
    out = Path(__file__).resolve().parents[1] / "raw" / "tickers.json"
    out.write_text(json.dumps(table, indent=1))
    print(f"  -> {out.relative_to(out.parents[2])}")
    return table


if __name__ == "__main__":
    main()
