"""General stats: stars, commits, PRs, issues, ... plus yearly contributions ring."""
import datetime as dt

from ..svg import card, human, ring, stat_row

DESCRIPTION = "General GitHub stats with a yearly contributions ring"

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
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes { stargazerCount forkCount }
    }
  }
}
"""


def fetch(api, login, options):
    # Repo counts/stars are public-only by design; options are not used here
    year = dt.datetime.now(dt.timezone.utc).year
    stars = forks = 0
    for page in api.paginate(QUERY, ["user", "repositories"],
                             login=login, **{"from": f"{year}-01-01T00:00:00Z"}):
        user = page["user"]
        stars += sum(r["stargazerCount"] for r in user["repositories"]["nodes"])
        forks += sum(r["forkCount"] for r in user["repositories"]["nodes"])
    return {
        "name": user["name"] or user["login"],
        "year": year,
        "stars": stars,
        "forks": forks,
        "repos": user["repositories"]["totalCount"],
        "commits": user["thisYear"]["totalCommitContributions"],
        "prs": user["pullRequests"]["totalCount"],
        "issues": user["issues"]["totalCount"],
        "contributed": user["repositoriesContributedTo"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "contributions": user["lastYear"]["contributionCalendar"]["totalContributions"],
        # Private contributions are only exposed as one total (not split by type)
        "private": user["lastYear"]["restrictedContributionsCount"],
    }


def render(data, theme, title=None):
    rows = [
        ("Total stars", data["stars"]),
        (f"Commits ({data['year']})", data["commits"]),
        ("Private contributions (last year)", data["private"]),
        ("Pull requests", data["prs"]),
        ("Issues", data["issues"]),
        ("Contributed to (last year)", data["contributed"]),
        ("Public repos", data["repos"]),
    ]
    body = "".join(stat_row(theme, i, label, human(v)) for i, (label, v) in enumerate(rows))
    body += ring(theme, 410, 122, 50, human(data["contributions"]),
                 ("contributions", "last year"))
    return card(theme, title or f"{data['name']}'s GitHub Stats", body, height=232)
