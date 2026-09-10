"""One mapping from Fiskeridirektoratet's application types to readable families.

Kept in one file so every chart in this recipe names the same thing the same way.
The source strings are Norwegian, long, and several are truncated in the feed —
"Særlige formå" for "Særlige formål" — so matching is on a prefix or a contained
word rather than on equality.
"""
from __future__ import annotations


def family_of(raw: str) -> str | None:
    t = (raw or "").strip().lower()
    if not t:
        return None
    if t.startswith("ny lokalitet"):
        return "New sea site"
    if t.startswith("endring"):
        return "Change existing site"
    if "samlokalisering" in t:
        return "Co-location"
    if t.startswith(("særlige", "saerlige")):
        return "Special purpose"
    if "på land" in t or "landbasert" in t:
        return "Land-based"
    if t.startswith(("ny akvakulturtillatelse", "ny tillatelse")):
        return "New licence"
    return None


# Does granting this application create capacity that did not exist before, or
# does it modify something already licensed? The queue treats the two completely
# differently and the distinction is not in any single field — it has to be
# derived from the application type.
NEW_CAPACITY = {"New sea site", "Land-based", "New licence",
                "Special purpose"}


def adds_capacity(fam: str) -> bool:
    return fam in NEW_CAPACITY
