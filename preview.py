#!/usr/bin/env python3
"""Render every card in every theme from sample data into preview/index.html.

No token or network needed:  python3 preview.py [samples/spidero.json]
Refresh the sample data:     GITHUB_TOKEN=... python3 -m github_cards <login> /tmp/x --cards all --dump-data samples/<login>.json
"""
import os
import subprocess
import sys

from github_cards.__main__ import output_name
from github_cards.cards import load_cards
from github_cards.themes import THEMES

sample = sys.argv[1] if len(sys.argv) > 1 else "samples/spidero.json"
out = "preview"
subprocess.run([sys.executable, "-m", "github_cards", "--data", sample, "--cards", "all",
                "--themes", ",".join(THEMES), "x", out], check=True, stdout=subprocess.DEVNULL)

rows = []
for name, mod in load_cards().items():
    imgs = "".join(
        f'<div style="background:{THEMES[t]["bg"]};padding:16px"><img src="{output_name(name, t)}"></div>'
        for t in THEMES
    )
    rows.append(f"<h2>{name}</h2><p>{mod.DESCRIPTION}</p><div style='display:flex;flex-wrap:wrap;gap:8px'>{imgs}</div>")

with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
    f.write("<!doctype html><meta charset='utf-8'><title>Cards preview</title>"
            "<body style='font-family:sans-serif;margin:24px'>" + "".join(rows))
print(f"open {os.path.abspath(out)}/index.html")
