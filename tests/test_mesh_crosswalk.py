import unittest
from scripts.build_sheet_mesh_crosswalk import calculate, mesh_bounds, mesh_code


class MeshCrosswalkTests(unittest.TestCase):
    def test_independent_mesh_definitions(self):
        self.assertEqual(mesh_code(1,53,39),'5339')
        self.assertEqual(mesh_code(2,53*8+4,39*8+5),'533945')
        self.assertEqual(mesh_code(3,53*80+41,39*80+52),'53394512')
        west,south,east,north = mesh_bounds(2,53*8+4,39*8+5)
        self.assertAlmostEqual(west,139.625)
        self.assertAlmostEqual(south,35+40/60)
        self.assertAlmostEqual(east,139.75)
        self.assertAlmostEqual(north,35.75)

    def test_known_sheet_coverage_and_refinement(self):
        for level in (1,2,3):
            rows,qa,_=calculate('04HE00',level,100)
            fine,fqa,_=calculate('04HE00',level,50)
            self.assertEqual({r['mesh_code'] for r in rows},{r['mesh_code'] for r in fine})
            self.assertEqual(qa['sheet_area_m2'],12000000)
            self.assertLess(qa['uncovered_m2'],0.01)
            self.assertLess(fqa['sum_error_m2'],0.01)
            self.assertTrue(all(0<r['sheet_coverage_ratio']<=1+1e-12 for r in fine))
            self.assertTrue(all(r['availability']=='unverified' for r in fine))


if __name__=='__main__': unittest.main()
