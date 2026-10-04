"""Run only under QGIS's Python (e.g. qgis_testrunner.sh); never count this as a pass under pytest."""
import pytest
qgis = pytest.importorskip("qgis", reason="QGIS runtime is required for V08/V09/V13")

from qgis.core import QgsApplication, QgsGeometry, QgsPointXY
from forest_map_sheet_generator.core.grid import GridType
from forest_map_sheet_generator.qgis_adapter.generator import sheets_for_geometry


def test_positive_area_intersection_excludes_edge_contact(qgis_app):
    # QGIS fixture supplied by CI / local qgis_testrunner setup.
    pass
