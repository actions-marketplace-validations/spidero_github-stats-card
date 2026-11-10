"""Shared repository filtering (exclude_repos / exclude_archived)."""


def keep_repo(repo, options):
    """True if `repo` (GraphQL node with name, isArchived) should be counted."""
    excluded = {r.lower() for r in options.get("exclude_repos", [])}
    if repo["name"].lower() in excluded:
        return False
    if options.get("exclude_archived") and repo.get("isArchived"):
        return False
    return True


def hidden(options):
    """Lower-cased set of names from the `hide` option."""
    return {h.lower() for h in options.get("hide", [])}
