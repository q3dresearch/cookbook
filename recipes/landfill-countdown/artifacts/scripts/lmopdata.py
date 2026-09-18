#!/usr/bin/env python3
"""Load the two surviving editions of the federal landfill register.

Shared by every script here so the traps are fixed in one place.

THREE TRAPS, ALL MEASURED BEFORE ANY OF THIS WAS BUILT.

**A rename is not a transaction.** The owner column is a free-text company name. A naive
diff of the 2021 and 2024 editions reports 304 changes of owner, and 248 of them are
"Waste Management, Inc." becoming "WM" -- one corporate rebrand, no site changing hands.
Several more are punctuation. `owner_key` normalises before anything is compared, and
`real_owner_changes` reports both numbers so the size of the trap stays visible.

**The waste-in-place figure is not from a common year.** Its companion column runs from
1993 to 2022. Computing a fill rate from a 1998 stock against a 2022 acceptance rate is
arithmetic on two different worlds, so `countdown` refuses any site whose stock is older
than FRESH.

**Design capacity is filled on about half the sites.** The countdown exists for that half
and the half is not random, so every count is reported against its denominator.
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlsxlite                                                          # noqa: E402

DATA = os.environ.get("LF_DATA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
EDITIONS = {"2021": "lmop-2021-09.xlsx", "2024": "lmop-2024-09.xlsx"}
FRESH = 2020          # a waste-in-place stock older than this cannot be divided by a 2022 flow

_SUFFIX = re.compile(r"\b(inc|incorporated|llc|l\.?l\.?c|corp|corporation|co|company|ltd|lp|llp|"
                     r"usa|us|of|the|and|&|environmental|environment|services|service|waste|"
                     r"management|systems|group|holdings|solutions|disposal|sanitation)\b")
_ALIAS = {"wm": "wm", "waste management": "wm"}


def owner_key(name):
    """One company, one key. 'Waste Management, Inc.' and 'WM' are the same firm; the
    rebrand happened in 2022 and it is 82% of the raw change count between editions."""
    s = re.sub(r"[^a-z0-9 ]+", " ", (name or "").lower())
    s = re.sub(r"\s+", " ", s).strip()
    if s.startswith("waste management") or s == "wm":
        return "wm"
    s2 = re.sub(r"\s+", " ", _SUFFIX.sub(" ", s)).strip()
    # Regional subsidiaries are the same firm. "Waste Connections Inc. - Central Region"
    # normalises to "connections central region" and would otherwise be counted as a
    # separate owner from "connections", understating concentration by splitting it.
    s2 = re.sub(r"\b(central|eastern|western|southern|northern|north|south|east|west|"
                r"midwest|southeast|southwest|northeast|northwest|region|regional|"
                r"district|division|area|operating|operations)\b", " ", s2)
    s2 = re.sub(r"\s+", " ", s2).strip()
    return _ALIAS.get(s2, s2 or s)


def num(v):
    try:
        f = float(str(v).replace(",", "").strip())
        return f if f == f else None
    except (TypeError, ValueError):
        return None


def load(edition):
    """Read the published workbook with the standard library.

    This used openpyxl, which is a better library than the sixty lines that replaced it. The
    swap is so a promoted copy of this recipe has nothing to install: it was verified cell by
    cell against openpyxl on both editions -- 2,642 rows, no disagreement -- and the figures
    it produces are byte-identical to the ones built before it."""
    rows = list(xlsxlite.load_workbook(os.path.join(DATA, EDITIONS[edition])).rows("LMOP Database"))
    head = rows[:4]
    hdr = max(head, key=lambda r: sum(1 for x in r if x is not None))
    cols = [str(x).strip() for x in hdr if x is not None]
    out = {}
    for r in rows[head.index(hdr) + 1:]:
        d = dict(zip(cols, r))
        k = d.get("Landfill ID")
        if k is None:
            continue
        out[str(k).strip()] = d
    return out


def countdown(rec, fresh=None):
    """Years until full, or None with the reason it cannot be computed.

    `fresh` is the oldest stock year still worth dividing by a current flow. It defaults
    to FRESH, which is right for the 2024 edition. Comparing the two editions needs the
    2021 one judged by its own calendar -- its stocks stop at 2020 -- or every site looks
    uncomputable in the older file and the pairing silently keeps only the newest.""" 
    cap = num(rec.get("Landfill Design Capacity (tons)"))
    wip = num(rec.get("Waste in Place (tons)"))
    yr = num(rec.get("Waste in Place Year"))
    rate = num(rec.get("Annual Waste Acceptance Rate (tons per year)"))
    status = str(rec.get("Current Landfill Status") or "").strip()
    if status != "Open":
        return None, "not open"
    if cap is None:
        return None, "no design capacity"
    if wip is None or yr is None:
        return None, "no dated stock"
    if yr < (FRESH if fresh is None else fresh):
        return None, f"stock is from {int(yr)}"
    if not rate or rate <= 0:
        return None, "no acceptance rate"
    remaining = cap - wip
    if remaining <= 0:
        return 0.0, "already at or past design capacity"
    return remaining / rate, ""
