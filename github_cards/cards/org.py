"""Organization stats: stars, forks, repos, open issues/PRs, members, activity, languages."""
import datetime as dt

from ..repo_filter import hidden, keep_repo
from ..svg import THEMES, bar, card, escape, human, stat_row

DESCRIPTION = "Organization stats with top languages (set the `org` option)"
ROWS = ["stars", "forks", "repos", "active", "issues", "prs", "members"]
TOP = 5

QUERY = """
query($org: String!, $cursor: String) {
  organization(login: $org) {
    name
    login
    membersWithRole { totalCount }
    repositories(first: 100, after: $cursor, privacy: PUBLIC, isFork: false) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        isArchived
        stargazerCount
        forkCount
        pushedAt
        issues(states: OPEN) { totalCount }
        pullRequests(states: OPEN) { totalCount }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


def fetch(api, login, options):
    # Public repositories only (organization private data is never shown)
    org_login = options.get("org") or login
    month_ago = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)).isoformat()
    totals = {"stars": 0, "forks": 0, "repos": 0, "active": 0, "issues": 0, "prs": 0}
    sizes, colors = {}, {}
    for page in api.paginate(QUERY, ["organization", "repositories"], org=org_login):
        org = page["organization"]
        if org is None:
            raise SystemExit(f"organization '{org_login}' not found")
        for r in org["repositories"]["nodes"]:
            if not keep_repo(r, options):
                continue
            totals["repos"] += 1
            totals["stars"] += r["stargazerCount"]
            totals["forks"] += r["forkCount"]
            totals["issues"] += r["issues"]["totalCount"]
            totals["prs"] += r["pullRequests"]["totalCount"]
            if (r["pushedAt"] or "") >= month_ago[:19]:
                totals["active"] += 1
            for edge in r["languages"]["edges"]:
                name = edge["node"]["name"]
                sizes[name] = sizes.get(name, 0) + edge["size"]
                colors[name] = edge["node"]["color"]
    langs = sorted(sizes.items(), key=lambda kv: kv[1], reverse=True)
    return {
        "name": org["name"] or org["login"],
        "login": org["login"],
        "members": org["membersWithRole"]["totalCount"],
        **totals,
        "languages": [{"name": n, "size": s, "color": colors[n]} for n, s in langs],
    }


def render(data, theme, options):
    c = THEMES[theme]
    labels = {
        "stars": "Total stars",
        "forks": "Forks",
        "repos": "Public repos",
        "active": "Active repos (30 days)",
        "issues": "Open issues",
        "prs": "Open pull requests",
        "members": "Members",
    }
    hide = hidden(options)
    rows = [(labels[k], data[k]) for k in ROWS if k not in hide]
    body = [stat_row(theme, i, label, human(v), value_x=210) for i, (label, v) in enumerate(rows)]

    # Right column: top languages (hide also removes languages)
    langs = [l for l in data["languages"] if l["name"].lower() not in hide]
    total = sum(l["size"] for l in langs) or 1
    top = [(l["name"], l["size"] / total, l["color"] or c["accent"]) for l in langs[:TOP]]
    rest = 1 - sum(f for _, f, _ in top)
    body.append(f'<text x="290" y="70" class="label">Top languages</text>')
    for i, (name, frac, color) in enumerate(top):
        y = 94 + i * 20
        body.append(
            f'<g class="fade" style="animation-delay:{300 + i * 100}ms">'
            f'<circle cx="295" cy="{y - 4}" r="4.5" fill="{color}"/>'
            f'<text x="306" y="{y}" class="small" style="font-size:12px">{escape(name)}</text>'
            f'<text x="470" y="{y}" text-anchor="end" class="value" style="font-size:12px">{frac * 100:.1f}%</text></g>'
        )
    height = max(70 + len(rows) * 22 + 34, 94 + TOP * 20 + 34)
    parts = [(f, col) for _, f, col in top] + ([(rest, c["track"])] if rest > 0.001 else [])
    body.append(bar(theme, 25, height - 42, 445, 8, parts))
    return card(theme, options.get("title") or f"{data['name']} · Organization", "".join(body), height=height + 8)
