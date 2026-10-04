from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsGeometry, QgsProject

from .core.grid import GridType, sheet_from_code
from .dialog import GeneratorDialog
from .qgis_adapter.generator import sheets_for_geometry
from .qgis_adapter.zones import clipped_areas_by_zone, ZoneLayerError
from .qgis_adapter.writer import write_sheets

PLUGIN_VERSION = "0.1.0-dev"


class ForestMapSheetGenerator:
    def __init__(self, iface): self.iface = iface; self.action = None
    def initGui(self):
        self.action = QAction("森林資源メッシュ用国土基本図図郭作成", self.iface.mainWindow()); self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("森林資源メッシュ", self.action); self.iface.addToolBarIcon(self.action)
    def unload(self):
        if self.action: self.iface.removePluginMenu("森林資源メッシュ", self.action); self.iface.removeToolBarIcon(self.action)
    def run(self):
        dialog = GeneratorDialog(self.iface)
        if not dialog.exec(): return
        if not dialog.output.text(): QMessageBox.warning(dialog, "出力先", "GeoPackage保存先を指定してください"); return
        # Direct code is intentionally independent of an area layer and zone polygons.
        if dialog.source.currentIndex() == 3:
            try: sheets = [sheet_from_code(code) for code in dialog.codes.text().split(",") if code.strip()]
            except ValueError as error: QMessageBox.warning(dialog, "図郭コード", str(error)); return
        else:
            canvas = self.iface.mapCanvas(); source_crs = canvas.mapSettings().destinationCrs()
            if dialog.source.currentIndex() == 0:
                geometry = QgsGeometry.fromRect(canvas.extent())
            else:
                layer = QgsProject.instance().mapLayer(dialog.area_layer.currentData())
                if layer is None: QMessageBox.warning(dialog, "対象", "対象ポリゴンレイヤを選択してください"); return
                features = layer.selectedFeatures() if dialog.source.currentIndex() == 2 else list(layer.getFeatures())
                if not features: QMessageBox.warning(dialog, "対象", "対象地物がありません"); return
                geometry = QgsGeometry.unaryUnion([f.geometry() for f in features]); source_crs = layer.crs()
            if dialog.auto_zone.isChecked():
                zone_layer = QgsProject.instance().mapLayer(dialog.zone_layer.currentData())
                try: areas_by_zone = clipped_areas_by_zone(geometry, source_crs, zone_layer); zones = list(areas_by_zone)
                except ZoneLayerError as error: QMessageBox.warning(dialog, "適用区域", str(error)); return
                if not zones: QMessageBox.warning(dialog, "適用区域", "正の面積で重なる系がなく、未被覆です"); return
            else: zones = [int(item.text()) for item in dialog.zones.selectedItems()]; areas_by_zone = {zone: geometry for zone in zones}
            if not zones: QMessageBox.warning(dialog, "系", "手動の系を1つ以上選択してください"); return
            sheets = [sheet for zone in zones for sheet in sheets_for_geometry(areas_by_zone[zone], source_crs, zone, dialog.kind.currentData())]
        try:
            names = write_sheets(dialog.output.text(), sheets, "direct_code" if dialog.source.currentIndex() == 3 else "manual", PLUGIN_VERSION)
            QMessageBox.information(dialog, "完了", f"{len(sheets)}図郭を保存しました: {', '.join(names)}")
        except Exception as error: QMessageBox.critical(dialog, "保存失敗", str(error))
