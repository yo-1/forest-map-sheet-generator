"""Validation and automatic selection from a ZONE polygon layer."""
from __future__ import annotations

from qgis.core import QgsGeometry


class ZoneLayerError(ValueError):
    pass


def validate_zone_layer(layer):
    if layer is None or not layer.crs().isValid():
        raise ZoneLayerError("適用区域レイヤのCRSが未設定です")
    idx = layer.fields().indexOf("ZONE")
    if idx < 0:
        raise ZoneLayerError("適用区域レイヤに整数属性 ZONE がありません")
    zones = set()
    for feature in layer.getFeatures():
        zone = feature["ZONE"]
        geometry = feature.geometry()
        if not isinstance(zone, int) or not 1 <= zone <= 19:
            raise ZoneLayerError("ZONE は整数1～19である必要があります")
        if geometry.isEmpty() or not geometry.isGeosValid():
            raise ZoneLayerError(f"ZONE {zone} に空または無効な形状があります")
        zones.add(zone)
    if not zones:
        raise ZoneLayerError("適用区域レイヤに地物がありません")
    return zones


def auto_zones(area, area_crs, zone_layer):
    """Select zones where A∩Z has positive area; multiple features per zone are supported."""
    from .generator import transformed_geometry
    validate_zone_layer(zone_layer)
    matches = set()
    from qgis.core import QgsCoordinateTransform, QgsProject
    transformed = QgsGeometry(area)
    transformed.transform(QgsCoordinateTransform(area_crs, zone_layer.crs(), QgsProject.instance()))
    for feature in zone_layer.getFeatures():
        zone = feature["ZONE"]
        candidate = QgsGeometry(feature.geometry())
        if candidate.intersection(transformed).area() > 1e-7:
            matches.add(zone)
    return matches


def clipped_areas_by_zone(area, area_crs, zone_layer):
    """Return A∩Z in A's CRS; callers must generate only from these geometries."""
    from qgis.core import QgsCoordinateTransform, QgsProject
    validate_zone_layer(zone_layer)
    transform = QgsCoordinateTransform(zone_layer.crs(), area_crs, QgsProject.instance())
    grouped = {}
    for feature in zone_layer.getFeatures():
        zone = feature["ZONE"]; part = QgsGeometry(feature.geometry()); part.transform(transform)
        overlap = QgsGeometry(area).intersection(part)
        if overlap.area() > 1e-7: grouped.setdefault(zone, []).append(overlap)
    return {zone: QgsGeometry.unaryUnion(parts) for zone, parts in grouped.items()}
