"""The data-viz primitives this recipe's figures are drawn with.

Palette, type, mark specs and the two spacers come from the data-viz method:
one system sans, a validated categorical order, one linear scale per axis,
hairline gridlines, marks no thicker than 24px, a 2px surface gap between
touching marks, and direct labels only where they earn their place.

Self-contained on purpose. A recipe is the unit someone copies; nothing here
imports from another recipe.
"""
from __future__ import annotations

import math

# ── palette (data-viz reference instance) ───────────────────────────────────
SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"

BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
MAGENTA, GREEN, VIOLET, RED = "#e87ba4", "#008300", "#4a3aa7", "#e34948"
CATEGORICAL = (BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED)

# Sequential blue ramp, 100 -> 700.
BLUE_RAMP = ("#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
             "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281",
             "#0d366b")

FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


# ── text and marks ──────────────────────────────────────────────────────────

def esc(value) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def text(x, y, value, size=12, fill=INK, anchor="start", weight="normal",
         tabular=False, style="", opacity=None) -> str:
    extra = ' font-variant-numeric="tabular-nums"' if tabular else ""
    if style:
        extra += f' font-style="{style}"'
    if opacity is not None:
        extra += f' fill-opacity="{opacity}"'
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family=\'{FONT}\' font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}"{extra}>'
            f'{esc(value)}</text>')


def line(x1, y1, x2, y2, stroke=GRID, width=1, dash=None) -> str:
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{width}"{extra}/>')


def rect(x, y, width, height, fill, opacity=1.0, rx=0, stroke="none", sw=1) -> str:
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(width, 0):.1f}" '
            f'height="{max(height, 0):.1f}" fill="{fill}" fill-opacity="{opacity}" '
            f'rx="{rx}" stroke="{stroke}" stroke-width="{sw}"/>')


def circle(x, y, r, fill, stroke="none", sw=1, opacity=1.0) -> str:
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" '
            f'fill-opacity="{opacity}" stroke="{stroke}" stroke-width="{sw}"/>')


def bar_h(x, y, width, height, fill, radius=4, opacity=1.0) -> str:
    """Horizontal bar: rounded at the data end (right), square at the baseline."""
    radius = min(radius, max(width / 2, 0.1), height / 2)
    if width <= 0:
        return ""
    return (f'<path d="M{x:.1f},{y:.1f} h{width - radius:.1f} '
            f'q{radius:.1f},0 {radius:.1f},{radius:.1f} '
            f'v{height - 2 * radius:.1f} q0,{radius:.1f} -{radius:.1f},{radius:.1f} '
            f'h-{width - radius:.1f} z" fill="{fill}" fill-opacity="{opacity}"/>')


def bar_h_left(x, y, width, height, fill, radius=4, opacity=1.0) -> str:
    """Horizontal bar growing left: rounded at the data end, square at the base."""
    radius = min(radius, max(width / 2, 0.1), height / 2)
    if width <= 0:
        return ""
    return (f'<path d="M{x:.1f},{y:.1f} h-{width - radius:.1f} '
            f'q-{radius:.1f},0 -{radius:.1f},{radius:.1f} '
            f'v{height - 2 * radius:.1f} q0,{radius:.1f} {radius:.1f},{radius:.1f} '
            f'h{width - radius:.1f} z" fill="{fill}" fill-opacity="{opacity}"/>')


def bar_v(x, y, width, height, fill, radius=4, opacity=1.0) -> str:
    """Vertical bar: rounded at the data end (top), square at the baseline."""
    radius = min(radius, max(height / 2, 0.1), width / 2)
    if height <= 0:
        return ""
    return (f'<path d="M{x:.1f},{y + height:.1f} v-{height - radius:.1f} '
            f'q0,-{radius:.1f} {radius:.1f},-{radius:.1f} '
            f'h{width - 2 * radius:.1f} q{radius:.1f},0 {radius:.1f},{radius:.1f} '
            f'v{height - radius:.1f} z" fill="{fill}" fill-opacity="{opacity}"/>')


def dot(x, y, r=5, fill=BLUE) -> str:
    """A dot carries a 2px surface ring so it reads over a line or another dot."""
    return circle(x, y, r + 2, SURFACE) + circle(x, y, r, fill)


# ── document ────────────────────────────────────────────────────────────────

