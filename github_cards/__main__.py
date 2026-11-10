"""CLI: python3 -m github_cards <login> <out_dir> [--cards stats,languages] [--themes light,dark]"""
import argparse
import json
import os

from . import svg
from .api import GitHubAPI
from .cards import load_cards
from .themes import THEMES


def split(value):
    return [v.strip() for v in value.split(",") if v.strip()]


def output_name(card, theme):
    return f"github-{card}.svg" if theme == "light" else f"github-{card}-{theme}.svg"


def main():
    cards = load_cards()
    ap = argparse.ArgumentParser(prog="github_cards", description="Generate GitHub stats cards (SVG).")
    ap.add_argument("login", nargs="?", help="GitHub username")
    ap.add_argument("out_dir", nargs="?", default="dist", help="directory for the SVG files (default: dist)")
    ap.add_argument("--cards", default="stats", help=f"comma-separated, 'all' for every card: {', '.join(cards)}")
    ap.add_argument("--themes", default="light,dark", help=f"comma-separated: {', '.join(THEMES)}")
    ap.add_argument("--title", default="", help="custom title (applies to every selected card)")
    ap.add_argument("--include-private", action="store_true",
                    help="cards that support it also use private repos (needs a PAT)")
    ap.add_argument("--hide", default="",
                    help="comma-separated items to hide: stats rows (stars, commits, private, prs, "
                         "issues, contributed, repos) and/or language names")
    ap.add_argument("--exclude-repos", default="", help="comma-separated repository names to skip")
    ap.add_argument("--exclude-archived", action="store_true", help="skip archived repositories")
    ap.add_argument("--no-credit", action="store_true",
                    help="hide the small project link in the bottom-left corner")
    ap.add_argument("--data", help="render from a JSON file (from --dump-data) instead of the API")
    ap.add_argument("--dump-data", help="also save fetched data to this JSON file")
    ap.add_argument("--list", action="store_true", help="list available cards and exit")
    args = ap.parse_args()

    if args.list:
        for name, mod in cards.items():
            print(f"{name:12} {mod.DESCRIPTION}")
        return

    names = list(cards) if args.cards.strip() == "all" else split(args.cards)
    themes = split(args.themes)
    if not names or set(names) - set(cards):
        ap.error(f"unknown card(s): {sorted(set(names) - set(cards))}; available: {', '.join(cards)}")
    if not themes or set(themes) - set(THEMES):
        ap.error(f"unknown theme(s): {sorted(set(themes) - set(THEMES))}; available: {', '.join(THEMES)}")

    options = {
        "title": args.title or None,
        "hide": split(args.hide),
        "include_private": args.include_private,
        "exclude_repos": split(args.exclude_repos),
        "exclude_archived": args.exclude_archived,
    }

    if args.data:
        with open(args.data, encoding="utf-8") as f:
            data = json.load(f)
        missing = [n for n in names if n not in data]
        if missing:
            ap.error(f"no data for card(s) {missing} in {args.data}")
    else:
        if not args.login:
            ap.error("login is required (unless --data is used)")
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("GITHUB_TOKEN is not set")
        api = GitHubAPI(token)
        data = {n: cards[n].fetch(api, args.login, options) for n in names}
        print(json.dumps(data, indent=2))

    if args.dump_data:
        os.makedirs(os.path.dirname(os.path.abspath(args.dump_data)), exist_ok=True)
        with open(args.dump_data, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        print(f"wrote {args.dump_data}")

    svg.SHOW_CREDIT = not args.no_credit
    os.makedirs(args.out_dir, exist_ok=True)
    for name in names:
        for theme in themes:
            path = os.path.join(args.out_dir, output_name(name, theme))
            with open(path, "w", encoding="utf-8") as f:
                f.write(cards[name].render(data[name], theme, options))
            print(f"wrote {path}")


if __name__ == "__main__":
    main()
