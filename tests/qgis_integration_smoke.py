"""Executable QGIS integration smoke test (not imported by pure-Python pytest)."""
import os
import sqlite3
import tempfile

from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsGeometry, QgsRectangle

app = QgsApplication([], False); app.initQgis()
try:
    from forest_map_sheet_generator.core.grid import GridType
    from forest_map_sheet_generator.qgis_adapter.generator import sheets_for_geometry
    from forest_map_sheet_generator.qgis_adapter.writer import write_sheets
    source = QgsCoordinateReferenceSystem("EPSG:6672")  # zone 4
    # Positive area inside 04HE produces it; its eastern edge only touches 04IE.
    area = QgsGeometry.fromRect(QgsRectangle(280_100, 120_100, 319_999, 149_999))
    sheets = sheets_for_geometry(area, source, 4, GridType.FIFTY_THOUSAND)
    assert [s.sheet_code for s in sheets] == ["04HE"]
    path = os.path.join(tempfile.mkdtemp(), "smoke.gpkg")
    assert write_sheets(path, sheets, "manual", "test") == ["grid_z04_50000"]
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT sheet_code, epsg FROM grid_z04_50000").fetchone() == ("04HE", 6672)
        assert db.execute("SELECT count(*) FROM grid_provenance").fetchone()[0] == 1
    print("QGIS integration smoke: PASS")
finally:
    app.exitQgis()
