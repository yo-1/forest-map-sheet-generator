"""Run explicitly under QGIS Python; ordinary unit runs must not count as this test."""
import os
import tempfile
import unittest

try:
    from qgis.core import QgsApplication
except ImportError as error:
    raise unittest.SkipTest(f"QGIS Python unavailable: {error}")

from forest_map_sheet_generator.core.grid import sheet_from_code
from forest_map_sheet_generator.qgis_adapter.writer import write_sheets


class QgisIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication([], False); cls.app.initQgis()
    @classmethod
    def tearDownClass(cls): cls.app.exitQgis()
    def test_gpkg_roundtrip_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "grid.gpkg")
            self.assertEqual(write_sheets(path, 4, "50000", [sheet_from_code("04HE")], "0.1.0-dev"), "grid_z04_50000")
            with self.assertRaises(FileExistsError): write_sheets(path, 4, "50000", [sheet_from_code("04HE")], "0.1.0-dev")
