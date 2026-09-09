#!/usr/bin/env python3
"""How GDPR cases run: what they conclude, who they hit, and how long they take.

    python gdpr-case-timeline.py <gdprhub.jsonl>

The article distribution says what regulators engage with. This says what happens
to a case — the part a company on the receiving end actually experiences.

    outcomes     what proportion of published decisions find a violation at all
    lead time    Date_Started to Date_Decided, in days
    parties      how many distinct companies, and who recurs
    appeals      how often a decision is appealed, per Appeal_To_Status
    trend        whether any of the above is moving year on year

What this deliberately does NOT do is call a fine "company-killing". GDPR fines
are capped at 4% of global annual turnover, so the only way to judge severity is
against revenue, and GDPRhub records no revenue, no employee count and no company
identifier beyond a name typed by a contributor. A €2m fine is a rounding error
to a bank and fatal to an agency, and nothing here distinguishes them. The
absolute distribution is reported and the question is left open rather than
answered badly.

Two more things the fine field will not support:

* It is the fine as *imposed*, not as paid. Reductions live in the prose — one
  Spanish bank's €2,000,000 was settled at €1,200,000 — so totals here are
  upper bounds on what was actually collected.
* Publication is not enforcement. These are the decisions authorities chose to
  publish, and a case that quietly closed is invisible. "What does not get
  prosecuted" cannot be read off a corpus of prosecutions.
"""
from __future__ import annotations

import collections
import datetime as dt
import importlib.util
import json
import re
import statistics
import sys
import unicodedata
from pathlib import Path


def _analysis():
    spec = importlib.util.spec_from_file_location(
        "gdpr_analysis", str(Path(__file__).with_name("gdpr-article-concentration.py")))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Authorities describe the same conclusion in different words: a Spanish
# "Violation Found" and an Irish "Upheld" are one outcome, and leaving them
# apart splits the headline number in half. The mapping is stated rather than
# inferred, and anything unrecognised is counted as unknown instead of being
# quietly folded into the nearest bucket.
OUTCOME_MAP = {
    "upheld": "violation found", "violation found": "violation found",
    "partly upheld": "partly upheld", "partially upheld": "partly upheld",
    "rejected": "no violation", "no violation found": "no violation",
    "dismissed": "no violation", "not upheld": "no violation",
    "no further action": "no violation", "withdrawn": "closed without a finding",
    "settled": "closed without a finding", "inadmissible": "closed without a finding",
    "other outcome": "other", "other": "other",
}

# Parties are typed by contributors, and many are pseudonymised natural persons
# rather than companies. Counting distinct strings as "companies targeted" would
# be wrong in both directions: these inflate it, and 'Google LLC (Google Spain,
# S.L.)' versus 'Google LLC' deflates it.
ANON = re.compile(r"^(?:[A-Z]\.?\s*){1,4}$|"
                  r"^(?:an?\s+)?(?:anonym|unnamed|data subject|the complainant|complainant|"
                  r"unknown|n/?a|individual|natural person|private person|redacted|x+$)", re.I)


def canon(name: str) -> str:
    """Fold obvious spelling variants of one company together.

    'Vodafone España, S.A.U.' and 'VODAFONE ESPAÑA, S.A.U.' are the same firm
    typed twice, and counting them separately both inflates the number of
    companies and hides the repeat offenders. This only folds case, accents,
    punctuation and legal-form suffixes — it will not merge 'Google' with
    'Google LLC', so the counts below remain conservative in that direction.
    """
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\b(s a u|s a|s l u|s l|sau|sa|slu|sl|gmbh|ltd|limited|llc|inc|bv|b v|"
               r"nv|n v|ag|as|ab|oy|plc|spa|s p a|srl|s r l|kft|zrt|d o o|sp z o o)\b",
               " ", s)
    return re.sub(r"\s+", " ", s).strip()


def outcome_of(r: dict) -> str:
    raw = (r.get("outcome") or "").strip()
    if not raw:
        return "unknown"
    return OUTCOME_MAP.get(raw.lower(), "unknown")


