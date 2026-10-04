import csv
from pathlib import Path
import unittest

from forest_map_sheet_generator.core.codes import SheetCodeError, parse
from forest_map_sheet_generator.core.grid import _index, children, parent_from_point, sheet_from_code, sheets_covering_bbox


class GridTests(unittest.TestCase):
    def test_independent_fixed_expectations(self):
        with (Path(__file__).parent / "fixtures" / "expected_grids.csv").open(encoding="utf-8") as file:
            for expected in csv.DictReader(file):
                sheet = sheet_from_code(expected["code"])
                self.assertEqual(sheet.grid_type, expected["grid_type"])
                self.assertEqual((sheet.e_min, sheet.e_max, sheet.n_min, sheet.n_max), tuple(float(expected[key]) for key in ("e_min", "e_max", "n_min", "n_max")))
    def test_5000_order_and_total(self):
        sheets = children("04HE", "5000")
        self.assertEqual(len(sheets), 100); self.assertEqual(sheets[0].sheet_code, "04HE00"); self.assertEqual(sheets[-1].sheet_code, "04HE99")
        self.assertEqual(sum(s.width * s.height for s in sheets), 40_000 * 30_000)
    def test_quarters(self):
        sheets = children("04HE", "forest_quarter")
        self.assertEqual([s.sheet_code for s in sheets], ["04HE1", "04HE2", "04HE3", "04HE4"])
        self.assertEqual(sum(s.width * s.height for s in sheets), 40_000 * 30_000)
    def test_boundary_and_negative_floor(self):
        self.assertEqual(parent_from_point(4, 280000, 120000).sheet_code, "04HE")
        self.assertEqual(parent_from_point(4, 320000 - 1e-4, 150000 - 1e-4).sheet_code, "04HE")
        self.assertEqual(_index(-1, 40_000), -1)
        self.assertEqual(sheets_covering_bbox(4, 280000, 120000, 320000, 150000, "50000"), [sheet_from_code("04HE")])
    def test_code_roundtrip_and_rejection(self):
        for code in ("04HE", "04HE00", "04HE99", "04HE1", "19ZZ4"):
            item = sheet_from_code(code); centre = ((item.e_min + item.e_max) / 2, (item.n_min + item.n_max) / 2)
            self.assertEqual(sheet_from_code(code).sheet_code, code)
            self.assertTrue(centre[0] > item.e_min)
        for bad in ("00HE", "20HE", "04IE", "04HEA", "04HE5", "04HE000"):
            with self.assertRaises(SheetCodeError): parse(bad)
