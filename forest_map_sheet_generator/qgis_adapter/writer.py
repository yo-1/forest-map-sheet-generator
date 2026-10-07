from __future__ import annotations

from datetime import datetime, timezone
from contextlib import closing
import os
import sqlite3
import tempfile

from qgis.core import QgsCoordinateReferenceSystem, QgsFeature, QgsField, QgsFields, QgsProject, QgsVectorFileWriter, QgsWkbTypes
from qgis.PyQt.QtCore import QVariant


def layer_name(zone: int, grid_type: str) -> str:
    return f"grid_z{zone:02d}_{grid_type}"


def write_sheets(path, zone, grid_type, sheets, plugin_version, commit="unknown", method="unknown", zone_data_version="unknown", cancel=None):
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
    try:
        for sheet in sheets:
            if cancel and cancel():
                from .generator import GenerationCancelled
                raise GenerationCancelled("書込みを取り消しました。確定前の出力は破棄します")
            feature = QgsFeature(fields)
            feature.setGeometry(QgsGeometry.fromPolygonXY([[QgsPointXY(e, n) for e, n in (*sheet.corners, sheet.corners[0])]]))
            feature.setAttributes([sheet.sheet_code, sheet.grid_type, sheet.parent_code, zone, epsg, sheet.e_min, sheet.e_max, sheet.n_min, sheet.n_max])
            if not writer.addFeature(feature):
                raise RuntimeError("GeoPackageへの地物書込みに失敗しました")
    finally:
        del writer
    connection = sqlite3.connect(path)
    try:
        connection.execute('CREATE TABLE IF NOT EXISTS forest_map_sheet_provenance (plugin_version TEXT NOT NULL, "commit" TEXT NOT NULL, generated_at TEXT NOT NULL, method TEXT NOT NULL, zone_data_version TEXT NOT NULL, layer_name TEXT NOT NULL, source_url TEXT NOT NULL)')
        connection.execute("INSERT INTO forest_map_sheet_provenance VALUES (?, ?, ?, ?, ?, ?, ?)", (plugin_version, commit, datetime.now(timezone.utc).isoformat(), method, zone_data_version, name, "https://gsj-seamless.jp/labs/tools/zukakuCodeNote.html"))
        connection.commit()
    finally:
        connection.close()
    return name


def write_sheets_batch(path, groups, grid_type, plugin_version, commit="unknown", method="unknown",
                       zone_data_version="unknown", cancel=None):
    """Publish all layers together; cancellation/failure leaves the destination unchanged."""
    parent = os.path.dirname(os.path.abspath(path))
    fd, staging = tempfile.mkstemp(prefix=".forest_grid_", suffix=".gpkg", dir=parent)
    os.close(fd)
    os.unlink(staging)
    try:
        if os.path.exists(path):
            with closing(sqlite3.connect(f"file:{os.path.abspath(path)}?mode=ro", uri=True)) as source:
                with closing(sqlite3.connect(staging)) as destination:
                    source.backup(destination)
        names = []
        for zone, sheets in groups.items():
            if cancel and cancel():
                from .generator import GenerationCancelled
                raise GenerationCancelled("書込みを取り消しました。出力は変更していません")
            names.append(write_sheets(staging, zone, grid_type, sheets, plugin_version,
                                      commit=commit, method=method, zone_data_version=zone_data_version,
                                      cancel=cancel))
        if cancel and cancel():
            from .generator import GenerationCancelled
            raise GenerationCancelled("書込みを取り消しました。出力は変更していません")
        os.replace(staging, path)
        return names
    finally:
        for suffix in ("", "-wal", "-shm", "-journal"):
            try:
                os.unlink(staging + suffix)
            except FileNotFoundError:
                pass
