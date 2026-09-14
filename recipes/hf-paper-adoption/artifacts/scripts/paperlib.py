#!/usr/bin/env python3
"""Shared loading, field mapping and SVG helpers for this recipe's charts.

Every chart here answers a prescriptive question — where to work, what predicts
adoption, how long to wait — so they all need the same three joins, done once:

    feed()      17k papers from the daily feed: date, keywords, upvotes, stars, org
    models()    the top-1,000 listing: createdAt, pipeline_tag, arxiv tags, base_model
    bibs()      424 papers' own reference lists, from arXiv LaTeX source

**The field taxonomy is the load-bearing part and it is imperfect.** Papers are
assigned a field by keyword, models by `pipeline_tag`. Two fields that matter have no
pipeline_tag at all — **there is no tag for agents or reinforcement learning**, so
those models ship as `text-generation` and their adoption lands under LLM-core. An
earlier version reported agents and RL at zero adoptions per thousand papers; that was
this taxonomy failing, not a finding. They are excluded from any adoption rate rather
than shown as zero.

**Colour discipline:** at most two categorical hues anywhere. Five to eight fields
cannot be told apart by hue under colour-vision deficiency, so fields are separated by
position and direct labels, and magnitude uses one sequential ramp.
"""
import collections
import datetime as dt
import os
import glob
import gzip
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape


# Where the captured archive lives. Resolution order, so that this runs for someone
# who is not the author:
#   1. $WSS_HUGGING_FACE, if set
#   2. artifacts/data/wss-hugging-face inside this recipe (git-ignored)
# The recipe reads a capture repository it does not own; see README for how to get one.
RECIPE = Path(__file__).resolve().parents[2]
DATA = RECIPE / "artifacts" / "data"


def _archive() -> Path:
    env = os.environ.get("WSS_HUGGING_FACE")
    for cand in ([Path(env)] if env else []) + [DATA / "wss-hugging-face"]:
        if (cand / "raw").is_dir():
            return cand
    raise SystemExit(
        "cannot find the wss-hugging-face capture.\n"
        "  set WSS_HUGGING_FACE=/path/to/wss-hugging-face, or place it at\n"
        f"  {DATA / 'wss-hugging-face'}\n"
        "  see README.md -> 'Running this yourself'."
    )

ARCHIVE = _archive()
HERE = Path(__file__).resolve().parent
RAW = DATA                       # derived inputs: bibliographies.json, openalex.json...
CHARTS = RECIPE / "artifacts" / "charts"

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, RULE, BASELINE = "#e1e0d9", "#ebeae3", "#c3c2b7"
HOT, COOL = "#b03a2e", "#1b4f8a"
RAMP = ["#eef2f7", "#cfdcea", "#a8c1db", "#7ba0c7", "#4d7cb0", "#1b4f8a"]
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'

# Okabe-Ito, the standard colour-vision-deficient-safe set. Validated with the
# recipe's own checker: six hues pass normal, protanope, deuteranope and tritanope.
# A home-picked six failed at tritanope dE 1.8, which is why this is not eyeballed.
# Colour is still a SECOND encoding here -- every mark carries its field name -- but
# it is worth getting right for the readers who can use it.
FIELD_COLOR = {
    "LLM-core":              "#0072B2",
    "image-gen":             "#D55E00",
    "embedding":             "#009E73",
    "speech":                "#CC79A7",
    "vision":                "#E69F00",
    "time-series":           "#56B4E9",
    "unmapped: agents, RL":  "#555555",
}


# Keyword patterns that place a *paper* in a field.
FIELD_KW = {
    "speech": ("speech", "audio", " asr", "text-to-speech", "voice", "transcription"),
    "embedding": ("embedding", "retrieval", "sentence similarity", "rerank", " rag",
                  "dense retrieval", "vector database"),
    "vision": ("vision transformer", "image classification", "object detection",
               "segmentation", "visual recognition", "depth estimation"),
    "image-gen": ("diffusion", "text-to-image", "image generation", "image synthesis"),
    "time-series": ("time series", "forecasting"),
    "LLM-core": ("large language model", "llm", "pretraining", "transformer",
                 "attention", "tokeniz", "context window"),
}
# pipeline_tag -> field, for the *model* side. Deliberately partial.
FIELD_TAG = {
    "automatic-speech-recognition": "speech", "text-to-speech": "speech",
    "audio-classification": "speech", "audio-to-audio": "speech",
    "feature-extraction": "embedding", "sentence-similarity": "embedding",
    "text-ranking": "embedding",
    "image-classification": "vision", "object-detection": "vision",
    "image-segmentation": "vision", "zero-shot-image-classification": "vision",
    "depth-estimation": "vision", "image-to-text": "vision",
    "text-to-image": "image-gen", "image-to-image": "image-gen",
    "time-series-forecasting": "time-series",
    "text-generation": "LLM-core", "text2text-generation": "LLM-core",
    "fill-mask": "LLM-core",
}
# Fields whose adoption cannot be isolated, because the models carry no distinct tag.
UNMEASURABLE = ("agents", "RL/align")
QWEN = "Qwen2.5-Coder-32B-Instruct"


