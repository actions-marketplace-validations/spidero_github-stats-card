#!/usr/bin/env python3
"""Usage report for this repository (stdlib only).

Collects repository traffic (views, clones, referrers) and searches public code
for references to the repository (e.g. `uses: owner/repo@v1`), merges the
results into a history kept in DATA_DIR and writes a Markdown report.

The traffic API keeps only the last 14 days, so the history is merged by day
on every run. Code search results remember when each repository was first seen.

Environment:
  GH_TOKEN    token; traffic needs push access (fine-grained: "Administration: read")
  REPO        owner/name (defaults to GITHUB_REPOSITORY)
  DATA_DIR    directory with the history files (default: usage)
  QUERY       code search query (default: the repository name, "owner/name")
  INCLUDE_OWN "true" to keep the owner's own repositories in the code search results
"""
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"


def api_get(path, token, params=None):
    url = f"{API}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "github-stats-card-usage",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


# --- pure merge helpers (unit tested) ---------------------------------------

def merge_daily(history, api_items):
    """Merge traffic API "views"/"clones" items into {date: {count, uniques}}.

    The newest value for a day wins (the current day is still growing).
    """
    merged = dict(history)
    for item in api_items:
        day = item["timestamp"][:10]
        merged[day] = {"count": item["count"], "uniques": item["uniques"]}
    return dict(sorted(merged.items()))


def merge_search(history, hits, today):
    """Merge code search hits [(repo, path)] into {repo: {first_seen, last_seen, paths}}."""
    merged = {k: dict(v) for k, v in history.items()}
    for repo, path in hits:
        entry = merged.setdefault(repo, {"first_seen": today, "paths": []})
        entry["last_seen"] = today
        if path not in entry["paths"]:
            entry["paths"] = sorted(entry["paths"] + [path])
    return dict(sorted(merged.items()))


def totals(daily, since=None):
    days = [v for d, v in daily.items() if since is None or d >= since]
    return sum(v["count"] for v in days), sum(v["uniques"] for v in days)


# --- report -----------------------------------------------------------------

def render(repo, traffic, search, today, errors):
    since14 = (datetime.date.fromisoformat(today) - datetime.timedelta(days=13)).isoformat()
    v14, vu14 = totals(traffic.get("views", {}), since14)
    c14, cu14 = totals(traffic.get("clones", {}), since14)
    v_all, _ = totals(traffic.get("views", {}))
    c_all, _ = totals(traffic.get("clones", {}))
    first = min(traffic.get("views", {}) or [today])

    out = [f"# Usage of {repo}", "", f"Updated: {today}", ""]
    if errors:
        out += ["> **Warnings**", ">"] + [f"> - {e}" for e in errors] + [""]
    out += [
        "## Traffic",
        "",
        "| | Last 14 days | Unique (sum of daily) | Since " + first + " |",
        "|---|--:|--:|--:|",
        f"| Views | {v14} | {vu14} | {v_all} |",
        f"| Clones | {c14} | {cu14} | {c_all} |",
        "",
        "Clones include bots, scanners and CI checkouts; they are not users.",
        "",
    ]
    stars = traffic.get("repo", {})
    if stars:
        out += [f"Stars: **{stars.get('stars', 0)}**, forks: **{stars.get('forks', 0)}**", ""]
    refs = traffic.get("referrers", [])
    if refs:
        out += ["### Referrers (14 days)", "", "| Source | Views | Unique |", "|---|--:|--:|"]
        out += [f"| {r['referrer']} | {r['count']} | {r['uniques']} |" for r in refs]
        out += [""]

    out += ["## Repositories referencing the project (code search)", ""]
    if not search:
        out += ["None found yet.", ""]
    else:
        new = [r for r, v in search.items() if v["first_seen"] >= since14]
        out += [f"Total: **{len(search)}**, new in the last 14 days: **{len(new)}**", "",
                "| Repository | Files | First seen | Last seen |", "|---|---|---|---|"]
        for r, v in sorted(search.items(), key=lambda kv: kv[1]["first_seen"], reverse=True):
            files = "<br>".join(f"[{p}](https://github.com/{r}/blob/HEAD/{p})" for p in v["paths"])
            mark = " 🆕" if r in new else ""
            out.append(f"| [{r}](https://github.com/{r}){mark} | {files} | {v['first_seen']} | {v.get('last_seen', '')} |")
        out += ["", "Code search covers public repositories only and indexes new files with a delay.", ""]
    return "\n".join(out)


def code_search(query, token):
    hits = []
    for page in range(1, 11):  # API returns at most 1000 results
        data = api_get("/search/code", token, {"q": query, "per_page": 100, "page": page})
        items = data.get("items", [])
        hits += [(i["repository"]["full_name"], i["path"]) for i in items]
        if len(items) < 100:
            break
        time.sleep(7)  # code search: 10 requests per minute
    return hits


def main():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("REPO") or os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        sys.exit("GH_TOKEN and REPO (or GITHUB_REPOSITORY) are required")
    data_dir = os.environ.get("DATA_DIR", "usage")
    query = os.environ.get("QUERY") or f'"{repo}"'
    include_own = os.environ.get("INCLUDE_OWN", "").lower() == "true"
    owner = repo.split("/")[0].lower()
    today = datetime.date.today().isoformat()
    os.makedirs(data_dir, exist_ok=True)

    traffic_path = os.path.join(data_dir, "traffic.json")
    search_path = os.path.join(data_dir, "code-search.json")
    traffic = load_json(traffic_path, {"views": {}, "clones": {}})
    search = load_json(search_path, {})
    errors = []

    try:
        r = api_get(f"/repos/{repo}", token)
        traffic["repo"] = {"stars": r["stargazers_count"], "forks": r["forks_count"]}
    except urllib.error.HTTPError as e:
        errors.append(f"repository info: HTTP {e.code}")

    for kind in ("views", "clones"):
        try:
            data = api_get(f"/repos/{repo}/traffic/{kind}", token)
            traffic[kind] = merge_daily(traffic.get(kind, {}), data.get(kind, []))
        except urllib.error.HTTPError as e:
            errors.append(f"traffic/{kind}: HTTP {e.code} (token needs push access / Administration: read)")
    try:
        traffic["referrers"] = api_get(f"/repos/{repo}/traffic/popular/referrers", token)
    except urllib.error.HTTPError as e:
        errors.append(f"traffic/referrers: HTTP {e.code}")

    try:
        hits = code_search(query, token)
        hits = [(r, p) for r, p in hits
                if r.lower() != repo.lower() and (include_own or r.split("/")[0].lower() != owner)]
        search = merge_search(search, hits, today)
    except urllib.error.HTTPError as e:
        errors.append(f"code search: HTTP {e.code} (needs a personal access token)")

    save_json(traffic_path, traffic)
    save_json(search_path, search)
    report = render(repo, traffic, search, today, errors)
    with open(os.path.join(data_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(report)

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(report + "\n")
    print(report)


if __name__ == "__main__":
    main()
