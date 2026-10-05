import os
import sqlite3

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QAction, QApplication, QMessageBox, QProgressDialog
from qgis.core import QgsGeometry

from .core.grid import sheet_from_code
from .dialog import GeneratorDialog
from .qgis_adapter.generator import GenerationCancelled, generate_for_geometry, transformed_geometry
from .qgis_adapter.writer import layer_name, write_sheets
from .qgis_adapter.zones import ZoneLayerError, automatic_zones, coverage_warnings, validate_zone_layer

try:
    from ._build_info import COMMIT
except ImportError:
    COMMIT = "unknown"


class ForestMapSheetGeneratorPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None

    def initGui(self):
        self.action = QAction("森林資源メッシュ用国土基本図図郭作成", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("森林資源メッシュ", self.action)

    def unload(self):
        if self.action:
            self.iface.removePluginMenu("森林資源メッシュ", self.action)
            self.action.deleteLater()
            self.action = None

    @staticmethod
    def _zones(value):
        try:
            result = sorted({int(item.strip()) for item in value.split(",") if item.strip()})
        except ValueError:
            result = []
        if not result or any(not 1 <= zone <= 19 for zone in result):
            raise ValueError("手動の系番号は1～19をカンマ区切りで指定してください")
        return result

    def _target(self, dialog):
        method = dialog.method.currentData()
        if method == "extent":
            canvas = self.iface.mapCanvas()
            return QgsGeometry.fromRect(canvas.extent()), canvas.mapSettings().destinationCrs(), None
        if method == "polygon":
            layer = dialog.target_layer.currentLayer()
            if not layer or not layer.isValid():
                raise ValueError("有効な対象ポリゴンレイヤを選択してください")
            features = layer.selectedFeatures() or list(layer.getFeatures())
            if not features:
                raise ValueError("対象ポリゴンがありません")
            return QgsGeometry.unaryUnion([feature.geometry() for feature in features]), layer.crs(), None
        return None, None, sheet_from_code(dialog.code.text())

    def _generate(self, dialog, cancel=None):
        target, target_crs, direct = self._target(dialog)
        grid_type = dialog.grid_type.currentData()
        if direct:
            if direct.grid_type != grid_type:
                raise ValueError("直接コードと図郭種別が一致しません")
            return {direct.zone: [direct]}, "code", []
        mode = dialog.zone_mode.currentData()
        if mode == "manual":
            groups = {}
            for zone in self._zones(dialog.manual_zones.text()):
                if cancel and cancel():
                    raise GenerationCancelled("図郭の生成を取り消しました。出力は開始していません")
                groups[zone] = generate_for_geometry(target, target_crs, zone, grid_type, cancel=cancel)
            return groups, "manual", []
        if mode != "automatic":
            raise ValueError("範囲指定では手動または自動の系選択を指定してください")
        layer = dialog.zone_layer.currentLayer()
        zones = validate_zone_layer(layer)
        geometry = transformed_geometry(target, target_crs, layer.crs())
        selected = automatic_zones(geometry, zones)
        warnings = coverage_warnings(geometry, zones)
        if not selected:
            raise ValueError("適用区域と正の面積で交差する系がありません。" + "。".join(warnings))
        groups = {}
        for zone, area in selected.items():
            if cancel and cancel():
                raise GenerationCancelled("図郭の生成を取り消しました。出力は開始していません")
            groups[zone] = generate_for_geometry(area, layer.crs(), zone, grid_type, cancel=cancel)
        return groups, "automatic", warnings

    def run(self):
        dialog = GeneratorDialog(self.iface.mainWindow())
        if not dialog.exec_():
            return
        progress = None
        writing = False
        try:
            path = dialog.output.filePath().strip()
            if not path:
                raise ValueError("出力GeoPackageを指定してください")
            progress = QProgressDialog("図郭候補を計算中（取消できます）", "取消", 0, 0, self.iface.mainWindow())
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.show()

            def cancelled():
                QApplication.processEvents()
                return progress.wasCanceled()

            groups, method, warnings = self._generate(dialog, cancel=cancelled)
            if cancelled():
                raise GenerationCancelled("図郭の生成を取り消しました。出力は開始していません")
            groups = {z: list({s.sheet_code: s for s in sheets}.values()) for z, sheets in groups.items() if sheets}
            count = sum(map(len, groups.values()))
            progress.close()
            progress = None
            if not count:
                raise ValueError("正の面積で重なる図郭がありません")
            if os.path.exists(path):
                with sqlite3.connect(path) as connection:
                    present = {row[0] for row in connection.execute("SELECT table_name FROM gpkg_contents")}
                duplicate = present.intersection(layer_name(z, dialog.grid_type.currentData()) for z in groups)
                if duplicate:
                    raise FileExistsError("既存レイヤは上書きしません: " + ", ".join(sorted(duplicate)))
            summary = f"{count}件を生成します。書込開始後は取消できません。続行しますか？"
            if warnings:
                summary += "\n\n注意:\n" + "\n".join(warnings)
            if QMessageBox.question(dialog, "生成件数の確認", summary) != QMessageBox.Yes:
                return
            version = dialog.zone_data_version.text().strip() if method == "automatic" else "unknown"
            writing = True
            names = [write_sheets(path, z, dialog.grid_type.currentData(), sheets, "0.1.0-rc2", commit=COMMIT,
                                  method=method, zone_data_version=version or "unknown") for z, sheets in groups.items()]
            QMessageBox.information(dialog, "完了", f"{count}件を出力しました: {', '.join(names)}")
        except GenerationCancelled as error:
            QMessageBox.information(dialog, "取消", str(error))
        except (ValueError, ZoneLayerError, RuntimeError, FileExistsError, sqlite3.Error) as error:
            suffix = "\n書込途中で失敗したため、出力GeoPackageに一部のレイヤが残っていないか確認してください" if writing else ""
            QMessageBox.warning(dialog, "生成できません", str(error) + suffix)
        finally:
            if progress is not None:
                progress.close()
