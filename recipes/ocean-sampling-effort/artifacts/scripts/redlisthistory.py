#!/usr/bin/env python3
"""Every published Red List version GBIF still hosts, and the transitions between them.

    python3 redlisthistory.py      # download, cache, diff (~180 MB, several minutes)

THIS IS A CAPTURE WEARING A RECIPE'S CLOTHES, and it has been moved. Downloading bytes that
perish and keeping them is `wss` work, not larder work: the recipe owns questions, wss owns
bytes over time. The same archive is now captured quarterly by `wss/wss-redlist`, with gates, a
manifest, and a parser that fails loudly on all four traps recorded below. This script stays
only so the recipe reproduces standalone; once that repo is capturing, read its observations
instead and delete this.

OBIS's `checklist/redlist` returns a current state with no assessment date, no version and no
previous category, so species entering or leaving threatened status is unanswerable from it.
The obvious conclusion -- start capturing monthly and ask again in a year -- turns out to be
wrong, because the history is **already published**.

GBIF hosts the IUCN Red List as a Darwin Core archive under CC-BY at
`hosted-datasets.gbif.org/datasets/iucn/`, and the directory is listable. It holds nine dated
archives as well as `iucn-latest.zip`, spanning Red List versions **2020-3 to 2026-1**. Each is
~20 MB, needs no token, and carries `threatStatus` in the Distribution extension with the full
category set -- Least Concern, Near Threatened and Data Deficient included, which is exactly
what OBIS drops. 178,011 taxa carry a status; 310,544 are listed in total.

**The mirror is incomplete, and that is the point.** Present: 2020-3, 2021-2, 2021-3, 2022-1,
2022-1_2022-08-12, 2024-2, 2025-1, 2025-2, 2026-1. Missing: everything between 2022-1 and
2024-2, so a transition measured across that pair spans several real releases and cannot be
attributed to one. GBIF keeps what GBIF keeps. Those versions are not recoverable here by any
amount of later work -- which is the argument for capturing the current one on a schedule
rather than trusting a mirror to keep it.

**The join key is genus plus epithet, never scientificName.** IUCN writes the authorship into
`scientificName` -- "Agrotis procellaris Meyrick 1900", "Pradosia argentea (Kunth) T.D.Penn." --
and OBIS writes a bare binomial. Joining the two on that field matched **0 of 6,757** category
changes to a marine species, which reads as a fact about the ocean and is a fact about string
formatting. The archive carries `genus` and `specificEpithet` as separate fields; those are used.

**The Darwin Core schema is not stable across versions.** In `iucn-2020-3` the Distribution
extension carries threatStatus at index 4; in `iucn-2026-1` it is at index 5, with locality and
countryCode swapped and establishmentMeans moved. Every field is therefore located by term from
each archive's own `meta.xml`, never by position, and a version that parses to zero categories
aborts the run rather than being diffed -- an empty version would read as 178,011 transitions.

**The mirror drops transfers.** Downloads of the same URL fail at arbitrary points -- 111 KB,
985 KB, 7 MB of a 14.1 MB file -- and then succeed in four seconds on the next attempt. It is
not a size limit and not a deterministic bug; three attempts was simply not enough. Each fetch
now gets eight, with exponential backoff, and each attempt is verified independently.

**A download is not a file until it is checked.** The first run accepted a 124,685-byte
truncation of the 14.1 MB 2020-3 archive, because a size floor of 1 MB was doing duty as a
validity check and a truncated zip still has a valid header. Every fetch now compares bytes
read against the server's Content-Length and opens the archive before it is allowed into the
cache; nothing reaches the cache under a different name than what was verified.

**Casing is not clean.** `threatStatus` carries both "Near Threatened" and "near threatened",
"Least Concern" and "least concern", plus "conservation dependent" from the pre-2001 system.
Values are normalised to the v3.1 codes before anything is diffed; an unnormalised diff would
invent thousands of transitions.

**The assessment year is also recoverable per species**, from the DOI inside
`bibliographicCitation`: `...2013-1.RLTS.T133722A512509.en` gives both the Red List version the
assessment appeared in and the assessment id. 290,544 of 310,544 taxa carry one.
"""
import collections, json, os, re, socket, sys, time, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("OBIS_DATA") or os.path.join(HERE, "..", "data")
CACHE = os.path.join(DATA, "iucn")
OUT = os.path.join(DATA, "redlisthistory.json")
BASE = "https://hosted-datasets.gbif.org/datasets/iucn/"
UA = "web-snapshots research bot (dl.eeee.nv@gmail.com)"

