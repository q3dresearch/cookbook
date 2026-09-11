#!/usr/bin/env python3
"""The two outcomes that matter: a business that cannot work, or a crime.

    python capture_jackpot.py

Every outcome measure earlier in this recipe scored a report by what the stock did.
That is the wrong scoreboard. A report that panics a stock down 40% on a rumour is
worth nothing; a report that proves the unit economics never worked, or that a crime
is happening, is worth something whether or not the trade paid. Five of the nineteen
corroborated targets BEAT the market between the report and the filing that conceded
the point. Under a P&L scoreboard those five are failures. They are not.

So two axes, both from SEC, both dated, both free, and both computed for the 140
control filers as well -- because "targets have thin margins" means nothing until
you know what an untargeted company's margin looks like.

**Broken unit economics** from XBRL, at the last annual figures FILED BEFORE the
report date -- not the last figures that exist. A short seller in March 2021 could
not read a 10-K filed in April, so neither can this script. Three measures, all
from one matched period so the ratios are comparable:

    gross margin        below zero: every sale loses money
    operating margin    below zero: sales do not cover the overhead
    operating cash flow below zero: customers are not funding the company

Tags drift. Nikola never files `Revenues` at all -- only
`RevenueFromContractWithCustomerExcludingAssessedTax`. Riot files `GrossProfit`
until 2016 and `CostOfRevenue` until 2021, same company, same filings. So each
measure is a list of aliases and the first that resolves for the chosen period
wins. A company with revenue tags but no revenue is recorded as pre-revenue,
because that IS the finding.

**Criminality** from EDGAR full-text search over the company's own filings. A Wells
notice, a subpoena, a grand jury, a DOJ or SEC investigation disclosed in an 8-K is
the company conceding, in a document it is legally obliged to file, that it is under
investigation. Dated, so it lands before or after the short report.

Two cautions that belong in any reading of the output. A subpoena is not a
conviction, and a negative margin can be a growth company burning deliberately --
Amazon ran negative operating margins for years. These are the hardest public dated
evidence available, not verdicts. And EDGAR full-text search only reaches back to
2001, which is fine here (earliest report in the corpus is 2017) but is a wall for
anyone extending this corpus backwards.
"""
import json, subprocess, sys, time, urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw"
UA = "q3dresearch cookbook research dl.eeee.nv@gmail.com"
PAUSE = 0.2

# Aliases run us-gaap first, then ifrs-full: a third of this corpus is Canadian or
# Chinese and files IFRS. Aurora Cannabis has NO us-gaap namespace at all, so a
# us-gaap-only script silently drops every foreign target -- and foreign targets are
# not a random subset, they are the ones short sellers like most.
REVENUE = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
           "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet",
           "SalesRevenueGoodsNet", "SalesRevenueServicesNet",
           "Revenue", "RevenueFromContractsWithCustomers",
           "PremiumsEarnedNet", "InterestAndDividendIncomeOperating"]
COST = ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold",
        "CostOfServices", "CostOfSales"]
GROSS = ["GrossProfit"]
OPINC = ["OperatingIncomeLoss", "ProfitLossFromOperatingActivities"]
OCF = ["NetCashProvidedByUsedInOperatingActivities",
       "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
       "CashFlowsFromUsedInOperatingActivities"]

# Every phrase here is something a company says about ITSELF, and only about itself.
# Two obvious candidates were tested and cut. "Department of Justice" returns 27 hits
# for AMETEK, all inside EX-10.x employment contracts and indemnification clauses --
# compliance boilerplate, not disclosure. "class action" is worse than imprecise: a
# securities class action FOLLOWS a stock drop, so counting it after a short report
# measures the report's own wake, not independent evidence of a crime. Restricting to
# primary forms does not help, because EDGAR attributes an exhibit to its parent form
# (27 hits all-forms, 27 hits 8-K/10-K/10-Q/20-F/6-K). The fix is the phrase, not the
# filter. With these four, AMETEK correctly scores zero.
CRIME = ['"Wells notice"', '"grand jury"', '"received a subpoena"',
         '"formal order of investigation"']


