"""Load the GRAS inventory and resolve resubmission chains.

Two fields link retries, and their direction matters:
  Resubmitted  on a notice -> "this was resubmitted as GRN X"  (forward)
  Resubmission on a notice -> "this replaces GRN Y"            (backward)

Following them collapses notices into *substances*, which is the correct
denominator: a company that withdraws and refiles appears three times in a
notice count and once in a chain count.
"""
import csv, glob, html, io, os, re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
# Written for an earlier layout and left resolving two levels too shallow when
# the scripts moved under the recipe, so every path pointed at nothing. Anchor
# on the recipe, then walk up to the larder root.
RECIPE = os.path.dirname(os.path.dirname(HERE))
CHARTS = os.path.join(RECIPE, "artifacts", "charts")
# This recipe commits no data. capture.py writes into a work directory and every
# other script reads the same one: set GRAS_WORK, or accept ./work in the current
# directory. Nothing reaches outside the recipe except that dir.
WORK = os.environ.get("GRAS_WORK") or os.path.join(os.getcwd(), "work")
RAW = os.path.join(WORK, "fda-gras")
os.makedirs(RAW, exist_ok=True)
LETTER = "FDA's Letter"


def latest_capture():
    files = sorted(glob.glob(os.path.join(RAW, "gras-notices-*.csv")))
    if not files:
        raise SystemExit("no capture found — run capture.py first")
    return files[-1]


def _clean(s):
    """Cells carry HTML entities and italic tags from the web view."""
    s = html.unescape(re.sub(r"<[^>]+>", "", s or ""))
    return re.sub(r"\s+", " ", re.sub(r"\s*\(in PDF\)\s*", "", s,
                                      flags=re.I)).strip()


def _num(s):
    """Cells arrive as Excel formula literals: =T("415")."""
    m = re.search(r'=T\("(\d+)"\)|(\d+)', s or "")
    return int(m.group(1) or m.group(2)) if m else None


def classify(letter):
    v = _clean(letter).lower()
    if "ceased to evaluate" in v:
        return "withdrawn"
    if "does not provide a basis" in v:
        return "rejected"
    if "no questions" in v:
        return "no questions"
    if "pending" in v:
        return "pending"
    return "unknown"


def load(path=None):
    path = path or latest_capture()
    raw = open(path, encoding="latin-1").read()
    rows = list(csv.DictReader(io.StringIO(raw.split("\n", 2)[2])))
    out = {}
    for r in rows:
        g = _num(r["GRAS Notice (GRN) No."])
        if g is None:
            continue
        closed = (r.get("Date of closure") or "").strip()
        out[g] = {
            "grn": g,
            "substance": _clean(r.get("Substance")),
            "notifier": _clean(r.get("Notifier")),
            "outcome": classify(r.get(LETTER)),
            "closed_year": int(closed[-4:]) if closed[-4:].isdigit() else None,
            "next": _num(r.get("Resubmitted")),
            "prev": _num(r.get("Resubmission")),
        }
    return out, os.path.basename(path)


def final(rec, by):
    """Walk the retry chain to its last notice, guarding against cycles."""
    seen = set()
    while rec["next"] and rec["next"] in by and rec["next"] not in seen:
        seen.add(rec["grn"])
        rec = by[rec["next"]]
    return rec


def chain(rec, by):
    out, seen = [], set()
    cur = rec
    while cur and cur["grn"] not in seen:
        seen.add(cur["grn"])
        out.append(cur)
        cur = by.get(cur["next"]) if cur["next"] else None
    return out


def heads(by):
    """Notices that are not themselves a resubmission — one per substance."""
    return [v for v in by.values() if not v["prev"]]


import html as _html

