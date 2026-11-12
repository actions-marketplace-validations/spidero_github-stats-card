"""Color themes shared by all cards.

Keys: bg, border, title, label, value, accent, track; optional bg2 = gradient end
(top-left -> bottom-right). "none" is allowed for bg/border (transparent).
The light theme writes github-<card>.svg, every other theme github-<card>-<theme>.svg.
"""
import re

THEMES = {
    "light": {
        "bg": "#ffffff", "border": "#d0d7de", "title": "#0969da",
        "label": "#57606a", "value": "#1f2328", "accent": "#0969da",
        "track": "#d8e6f8",
    },
    "dark": {
        "bg": "#0d1117", "border": "#30363d", "title": "#58a6ff",
        "label": "#8b949e", "value": "#e6edf3", "accent": "#58a6ff",
        "track": "#1c2a3d",
    },
    # Softer dark grey
    "dimmed": {
        "bg": "#22272e", "border": "#444c56", "title": "#6cb6ff",
        "label": "#909dab", "value": "#cdd9e5", "accent": "#6cb6ff",
        "track": "#2d3a4a",
    },
    # Works on both light and dark pages: no background, mid-tone text
    "transparent": {
        "bg": "none", "border": "none", "title": "#3b82f6",
        "label": "#808a96", "value": "#808a96", "accent": "#3b82f6",
        "track": "#80808040",
    },
    # Deep navy gradient
    "midnight": {
        "bg": "#0b1026", "bg2": "#1b2150", "border": "#2a3166", "title": "#9ab8ff",
        "label": "#8d96c7", "value": "#e6e9ff", "accent": "#7aa2ff",
        "track": "#262c5a",
    },
    # Teal-to-violet dark gradient with mint accent
    "aurora": {
        "bg": "#0f2027", "bg2": "#2c1d4a", "border": "#2f4550", "title": "#7ef9e4",
        "label": "#9fb7c0", "value": "#effcfa", "accent": "#5ee6c8",
        "track": "#24414a",
    },
    # Warm light gradient
    "sunset": {
        "bg": "#fff6ec", "bg2": "#ffe1dc", "border": "#f3c9b5", "title": "#d9480f",
        "label": "#8a5a44", "value": "#3d1f12", "accent": "#f76707",
        "track": "#ffd8c2",
    },
    # Dark green
    "forest": {
        "bg": "#0d1a12", "bg2": "#132a1c", "border": "#24412d", "title": "#69db7c",
        "label": "#8fb39a", "value": "#e6f4ea", "accent": "#40c057",
        "track": "#1f3a27",
    },
    # Black and white, print-friendly
    "mono": {
        "bg": "#ffffff", "border": "#d4d4d4", "title": "#111111",
        "label": "#555555", "value": "#111111", "accent": "#111111",
        "track": "#e5e5e5",
    },
    # Maximum contrast (accessibility)
    "high-contrast": {
        "bg": "#000000", "border": "#ffffff", "title": "#ffd400",
        "label": "#ffffff", "value": "#ffffff", "accent": "#ffd400",
        "track": "#3a3a3a",
    },
}

KEYS = {"bg", "bg2", "border", "title", "label", "value", "accent", "track"}
COLOR_RE = re.compile(r"^(#[0-9a-fA-F]{3,8}|none)$")


def parse_colors(spec):
    """'accent=#ff0066,bg=#101010' -> dict; values are validated (they go into SVG)."""
    out = {}
    for item in filter(None, (s.strip() for s in spec.split(","))):
        key, _, value = item.partition("=")
        key, value = key.strip(), value.strip()
        if key not in KEYS:
            raise ValueError(f"unknown color key '{key}'; use: {', '.join(sorted(KEYS))}")
        if not COLOR_RE.match(value):
            raise ValueError(f"invalid color '{value}' for '{key}'; use #rgb, #rrggbb, #rrggbbaa or none")
        out[key] = value
    return out
