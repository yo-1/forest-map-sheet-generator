# CHANGELOG

## v0.1.1 — 2026-11-08
- Prepare the portal resubmission after the v0.1.0 detect-secrets scan flagged the embedded commit ID. The package now embeds a 12-character commit prefix; the exact full commit remains the build input and GitHub source reference.
- Keep metadata, build ZIP name, and GeoPackage provenance version aligned at 0.1.1.
- Add CI scanning of the built ZIP contents with detect-secrets to catch packaging regressions.


## v0.1.0 — 2026-11-05
- 初回の正式版。Windows 11 / QGIS 3.44 での実機確認（初回確認・再試験・修正検証）を完了して公開。
- 既存 GeoPackage へ別系レイヤを追加すると `PermissionError [WinError 5]` になる不具合を修正（Issue #3、PR #6）。原因は、出力先の重複チェックで開いた sqlite 接続を閉じないまま `os.replace()` していたこと。

## 未リリース
- tests/test_metadata.py を追加し CI で実行。metadata.txt の必須項目（description など）の欠落、BOM、バージョン表記のずれを検出する（rc4 で直した起動時読み込み不具合の再発防止）。

## v0.1.0-rc4
- metadata.txt に必須項目 description を追加。欠けていたため、QGIS 起動時に「メタデータを読み込み中にエラー」となり、再起動後に自動で読み込まれなかった。

## v0.1.0-rc3
- 設定ダイアログの各入力に objectName を付与（実機検証・UIテスト用。挙動変更なし）。
- 来歴に記録するバージョン表記を 0.1.0-rc3 へ更新。

## 準備資料 v0.1.0 — 2026-10-05

新規開発用の仕様・実装指示・検証計画・GitHub初期文書を作成。プラグインの実装は含みません。

## 2026-10-05 図郭原典照合修正
- 英字を南北A～T／東西A～Hの順にし、I/Oを許容。
- 原点中心の東距±160km／北距±300kmと負座標へ修正。
- 原典からの固定値11件、全国19系と境界試験を追加。
- 正面積抽出でepsilonより細い交差を失わないよう修正。
- 旧a0074378の位置期待値と旧ZIPの検証根拠を訂正。
