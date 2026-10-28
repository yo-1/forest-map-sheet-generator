import csv
from pathlib import Path
import unittest

from forest_map_sheet_generator.core.codes import SheetCodeError, parse
from forest_map_sheet_generator.core.grid import children, parent_from_point, sheet_from_code, sheets_covering_bbox


class GridTests(unittest.TestCase):
    def test_independent_fixed_expectations(self):
        with (Path(__file__).parent / 'fixtures' / 'expected_grids.csv').open(encoding='utf-8') as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), 11)
        for expected in rows:
            with self.subTest(code=expected['code']):
                sheet = sheet_from_code(expected['code'])
                self.assertEqual(sheet.grid_type, expected['grid_type'])
                self.assertEqual((sheet.e_min, sheet.e_max, sheet.n_min, sheet.n_max), tuple(float(expected[key]) for key in ('e_min', 'e_max', 'n_min', 'n_max')))

    def test_parent_grid_all_zones(self):
        for zone in range(1, 20):
            for row, letter in enumerate('ABCDEFGHIJKLMNOPQRST'):
                for col, column in enumerate('ABCDEFGH'):
                    with self.subTest(zone=zone, row=row, col=col):
                        e, n = -160000 + col * 40000 + 20000, 300000 - row * 30000 - 15000
                        expected = f'{zone:02d}{letter}{column}'
                        self.assertEqual(parent_from_point(zone, e, n).sheet_code, expected)
                        self.assertEqual(sheets_covering_bbox(zone, e-1, n-1, e+1, n+1, '50000')[0].sheet_code, expected)

    def test_5000_partition(self):
        sheets = children('04HE', '5000')
        self.assertEqual(len(sheets), 100)
        self.assertEqual(len({s.sheet_code for s in sheets}), 100)
        self.assertEqual(sum(s.width * s.height for s in sheets), 40000 * 30000)
        for i in range(10):
            for j in range(10):
                s = sheets[i*10+j]
                self.assertEqual((s.e_min, s.e_max, s.n_min, s.n_max), (j*4000, (j+1)*4000, 87000-i*3000, 90000-i*3000))

    def test_quarter_partition(self):
        sheets = children('04HE', 'forest_quarter')
        self.assertEqual([s.sheet_code for s in sheets], ['04HE1', '04HE2', '04HE3', '04HE4'])
        self.assertEqual(sum(s.width * s.height for s in sheets), 40000 * 30000)
        for s in sheets:
            self.assertEqual((s.width, s.height), (20000, 15000))
        for i, a in enumerate(sheets):
            for b in sheets[i+1:]:
                area = max(0, min(a.e_max,b.e_max)-max(a.e_min,b.e_min)) * max(0, min(a.n_max,b.n_max)-max(a.n_min,b.n_min))
                self.assertEqual(area, 0)

    def test_boundaries_and_four_quadrants(self):
        for e, n, code in [(-1,-1,'04KD'), (1,-1,'04KE'), (-1,1,'04JD'), (1,1,'04JE'), (0,0,'04JE'), (0,60000,'04HE'), (40000,90000,'04GF'), (-160000,-300000,'04TA')]:
            self.assertEqual(parent_from_point(4,e,n).sheet_code, code)
        self.assertEqual(sheets_covering_bbox(4,0,60000,40000,90000,'50000'), [sheet_from_code('04HE')])
        self.assertEqual(sheets_covering_bbox(4,-160000,-300000,160000,300000,'50000').__len__(),160)
        for e,n in [(160000,0),(0,300000),(-160001,0),(0,-300001),(float('nan'),0)]:
            with self.assertRaises(SheetCodeError): parent_from_point(4,e,n)
        with self.assertRaises(SheetCodeError): sheets_covering_bbox(4,-160001,0,0,1,'50000')

    def test_tiny_positive_overlap_and_touch(self):
        self.assertEqual({s.sheet_code for s in sheets_covering_bbox(4,-1,60001,1e-8,60002,'50000')}, {'04HD','04HE'})
        self.assertEqual([s.sheet_code for s in sheets_covering_bbox(4,-1,60001,0,60002,'50000')], ['04HD'])
        self.assertEqual(sheets_covering_bbox(4,0,0,0,1,'50000'), [])
        for kind in ('5000', 'forest_quarter'):
            s=sheet_from_code('04HE00' if kind=='5000' else '04HE1')
            self.assertEqual(sheets_covering_bbox(4,s.e_min,s.n_min,s.e_max,s.n_max,kind),[s])

    def test_code_validation(self):
        for code in ('04HE','04HE00','04HE99','04HE1','19TH4','09IE','09OE'):
            self.assertEqual(sheet_from_code(code).sheet_code,code)
        self.assertEqual(parse(' 04he ')['row_letter'],'H')
        for bad in ('00HE','20HE','04UH','04HI','04HEA','04HE5','04HE000','19ZZ4'):
            with self.assertRaises(SheetCodeError): parse(bad)
        with self.assertRaises(SheetCodeError): sheets_covering_bbox(4,0,0,1,1,'2500')


if __name__ == '__main__': unittest.main()
