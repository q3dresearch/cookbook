#!/usr/bin/env python3
"""Award-level fold for the two notice questions (Q19, Q20), cached beside the data.

Not a chart. `chart-11-notice.py` draws it. The fold costs a few minutes, so it caches;
delete `artifacts/data/notice-fy2016.json` to rebuild it from the zip.

Two columns are folded here and nowhere else in the recipe:

- **`fed_biz_opps`** -- whether the opportunity was posted on the public notice site. FAR
  5.101 requires a contracting officer to publicise a proposed action expected to exceed
  $25,000, so the posted and unposted populations differ in size *by rule*. Any comparison
  between them that does not hold size fixed is reading the threshold.
- **`commercial_item_acquisition_procedures`** -- FAR Part 12, the closest thing the register
  carries to a commodity-versus-bespoke axis.

**Everything is counted inside a joint cell**, not as marginal rates, because the whole point
is the controls. The cell is (competed, fbo group, commercial group, product family, size
band) and it carries the award count and the single-bid count. Every rate, every control and
every standardisation in the figure is a sum over that one table, so the pooled number and
the controlled number cannot come from different populations.

Three rules repeated from the rest of the recipe, because getting any of them wrong moves the
answer more than the effect being measured:

**The bid rule.** The FIRST NON-BLANK `number_of_offers_received` across an award's
transactions. A recorded 0 is not a bid count and that award is dropped -- 1,876 of them in
FY2016.

**The competed label set.** Five values, listed in COMPETED below. FOLLOW ON TO COMPETED
ACTION is easy to miss and is worth 137 awards.

**The base.** Rates are computed inside the competed label. Across all awards the uncompeted
ones are 99%+ single-bid whatever else is recorded and they swamp every comparison.
"""
import collections, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L                                                         # noqa: E402

DATA = os.path.join(HERE, "..", "data")
CACHE = os.path.join(DATA, "notice-fy2016.json")
SRC = os.path.join(DATA, "civilian-fy2016.zip")

COMPETED = {"FULL AND OPEN COMPETITION", "COMPETED UNDER SAP",
            "FULL AND OPEN COMPETITION AFTER EXCLUSION OF SOURCES",
            "COMPETITIVE DELIVERY ORDER", "FOLLOW ON TO COMPETED ACTION"}

# FAR 5.101 publicises above $25,000; the simplified acquisition threshold was $150,000 in
# FY2016. Both are band edges so the comparison can be read on either side of a real rule.
EDGES = [2500, 5000, 10000, 25000, 50000, 100000, 150000, 250000, 500000,
         1_000_000, 5_000_000]
BAND_LAB = ["<= $0", "$1-2.5k", "$2.5-5k", "$5-10k", "$10-25k", "$25-50k", "$50-100k",
            "$100-150k", "$150-250k", "$250-500k", "$500k-1m", "$1-5m", "> $5m"]

FAM = {"1": "weapons", "2": "vehicles and engines", "3": "machinery",
       "4": "pipes, pumps, valves", "5": "construction materials",
       "6": "medical, lab and photo equipment", "7": "office, IT and furniture",
       "8": "clothing and subsistence", "9": "fuels and chemicals",
       "A": "research and development", "B": "special studies",
       "C": "architect and engineering", "D": "IT services",
       "E": "purchase of structures", "F": "natural resources",
       "G": "social services", "H": "quality control and testing",
       "J": "equipment maintenance", "K": "equipment modification",
       "L": "technical representative", "M": "facility operation",
       "N": "installation of equipment", "P": "salvage", "Q": "medical services",
       "R": "professional support", "S": "utilities and housekeeping",
       "T": "photographic and mapping", "U": "education and training",
       "V": "transport and travel", "W": "equipment lease",
       "X": "real property lease", "Y": "construction",
       "Z": "maintenance of real property"}


def bids(o):
    """The recipe's rule: first non-blank, and a recorded 0 is not a count."""
    try:
        n = int(float(o))
    except (TypeError, ValueError):
        return None
    return n if n >= 1 else None


def band(v):
    if v <= 0:
        return 0
    for i, e in enumerate(EDGES):
        if v <= e:
            return i + 1
    return len(EDGES) + 1


