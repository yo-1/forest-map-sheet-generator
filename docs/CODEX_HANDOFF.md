# Codexへの実装指示 v0.1.0

この新規開発一式を基準に実装してください。別途渡される引継ぎ書にはDrive IDが含まれることがあります。その引継ぎ書自体、Drive ID、個人連絡先をコミット・PR・Issueへ掲載しないでください。

## 対象と変更範囲

対象リポジトリ：yo-1/forest-map-sheet-generator（作成済み）。
既存のcsmap-sheets、fme-csmap-pipeline、forest-mesh20m、japan-plane-rectangular-cs-zonesは変更しません。
基礎ポリゴンの系区分ルールや告示照合は再実施せず、公開資料を参照します。
SPEC.mdとVALIDATION_PLAN.mdに従うQGISプラグインを実装します。

## 初回実装のファイル構成

forest_map_sheet_generator/__init__.py：QGIS classFactory。
plugin.py：起動・終了、メニュー管理。
dialog.py：範囲・種別・系・出力指定。
core/grid.py：QGISに依存しない寸法・コード・座標計算。
core/codes.py：入力検証、正規化、コード往復。
qgis_adapter/zones.py：区域レイヤ検証、系判定。
qgis_adapter/generator.py：座標変換、交差判定、取消。
qgis_adapter/writer.py：GeoPackage、来歴保存。
metadata.txt、アイコン、LICENSE、操作説明。
tests/fixtures/expected_grids.csv：根拠付き独立期待値。
tests/：純Pythonの計算試験、QGIS環境での結合試験。
scripts/build_plugin_zip.py、.github/workflows/tests.yml。

## 作業順

1. 仕様と根拠を読み、英字割当・四隅座標・境界帰属の期待値を作る。
2. 純Pythonの図郭計算と試験を実装。
3. QGIS UI、区域判定、GeoPackage出力を実装。
4. 実際に実行できるCIを追加。QGIS未導入の試験を成功扱いしない。
5. 配布ZIPを生成し、Windows/QGIS実機手順を提出。

新規ブランチで作業し、PRとして提出。mainへの直接push、無指示のマージ・Release公開は行わないでください。
ライセンス案はGPL-3.0-only。ユーザーによる確定を得てからLICENSEと配布metadataに設定してください。
プラグイン版は初回実装v0.1.0-dev、試験配布はv0.1.0-rc1を提案します。準備資料の版と混同しないこと。

## 完了報告

変更ファイル、対象コミット、実行環境、成功・失敗・未実行件数、既知制約、ZIPとSHA256、実機手順を提出。
計算の合格とQGIS/Windows実機の合格を区別します。実機未確認で正式版完成とは記載しません。
