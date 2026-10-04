from __future__ import annotations

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsGeometry, QgsProject, QgsRectangle

from ..core.grid import Sheet, sheets_covering_bbox


def _transformed_bbox(geometry, source_crs, destination_crs):
    transform = QgsCoordinateTransform(source_crs, destination_crs, QgsProject.instance())
    # Densification protects against transformed curved extent edges.
    dense = geometry.densifyByCount(32)
    return transform.transformBoundingBox(dense.boundingBox())


def _sheet_geometry(sheet: Sheet):
    return QgsGeometry.fromRect(QgsRectangle(sheet.e_min, sheet.n_min, sheet.e_max, sheet.n_max))


def generate_for_geometry(geometry, source_crs, zone, grid_type, cancel=None):
    destination = QgsCoordinateReferenceSystem(f"EPSG:{6668 + zone}")
    bbox = _transformed_bbox(geometry, source_crs, destination)
    candidates = sheets_covering_bbox(zone, bbox.xMinimum(), bbox.yMinimum(), bbox.xMaximum(), bbox.yMaximum(), grid_type)
    transformer = QgsCoordinateTransform(source_crs, destination, QgsProject.instance())
    transformed = QgsGeometry(geometry)
    transformed.transform(transformer)
    result = []
    for sheet in candidates:
        if cancel and cancel():
            break
        overlap = transformed.intersection(_sheet_geometry(sheet))
        if not overlap.isEmpty() and overlap.area() > 0:
            result.append(sheet)
    return result
