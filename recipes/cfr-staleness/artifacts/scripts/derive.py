"""Derive a section-level table from captured eCFR part XML.

Re-runnable against the raw store at zero network cost, which is the point of
capturing the bytes: a new question is a new derive, not a new crawl.
"""
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
import csv, glob, gzip, json, os, re, sys
import xml.etree.ElementTree as ET

TITLE = sys.argv[1]
DATE = sys.argv[2] if len(sys.argv) > 2 else "2026-09-01"
SRC = os.path.join(RAW, "ecfr", f"title-{TITLE}", DATE)
OUT = os.path.join(DERIVED, f"cfr-title{TITLE}-sections.csv")

struct = json.loads(gzip.open(f"{SRC}/structure.json.gz", "rt").read())


def walk(n, chap=None, part=None, label=None):
    t, i = n.get("type"), n.get("identifier")
    if t == "chapter":
        chap, label = i, n.get("label_description") or ""
    if t == "part":
        part = i
    yield n, chap, part, label
    for c in n.get("children") or []:
        yield from walk(c, chap, part, label)


nodes = list(walk(struct))
sec_meta = {n["identifier"]: (c, lab, bool(n.get("reserved")))
            for n, c, p, lab in nodes
            if n.get("type") == "section" and n.get("identifier")}
part_meta = {p: (c, lab, bool(n.get("reserved")))
             for n, c, p, lab in nodes if n.get("type") == "part"}


def group_heads(root):
    """section id -> (subpart head, subject-group head) from the XML nesting."""
    parent = {c: p for p in root.iter() for c in p}
    out = {}
    for d in root.iter():
        if not (d.tag.startswith("DIV") and d.get("TYPE") == "SECTION"):
            continue
        sp = sg = ""
        n = d
        while n in parent:
            n = parent[n]
            if not n.tag.startswith("DIV"):
                continue
            h = " ".join((n.findtext("HEAD") or "").split())
            if n.get("TYPE") == "SUBJGRP" and not sg:
                sg = h
            elif n.get("TYPE") == "SUBPART" and not sp:
                sp = h
        out[d.get("N") or ""] = (sp, sg)
    return out


def cita_of(div):
    for c in div.iter("CITA"):
        return " ".join("".join(c.itertext()).split())
    return ""


rows = []
for path in sorted(glob.glob(f"{SRC}/part-*.xml.gz")):
    part = os.path.basename(path)[5:-7]
    try:
        root = ET.fromstring(gzip.open(path, "rt").read())
    except ET.ParseError as e:
        print("parse fail", part, e)
        continue
    pcita = ""
    for d in root.iter():
        if d.tag.startswith("DIV") and d.get("TYPE") == "PART":
            pcita = cita_of(d)
            break
    pchap, plab, pres = part_meta.get(part, ("", "", False))
    gh = group_heads(root)
    phead = " ".join((next((d.findtext("HEAD") for d in root.iter()
        if d.tag.startswith("DIV") and d.get("TYPE") == "PART"), "") or "").split())
    for d in root.iter():
        if not (d.tag.startswith("DIV") and d.get("TYPE") == "SECTION"):
            continue
        num = (d.get("N") or "").strip()
        head = " ".join((d.findtext("HEAD") or "").split())
        own = cita_of(d)
        chap, lab, res = sec_meta.get(num, (pchap, plab, False))
        sp, sg = gh.get(num, ("", ""))
        rows.append({
            "title": TITLE, "chapter": chap or pchap or "",
            "agency": lab or plab or "", "part": part, "section": num,
            "heading": head,
            "part_head": phead, "subpart": sp, "subjgrp": sg,
            "reserved": int(bool(res) or "[Reserved]" in head or bool(pres)),
            "cite_level": "section" if own else ("part" if pcita else "none"),
            "source_note": (own or pcita).replace("\n", " "),
        })

cols = ["title", "chapter", "agency", "part", "part_head", "subpart",
        "subjgrp", "section", "heading", "reserved", "cite_level",
        "source_note"]
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, cols)
    w.writeheader()
    w.writerows(rows)
print(f"derived {len(rows)} sections from {len(glob.glob(f'{SRC}/part-*.xml.gz'))} "
      f"parts -> {OUT}")
