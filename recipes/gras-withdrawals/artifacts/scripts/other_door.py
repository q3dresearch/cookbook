"""Q10: where do the vanished GRAS filings go? Some took another door.

    python other_door.py

155 withdrawn notices have no recorded resubmission. Three fates: abandoned,
refiled by another route, or marketed with no notice at all. The third is
invisible by law. This tests the second.

FDA's "Substances Added to Food" inventory (formerly EAFUS) lists 3,971
substances it permits, each with the 21 CFR sections that allow it — 172.x is
the food additive petition route, 182/184 is GRAS by regulation, 175–178 is food
contact. If a vanished substance is in there, it did not vanish.

THE JOIN IS WEAK AND IS NOT USED AS A RATE. Both sides are free-text chemical
names. Exact normalised matching finds 11 of 155; loosening to token containment
finds 27, of which reading every one shows 11 are wrong — "White mulberry leaf
extract" matched "MUSTARD, YELLOW, EXTRACT", and Bacillus subtilis matched an
enzyme merely derived from it. Precision is 59%.

So the fuzzy pass generates candidates and a human decides. VERIFIED below is
that decision, written down so it can be argued with. The number it produces is
a FLOOR: a substance under a different name is still missed.
"""
import sys, os, csv, re, html, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graslib

# GRN -> (inventory name, route). Each read by hand against the candidate list.
VERIFIED = {
    "16":   ("MENHADEN OIL", "GRAS by regulation"),
    "58":   ("GUM ARABIC", "GRAS by regulation"),
    "107":  ("POLYDEXTROSE", "food additive petition"),
    "257":  ("4-AMINOBUTYRIC ACID", "listed, no CFR section"),
    "340":  ("THEOBROMINE", "listed, no CFR section"),
    "347":  ("CAFFEINE", "GRAS by regulation"),
    "362":  ("L-CARNITINE", "listed, no CFR section"),
    "391":  ("SPIRULINA EXTRACT", "listed, no CFR section"),
    "442":  ("ALLYL ISOTHIOCYANATE", "food additive petition"),
    "595":  ("4-AMINOBUTYRIC ACID", "listed, no CFR section"),
    "658":  ("GRAPEFRUIT, EXTRACT", "GRAS by regulation"),
    "718":  ("CALCIUM PYROPHOSPHATE", "GRAS by regulation"),
    "782":  ("L-ARABINOSE", "listed, no CFR section"),
    "912":  ("TREHALOSE, DIHYDRATE", "listed, no CFR section"),
    "1044": ("ETHYLENEDIAMINETETRAACETIC ACID DISODIUM", "listed, no CFR section"),
    "1165": ("1,3-BUTYLENE GLYCOL", "food additive petition"),
}
# Candidates the fuzzy pass produced and a human rejected, kept so the rejection
# is auditable rather than silent.
REJECTED = {
    "139": "Cassia gum matched CASSIA BUDS — a gum is not a bud",
    "174": "Lysozyme matched ALPHA-ACETOLACTATE DECARBOXYLASE",
    "431": "Colostral whey protein matched FISH PROTEIN CONCENTRATE",
    "433": "Poloxamer fatty acid esters matched BUTTER ESTERS",
    "559": "Bacillus coagulans matched an enzyme derived FROM it",
    "560": "Bacillus licheniformis matched an enzyme derived FROM it",
    "562": "Bacillus subtilis matched an enzyme derived FROM it",
    "710": "Basic methacrylate copolymer matched POLYACRYLAMIDE RESIN",
    "820": "Lactobacillus fermentum matched a urease preparation using it",
    "894": "White mulberry leaf extract matched MUSTARD, YELLOW, EXTRACT",
    "992": "as 894",
}


def latest_inventory():
    import glob
    f = sorted(glob.glob(os.path.join(graslib.RAW, "food-substances-*.csv")))
    if not f:
        raise SystemExit("no food-substances capture — run capture.py first")
    return f[-1]


def norm(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    s = re.sub(r"\(.*?\)", " ", s).lower()
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())


def load_inventory(path):
    """Substance name (and every synonym) -> the row, plus its CFR sections."""
    raw = list(csv.reader(open(path, encoding="cp1252")))
    hdr = [h.strip() for h in raw[4]]          # rows 0-3 are banner and blanks
    rows = [dict(zip(hdr, r)) for r in raw[5:] if len(r) == len(hdr)]
    inv = {}
    for r in rows:
        names = [r["Substance"]] + re.split(r"<br />|&diams;", r["Other Names"] or "")
        for n in names:
            k = norm(n)
            if len(k) > 3:
                inv.setdefault(k, r)
    return rows, inv


def candidates(wd, inv):
    """The fuzzy pass. Generates suggestions; it does not decide."""
    out = []
    for r in wd:
        t = {x for x in norm(graslib.clean_substance(r["substance"])).split() if len(x) > 4}
        if not t:
            continue
        for nm, row in inv.items():
            nt = set(nm.split())
            if t <= nt or (len(t) >= 2 and len(t & nt) >= max(2, len(t) - 1)):
                out.append((r, row))
                break
    return out


def main():
    by, src = graslib.load()
    wd = [r for r in by.values() if r["outcome"] == "withdrawn"
          and not (r["next"] and str(r["next"]) != "None")]
    inv_rows, inv = load_inventory(latest_inventory())
    cands = candidates(wd, inv)
    seen = {str(r["grn"]) for r, _ in cands}
    print(f"{len(inv_rows):,} substances FDA permits, {len(inv):,} searchable names")
    print(f"{len(wd)} withdrawn notices with no recorded resubmission")
    print(f"  fuzzy candidates this run: {len(cands)}")
    stale = seen - set(VERIFIED) - set(REJECTED)
    gone = (set(VERIFIED) | set(REJECTED)) - seen
    if stale:
        print(f"  !! {len(stale)} candidate(s) not yet judged by hand: {sorted(stale)}")
    if gone:
        print(f"  !! {len(gone)} judged GRN(s) the fuzzy pass no longer proposes: {sorted(gone)}")
    if not stale and not gone:
        print("  every candidate has a recorded human verdict")
    found = [r for r in wd if str(r["grn"]) in VERIFIED]
    print(f"  rejected by hand: {len(REJECTED)} — precision "
          f"{len(VERIFIED)/(len(VERIFIED)+len(REJECTED)):.0%}")
    print(f"  VERIFIED still permitted in food today: {len(found)} = "
          f"{len(found)/len(wd):.0%} of the 155\n")
    route = collections.Counter(VERIFIED[str(r['grn'])][1] for r in found)
    for k, v in route.most_common():
        print(f"    {v:2d}  {k}")
    print()
    for r in sorted(found, key=lambda r: int(r["grn"])):
        nm, rt = VERIFIED[str(r["grn"])]
        print(f"  GRN {str(r['grn']):>4s}  {graslib.clean_substance(r['substance'])[:40]:40s}"
              f" -> {nm[:34]:34s} {rt}")
    print(f"\n  So at least {len(found)} of the 155 did not vanish — they were already "
          f"permitted or got there another way.")
    print(f"  This is a FLOOR. A substance listed under a different name is still missed, "
          f"and the third branch —")
    print(f"  sold on an undisclosed self-determination — leaves no record anywhere by "
          f"construction.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
