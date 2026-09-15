#!/usr/bin/env python3
"""Three national shortage registers, three formats, one vocabulary.

    FDA   (US)        clean JSON, one row per package NDC
    ANSM  (France)    one HTML table, the INN in square brackets
    TGA   (Australia) a 1.7MB page with no <table> at all

**The join is the whole recipe and it is the part that can silently fail.** A first
pass returned ONE distinct substance for France, which reads exactly like "France
shares nothing with anyone" and was in fact the extractor taking the status column
instead of the drug name. Every parser here therefore reports its own yield, and
`verify.py` fails if a yield collapses.

**Normalisation, and what it costs.** The three registers name the same molecule
differently -- `Dexamethasone Sodium Phosphate Injection`, `[dexamethasone]`,
`Dexamethasone`. So each name is reduced to a stem: de-accented, salts and dose forms
removed, first token kept, then a trailing `e` dropped so the French `indometacine`
and the English `indomethacin` can meet.

That last step over-merges by design, and the direction of the error is what matters:
**it can only create matches, never destroy them**, so the overlap it reports is a
ceiling on precision and a floor on recall. `collisions()` lists every case where two
genuinely different substances land on one stem, and the count is published rather
than hidden.
"""
import glob
import gzip
import json
import os
import re
import unicodedata
from pathlib import Path
from xml.sax.saxutils import escape

RECIPE = Path(__file__).resolve().parents[2]
DATA = RECIPE / "artifacts" / "data"
CHARTS = RECIPE / "artifacts" / "charts"

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, RULE, BASELINE = "#e1e0d9", "#ebeae3", "#c3c2b7"
HOT, COOL, WARM = "#b03a2e", "#1b4f8a", "#c07a1e"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
COUNTRY = {"US": "#0072B2", "FR": "#D55E00", "AU": "#009E73"}

SALT = (r"\b(sodium|potassium|hydrochloride|hcl|sulfate|sulphate|phosphate|acetate|"
        r"succinate|tartrate|maleate|mesylate|besylate|citrate|calcium|magnesium|"
        r"dihydrate|monohydrate|anhydrous|chlorhydrate|bromide|fumarate|lactate)\b")
FORM = (r"\b(injection|injectable|tablet|tablets|capsule|capsules|solution|suspension|"
        r"cream|ointment|inhal\w*|syrup|oral|iv|intravenous|powder|gel|patch|spray|"
        r"drops?|concentrate|infusion|ophthalmic|topical|nasal)\b")


def _archive() -> Path:
    env = os.environ.get("WSS_DRUG_SCARCITY")
    for c in ([Path(env)] if env else []) + [DATA / "wss-drug-scarcity"]:
        if (c / "raw").is_dir():
            return c
    raise SystemExit(
        "cannot find the wss-drug-scarcity capture.\n"
        "  set WSS_DRUG_SCARCITY=/path/to/wss-drug-scarcity, or place it at\n"
        f"  {DATA / 'wss-drug-scarcity'}\n  see README.md -> 'Running this yourself'.")


ARCHIVE = _archive()


