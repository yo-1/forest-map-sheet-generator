"""GeoPackage output with one layer per zone/type and provenance table."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from qgis.core import QgsFeature, QgsField, QgsFields, QgsVectorFileWriter, QgsVectorLayer, QgsWkbTypes
from qgis.PyQt.QtCore import QVariant

from .generator import rectangle_geometry, zone_crs
from ..core.grid import epsg_for_zone


def write_sheets(path: str, sheets, method: str, plugin_version: str, commit: str = "unknown"):
    if not sheets:
        return []
    if Path(path).exists():
        raise FileExistsError("既存GeoPackageは上書きしません。新しい保存先を指定してください")
    groups = {}
    for sheet in sheets:
        groups.setdefault((sheet.zone, sheet.grid_type.value), []).append(sheet)
    written = []
    for group_index, ((zone, kind), items) in enumerate(groups.items()):
        name = f"grid_z{zone:02d}_{kind}"
        layer = QgsVectorLayer(f"Polygon?crs=EPSG:{epsg_for_zone(zone)}", name, "memory")
        provider = layer.dataProvider()
        provider.addAttributes([QgsField(n, t) for n, t in [
            ("sheet_code", QVariant.String), ("zone", QVariant.Int), ("grid_type", QVariant.String),
            ("parent_code", QVariant.String), ("epsg", QVariant.Int), ("e_min", QVariant.Double),
            ("e_max", QVariant.Double), ("n_min", QVariant.Double), ("n_max", QVariant.Double)]])
        layer.updateFields()
        features = []
        for sheet in items:
            f = QgsFeature(layer.fields()); f.setGeometry(rectangle_geometry(sheet))
            f.setAttributes([sheet.sheet_code, zone, kind, sheet.parent_code, epsg_for_zone(zone), sheet.e_min, sheet.e_max, sheet.n_min, sheet.n_max]); features.append(f)
        provider.addFeatures(features)
        options = QgsVectorFileWriter.SaveVectorOptions(); options.layerName = name
        options.actionOnExistingFile = (QgsVectorFileWriter.CreateOrOverwriteFile if group_index == 0
                                        else QgsVectorFileWriter.CreateOrOverwriteLayer)
        write_result = QgsVectorFileWriter.writeAsVectorFormatV3(layer, path, layer.transformContext(), options)
        result, message = write_result[0], write_result[1]
        if result != QgsVectorFileWriter.NoError:
            raise RuntimeError(message)
        written.append(name)
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS grid_provenance (plugin_version TEXT NOT NULL, "commit" TEXT NOT NULL, generated_at TEXT NOT NULL, method TEXT NOT NULL, zone_layer_version TEXT, layer_name TEXT NOT NULL, source_url TEXT NOT NULL)')
        db.executemany("INSERT INTO grid_provenance VALUES (?, ?, ?, ?, ?, ?, ?)", [(plugin_version, commit, datetime.now(timezone.utc).isoformat(), method, "unknown", name, "https://github.com/yo-1/japan-plane-rectangular-cs-zones") for name in written])
    return written
