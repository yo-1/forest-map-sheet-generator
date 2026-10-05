from qgis.gui import QgsFileWidget, QgsMapLayerComboBox
from qgis.core import QgsMapLayerProxyModel
from qgis.PyQt.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QLabel, QStackedWidget, QWidget


class GeneratorDialog(QDialog):
    """Collect a target, system-selection method, grid type and GeoPackage path."""
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("森林資源メッシュ用国土基本図図郭作成")
        layout = QFormLayout(self)
        self.method = QComboBox()
        for label, value in (("図郭コード直接入力", "code"), ("地図の表示範囲", "extent"), ("ポリゴンレイヤ（選択地物を優先）", "polygon")): self.method.addItem(label, value)
        self.method.currentIndexChanged.connect(self._method_changed); layout.addRow("範囲指定", self.method)
        self.target_stack = QStackedWidget()
        code_page = QWidget(); code_layout = QFormLayout(code_page); self.code = QLineEdit(); self.code.setPlaceholderText("例: 04HE / 04HE00 / 04HE1"); code_layout.addRow("図郭コード", self.code); self.target_stack.addWidget(code_page)
        self.target_stack.addWidget(QWidget())
        polygon_page = QWidget(); polygon_layout = QFormLayout(polygon_page); self.target_layer = QgsMapLayerComboBox(); self.target_layer.setFilters(QgsMapLayerProxyModel.PolygonLayer); polygon_layout.addRow("対象レイヤ", self.target_layer); self.target_stack.addWidget(polygon_page)
        layout.addRow(self.target_stack)
        self.grid_type = QComboBox()
        for label, value in (("1:50,000", "50000"), ("1:5,000", "5000"), ("森林用4分割", "forest_quarter")): self.grid_type.addItem(label, value)
        layout.addRow("図郭種別", self.grid_type)
        self.zone_mode = QComboBox()
        for label, value in (("直接コードから決定", "code"), ("手動（1～19、カンマ区切り）", "manual"), ("適用区域レイヤで自動判定", "automatic")): self.zone_mode.addItem(label, value)
        self.zone_mode.currentIndexChanged.connect(self._zone_changed); layout.addRow("系の選択", self.zone_mode)
        self.zone_stack = QStackedWidget(); self.zone_stack.addWidget(QLabel("直接コードの系を使用します。"))
        manual_page = QWidget(); manual_layout = QFormLayout(manual_page); self.manual_zones = QLineEdit(); self.manual_zones.setPlaceholderText("例: 4 または 4, 5, 6"); manual_layout.addRow("系番号", self.manual_zones); self.zone_stack.addWidget(manual_page)
        automatic_page = QWidget(); automatic_layout = QFormLayout(automatic_page); self.zone_layer = QgsMapLayerComboBox(); self.zone_layer.setFilters(QgsMapLayerProxyModel.PolygonLayer); automatic_layout.addRow("適用区域レイヤ", self.zone_layer); self.zone_stack.addWidget(automatic_page)
        layout.addRow(self.zone_stack)
        self.zone_data_version = QLineEdit(); self.zone_data_version.setPlaceholderText("例: v2026.1（不明なら空欄）"); layout.addRow("適用区域データ版", self.zone_data_version)
        self.output = QgsFileWidget(); self.output.setFilter("GeoPackage (*.gpkg)"); self.output.setStorageMode(QgsFileWidget.SaveFile); layout.addRow("出力GeoPackage", self.output)
        layout.addRow(QLabel("生成中は取消できます。書込開始後は取消できません。既存の同名レイヤは上書きしません。"))
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); layout.addRow(buttons)
    def _method_changed(self, index): self.target_stack.setCurrentIndex(index)
    def _zone_changed(self, index): self.zone_stack.setCurrentIndex(index)
