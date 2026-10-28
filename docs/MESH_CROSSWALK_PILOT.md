# 地域メッシュ対照の小範囲試算

これはファイル配布カタログではなく、正面積交差を持つ地域メッシュの幾何的候補表です。プラグインUIへ機能を追加しません。

```bash
python -m pip install pyproj shapely
python -m unittest discover -s tests -p test_mesh_crosswalk.py -v
python scripts/build_sheet_mesh_crosswalk.py --codes 04HE 04HE1 04HE2 04HE3 04HE4 04HE00 09LD35 --output pilot --step 100
```

既存出力フォルダは拒否します。水平CRSはJGD2011（メッシュEPSG:6668、図郭EPSG:6669～6687）。100mと50mの辺細分化で候補集合の一致を確認し、交差面積の最大変化、未被覆面積、面積総和誤差を報告。50m計算のCSVを保存します。1・2次直接計算と3次からの親コード集約も照合します。

出力はCSV、coverage_qa.json、preview.geojson。GeoJSONはJGD2011をcrsメンバーに明示する旧形式で、RFC7946のWGS84 GeoJSONではありません。QGIS読込み時にEPSG:6668を確認してください。

availabilityは全件unverified。実データの整備・版・計測時期・欠測・配布ファイルの存在を検証していないため、この表だけでダウンロード完了や取得漏れなしと判断しないでください。数値近似の確認であり、公的に認証された対照表ではありません。

全国化、系適用区域、行政界との交差、2500図郭の入力、複数測地系は別工程。地域メッシュ定義の根拠：https://www.stat.go.jp/data/mesh/m_tuite.html
