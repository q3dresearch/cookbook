#!/usr/bin/env python3
"""Population and distance features for the landfill register, from Census bulk files.

    python3 geo.py          # fetch, build the two compact tables, report coverage

The register says where a landfill is and nothing about who lives there. Three keyless
Census bulk files fix that. The Census *API* now refuses without a key -- it returns an
HTML page titled "Missing Key" with a 200 -- but `www2.census.gov` serves the same
underlying data as flat files and needs nothing.

    urban areas   2023 gazetteer            GEOID, name, centroid lat/lon
    urban areas   ua_list_all.txt           UACE, name, population
    counties      co-est2023-alldata.csv    state, county, population estimate
    counties      2023 county gazetteer     land area, for density

Two joins, both measured rather than assumed:

**Urban coordinates to urban population joins on GEOID at 88%, not on name.** The
gazetteer is 2020-vintage and the population list is 2010-vintage, and the areas were
renamed in between -- "New York--Newark, NY--NJ--CT" became "New York--Jersey City--
Newark, NY--NJ". Joining on name silently drops the largest urban area in the country,
which is the one that matters most for a proximity measure.

**Landfills to county population joins at 98%.** Every miss is Connecticut, which
replaced its counties with nine planning regions in 2022, so the register still files
by a county the population series no longer publishes. That is a real gap with a date
on it rather than a parsing failure.
"""
import csv, gzip, io, math, os, re, sys, unicodedata, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
UA_OUT = os.path.join(DATA, "census-urban-areas.csv.gz")
CO_OUT = os.path.join(DATA, "census-counties.csv.gz")
AGENT = "public-record-research/1.0 (landfill capacity recipe; contact dl.eeee.nv@gmail.com)"
SRC = {
    "gaz_ua": "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_ua_national.zip",
    "ua_pop": "https://www2.census.gov/geo/docs/reference/ua/ua_list_all.txt",
    "co_pop": "https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/counties/totals/co-est2023-alldata.csv",
    "gaz_co": "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_counties_national.zip",
}
STATES = {
    'AL':'ALABAMA','AK':'ALASKA','AZ':'ARIZONA','AR':'ARKANSAS','CA':'CALIFORNIA','CO':'COLORADO',
    'CT':'CONNECTICUT','DE':'DELAWARE','FL':'FLORIDA','GA':'GEORGIA','HI':'HAWAII','ID':'IDAHO',
    'IL':'ILLINOIS','IN':'INDIANA','IA':'IOWA','KS':'KANSAS','KY':'KENTUCKY','LA':'LOUISIANA',
    'ME':'MAINE','MD':'MARYLAND','MA':'MASSACHUSETTS','MI':'MICHIGAN','MN':'MINNESOTA',
    'MS':'MISSISSIPPI','MO':'MISSOURI','MT':'MONTANA','NE':'NEBRASKA','NV':'NEVADA',
    'NH':'NEW HAMPSHIRE','NJ':'NEW JERSEY','NM':'NEW MEXICO','NY':'NEW YORK','NC':'NORTH CAROLINA',
    'ND':'NORTH DAKOTA','OH':'OHIO','OK':'OKLAHOMA','OR':'OREGON','PA':'PENNSYLVANIA',
    'RI':'RHODE ISLAND','SC':'SOUTH CAROLINA','SD':'SOUTH DAKOTA','TN':'TENNESSEE','TX':'TEXAS',
    'UT':'UTAH','VT':'VERMONT','VA':'VIRGINIA','WA':'WASHINGTON','WV':'WEST VIRGINIA',
    'WI':'WISCONSIN','WY':'WYOMING','DC':'DISTRICT OF COLUMBIA','PR':'PUERTO RICO',
}
# "City" is deliberately NOT stripped. Virginia has 38 independent cities that are
# county-equivalents, several sharing a name with a county -- Richmond City and Richmond
# County are different places. Stripping the word collapsed four of them onto each other.
_SUFFIX = re.compile(r"\s+(County|Parish|Borough|Census Area|Municipality|City and Borough)$", re.I)


CACHE = os.environ.get("LANDFILL_CACHE") or os.path.join(DATA, "census-cache")


