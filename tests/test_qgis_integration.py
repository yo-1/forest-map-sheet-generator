"""Run explicitly under QGIS Python; ordinary unit runs must not count as this test."""
import os
import tempfile
import unittest

try:
    from qgis.core import QgsApplication, QgsFeature, QgsField, QgsGeometry, QgsVectorLayer
    from qgis.PyQt.QtCore import QVariant
except ImportError as error:
    raise unittest.SkipTest(f"QGIS Python unavailable: {error}")

from forest_map_sheet_generator.core.grid import sheet_from_code
from forest_map_sheet_generator.qgis_adapter.writer import write_sheets
from forest_map_sheet_generator.qgis_adapter.zones import ZoneLayerError, automatic_zones, validate_zone_layer


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
            layer = QgsVectorLayer(f"{path}|layername=grid_z04_50000", "grid", "ogr")
            self.assertTrue(layer.isValid())
            self.assertEqual(layer.crs().authid(), "EPSG:6672")
            self.assertEqual(layer.featureCount(), 1)
            feature = next(layer.getFeatures())
            self.assertEqual(feature["sheet_code"], "04HE")
            self.assertEqual((feature["e_min"], feature["e_max"], feature["n_min"], feature["n_max"]), (0.0, 40000.0, 60000.0, 90000.0))
            with self.assertRaises(FileExistsError): write_sheets(path, 4, "50000", [sheet_from_code("04HE")], "0.1.0-dev")

    def test_zone_validation_and_positive_area_selection(self):
        layer = QgsVectorLayer("Polygon?crs=EPSG:6668", "zones", "memory")
        layer.dataProvider().addAttributes([QgsField("ZONE", QVariant.Int)])
        layer.updateFields()
        feature = QgsFeature(layer.fields()); feature.setAttribute("ZONE", 4)
        feature.setGeometry(QgsGeometry.fromWkt("POLYGON((0 0,10 0,10 10,0 10,0 0))"))
        layer.dataProvider().addFeature(feature)
        zones = validate_zone_layer(layer)
        self.assertEqual(set(automatic_zones(QgsGeometry.fromWkt("POLYGON((5 5,15 5,15 15,5 15,5 5))"), zones)), {4})
        self.assertEqual(automatic_zones(QgsGeometry.fromWkt("POLYGON((10 0,15 0,15 5,10 5,10 0))"), zones), {})
        invalid = QgsVectorLayer("Polygon?crs=EPSG:6668", "bad", "memory")
        invalid.dataProvider().addAttributes([QgsField("ZONE", QVariant.Int)]); invalid.updateFields()
        bad_feature = QgsFeature(invalid.fields()); bad_feature.setAttribute("ZONE", 20); bad_feature.setGeometry(feature.geometry()); invalid.dataProvider().addFeature(bad_feature)
        with self.assertRaises(ZoneLayerError): validate_zone_layer(invalid)
        invalid_epsg = QgsVectorLayer("Polygon?crs=EPSG:6668", "bad-epsg", "memory")
        invalid_epsg.dataProvider().addAttributes([QgsField("ZONE", QVariant.Int), QgsField("EPSG", QVariant.Int)]); invalid_epsg.updateFields()
        epsg_feature = QgsFeature(invalid_epsg.fields()); epsg_feature.setAttributes([4, 6669]); epsg_feature.setGeometry(feature.geometry()); invalid_epsg.dataProvider().addFeature(epsg_feature)
        with self.assertRaises(ZoneLayerError): validate_zone_layer(invalid_epsg)
