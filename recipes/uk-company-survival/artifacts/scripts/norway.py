#!/usr/bin/env python3
"""Norway: the register that publishes its own deletions, with industry codes.

    python3 norway.py

Norway is the sector comparison. It carries NACE industry codes, which UK SIC 2007 is
derived from, so the two classify a company the same way -- that is the join that makes a
cross-country sector comparison possible at all.

It is also a better-built register than either of the others here. Deletion is an
explicit dated EVENT in an update feed rather than something inferred by differencing
snapshots, and bankruptcy is a flag of its own rather than something estimated. So the
UK's central workaround is unnecessary here, which is itself worth showing.

WHAT IS NOT COMPARABLE, AND WHY THE LEVELS ARE NOT THE POINT. A company's chance of
being struck off depends on that country's filing deadlines and enforcement practice.
The UK hazard peaks at one to two years because first accounts fall due around twenty-one
months; that is company law, not economics. So the comparison this recipe makes is of the
ORDERING of sectors within each country, never of the levels between them -- the same
logic that made the check against the official UK statistics meaningful.
"""
import gzip, json, os, subprocess, sys, time

DATA = os.environ.get("FSB_DATA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
UA = "q3dresearch wss +https://github.com/q3dresearch"
BULK = "https://data.brreg.no/enhetsregisteret/api/enheter/lastned"
OUT = os.path.join(DATA, "norway-enheter.json.gz")


def get(url, dest, accept=None):
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print(f"  have {os.path.basename(dest)} ({os.path.getsize(dest)/1e6:.0f} MB)")
        return
    cmd = ["curl", "-sSL", "-m", "1800", "-A", UA]
    if accept:
        cmd += ["-H", f"Accept: {accept}"]
    cmd += [url, "-o", dest]
    subprocess.run(cmd, check=True)
    print(f"  fetched {os.path.basename(dest)} ({os.path.getsize(dest)/1e6:.1f} MB)")


def main():
    os.makedirs(DATA, exist_ok=True)
    print("  the live register, all entities, one gzipped JSON array")
    get(BULK, OUT, accept="application/vnd.brreg.enhetsregisteret.enhet.v2+gzip")
    with gzip.open(OUT, "rt", encoding="utf-8") as fh:
        rows = json.load(fh)
    print(f"  {len(rows):,} entities")
    k = rows[0]
    print("  fields on a record:", ", ".join(sorted(k)[:14]))
    n_nace = sum(1 for r in rows if r.get("naeringskode1"))
    n_reg = sum(1 for r in rows if r.get("registreringsdatoEnhetsregisteret"))
    n_bank = sum(1 for r in rows if r.get("konkurs"))
    n_avv = sum(1 for r in rows if r.get("underAvvikling"))
    print(f"  with a NACE code: {n_nace:,} ({n_nace/len(rows):.0%})")
    print(f"  with a registration date: {n_reg:,} ({n_reg/len(rows):.0%})")
    print(f"  flagged bankrupt: {n_bank:,} | under liquidation: {n_avv:,}")
    import collections
    forms = collections.Counter((r.get("organisasjonsform") or {}).get("kode") for r in rows)
    print("  legal forms:", forms.most_common(6))
    yrs = collections.Counter((r.get("registreringsdatoEnhetsregisteret") or "")[:4] for r in rows)
    print("  registration years, oldest:", sorted(y for y in yrs if y)[:3],
          "| newest:", sorted(y for y in yrs if y)[-3:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
