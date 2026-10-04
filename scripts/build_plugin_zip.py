#!/usr/bin/env python3
"""Create an installable QGIS plugin ZIP without build artefacts."""
from __future__ import annotations
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "forest_map_sheet_generator-0.1.0-rc1.zip"
INCLUDE = ("forest_map_sheet_generator", "metadata.txt")

OUT.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as archive:
    for entry in INCLUDE:
        source = ROOT / entry
        if source.is_file(): archive.write(source, entry)
        else:
            for file in source.rglob("*"):
                if file.is_file() and "__pycache__" not in file.parts:
                    archive.write(file, file.relative_to(ROOT))
digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
(OUT.with_suffix(OUT.suffix + ".sha256")).write_text(f"{digest}  {OUT.name}\n", encoding="utf-8")
print(OUT)
print(digest)
