"""Card registry: every module in this package is one card.

A card module must define:
    DESCRIPTION: str                      one-line description
    fetch(api, login, options) -> dict    collect data (JSON-serialisable!);
                                          options: {"include_private": bool}
    render(data, theme, title=None) -> str  return the SVG markup
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
