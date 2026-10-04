"""Coordinate calculations for Japanese plane-rectangular sheet grids.

All coordinates are easting/northing in the selected JGD2011 plane zone.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import floor

from .codes import ParsedCode, SheetCodeError, parent_code, parse

PARENT_WIDTH, PARENT_HEIGHT = 40_000, 30_000
TOLERANCE = 1e-7


class GridType(str, Enum):
    FIFTY_THOUSAND = "50000"
    FIVE_THOUSAND = "5000"
    FOREST_QUARTER = "forest_quarter"


@dataclass(frozen=True)
class Sheet:
    sheet_code: str
    zone: int
    grid_type: GridType
    parent_code: str
    e_min: float
    e_max: float
    n_min: float
    n_max: float

    @property
    def corners(self):
        return ((self.e_min, self.n_min), (self.e_min, self.n_max),
                (self.e_max, self.n_max), (self.e_max, self.n_min))


def epsg_for_zone(zone: int) -> int:
    if not 1 <= zone <= 19:
        raise ValueError("zone must be 1..19")
    return 6668 + zone


def _parent(parsed: ParsedCode) -> Sheet:
    code = parent_code(parsed.zone, parsed.column, parsed.row)
    e_min, n_min = parsed.column * PARENT_WIDTH, parsed.row * PARENT_HEIGHT
    return Sheet(code, parsed.zone, GridType.FIFTY_THOUSAND, code,
                 e_min, e_min + PARENT_WIDTH, n_min, n_min + PARENT_HEIGHT)


def sheet_from_code(code: str) -> Sheet:
    parsed = parse(code)
    parent = _parent(parsed)
    if parsed.child is None:
        return parent
    if len(parsed.child) == 2:
        row, col = int(parsed.child[0]), int(parsed.child[1])
        # Child row 0 is north; coordinate rows therefore run southward.
        return Sheet(parent.sheet_code + parsed.child, parent.zone, GridType.FIVE_THOUSAND,
                     parent.sheet_code, parent.e_min + col * 4_000, parent.e_min + (col + 1) * 4_000,
                     parent.n_max - (row + 1) * 3_000, parent.n_max - row * 3_000)
    quarter = int(parsed.child)
    col = (quarter - 1) % 2
    north = quarter <= 2
    return Sheet(parent.sheet_code + str(quarter), parent.zone, GridType.FOREST_QUARTER,
                 parent.sheet_code, parent.e_min + col * 20_000, parent.e_min + (col + 1) * 20_000,
                 parent.n_min + (15_000 if north else 0), parent.n_min + (30_000 if north else 15_000))


def code_for_point(zone: int, easting: float, northing: float, grid_type: GridType) -> str:
    """Return the half-open-cell owner: [min,max), with exact outer maxima owned east/north.

    Exact shared east/north boundaries belong to the adjacent sheet; this avoids duplicates.
    """
    col, row = floor((easting + TOLERANCE) / PARENT_WIDTH), floor((northing + TOLERANCE) / PARENT_HEIGHT)
    parent = parent_code(zone, col, row)
    if grid_type is GridType.FIFTY_THOUSAND:
        return parent
    local_e, local_n = easting - col * PARENT_WIDTH, northing - row * PARENT_HEIGHT
    if grid_type is GridType.FIVE_THOUSAND:
        child_col = min(9, max(0, floor((local_e + TOLERANCE) / 4_000)))
        child_row = min(9, max(0, 9 - floor((local_n + TOLERANCE) / 3_000)))
        return f"{parent}{child_row}{child_col}"
    quarter_col = min(1, max(0, floor((local_e + TOLERANCE) / 20_000)))
    quarter_north = local_n + TOLERANCE >= 15_000
    return f"{parent}{(1 if quarter_north else 3) + quarter_col}"


def sheets_covering_bbox(zone: int, e_min: float, n_min: float, e_max: float, n_max: float, grid_type: GridType):
    """Candidate parent sheets intersecting a bbox; callers apply true positive-area geometry tests."""
    if e_max <= e_min or n_max <= n_min:
        return []
    start_col, start_row = floor(e_min / PARENT_WIDTH), floor(n_min / PARENT_HEIGHT)
    end_col, end_row = floor((e_max - TOLERANCE) / PARENT_WIDTH), floor((n_max - TOLERANCE) / PARENT_HEIGHT)
    result = []
    for col in range(start_col, end_col + 1):
        for row in range(start_row, end_row + 1):
            parent = parent_code(zone, col, row)
            if grid_type is GridType.FIFTY_THOUSAND:
                result.append(sheet_from_code(parent))
            elif grid_type is GridType.FIVE_THOUSAND:
                result.extend(sheet_from_code(f"{parent}{r}{c}") for r in range(10) for c in range(10))
            else:
                result.extend(sheet_from_code(f"{parent}{q}") for q in range(1, 5))
    return result
