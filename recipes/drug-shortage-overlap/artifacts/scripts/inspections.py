#!/usr/bin/env python3
"""Firm-name normalisation and pooled inspection loading.

Shared by `verify.py` and `negative/chart-4-inspection-null.py` so the two cannot
drift: a verifier that reimplements the thing it checks verifies its own copy.
"""
import collections, glob, json, os, re, sys
sys.path.insert(0, ".")
import shortagelib as S


STRIP = (r"\b(inc|llc|ltd|corp|corporation|company|co|usa|us|america|limited|plc|gmbh|"
         r"sa|ag|pharmaceuticals?|pharma|healthcare|health|laboratories|labs?|group|"
         r"holdings?|international|a pfizer)\b")


def firm(s):
    s = S.deaccent(s or "").lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(STRIP, " ", s)
    return re.sub(r"\s+", " ", s).strip()


def inspections():
    out = collections.defaultdict(list)
    rows = 0
    for src in ("fda.inspections.history", "fda.inspections.drugs"):
        for p in glob.glob(str(S.ARCHIVE / "raw" / src / "**" / "*"), recursive=True):
            if not os.path.isfile(p) or p.endswith(".gitkeep"):
                continue
            try:
                d = json.loads(S._read(p)).get("result") or []
            except Exception:
                continue
            rows += len(d)
            for r in d:
                f = firm(r.get("LegalName"))
                if f: out[f].append(r)
    return out, rows



def inspections_for_verify():
    return inspections()
