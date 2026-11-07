"""Independent IFC->XML read-only projection, unsupported ledger, exact no-op."""
from __future__ import annotations
import hashlib
from pathlib import Path
import tempfile
import unittest

import ifcopenshell
from src.runtime.ifc_projection import UnsupportedIFCGeometry, project_ifc
from src.runtime.ifc_snapshot import SourceIntegrityError, passthrough_noop, snapshot_source
from src.runtime.xml_parser import parse_xml

ROOT=Path(__file__).resolve().parents[1]
FIXTURES=ROOT/"tests/fixtures/synthetic"

class SyntheticProjectionTests(unittest.TestCase):
    def test_all_synthetic_sources_parse_with_stable_guids(self):
        for path in sorted(FIXTURES.glob("*.ifc")):
            with self.subTest(path=path.name):
                projection=project_ifc(path)
                doc=parse_xml(projection.xml,
                              expected_source_sha256=projection.source.source_sha256)
                self.assertEqual(projection.source.ifc_schema,"IFC4X3")
                self.assertEqual(len(doc.levels),1)
                self.assertEqual(len(doc.elements),7)
                self.assertEqual(len(doc.relations),0)
                self.assertEqual(len(projection.projected_global_ids),8)
                self.assertEqual(projection.report()["unsupported_counts"],{"IfcSpace":1})
                self.assertIn("IfcRelSpaceBoundary:", " ".join(projection.opaque_relation_reasons))
                ifc=ifcopenshell.open(str(path))
                allguids={e.GlobalId for e in ifc.by_type("IfcRoot")}
                self.assertTrue(all(g in allguids for g in dict(projection.projected_global_ids)))
                self.assertFalse(b"<Create" in projection.xml)

    def test_exact_xml_projection_is_deterministic_for_same_ifc(self):
        path=FIXTURES/"input.ifc"
        a=project_ifc(path)
        b=project_ifc(path)
        self.assertEqual(a.xml,b.xml)
        self.assertEqual(a.projected_global_ids,b.projected_global_ids)
        self.assertEqual(a.opaque_references,b.opaque_references)
        self.assertEqual(a.source.graph_fingerprint,b.source.graph_fingerprint)

    def test_geometry_and_derived_hosts_correct(self):
        p=project_ifc(FIXTURES/"input.ifc")
        d=parse_xml(p.xml)
        by_kind={k:[e for e in d.elements if e.kind==k]
                 for k in ("Wall","Slab","Column","Opening","Window","Door")}
        wall=by_kind["Wall"][0]
        self.assertEqual(float(wall.attrs()["height"]),3.0)
        self.assertEqual(float(wall.attrs()["thickness"]),0.2)
        self.assertEqual(float(wall.attrs()["x2"]),6.0)
        self.assertEqual(len(by_kind["Opening"]),2)
        self.assertEqual({o.attrs()["host"] for o in by_kind["Opening"]},{wall.id})
        self.assertEqual({o.attrs()["offset"] for o in by_kind["Opening"]},
                         {__import__("decimal").Decimal("1.6"),__import__("decimal").Decimal("3.7")})
        self.assertEqual({w.attrs()["opening"] for w in by_kind["Window"]+by_kind["Door"]},
                         {o.id for o in by_kind["Opening"]})

    def test_missing_space_geometry_is_explicit_unsupported(self):
        p=project_ifc(FIXTURES/"input.ifc")
        missing=[r for r in p.opaque_references if r.ifc_class=="IfcSpace"]
        self.assertEqual(len(missing),1)
        self.assertIn("representation",missing[0].reason)
        self.assertEqual(p.report()["unsupported_counts"]["IfcSpace"],1)
        with self.assertRaisesRegex(UnsupportedIFCGeometry,"Unsupported editable"):
            project_ifc(FIXTURES/"input.ifc",strict_on_opaque=True)

    def test_missing_opening_host_becomes_opaque_not_invented(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=ifcopenshell.open(str(FIXTURES/"input.ifc"))
            rel=next(r for r in f.by_type("IfcRelVoidsElement")
                     if r.RelatedOpeningElement.Name=="Window Opening")
            f.remove(rel)
            source=Path(tmp)/"missing_host.ifc"
            f.write(str(source))
            p=project_ifc(source)
            self.assertEqual(p.report()["unsupported_counts"]["IfcOpeningElement"],1)
            self.assertEqual(p.report()["unsupported_counts"]["IfcWindow"],1)
            self.assertIn("unique managed IfcWall host",
                          " ".join(x.reason for x in p.opaque_references))

class ImmutableNoopTests(unittest.TestCase):
    def test_noop_copy_is_exact_bytes_and_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=FIXTURES/"input.ifc"
            before=path.read_bytes()
            projection=project_ifc(path)
            initial=parse_xml(projection.xml)
            edited=parse_xml(projection.xml.replace(b'height="3"',b'height="3.0"'))
            out=Path(tmp)/"result.ifc"
            copied=passthrough_noop(projection.source,initial,edited,out)
            self.assertEqual(out.read_bytes(),before)
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(copied.source_sha256,projection.source.source_sha256)
            self.assertEqual(copied.graph_fingerprint,projection.source.graph_fingerprint)
            self.assertEqual(copied.entity_count,projection.source.entity_count)
            self.assertEqual(copied.global_ids,projection.source.global_ids)
            self.assertEqual(copied.named_relation_memberships,projection.source.named_relation_memberships)
            self.assertEqual(copied.entity_class_counts,projection.source.entity_class_counts)

    def test_actual_xml_edit_is_refused_no_result_ifc_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            projection=project_ifc(FIXTURES/"input.ifc")
            initial=parse_xml(projection.xml)
            changed=parse_xml(projection.xml.replace(b'height="3"',b'height="3.5"'))
            destination=Path(tmp)/"result.ifc"
            with self.assertRaisesRegex(SourceIntegrityError,"unavailable"):
                passthrough_noop(projection.source,initial,changed,destination)
            self.assertFalse(destination.exists())

    def test_cannot_overwrite_input_or_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=project_ifc(FIXTURES/"input.ifc")
            d=parse_xml(p.xml)
            with self.assertRaises(SourceIntegrityError):
                passthrough_noop(p.source,d,d,p.source.source_file)
            target=Path(tmp)/"result.ifc"
            target.write_bytes(b"existing")
            with self.assertRaises(SourceIntegrityError):
                passthrough_noop(p.source,d,d,target)
            self.assertEqual(target.read_bytes(),b"existing")

    def test_changed_source_since_snapshot_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            input=Path(tmp)/"source.ifc"
            input.write_bytes((FIXTURES/"input.ifc").read_bytes())
            p=project_ifc(input)
            d=parse_xml(p.xml)
            input.write_bytes(input.read_bytes()+b"\n")
            target=Path(tmp)/"result.ifc"
            with self.assertRaisesRegex(SourceIntegrityError,"changed since"):
                passthrough_noop(p.source,d,d,target)
            self.assertFalse(target.exists())

    def test_semantic_graph_hash_detects_non_geometry_edit(self):
        import ifcopenshell.api.pset
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)/"with_psets.ifc"
            f=ifcopenshell.open(str(FIXTURES/"input.ifc"))
            wall=f.by_type("IfcWall")[0]
            pset=ifcopenshell.api.pset.add_pset(f,product=wall,name="Pset_Proof")
            ifcopenshell.api.pset.edit_pset(f,pset=pset,properties={"FireRating":"F120"})
            f.write(str(base))
            snapshot=snapshot_source(base)
            projection=project_ifc(base)
            d=parse_xml(projection.xml)
            copied=passthrough_noop(projection.source,d,d,Path(tmp)/"copy.ifc")
            self.assertEqual(copied.graph_fingerprint,snapshot.graph_fingerprint)
            mutated=ifcopenshell.open(str(base))
            prop=mutated.by_type("IfcPropertySingleValue")[0]
            prop.NominalValue=mutated.create_entity("IfcLabel","F60")
            changed=Path(tmp)/"changed.ifc"
            mutated.write(str(changed))
            self.assertNotEqual(snapshot.graph_fingerprint,
                                snapshot_source(changed).graph_fingerprint)

class RealBenchmarkTinyAssetTests(unittest.TestCase):
    def test_pinned_real_ifc_17_wall_projection(self):
        p=ROOT/"data/ifc/simple/17_input.ifc"
        if not p.exists():
            self.skipTest("15 KiB pinned real IFC file not cached")
        projected=project_ifc(p,strict_on_opaque=True)
        report=projected.report()
        self.assertEqual(report["supported_counts"]["IfcWall"],5)
        self.assertEqual(report["supported_counts"]["IfcBuildingStorey"],2)
        self.assertEqual(report["unsupported_counts"],{})
        doc=parse_xml(projected.xml)
        self.assertEqual(len(doc.elements),5)
        self.assertGreaterEqual(len(doc.relations),1)
        self.assertEqual(set(x.kind for x in doc.elements),{"Wall"})
        self.assertEqual(projected.source.source_sha256,hashlib.sha256(p.read_bytes()).hexdigest())
        self.assertGreater(projected.source.entity_count,0)
        self.assertGreaterEqual(projected.source.manifest()["relation_edges"],1)

if __name__=="__main__":unittest.main()
