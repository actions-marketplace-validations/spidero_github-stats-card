"""Minimal GitHub GraphQL client (stdlib only)."""
import json
import urllib.request

API_URL = "https://api.github.com/graphql"


class GitHubAPI:
    def __init__(self, token):
        self.token = token

    def query(self, query, **variables):
        """Run a GraphQL query and return its "data" object."""
        req = urllib.request.Request(
            API_URL,
            data=json.dumps({"query": query, "variables": variables}).encode(),
            headers={
                "Authorization": f"bearer {self.token}",
                "Content-Type": "application/json",
                "User-Agent": "github-stats-card",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.load(resp)
        if payload.get("errors"):
            raise SystemExit(f"GraphQL error: {payload['errors']}")
        return payload["data"]

    def paginate(self, query, path, **variables):
        """Yield every page of a connection.

        `path` points to the connection inside "data" (e.g. ["user", "repositories"]);
        the query must accept `$cursor: String` and select `pageInfo { hasNextPage endCursor }`.
        Each yielded item is the full "data" object of one page.
        """
        cursor = None
        while True:
            data = self.query(query, cursor=cursor, **variables)
            yield data
            conn = data
            for key in path:
                conn = conn[key]
            if not conn["pageInfo"]["hasNextPage"]:
                return
            cursor = conn["pageInfo"]["endCursor"]
