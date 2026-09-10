"""Minimal stdlib SVG helpers, shared by the CFR charts."""
BLUE, ORANGE, AQUA, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"
INK, MUTE, GRID = "#1c2530", "#6b7684", "#dfe4ea"
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def txt(x, y, s, size=12, fill=INK, anchor="start", weight="normal", style=""):
    st = f' font-style="{style}"' if style else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}"{st}>'
            f'{esc(s)}</text>')


def line(x1, y1, x2, y2, stroke=GRID, w=1, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{w}"{d}/>')


def rect(x, y, w, h, fill, stroke="none", sw=1, op=1.0, rx=0):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w,0):.1f}" '
            f'height="{max(h,0):.1f}" fill="{fill}" fill-opacity="{op}" '
            f'stroke="{stroke}" stroke-width="{sw}" rx="{rx}"/>')


def circ(x, y, r, fill, stroke="none", sw=1):
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>')


def wrap(words, width):
    """Greedy wrap on an ~6px-per-char estimate at 11px."""
    out, cur = [], ""
    for w in str(words).split():
        t = (cur + " " + w).strip()
        if len(t) * 6.0 > width and cur:
            out.append(cur); cur = w
        else:
            cur = t
    if cur:
        out.append(cur)
    return out


def doc(w, h, body, bg="#ffffff"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}">'
            f'<rect width="{w}" height="{h}" fill="{bg}"/>' + "".join(body) + "</svg>")


def quantiles(vals, qs):
    """Linear-interpolation quantiles; vals must be sorted."""
    n = len(vals)
    out = []
    for q in qs:
        if n == 1:
            out.append(vals[0]); continue
        p = q * (n - 1)
        lo = int(p); hi = min(lo + 1, n - 1)
        out.append(vals[lo] + (vals[hi] - vals[lo]) * (p - lo))
    return out
