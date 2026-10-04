import csv
from pathlib import Path
import pytest

from forest_map_sheet_generator.core.codes import SheetCodeError, parse
from forest_map_sheet_generator.core.grid import GridType, code_for_point, epsg_for_zone, sheet_from_code, sheets_covering_bbox


@pytest.mark.parametrize("row", list(csv.DictReader((Path(__file__).parent / "fixtures/expected_grids.csv").open())), ids=lambda r: r["sheet_code"])
def test_independent_fixed_expectations(row):
    sheet = sheet_from_code(row["sheet_code"])
    assert (sheet.zone, sheet.grid_type.value) == (int(row["zone"]), row["grid_type"])
    assert (sheet.e_min, sheet.e_max, sheet.n_min, sheet.n_max) == tuple(float(row[k]) for k in ("e_min", "e_max", "n_min", "n_max"))


def test_5000_has_100_tiles_and_exact_parent_area():
    children = [sheet_from_code(f"04HE{r}{c}") for r in range(10) for c in range(10)]
    assert sum((x.e_max-x.e_min)*(x.n_max-x.n_min) for x in children) == 40_000 * 30_000
    assert len({x.sheet_code for x in children}) == 100


def test_forest_quarters_have_required_positions_and_area():
    sheets = [sheet_from_code(f"04HE{i}") for i in range(1, 5)]
    assert sheets[0].n_min == sheets[1].n_min == 135_000
    assert sheets[2].n_max == sheets[3].n_max == 135_000
    assert sum((x.e_max-x.e_min)*(x.n_max-x.n_min) for x in sheets) == 40_000 * 30_000


def test_boundary_owner_is_east_and_north_neighbor():
    assert code_for_point(4, 320_000, 150_000, GridType.FIFTY_THOUSAND) == "04IF"
    assert code_for_point(4, 280_000, 120_000, GridType.FIVE_THOUSAND) == "04HE90"


def test_negative_coordinates_floor_not_truncate():
    # floor(-1/40000) is -1 (not 0); it is outside the alphabetic code domain,
    # and must fail instead of silently becoming 04AA.
    with pytest.raises(SheetCodeError):
        code_for_point(4, -1, -1, GridType.FIFTY_THOUSAND)


def test_codes_round_trip_at_centres_and_epsg():
    for code in ("01AA", "04HE00", "04HE99", "19ZZ4"):
        s = sheet_from_code(code); centre = ((s.e_min+s.e_max)/2, (s.n_min+s.n_max)/2)
        assert code_for_point(s.zone, *centre, s.grid_type) == code
    assert epsg_for_zone(1) == 6669 and epsg_for_zone(19) == 6687


@pytest.mark.parametrize("code", ["00AA", "20AA", "04A", "04HE5", "04HE0A"])
def test_bad_codes_have_reason(code):
    with pytest.raises(SheetCodeError): parse(code)


def test_bbox_excludes_contact_only_candidate():
    assert [x.sheet_code for x in sheets_covering_bbox(4, 280000, 120000, 320000, 150000, GridType.FIFTY_THOUSAND)] == ["04HE"]
