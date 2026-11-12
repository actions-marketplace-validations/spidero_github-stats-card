"""Render every card in every theme from sample data and check the SVG output."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from github_cards.cards import load_cards
from github_cards.themes import THEMES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.path.join(ROOT, "samples", "spidero.json")
NS = "{http://www.w3.org/2000/svg}"


def texts(svg):
    return [t.text or "" for t in ET.fromstring(svg).iter(f"{NS}text")]


class TestRender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(SAMPLE, encoding="utf-8") as f:
            cls.data = json.load(f)
        cls.cards = load_cards()

    def test_sample_has_every_card(self):
        self.assertEqual(set(self.cards), set(self.data))

    def test_every_card_every_theme_is_valid_svg(self):
        for name, mod in self.cards.items():
            for theme in THEMES:
                with self.subTest(card=name, theme=theme):
                    svg = mod.render(self.data[name], theme, {})
                    root = ET.fromstring(svg)  # well-formed XML
                    self.assertEqual(root.tag, f"{NS}svg")
                    self.assertTrue(any(texts(svg)), "card has no text")

    def test_content_visible_without_animation(self):
        # Regression: nothing may start hidden (opacity: 0 outside @keyframes)
        for name, mod in self.cards.items():
            svg = mod.render(self.data[name], "light", {})
            css = svg.split("<style>", 1)[1].split("</style>", 1)[0]
            outside_keyframes = css.split("@keyframes")[0]
            self.assertNotIn("opacity: 0", outside_keyframes, name)

    def test_title_option_and_escaping(self):
        svg = self.cards["stats"].render(self.data["stats"], "dark", {"title": "A & <B>"})
        self.assertIn("A & <B>", texts(svg))

    def test_hide_stats_rows(self):
        svg = self.cards["stats"].render(self.data["stats"], "light", {"hide": ["issues", "private"]})
        joined = " ".join(texts(svg))
        self.assertNotIn("Issues:", joined)
        self.assertNotIn("Private contributions", joined)
        self.assertIn("Pull requests:", joined)

    def test_hide_languages_recomputes(self):
        data = self.data["languages"]
        first = data["languages"][0]["name"]
        svg = self.cards["languages"].render(data, "light", {"hide": [first]})
        self.assertNotIn(first, texts(svg))

    def test_org_without_members(self):
        data = dict(self.data["org"], members=None)
        svg = self.cards["org"].render(data, "light", {})
        self.assertNotIn("Members:", " ".join(texts(svg)))

    def test_credit_toggle(self):
        from github_cards import svg as svgmod
        try:
            svgmod.SHOW_CREDIT = False
            svg = self.cards["stats"].render(self.data["stats"], "light", {})
            self.assertNotIn("spidero/github-stats-card", texts(svg))
        finally:
            svgmod.SHOW_CREDIT = True


class TestCLI(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "github_cards", *args],
                              cwd=ROOT, capture_output=True, text=True)

    def test_data_mode_writes_files(self):
        with tempfile.TemporaryDirectory() as out:
            r = self.run_cli("--data", SAMPLE, "--cards", "all", "--org", "x",
                             "--themes", "light,dark,transparent", "x", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            files = set(os.listdir(out))
            for card in load_cards():
                self.assertIn(f"github-{card}.svg", files)
                self.assertIn(f"github-{card}-dark.svg", files)
                self.assertIn(f"github-{card}-transparent.svg", files)

    def test_all_skips_org_without_org_option(self):
        with tempfile.TemporaryDirectory() as out:
            r = self.run_cli("--data", SAMPLE, "--cards", "all", "x", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn("github-org.svg", os.listdir(out))

    def test_errors(self):
        self.assertNotEqual(self.run_cli("--data", SAMPLE, "--cards", "nope", "x", "/tmp").returncode, 0)
        self.assertNotEqual(self.run_cli("--data", SAMPLE, "--themes", "nope", "x", "/tmp").returncode, 0)
        self.assertNotEqual(self.run_cli("--data", SAMPLE, "--colors", "accent=red", "x", "/tmp").returncode, 0)


if __name__ == "__main__":
    unittest.main()