def _open(p):
    return (gzip.open if str(p).endswith(".gz") else open)(p, "rt")


def write_json_atomic(path, obj, indent=None):
    """Write JSON via a temp file and rename, so a kill cannot corrupt the target.

    The fetchers checkpoint a resume cache every 25 papers with a plain overwrite.
    That is a truncate-then-write: a process killed inside the window loses not the
    last 25 papers but the entire cache, and a reader that lands in the window sees a
    partial file. Both happened during the 2026-09-14 re-fetch — `verify.py` read 16
    bibliographies out of a file that held 163. os.replace is atomic on POSIX.
    """
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=indent))
    os.replace(tmp, path)


def feed(one_extractor=True):
    """Daily-papers records, keyed by arXiv id.

    `one_extractor` keeps only papers keyworded by the model that produced ~99% of the
    archive. That is necessary and **not sufficient**. Hugging Face swapped extractors
    on 2026-07-13, and the new one emits a fifth fewer keywords per paper, deflating
    EVERY keyword's share to ~81% of its old value. But regime detection on the output
    itself (`chart-11-instrument`) finds a SECOND boundary at 2025-12-25 with no
    declared change, and by these features it is the larger of the two. So this filter
    still pools two instruments, and any comparison spanning 2025-12 crosses a break it
    cannot see. Prefer restricting to one detected regime when the question is a trend.
        """
    out = {}
    for p in glob.glob(str(ARCHIVE / "raw" / "hf.papers.daily*" / "*" / "*" / "*")):
        try:
            d = json.load(_open(p))
        except Exception:
            continue
        for r in d:
            pa = r.get("paper") or {}
            if not pa.get("id") or not pa.get("publishedAt"):
                continue
            if one_extractor and QWEN not in (pa.get("ai_summary_model") or ""):
                continue
            pa["_org"] = (r.get("organization") or pa.get("organization") or {}).get("name")
            out[pa["id"]] = pa
    return out


def models(latest_only=True):
    files = sorted(glob.glob(str(ARCHIVE / "raw" / "hf.models.top-downloads" / "*" / "*" / "*")))
    files = files[-1:] if latest_only else files
    seen = {}
    for p in files:
        for m in json.load(_open(p)):
            seen[m["id"]] = m
    return list(seen.values())


def bibs():
    p = RAW / "bibliographies.json"
    if not p.exists():
        return {}
    MAX, JUNK = 400, ("frobnicat", "foo filter", "author guidelines")
    return {k: [r for r in v if not any(j in r.lower() for j in JUNK)]
            for k, v in json.loads(p.read_text()).items() if v and len(v) <= MAX}


def paper_field(pa):
    """Fields a paper touches, by keyword. A paper can sit in more than one."""
    blob = " ".join(x.lower() for x in (pa.get("ai_keywords") or []))
    blob += " " + (pa.get("title") or "").lower()
    return {f for f, pats in FIELD_KW.items() if any(p in blob for p in pats)}


def arxiv_ids(m):
    return {t.split(":", 1)[1] for t in m.get("tags", []) if t.startswith("arxiv:")}


def foreign_base(m):
    me = m["id"].split("/")[0]
    for t in m.get("tags", []):
        if t.startswith("base_model:"):
            ref = t.split(":")[-1]
            if "/" in ref and ref.split("/")[0] != me:
                return ref.split("/")[0]
    return None


def pub_month(a):
    h = a.split(".")[0]
    if len(h) != 4 or not h.isdigit():
        return None
    y, m = 2000 + int(h[:2]), int(h[2:])
    return y * 12 + m if 1 <= m <= 12 else None


def quarter(datestr):
    d = dt.date.fromisoformat(datestr[:10])
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


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
        for i, line in enumerate(footer):
            s.append(txt(28, fy + i * 15, line, size=11, fill=INK2 if i == 0 else MUTED))
    s.append("</svg>")
    return "\n".join(s)


def write(name, svg):
    CHARTS.mkdir(parents=True, exist_ok=True)
    (CHARTS / name).write_text(svg, encoding="utf-8")
    return f"wrote charts/{name}"
