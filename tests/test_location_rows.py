"""Offline row lifecycle tests, without GTK, settings, or network access."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import unittest


class PreferencesGroup:
    """Only the public add/remove API used by the location list."""

    def __init__(self):
        self.rows = []
        self.header_suffix = object()

    def add(self, row):
        self.rows.append(row)

    def remove(self, row):
        self.rows.remove(row)


class LocationRowsTest(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).resolve().parents[1] / "src/windowLocations.py"
        tree = ast.parse(source.read_text())
        window = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                      and n.name == "WeatherLocations")
        refresh = next(n for n in window.body if isinstance(n, ast.FunctionDef)
                       and n.name == "_refresh_list")
        self.settings = SimpleNamespace(added_cities=[])
        namespace = {"settings": self.settings,
                     "LocationData": SimpleNamespace(from_storage_string=json.loads)}
        exec(compile(ast.Module(body=[refresh], type_ignores=[]), str(source), "exec"),
             namespace)
        self.refresh = namespace["_refresh_list"]
        self.group = PreferencesGroup()
        self.window = SimpleNamespace(location_grp=self.group, location_rows=[],
                                      _create_row=lambda city: SimpleNamespace(city=city))

    def test_empty_list_preserves_header(self):
        header = self.group.header_suffix
        self.refresh(self.window)
        self.assertEqual(self.group.rows, [])
        self.assertIs(self.group.header_suffix, header)

    def test_refresh_replaces_rows_without_duplicates(self):
        self.settings.added_cities = [json.dumps({"name": "Synthetic A"}), "",
                                     json.dumps({"name": "Synthetic B"})]
        self.refresh(self.window)
        old_rows = list(self.group.rows)
        self.refresh(self.window)
        self.assertEqual([r.city["name"] for r in self.group.rows],
                         ["Synthetic A", "Synthetic B"])
        self.assertTrue(all(a is not b for a, b in zip(old_rows, self.group.rows)))
        self.assertEqual(self.window.location_rows, self.group.rows)

    def test_refresh_after_removing_all_locations(self):
        self.settings.added_cities = [json.dumps({"name": "Synthetic"})]
        self.refresh(self.window)
        self.settings.added_cities = []
        self.refresh(self.window)
        self.assertEqual(self.group.rows, [])
        self.assertEqual(self.window.location_rows, [])


if __name__ == "__main__":
    unittest.main()