# v3.1 codes. The pre-2001 "conservation dependent" has no v3.1 equivalent and is kept as its
# own token rather than folded into anything, because folding it would fabricate a transition.
NORM = {
    "least concern": "LC", "near threatened": "NT", "vulnerable": "VU",
    "endangered": "EN", "critically endangered": "CR", "extinct": "EX",
    "extinct in the wild": "EW", "data deficient": "DD",
    "conservation dependent": "CD", "lower risk/conservation dependent": "CD",
    "lower risk/near threatened": "NT", "lower risk/least concern": "LC",
}
THREATENED = {"CR", "EN", "VU"}
VERKEY = re.compile(r"iucn-(\d{4})-(\d)")


def versions():
    socket.setdefaulttimeout(60)
    html = urllib.request.urlopen(urllib.request.Request(
        BASE, headers={"User-Agent": UA}), timeout=60).read().decode("utf-8", "replace")
    zips = sorted(set(re.findall(r'href="(iucn-[^"]+\.zip)"', html)))
    dated = [z for z in zips if VERKEY.match(z)]
    return sorted(dated, key=lambda z: (VERKEY.match(z).group(1), VERKEY.match(z).group(2), z))


def ok_zip(p):
    """A cached file counts only if it opens AND carries the two members we read. The first
    run accepted a 124,685-byte truncation of a 14.1 MB archive: it had a valid zip header,
    so a size floor let it through and the parser blew up three lines later."""
    try:
        z = zipfile.ZipFile(p)
        return {"taxon.txt", "distribution.txt"} <= set(z.namelist()) and z.testzip() is None
    except Exception:                                                    # noqa: BLE001
        return False


def fetch(name, tries=8):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, name)
    if os.path.exists(p) and ok_zip(p):
        return p, False
    last = None
    for attempt in range(tries):
        tmp = p + ".part"
        got = 0
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    BASE + name, headers={"User-Agent": UA}), timeout=900) as r:
                want = int(r.headers.get("Content-Length") or 0)
                with open(tmp, "wb") as fh:
                    while True:
                        b = r.read(1 << 20)
                        if not b:
                            break
                        fh.write(b)
                        got += len(b)
            # the server says how many bytes it is sending; a short read is a failed fetch,
            # not a small file, and must never reach the cache
            if want and got != want:
                last = f"short read {got:,} of {want:,}"
                raise OSError(last)
            os.replace(tmp, p)
            if not ok_zip(p):
                last = "downloaded bytes are not a usable archive"
                os.remove(p)
                raise OSError(last)
            return p, True
        except Exception as e:                                           # noqa: BLE001
            last = last or f"{type(e).__name__}: {e}"
            for f in (tmp,):
                if os.path.exists(f):
                    os.remove(f)
            if attempt == tries - 1:
                raise SystemExit(f"  {name}: giving up after {tries} attempts -- {last}")
            print(f"      retry {attempt+1}/{tries-1} after {last}", flush=True)
            time.sleep(min(2 ** attempt, 20))
            last = None
    raise SystemExit(f"  {name}: {last}")


def schema(z):
    """Field index by term, per file, read from meta.xml. Never assume a position: the
    Distribution extension puts threatStatus at index 4 in the 2020-3 archive and index 5 in
    2026-1, with locality and countryCode swapped as well. Reading index 5 from the old
    archives yields establishmentMeans, which normalises to nothing -- so the failure shows up
    as a version with zero categories, and a diff against it would have invented a transition
    for every one of the 178,011 taxa."""
    meta = z.read("meta.xml").decode("utf-8", "replace")
    out = {}
    for m in re.finditer(r"<(core|extension)[^>]*>(.*?)</\1>", meta, re.S):
        body = m.group(2)
        loc = re.search(r"<location>([^<]+)</location>", body)
        if not loc:
            continue
        out[loc.group(1)] = {f.group(2).split("/")[-1]: int(f.group(1))
                             for f in re.finditer(
                                 r'<field\s+index="(\d+)"\s+term="([^"]+)"', body)}
    return out


