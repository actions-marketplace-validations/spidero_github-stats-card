"""Contribution activity over the years as a line chart (monthly totals).

Styles (option activity_style):
  line   one continuous line across the years (default)
  years  one line per year on a Jan-Dec axis (year-over-year comparison)
  both   both files: github-activity*.svg (line) and github-activity-years*.svg
activity_years limits the number of years shown (0 = auto: every year with
contributions for "line", the last 3 years for "years").
"""
import math

from ..contrib import daily_counts
from ..svg import THEMES, card, escape, human

DESCRIPTION = "Monthly contributions over the years (line chart, one line or one per year)"

STYLES = ("line", "years")
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# Plot area
LEFT, RIGHT, TOP = 52, 470, 62
# Older years in the "years" style: fading label color + dash pattern (newest year = accent)
OLDER = [(0.9, ""), (0.65, "5 3"), (0.45, "2 3"), (0.35, "8 3 2 3"), (0.25, "1 2")]


def monthly(days):
    """[(iso_date, count)] -> {"YYYY-MM": total}."""
    out = {}
    for date, count in days:
        out[date[:7]] = out.get(date[:7], 0) + count
    return out


def fetch(api, login, options):
    cal = daily_counts(api, login)
    # Keep every month (the style is chosen at render time, so --data works with any option)
    return {"name": cal["name"], "today": cal["today"], "months": monthly(cal["days"])}


def nice_max(value):
    """Round up to a "nice" number (even, so the half-way grid label is whole)."""
    if value <= 4:
        return 4
    exp = 10 ** math.floor(math.log10(value))
    for step in (1, 1.2, 1.6, 2, 2.4, 3, 4, 5, 6, 8, 10):
        if value <= step * exp:
            return int(step * exp) if step * exp >= 4 else 4
    return int(10 * exp)


def series(data, years_limit, style):
    """Month keys to plot: [(year, [counts by month, up to the current month])]."""
    months, today = data["months"], data["today"]
    last_year, last_month = int(today[:4]), int(today[5:7])
    active = sorted({int(k[:4]) for k, v in months.items() if v > 0}) or [last_year]
    if years_limit:
        first = last_year - years_limit + 1
    elif style == "years":
        first = last_year - 2
    else:
        first = active[0]
    out = []
    for year in range(first, last_year + 1):
        upto = last_month if year == last_year else 12
        out.append((year, [months.get(f"{year}-{m:02d}", 0) for m in range(1, upto + 1)]))
    return out


def _grid(c, top, bottom, ymax):
    out = []
    for i in range(3):
        v = ymax * i / 2
        y = bottom - (bottom - top) * i / 2
        dash = "" if i == 0 else ' stroke-dasharray="3 3"'
        out.append(f'<line x1="{LEFT}" y1="{y:.1f}" x2="{RIGHT}" y2="{y:.1f}" stroke="{c["track"]}" '
                   f'stroke-width="1"{dash}/>')
        out.append(f'<text x="{LEFT - 8}" y="{y + 3:.1f}" text-anchor="end" class="small">{human(int(v))}</text>')
    return out


def _path(points):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points)


def _draw(i):
    # Line draws itself from hidden; without animation it is fully visible
    return (f'class="draw" style="animation-delay:{200 + i * 150}ms"')


CSS = """  .draw { stroke-dasharray: 1; stroke-dashoffset: 0; animation: draw 1.4s ease-out backwards; }
  @keyframes draw { from { stroke-dashoffset: 1; } }"""


