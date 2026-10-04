from qgis.PyQt.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
                                 QLineEdit, QListWidget, QPushButton, QRadioButton, QTextEdit)
from .core.grid import GridType


class GeneratorDialog(QDialog):
    def __init__(self, iface):
        super().__init__(iface.mainWindow()); self.iface = iface; self.setWindowTitle("国土基本図図郭を作成")
        form = QFormLayout(self)
        self.source = QComboBox(); self.source.addItems(["地図の表示範囲", "ポリゴンレイヤ全体", "選択地物", "図郭コード直接入力"])
        self.area_layer = QComboBox(); self.zone_layer = QComboBox(); self._populate_layers()
        self.codes = QLineEdit(); self.codes.setPlaceholderText("例: 04HE, 04HE00, 04HE1（カンマ区切り）")
        self.kind = QComboBox(); self.kind.addItem("1:50,000", GridType.FIFTY_THOUSAND); self.kind.addItem("1:5,000", GridType.FIVE_THOUSAND); self.kind.addItem("森林用4分割", GridType.FOREST_QUARTER)
        self.zones = QListWidget(); self.zones.setSelectionMode(QListWidget.MultiSelection); [self.zones.addItem(str(i)) for i in range(1, 20)]
        self.auto_zone = QCheckBox("適用区域レイヤから自動判定")
        self.output = QLineEdit(); browse = QPushButton("参照…"); browse.clicked.connect(self._browse)
        self.preview = QTextEdit(); self.preview.setReadOnly(True)
        form.addRow("範囲", self.source); form.addRow("対象ポリゴンレイヤ", self.area_layer); form.addRow("直接コード", self.codes); form.addRow("図郭種別", self.kind); form.addRow("適用区域レイヤ", self.zone_layer); form.addRow("系選択", self.auto_zone); form.addRow("手動の系（複数可）", self.zones); form.addRow("出力 GeoPackage", self.output); form.addRow("プレビュー", self.preview)
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); form.addRow(buttons)

    def _browse(self):
        path, _ = QFileDialog.getSaveFileName(self, "GeoPackage保存先", filter="GeoPackage (*.gpkg)")
        if path: self.output.setText(path)

    def _populate_layers(self):
        self.area_layer.addItem("（選択）", None); self.zone_layer.addItem("（選択）", None)
        for layer in self.iface.mapCanvas().layers():
            if layer.type() == layer.VectorLayer and layer.geometryType() == 2:
                self.area_layer.addItem(layer.name(), layer.id()); self.zone_layer.addItem(layer.name(), layer.id())
