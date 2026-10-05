from __future__ import annotations

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsGeometry, QgsProject, QgsRectangle

from ..core.grid import Sheet, sheets_covering_bbox


class GenerationCancelled(RuntimeError):
    """No output has been written when candidate generation is cancelled."""


def transformed_geometry(geometry, source_crs, destination_crs):
    """Densify the actual polygon before transforming, not only its bbox."""
    dense = QgsGeometry(geometry).densifyByCount(32)
    dense.transform(QgsCoordinateTransform(source_crs, destination_crs, QgsProject.instance().transformContext()))
    return dense


def _transformed_bbox(geometry, source_crs, destination_crs):
    return transformed_geometry(geometry, source_crs, destination_crs).boundingBox()


def _sheet_geometry(sheet: Sheet):
    return QgsGeometry.fromRect(QgsRectangle(sheet.e_min, sheet.n_min, sheet.e_max, sheet.n_max))


def generate_for_geometry(geometry, source_crs, zone, grid_type, cancel=None):
    destination = QgsCoordinateReferenceSystem(f"EPSG:{6668 + zone}")
    transformed = transformed_geometry(geometry, source_crs, destination)
    bbox = transformed.boundingBox()
    candidates = sheets_covering_bbox(zone, bbox.xMinimum(), bbox.yMinimum(), bbox.xMaximum(), bbox.yMaximum(), grid_type)
    result = []
    for sheet in candidates:
        if cancel and cancel():
            raise GenerationCancelled("図郭の生成を取り消しました。出力は開始していません")
        overlap = transformed.intersection(_sheet_geometry(sheet))
        if not overlap.isEmpty() and overlap.area() > 0:
            result.append(sheet)
    return result
