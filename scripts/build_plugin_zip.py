#!/usr/bin/env python3
"""Build a deterministic installable plugin archive from the repository root."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import hashlib

ROOT = Path(__file__).resolve().parents[1]; PACKAGE = ROOT / "forest_map_sheet_generator"
OUT = ROOT / "dist" / "forest_map_sheet_generator-0.1.0-rc1.zip"
OUT.parent.mkdir(exist_ok=True)
with ZipFile(OUT, "w", ZIP_DEFLATED) as archive:
    for file in sorted(PACKAGE.rglob("*")):
        if file.is_file() and "__pycache__" not in file.parts:
            item = ZipInfo(str(Path(PACKAGE.name) / file.relative_to(PACKAGE)).replace("\\\\", "/")); item.date_time = (2026, 1, 1, 0, 0, 0)
            archive.writestr(item, file.read_bytes(), compress_type=ZIP_DEFLATED)
digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
(OUT.with_suffix(".zip.sha256")).write_text(f"{digest}  {OUT.name}\\n", encoding="utf-8")
print(OUT); print(digest)
