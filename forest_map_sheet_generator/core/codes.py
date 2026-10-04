"""Pure-Python sheet-code validation and conversion."""
from __future__ import annotations

import re
from dataclasses import dataclass

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
PARENT_RE = re.compile(r"^(0[1-9]|1[0-9])([A-Z])([A-Z])$")


class SheetCodeError(ValueError):
    """A sheet code is syntactically valid-looking but not supported."""


@dataclass(frozen=True)
class ParsedCode:
    zone: int
    column: int
    row: int
    child: str | None = None


def normalize(code: str) -> str:
    return "".join(code.strip().upper().split())


def parse(code: str) -> ParsedCode:
    value = normalize(code)
    parent, child = value[:4], value[4:] or None
    match = PARENT_RE.fullmatch(parent)
    if not match:
        raise SheetCodeError("図郭コードは 01AA 形式（系01～19、英字2文字）で指定してください")
    if child is not None and not (len(child) == 2 and child.isdigit() or child in ("1", "2", "3", "4")):
        raise SheetCodeError("子図郭は 1:5,000 の00～99または森林用の1～4です")
    # A=0 is deliberate: it is the GSJ 50k-code offset from the plane-coordinate origin.
    return ParsedCode(int(match.group(1)), LETTERS.index(match.group(2)), LETTERS.index(match.group(3)), child)


def parent_code(zone: int, column: int, row: int) -> str:
    if not 1 <= zone <= 19:
        raise SheetCodeError("系は1～19です")
    if not 0 <= column < len(LETTERS) or not 0 <= row < len(LETTERS):
        raise SheetCodeError("英字で表せる図郭範囲外です")
    return f"{zone:02d}{LETTERS[column]}{LETTERS[row]}"
