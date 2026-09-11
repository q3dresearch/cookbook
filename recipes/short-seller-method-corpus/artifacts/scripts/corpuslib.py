"""The denominator, defined once in code instead of remembered in prose.

Question 1 of this recipe answered "what is the denominator?" with 94 initial
reports rather than the 105 posts the API returns. That answer then lived only as a
sentence in questions.md, so chart-independent-barrier.py went on dividing by 105
and shipped a figure that contradicted an answered question. This module is the
fix: one definition, imported by every script that needs a base.

    105 posts = 94 initial reports + 9 follow-ups + 2 admin

A follow-up REACTS to the target's rebuttal — "Our Reply to X", "X's Response",
"Update: after 96 hours". A numbered sequel ("Aphria Part 2") is a new report: it
carries new findings rather than answering a denial, which is why it counts in the
94 and the rebuttals do not.
"""
import html, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
def _corpus():
    """The newest capture on disk, not a hardcoded date.

    This named one file, `hindenburg-corpus-2026-09-07.json`. capture_hindenburg.py
    writes the day it runs, so a reader who captured fresh got the file and a
    FileNotFoundError for a date they never had.
    """
    d = HERE.parent / "raw" / "hindenburg"
    found = sorted(d.glob("hindenburg-corpus-*.json"))
    if not found:
        raise SystemExit(
            "  No Hindenburg capture found.\n"
            "  Run:  python artifacts/scripts/capture_hindenburg.py\n"
            f"  It writes into {d}")
    return found[-1]


CORPUS = None   # resolved on first load, so importing this module never touches disk

# Reacting to the target talking back. Ordered before the sequel test on purpose.
FOLLOWUP = re.compile(
    r"\bour (reply|response) to\b|\b(response|reply)\b.*\bconfirmed\b|"
    r"^update:|\bwe view .*'?s? response\b|\btacit admission\b|"
    r"\b(response|reply)\b\s*$|:\s*our response\b|"
    r"\bupdate\b\s*[-–—]|\bfails to address\b", re.I)
# House business: no target company at all.
ADMIN = re.compile(r"announces \$|\bbounty\b|a personal note|we are hiring|"
                   r"\binternship\b|\bnewsletter\b", re.I)


def title(p):
    t = p.get("title", {})
    raw = t.get("rendered", t) if isinstance(t, dict) else str(t)
    return html.unescape(re.sub(r"<[^>]+>", "", raw)).strip()


def body(p):
    return html.unescape(re.sub(r"<[^>]+>", " ", p["content"]["rendered"]))


def kind(p):
    t = title(p)
    if ADMIN.search(t):
        return "admin"
    if FOLLOWUP.search(t):
        return "follow-up"
    return "initial"


def load(only="initial"):
    """Posts of one kind, or all of them when only=None."""
    global CORPUS
    if CORPUS is None:
        CORPUS = _corpus()
    posts = json.load(open(CORPUS))
    for p in posts:
        p["kind"] = kind(p)
    return [p for p in posts if only is None or p["kind"] == only]


if __name__ == "__main__":
    from collections import Counter
    posts = load(None)
    c = Counter(p["kind"] for p in posts)
    print(f"  {len(posts)} posts: " + ", ".join(f"{v} {k}" for k, v in c.most_common()))
    expect = {"initial": 94, "follow-up": 9, "admin": 2}
    bad = {k: (c[k], v) for k, v in expect.items() if c[k] != v}
    print("  MATCHES the answer recorded in questions.md" if not bad
          else f"  DISAGREES with questions.md: {bad}")
    for p in posts:
        if p["kind"] != "initial":
            print(f"    {p['kind']:<10} {p['date'][:10]}  {title(p)[:62]}")


# ---------------------------------------------------------------------------
# The probes, defined once.
#
# They were copied into three scripts and the copies drifted: one paid-terminal
# probe listed Morningstar and the other did not, so the same corpus reported
# 39% in one place and 41% in another. Worse, the field-legwork probe named
# "Hindenburg" outright, which can only ever score zero on another firm — it
# would have manufactured the finding that Hindenburg does more legwork than
# anyone. The firm name is a parameter here.
# ---------------------------------------------------------------------------