def _get(url, tries=4):
    """Fetch, cached on disk by filename, with retries.

    The first version read each URL straight into memory in one call. On a connection
    that drops mid-stream -- which this one does -- a failure anywhere meant starting
    all four files again, and a 1.7 MB fetch had not finished after fifteen minutes.
    Cache each source as it lands so a retry costs only the file that failed."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, url.rsplit("/", 1)[-1])
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return open(path, "rb").read()
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": AGENT})
            with urllib.request.urlopen(req, timeout=90) as r:
                blob = r.read()
            if not blob:
                raise OSError("empty body")
            tmp = path + ".tmp"
            with open(tmp, "wb") as f:
                f.write(blob)
            os.replace(tmp, path)
            return blob
        except Exception as e:                       # noqa: BLE001 - any transport failure retries
            last = e
            print(f"    {os.path.basename(path)}: attempt {attempt+1} failed ({e}), retrying")
    raise RuntimeError(f"could not fetch {url}: {last}")


def _unzip_one(blob):
    z = zipfile.ZipFile(io.BytesIO(blob))
    return z.read(z.namelist()[0]).decode("latin-1")


def _norm(name):
    """Fold to letters and digits only, after dropping the county-type suffix.

    The register writes "Dona Ana" where the Census writes "Dona Ana" with a tilde, and
    "La Salle" where the Census writes "LaSalle". Both are the same parish or county and
    both failed a literal match."""
    s = unicodedata.normalize("NFKD", str(name or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", "", _SUFFIX.sub("", s.strip()).upper())


def county_key(state_abbr, county):
    s = STATES.get(str(state_abbr or "").strip().upper())
    c = _norm(county)
    return (s, c) if s and c else None


def km(p, q):
    la1, lo1, la2, lo2 = map(math.radians, (p[0], p[1], q[0], q[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(min(1, math.sqrt(h)))


def build():
    os.makedirs(DATA, exist_ok=True)
    gaz = {}
    for r in csv.DictReader(io.StringIO(_unzip_one(_get(SRC["gaz_ua"]))), delimiter="\t"):
        r = {k.strip(): (v.strip() if v else v) for k, v in r.items()}
        gaz[r["GEOID"]] = (r["NAME"], float(r["INTPTLAT"]), float(r["INTPTLONG"]))
    pop = {}
    txt = _get(SRC["ua_pop"]).decode("latin-1").splitlines()
    for line in txt[1:]:
        p = re.split(r"\s{2,}", line.strip())
        if len(p) >= 3 and p[0].isdigit():
            try:
                pop[p[0]] = int(p[2])
            except ValueError:
                pass
    with gzip.open(UA_OUT, "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["geoid", "name", "lat", "lon", "pop"])
        n = 0
        for k, (nm, la, lo) in sorted(gaz.items()):
            if k in pop:
                w.writerow([k, nm, f"{la:.5f}", f"{lo:.5f}", pop[k]]); n += 1
    print(f"  urban areas: {n} of {len(gaz)} gazetteer rows carry a population ({n/len(gaz):.0%})")

    land = {}
    for r in csv.DictReader(io.StringIO(_unzip_one(_get(SRC["gaz_co"]))), delimiter="\t"):
        r = {k.strip(): (v.strip() if v else v) for k, v in r.items()}
        land[r["GEOID"]] = float(r["ALAND_SQMI"])
    rows = 0
    with gzip.open(CO_OUT, "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["state", "county", "pop", "sqmi"])
        for r in csv.DictReader(io.StringIO(_get(SRC["co_pop"]).decode("latin-1"))):
            if r["SUMLEV"] != "050":
                continue
            fips = r["STATE"] + r["COUNTY"]
            w.writerow([r["STNAME"].upper(), _norm(r["CTYNAME"]),
                        r["POPESTIMATE2023"], f"{land.get(fips, 0):.2f}"]); rows += 1
    print(f"  counties: {rows} with a 2023 population estimate")
    if rows != len(counties()):
        print(f"  WARNING: {rows - len(counties())} rows collided on the normalised key")


def urban():
    """[(lat, lon, population)] for every urban area that has both."""
    with gzip.open(UA_OUT, "rt", encoding="utf-8") as f:
        return [(float(r["lat"]), float(r["lon"]), int(r["pop"])) for r in csv.DictReader(f)]


def counties():
    """{(STATE, COUNTY): (population, land area in square miles)}"""
    out = {}
    with gzip.open(CO_OUT, "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[(r["state"], r["county"])] = (int(r["pop"]), float(r["sqmi"]))
    return out


def main():
    build()
    sys.path.insert(0, HERE)
    from lmopdata import load
    b = load("2024")
    co = counties()
    rows = [r for r in b.values()
            if str(r.get("Current Landfill Status") or "").strip() in ("Open", "Closed")]
    hit = sum(1 for r in rows if county_key(r.get("State"), r.get("County")) in co)
    miss = sorted({f"{r.get('State')}" for r in rows
                   if county_key(r.get("State"), r.get("County")) not in co})
    print(f"  landfills joining a county: {hit} of {len(rows)} ({hit/len(rows):.0%})")
    print(f"  states with unjoined counties: {', '.join(miss)}")
    print(f"  ({len(urban())} urban areas loaded, "
          f"{sum(1 for _, _, p in urban() if p >= 50000)} of them over 50,000 people)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