def doc(width, height, title, desc, body) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">\n'
        f'<title>{esc(title)}</title>\n<desc>{esc(desc)}</desc>\n'
        f'<rect width="{width}" height="{height}" fill="{SURFACE}"/>\n'
        + "\n".join(body) + "\n</svg>\n"
    )


def header(title, subtitle, source, width=980) -> list[str]:
    return [
        text(36, 44, title, size=21, weight="600"),
        text(36, 69, subtitle, size=13.5, fill=INK2),
        text(36, 89, source, size=11, fill=MUTED),
    ]


def footer(note, y, width=980) -> str:
    return text(36, y, note, size=11, fill=MUTED)


def wrap(value, width, size=12) -> list[str]:
    """Greedy wrap on a rough 0.56em per character; good enough for labels."""
    lines, current = [], ""
    limit = width / (size * 0.56)
    for word in str(value).split():
        candidate = (current + " " + word).strip()
        if len(candidate) > limit and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


# ── scales and ticks ────────────────────────────────────────────────────────

def scale_linear(value, domain, range_):
    lo, hi = domain
    a, b = range_
    if hi == lo:
        return a
    return a + (value - lo) / (hi - lo) * (b - a)


def scale_log(value, domain, range_):
    lo, hi = math.log10(domain[0]), math.log10(domain[1])
    value = max(value, domain[0])
    return scale_linear(math.log10(value), (lo, hi), range_)


def ticks_log(lo, hi):
    """Every power of ten, and the 2/5 steps where there is room."""
    out = []
    start, end = math.floor(math.log10(lo)), math.ceil(math.log10(hi))
    for power in range(start, end + 1):
        for mult in (1, 2, 5):
            value = mult * 10 ** power
            if lo <= value <= hi:
                out.append(value)
    return out


def ticks_linear(lo, hi, count=5):
    """Clean multiples: 1, 2, 2.5 or 5 times a power of ten."""
    if hi == lo:
        return [lo]
    raw = (hi - lo) / max(count - 1, 1)
    power = 10 ** math.floor(math.log10(raw))
    for mult in (1, 2, 2.5, 5, 10):
        step = mult * power
        if step >= raw:
            break
    first = math.ceil(lo / step) * step
    out, value = [], first
    while value <= hi + step * 1e-9:
        out.append(round(value, 10))
        value += step
    return out


def ticks_linear_zero(hi, count=5):
    return ticks_linear(0, hi, count)


# ── formatting ──────────────────────────────────────────────────────────────

def usd(value, places=None):
    if places is not None:
        return f"${value:,.{places}f}"
    if abs(value) >= 100:
        return f"${value:,.0f}"
    if abs(value) >= 10:
        return f"${value:,.1f}"
    if abs(value) >= 1:
        return f"${value:,.2f}"
    if abs(value) >= 0.01:
        return f"${value:,.3f}"
    return f"${value:,.4f}"


def tokens(value):
    for threshold, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= threshold:
            return f"{value / threshold:,.1f}{suffix}".replace(".0", "")
    return f"{value:,.0f}"


def pct(value, places=0):
    return f"{value * 100:,.{places}f}%"


def legend(items, y, x0=36, gap=24) -> list[str]:
    out, x = [], x0
    for item in items:
        label, colour = item[0], item[1]
        shape = item[2] if len(item) > 2 else "dot"
        if shape == "line":
            out.append(line(x, y - 4, x + 18, y - 4, stroke=colour, width=2))
        else:
            out.append(circle(x + 5, y - 4, 5, colour))
        out.append(text(x + 24, y, label, size=11, fill=INK2))
        x += 24 + len(label) * 6.4 + gap
    return out


def grid_y(values, scale, x0, x1, ticks, labeler=usd) -> list[str]:
    out = []
    for value in ticks:
        y = scale(value)
        out.append(line(x0, y, x1, y, stroke=GRID))
        out.append(text(x0 - 10, y + 4, labeler(value), size=11, fill=MUTED,
                        anchor="end", tabular=True))
    return out


def grid_x(values, scale, y0, y1, ticks, labeler=lambda v: f"{v:g}") -> list[str]:
    out = []
    for value in ticks:
        x = scale(value)
        out.append(line(x, y0, x, y1, stroke=GRID))
        out.append(text(x, y1 + 18, labeler(value), size=11, fill=MUTED,
                        anchor="middle", tabular=True))
    return out


def baseline(x0, x1, y, axis="x") -> str:
    return line(x0, y, x1, y, stroke=BASELINE)
