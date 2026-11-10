"""General stats: stars, commits, PRs, issues, ... plus yearly contributions ring."""
import datetime as dt

from ..repo_filter import hidden, keep_repo
from ..svg import card, human, ring, stat_row

DESCRIPTION = "General GitHub stats with a yearly contributions ring"
# Row keys usable in `hide` (in display order)
ROWS = ["stars", "commits", "private", "prs", "issues", "contributed", "repos"]

QUERY = """
query($login: String!, $from: DateTime!, $cursor: String) {
  user(login: $login) {
    name
    login
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositoriesContributedTo(
      first: 1
      contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, PULL_REQUEST_REVIEW]
    ) { totalCount }
    thisYear: contributionsCollection(from: $from) { totalCommitContributions }
    lastYear: contributionsCollection {
      contributionCalendar { totalContributions }
      restrictedContributionsCount
    }
    repositories(
      first: 100, after: $cursor, ownerAffiliations: OWNER,
      isFork: false, privacy: PUBLIC
    ) {
      pageInfo { hasNextPage endCursor }
      nodes { name isArchived stargazerCount forkCount }
    }
  }
}
"""


def fetch(api, login, options):
    # Repo-based numbers (stars, repos) are public-only by design and honour
    # exclude_repos / exclude_archived
    year = dt.datetime.now(dt.timezone.utc).year
    stars = forks = repos = 0
    for page in api.paginate(QUERY, ["user", "repositories"],
                             login=login, **{"from": f"{year}-01-01T00:00:00Z"}):
        user = page["user"]
        for r in user["repositories"]["nodes"]:
            if keep_repo(r, options):
                repos += 1
                stars += r["stargazerCount"]
                forks += r["forkCount"]
    return {
        "name": user["name"] or user["login"],
        "year": year,
        "stars": stars,
        "forks": forks,
        "repos": repos,
        "commits": user["thisYear"]["totalCommitContributions"],
        "prs": user["pullRequests"]["totalCount"],
        "issues": user["issues"]["totalCount"],
        "contributed": user["repositoriesContributedTo"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "contributions": user["lastYear"]["contributionCalendar"]["totalContributions"],
        # Private contributions are only exposed as one total (not split by type)
        "private": user["lastYear"]["restrictedContributionsCount"],
    }


def render(data, theme, options):
    labels = {
        "stars": "Total stars",
        "commits": f"Commits ({data['year']})",
        "private": "Private contributions (last year)",
        "prs": "Pull requests",
        "issues": "Issues",
        "contributed": "Contributed to (last year)",
        "repos": "Public repos",
    }
    hide = hidden(options)
    rows = [(labels[k], data[k]) for k in ROWS if k not in hide]
    body = "".join(stat_row(theme, i, label, human(v)) for i, (label, v) in enumerate(rows))
    # Height follows the number of rows, but always leaves room for the ring
    height = max(70 + len(rows) * 22 + 10, 175)
    body += ring(theme, 410, (height + 20) // 2, 50, human(data["contributions"]),
                 ("contributions", "last year"))
    return card(theme, options.get("title") or f"{data['name']}'s GitHub Stats", body, height=height)
