"""Sections whose own text sets an expiry — and whether that date has passed.

Two traps found by reading the first run's output rather than trusting its count:

  * The bracketed SOURCE NOTE at the end of every section is full of dates
    ("[53 FR 19433, May 27, 1988, as amended at 82 FR 27583...]"). A date regex
    finds them and they are publication dates, not expiries. CITA/CITATION
    elements are stripped before scanning.
  * "This section shall be effective on December 20, 2010" is an EFFECTIVE date,
    the opposite of a sunset, and the naive pattern matched it on the word
    "effect". Expiry now requires expiry semantics, and "effective" only counts
    when bounded — "effective until", "remain in effect until".

Both bugs inflated the first count from ~10 real sections to 33.
"""
import gzip, glob, re, sys, csv, datetime as dt
import xml.etree.ElementTree as ET

RAW = sys.argv[1]
TODAY = dt.date(2026, 9, 10)
MONTHS = {m: i + 1 for i, m in enumerate(
    "January February March April May June July August September October "
    "November December".split())}

SUBJECT = r"(this|the) (section|paragraph|subpart|part|appendix|exemption|" \
          r"exception|provision|rule|authority|extension|waiver|relief)"
# "shall not apply" is SCOPE, not expiry, and it is everywhere: including it
# produced 211 phantom "undated sunsets" in Title 12, 99% of which were
# exceptions like "shall not apply to an employee ... if the institution
# determines it is not feasible". Only expiry semantics survive here.
EXPIRY = (r"(expires?\b|shall expire|expiration date of this|sunset date|"
          r"cease[sd]? to be effective|shall cease to apply|"
          r"(?:shall|will) no longer (?:be in effect|apply|have (?:any )?effect)|"
          r"(?:remain|be)(?:s)? in effect (?:only )?(?:un)?til|"
          r"effective (?:only )?(?:un)?til|"
          r"applies only (?:until|through)|is repealed effective)")
SELF = re.compile(rf"{SUBJECT}[^.;]{{0,120}}?{EXPIRY}"
                  rf"|{EXPIRY}[^.;]{{0,60}}?{SUBJECT}", re.I)
DATE = re.compile(r"\b(January|February|March|April|May|June|July|August|"
                  r"September|October|November|December)\s+(\d{1,2}),\s+((?:19|20)\d{2})")


def body_without_citations(el):
    """Section text with source notes removed — they are dated, and not expiries."""
    clone = ET.fromstring(ET.tostring(el))
    for parent in clone.iter():
        for child in list(parent):
            if child.tag in ("CITA", "CITATION", "EDNOTE", "SECAUTH", "AUTH", "FTNT"):
                parent.remove(child)
    t = re.sub(r"\s+", " ", "".join(clone.itertext()))
    return re.sub(r"\[[^\]]{0,400}?\b(?:FR|Stat\.)\b[^\]]{0,400}?\]", " ", t).strip()


rows = []
for f in sorted(glob.glob(f"{RAW}/*.xml.gz")):
    try:
        root = ET.parse(gzip.open(f, "rb")).getroot()
    except Exception as e:
        print(f"  PARSE FAIL {f}: {e}", file=sys.stderr)
        continue
    for d in root.iter():
        if d.tag != "DIV8" or (d.get("TYPE") or "") != "SECTION":
            continue
        body = body_without_citations(d)
        m = SELF.search(body)
        if not m:
            continue
        # The date must sit in the same clause AND after the expiry phrase. Third
        # bug found by reading output: 29 CFR 2582.8478-4 says "shall become
        # effective January 1, 1990, and remain in effect until it is amended or
        # withdrawn" — an effective date plus an indefinite term, which a
        # clause-wide search reports as an expiry in 1990.
        clause = body[m.start():m.end() + 90].split(";")[0]
        tail = body[m.end() - 12:m.end() + 90].split(";")[0]
        if re.search(r"until (it is |such time as )?(amended|withdrawn|superseded|"
                     r"revoked|replaced|rescinded|modified)", tail, re.I):
            tail = ""                  # indefinite: ends when someone ends it
        dm = DATE.search(tail)
        when = None
        if dm:
            try:
                when = dt.date(int(dm.group(3)), MONTHS[dm.group(1)], int(dm.group(2)))
            except ValueError:
                when = None
        rows.append({
            "section": (d.get("N") or "").strip(),
            "heading": (d.findtext("HEAD") or "").strip()[:90],
            "expiry": when.isoformat() if when else "",
            "passed": "yes" if when and when < TODAY else ("no" if when else "undated"),
            "quote": clause.strip()[:230],
        })
w = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]) if rows else ["section"])
w.writeheader(); w.writerows(rows)
n_p = sum(1 for r in rows if r["passed"] == "yes")
print(f"# {len(rows)} sections set their own expiry; {n_p} name a date already past; "
      f"{sum(1 for r in rows if r['passed']=='undated')} give no date", file=sys.stderr)
