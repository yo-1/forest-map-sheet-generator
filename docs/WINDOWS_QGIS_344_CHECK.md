# Windows / QGIS 3.44 実機確認手順

1. 対象コミットで `python scripts/build_plugin_zip.py` を実行し、`dist/forest_map_sheet_generator-0.1.0-rc1.zip` と `.sha256` を作る。PowerShellで `Get-FileHash .\dist\forest_map_sheet_generator-0.1.0-rc1.zip -Algorithm SHA256` を実行し、記録値と一致することを確認する。
2. QGIS 3.44 の「プラグインの管理とインストール」から「ZIPからインストール」を選び、ZIPを指定する。ライセンス表示は確定前のため確認対象外。
3. 基準適用区域GeoPackageを読み込み、`ZONE`が整数1～19、レイヤCRSが設定されていることを確認する。表示範囲・ポリゴン全体・選択地物・直接コードでそれぞれ生成を確認する。
4. 手動で第4系を選び `04HE`、`04HE00`、`04HE1` を生成する。属性と四隅を `docs/GRID_EXPECTATIONS.md` と照合する。
5. 自動判定では区域境界をまたぐポリゴンを使い、正の面積で重なる各系だけに別レイヤができ、図郭が完全長方形でクリップされないことを確認する。境界だけに接する図郭は出ないことを確認する。
6. GeoPackageをQGISへ再読込し、先頭ゼロを含む `sheet_code`、CRS、属性、`grid_provenance` の非空間テーブルを確認する。既存GeoPackageを指定した場合に上書きせずエラーになることも確認する。

このリポジトリの作業環境は QGIS 3.40.6。Windows/QGIS 3.44 実機検証は未実施であり、結果を正式版合格として扱わない。