def render_line(data, theme, options, years):
    c = THEMES[theme]
    height, bottom = 215, 165
    values = [v for _, vals in years for v in vals]
    ymax = nice_max(max(values, default=0))
    n = len(values)
    step = (RIGHT - LEFT) / max(n - 1, 1)
    pts = [(LEFT + i * step, bottom - (bottom - TOP) * v / ymax) for i, v in enumerate(values)]

    body = _grid(c, TOP, bottom, ymax)
    # Year labels at January positions, thinned out so they never overlap
    every = max(1, math.ceil(34 / (12 * step))) if n > 1 else 1
    idx = 0
    for k, (year, vals) in enumerate(years):
        x = LEFT + idx * step
        if k % every == 0:
            body.append(f'<line x1="{x:.1f}" y1="{bottom}" x2="{x:.1f}" y2="{bottom + 4}" stroke="{c["border"]}"/>')
            anchor = "start" if k == 0 else "middle"
            body.append(f'<text x="{x:.1f}" y="{bottom + 16}" text-anchor="{anchor}" class="small">{year}</text>')
        idx += len(vals)
    if len(pts) > 1:
        area = _path(pts) + f" L{pts[-1][0]:.1f},{bottom} L{pts[0][0]:.1f},{bottom} Z"
        body.append(f'<path d="{area}" fill="{c["accent"]}" fill-opacity="0.12" class="fade" '
                    f'style="animation-delay:600ms"/>')
        body.append(f'<path d="{_path(pts)}" pathLength="1" fill="none" stroke="{c["accent"]}" stroke-width="2" '
                    f'stroke-linejoin="round" stroke-linecap="round" {_draw(0)}/>')
    # Peak month marker
    if values and max(values) > 0:
        i = values.index(max(values))
        x, y = pts[i]
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{c["accent"]}" class="fade" '
                    f'style="animation-delay:900ms"/>')
    total = sum(values)
    span = f"{years[0][0]}-{years[-1][0]}" if len(years) > 1 else str(years[0][0])
    body.append(f'<text x="{RIGHT}" y="35" text-anchor="end" class="small">'
                f'{escape(human(total))} contributions, {span}</text>')
    title = options.get("title") or f"{data['name']}'s Activity"
    return card(theme, title, "".join(body), height=height, extra_css=CSS)


def render_years(data, theme, options, years):
    c = THEMES[theme]
    height, bottom = 235, 160
    ymax = nice_max(max((v for _, vals in years for v in vals), default=0))
    step = (RIGHT - LEFT) / 11

    body = _grid(c, TOP, bottom, ymax)
    for m, name in enumerate(MONTHS):
        x = LEFT + m * step
        anchor = "start" if m == 0 else "end" if m == 11 else "middle"
        body.append(f'<text x="{x:.1f}" y="{bottom + 16}" text-anchor="{anchor}" class="small">{name}</text>')

    # Oldest first, so the newest (accent) line is drawn on top
    newest = years[-1][0]
    legend = []
    for k, (year, vals) in enumerate(years):
        age = newest - year
        if age == 0:
            color, opacity, dash, width = c["accent"], 1, "", 2.5
        else:
            opacity, dash = OLDER[min(age - 1, len(OLDER) - 1)]
            color, width = c["label"], 1.6
        pts = [(LEFT + m * step, bottom - (bottom - TOP) * v / ymax) for m, v in enumerate(vals)]
        style = (f'stroke="{color}" stroke-opacity="{opacity}" stroke-width="{width}"'
                 + (f' stroke-dasharray="{dash}"' if dash else ""))
        if len(pts) > 1:
            # Dashed lines can't use the dash-offset draw animation; they fade in instead
            anim = (f'pathLength="1" {_draw(k)}' if not dash
                    else f'class="fade" style="animation-delay:{200 + k * 150}ms"')
            body.append(f'<path d="{_path(pts)}" fill="none" {style} stroke-linejoin="round" '
                        f'stroke-linecap="round" {anim}/>')
        elif pts:
            body.append(f'<circle cx="{pts[0][0]:.1f}" cy="{pts[0][1]:.1f}" r="2.5" fill="{color}" '
                        f'fill-opacity="{opacity}"/>')
        legend.append((year, sum(vals), style))

    # Legend, newest first; wraps into more rows (the card grows) when it doesn't fit
    rows, row = [], []
    x = LEFT
    for year, total, style in reversed(legend):
        label = f"{year}: {human(total)}"
        w = 23 + 6 * len(label) + 16
        if row and x + w - 16 > RIGHT:
            rows.append(row)
            row, x = [], LEFT
        row.append((x, label, style))
        x += w
    rows.append(row)
    for r, items in enumerate(rows):
        y = bottom + 33 + r * 16
        for x, label, style in items:
            body.append(f'<g class="fade" style="animation-delay:500ms">'
                        f'<line x1="{x}" y1="{y}" x2="{x + 18}" y2="{y}" {style}/>'
                        f'<text x="{x + 23}" y="{y + 4}" class="small">{escape(label)}</text></g>')
    height += 16 * (len(rows) - 1)
    title = options.get("title") or f"{data['name']}'s Activity by Year"
    return card(theme, title, "".join(body), height=height, extra_css=CSS)


def variants(options):
    """Output files: "both" renders the line chart and the per-year chart (-years suffix)."""
    if options.get("activity_style") == "both":
        return [("", {**options, "activity_style": "line"}),
                ("-years", {**options, "activity_style": "years"})]
    return [("", options)]


def render(data, theme, options):
    style = options.get("activity_style") or "line"
    years = series(data, options.get("activity_years") or 0, style)
    if style == "years":
        return render_years(data, theme, options, years)
    return render_line(data, theme, options, years)
