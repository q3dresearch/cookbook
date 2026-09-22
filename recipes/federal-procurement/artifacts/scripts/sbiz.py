#!/usr/bin/env python3
"""Shared fold for the two small-business figures.

Not a chart. `chart-1-smallbiz.py` draws where the award base and the dollar base part
company; `chart-2-setasides.py` draws the same gap by department and by programme. Both
need one award-level pass over the same zip, so it lives here.

The split exists because the original plate carried four blocks, one of which was not a
chart at all -- a column of prose reporting a control that came back empty. Per
`webprobes/doctrine/one-chart-per-plate.md` that prose belongs in the recipe, and two
subjects sharing an expensive fold is an argument for sharing code, not a canvas.
"""
import bisect, collections, csv, io, math, os, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import load as L, plate                                                  # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID, FAINT   # noqa: E402

SRC = os.path.join(HERE, "..", "data", "civilian-fy2016.zip")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#7d8891"
SMALL = "SMALL BUSINESS"
NONE_SA = "NO SET ASIDE USED."
SHORT = {"Department of Veterans Affairs": "Veterans Affairs",
         "Department of Justice": "Justice",
         "Department of Health and Human Services": "Health & Human Svcs",
         "Department of Homeland Security": "Homeland Security",
         "Department of Agriculture": "Agriculture",
         "Department of the Interior": "Interior",
         "Department of Commerce": "Commerce",
         "Department of Transportation": "Transportation",
         "National Aeronautics and Space Administration": "NASA",
         "Environmental Protection Agency": "EPA",
         "Department of Energy": "Energy"}
SA_SHORT = {NONE_SA: "no set-aside",
            "": "field left blank",
            "SMALL BUSINESS SET ASIDE - TOTAL": "small business, total",
            "SERVICE DISABLED VETERAN OWNED SMALL BUSINESS SET-ASIDE": "service-disabled veteran",
            "8(A) SOLE SOURCE": "8(a) sole source",
            "8A COMPETED": "8(a) competed",
            "SMALL BUSINESS SET ASIDE - PARTIAL": "small business, partial",
            "HUBZONE SET-ASIDE": "HUBZone",
            "INDIAN SMALL BUSINESS ECONOMIC ENTERPRISE": "Indian small business",
            "WOMEN OWNED SMALL BUSINESS": "women-owned",
            "SDVOSB SOLE SOURCE": "SDVOSB sole source",
            "VETERAN SET ASIDE": "veteran"}



def read_awards(path):
    """One pass over the transaction file; one record per contract_award_unique_key.

    Business size and set-aside are taken from the base action (modification_number 0 or
    blank), falling back to the first non-empty value seen. Obligation is the sum over every
    transaction, negatives included.
    """
    cols = ["contract_award_unique_key", "federal_action_obligation",
            "contracting_officers_determination_of_business_size", "type_of_set_aside",
            "awarding_agency_name", "potential_total_value_of_award", "modification_number"]
    z = zipfile.ZipFile(path)
    name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
    acc, tx, disagree, negtx, modtx, postx = {}, 0, 0, 0, 0, 0.0
    with z.open(name) as f:
        rd = csv.reader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"))
        head = next(rd)
        K, FA, BS, SA, AG, PT, MN = [head.index(c) for c in cols]
        for row in rd:
            tx += 1
            k = row[K]
            if not k:
                continue
            fa = L.num(row[FA]) or 0.0
            if fa < 0:
                negtx += 1
            else:
                postx += fa
            if (row[MN] or "") not in ("0", ""):
                modtx += 1
            a = acc.get(k)
            if a is None:
                a = acc[k] = [row[BS].strip(), row[SA].strip(), row[AG].strip(), 0.0, 0]
            elif row[BS].strip() and a[0] and row[BS].strip() != a[0]:
                disagree += 1
            if (row[MN] or "") in ("0", ""):
                if row[BS].strip():
                    a[0] = row[BS].strip()
                if row[SA].strip():
                    a[1] = row[SA].strip()
            else:
                if not a[0] and row[BS].strip():
                    a[0] = row[BS].strip()
                if not a[1] and row[SA].strip():
                    a[1] = row[SA].strip()
            a[3] += fa
            if L.num(row[PT]) is not None:
                a[4] = 1
    return ([{"size": a[0], "sa": a[1], "ag": a[2], "ob": a[3], "ceil": a[4]}
             for a in acc.values()],
            {"tx": tx, "disagree": disagree, "neg": negtx, "mod": modtx, "pos": postx})


def logistic(data, iters=80):
    """Newton-Raphson for P(small) = f(b0 + b1 * log10 obligation). Bounded model, bounded
    outcome -- a linear fit on a share manufactures a null at the floor."""
    b0 = b1 = 0.0
    for _ in range(iters):
        g0 = g1 = h00 = h01 = h11 = 0.0
        for x, y in data:
            p = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, b0 + b1 * x))))
            g0 += y - p
            g1 += (y - p) * x
            w = p * (1 - p)
            h00 += w
            h01 += w * x
            h11 += w * x * x
        det = h00 * h11 - h01 * h01
        if abs(det) < 1e-12:
            break
        d0 = (h11 * g0 - h01 * g1) / det
        d1 = (-h01 * g0 + h00 * g1) / det
        b0 += d0
        b1 += d1
        if abs(d0) < 1e-11 and abs(d1) < 1e-11:
            break
    return b0, b1


def med(v):
    v = sorted(v)
    n = len(v)
    return v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])