def deaccent(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


# Words that are a counter-ion in most products and the ACTIVE ingredient in a few.
# Stripping them blindly turned "calcium chloride dihydrate" and a four-salt
# electrolyte solution into the same stem, "chlorid", which is a false join rather
# than a loose one. When salt-stripping eats the whole name, the original first token
# is kept instead.
COUNTERION = {"chlorid", "chloride", "gluconat", "gluconate", "bicarbonat",
              "bicarbonate", "carbonat", "carbonate", "oxid", "oxide", "hydroxid",
              "hydroxide", "glycerophosphat", "lactat", "lactate"}


def stem(s):
    """Reduce a product string to a joinable substance stem. Over-merges on purpose."""
    raw = deaccent(s or "").lower()
    raw = re.sub(r"\(.*?\)", " ", raw)
    raw = re.sub(r"[^a-z\s]", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    if not raw:
        return ""

    def fold(w):
        return re.sub(r"e$", "", w) if len(w) > 5 else w

    t = re.sub(SALT, " ", raw)
    t = re.sub(FORM, " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return fold(raw.split()[0])
    w = fold(t.split()[0])
    if w in COUNTERION:
        first = fold(raw.split()[0])
        return first if first not in COUNTERION else w
    return w


def write_json_atomic(path, obj):
    """Temp file then rename, so a kill cannot corrupt a resumable cache."""
    tmp = Path(path).with_suffix(Path(path).suffix + ".tmp")
    tmp.write_text(json.dumps(obj))
    os.replace(tmp, path)


def latest(source):
    """The newest FILE of a source. Right for a one-request source; WRONG for a
    paginated one -- see latest_run()."""
    fs = sorted(p for p in glob.glob(str(ARCHIVE / "raw" / source / "**" / "*"), recursive=True)
                if os.path.isfile(p) and not p.endswith(".gitkeep"))
    return fs[-1] if fs else None


def latest_run(source, gap_minutes=10):
    """Every file of the newest capture RUN, oldest first.

    A SOURCE CAN BE MORE THAN ONE REQUEST. `fda.shortages.current` is paginated --
    `?limit=1000&skip=0` then `skip=1000` -- so one run writes two files 28 seconds
    apart, and the lexically newest is PAGE TWO. The first published version of this
    recipe read only that file: 619 of 1,619 rows, 148 of 206 substances, and every
    FDA number in it was computed on the smaller, later-sorted half. Nothing looked
    wrong; the row count was plausible and the verifier re-derived from the same
    half. Files are named with a UTC stamp, so a run is the cluster of files within
    ten minutes of the newest one.
    """
    import datetime as _dt
    fs = [p for p in glob.glob(str(ARCHIVE / "raw" / source / "**" / "*"), recursive=True)
          if os.path.isfile(p) and not p.endswith(".gitkeep")]
    stamped = []
    for p in fs:
        m = re.match(r"(\d{8}T\d{6}Z)", os.path.basename(p))
        if m:
            stamped.append((_dt.datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ"), p))
    if not stamped:
        return [latest(source)] if fs else []
    stamped.sort()
    run = [stamped[-1]]
    for when, p in reversed(stamped[:-1]):
        if (run[-1][0] - when).total_seconds() <= gap_minutes * 60:
            run.append((when, p))
        else:
            break
    return [p for _, p in sorted(run)]


def fda_rows():
    """Every row of the newest FDA capture run -- all pages merged."""
    return [r for p in latest_run("fda.shortages.current") for r in json.loads(_read(p))["results"]]


def _read(p):
    return (gzip.open if p.endswith(".gz") else open)(p, "rt", errors="replace").read()


def fda():
    """-> list of (display_name, stem). One row per package NDC, deduplicated by name."""
    run = latest_run("fda.shortages.current")
    p = run[-1]
    rows = fda_rows()
    # One entry per DISTINCT NAME, not per stem. Deduplicating by stem before coding
    # dropped six substances from the ingredient join -- `Methylphenidate Hydrochloride
    # Tablet, Extended Release` lost to `Methylphenidate Film, Extended Release`, whose
    # cleaned name RxNav cannot resolve, so methylphenidate vanished from the
    # three-country overlap while sitting in the README as its own example. The stem
    # is still carried for the string join that negative/2-string-vs-code measures.
    out = {}
    for r in rows:
        n = (r.get("generic_name") or "").strip()
        if n and stem(n):
            out.setdefault(deaccent(n).lower(), n)
    return [(v, stem(v)) for v in out.values()], len(rows), p


def ansm():
    """-> list of (display_name, stem). The INN sits in square brackets at the end."""
    p = latest("ansm.shortages.fr")
    h = _read(p)
    trs = re.findall(r'<tr class="product-item".*?</tr>', h, re.S)
    out, withinn = {}, 0
    for tr in trs:
        txt = re.sub(r"<[^>]+>", " ", tr)
        inn = re.findall(r"\[([^\]]{3,60})\]", txt)
        if not inn:
            continue
        withinn += 1
        n = inn[-1].strip()
        if stem(n):
            out.setdefault(deaccent(n).lower(), n)
    return [(v, stem(v)) for v in out.values()], len(trs), p, withinn


def tga():
    """-> list of (display_name, stem). No <table>; the names are free text lines."""
    p = latest("tga.shortages.au")
    h = re.sub(r"<script.*?</script>", " ", _read(p), flags=re.S)
    lines = [re.sub(r"\s+", " ", x).strip() for x in re.sub(r"<[^>]+>", "\n", h).split("\n")]
    cand = [x for x in lines if 4 < len(x) < 90 and re.match(r"^[A-Za-z][A-Za-z \-'()]+$", x)]
    out = {}
    for n in cand:
        if stem(n):
            out.setdefault(deaccent(n).lower(), n)
    return [(v, stem(v)) for v in out.values()], len(cand), p


def tga_records():
    """Every TGA record as a dict -- the JSON literal the page inlines, 16 fields.

    Status is one letter, read off the data: C current, D discontinued, R resolved,
    A anticipated. Dates arrive as "01 Jan 2013" in shortage_start/shortage_end and
    "16-10-2009" in last_updated. `shortage_end` on a C row is an ANTICIPATED date --
    405 of 409 lie after the capture, one in 2031 -- so "has an end date" must never
    be read as "resolved".
    """
    h = _read(latest("tga.shortages.au"))
    i = h.find('[{"')
    if i < 0:
        return []
    depth, end = 0, None
    for j in range(i, len(h)):
        if h[j] == "[":
            depth += 1
        elif h[j] == "]":
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    return json.loads(h[i:end])


def tga_date(s):
    import datetime as _dt
    try:
        return _dt.datetime.strptime(str(s or "").strip(), "%d %b %Y").date()
    except ValueError:
        return None


def ansm_table():
    """Every ANSM row as its five cells: Statut, Mise à jour, Spécialité,
    Remise à disposition, Domaines médicaux. Dates are French, DD/MM/YYYY."""
    from html import unescape as _u
    h = _read(latest("ansm.shortages.fr"))
    out = []
    for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", h, re.S):
        cells = [_u(re.sub(r"<[^>]*>", "", c)).strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", m.group(1), re.S)]
        if len(cells) >= 4:
            out.append(cells)
    return out


def registers():
    f, fn, fp = fda()
    a, an, ap, ai = ansm()
    t, tn, tp = tga()
    return {"US": {"rows": f, "raw": fn, "file": fp, "label": "FDA (United States)"},
            "FR": {"rows": a, "raw": an, "file": ap, "yield": ai, "label": "ANSM (France)"},
            "AU": {"rows": t, "raw": tn, "file": tp, "label": "TGA (Australia)"}}


# Stems that pass the normaliser and are NOT the same drug, hand-ruled after reading
# the three names side by side. Recorded here rather than silently dropped, because a
# reader needs to know the list was checked. The same pattern as a boilerplate
# exclusion list: guessing is worse than naming.
FALSE_JOIN = {
    "sodium": ("US and FR list sodium BICARBONATE; Australia lists sodium CHLORIDE. "
               "The string 'bicarbonate' does not appear in the TGA capture at all."),
}


def shared(regs, countries=("US", "FR", "AU")):
    """STEM join. Superseded by shared_coded(); kept because chart 2 measures it."""
    sets = [{st for _, st in regs[c]["rows"]} for c in countries]
    out = set.intersection(*sets)
    return sorted(out - set(FALSE_JOIN)), sorted(out & set(FALSE_JOIN))


def sub_key(entry):
    """The substance key: the full ingredient SET, falling back to the single code.

    Q11. Keying on one ingredient merged `acetaminophen oxycodone` into `acetaminophen`,
    which inflated the pairwise overlaps by six -- US-AU alone fell from 62 to 57 once
    combinations stopped matching single-ingredient drugs on a shared first ingredient.
    The three-country overlap is 19 either way.
    """
    return (entry or {}).get("set_key") or (entry or {}).get("rxcui")


def coded(regs):
    """-> {country: {substance_key: (ingredient_name, register_name)}}, keyed on the SET.

    The join key. A name is not a molecule: the United States writes `Rifampin` where
    France writes `rifampicine`, and one word `insulin` covers three molecules. Only a
    substance code survives both, so `FALSE_JOIN` is not needed here -- the code
    rejects sodium chloride against sodium bicarbonate without being told to.
    """
    import json as _j
    from rxnorm import clean as _clean
    rx = _j.loads((DATA / "rxnorm.json").read_text())
    out = {}
    for c, d in regs.items():
        m = {}
        for name, _ in d["rows"]:
            e = rx.get(_clean(name)) or {}
            k = sub_key(e)
            if k:
                m.setdefault(k, (e.get("ingredient") or _clean(name), name))
        out[c] = m
    return out


def shared_coded(regs, countries=("US", "FR", "AU")):
    """Ingredient codes present in every named register."""
    cd = coded(regs)
    return sorted(set.intersection(*[set(cd[c]) for c in countries])), cd


def coded_set(regs):
    """-> ({country: {set_key: (display, register_name, n_ingredients)}}, coverage).

    The Q11 fix. `coded()` keys on ONE ingredient rxcui, so a combination product
    collapses onto its first ingredient and two different combinations can collide
    there -- `acetaminophen oxycodone` and `acetaminophen butalbital caffeine` both
    become `acetaminophen`. This keys on the full ingredient SET instead, so a
    combination is only ever equal to the same combination.

    `coverage` is the share of resolvable names whose cache entry carries the set,
    and it is returned rather than assumed: a cache written before the resolver was
    fixed has no sets at all, and a half-finished re-resolve has some. Silently
    keying on whatever happens to be present is how a partial parse becomes a finding.
    """
    import json as _j
    from rxnorm import clean as _clean
    rx = _j.loads((DATA / "rxnorm.json").read_text())
    out, have, want = {}, 0, 0
    for c, d in regs.items():
        m = {}
        for name, _ in d["rows"]:
            e = rx.get(_clean(name)) or {}
            if not e.get("rxcui"):
                continue
            want += 1
            key = e.get("set_key")
            if key:
                have += 1
            else:
                key = e["rxcui"]          # pre-fix entry: single ingredient, as before
            allin = e.get("all") or []
            m.setdefault(key, (e.get("ingredient") or _clean(name), name, len(allin) or 1))
        out[c] = m
    return out, (have / want if want else 0.0)


def shared_coded_set(regs, countries=("US", "FR", "AU")):
    """Ingredient SETS present in every named register, with the cache coverage."""
    cd, cov = coded_set(regs)
    return sorted(set.intersection(*[set(cd[c]) for c in countries])), cd, cov


def collisions(regs):
    """Stems reached by more than one distinct display name. The cost of over-merging."""
    seen = {}
    for c, d in regs.items():
        for name, st in d["rows"]:
            seen.setdefault(st, set()).add(deaccent(name).lower())
    return {k: sorted(v) for k, v in seen.items() if len(v) > 1}


# ---- SVG ---------------------------------------------------------------

def txt(x, y, s, *, size, fill, anchor="start", weight="normal", tab=False):
    st = "font-variant-numeric: tabular-nums;" if tab else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family=\'{FONT}\' font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
            f'style="{st}">{escape(str(s))}</text>')


def para(x, y, s, *, size, fill, chars, leading=16.0):
    words, line, out, n = str(s).split(), [], [], 0
    for w in words:
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
            line, n = [], n + 1
        line.append(w)
    if line:
        out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
        n += 1
    return out, n * leading


def frame(w, h, title, subtitle, body, footer=None, chars=112):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
         f'viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="{SURFACE}"/>']
    s.append(txt(28, 42, title, size=19, fill=INK, weight="600"))
    sub, _ = para(28, 66, subtitle, size=12.5, fill=INK2, chars=chars)
    s += sub
    s += body
    if footer:
        fy = h - 18 - 15 * (len(footer) - 1)
        s.append(f'<line x1="28" y1="{fy - 20:.1f}" x2="{w - 28:.1f}" y2="{fy - 20:.1f}" '
                 f'stroke="{RULE}" stroke-width="1"/>')
        # A footer line is drawn unwrapped, so an over-long one silently runs off the
        # right edge of the page. It has happened three times; now it says so.
        cap = int((w - 56) / 5.42)
        for i, line in enumerate(footer):
            if len(line) > cap:
                print(f"  !! footer line {i+1} is {len(line)} chars, {cap} fit — it will "
                      f"overflow:\n     {line[cap-12:cap+24]!r}")
            s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    return "\n".join(s)


def write(name, svg):
    # `name` may carry a subdirectory — charts/negative/ holds the worked failures.
    out = CHARTS / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    return f"wrote charts/{name}"
