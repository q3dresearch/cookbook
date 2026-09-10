"""Print a section's enclosing subpart heading and opening text from the raw store."""
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
import glob, gzip, sys, re
import xml.etree.ElementTree as ET
SRC = os.path.join(RAW, "ecfr", "title-12", "2026-09-01")
want = sys.argv[1:]
for w in want:
    part = w.split(".")[0]
    p = f"{SRC}/part-{part}.xml.gz"
    root = ET.fromstring(gzip.open(p, "rt").read())
    parent = {c: par for par in root.iter() for c in par}
    for d in root.iter():
        if d.tag.startswith("DIV") and d.get("TYPE") == "SECTION" and (d.get("N") or "") == w:
            chain = []
            n = d
            while n in parent:
                n = parent[n]
                if n.tag.startswith("DIV") and n.get("TYPE") in ("SUBPART", "SUBJGRP", "PART"):
                    chain.append(f"{n.get('TYPE')}: {' '.join((n.findtext('HEAD') or '').split())}")
            body = " ".join(" ".join("".join(x.itertext()).split())
                            for x in d.iter("P"))
            print(f"### {w}  {' '.join((d.findtext('HEAD') or '').split())}")
            for c in reversed(chain):
                print(f"    {c}")
            print(f"    TEXT: {body[:520]}")
            print()