# Substance category, inferred from the notice's own substance name. Ordered:
# first match wins, so the specific rules sit above the general ones.
CATS = [
    ("Recombinant protein", r"produced by <?i?>?escherichia|produced by e\. ?coli"
                            r"|purified from rice|recombinant|expressing"),
    ("Enzyme preparation", r"\benzyme\b|ase preparation|\bamylase|\bxylanase"
                           r"|\bprotease|\blipase|\bglucanase|sucrase|lysozyme"
                           r"|lactoperoxidase"),
    ("Probiotic, culture or phage", r"lactobacill|bifidobact|\bbacillus\b|phage"
                                    r"|metschnikowia|carnobacterium|saccharomyces"
                                    r"|colicin|lallemand|strain [A-Z0-9]"),
    ("Microbial or algal biomass and oil", r"algal|\balgae|euglena|chlorella|spirulina"
                                           r"|schizochytrium|aurantiochytrium|mortierella"
                                           r"|mycelial|mycelia|biomass|haematococcus"
                                           r"|galdieria|arthrospira|phycocyanin|paramylon"
                                           r"|lemnaceae|wolffia|fungal oil"),
    ("Novel sugar or oligosaccharide", r"oligosacchar|fucosyllactose|sialyllactose"
                                       r"|lacto-<?i?>?n</?i?>?-tetraose|cellobiose"
                                       r"|trehalose|psicose|polydextrose|arabinose"
                                       r"|glucosamine|maltosyl|starch hydrolysate"),
    ("Dairy or animal fraction", r"whey|casein|lactoglobulin|lactoferrin|colostral"
                                 r"|osteopontin|plasma protein|animal blood|eggshell"
                                 r"|chitosan|chitin|fish meal|shrimp"),
    ("Lipid or oil fraction", r"\boil\b|triglycerid|phosphatidyl|lipid|fatty acid"
                              r"|\bwax\b|lecithin|menhaden"),
    ("Botanical extract", r"extract|leaf|root|fruit|ginseng|mulberry|olive|tea"
                          r"|resveratrol|piperine|isoflavone|ginkgo|guayusa"
                          r"|ashitaba|miracle fruit|tomato|grapefruit|agave|gac"),
    ("Fibre or polysaccharide", r"fib(re|er)|\bgum\b|cellulose|\bglucan|inulin"
                                r"|hull|bran|flour|\bhusk"),
    ("Synthetic or defined chemical", r"chloride|copolymer|poloxamer|pyrophosphate"
                                      r"|ethylenediamine|butanediol|carnitine|caffeine"
                                      r"|theobromine|picolinate|lactate|folate"
                                      r"|butyric|glycerophosphorylcholine|carbon monoxide"
                                      r"|apoaequorin|menaquinone|spermidine|hyaluronate"),
]


def clean_substance(s):
    return _html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def category(substance):
    h = clean_substance(substance).lower()
    for name, pat in CATS:
        if re.search(pat, h):
            return name
    return "Other"


# ---------------------------------------------------------------- animal food

def latest_animal_capture():
    files = sorted(glob.glob(os.path.join(RAW, "agras-notices-*.html")))
    if not files:
        raise SystemExit("no animal capture — run capture.py first")
    return files[-1]


def load_animal(path=None):
    """Parse the rendered AGRN inventory table. No export exists for this one."""
    path = path or latest_animal_capture()
    h = open(path, encoding="utf-8", errors="replace").read()
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S):
        cells = [" ".join(html.unescape(re.sub(r"<[^>]+>", " ", c)).split())
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
        if len(cells) < 7:
            continue
        m = re.match(r"\s*(\d+)", cells[0])
        if not m:
            continue
        out.append({
            "agrn": int(m.group(1)), "notifier": cells[1], "substance": cells[2],
            "use": cells[3], "species": cells[4], "filed": cells[5],
            "outcome": classify(cells[6]),
        })
    return out, os.path.basename(path)


# Purpose, from the notice's own Intended Use text. Ordered; first match wins.
USES = [
    ("Phosphorus availability (phytase)", r"phytin|phytase|phosph"),
    ("Synthetic amino acid", r"l-(threonine|valine|tryptophan|arginine|isoleucine"
                             r"|lysine|methionine)|amino acid"),
    ("Direct-fed microbial", r"viable microorganism|direct-fed micro|gut microflora"
                             r"|probiotic"),
    ("Ethanol co-product", r"fermentation and distillation|fermentation of corn"
                           r"|distillers"),
    ("Viscosity / NSP enzyme", r"viscosity|non-starch|mannanase|xylanase|glucanase"),
    ("Omega-3 / DHA", r"docosahexa|\bdha\b|pufa|polyunsaturated"),
    ("Protein source", r"\bprotein\b"),
    ("Processing aid", r"processing aid|pelleting|binder|anti-caking|anticak"
                       r"|defoam|film coating"),
    ("Pathogen / preservation", r"contamin|pathogen|salmonella|antimicrob|preserv"
                                r"|antioxidant"),
    ("Palatability", r"palatab|flavor|palatant"),
    ("Fibre / glucan", r"fiber|fibre|beta-glucan"),
    ("Nutrient / mineral", r"calcium balance|nutrient|vitamin|source of the nutrient"),
    ("Energy source", r"energy"),
]

# "Utility information not evaluated for GRAS" is a status note, not a use.
NO_UTILITY = "utility information not evaluated"

SPECIES = [
    ("Pets", r"cat\b|cats|dog|companion|pet"),
    ("Poultry", r"poultry|chicken|broiler|layer|turkey"),
    ("Swine", r"swine|pig\b|pork"),
    ("Cattle / ruminant", r"cattle|cow|dairy|calve|beef|ruminant|bovine"),
    ("Aquaculture", r"salmon|fish|aquacult|shrimp|trout|tilapia"),
    ("Bees", r"honeybee|bee\b"),
]


def purpose(intended_use):
    s = (intended_use or "").lower()
    if NO_UTILITY in s:
        return None                      # FDA did not assess utility; not a use
    for name, pat in USES:
        if re.search(pat, s):
            return name
    return "Other"


def species(intended_species):
    s = (intended_species or "").lower()
    tags = [n for n, p in SPECIES if re.search(p, s)]
    if not tags and re.search(r"all (categories|animal|species)|food-producing", s):
        tags = ["All / food-producing"]
    return tags or ["Unspecified"]