def get(url, raw=False):
    try:
        r = subprocess.run(["curl", "-sS", "--max-time", "45", "-A", UA, url],
                           capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        return None
    try:
        return json.loads(r.stdout.decode("utf-8", "replace"))
    except Exception:
        return None


def annual(facts, tags, before):
    """({tag, currency}, {period_end: value}) for the first alias that resolves.

    `before` filters on the FILED date, not the period end: a short seller could not
    read a 10-K that had not been filed yet, and a figure filed later is the RESTATED
    figure -- which in a fraud study is the one thing you must not quietly substitute
    for what was public at the time. Annual means a 300-400 day span, which admits
    52/53-week retail years without admitting quarters.

    Currency is whatever the filer used, not USD. Aurora Cannabis reports in CAD and a
    USD-only reader drops it entirely. Every measure built on this is a ratio, so the
    currency cancels; only the absolute revenue figure carries one, and it is labelled.
    """
    for tag in tags:
        units = facts.get(tag, {}).get("units", {})
        cur = next((u for u in ("USD", "CAD", "EUR", "GBP", "CNY", "HKD") if u in units),
                   next(iter(units), None))
        rows = units.get(cur, []) if cur else []
        out = {}
        for r in rows:
            if not r.get("end") or r.get("val") is None:
                continue
            if before and (r.get("filed") or "9999") > before:
                continue
            if r.get("start"):
                from datetime import date
                y0, m0, d0 = map(int, r["start"].split("-"))
                y1, m1, d1 = map(int, r["end"].split("-"))
                span = (date(y1, m1, d1) - date(y0, m0, d0)).days
                if not (300 <= span <= 400):
                    continue
            out[r["end"]] = r["val"]
        if out:
            return {"tag": tag, "currency": cur}, out
    return None, {}


def economics(facts, before):
    """Margins from ONE matched annual period, so the ratios are comparable."""
    rmeta, rev = annual(facts, REVENUE, before)
    if not rev:
        # Distinguish two very different misses. A company with a revenue tag it has
        # simply never filed an annual for is usually a recent SPAC -- Clover Health
        # was attacked weeks after listing, with no 10-K in existence. That is a fact
        # about the short seller's timing, not a gap in this script.
        if any(t in facts for t in REVENUE):
            return {"status": "no annual filed before report"}
        return {"status": "no revenue tag"}
    period = max(rev)
    if not rev[period]:
        return {"status": "pre-revenue", "as_of": period}
    out = {"status": "ok", "as_of": period, "revenue": rev[period],
           "revenue_tag": rmeta["tag"], "currency": rmeta["currency"]}

    gmeta, gross = annual(facts, GROSS, before)
    if period in gross:
        out["gross_margin"] = gross[period] / rev[period]
        out["gross_tag"] = gmeta["tag"]
    else:
        cmeta, cost = annual(facts, COST, before)
        if period in cost:
            out["gross_margin"] = (rev[period] - cost[period]) / rev[period]
            out["gross_tag"] = f"{rmeta['tag']} - {cmeta['tag']}"

    _, oi = annual(facts, OPINC, before)
    if period in oi:
        out["operating_margin"] = oi[period] / rev[period]

    _, cf = annual(facts, OCF, before)
    if period in cf:
        out["operating_cash_flow"] = cf[period]
        out["cash_burn_ratio"] = cf[period] / rev[period]
    return out


def enforcement(cik, before):
    """Enforcement language the company disclosed about itself, split at the report."""
    hits, failed = [], []
    for phrase in CRIME:
        time.sleep(PAUSE)
        url = (f"https://efts.sec.gov/LATEST/search-index"
               f"?q={urllib.parse.quote(phrase)}&ciks={cik:010d}")
        d = get(url)
        if d is None:
            failed.append(phrase)
            continue
        for h in d.get("hits", {}).get("hits", []):
            s = h.get("_source", {})
            if s.get("file_date"):
                hits.append({"phrase": phrase.strip('"'), "date": s["file_date"],
                             "form": s.get("file_type") or ""})
    hits.sort(key=lambda x: x["date"])
    return {"before": [h for h in hits if h["date"] <= before],
            "after": [h for h in hits if h["date"] > before],
            "failed_phrases": failed}


def one(cik, asof):
    time.sleep(PAUSE)
    cf = get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
    ns = (cf or {}).get("facts", {})
    facts = {**ns.get("ifrs-full", {}), **ns.get("us-gaap", {})}
    econ = economics(facts, asof) if facts else {"status": "no xbrl"}
    econ["standard"] = "us-gaap" if ns.get("us-gaap") else ("ifrs" if ns.get("ifrs-full") else None)
    return {"economics": econ, "enforcement": enforcement(cik, asof)}


def run(items, dest, label):
    done = json.loads(dest.read_text()) if dest.exists() else {}
    todo = [x for x in items if x[0] not in done]
    print(f"  {label}: {len(todo)} to read ({len(done)} cached)")
    for i, (key, cik, asof, extra) in enumerate(todo, 1):
        done[key] = {**extra, "cik": cik, "as_of": asof, **one(cik, asof)}
        if i % 10 == 0:
            print(f"    {label} {i}/{len(todo)}", flush=True)
            dest.write_text(json.dumps(done, indent=1))
    dest.write_text(json.dumps(done, indent=1))
    return done


def main():
    outcomes = json.loads((RAW / "target_outcomes.json").read_text())
    targets = [(s, v["cik"], v["date"], {"firm": v["firm"]})
               for s, v in sorted(outcomes.items())]
    t = run(targets, RAW / "jackpot_targets.json", "targets")

    ctrl = json.loads((RAW / "control_firms.json").read_text())
    rows = ctrl if isinstance(ctrl, list) else list(ctrl.values())
    # Controls have no report date; use the corpus median report date so the
    # "filed before" cutoff is the same kind of constraint for both groups.
    dates = sorted(v["date"] for v in outcomes.values())
    median = dates[len(dates) // 2]
    controls = [(str(r.get("cik")), int(r["cik"]), median, {"name": r.get("name", "")})
                for r in rows if r.get("cik")]
    c = run(controls, RAW / "jackpot_controls.json", "controls")

    for name, d in (("targets", t), ("controls", c)):
        ok = [v for v in d.values() if v["economics"].get("status") == "ok"]
        gm = [v["economics"]["gross_margin"] for v in ok if "gross_margin" in v["economics"]]
        print(f"  {name}: {len(d)} read, {len(ok)} with usable annuals, "
              f"{sum(1 for v in d.values() if v['economics'].get('status')=='pre-revenue')} pre-revenue, "
              f"{sum(1 for g in gm if g < 0)}/{len(gm)} negative gross margin, "
              f"{sum(1 for v in d.values() if v['enforcement']['after'])} enforcement after")


if __name__ == "__main__":
    main()