def fbo_group(v):
    """NOT APPLICABLE is tested before NO, because it starts with it. Getting that order
    wrong silently merges the third population into the second and moves NO from 46.2% to
    44.0% without erroring."""
    v = (v or "").strip().upper()
    if not v:
        return "BLANK"
    if "NOT APPLICABLE" in v:
        return "NOT APPLICABLE"
    if v.startswith("YES"):
        return "YES"
    if v.startswith("NO"):
        return "NO"
    return "OTHER"


def cip_group(v):
    v = (v or "").strip().upper()
    if not v:
        return "BLANK"
    if "NOT USED" in v:
        return "NOT USED"
    if v.startswith("COMMERCIAL ITEM"):
        return "COMMERCIAL"
    return "OTHER"


def sp_group(v):
    """Figure 5's mechanism, collapsed. It is the strongest predictor of a single bid in
    this recipe, so it is carried in the cell and not left to a marginal: an apparent
    posting effect that is really the vehicle effect has to be detectable."""
    v = (v or "").strip().upper()
    if "MULTIPLE AWARD FAIR OPPORTUNITY" in v:
        return "VEHICLE"
    if "SIMPLIFIED" in v:
        return "SIMPLIFIED"
    if "NEGOTIATED" in v:
        return "NEGOTIATED"
    if "SEALED" in v or "TWO STEP" in v:
        return "SEALED"
    return "OTHER"


def awt_group(v):
    v = (v or "").strip().upper()
    for g in ("BPA CALL", "DELIVERY ORDER", "PURCHASE ORDER", "DEFINITIVE CONTRACT"):
        if v == g:
            return g
    return "OTHER"


# positions in the per-award record
PSC, FBO, CIP, CMP, OFF, AWT, SP, PAR, AG, IDV, OBL, BAO, FBOX, CIPX, TX = range(15)


