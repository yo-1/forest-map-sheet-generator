from __future__ import annotations

from datetime import datetime, timezone
import os
import sqlite3

from qgis.core import QgsCoordinateReferenceSystem, QgsFeature, QgsField, QgsFields, QgsProject, QgsVectorFileWriter, QgsWkbTypes
from qgis.PyQt.QtCore import QVariant


def layer_name(zone: int, grid_type: str) -> str:
    return f"grid_z{zone:02d}_{grid_type}"


def write_sheets(path, zone, grid_type, sheets, plugin_version, commit="unknown", method="unknown", zone_data_version="unknown"):
    """Write one non-overwriting GeoPackage layer and a non-spatial provenance table."""
    name = layer_name(zone, grid_type)
    exists = os.path.exists(path)
    if exists:
        existing = sqlite3.connect(path)
        try:
            if existing.execute("SELECT 1 FROM gpkg_contents WHERE table_name = ?", (name,)).fetchone():
                raise FileExistsError(f"既存レイヤ {name} は上書きしません。別の出力先またはレイヤ名を指定してください")
        finally:
            existing.close()
    fields = QgsFields()
    for field in ("sheet_code", "grid_type", "parent_code"):
        fields.append(QgsField(field, QVariant.String))
    fields.append(QgsField("zone", QVariant.Int))
    fields.append(QgsField("epsg", QVariant.Int))
    for field in ("e_min", "e_max", "n_min", "n_max"):
        fields.append(QgsField(field, QVariant.Double))
    epsg = 6668 + zone
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = name
    options.actionOnExistingFile = (QgsVectorFileWriter.CreateOrOverwriteLayer if exists
                                    else QgsVectorFileWriter.CreateOrOverwriteFile)
    writer = QgsVectorFileWriter.create(path, fields, QgsWkbTypes.Polygon, QgsCoordinateReferenceSystem(f"EPSG:{epsg}"), QgsProject.instance().transformContext(), options)
    if writer.hasError():
        raise RuntimeError(writer.errorMessage())
    from qgis.core import QgsGeometry, QgsPointXY
    for sheet in sheets:
        feature = QgsFeature(fields)
        feature.setGeometry(QgsGeometry.fromPolygonXY([[QgsPointXY(e, n) for e, n in (*sheet.corners, sheet.corners[0])]]))
        feature.setAttributes([sheet.sheet_code, sheet.grid_type, sheet.parent_code, zone, epsg, sheet.e_min, sheet.e_max, sheet.n_min, sheet.n_max])
        if not writer.addFeature(feature):
            raise RuntimeError("GeoPackageへの地物書込みに失敗しました")
    del writer
    connection = sqlite3.connect(path)
    try:
        connection.execute('CREATE TABLE IF NOT EXISTS forest_map_sheet_provenance (plugin_version TEXT NOT NULL, "commit" TEXT NOT NULL, generated_at TEXT NOT NULL, method TEXT NOT NULL, zone_data_version TEXT NOT NULL, layer_name TEXT NOT NULL, source_url TEXT NOT NULL)')
        connection.execute("INSERT INTO forest_map_sheet_provenance VALUES (?, ?, ?, ?, ?, ?, ?)", (plugin_version, commit, datetime.now(timezone.utc).isoformat(), method, zone_data_version, name, "https://gsj-seamless.jp/labs/tools/zukakuCodeNote.html"))
        connection.commit()
    finally:
        connection.close()
    return name
