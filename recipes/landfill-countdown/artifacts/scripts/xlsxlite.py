#!/usr/bin/env python3
"""Read an .xlsx with the standard library, because a recipe may not require a pip install.

    python3 xlsxlite.py <file.xlsx> [sheet]     # print the first rows, to check it parses

An .xlsx is a zip of XML. `openpyxl` is a fine library and this is not a replacement for it;
it covers exactly the subset this project needs — **read-only, cached values, iterate rows** —
so that a published recipe has no third-party dependency and a stranger can run it with
nothing installed.

**Three things that bite when you do this by hand:**

**Cells are sparse and addressed, not positional.** A row emits only the cells that hold
something, each carrying a reference like `C5`. Reading them in order and assuming column
order gives a row whose fields have silently shifted left wherever a blank was skipped. The
reference is parsed and gaps are filled.

**Most strings are not in the sheet.** They live once in `xl/sharedStrings.xml` and the cell
holds an index with `t="s"`. A reader that ignores `t` returns the integer 4 where the sheet
shows "LANDFILL".

**A formula cell holds both the formula and its last cached result.** Reading `<v>` gives the
value the file was saved with, which is what `data_only=True` means elsewhere. If the file was
written by something that never calculated, `<v>` is absent and the cell reads as None — that
is the file's problem, but it is silent, so it is worth knowing.

**Not covered:** dates (stored as serial numbers with a style, and undoing that needs the
number-format table), styles, merged cells, charts, writing. If a column comes back as 45000
rather than a date, that is why.
"""
import re, sys, zipfile
from xml.etree import ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG = "{http://schemas.openxmlformats.org/package/2006/relationships}"
CELL = re.compile(r"([A-Z]+)(\d+)")


def _col(ref):
    """'C5' -> 2. Base-26 with no zero, so A=1 and AA=27."""
    m = CELL.match(ref or "")
    if not m:
        return None
    n = 0
    for ch in m.group(1):
        n = n * 26 + (ord(ch) - 64)
    return n - 1


class Workbook:
    def __init__(self, path):
        self.z = zipfile.ZipFile(path)
        self.shared = self._shared()
        self.sheets = self._sheets()

    def _shared(self):
        if "xl/sharedStrings.xml" not in self.z.namelist():
            return []
        out = []
        with self.z.open("xl/sharedStrings.xml") as fh:
            for _, el in ET.iterparse(fh, ("end",)):
                if el.tag == NS + "si":
                    # a string may be split into runs; concatenate every <t> under it
                    out.append("".join(t.text or "" for t in el.iter(NS + "t")))
                    el.clear()
        return out

    def _sheets(self):
        rels = {}
        with self.z.open("xl/_rels/workbook.xml.rels") as fh:
            for el in ET.parse(fh).getroot():
                rels[el.get("Id")] = el.get("Target").lstrip("/")
        out = {}
        with self.z.open("xl/workbook.xml") as fh:
            for el in ET.parse(fh).getroot().iter(NS + "sheet"):
                t = rels.get(el.get(RNS + "id"), "")
                out[el.get("name")] = t if t.startswith("xl/") else "xl/" + t
        return out

    @property
    def sheetnames(self):
        return list(self.sheets)

    def rows(self, sheet=None):
        """Yield each row as a list of values, gaps filled with None."""
        path = self.sheets[sheet or self.sheetnames[0]]
        with self.z.open(path) as fh:
            for _, el in ET.iterparse(fh, ("end",)):
                if el.tag != NS + "row":
                    continue
                cells = {}
                for c in el.findall(NS + "c"):
                    i = _col(c.get("r"))
                    if i is None:
                        continue
                    t = c.get("t")
                    if t == "inlineStr":
                        v = "".join(x.text or "" for x in c.iter(NS + "t"))
                    else:
                        node = c.find(NS + "v")
                        v = node.text if node is not None else None
                        if v is not None and t == "s":
                            v = self.shared[int(v)]
                        elif v is not None and t == "b":
                            v = v == "1"
                        elif v is not None and t not in ("str", "e"):
                            try:
                                v = int(v) if "." not in v and "E" not in v.upper() else float(v)
                            except ValueError:
                                pass
                    cells[i] = v
                el.clear()
                yield [cells.get(i) for i in range(max(cells) + 1)] if cells else []


def load_workbook(path):
    return Workbook(path)


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip().split("\n\n")[0])
        return 1
    wb = load_workbook(sys.argv[1])
    print(f"  sheets: {wb.sheetnames}")
    name = sys.argv[2] if len(sys.argv) > 2 else None
    for i, r in enumerate(wb.rows(name)):
        print(f"   {i}: {[str(x)[:18] for x in r[:8]]}")
        if i >= 5:
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
