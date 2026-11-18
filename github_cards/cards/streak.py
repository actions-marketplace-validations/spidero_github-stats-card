"""Contribution streaks: total contributions, current streak and longest streak."""
from ..contrib import daily_counts
from ..svg import THEMES, card, escape, fmt_date, human, ring

DESCRIPTION = "Total contributions, current and longest daily streak"


def streaks(days):
    """days: [(iso_date, count)] sorted ascending -> (current, longest) as dicts."""
    longest = {"length": 0, "start": None, "end": None}
    run_start, run = None, 0
    for date, count in days:
        if count > 0:
            run_start = run_start if run else date
            run += 1
            if run > longest["length"]:
                longest = {"length": run, "start": run_start, "end": date}
        else:
            run = 0
    # Current streak: ends today, or yesterday if today has no contributions yet
    current = {"length": 0, "start": None, "end": None}
    i = len(days) - 1
    if i >= 0 and days[i][1] == 0:
        i -= 1
    end = days[i][0] if i >= 0 else None
    while i >= 0 and days[i][1] > 0:
        current = {"length": current["length"] + 1, "start": days[i][0], "end": end}
        i -= 1
    return current, longest


def fetch(api, login, options):
    cal = daily_counts(api, login)
    days, today = cal["days"], cal["today"]
    current, longest = streaks(days)
    return {
        "name": cal["name"],
        "total": sum(c for _, c in days),
        "first": days[0][0] if days else today,
        "today": today,
        "current": current,
        "longest": longest,
    }


def _range(s):
    if not s["length"]:
        return "No streak"
    if s["start"] == s["end"]:
        return fmt_date(s["start"])
    return f"{fmt_date(s['start'])} - {fmt_date(s['end'])}"


def render(data, theme, options):
    c = THEMES[theme]
    cur, best = data["current"], data["longest"]
    height = 215
    cols = (85, 247, 410)

    def side(x, value, label, sub, delay):
        return (f'<g class="fade" style="animation-delay:{delay}ms">'
                f'<text x="{x}" y="98" text-anchor="middle" class="big">{escape(value)}</text>'
                f'<text x="{x}" y="150" text-anchor="middle" class="label">{escape(label)}</text>'
                f'<text x="{x}" y="168" text-anchor="middle" class="small">{escape(sub)}</text></g>')

    body = [
        side(cols[0], human(data["total"]), "Total contributions",
             f"{fmt_date(data['first'])} - Present", 150),
        side(cols[2], f"{best['length']} days", "Longest streak", _range(best), 400),
        # Separators
        f'<line x1="166" y1="60" x2="166" y2="175" stroke="{c["border"]}"/>',
        f'<line x1="328" y1="60" x2="328" y2="175" stroke="{c["border"]}"/>',
        # Middle: ring shows the current streak as progress towards the longest one
        ring(theme, cols[1], 94, 36, cur["length"],
             fraction=(cur["length"] / best["length"]) if best["length"] else 0, width=6, big_y=102),
        f'<g class="fade" style="animation-delay:250ms">'
        f'<text x="{cols[1]}" y="150" text-anchor="middle" class="label" style="fill:{c["title"]}">Current streak</text>'
        f'<text x="{cols[1]}" y="168" text-anchor="middle" class="small">{escape(_range(cur))}</text></g>',
    ]
    return card(theme, options.get("title") or f"{data['name']}'s Streak", "".join(body), height=height)
