# GitHub新規作成手順

1. GitHubのNew repositoryを開き、Ownerをyo-1にします。
2. Repository name：forest-map-sheet-generator（候補）。
3. Description：森林資源メッシュ用国土基本図図郭作成プラグイン。QGISで国土基本図図郭と森林用4分割図郭を生成します。
4. Publicを推奨。初期LICENSEはライセンス確定まで選択しません。
5. この一式を展開し、README.md、docs/、DATA_SOURCES.md、CHANGELOG.md、.gitignore、.gitattributesを初期ファイルとして配置。
6. Codexへdocs/CODEX_HANDOFF.mdを渡し、新規ブランチ・PRで実装。

この準備ZIPをQGISの「ZIPからインストール」で使わないでください。
Releasesには将来生成するプラグイン配布ZIPを添付し、実機検証記録と対応版を明示します。
リポジトリ名、Public設定、GPL-3.0-only案は提案であり、まだリポジトリを作成していません。
