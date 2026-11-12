"""Minimal GitHub GraphQL client (stdlib only)."""
import json
import urllib.request

API_URL = "https://api.github.com/graphql"


class GitHubAPI:
    def __init__(self, token):
        self.token = token

    def query(self, query, **variables):
        """Run a GraphQL query and return its "data" object (exit on errors)."""
        payload = self._post(query, variables)
        if payload.get("errors"):
            raise SystemExit(f"GraphQL error: {payload['errors']}")
        return payload["data"]

    def try_query(self, query, **variables):
        """Like query(), but return None on GraphQL errors (e.g. fields the token can't access)."""
        payload = self._post(query, variables)
        return None if payload.get("errors") else payload["data"]

    def _post(self, query, variables):
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
            return json.load(resp)

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
