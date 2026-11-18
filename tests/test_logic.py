"""Unit tests for pure helpers (no network)."""
import unittest

from github_cards.cards.activity import monthly, nice_max, series
from github_cards.cards.streak import streaks
from github_cards.repo_filter import hidden, keep_repo
from github_cards.svg import fmt_date, human
from github_cards.themes import THEMES, parse_colors


def days(pattern, start=1):
    """'0110' -> [('2026-01-01', 0), ('2026-01-02', 1), ...]"""
    return [(f"2026-01-{i + start:02d}", int(ch)) for i, ch in enumerate(pattern)]


class TestStreaks(unittest.TestCase):
    def check(self, pattern, current, longest):
        cur, best = streaks(days(pattern))
        self.assertEqual(cur["length"], current, f"current for {pattern}")
        self.assertEqual(best["length"], longest, f"longest for {pattern}")

    def test_basic(self):
        self.check("0110111", 3, 3)
        self.check("1111", 4, 4)
        self.check("0000", 0, 0)

    def test_today_empty_keeps_streak(self):
        # No contribution today yet: the streak ending yesterday is still current
        self.check("1110", 3, 3)

    def test_two_empty_days_break_streak(self):
        self.check("11101100", 0, 3)

    def test_empty_input(self):
        self.assertEqual(streaks([])[0]["length"], 0)

    def test_dates(self):
        cur, best = streaks(days("0111011"))
        self.assertEqual((best["start"], best["end"]), ("2026-01-02", "2026-01-04"))
        self.assertEqual((cur["start"], cur["end"]), ("2026-01-06", "2026-01-07"))


class TestFormatting(unittest.TestCase):
    def test_human(self):
        cases = {0: "0", 11: "11", 1167: "1167", 9999: "9999", 10000: "10k",
                 12345: "12.3k", 105128: "105.1k", 2_500_000: "2.5M", 1_000_000: "1M"}
        for n, expected in cases.items():
            self.assertEqual(human(n), expected, n)

    def test_fmt_date(self):
        self.assertEqual(fmt_date("2026-03-07"), "Mar 7, 2026")


class TestColors(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(parse_colors("accent=#ff0066, bg=#101010,bg2=#abc,track=#80808040,border=none"),
                         {"accent": "#ff0066", "bg": "#101010", "bg2": "#abc",
                          "track": "#80808040", "border": "none"})
        self.assertEqual(parse_colors(""), {})

    def test_rejects_injection_and_names(self):
        for bad in ['title=#f00"/><script>', "accent=red", "accent=#12", "accent=url(#x)"]:
            with self.assertRaises(ValueError, msg=bad):
                parse_colors(bad)

    def test_rejects_unknown_key(self):
        with self.assertRaises(ValueError):
            parse_colors("font=#fff")

    def test_all_theme_values_valid(self):
        for name, theme in THEMES.items():
            spec = ",".join(f"{k}={v}" for k, v in theme.items())
            parse_colors(spec)  # raises if a built-in theme has a bad value
            for key in ("bg", "border", "title", "label", "value", "accent", "track"):
                self.assertIn(key, theme, f"{name} misses {key}")


class TestFilters(unittest.TestCase):
    def test_keep_repo(self):
        repo = {"name": "Old-Repo", "isArchived": True}
        self.assertTrue(keep_repo(repo, {}))
        self.assertFalse(keep_repo(repo, {"exclude_repos": ["old-repo"]}))  # case-insensitive
        self.assertFalse(keep_repo(repo, {"exclude_archived": True}))
        self.assertTrue(keep_repo({"name": "x", "isArchived": False}, {"exclude_archived": True}))

    def test_hidden(self):
        self.assertEqual(hidden({"hide": ["Issues", "HTML"]}), {"issues", "html"})
        self.assertEqual(hidden({}), set())


class TestActivity(unittest.TestCase):
    def test_monthly(self):
        self.assertEqual(monthly([("2025-01-01", 2), ("2025-01-31", 3), ("2025-02-01", 1)]),
                         {"2025-01": 5, "2025-02": 1})

    def test_nice_max(self):
        self.assertEqual(nice_max(0), 4)
        self.assertEqual(nice_max(664), 800)
        self.assertEqual(nice_max(81), 100)
        for v in (5, 13, 99, 1001, 37000):
            self.assertGreaterEqual(nice_max(v), v)

    def test_series_auto_and_limit(self):
        data = {"today": "2026-03-10", "months": {"2023-05": 4, "2024-01": 0, "2026-02": 1}}
        line = series(data, 0, "line")
        self.assertEqual([y for y, _ in line], [2023, 2024, 2025, 2026])  # from first active year
        self.assertEqual(len(line[-1][1]), 3)  # current year stops at the current month
        self.assertEqual([y for y, _ in series(data, 0, "years")], [2024, 2025, 2026])
        self.assertEqual([y for y, _ in series(data, 1, "line")], [2026])

    def test_series_no_contributions(self):
        self.assertEqual(series({"today": "2026-01-05", "months": {}}, 0, "line"), [(2026, [0])])

if __name__ == "__main__":
    unittest.main()
