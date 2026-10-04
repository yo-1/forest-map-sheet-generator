"""Validation and normalisation of national-base-map sheet codes."""
from __future__ import annotations

import re

_PARENT = re.compile(r"^(0[1-9]|1[0-9])([A-HJ-NP-Z]{2})$")
_CHILD = re.compile(r"^(0[1-9]|1[0-9])([A-HJ-NP-Z]{2})([0-9])([0-9])$")
_QUARTER = re.compile(r"^(0[1-9]|1[0-9])([A-HJ-NP-Z]{2})([1-4])$")


class SheetCodeError(ValueError):
    """A code is malformed or does not identify the requested grid type."""


def normalize(code: str) -> str:
    if not isinstance(code, str):
        raise SheetCodeError("図郭コードは文字列で指定してください")
    value = code.strip().upper()
    if not value:
        raise SheetCodeError("図郭コードが空です")
    return value


def parse(code: str, grid_type: str | None = None) -> dict[str, int | str]:
    value = normalize(code)
    match = _PARENT.fullmatch(value)
    kind = "50000"
    if not match:
        match = _CHILD.fullmatch(value)
        kind = "5000"
    if not match:
        match = _QUARTER.fullmatch(value)
        kind = "forest_quarter"
    if not match:
        raise SheetCodeError(
            "図郭コードの形式が不正です（例: 04HE, 04HE00, 04HE1）。"
            "系は01～19、英字はI/Oを除きます"
        )
    if grid_type and kind != grid_type:
        raise SheetCodeError(f"{value} は {grid_type} の図郭コードではありません")
    groups = match.groups()
    result: dict[str, int | str] = {"code": value, "grid_type": kind, "zone": int(groups[0]), "col_letter": groups[1][0], "row_letter": groups[1][1]}
    if kind == "5000":
        result.update(row=int(groups[2]), column=int(groups[3]))
    elif kind == "forest_quarter":
        result["quarter"] = int(groups[2])
    return result
