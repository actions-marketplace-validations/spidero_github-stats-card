"""Card registry: every module in this package is one card.

A card module must define:
    DESCRIPTION: str                      one-line description
    fetch(api, login, options) -> dict    collect data (JSON-serialisable!)
    render(data, theme, options) -> str   return the SVG markup
options (same dict for both): title, hide, include_private, exclude_repos, exclude_archived,
org, activity_style, activity_years
(see github_cards/__main__.py); cards use what they support and ignore the rest.
Optional: variants(options) -> [(suffix, options)] to write several files from the same data
(file github-<name><suffix>[-<theme>].svg).
The module name is the card name; output files are github-<name>[-<theme>].svg.
"""
import importlib
import pkgutil


def load_cards():
    cards = {}
    for info in pkgutil.iter_modules(__path__):
        if info.name.startswith("_"):
            continue
        mod = importlib.import_module(f"{__name__}.{info.name}")
        cards[info.name] = mod
    return cards
