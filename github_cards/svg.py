"""SVG building blocks shared by cards."""
import datetime as dt
from xml.sax.saxutils import escape

from .themes import THEMES

FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"
WIDTH = 495
REPO = "spidero/github-stats-card"
# Small credit in the bottom-left corner; the CLI turns it off with --no-credit
SHOW_CREDIT = True

__all__ = ["FONT", "WIDTH", "escape", "human", "card", "stat_row", "ring", "bar", "fmt_date"]


def human(n):
    """Exact value below 10k, short form above (12.3k, 2.5M)."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    if n >= 10_000:
        return f"{n / 1_000:.1f}".rstrip("0").rstrip(".") + "k"
    return str(n)


def card(theme, title, body, height, width=WIDTH, extra_css="", footer=True):
    """Wrap `body` (SVG markup) in a themed card with a title and "updated" footer."""
    c = THEMES[theme]
    title = escape(title)
    foot = ""
    if footer:
        updated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
        foot = (f'<text x="{width - 25}" y="{height - 12}" text-anchor="end" '
                f'class="small">updated {updated}</text>')
        if SHOW_CREDIT:
            foot += (f'<a href="https://github.com/{REPO}" target="_blank">'
                     f'<text x="25" y="{height - 12}" class="small credit">{REPO}</text></a>')
    # Optional gradient background (theme key bg2)
    fill, defs = c["bg"], ""
    if c.get("bg2") and c["bg"] != "none":
        fill = "url(#bg)"
        defs = (f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
                f'<stop offset="0" stop-color="{c["bg"]}"/><stop offset="1" stop-color="{c["bg2"]}"/>'
                f'</linearGradient></defs>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{title}">
<title>{title}</title>
<style>
  .title {{ font: 600 18px {FONT}; fill: {c["title"]}; }}
  .label {{ font: 600 13px {FONT}; fill: {c["label"]}; }}
  .value {{ font: 700 13px {FONT}; fill: {c["value"]}; }}
  .big {{ font: 700 22px {FONT}; fill: {c["value"]}; }}
  .small {{ font: 400 10px {FONT}; fill: {c["label"]}; }}
  .credit {{ opacity: .55; }}
  /* Visible by default; the animation only fades in from 0 (no-animation renderers show the final state) */
  .fade {{ animation: fade .5s ease-in-out backwards; }}
  @keyframes fade {{ from {{ opacity: 0; }} }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
{extra_css}
</style>
{defs}<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="6" fill="{fill}" stroke="{c["border"]}"/>
<text x="25" y="35" class="title">{title}</text>
{body}
{foot}
</svg>
"""


def stat_row(theme, i, label, value, y0=70, step=22, value_x=265):
    """One "■ Label: value" row; `i` is the row index (position + fade-in delay)."""
    c = THEMES[theme]
    y = y0 + i * step
    return (
        f'<g class="fade" style="animation-delay:{150 + i * 120}ms">'
        f'<rect x="25" y="{y - 9}" width="8" height="8" rx="2" fill="{c["accent"]}"/>'
        f'<text x="43" y="{y}" class="label">{escape(label)}:</text>'
        f'<text x="{value_x}" y="{y}" class="value">{escape(str(value))}</text></g>'
    )


def ring(theme, cx, cy, r, big, lines=(), fraction=1.0, width=8, big_y=None):
    """Animated progress ring with a big value and small caption lines inside."""
    c = THEMES[theme]
    circ = 2 * 3.14159 * r
    end = circ * (1 - max(0.0, min(1.0, fraction)))
    rid = f"ring{cx}x{cy}"  # unique per ring, so several rings can coexist
    big_y = cy + 4 if big_y is None else big_y
    caption = "".join(
        f'<text x="{cx}" y="{cy + 20 + 12 * i}" text-anchor="middle" class="small">{escape(t)}</text>'
        for i, t in enumerate(lines)
    )
    return f"""<style>
  .{rid} {{ stroke-dasharray: {circ:.1f}; stroke-dashoffset: {end:.1f}; animation: {rid} 1.2s ease-out backwards; }}
  @keyframes {rid} {{ from {{ stroke-dashoffset: {circ:.1f}; }} }}
</style>
<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{c["track"]}" stroke-width="{width}"/>
<circle class="{rid}" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{c["accent"]}" stroke-width="{width}" stroke-linecap="round" transform="rotate(-90 {cx} {cy})"/>
<text x="{cx}" y="{big_y}" text-anchor="middle" class="big">{escape(str(big))}</text>
{caption}"""


def bar(theme, x, y, width, height, parts, gap=2):
    """Horizontal stacked bar. `parts` = [(fraction, color), ...], fractions sum to ~1."""
    c = THEMES[theme]
    clip = f"bar{x}{y}"
    out = [f'<clipPath id="{clip}"><rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{height / 2}"/></clipPath>',
           f'<g clip-path="url(#{clip})"><rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{c["track"]}"/>']
    pos = x
    for frac, color in parts:
        w = width * frac
        if w <= 0:
            continue
        out.append(f'<rect x="{pos:.1f}" y="{y}" width="{max(w - gap, 0.5):.1f}" height="{height}" fill="{color}"/>')
        pos += w
    out.append("</g>")
    return "".join(out)


def fmt_date(iso):
    """'2026-03-07' -> 'Mar 7, 2026'."""
    d = dt.date.fromisoformat(iso)
    return f"{d.strftime('%b')} {d.day}, {d.year}"