def read(p):
    """taxonID -> (scientificName, code). Names come from the core, statuses from the
    Distribution extension, which is the only place a category appears."""
    z = zipfile.ZipFile(p)
    sch = schema(z)
    T = sch.get("taxon.txt", {})
    ti, gi, si = T.get("scientificName"), T.get("genus"), T.get("specificEpithet")
    di = sch.get("distribution.txt", {}).get("threatStatus")
    if ti is None or di is None or gi is None or si is None:
        raise SystemExit(f"  {os.path.basename(p)}: meta.xml is missing a needed term "
                         f"(scientificName={ti} genus={gi} specificEpithet={si} "
                         f"threatStatus={di}) -- schema changed again")
    names, status = {}, {}
    with z.open("taxon.txt") as fh:
        for line in fh:
            f = line.decode("utf-8", "replace").rstrip("\n").split("\t")
            if len(f) <= max(ti, gi, si):
                continue
            # The key is genus + specificEpithet, NOT scientificName: IUCN's scientificName
            # carries the authorship ("Agrotis procellaris Meyrick 1900") and OBIS's does not,
            # so joining on it gave 0 of 6,757 changes matching a marine species -- a join
            # failure that looks exactly like a finding about the ocean.
            g, sp = f[gi].strip(), f[si].strip()
            names[f[0]] = f"{g} {sp}" if g and sp else f[ti].strip()
    with z.open("distribution.txt") as fh:
        for line in fh:
            f = line.decode("utf-8", "replace").rstrip("\n").split("\t")
            if len(f) > di and f[di].strip():
                c = NORM.get(f[di].strip().lower())
                if c:
                    status[f[0]] = c
    out = {names.get(k, k): v for k, v in status.items() if names.get(k)}
    if not out:
        raise SystemExit(f"  {os.path.basename(p)}: zero categories parsed -- refusing to "
                         f"diff against an empty version")
    return out


def main():
    vs = versions()
    print(f"  {len(vs)} dated archives on the mirror: {', '.join(v[5:-4] for v in vs)}")
    snap = {}
    for v in vs:
        p, fresh = fetch(v)
        print(f"    {v:<30}{'downloaded' if fresh else 'cached':<12}"
              f"{os.path.getsize(p)/1e6:>6.1f} MB", flush=True)
        snap[v[5:-4]] = read(p)
        print(f"      -> {len(snap[v[5:-4]]):,} taxa with a normalised category", flush=True)
    keys = list(snap)
    trans = []
    for a, b in zip(keys, keys[1:]):
        A, B = snap[a], snap[b]
        moved = [{"name": k, "from": A.get(k), "to": B.get(k)}
                 for k in set(A) | set(B) if A.get(k) != B.get(k)]
        both = [m for m in moved if m["from"] and m["to"]]
        trans.append({
            "from_version": a, "to_version": b,
            "taxa_from": len(A), "taxa_to": len(B),
            "added": sum(1 for m in moved if not m["from"]),
            "dropped": sum(1 for m in moved if not m["to"]),
            "changed": len(both),
            "into_threatened": sum(1 for m in both
                                   if m["from"] not in THREATENED and m["to"] in THREATENED),
            "out_of_threatened": sum(1 for m in both
                                     if m["from"] in THREATENED and m["to"] not in THREATENED),
            "moves": both})
        t = trans[-1]
        print(f"  {a} -> {b}: {t['changed']:,} category changes, "
              f"{t['into_threatened']:,} into threatened, "
              f"{t['out_of_threatened']:,} out", flush=True)
    os.makedirs(DATA, exist_ok=True)
    json.dump({"base": BASE, "versions": keys, "transitions": trans,
               "counts": {k: dict(collections.Counter(v.values())) for k, v in snap.items()}},
              open(OUT, "w"), indent=1)
    print(f"\n  written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
