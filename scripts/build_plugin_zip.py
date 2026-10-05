#!/usr/bin/env python3
"""Create an installable QGIS plugin ZIP without build artefacts."""
from __future__ import annotations
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "forest_map_sheet_generator-0.1.0-rc2.zip"
PLUGIN_DIR = "forest_map_sheet_generator"
ROOT_FILES = ("metadata.txt", "LICENSE", "README.md", "DATA_SOURCES.md")

OUT.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as archive:
    source_dir = ROOT / PLUGIN_DIR
    for file in sorted(source_dir.rglob("*")):
        if file.is_file() and "__pycache__" not in file.parts:
            info = zipfile.ZipInfo(str(file.relative_to(ROOT)), date_time=(2026, 10, 5, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, file.read_bytes())
    for entry in ROOT_FILES:
        info = zipfile.ZipInfo(f"{PLUGIN_DIR}/{entry}", date_time=(2026, 10, 5, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, (ROOT / entry).read_bytes())
digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
(OUT.with_suffix(OUT.suffix + ".sha256")).write_text(f"{digest}  {OUT.name}\n", encoding="utf-8")
print(OUT)
print(digest)
