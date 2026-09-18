#!/usr/bin/env python3
"""Norway: who is still starting companies in which industry, and who has stopped.

    python3 norway_entry.py

WHY ENTRY AND NOT SURVIVAL, FOR NOW. Norway's register removes a company when it is
deleted, exactly as the UK's does. Deleted records remain retrievable by number and carry
a `slettedato`, so the deaths ARE published -- but enumerating them means crawling an
update feed of 16.5 million events, which this connection will not sustain. That is
recorded as the reason rather than presented as an absence.

What needs no deaths at all is ENTRY: registration dates and industry codes are on every
live record, so the share of new companies formed in each sector, year by year, is
answerable from survivors alone. That is also the better instrument for the question this
comparison is really about. A sector can lose most of its output while its surviving
firms die at ordinary rates, because the ones left are the ones that adapted. What shows
a sector emptying out is that nobody starts one any more.

TWO CHOICES THAT MAKE THE COMPARISON HONEST.

  * **AS only.** 432,545 of the register's 1,174,649 entities are aksjeselskap, the
    limited company, which is what Companies House counts. Including sole traders and
    associations would compare a different animal.
  * **Monthly slices.** The API caps paging depth, and a year of AS registrations
    exceeds it. Monthly windows stay under the cap and keep each request small, which
    this link needs.
"""
import collections, csv, datetime as dt, gzip, json, os, subprocess, sys, time

DATA = os.environ.get("FSB_DATA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
OUT = os.path.join(DATA, f"norway-as-{os.environ.get('NO_FROM', '2019')}.csv.gz")
API = "https://data.brreg.no/enhetsregisteret/api/enheter"
UA = "q3dresearch wss +https://github.com/q3dresearch"
# Scoped by default to the years the comparison actually uses. The full series back to
# 1995 is fetchable and was abandoned after ninety minutes returned eleven years: the
# link to this API runs at a few hundred rows a minute from here, and the long Norwegian
# series would have been survivor-biased anyway, with no survival curve to correct it.
START_YEAR = int(os.environ.get("NO_FROM", "2019"))


def get(params, tries=4):
    url = API + "?" + "&".join(f"{k}={v}" for k, v in params.items())
    for i in range(tries):
        r = subprocess.run(["curl", "-sSL", "-m", "120", "-A", UA, url], capture_output=True, text=True)
        try:
            return json.loads(r.stdout)
        except Exception:
            time.sleep(1.5 * (i + 1))
    return {}


def month_slices(y0, y1):
    for y in range(y0, y1 + 1):
        for m in range(1, 13):
            a = dt.date(y, m, 1)
            b = dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)
            if a > dt.date.today():
                return
            yield a.isoformat(), b.isoformat()


def main():
    os.makedirs(DATA, exist_ok=True)
    if os.path.exists(OUT):
        print(f"  have {os.path.basename(OUT)}")
        return 0
    n, empty = 0, 0
    with gzip.open(OUT + ".tmp", "wt", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["orgnr", "registered", "founded", "nace", "nace_text", "bankrupt",
                    "bankrupt_date", "winding_up", "employees", "municipality"])
        for a, b in month_slices(START_YEAR, dt.date.today().year):
            page, total = 0, None
            while True:
                d = get({"organisasjonsform": "AS", "size": 1000, "page": page,
                         "fraRegistreringsdatoEnhetsregisteret": a,
                         "tilRegistreringsdatoEnhetsregisteret": b})
                rows = d.get("_embedded", {}).get("enheter", [])
                total = (d.get("page") or {}).get("totalElements", total)
                if not rows:
                    empty += 1
                    break
                for r in rows:
                    nk = r.get("naeringskode1") or {}
                    adr = r.get("forretningsadresse") or {}
                    w.writerow([r.get("organisasjonsnummer"),
                                r.get("registreringsdatoEnhetsregisteret", ""),
                                r.get("stiftelsesdato", ""),
                                nk.get("kode", ""), (nk.get("beskrivelse") or "")[:60],
                                r.get("konkurs"), r.get("konkursdato", ""),
                                r.get("underAvvikling"),
                                r.get("antallAnsatte", ""),
                                adr.get("kommune", "")])
                n += len(rows)
                page += 1
                if len(rows) < 1000 or page * 1000 >= (total or 0):
                    break
            if a.endswith("-01-01"):
                print(f"    {a[:4]}: {n:,} rows so far", flush=True)
    os.replace(OUT + ".tmp", OUT)
    print(f"  {n:,} limited companies -> {os.path.basename(OUT)} "
          f"({os.path.getsize(OUT)/1e6:.1f} MB), {empty} empty months")
    return 0


if __name__ == "__main__":
    sys.exit(main())
