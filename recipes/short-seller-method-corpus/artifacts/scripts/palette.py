"""Colourblind-safety check for a categorical palette, as code rather than a comment.

Earlier recipes ran this check ad hoc and kept only the verdict in a source comment
("OKLab dE 28.2 normal, 23.2 protanope"), so nothing could re-run it when the
palette changed. This module is the check itself.

Thresholds, from the dataviz doctrine: CVD delta-E >= 8 is the target and 6-8 is a
floor that is only legal alongside a second encoding; normal-vision delta-E below 15
is a hard failure, because full-colour readers cannot tell the pair apart either.

    python palette.py "#2361b0,#c8532a,..."
"""
import sys

def _srgb(h):
    h = h.lstrip("#")
    return [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]

def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def _oklab(rgb):
    r, g, b = (_lin(c) for c in rgb)
    l = (0.4122214708*r + 0.5363325363*g + 0.0514459929*b) ** (1/3)
    m = (0.2119034982*r + 0.6806995451*g + 0.1073969566*b) ** (1/3)
    s = (0.0883024619*r + 0.2817188376*g + 0.6299787005*b) ** (1/3)
    return (0.2104542553*l + 0.7936177850*m - 0.0040720468*s,
            1.9779984951*l - 2.4285922050*m + 0.4505937099*s,
            0.0259040371*l + 0.7827717662*m - 0.8086757660*s)

# Viénot-Brettel-Mollon LMS reductions for dichromacy.
_SIM = {
    "protanope":   [[0, 1.05118294, -0.05116099], [0, 1, 0], [0, 0, 1]],
    "deuteranope": [[1, 0, 0], [0.9513092, 0, 0.04866992], [0, 0, 1]],
    "tritanope":   [[1, 0, 0], [0, 1, 0], [-0.86744736, 1.86727089, 0]],
}
_TO_LMS = [[0.31399022, 0.63951294, 0.04649755],
           [0.15537241, 0.75789446, 0.08670142],
           [0.01775239, 0.10944209, 0.87256922]]
_FROM_LMS = [[5.47221206, -4.6419601, 0.16963708],
             [-1.1252419, 2.29317094, -0.1678952],
             [0.02980165, -0.19318073, 1.16364789]]

def _mul(M, v):
    return [sum(M[i][j] * v[j] for j in range(3)) for i in range(3)]

def simulate(hexcol, kind):
    rgb = [_lin(c) for c in _srgb(hexcol)]
    out = _mul(_FROM_LMS, _mul(_SIM[kind], _mul(_TO_LMS, rgb)))
    return [min(1, max(0, c)) ** (1 / 2.2) for c in out]

def dE(a, b):
    """OKLab distance x100, on already-linear-ish rgb triples or hex strings."""
    A = _oklab(_srgb(a) if isinstance(a, str) else a)
    B = _oklab(_srgb(b) if isinstance(b, str) else b)
    return 100 * sum((A[i] - B[i]) ** 2 for i in range(3)) ** 0.5

def check(cols, *, label=""):
    worst = {"normal": (999, None)}
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            d = dE(cols[i], cols[j])
            if d < worst["normal"][0]:
                worst["normal"] = (d, (cols[i], cols[j]))
            for k in _SIM:
                d2 = dE(simulate(cols[i], k), simulate(cols[j], k))
                if d2 < worst.get(k, (999, None))[0]:
                    worst[k] = (d2, (cols[i], cols[j]))
    ok = True
    print(f"  {label or 'palette'}: {len(cols)} colours")
    for k in ("normal", "protanope", "deuteranope", "tritanope"):
        d, pair = worst[k]
        floor = 15 if k == "normal" else 8
        verdict = "PASS" if d >= floor else ("FLOOR" if d >= 6 and k != "normal" else "FAIL")
        ok &= verdict == "PASS"
        print(f"    {k:<13} worst pair dE {d:>5.1f}  (floor {floor})  {verdict}   {pair[0]} / {pair[1]}")
    return ok

if __name__ == "__main__":
    cols = [c.strip() for c in sys.argv[1].split(",")]
    sys.exit(0 if check(cols) else 1)
