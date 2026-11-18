"""Daily contribution counts since the account was created (shared by several cards)."""
import datetime as dt

CREATED = "query($login: String!) { user(login: $login) { name login createdAt } }"
YEAR = """
  y{year}: contributionsCollection(from: "{start}", to: "{end}") {{
    contributionCalendar {{ weeks {{ contributionDays {{ date contributionCount }} }} }}
  }}"""

# One fetch per login per run, even when several cards need the calendar
_cache = {}


def daily_counts(api, login):
    """Return {"name", "today", "days": [(iso_date, count)] sorted ascending, up to today}."""
    if login in _cache:
        return _cache[login]
    user = api.query(CREATED, login=login)["user"]
    now = dt.datetime.now(dt.timezone.utc)
    first = dt.datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    # One aliased contributionsCollection per calendar year (the API allows max 1 year each)
    parts = []
    for year in range(first.year, now.year + 1):
        start = max(first, dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc))
        end = min(now, dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc))
        parts.append(YEAR.format(year=year, start=start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                 end=end.strftime("%Y-%m-%dT%H:%M:%SZ")))
    query = "query($login: String!) { user(login: $login) {" + "".join(parts) + "} }"
    data = api.query(query, login=login)["user"]

    counts = {}
    for coll in data.values():
        for week in coll["contributionCalendar"]["weeks"]:
            for day in week["contributionDays"]:
                counts[day["date"]] = day["contributionCount"]
    today = now.date().isoformat()
    result = {
        "name": user["name"] or user["login"],
        "today": today,
        "days": sorted((d, c) for d, c in counts.items() if d <= today),
    }
    _cache[login] = result
    return result
