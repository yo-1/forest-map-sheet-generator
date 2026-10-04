# Windows / QGIS 3.44 実機確認手順

この手順は未実行である。確認者は対象コミットとZIPのSHA256を記録する。

1. 対象コミットを取得して `python scripts/build_plugin_zip.py` を実行する。`dist/forest_map_sheet_generator-0.1.0-rc1.zip` と同名 `.sha256` の値を `CertUtil -hashfile dist\forest_map_sheet_generator-0.1.0-rc1.zip SHA256` で照合する。
2. QGIS 3.44（Windows）で「プラグインを管理とインストール」→「ZIPからインストール」を選び、上記ZIPを指定して有効化する。メニュー「森林資源メッシュ」に項目が一つだけ現れることを確認する。
3. ダイアログで `04HE`、`04HE00`、`04HE1` を順に入力し、各プレビューが 40,000×30,000m、4,000×3,000m、20,000×15,000mとなることを確認する。
4. QGIS Python Consoleから `write_sheets` を使って任意の新規GeoPackageへ出力し、`grid_z04_50000` の CRS=EPSG:6672、属性値、四隅を再読込して確認する。同名レイヤへの再出力が拒否されることを確認する。
5. 適用区域レイヤ（ZONE整数1～19、実CRS設定済み）を使う自動判定では、正面積で交差する系だけを選び、境界の点・辺接触のみは選ばないことを確認する。異なる系で重なる完全長方形は許容する。
6. 結果を `docs/VALIDATION_PLAN.md` のV01～V14に、コミット、ZIP SHA256、QGIS版、成功/失敗/未実行、証拠とともに記録する。
