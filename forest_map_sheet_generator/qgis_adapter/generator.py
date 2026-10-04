"""QGIS geometry selection; imported only inside QGIS."""
from __future__ import annotations

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsGeometry, QgsProject, QgsRectangle

from ..core.grid import GridType, Sheet, epsg_for_zone, sheets_covering_bbox


def zone_crs(zone: int) -> QgsCoordinateReferenceSystem:
    return QgsCoordinateReferenceSystem(f"EPSG:{epsg_for_zone(zone)}")


def rectangle_geometry(sheet: Sheet) -> QgsGeometry:
    return QgsGeometry.fromRect(QgsRectangle(sheet.e_min, sheet.n_min, sheet.e_max, sheet.n_max))


def transformed_geometry(geometry: QgsGeometry, source_crs, zone: int) -> QgsGeometry:
    output = QgsGeometry(geometry)
    transform = QgsCoordinateTransform(source_crs, zone_crs(zone), QgsProject.instance())
    # QgsGeometry transform densifies neither lines nor polygons. Densify before projecting to
    # avoid omitting a curved projected edge whose corners alone miss a candidate grid.
    output = output.densifyByDistance(1_000)
    output.transform(transform)
    return output


def sheets_for_geometry(geometry: QgsGeometry, source_crs, zone: int, grid_type: GridType):
    projected = transformed_geometry(geometry, source_crs, zone)
    box = projected.boundingBox()
    result = []
    for sheet in sheets_covering_bbox(zone, box.xMinimum(), box.yMinimum(), box.xMaximum(), box.yMaximum(), grid_type):
        rect = rectangle_geometry(sheet)
        # A line/point contact has zero area and is intentionally excluded.
        if projected.intersection(rect).area() > 1e-7:
            result.append(sheet)
    return result
