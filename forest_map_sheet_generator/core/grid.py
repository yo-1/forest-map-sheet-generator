"""Projection-coordinate calculations for the three supported sheet grids.

Coordinates are always easting/northing (GIS x/y), not Japanese survey X/Y.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import floor

from .codes import SheetCodeError, parse

# GSJ's alphabet omits I and O.  The first letter increments eastward in 40 km
# bands; the second increments northward in 30 km bands.
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ"
PARENT_WIDTH, PARENT_HEIGHT = 40_000, 30_000
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


def _letter(index: int) -> str:
    if not 0 <= index < len(ALPHABET):
        raise SheetCodeError("投影座標が国土基本図図郭コードの英字範囲外です")
    return ALPHABET[index]


def parent_from_point(zone: int, easting: float, northing: float) -> Sheet:
    if not 1 <= int(zone) <= 19:
        raise SheetCodeError("系番号は1～19です")
    column, row = _index(easting, PARENT_WIDTH), _index(northing, PARENT_HEIGHT)
    code = f"{int(zone):02d}{_letter(column)}{_letter(row)}"
    return Sheet(code, int(zone), "50000", code, column * PARENT_WIDTH,
                 (column + 1) * PARENT_WIDTH, row * PARENT_HEIGHT, (row + 1) * PARENT_HEIGHT)


def sheet_from_code(code: str) -> Sheet:
    item = parse(code)
    column, row = ALPHABET.index(item["col_letter"]), ALPHABET.index(item["row_letter"])
    parent_code = f"{item['zone']:02d}{item['col_letter']}{item['row_letter']}"
    parent = Sheet(parent_code, item["zone"], "50000", parent_code, column * PARENT_WIDTH,
                   (column + 1) * PARENT_WIDTH, row * PARENT_HEIGHT, (row + 1) * PARENT_HEIGHT)
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
    if e_max <= e_min or n_max <= n_min:
        return []
    start = parent_from_point(zone, e_min, n_min)
    # max edge is excluded: a sheet only touching it is not selected.
    end = parent_from_point(zone, e_max - EPSILON, n_max - EPSILON)
    parents = [sheet_from_code(f"{zone:02d}{_letter(c)}{_letter(r)}")
               for c in range(_index(start.e_min, PARENT_WIDTH), _index(end.e_min, PARENT_WIDTH) + 1)
               for r in range(_index(start.n_min, PARENT_HEIGHT), _index(end.n_min, PARENT_HEIGHT) + 1)]
    candidates = parents if grid_type == "50000" else [child for parent in parents for child in children(parent.sheet_code, grid_type)]
    # Bbox-only callers require the same positive-area rule as QGIS callers.
    return [sheet for sheet in candidates if sheet.e_min < e_max - EPSILON and sheet.e_max > e_min + EPSILON
            and sheet.n_min < n_max - EPSILON and sheet.n_max > n_min + EPSILON]
