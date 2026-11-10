"""Top languages across your own (non-fork) repositories, by code size."""
from ..repo_filter import hidden, keep_repo
from ..svg import card, escape, bar
from ..themes import THEMES

DESCRIPTION = "Top languages by code size in your own repositories"
TOP = 8

QUERY = """
query($login: String!, $privacy: RepositoryPrivacy, $cursor: String) {
  user(login: $login) {
    name
    login
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, isFork: false, privacy: $privacy) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        isArchived
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


def fetch(api, login, options):
    # Public repos by default. With include_private, every repo the token can see
    # (private ones need a PAT). Only language names and sizes are kept, never repo names.
    privacy = None if options.get("include_private") else "PUBLIC"
    sizes, colors = {}, {}
    for page in api.paginate(QUERY, ["user", "repositories"], login=login, privacy=privacy):
        user = page["user"]
        for repo in user["repositories"]["nodes"]:
            if not keep_repo(repo, options):
                continue
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                sizes[name] = sizes.get(name, 0) + edge["size"]
                colors[name] = edge["node"]["color"]
    langs = sorted(sizes.items(), key=lambda kv: kv[1], reverse=True)
    return {
        "name": user["name"] or user["login"],
        "include_private": privacy is None,
        "languages": [{"name": n, "size": s, "color": colors[n]} for n, s in langs],
    }


def render(data, theme, options):
    # `hide` removes languages (case-insensitive); percentages are recomputed without them
    hide = hidden(options)
    langs = [l for l in data["languages"] if l["name"].lower() not in hide]
    total = sum(l["size"] for l in langs) or 1
    top, rest = langs[:TOP], langs[TOP:]
    items = [(l["name"], l["size"] / total, l["color"] or THEMES[theme]["accent"]) for l in top]
    if rest:
        items.append(("Other", sum(l["size"] for l in rest) / total, THEMES[theme]["track"]))

    body = [bar(theme, 25, 55, 445, 10, [(f, c) for _, f, c in items])]
    # Legend in two columns
    for i, (name, frac, color) in enumerate(items):
        col, row = i % 2, i // 2
        x, y = 25 + col * 230, 92 + row * 24
        body.append(
            f'<g class="fade" style="animation-delay:{150 + i * 100}ms">'
            f'<circle cx="{x + 5}" cy="{y - 4}" r="5" fill="{color}"/>'
            f'<text x="{x + 17}" y="{y}" class="label">{escape(name)}</text>'
            f'<text x="{x + 205}" y="{y}" text-anchor="end" class="value">{frac * 100:.1f}%</text></g>'
        )
    rows = (len(items) + 1) // 2
    height = 92 + max(rows, 1) * 24 + 16
    return card(theme, options.get("title") or "Most Used Languages", "".join(body), height=height)