def probes(firm="Hindenburg"):
    """label -> regex. `firm` is the publishing firm's name, for self-reference."""
    esc = re.escape(firm)
    return {
        "SEC filings":            r"10-K|10-Q|8-K|proxy|DEF 14A|prospectus|SEC filing",
        "court / litigation":     r"\bcomplaint\b|\blawsuit\b|\bdocket\b|\bcourt filing|indictment",
        "social media":           r"\bInstagram\b|\bLinkedIn\b|\bFacebook\b|\bYouTube\b|\bTikTok\b|\bTwitter\b",
        "paid terminal":          r"\bBloomberg\b|\bFactSet\b|\bYCharts\b|\bRefinitiv\b|\bCapital IQ\b|Morningstar",
        # Widened after reading Night Market, which writes "We visited POET's
        # Toronto HQ building" and "we sent an investigator to Canada". The
        # original demanded the exact phrase "visited the facility" and the
        # possessive "our investigator", so it scored that firm at zero field
        # legwork while the reports described three separate site visits.
        "own field legwork":      r"onsite visit|site visit|we visited|we have visited|"
                                  r"visited the (facility|site|office|plant|building)|"
                                  r"we (sent|hired|engaged|dispatched) (an?|our) "
                                  r"(local |private )?(investigator|researcher|photographer)|"
                                  r"our (investigator|researcher)s?|" + esc + r" (Researcher|Investigator)",
        # \b on every acronym. Without it, case-insensitive "UCC" matches the
        # "ucc" inside "success" and "succeed" — it scored 69/94 reports as
        # having searched a state lien registry. The real figure is 7.
        "foreign/state registry": r"\bQCC\b|Qichacha|\bSAIC\b|companies house|"
                                  r"entity search|secretary of state|\bUCC\b|"
                                  # "registry" alone would catch clinical-trial registries
                                  # in every pharma report, so it must be qualified.
                                  r"corporate records|(state|business|company|companies) registry|"
                                  r"corporate registry|registrar of companies",
        "web archive":            r"wayback machine|web\.archive\.org|archive\.org",
        "whistleblower":          r"whistleblower|leaked (documents?|recordings?)|internal documents obtained",
        "import / trade records": r"Import ?Genius|Panjiva|bill of lading|customs record",
        "expert network":         r"expert network|industry experts?",
        # Added after the control corpus, not before it. The probe set was written
        # by reading Hindenburg, so it named Hindenburg's habits: Night Market
        # confirms claims through FOIA requests and by interviewing companies at
        # trade conferences, and the original ten probes scored it at zero for
        # original sourcing. A probe list built from one firm measures that firm.
        "records request":        r"\bFOIA\b|freedom of information|public records request|"
                                  r"records request|subject access request",
        "original interviews":    r"we (spoke|talked) (with|to)|we interviewed|"
                                  r"(told|said to) (us|this firm)|in an interview with us|"
                                  r"our (call|conversation)s? with",
    }


# What each probe costs an independent researcher. Ordered, so figures that use
# it want an ordinal ramp, not categorical hues.
BARRIER = {
    "free & remote":  ["SEC filings", "court / litigation", "social media",
                       "foreign/state registry", "web archive", "records request"],
    "needs money":    ["paid terminal", "import / trade records", "expert network"],
    # "Presence" is a person, not a place: getting someone to talk to you is the
    # barrier, whether you flew there or picked up a phone.
    "needs presence": ["own field legwork", "original interviews"],
    "needs luck":     ["whistleblower"],
}


# ---------------------------------------------------------------------------
# Hand-verified overrides for "own field legwork".
#
# This probe is wrong in both directions and no regex fixed it. The loose version
# (`Researcher|Investigator`, unanchored) scored 36/94 by catching the firm calling
# itself "professional fraud researchers", a state regulator's investigators, and a
# quote from the target company's own press release. The tight version missed
# "our local investigator", "an investigator sent to the exact site", and "the
# Indian investigator in front of Next Gen's offices" — all plainly their own
# people on the ground.
#
# So: the regex proposes, and every disagreement between the two versions was read
# and ruled. The quote is the evidence for the ruling.
# ---------------------------------------------------------------------------

LEGWORK_YES = {
    "ebang":      "an employee ... told our local investigator",
    "nikola":     "an investigator sent to the exact site used by Nikola",
    "eros-international-on-the-ground-research-em":
                  "the Indian investigator in front of Next Gen's offices",
}
LEGWORK_NO = {
    "wagner":     "'we are professional fraud researchers' — the firm describing itself",
    "draftkings": "Oregon flying investigators to Bulgaria — the regulator's, not theirs",
    "clover":     "'whether short-sellers and critical researchers play an important role' — rhetoric",
    "tecnoglass": "'one of the lead investigators in the case' — a criminal investigation",
    "facedrive":  "'Facedrive Health and Waterloo researchers' — the target's partners",
    "predictive-technology": "'Lisa Fortier, a researcher at Cornell' — a cited academic",
    "pulse-biosciences-failed-fda-clearance-new-sec":
                  "'our network of clinical investigators' — quoted from the company",
    "sorrento":   "'one Mount Sinai researcher we talked to' — a phone interview, not presence",
}


def legwork(post):
    """Did the firm put its own people on the ground for this report?"""
    for slug, _ in LEGWORK_YES.items():
        if post["slug"].startswith(slug):
            return True
    for slug, _ in LEGWORK_NO.items():
        if post["slug"].startswith(slug):
            return False
    return bool(re.search(probes()["own field legwork"], body(post), re.I))
