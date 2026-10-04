# 森林資源メッシュ用国土基本図図郭作成プラグイン

初回実装 v0.1.0-dev／2026-10-05。作者：Yoichi Wada。
QGISプラグインの試験実装です。配布候補ZIPは `python scripts/build_plugin_zip.py` で生成します。

森林資源メッシュの作成・管理に使う国土基本図図郭とコードをQGISで生成します。
初版は1:50,000、1:5,000、森林オープンデータ用の1:50,000図郭4分割に対応します。
対象環境：Windows／QGIS 3.44／JGD2011。

- 仕様：docs/SPEC.md
- 実装指示：docs/CODEX_HANDOFF.md
- 検証計画：docs/VALIDATION_PLAN.md
- GitHub作成手順：docs/GITHUB_SETUP.md
- データと出典：DATA_SOURCES.md
- 完了条件・状況：docs/STATUS.md
- Windows／QGIS 3.44 実機確認手順：docs/WINDOWS_QGIS_344_CHECK.md

系の適用区域には https://github.com/yo-1/japan-plane-rectangular-cs-zones の公開GeoPackageを使用します。
DEM解析・20mメッシュ作成・CS立体図計算はこのプラグインの機能に含めません。
