"""Projection-coordinate calculations for the three supported sheet grids.

Coordinates are always easting/northing (GIS x/y), not Japanese survey X/Y.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import floor, isfinite

from .codes import SheetCodeError, parse

# Forest open-data standard Ver2.1, printed p63, reference 3 figure 1.
# First letter: north-to-south A..T (including I/O); second: west-to-east A..H.
ROW_LETTERS = "ABCDEFGHIJKLMNOPQRST"
COL_LETTERS = "ABCDEFGH"
PARENT_WIDTH, PARENT_HEIGHT = 40_000, 30_000
E_MIN, E_MAX, N_MIN, N_MAX = -160_000, 160_000, -300_000, 300_000
EPSILON = 1e-7  # metres; only removes numerical noise at an exact boundary


@dataclass(frozen=True)
class Sheet:
    sheet_code: str
    zone: int
    grid_type: str
    parent_code: str
    e_min: float
    e_max: float
    n_min: float
    n_max: float

    @property
    def width(self) -> float:
        return self.e_max - self.e_min

    @property
    def height(self) -> float:
        return self.n_max - self.n_min

    @property
    def corners(self) -> tuple[tuple[float, float], ...]:
        return ((self.e_min, self.n_min), (self.e_max, self.n_min),
                (self.e_max, self.n_max), (self.e_min, self.n_max))


def _index(value: float, size: float) -> int:
    """Lower-inclusive, upper-exclusive band index with a tiny noise tolerance."""
    nearest = round(value / size)
    if abs(value - nearest * size) <= EPSILON:
        value = nearest * size
    return floor(value / size)


def parent_from_point(zone: int, easting: float, northing: float) -> Sheet:
    if not 1 <= int(zone) <= 19:
        raise SheetCodeError("系番号は1～19です")
    if not isfinite(easting) or not isfinite(northing):
        raise SheetCodeError("座標は有限値で指定してください")
    column = _index(easting - E_MIN, PARENT_WIDTH)
    row = len(ROW_LETTERS) - 1 - _index(northing - N_MIN, PARENT_HEIGHT)
    if not 0 <= column < len(COL_LETTERS) or not 0 <= row < len(ROW_LETTERS):
        raise SheetCodeError("座標は原典図郭範囲（東距±160km、北距±300km）の外です")
    return sheet_from_code(f"{int(zone):02d}{ROW_LETTERS[row]}{COL_LETTERS[column]}")


def sheet_from_code(code: str) -> Sheet:
    item = parse(code)
    column, row = COL_LETTERS.index(item["col_letter"]), ROW_LETTERS.index(item["row_letter"])
    parent_code = f"{item['zone']:02d}{item['row_letter']}{item['col_letter']}"
    e_min = E_MIN + column * PARENT_WIDTH
    n_max = N_MAX - row * PARENT_HEIGHT
    parent = Sheet(parent_code, item["zone"], "50000", parent_code, e_min,
                   e_min + PARENT_WIDTH, n_max - PARENT_HEIGHT, n_max)
    if item["grid_type"] == "50000":
        return parent
    if item["grid_type"] == "5000":
        row5, col5 = item["row"], item["column"]
        # Code row 0 is the northernmost row, hence northing is reversed.
        n_max = parent.n_max - row5 * 3_000
        return Sheet(item["code"], item["zone"], "5000", parent_code,
                     parent.e_min + col5 * 4_000, parent.e_min + (col5 + 1) * 4_000,
                     n_max - 3_000, n_max)
    quarter = item["quarter"]
    offsets = {1: (0, 15_000), 2: (20_000, 15_000), 3: (0, 0), 4: (20_000, 0)}
    east, north = offsets[quarter]
    return Sheet(item["code"], item["zone"], "forest_quarter", parent_code,
                 parent.e_min + east, parent.e_min + east + 20_000,
                 parent.n_min + north, parent.n_min + north + 15_000)


def children(parent_code: str, grid_type: str) -> list[Sheet]:
    parent = sheet_from_code(parent_code)
    if parent.grid_type != "50000":
        raise SheetCodeError("子図郭の親は1:50,000図郭で指定してください")
    if grid_type == "5000":
        return [sheet_from_code(f"{parent.sheet_code}{row}{col}") for row in range(10) for col in range(10)]
    if grid_type == "forest_quarter":
        return [sheet_from_code(f"{parent.sheet_code}{number}") for number in range(1, 5)]
    raise SheetCodeError("子図郭種別は5000またはforest_quarterです")


def sheets_covering_bbox(zone: int, e_min: float, n_min: float, e_max: float, n_max: float, grid_type: str) -> list[Sheet]:
    """Return sheets having positive-area overlap with the half-open bbox."""
    if grid_type not in ("50000", "5000", "forest_quarter"):
        raise SheetCodeError("図郭種別は50000、5000、forest_quarterです")
    if not 1 <= int(zone) <= 19:
        raise SheetCodeError("系番号は1～19です")
    if not all(isfinite(v) for v in (e_min, n_min, e_max, n_max)):
        raise SheetCodeError("範囲の座標は有限値で指定してください")
    if e_max <= e_min or n_max <= n_min:
        return []
    if e_min < E_MIN or e_max > E_MAX or n_min < N_MIN or n_max > N_MAX:
        raise SheetCodeError("指定範囲が原典図郭範囲の外へ延びています。範囲を確認してください")
    # Scan the finite 160 parents, without subtracting epsilon from max edges.
    # Thus even a positive overlap narrower than EPSILON is retained.
    parents = []
    for r in ROW_LETTERS:
        for c in COL_LETTERS:
            parent = sheet_from_code(f"{int(zone):02d}{r}{c}")
            if parent.e_min < e_max and parent.e_max > e_min and parent.n_min < n_max and parent.n_max > n_min:
                parents.append(parent)
    candidates = parents if grid_type == "50000" else [child for parent in parents for child in children(parent.sheet_code, grid_type)]
    # Bbox-only callers require the same positive-area rule as QGIS callers.
    return [sheet for sheet in candidates if sheet.e_min < e_max and sheet.e_max > e_min
            and sheet.n_min < n_max and sheet.n_max > n_min]
