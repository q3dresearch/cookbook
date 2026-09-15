#!/usr/bin/env python3
"""Resolve each register's drug names to an RxNorm INGREDIENT code.

    python rxnorm.py            # resumable; safe to re-run

**String matching is the wrong instrument for a chemical identity question**, and the
first version of this recipe used one. `dexamethason` as a stem happens to work;
`sodium` does not, and it took reading three names side by side to notice that the US
and France meant bicarbonate while Australia meant chloride. A stem cannot know that. A
substance code can.

So every name is resolved twice:

    name  ->  RxCUI          (whatever concept the string names)
    RxCUI ->  ingredient     (/rxcui/{id}/related?tty=IN)

The second call is the one that matters. `dexamethasone sodium phosphate` is RxCUI
48933 and `dexamethasone` is 3264; rolled up to ingredient, both are **3264**. Salt
forms collapse the way a chemist would collapse them, rather than the way a regular
expression guesses.

**It also crosses the language boundary, which is the part a stemmer cannot do
honestly.** RxNav resolves the French `indometacine` and the English `indomethacin` to
the same 5781. The stemmer only got there by deleting a trailing `e` and hoping.

**Names are cleaned before querying, not stemmed.** RxNav is an English vocabulary, so
French salt phrasing fails outright -- `valproate semisodique` returns nothing. The
parenthetical and the salt words come off, the base INN goes in.

**This is enrichment, not capture.** NLM serves RxNav free, without a key, and keeps
its history, so a failed lookup can be retried whenever and no window is closing. The
cache is the only artifact and it is git-ignored.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

sys.path.insert(0, ".")
import shortagelib as S

CACHE = S.DATA / "rxnorm.json"
PAUSE = 0.35
UA = "q3dresearch wss +https://github.com/q3dresearch" + (
    f" ({os.environ['WSS_CONTACT']})" if os.environ.get("WSS_CONTACT") else "")


def clean(name):
    """De-accent and drop salts and dose forms, but keep the whole base name."""
    s = S.deaccent(name or "").lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z\s-]", " ", s)
    s = re.sub(S.SALT, " ", s)
    s = re.sub(S.FORM, " ", s)
    # Trailing presentation words RxNav will not match. Leaving them in cost four
    # substances: "Lamotrigine Tablet, Extended Release" cleaned to
    # "lamotrigine extended release", failed to resolve, and looked exactly like a
    # drug the United States does not have a shortage of.
    s = re.sub(r"\b(extended|delayed|prolonged|immediate|modified|sustained|controlled)\s+"
               r"releas\w*\b", " ", s)
    s = re.sub(r"\bfor\s+(suspension|solution|injection|infusion|reconstitution)\b", " ", s)
    s = re.sub(r"\b(de|du|des|la|le|les|semisodique|sodique|for|with|and|er|xr|sr|la)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _get(url):
    r = subprocess.run(["curl", "-sS", "--max-time", "25", "-A", UA, url],
                       capture_output=True, timeout=40)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {}


def resolve(name):
    """-> (ingredient_rxcui, ingredient_name, [(rxcui, name), ...] for EVERY ingredient).

    The third value is the fix for Q11. An earlier version returned from inside the
    concept loop on the first hit, so `acetaminophen oxycodone` came back as
    `acetaminophen` and two different combinations could collide on one key. A
    combination product is not its first ingredient, and the drop was silent.
    """
    q = urllib.parse.quote(name)
    d = _get(f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={q}&search=2")
    ids = (d.get("idGroup") or {}).get("rxnormId") or []
    if not ids:
        return None, None, []
    time.sleep(PAUSE)
    d = _get(f"https://rxnav.nlm.nih.gov/REST/rxcui/{ids[0]}/related.json?tty=IN")
    allin = [(c["rxcui"], c["name"])
             for grp in ((d.get("relatedGroup") or {}).get("conceptGroup") or [])
             for c in grp.get("conceptProperties", [])]
    allin.sort(key=lambda t: int(t[0]))
    if allin:
        return allin[0][0], allin[0][1], allin
    return ids[0], None, []      # already an ingredient, or no rollup available


def main():
    S.DATA.mkdir(parents=True, exist_ok=True)
    done = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    regs = S.registers()
    want = set()
    for c, d in regs.items():
        for n, _ in d["rows"]:
            q = clean(n)
            if q: want.add(q)
    # An entry without `all` predates the combination-product fix and is re-resolved:
    # its single ingredient may be one of several, and there is no way to tell from here.
    todo = sorted((want - set(done)) | {q for q in want & set(done)
                                        if "all" in done.get(q, {}) is None
                                        or "all" not in done.get(q, {})})
    print(f"  {len(want)} distinct cleaned names, {len(done)} cached, {len(todo)} to resolve", flush=True)
    for i, q in enumerate(todo, 1):
        rx, nm, allin = resolve(q)
        done[q] = {"rxcui": rx, "ingredient": nm,
                   "all": [list(t) for t in allin],
                   "set_key": "+".join(t[0] for t in allin) or None}
        if i % 25 == 0:
            hit = sum(1 for v in done.values() if v.get("rxcui"))
            print(f"    {i}/{len(todo)}  resolved={hit}", flush=True)
            S.write_json_atomic(CACHE, done)
        time.sleep(PAUSE)
    S.write_json_atomic(CACHE, done)
    hit = sum(1 for v in done.values() if v.get("rxcui"))
    combo = sum(1 for v in done.values() if len(v.get("all") or []) > 1)
    print(f"\n  {hit}/{len(done)} names carry an ingredient code ({hit*100//max(len(done),1)}%)")
    print(f"  {combo} are combination products with more than one ingredient")
    print(f"  wrote {CACHE}")



if __name__ == "__main__":
    main()
