"""Run with QGIS Python. A skipped test is not a successful integration run."""
import os
import sqlite3
import tempfile
import unittest
import zipfile

try:
    from qgis.core import (QgsApplication, QgsCoordinateReferenceSystem, QgsGeometry,
                           QgsVectorLayer, QgsFeature, QgsField)
    from qgis.PyQt.QtCore import QVariant
except ImportError as error:
    raise unittest.SkipTest(f"QGIS Python unavailable: {error}")

from forest_map_sheet_generator.core.grid import sheet_from_code
from forest_map_sheet_generator.qgis_adapter.generator import GenerationCancelled, generate_for_geometry, transformed_geometry
from forest_map_sheet_generator.qgis_adapter.writer import write_sheets
from forest_map_sheet_generator.qgis_adapter.zones import ZoneLayerError, automatic_zones, coverage_warnings, validate_zone_layer


class QgisIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication([], False)
        cls.app.initQgis()

    @classmethod
    def tearDownClass(cls):
        cls.app.exitQgis()

    def test_gpkg_roundtrip_provenance_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "grid.gpkg")
            self.assertEqual(write_sheets(path, 4, "50000", [sheet_from_code("04HE")],
                                          "0.1.0-dev", commit="a" * 40, zone_data_version="v2026.1"), "grid_z04_50000")
            layer = QgsVectorLayer(f"{path}|layername=grid_z04_50000", "grid", "ogr")
            self.assertTrue(layer.isValid())
            self.assertEqual(layer.crs().authid(), "EPSG:6672")
            self.assertEqual(layer.featureCount(), 1)
            feature = next(layer.getFeatures())
            self.assertEqual(feature["sheet_code"], "04HE")
            self.assertEqual((feature["e_min"], feature["e_max"], feature["n_min"], feature["n_max"]),
                             (0.0, 40000.0, 60000.0, 90000.0))
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute('SELECT "commit", zone_data_version FROM forest_map_sheet_provenance').fetchone(),
                                 ("a" * 40, "v2026.1"))
            with self.assertRaises(FileExistsError):
                write_sheets(path, 4, "50000", [sheet_from_code("04HE")], "0.1.0-dev")

    def test_zone_coverage_and_positive_area(self):
        layer = QgsVectorLayer("Polygon?crs=EPSG:6668", "zones", "memory")
        layer.dataProvider().addAttributes([QgsField("ZONE", QVariant.Int)])
        layer.updateFields()
        feature = QgsFeature(layer.fields())
        feature.setAttribute("ZONE", 4)
        feature.setGeometry(QgsGeometry.fromWkt("POLYGON((0 0,10 0,10 10,0 10,0 0))"))
        layer.dataProvider().addFeature(feature)
        zones = validate_zone_layer(layer)
        self.assertEqual(set(automatic_zones(QgsGeometry.fromWkt("POLYGON((5 5,15 5,15 15,5 15,5 5))"), zones)), {4})
        touching = QgsGeometry.fromWkt("POLYGON((10 0,15 0,15 5,10 5,10 0))")
        self.assertEqual(automatic_zones(touching, zones), {})
        warnings = coverage_warnings(touching, zones)
        self.assertTrue(any("覆われない" in warning for warning in warnings))
        self.assertTrue(any("含まれない系" in warning for warning in warnings))
        invalid = QgsVectorLayer("Polygon?crs=EPSG:6668", "bad", "memory")
        invalid.dataProvider().addAttributes([QgsField("ZONE", QVariant.Int)])
        invalid.updateFields()
        bad_feature = QgsFeature(invalid.fields())
        bad_feature.setAttribute("ZONE", 20)
        bad_feature.setGeometry(feature.geometry())
        invalid.dataProvider().addFeature(bad_feature)
        with self.assertRaises(ZoneLayerError):
            validate_zone_layer(invalid)
        invalid_epsg = QgsVectorLayer("Polygon?crs=EPSG:6668", "bad-epsg", "memory")
        invalid_epsg.dataProvider().addAttributes([QgsField("ZONE", QVariant.Int), QgsField("EPSG", QVariant.Int)])
        invalid_epsg.updateFields()
        epsg_feature = QgsFeature(invalid_epsg.fields())
        epsg_feature.setAttributes([4, 6669])
        epsg_feature.setGeometry(feature.geometry())
        invalid_epsg.dataProvider().addFeature(epsg_feature)
        with self.assertRaises(ZoneLayerError):
            validate_zone_layer(invalid_epsg)

    def test_transformed_geometry_densifies_and_cancel_aborts(self):
        geometry = QgsGeometry.fromWkt("POLYGON((139 34,140 34,140 35,139 35,139 34))")
        src = QgsCoordinateReferenceSystem("EPSG:6668")
        dst = QgsCoordinateReferenceSystem("EPSG:6672")
        transformed = transformed_geometry(geometry, src, dst)
        self.assertGreater(len(transformed.asPolygon()[0]), 5)
        # A no-op CRS still exercises cancellation before the first intersection.
        sheet = sheet_from_code("04HE")
        target = QgsGeometry.fromWkt("POLYGON((1 60001,2 60001,2 60002,1 60002,1 60001))")
        with self.assertRaises(GenerationCancelled):
            generate_for_geometry(target, dst, 4, "50000", cancel=lambda: True)
