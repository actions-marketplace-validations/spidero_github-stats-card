"""Unit tests for scripts/usage_report.py merge helpers (no network)."""
import importlib.util
import pathlib
import unittest

_path = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "usage_report.py"
_spec = importlib.util.spec_from_file_location("usage_report", _path)
usage = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(usage)


class TestMergeDaily(unittest.TestCase):
    def test_keeps_old_days_and_updates_overlap(self):
        history = {"2026-10-01": {"count": 5, "uniques": 2}, "2026-10-02": {"count": 1, "uniques": 1}}
        api = [{"timestamp": "2026-10-02T00:00:00Z", "count": 4, "uniques": 3},
               {"timestamp": "2026-10-03T00:00:00Z", "count": 2, "uniques": 1}]
        merged = usage.merge_daily(history, api)
        self.assertEqual(list(merged), ["2026-10-01", "2026-10-02", "2026-10-03"])
        self.assertEqual(merged["2026-10-02"], {"count": 4, "uniques": 3})
        self.assertEqual(usage.totals(merged), (11, 6))
        self.assertEqual(usage.totals(merged, since="2026-10-02"), (6, 4))


class TestMergeSearch(unittest.TestCase):
    def test_first_seen_is_kept(self):
        h = usage.merge_search({}, [("a/b", ".github/workflows/x.yml")], "2026-10-01")
        h = usage.merge_search(h, [("a/b", ".github/workflows/y.yml"), ("c/d", "w.yml")], "2026-10-08")
        self.assertEqual(h["a/b"]["first_seen"], "2026-10-01")
        self.assertEqual(h["a/b"]["last_seen"], "2026-10-08")
        self.assertEqual(h["a/b"]["paths"], [".github/workflows/x.yml", ".github/workflows/y.yml"])
        self.assertEqual(h["c/d"]["first_seen"], "2026-10-08")


class TestRender(unittest.TestCase):
    def test_report_contains_totals_and_new_marker(self):
        traffic = {"views": {"2026-11-10": {"count": 7, "uniques": 2}}, "clones": {}}
        search = {"x/y": {"first_seen": "2026-11-10", "last_seen": "2026-11-12", "paths": ["a.yml"]}}
        md = usage.render("o/r", traffic, search, "2026-11-12", ["oops"])
        self.assertIn("| Views | 7 | 2 | 7 |", md)
        self.assertIn("[x/y](https://github.com/x/y) 🆕", md)
        self.assertIn("oops", md)


if __name__ == "__main__":
    unittest.main()
