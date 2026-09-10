"""Shared loading/derivation for the CFR staleness charts."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
RECIPE = os.path.dirname(os.path.dirname(HERE))          # recipes/cfr-staleness
CHARTS = os.path.join(RECIPE, "artifacts", "charts")
# This recipe commits no data. capture.py writes into a work directory and every
# other script reads from the same one: set CFR_WORK, or accept ./work in the
# current directory. Nothing here reaches outside the recipe except that dir.
WORK = os.environ.get("CFR_WORK") or os.path.join(os.getcwd(), "work")
DERIVED = os.path.join(WORK, "derived")
RAW = os.path.join(WORK, "raw")
os.makedirs(DERIVED, exist_ok=True)
import csv, datetime as dt, re, statistics
from collections import defaultdict

TODAY = dt.date(2026, 9, 6)
MONTHS = {m: i for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}
CITE = re.compile(r"(\d+)\s+FR\s+[\d,]+(?:\s*,\s*[\d,]+)*\s*,?\s*"
                  r"([A-Z][a-z]{2})[a-z]*\.?\s+(\d{1,2}),\s+(\d{4})")
SHORT = {
    "Comptroller of the Currency, Department of the Treasury": "OCC",
    "Federal Reserve System": "Federal Reserve",
    "Federal Deposit Insurance Corporation": "FDIC",
    "Export-Import Bank of the United States": "Export-Import Bank",
    "Farm Credit Administration": "Farm Credit Admin",
    "National Credit Union Administration": "NCUA",
    "Consumer Financial Protection Bureau": "CFPB",
    "Federal Financial Institutions Examination Council": "FFIEC",
    "Federal Housing Finance Agency": "FHFA",
    "Financial Stability Oversight Council": "FSOC",
    "Farm Credit System Insurance Corporation": "Farm Credit Ins Corp",
    "Department of the Treasury": "Treasury",
    "Office of Financial Research, Department of the Treasury": "Office of Financial Research",
}


def dates(s):
    out = set()
    for _, mon, day, yr in CITE.findall(s or ""):
        m = MONTHS.get(mon.lower())
        if not m:
            continue
        y = int(yr)
        if 1930 <= y <= 2027:
            try:
                out.add(dt.date(y, m, int(day)))
            except ValueError:
                pass
    return sorted(out)


def load(path=os.path.join(DERIVED, "cfr-title12-sections.csv"), own_only=True):
    rows = list(csv.DictReader(open(path)))
    for r in rows:
        r["reserved"] = r["reserved"] == "1"
        r["d"] = dates(r["source_note"])
        r["agency"] = SHORT.get(r["agency"], r["agency"])
        r["age"] = ((TODAY - r["d"][-1]).days / 365.25) if r["d"] else None
        r["born"] = r["d"][0].year if r["d"] else None
        r["n_amend"] = max(len(r["d"]) - 1, 0)
    live = [r for r in rows if not r["reserved"] and r["d"]]
    if own_only:
        live = [r for r in live if r["cite_level"] == "section"]
    return rows, live


def part_activity(live):
    """Median age of the *other* sections in each part -> neighbourhood signal.

    Genuinely leave-one-out, keyed by (part, section). The previous version said
    "the other sections" and then included the section itself, which drags every
    point toward the diagonal and shrinks precisely the two populations the
    quadrant exists to find: it understated SETTLED by 45 sections (178 vs 223).
    It also took a[len(a)//2], the upper-middle element, which is not the median
    of an even-length list.

    A part holding one dated section has no neighbourhood at all. Those get no
    entry here rather than a self-comparison that would plot on the diagonal and
    read as a measurement.
    """
    by = defaultdict(list)
    for r in live:
        by[r["part"]].append(r["age"])
    med = {}
    for r in live:
        peers = [a for a in by[r["part"]]]
        peers.remove(r["age"])          # drops one instance, not every tie
        if peers:
            med[(r["part"], r["section"])] = statistics.median(peers)
    return med, by


# Functional category, inferred from the section heading. This is our own
# construct, not a publisher field: ordered rules, first match wins.
CATS = [
    ("Interpretation", None),                       # taken from subjgrp/subpart
    ("Definitions & scope", r"\bdefinition|\bmeaning|\bpurpose\b|\bscope\b|"
                            r"\bauthority\b|\bapplicabilit|\bcoverage\b|"
                            r"\bconstruction of|\bterminology"),
    ("Capital & risk", r"\bcapital\b|risk-weight|risk weight|\bleverage\b|"
                       r"\bliquid\b|\bliquidity\b|liquid asset|\bbuffer\b|"
                       r"\bsolvenc|net worth|\breserves?\b|stress test|"
                       r"\bexposure|\bmaturity\b|\boutflow|\binflow"),
    ("Application & licensing", r"\bapplicat|\bapproval|\bcharter|\bpermit|"
                                r"\blicens|\bmembership\b|\bregistrat|"
                                r"\bqualificat|\bchange in control|\bmerger|"
                                r"\bacquisit|\bnotice of intent"),
    ("Enforcement & penalties", r"\bpenalt|\benforcement|\bviolat|\bsanction|"
                                r"\bsuspension|\bremoval\b|cease and desist|"
                                r"\bprohibit|\bdebarment|\btermination\b|"
                                r"\bforfeit|\bliabilit"),
    ("Procedure & appeals", r"\bprocedure|\bhearing|\bappeal|\bpetition|"
                            r"\breview\b|\badjudicat|\bservice of|\bdiscovery\b|"
                            r"\bsubpoena|\bfiling\b|\bcomputation of time"),
    ("Reporting & records", r"\breport|\brecord|\bretention|\bdisclosure to the|"
                            r"\bbooks\b|\baudit|\bexaminat|\bdata\b|\bsubmission"),
    ("Disclosure & consumer", r"\bdisclos|\badvertis|\bnotice to|\bstatement\b|"
                              r"\bconsumer|\bborrower|\bcustomer|\bcomplaint|"
                              r"\bbilling\b|\bsolicitat"),
    ("Fees & assessments", r"\bfee\b|\bfees\b|\bassessment|\bpremium|\bcharge\b|"
                           r"\bpric|\bcost of\b"),
    ("Lending & credit", r"\bloan|\blend|\bcredit\b|\bmortgage|\bextension of credit|"
                         r"\badvance|\bcollateral|\bsecurit(y|ies) interest|"
                         r"\bunderwrit"),
    ("Governance & staff", r"\bdirector|\bofficer|\bemploye|\bboard of\b|"
                           r"\bconflict of interest|\bcompensation|\bethic|"
                           r"\bgovernance|\bfiduciar"),
    ("Powers & activities", r"\bactivit|\bpowers?\b|\bpermissible|\binvestment|"
                            r"\bdividend|\bdistribution|business combination|"
                            r"\bbranch|\bconversion\b|\brelocat|\boperations?\b|"
                            r"\bservices?\b|\bengag|\bownership|\bsubsidiar"),
    ("Computation & method", r"\bcomputation|\bmethodolog|\bformula|\bapproach\b|"
                             r"\bmeasure|\bdetermin|\bcalculat|\bcriteri|"
                             r"\bstandards?\b|\bfactors?\b|\bratio\b|"
                             r"\bthreshold|\blimits?\b|\bminimum\b|\bmaximum\b"),
]


# Institution names that contain category keywords ("Farm Credit", "credit
# union", "home loan bank") match on the entity, not the subject. Strip them
# before classifying: they were 22% of the Lending & credit bucket.
ENTITY = _re_entity = None


def _scrub(h):
    import re as _re
    global ENTITY
    if ENTITY is None:
        ENTITY = _re.compile(
            r"farm credit administration|farm credit system|farm credit bank"
            r"|farm credit|national credit union administration|credit union"
            r"|central liquidity facility|export-import bank"
            r"|federal home loan bank|home loan bank|bank for cooperatives")
    return ENTITY.sub(" ", h)


def category(r):
    import re as _re
    if "nterpret" in (r.get("subjgrp") or "") or "nterpret" in (r.get("subpart") or ""):
        return "Interpretation"
    h = _scrub((r.get("heading") or "").lower())
    for name, pat in CATS:
        if pat and _re.search(pat, h):
            return name
    return "Other"
