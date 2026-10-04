from qgis.PyQt.QtWidgets import QAction, QMessageBox

from .core.grid import sheet_from_code
from .dialog import GeneratorDialog


class ForestMapSheetGeneratorPlugin:
    def __init__(self, iface): self.iface = iface; self.action = None
    def initGui(self):
        self.action = QAction("森林資源メッシュ用国土基本図図郭作成", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("森林資源メッシュ", self.action)
    def unload(self):
        if self.action: self.iface.removePluginMenu("森林資源メッシュ", self.action)
    def run(self):
        dialog = GeneratorDialog(self.iface.mainWindow())
        if dialog.exec_() and dialog.code.text().strip():
            try:
                sheet = sheet_from_code(dialog.code.text())
                QMessageBox.information(dialog, "プレビュー", f"{sheet.sheet_code}: {sheet.width:g}m × {sheet.height:g}m")
            except ValueError as error:
                QMessageBox.warning(dialog, "入力エラー", str(error))