def date(raw: str) -> dt.date | None:
    """GDPRhub writes DD.MM.YYYY. Accept that and ISO; refuse anything else.

    Refusing matters more than coverage: a DD/MM read as MM/DD is a silent error
    of up to eleven months in a duration, in whichever direction flatters the
    story.
    """
    s = (raw or "").strip()
    if not s:
        return None
    m = re.fullmatch(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", s)
    if m:
        d, mo, y = (int(x) for x in m.groups())
        if mo > 12:
            return None                    # not DD.MM: ambiguous, drop it
        try:
            return dt.date(y, mo, d)
        except ValueError:
            return None
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return dt.date(*(int(x) for x in m.groups()))
        except ValueError:
            return None
    return None


def pct(part: int, whole: int) -> str:
    return f"{part/whole:>6.1%}" if whole else "     —"


def bar(v: float, mx: float, w: int = 26) -> str:
    return "█" * max(1, round(v / mx * w)) if v else ""


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    g = _analysis()
    rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
    n = len(rows)
    print(f"\n  {n:,} published decisions\n")

    # ---- outcomes -----------------------------------------------------------
    oc = collections.Counter(outcome_of(r) for r in rows)
    print("  OUTCOME — what the authority concluded, normalised")
    mx = max(oc.values())
    for o, c in oc.most_common(12):
        print(f"    {o[:34]:<36}{c:>6,}{pct(c, n)}  {bar(c, mx)}")
    decided = sum(c for o, c in oc.items() if o in ("violation found", "no violation",
                                                    "partly upheld"))
    if decided:
        v = oc["violation found"] + oc["partly upheld"]
        print(f"    of the {decided:,} that reached a finding either way, "
              f"{v/decided:.0%} found a violation")
    raw_oc = collections.Counter((r.get("outcome") or "(blank)").strip() for r in rows)
    unmapped = [(o, c) for o, c in raw_oc.most_common()
                if o and o.lower() not in OUTCOME_MAP]
    if unmapped:
        print(f"    unmapped outcome labels (counted as unknown): "
              f"{', '.join(f'{o} x{c}' for o, c in unmapped[:6])}")

    ty = collections.Counter((r.get("type") or "(blank)").strip() for r in rows)
    print("\n  TYPE — how the case arrived")
    for t, c in ty.most_common(8):
        print(f"    {t[:34]:<36}{c:>6,}{pct(c, n)}")

    # ---- lead time ----------------------------------------------------------
    spans = []
    for r in rows:
        a, b = date(r.get("date_started", "")), date(r.get("date_decided", ""))
        if a and b and b >= a and (b - a).days < 4000:
            spans.append(((b - a).days, r))
    print(f"\n  LEAD TIME — Date_Started to Date_Decided, {len(spans):,} of {n:,} "
          f"decisions carry both dates ({len(spans)/n:.0%})")
    # Coverage this thin is only usable if it is spread across authorities. If one
    # DPA fills the field and the rest do not, the median below is that DPA's
    # median wearing a European label.
    cov_n = collections.Counter(r["juris"] for r in rows if r.get("juris"))
    cov_k = collections.Counter(r["juris"] for _, r in spans if r.get("juris"))
    print("    coverage by authority — a median from one authority is not a European fact")
    for j, k in cov_k.most_common(6):
        print(f"      {j[:24]:<26}{k:>5,} of {cov_n[j]:>5,} decisions  "
              f"{k/cov_n[j]:>5.0%}")
    share_top = cov_k.most_common(1)[0][1] / len(spans) if spans else 0
    if share_top > 0.5:
        print(f"      WARNING: {cov_k.most_common(1)[0][0]} supplies "
              f"{share_top:.0%} of all dated cases — read the median as theirs")
    if spans:
        ds = sorted(s for s, _ in spans)
        q = statistics.quantiles(ds, n=4)
        print(f"    median {statistics.median(ds):>6,.0f} days  "
              f"({statistics.median(ds)/365.25:.1f} years)")
        print(f"    quartiles {q[0]:,.0f} / {q[1]:,.0f} / {q[2]:,.0f} days   "
              f"range {ds[0]:,}-{ds[-1]:,}")
        over = sum(1 for d in ds if d > 730)
        print(f"    {over:,} took more than two years ({over/len(ds):.0%})")

        print("\n    by outcome")
        byo = collections.defaultdict(list)
        for s, r in spans:
            byo[(r.get("outcome") or "(blank)").strip()].append(s)
        for o, vs in sorted(byo.items(), key=lambda kv: -len(kv[1]))[:6]:
            if len(vs) >= 15:
                print(f"      {o[:30]:<32}n={len(vs):>5,}  median {statistics.median(vs):>6,.0f}d")

        print("\n    by authority (>=25 dated decisions)")
        byj = collections.defaultdict(list)
        for s, r in spans:
            byj[r.get("juris") or "?"].append(s)
        rank = sorted(((statistics.median(v), k, len(v)) for k, v in byj.items()
                       if len(v) >= 25))
        head = rank[:4]
        tail = [r for r in rank[-4:] if r not in head]
        for med, j, k in head:
            print(f"      {j[:24]:<26}n={k:>5,}  median {med:>6,.0f}d   fastest")
        if tail:
            print("      ...")
            for med, j, k in tail:
                print(f"      {j[:24]:<26}n={k:>5,}  median {med:>6,.0f}d   slowest")

        print("\n    by year decided — is it getting slower?")
        byy = collections.defaultdict(list)
        for s, r in spans:
            d = date(r.get("date_decided", ""))
            if d:
                byy[d.year].append(s)
        for y in sorted(byy):
            if len(byy[y]) >= 15:
                print(f"      {y}  n={len(byy[y]):>5,}  median {statistics.median(byy[y]):>6,.0f}d")

        fined, unfined = [], []
        for s, r in spans:
            cur = (r.get("currency") or "").strip().upper()
            ok = cur in ("EUR", "€") or (not cur and r.get("juris") in g.EUROZONE)
            (fined if ok and g.money(r.get("fine", "")) else unfined).append(s)
        if len(fined) >= 15 and len(unfined) >= 15:
            print(f"\n    with a fine     n={len(fined):>5,}  median "
                  f"{statistics.median(fined):>6,.0f}d")
            print(f"    without a fine  n={len(unfined):>5,}  median "
                  f"{statistics.median(unfined):>6,.0f}d")

    # ---- parties ------------------------------------------------------------
    named = [r for r in rows if r.get("party")]
    anon = [r for r in named if ANON.match(r["party"].strip())]
    orgs = [r for r in named if not ANON.match(r["party"].strip())]
    parties = collections.Counter(r["party"].strip() for r in orgs)
    folded = collections.Counter(canon(r["party"]) for r in orgs if canon(r["party"]))
    print(f"\n  PARTIES — {len(named):,} decisions name one ({len(named)/n:.0%} of the "
          f"corpus); {len(anon):,} of those names are pseudonymised individuals")
    print(f"    {len(parties):,} distinct name strings across {len(orgs):,} decisions; "
          f"{len(folded):,} after folding case, accents and legal-form suffixes")
    rep = [(c, p) for p, c in folded.items() if c > 1]
    print(f"    {len(rep):,} organisations appear more than once "
          f"({sum(c for c, _ in rep):,} decisions, "
          f"{sum(c for c, _ in rep)/max(len(orgs),1):.0%} of named-organisation decisions)")
    print("    These are contributor-typed strings, not company identifiers: 'Google LLC'")
    print("    and 'Google LLC (Google Spain, S.L.)' are two names for one company, so the")
    print("    distinct count is an upper bound and the repeat count a lower one.")
    print("    most-cited organisations, after folding")
    shown = {}
    for r in orgs:
        shown.setdefault(canon(r["party"]), r["party"].strip())
    for p, c in folded.most_common(12):
        print(f"      {c:>4}  {shown.get(p, p)[:58]}")

    # ---- appeals ------------------------------------------------------------
    ap = collections.Counter((r.get("appeal_to_status") or "(blank)").strip() for r in rows)
    print("\n  APPEALS — Appeal_To_Status")
    for a, c in ap.most_common(8):
        print(f"    {a[:34]:<36}{c:>6,}{pct(c, n)}")
    known = {k: v for k, v in ap.items()
             if k and k.lower() not in ("unknown", "(blank)")}
    kn = sum(known.values())
    if kn:
        appealed = sum(v for k, v in known.items() if k.lower().startswith("appealed"))
        print(f"    Only {kn:,} of {n:,} decisions ({kn/n:.0%}) record a real status. "
              f"Among those, {appealed/kn:.0%} were appealed —")
        print(f"    and that is a rate among cases somebody bothered to follow up, "
              f"which is not the appeal rate.")

    # ---- fine distribution --------------------------------------------------
    vals = []
    for r in rows:
        cur = (r.get("currency") or "").strip().upper()
        if cur in ("EUR", "€") or (not cur and r.get("juris") in g.EUROZONE):
            v = g.money(r.get("fine", ""))
            if v:
                vals.append(v)
    if vals:
        vals.sort()
        print(f"\n  FINES — {len(vals):,} euro-denominated, as imposed (not as paid)")
        for label, q in (("min", vals[0]), ("p25", vals[len(vals)//4]),
                         ("median", statistics.median(vals)),
                         ("p75", vals[3*len(vals)//4]),
                         ("p90", vals[int(.9*len(vals))]),
                         ("p99", vals[int(.99*len(vals))]), ("max", vals[-1])):
            print(f"    {label:<8}{q:>16,.0f}")
        for t in (1e6, 1e7):
            k = sum(1 for v in vals if v >= t)
            print(f"    >= {t:>12,.0f}  {k:>5,}  {k/len(vals):.1%}")
        print("    Severity relative to the company is NOT measurable here: no revenue,")
        print("    no size, no identifier. The 4%-of-turnover cap cannot be checked.")

    red = [r for r in rows if re.search(r"reduc|settle|discount", r.get("summary", ""), re.I)]
    print(f"\n  {len(red):,} decisions mention a reduction or settlement in their summary "
          f"({len(red)/n:.1%}) — the Fine field does not reflect these.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
