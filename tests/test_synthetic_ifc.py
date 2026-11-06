import hashlib
import unittest
from pathlib import Path
import ifcopenshell
import ifcopenshell.geom
from tools.generate_synthetic_ifc import build, stable_guid

ROOT=Path(__file__).resolve().parents[1]/"tests/fixtures/synthetic"

class SyntheticIFCTests(unittest.TestCase):
    def test_ifc4x3_and_geometry(self):
        f=ifcopenshell.open(str(ROOT/"input.ifc"))
        self.assertEqual(f.schema,"IFC4X3")
        for typ,count in [
            ("IfcProject",1),("IfcSite",1),("IfcBuilding",1),("IfcBuildingStorey",1),
            ("IfcWall",1),("IfcSlab",1),("IfcColumn",1),
            ("IfcDoor",1),("IfcWindow",1),("IfcSpace",1),("IfcOpeningElement",2),
            ("IfcRelVoidsElement",2),("IfcRelFillsElement",2),("IfcRelSpaceBoundary",1)
        ]:
            self.assertEqual(len(f.by_type(typ)),count,typ)
        for typ in ("IfcWall","IfcSlab","IfcColumn","IfcDoor","IfcWindow"):
            shape=ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(),f.by_type(typ)[0])
            self.assertGreater(len(shape.geometry.verts),0,typ)
            self.assertGreater(len(shape.geometry.faces),0,typ)

    def test_space_host_opening_relationships(self):
        f=ifcopenshell.open(str(ROOT/"input.ifc"))
        wall=f.by_type("IfcWall")[0]
        rels=f.by_type("IfcRelVoidsElement")
        self.assertTrue(all(r.RelatingBuildingElement==wall for r in rels))
        fills=f.by_type("IfcRelFillsElement")
        self.assertEqual({f.RelatedBuildingElement.is_a() for f in fills},{"IfcWindow","IfcDoor"})
        self.assertEqual({f.RelatingOpeningElement for f in fills},{r.RelatedOpeningElement for r in rels})
        self.assertEqual(f.by_type("IfcRelSpaceBoundary")[0].RelatingSpace.is_a(),"IfcSpace")
        self.assertEqual(f.by_type("IfcRelSpaceBoundary")[0].RelatedBuildingElement,wall)

    def test_stable_ids_across_generated_outputs(self):
        orig=ifcopenshell.open(str(ROOT/"input.ifc"))
        tall=ifcopenshell.open(str(ROOT/"expected_wall_height.ifc"))
        moved=ifcopenshell.open(str(ROOT/"expected_window_move.ifc"))
        for typ in ("IfcWall","IfcSlab","IfcColumn","IfcDoor","IfcWindow","IfcSpace","IfcOpeningElement"):
            self.assertEqual(sorted(x.GlobalId for x in orig.by_type(typ)),
                             sorted(x.GlobalId for x in tall.by_type(typ)))
            self.assertEqual(sorted(x.GlobalId for x in orig.by_type(typ)),
                             sorted(x.GlobalId for x in moved.by_type(typ)))
        self.assertEqual(orig.by_type("IfcWall")[0].GlobalId,stable_guid("wall"))

    def test_predicted_wall_change_and_window_location(self):
        orig=ifcopenshell.open(str(ROOT/"input.ifc"))
        tall=ifcopenshell.open(str(ROOT/"expected_wall_height.ifc"))
        moved=ifcopenshell.open(str(ROOT/"expected_window_move.ifc"))
        self.assertNotEqual(
            orig.by_type("IfcWall")[0].Representation.Representations[0].Items[0].Depth,
            tall.by_type("IfcWall")[0].Representation.Representations[0].Items[0].Depth)
        # Window fill and opening should move consistently to a new absolute X.
        def x(m,typ):
            # Nested IFC placements: a window is relative to its opening.
            import ifcopenshell.util.placement
            return float(ifcopenshell.util.placement.get_local_placement(m.by_type(typ)[0].ObjectPlacement)[0,3])
        self.assertNotEqual(x(orig,"IfcWindow"),x(moved,"IfcWindow"))
        self.assertNotEqual(x(orig,"IfcOpeningElement"),x(moved,"IfcOpeningElement"))

    def test_generated_files_bounded(self):
        files=list(ROOT.glob("*.ifc"))
        self.assertEqual(len(files),3)
        self.assertTrue(all(0<p.stat().st_size<100_000 for p in files))

if __name__=="__main__": unittest.main()

class SyntheticRightsLedgerTests(unittest.TestCase):
    def test_fixture_content_hashes_and_explicit_rights(self):
        import json
        from src.security.agent_boundary import LicenseRecord
        repo=Path(__file__).resolve().parents[1]
        rights=json.loads((repo/"manifests/source_rights.json").read_text())
        for p in sorted((repo/"tests/fixtures/synthetic").glob("*.ifc")):
            line=next(x for x in rights["records"] if x["source"]==str(p.relative_to(repo)))
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),line["source_digest_sha256"])
            LicenseRecord(
                source=line["source"],source_digest_sha256=line["source_digest_sha256"],
                asset_rights=line["asset_rights"],rights_checked=line["rights_checked"],
                redistribution_permitted=line["redistribution_permitted"],
                consent_documented=line["consent_documented"]
            ).authorize_redistribution()
        for third in [x for x in rights["records"] if x["source"].startswith(("BIM-Edit/","sylvainHellin/","BIBIMBAP"))]:
            self.assertFalse(third["redistribution_permitted"])
