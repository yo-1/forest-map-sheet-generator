#!/usr/bin/env python3
"""Create a reproducible, installable QGIS plugin ZIP without build artefacts."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "forest_map_sheet_generator-0.1.0-rc2.zip"
PLUGIN_DIR = "forest_map_sheet_generator"
ROOT_FILES = ("metadata.txt", "LICENSE", "README.md", "DATA_SOURCES.md")

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--commit", help="exact source commit (required without git checkout)")
args = parser.parse_args()
if args.commit:
    commit = args.commit
else:
    run = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    commit = run.stdout.strip() if run.returncode == 0 else "unknown"
if commit != "unknown" and (len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit.lower())):
    parser.error("--commit must be a full 40-character git SHA or unknown")

OUT.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as archive:
    def add_bytes(path, data):
        info = zipfile.ZipInfo(path, date_time=(2026, 10, 5, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, data)

    for file in sorted((ROOT / PLUGIN_DIR).rglob("*")):
        if file.is_file() and "__pycache__" not in file.parts and file.name != "_build_info.py":
            add_bytes(str(file.relative_to(ROOT)), file.read_bytes())
    for entry in ROOT_FILES:
        add_bytes(f"{PLUGIN_DIR}/{entry}", (ROOT / entry).read_bytes())
    add_bytes(f"{PLUGIN_DIR}/_build_info.py", f"COMMIT = {commit!r}\n".encode("utf-8"))
digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
(OUT.with_suffix(OUT.suffix + ".sha256")).write_text(f"{digest}  {OUT.name}\n", encoding="utf-8")
print(OUT)
print(digest)
