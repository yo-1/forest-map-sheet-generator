from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsGeometry, QgsProject, QgsCoordinateTransform
from .core.grid import sheet_from_code
from .dialog import GeneratorDialog
from .qgis_adapter.generator import generate_for_geometry
from .qgis_adapter.writer import write_sheets
from .qgis_adapter.zones import ZoneLayerError, automatic_zones, validate_zone_layer


class ForestMapSheetGeneratorPlugin:
    def __init__(self, iface): self.iface = iface; self.action = None
    def initGui(self):
        self.action = QAction("森林資源メッシュ用国土基本図図郭作成", self.iface.mainWindow()); self.action.triggered.connect(self.run); self.iface.addPluginToMenu("森林資源メッシュ", self.action)
    def unload(self):
        if self.action: self.iface.removePluginMenu("森林資源メッシュ", self.action)
    @staticmethod
    def _zones(value):
        try: result = sorted({int(item.strip()) for item in value.split(",") if item.strip()})
        except ValueError: result = []
        if not result or any(not 1 <= zone <= 19 for zone in result): raise ValueError("手動の系番号は1～19をカンマ区切りで指定してください")
        return result
    def _target(self, dialog):
        method = dialog.method.currentData()
        if method == "extent":
            canvas = self.iface.mapCanvas(); return QgsGeometry.fromRect(canvas.extent()), canvas.mapSettings().destinationCrs(), None
        if method == "polygon":
            layer = dialog.target_layer.currentLayer()
            if not layer or not layer.isValid(): raise ValueError("有効な対象ポリゴンレイヤを選択してください")
            features = layer.selectedFeatures() or list(layer.getFeatures())
            if not features: raise ValueError("対象ポリゴンがありません")
            return QgsGeometry.unaryUnion([feature.geometry() for feature in features]), layer.crs(), None
        return None, None, sheet_from_code(dialog.code.text())
    def _generate(self, dialog):
        target, target_crs, direct = self._target(dialog); grid_type = dialog.grid_type.currentData()
        if direct:
            if direct.grid_type != grid_type: raise ValueError("直接コードと図郭種別が一致しません")
            return {direct.zone: [direct]}, "code"
        mode = dialog.zone_mode.currentData()
        if mode == "manual": return {z: generate_for_geometry(target, target_crs, z, grid_type) for z in self._zones(dialog.manual_zones.text())}, "manual"
        if mode != "automatic": raise ValueError("範囲指定では手動または自動の系選択を指定してください")
        layer = dialog.zone_layer.currentLayer(); zones = validate_zone_layer(layer)
        geometry = QgsGeometry(target); geometry.transform(QgsCoordinateTransform(target_crs, layer.crs(), QgsProject.instance().transformContext()))
        selected = automatic_zones(geometry, zones)
        if not selected: raise ValueError("適用区域と正の面積で交差する系がありません")
        return {z: generate_for_geometry(area, layer.crs(), z, grid_type) for z, area in selected.items()}, "automatic"
    def run(self):
        dialog = GeneratorDialog(self.iface.mainWindow())
        if not dialog.exec_(): return
        try:
            if not dialog.output.filePath().strip(): raise ValueError("出力GeoPackageを指定してください")
            groups, method = self._generate(dialog); groups = {z: list({s.sheet_code: s for s in sheets}.values()) for z, sheets in groups.items() if sheets}; count = sum(map(len, groups.values()))
            if not count: raise ValueError("正の面積で重なる図郭がありません")
            if QMessageBox.question(dialog, "生成件数の確認", f"{count}件を生成します。続行しますか？") != QMessageBox.Yes: return
            names = [write_sheets(dialog.output.filePath(), z, dialog.grid_type.currentData(), sheets, "0.1.0-dev", method=method) for z, sheets in groups.items()]
            QMessageBox.information(dialog, "完了", f"{count}件を出力しました: {', '.join(names)}")
        except (ValueError, ZoneLayerError, RuntimeError, FileExistsError) as error: QMessageBox.warning(dialog, "生成できません", str(error))
