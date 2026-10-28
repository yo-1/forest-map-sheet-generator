"""metadata.txt の必須項目とバージョン表記の整合を確認する（QGIS 不要）。

背景: description の欠落により、QGIS 起動時に「メタデータを読み込み中にエラー」となり、
再起動後にプラグインが自動で読み込まれなかった（0.1.0-rc3 まで。rc4 で修正）。
手動の読み込みでは動くため、実機の再起動まで気づけなかった。
"""
import configparser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
# QGIS のプラグイン仕様で必須の項目（email は空でも可とするが、キー自体は必要）
REQUIRED_KEYS = ("name", "qgisMinimumVersion", "description", "about", "version", "author", "email", "repository")
NON_EMPTY_KEYS = ("name", "qgisMinimumVersion", "description", "about", "version", "author", "repository")


def _metadata():
    parser = configparser.ConfigParser()
    with (ROOT / "metadata.txt").open(encoding="utf-8") as file:  # BOM 付きなら ここで先頭が崩れる
        parser.read_file(file)
    return parser["general"]


class MetadataTests(unittest.TestCase):
    def test_required_keys_present_and_non_empty(self):
        general = _metadata()
        for key in REQUIRED_KEYS:
            with self.subTest(key=key):
                self.assertIn(key, general)
        for key in NON_EMPTY_KEYS:
            with self.subTest(non_empty=key):
                self.assertTrue(general.get(key, "").strip())

    def test_no_bom(self):
        self.assertNotEqual((ROOT / "metadata.txt").read_bytes()[:3], b"\xef\xbb\xbf")

    def test_version_is_consistent_across_files(self):
        version = _metadata()["version"]
        build_script = (ROOT / "scripts" / "build_plugin_zip.py").read_text(encoding="utf-8")
        plugin = (ROOT / "forest_map_sheet_generator" / "plugin.py").read_text(encoding="utf-8")
        self.assertIn(f"forest_map_sheet_generator-{version}.zip", build_script)
        self.assertIn(f'"{version}"', plugin)
        self.assertRegex(version, re.compile(r"^\d+\.\d+\.\d+(-rc\d+)?$"))


if __name__ == "__main__":
    unittest.main()