def build():
    acc, ntx = {}, 0
    for r in L.transactions(SRC):
        k = r.get(L.KEY)
        if not k:
            continue
        ntx += 1
        a = acc.get(k)
        if a is None:
            a = acc[k] = ["", "", "", "", "", "", "", "", "", "", 0.0, 0.0, 0, 0, 0]
        a[TX] += 1
        a[OBL] += L.num(r.get("federal_action_obligation")) or 0.0
        bao = L.num(r.get("base_and_all_options_value")) or 0.0
        if bao > a[BAO]:
            a[BAO] = bao
        for dst, c in ((PSC, "product_or_service_code"),
                       (FBO, "fed_biz_opps"),
                       (CIP, "commercial_item_acquisition_procedures"),
                       (CMP, "extent_competed"),
                       (OFF, "number_of_offers_received"),
                       (AWT, "award_type"),
                       (SP, "solicitation_procedures"),
                       (PAR, "parent_award_id_piid"),
                       (AG, "awarding_agency_name"),
                       (IDV, "award_or_idv_flag")):
            v = (r.get(c) or "").strip()
            if v and not a[dst]:
                a[dst] = v
        # does a later transaction disagree with the value we kept?
        v = (r.get("fed_biz_opps") or "").strip()
        if v and a[FBO] and v != a[FBO]:
            a[FBOX] = 1
        v = (r.get("commercial_item_acquisition_procedures") or "").strip()
        if v and a[CIP] and v != a[CIP]:
            a[CIPX] = 1

    # -------------------------------------------------------------- the joint table
    # Two size bands, not one, because the size measure is itself a choice. `obl` is what
    # the award actually drew down inside FY2016 and puts a fifth of awards at or below
    # zero (the base was obligated in an earlier year, or the year holds only
    # de-obligations). `bao` is the largest base_and_all_options_value any of its
    # transactions carried, which is the value at signature -- and the value FAR 5.101's
    # $25,000 synopsis threshold is actually charged on. The controlled answer has to hold
    # under both or the control is a choice of column.
    cells = collections.Counter()   # (comp, fbo, cip, fam, oband, sp, awt) -> awards
    hits = collections.Counter()    # ... -> single-bid awards
    bcells = collections.Counter()  # (comp, fbo, cip, fam, bband) -> awards, for the
    bhits = collections.Counter()   # size-measure robustness check only
    n_awards = len(acc)
    n_usable = n_blankoff = n_zero = 0
    net = 0.0
    fbo_conflict = cip_conflict = 0
    # who the blank-fbo group is: cross-tabs against the things that could define it
    prof = {k: collections.defaultdict(lambda: [0, 0])
            for k in ("award_type", "solicitation_procedures", "extent_competed",
                      "agency", "parent", "idv_flag", "commercial")}
    rawv = {"fed_biz_opps": collections.Counter(),
           "commercial_item_acquisition_procedures": collections.Counter(),
           "extent_competed": collections.Counter()}
    for a in acc.values():
        rawv["fed_biz_opps"][a[FBO] or "(blank)"] += 1
        rawv["commercial_item_acquisition_procedures"][a[CIP] or "(blank)"] += 1
        rawv["extent_competed"][a[CMP] or "(blank)"] += 1
        net += a[OBL]
        fbo_conflict += a[FBOX]
        cip_conflict += a[CIPX]
        raw = a[OFF]
        b = bids(raw)
        if b is None:
            if raw.strip():
                n_zero += 1
            else:
                n_blankoff += 1
            continue
        n_usable += 1
        comp = 1 if a[CMP].upper() in COMPETED else 0
        g = fbo_group(a[FBO])
        c = cip_group(a[CIP])
        fam = (a[PSC][:1].upper() or "?")
        key = (comp, g, c, fam, band(a[OBL]), sp_group(a[SP]), awt_group(a[AWT]))
        cells[key] += 1
        bkey = (comp, g, c, fam, band(a[BAO]))
        bcells[bkey] += 1
        if b == 1:
            hits[key] += 1
            bhits[bkey] += 1
        if comp:
            for field, val in (("award_type", a[AWT] or "(blank)"),
                               ("solicitation_procedures", a[SP] or "(blank)"),
                               ("extent_competed", a[CMP] or "(blank)"),
                               ("agency", a[AG] or "(blank)"),
                               ("parent", "has parent_award_id" if a[PAR]
                                else "no parent_award_id"),
                               ("idv_flag", a[IDV] or "(blank)"),
                               ("commercial", c)):
                s = prof[field][(g, val)]
                s[0] += 1
                s[1] += (b == 1)

    return {
        "meta": {"src": os.path.basename(SRC), "bytes": os.path.getsize(SRC),
                 "transactions": ntx, "awards": n_awards, "usable": n_usable,
                 "zero_offers": n_zero, "blank_offers": n_blankoff,
                 "net_obligation": net,
                 "fbo_conflicting_awards": fbo_conflict,
                 "cip_conflicting_awards": cip_conflict,
                 "band_labels": BAND_LAB, "edges": EDGES,
                 "competed_labels": sorted(COMPETED)},
        "raw_values": {f: dict(c.most_common()) for f, c in rawv.items()},
        "cells": [[list(k), cells[k], hits[k]] for k in sorted(cells)],
        "bao_cells": [[list(k), bcells[k], bhits[k]] for k in sorted(bcells)],
        "profile": {f: [[list(k), v[0], v[1]] for k, v in sorted(d.items())]
                    for f, d in prof.items()},
    }


def load():
    if not os.path.exists(SRC) and os.path.exists(CACHE):
        return json.load(open(CACHE))   # the receipt stands without the zip
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    if not os.path.exists(SRC):
        raise SystemExit("  civilian-fy2016.zip missing - run usa2.py")
    print("  folding civilian-fy2016.zip for fed_biz_opps / commercial item ...", flush=True)
    o = build()
    tmp = CACHE + ".tmp"
    json.dump(o, open(tmp, "w"))
    os.replace(tmp, CACHE)
    return o


# ------------------------------------------------------------------ query helpers
COMP, FBOG, CIPG, FAMI, OBAND, SPG, AWTG = range(7)


