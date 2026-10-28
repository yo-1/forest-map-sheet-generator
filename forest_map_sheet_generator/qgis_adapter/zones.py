from __future__ import annotations

from qgis.core import QgsGeometry


class ZoneLayerError(ValueError):
    pass


def validate_zone_layer(layer):
    """Return {zone: merged geometry}; reject unsafe automatic-selection input."""
    if layer is None or not layer.isValid():
        raise ZoneLayerError("適用区域レイヤが無効です")
    if not layer.crs().isValid():
        raise ZoneLayerError("適用区域レイヤのCRSが未設定です")
    if layer.fields().indexFromName("ZONE") < 0:
        raise ZoneLayerError("適用区域レイヤに必須属性 ZONE がありません")
    epsg_index = layer.fields().indexFromName("EPSG")
    grouped = {}
    for feature in layer.getFeatures():
        value = feature["ZONE"]
        try:
            zone = int(value)
        except (TypeError, ValueError):
            raise ZoneLayerError("ZONE は整数1～19でなければなりません")
        if not 1 <= zone <= 19 or str(value).strip() not in {str(zone), f"{zone}.0"}:
            raise ZoneLayerError("ZONE は整数1～19でなければなりません")
        if epsg_index >= 0 and feature["EPSG"] not in (None, ""):
            try:
                epsg = int(feature["EPSG"])
            except (TypeError, ValueError):
                raise ZoneLayerError(f"ZONE={zone} のEPSG属性が整数ではありません")
            if epsg != 6668 + zone:
                raise ZoneLayerError(f"ZONE={zone} のEPSG属性 {epsg} はEPSG:{6668 + zone} と整合しません")
        geometry = feature.geometry()
        if geometry.isNull() or geometry.isEmpty() or not geometry.isGeosValid():
            raise ZoneLayerError(f"ZONE={zone} に空または無効な形状があります")
        grouped.setdefault(zone, []).append(geometry)
    if not grouped:
        raise ZoneLayerError("適用区域レイヤに地物がありません")
    return {zone: QgsGeometry.unaryUnion(geometries) for zone, geometries in grouped.items()}


def automatic_zones(target_geometry, zone_geometries):
    """Positive-area rule: points/edges touching a zone do not select it."""
    selected = {}
    for zone, geometry in zone_geometries.items():
        intersection = target_geometry.intersection(geometry)
        if not intersection.isEmpty() and intersection.area() > 0:
            selected[zone] = intersection
    return selected


def coverage_warnings(target_geometry, zone_geometries):
    """Report incomplete zone data and target area not assigned to any zone."""
    warnings = []
    missing = sorted(set(range(1, 20)) - set(zone_geometries))
    if missing:
        warnings.append("適用区域レイヤに含まれない系: " + ", ".join(map(str, missing)))
    union = QgsGeometry.unaryUnion(list(zone_geometries.values()))
    uncovered = target_geometry.difference(union)
    # A relative tolerance suppresses numerical slivers in the source CRS.
    if not uncovered.isEmpty() and uncovered.area() > max(1e-12, target_geometry.area() * 1e-10):
        warnings.append("対象範囲に適用区域で覆われない部分があります。系を自動割当しません")
    return warnings
