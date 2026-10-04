from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QComboBox, QLabel


class GeneratorDialog(QDialog):
    """Small initial UI; advanced selection remains available through QGIS layers."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("森林資源メッシュ用国土基本図図郭作成")
        layout = QFormLayout(self)
        self.code = QLineEdit()
        self.code.setPlaceholderText("例: 04HE / 04HE00 / 04HE1（直接入力）")
        self.grid_type = QComboBox()
        self.grid_type.addItem("1:50,000", "50000")
        self.grid_type.addItem("1:5,000", "5000")
        self.grid_type.addItem("森林用4分割", "forest_quarter")
        self.zone = QComboBox()
        self.zone.addItem("コードから自動", None)
        for item in range(1, 20): self.zone.addItem(f"第{item}系", item)
        layout.addRow("図郭コード", self.code)
        layout.addRow("図郭種別", self.grid_type)
        layout.addRow("系", self.zone)
        self.preview = QLabel("直接コード入力で1件をプレビューします。")
        layout.addRow(self.preview)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
