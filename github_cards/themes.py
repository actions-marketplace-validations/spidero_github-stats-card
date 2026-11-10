"""Color themes shared by all cards.

Keys: bg, border, title, label, value, accent, track.
The light theme writes github-<card>.svg, every other theme github-<card>-<theme>.svg.
"""

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
}