def table(d, which="cells"):
    """(comp, fbo, cip, fam, obl band, procedure, award type) -> (n, single).

    `which="bao_cells"` gives the parallel table banded on base_and_all_options_value
    instead of on the obligation, for checking that a control is not a choice of column;
    its key is (comp, fbo, cip, fam, bao band)."""
    return {tuple(c): (n, s) for c, n, s in d[which]}


def total(tab, pred):
    n = k = 0
    for key, (a, b) in tab.items():
        if pred(key):
            n += a
            k += b
    return n, k


def main():
    d = load()
    m = d["meta"]
    tab = table(d)
    print(f"  {m['transactions']:,} transactions, {m['awards']:,} awards, "
          f"{m['usable']:,} usable bid counts")
    print(f"  dropped: {m['zero_offers']:,} recording zero offers, "
          f"{m['blank_offers']:,} blank; net ${m['net_obligation']/1e9:.2f}bn")
    print(f"  awards where a later transaction disagrees: fed_biz_opps "
          f"{m['fbo_conflicting_awards']:,}, commercial item "
          f"{m['cip_conflicting_awards']:,}")
    cn, ck = total(tab, lambda k: k[0] == 1)
    an, ak = total(tab, lambda k: True)
    print(f"  competed and usable: {cn:,} awards, single-bid {ck/cn:.1%}; "
          f"all awards {ak/an:.1%} ({ak:,} = {ak/m['awards']:.1%} of the file)")
    for g in ("YES", "NO", "NOT APPLICABLE", "BLANK", "OTHER"):
        n, k = total(tab, lambda x, g=g: x[0] == 1 and x[1] == g)
        if n:
            print(f"    fed_biz_opps {g:<15} n={n:>7,}  single-bid {k/n:6.1%}")
    for g in ("COMMERCIAL", "NOT USED", "BLANK", "OTHER"):
        n, k = total(tab, lambda x, g=g: x[0] == 1 and x[2] == g)
        if n:
            print(f"    commercial   {g:<15} n={n:>7,}  single-bid {k/n:6.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ---------------------------------------------------------------------------
# Derived stats live here, not in a chart script. Figures 10 and 11 both read them,
# and a figure importing another figure's file by path breaks the moment the
# reading order is renumbered -- which is exactly how this was found.
MIN_FAM = 2000        # families below this many competed awards are not drawn
MIN_CELL = 25         # a stratum needs this many on BOTH sides to be used



# Short aliases for the stratum-key positions, so stats() reads the way the
# figures talk about it. Same tuple as COMP..AWTG above, by another name.
C, FB, CI, FA, OB, SP, AW = COMP, FBOG, CIPG, FAMI, OBAND, SPG, AWTG


def mh(tab, sel_a, sel_b, strat, min_cell=MIN_CELL):
    """Cochran-Mantel-Haenszel risk difference, group A minus group B.

    Each stratum contributes its own difference weighted by n_a*n_b/(n_a+n_b). A stratum
    holding fewer than `min_cell` awards on either side is dropped rather than allowed to
    contribute a 0/1 rate on two awards, and the dropped share is returned so it can be
    stated. Strata are visited in sorted order so the float sum is the same every run.
    """
    A = collections.defaultdict(lambda: [0, 0])
    B = collections.defaultdict(lambda: [0, 0])
    for key, (n, k) in tab.items():
        if sel_a(key):
            c = A[strat(key)]
        elif sel_b(key):
            c = B[strat(key)]
        else:
            continue
        c[0] += n
        c[1] += k
    num = den = var = 0.0
    used = na = nb = ka = kb = dropped = 0
    for s in sorted(set(A) | set(B)):
        a, b = A.get(s, [0, 0]), B.get(s, [0, 0])
        na += a[0]; nb += b[0]; ka += a[1]; kb += b[1]
        if a[0] < min_cell or b[0] < min_cell:
            dropped += a[0] + b[0]
            continue
        used += 1
        w = a[0] * b[0] / (a[0] + b[0])
        pa, pb = a[1] / a[0], b[1] / b[0]
        num += w * (pa - pb)
        den += w
        var += w * w * (pa * (1 - pa) / a[0] + pb * (1 - pb) / b[0])
    if den == 0:
        return None
    se = math.sqrt(var) / den
    return {"diff": num / den, "se": se, "lo": num / den - 1.96 * se,
            "hi": num / den + 1.96 * se, "mde": 2.802 * se, "strata": used,
            "na": na, "nb": nb, "pa": ka / na, "pb": kb / nb,
            "drop": dropped / (na + nb)}


def stats():
    d = load()
    tab = table(d)
    bao = table(d, "bao_cells")
    comp = lambda k: k[C] == 1
    sel = {"post": (lambda k: comp(k) and k[FB] == "YES",
                    lambda k: comp(k) and k[FB] == "NO"),
           "comm": (lambda k: comp(k) and k[CI] == "COMMERCIAL",
                    lambda k: comp(k) and k[CI] == "NOT USED"),
           "bpa": (lambda k: comp(k) and k[FB] == "BLANK",
                   lambda k: comp(k) and k[FB] == "YES")}
    ladders = {}
    for name, (sa, sb) in sorted(sel.items()):
        ladders[name] = [mh(tab, sa, sb, lambda k: 0),
                         mh(tab, sa, sb, lambda k: k[OB]),
                         mh(tab, sa, sb, lambda k: (k[FA], k[OB]))]

    # controls reported in the footer rather than drawn
    extra = {}
    for name, (sa, sb) in sorted(sel.items()):
        extra[name + "_fam"] = mh(tab, sa, sb, lambda k: k[FA])
        extra[name + "_proc"] = mh(tab, sa, sb, lambda k: (k[FA], k[OB], k[SP]))
        # the bao table's key is (comp, fbo, cip, fam, bao band): the selectors only read
        # positions 0-2 and the stratifier reads 3-4, so both work unchanged on it
        extra[name + "_bao"] = mh(bao, sa, sb, lambda k: (k[FA], k[OB]))
    for sp in ("VEHICLE", "SIMPLIFIED", "NEGOTIATED"):
        extra["proc_" + sp] = mh(
            tab, lambda k, s=sp: comp(k) and k[FB] == "YES" and k[SP] == s,
            lambda k, s=sp: comp(k) and k[FB] == "NO" and k[SP] == s,
            lambda k: (k[FA], k[OB]))
    extra["uncompeted"] = mh(tab, lambda k: k[C] == 0 and k[FB] == "YES",
                             lambda k: k[C] == 0 and k[FB] == "NO",
                             lambda k: (k[FA], k[OB]))

    # per family, award size held fixed
    tot = collections.Counter()
    for key, (n, k) in tab.items():
        if comp(key):
            tot[key[FA]] += n
    fams = []
    for f, n in sorted(tot.items(), key=lambda x: (-x[1], x[0])):
        if n < MIN_FAM:
            continue
        row = {"fam": f, "name": FAM.get(f, "other"), "n": n}
        for tag, (sa, sb) in (("post", sel["post"]), ("comm", sel["comm"])):
            row[tag] = mh(tab, lambda k, g=sa, f=f: g(k) and k[FA] == f,
                          lambda k, g=sb, f=f: g(k) and k[FA] == f,
                          lambda k: k[OB], min_cell=15)
        if row["post"] and row["comm"]:
            fams.append(row)
    fams.sort(key=lambda r: r["post"]["diff"])

    n_comp, k_comp = 0, 0
    for key, (n, k) in tab.items():
        if comp(key):
            n_comp += n
            k_comp += k
    bpa = {}
    for (g, v), n, k in d["profile"]["award_type"]:
        bpa.setdefault(v, [0, 0, 0])
        bpa[v][0] += n
        bpa[v][1] += k
        if g == "BLANK":
            bpa[v][2] += n
    blank_tot = sum(v[2] for v in bpa.values())
    return {"d": d, "ladders": ladders, "extra": extra, "fams": fams,
            "n_comp": n_comp, "k_comp": k_comp,
            "bpa_n": bpa["BPA CALL"][0], "bpa_blank": bpa["BPA CALL"][2],
            "bpa_share_of_blank": bpa["BPA CALL"][2] / blank_tot,
            "blank_tot": blank_tot}
