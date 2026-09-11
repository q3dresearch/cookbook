#!/usr/bin/env python3
"""What became of the targets, and why that question is harder than it sounds.

    python capture_fate.py

For each target whose ticker two independent routes agree on, ask the price source
where that symbol resolves today. A 200 means it still trades there. A redirect to a
Q-suffixed OTC symbol is a bankruptcy. A redirect to a different symbol is a rename,
a merger, or an acquisition. A 404 means it is not at that symbol on a US venue any
more, for reasons the request cannot distinguish.

**The tickers are confirmed WITHOUT using SEC's registry, deliberately.** That
registry lists current filers, so validating against it can only ever confirm
survivors — using it here would answer the survival question with the survival
assumption. A ticker the report's own URL also states is real whether or not the
company still exists.

**And the result does not mean what its labels suggest.** Of the four symbol changes
found, KDNY resolves to NVS because Chinook Therapeutics was acquired by Novartis:
a premium exit for shareholders, filed by this script in the same bucket as a fraud.
SQ to XYZ is Block renaming itself. Among the disappearances, RINO and CIFS are
delisted Chinese frauds, but FMCN went private and relisted in China and WSP simply
trades on the TSX. What this measures is symbol persistence on a US venue. Corporate
death is a different variable and needs merger, bankruptcy and deregistration
filings, which SEC keeps and this script does not read.
"""
import json, re, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw"
sys.path.insert(0, str(HERE))
import corpuslib, ctrllib, tickers

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/128.0 Safari/537.36")
PAUSE = 1.1
EXCH = r"NASDAQ|NYSE|NYSEAMERICAN|AMEX|OTC|OTCMKTS|TSX|TSXV|ASX|HKEX|SEHK|LSE"


def confirmed_targets():
    """Tickers two routes agree on: the URL slug and the report's own text."""
    out = {}
    for key, label in (("nightmarket", "Night Market"), ("jcapital", "J Capital"),
                       ("muddywaters", "Muddy Waters"), ("sprucepoint", "Spruce Point")):
        try:
            docs, _ = ctrllib.first_look(key)
        except Exception:
            continue
        for d in docs:
            sl = tickers.slug_ticker(d, key)
            if not sl or not re.fullmatch(r"[A-Z]{2,6}", sl):
                continue
            sym, _, _ = tickers.extract(d["text"])
            if sym == sl or re.search(rf"\b(?:{EXCH})\s*[:\-]\s*{sl}\b", d["text"], re.I):
                out[sl] = {"firm": label, "date": d.get("date")}
    for p in corpuslib.load("initial"):
        sym, _, _ = tickers.extract(corpuslib.body(p))
        # Hindenburg's slugs are company names, so the second route is the report
        # writing the symbol in bare parentheses as well as exchange-prefixed.
        if sym and re.fullmatch(r"[A-Z]{2,6}", sym) and re.search(rf"\({re.escape(sym)}\)",
                                                                  corpuslib.body(p)):
            out.setdefault(sym, {"firm": "Hindenburg", "date": p["date"][:10]})
    return out


def where_now(sym):
    r = subprocess.run(["curl", "-sS", "-I", "--max-time", "25", "-A", UA,
                        f"https://stockanalysis.com/stocks/{sym.lower()}/"],
                       capture_output=True, timeout=40)
    t = r.stdout.decode("utf-8", "replace")
    code = re.search(r"HTTP/[\d.]+ (\d+)", t)
    loc = re.search(r"(?im)^location:\s*(\S+)", t)
    parts = [p for p in (loc.group(1).strip() if loc else "").split("/") if p]
    return (code.group(1) if code else "000"), (parts[-1].upper() if parts else None)


VENUES = ("quote/tsx", "quote/tsxv", "quote/asx", "quote/otc", "quote/lon")


def elsewhere(sym):
    """A symbol absent from the US listing may simply trade somewhere else.

    Five of the eight targets this script first called "gone" are still quoted:
    AKG on the ASX, IRSA in London, PMET and WSP on the TSX, RINO on OTC. Without
    this second pass the figure reported a 41% non-survival rate where the real
    count of companies that cannot be found anywhere is three of thirty-two.
    """
    found = []
    for v in VENUES:
        time.sleep(0.7)
        r = subprocess.run(["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}",
                            "--max-time", "20", "-A", UA,
                            f"https://stockanalysis.com/{v}/{sym}/"],
                           capture_output=True, timeout=35)
        if r.stdout.decode().strip() == "200":
            found.append(v.split("/")[-1].upper())
    return found


def main():
    tg = confirmed_targets()
    print(f"  {len(tg)} tickers confirmed by two independent routes")
    out = {}
    for i, (sym, meta) in enumerate(sorted(tg.items()), 1):
        time.sleep(PAUSE)
        code, now = where_now(sym)
        if code == "200":
            fate = "trading"
        elif code == "301" and now and now.endswith("Q"):
            fate = "bankrupt"
        elif code == "301" and now and now != sym:
            fate = "symbol changed"
        else:
            fate = "gone from this symbol"
        venues = elsewhere(sym) if fate == "gone from this symbol" else []
        if venues:
            fate = "trades elsewhere"
        out[sym] = {**meta, "http": code, "now": now, "fate": fate, "venues": venues}
        if i % 10 == 0:
            print(f"    {i}/{len(tg)}", flush=True)
    (RAW / "target_fate.json").write_text(json.dumps(out, indent=1))
    from collections import Counter
    for f, n in Counter(v["fate"] for v in out.values()).most_common():
        print(f"    {f:<24}{n:>3}  {n/len(out):>4.0%}")
    print("\n  Read the non-survivors before quoting any of this: 'symbol changed'")
    print("  contains at least one acquisition at a premium, and 'gone' contains at")
    print("  least two companies still trading on other exchanges.")


if __name__ == "__main__":
    main()
