"""Actual IFC mutation evidence and fail-closed experimental compiler contract."""
from __future__ import annotations
from pathlib import Path
import hashlib
import tempfile
import unittest

import ifcopenshell
import ifcopenshell.geom
from lxml import etree as E

from src.runtime.compiler import CompilerError,compile_declarative_xml
from src.runtime.ifc_projection import project_ifc
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.transaction import TransactionError,stage_and_commit
from src.runtime.xml_parser import parse_xml

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"tests/fixtures/synthetic/input.ifc"

def source_xml():
    return project_ifc(SOURCE).xml

def insert_new_straight_wall(xml:bytes,*,identifier:str="new_standalone_wall",diagonal:bool=False):
    doc=parse_xml(xml)
    level=doc.levels[0].id
    x2=b"4" if not diagonal else b"3"
    wall=(b'<Wall id="'+identifier.encode()+b'" level="'+level.encode()+
          b'" x1="0" y1="4" z1="0" x2="'+x2+
          b'" y2="4" z2="0" height="3" thickness="0.2"/>')
    return xml.replace(b"<Elements>",b"<Elements>\n    "+wall)

class CompilerMutationTests(unittest.TestCase):
    def test_wall_height_update_changes_actual_ifc_extrusion(self):
        prior=SOURCE.read_bytes()
        xml=source_xml()
        changed=xml.replace(b'height="3" thickness="0.2"',
                            b'height="3.3" thickness="0.2"')
        self.assertNotEqual(xml,changed)
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"updated_wall.ifc"
            report=compile_declarative_xml(SOURCE,changed,dest)
            self.assertEqual([m.operation for m in report.operations],["UPDATE_WALL_HEIGHT"])
            self.assertTrue(dest.exists())
            self.assertNotEqual(dest.read_bytes(),prior)
            expected=ifcopenshell.open(str(dest)).by_type("IfcWall")[0]
            actual=next(i for r in expected.Representation.Representations
                        for i in r.Items if i.is_a("IfcExtrudedAreaSolid"))
            self.assertAlmostEqual(actual.Depth,3.3)
            shape=ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(),expected)
            self.assertGreater(len(shape.geometry.faces),0)
            self.assertGreater(report.untouched_root_objects_verified,10)
            self.assertEqual(report.unexpected_root_changes,())
            self.assertFalse(report.as_dict()["general_bim_edit_324_supported"])
        self.assertEqual(SOURCE.read_bytes(),prior)

    def test_noop_preserves_original_bytes_and_globalids(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"same.ifc"
            xml=source_xml()
            report=compile_declarative_xml(SOURCE,
                xml.replace(b'height="3" thickness="0.2"',b'thickness="0.20" height="3.0"'),
                out)
            self.assertEqual(report.operations,())
            self.assertEqual(out.read_bytes(),SOURCE.read_bytes())
            self.assertEqual(report.source_sha256,report.result_sha256)

    def test_create_straight_wall_is_real_ifc_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"created.ifc"
            xml=insert_new_straight_wall(source_xml())
            report=compile_declarative_xml(SOURCE,xml,dest)
            self.assertEqual(report.operations[0].operation,"CREATE_WALL")
            self.assertEqual(report.operations[0].xml_id,"new_standalone_wall")
            guid=report.operations[0].ifc_guid
            f=ifcopenshell.open(str(dest))
            self.assertEqual(len(f.by_type("IfcWall")),2)
            self.assertEqual(f.by_guid(guid).GlobalId,guid)
            self.assertIsNotNone(f.by_guid(guid).ObjectPlacement)
            self.assertTrue(f.by_guid(guid).ContainedInStructure)
            self.assertEqual(project_ifc(dest).report()["supported_counts"]["IfcWall"],2)
            # Keep SWIG triangulation owner alive while reading its geometry.
            mesh=ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(),f.by_guid(guid))
            self.assertGreater(len(mesh.geometry.faces),0)

    def test_delete_standalone_wall_after_real_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            new=Path(tmp)/"new.ifc"
            first=compile_declarative_xml(SOURCE,insert_new_straight_wall(source_xml()),new)
            guid=first.operations[0].ifc_guid
            second_projection=project_ifc(new)
            doc=E.fromstring(second_projection.xml)
            elements=doc.find('.//{%s}Elements'%doc.nsmap[None])
            elements.remove(next(x for x in elements if x.get("ifcGuid")==guid))
            edited=E.tostring(doc,encoding="utf-8",xml_declaration=True)
            gone=Path(tmp)/"removed.ifc"
            second=compile_declarative_xml(new,edited,gone)
            self.assertEqual(second.operations[0].operation,"DELETE_WALL")
            self.assertEqual(second.operations[0].ifc_guid,guid)
            f=ifcopenshell.open(str(gone))
            self.assertEqual(len(f.by_type("IfcWall")),1)
            with self.assertRaises(RuntimeError):
                f.by_guid(guid)
            self.assertEqual(len(f.by_type("IfcRelVoidsElement")),2)

    def test_combined_create_and_update_commits_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            xml=insert_new_straight_wall(source_xml()).replace(
                b'height="3" thickness="0.2"',b'height="3.25" thickness="0.2"')
            dest=Path(tmp)/"both.ifc"
            report=compile_declarative_xml(SOURCE,xml,dest)
            self.assertEqual({m.operation for m in report.operations},
                             {"CREATE_WALL","UPDATE_WALL_HEIGHT"})
            f=ifcopenshell.open(str(dest))
            self.assertEqual(len(f.by_type("IfcWall")),2)
            self.assertTrue(any(
                abs(item.Depth-3.25)<1e-5
                for w in f.by_type("IfcWall") for r in w.Representation.Representations
                for item in r.Items if item.is_a("IfcExtrudedAreaSolid")
            ))

class CompilerSafetyTests(unittest.TestCase):
    def test_invalid_xml_aborts_without_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"never.ifc"
            with self.assertRaises(CompilerError):
                compile_declarative_xml(SOURCE,b"<Building>",dest)
            self.assertFalse(dest.exists())

    def test_invalid_opening_placement_aborts(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"never.ifc"
            tampered=source_xml().replace(b'offset="1.6"',b'offset="5.8"')
            with self.assertRaises(CompilerError):
                compile_declarative_xml(SOURCE,tampered,dest)
            self.assertFalse(dest.exists())

    def test_wall_thickness_change_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"never.ifc"
            tampered=source_xml().replace(b'thickness="0.2"',b'thickness="0.3"',1)
            with self.assertRaisesRegex(CompilerError,"Only in-place"):
                compile_declarative_xml(SOURCE,tampered,dest)
            self.assertFalse(dest.exists())

    def test_cannot_delete_wall_with_hosted_openings(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"never.ifc"
            xml=source_xml()
            root=E.fromstring(xml)
            elems=root.find('.//{%s}Elements'%root.nsmap[None])
            wall=next(x for x in elems if E.QName(x).localname=="Wall")
            # Also remove hosted openings/fillings to keep XML valid; the
            # compiler must still reject non-wall removals.
            wid=wall.get("id")
            openings=[e for e in elems if e.get("host")==wid]
            opening_ids={e.get("id") for e in openings}
            for node in list(elems):
                if node==wall or node in openings or node.get("opening") in opening_ids:
                    elems.remove(node)
            changed=E.tostring(root,encoding="utf-8",xml_declaration=True)
            with self.assertRaises(CompilerError):
                compile_declarative_xml(SOURCE,changed,dest)
            self.assertFalse(dest.exists())

    def test_wrong_ifc_hash_aborts(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"never.ifc"
            projection=project_ifc(SOURCE)
            tampered=projection.xml.replace(projection.source.source_sha256.encode(),b"1"*64)
            with self.assertRaises(CompilerError):
                compile_declarative_xml(SOURCE,tampered,dest)
            self.assertFalse(dest.exists())

    def test_source_preserved_and_existing_output_refused(self):
        before=SOURCE.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"already.ifc"
            target.write_bytes(b"EXISTING OUTPUT")
            with self.assertRaises(CompilerError):
                compile_declarative_xml(SOURCE,source_xml(),target)
            self.assertEqual(target.read_bytes(),b"EXISTING OUTPUT")
        self.assertEqual(SOURCE.read_bytes(),before)

    def test_stage_writer_failure_does_not_commit_or_leave_temp(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"fail.ifc"
            def fail_writer(path):
                path.write_bytes(b"HALF_WRITTEN")
                raise ValueError("Simulated compiler failure")
            with self.assertRaisesRegex(ValueError,"Simulated"):
                stage_and_commit(dest,fail_writer,lambda _:None)
            self.assertFalse(dest.exists())
            self.assertEqual(list(Path(tmp).iterdir()),[])

    def test_stage_validator_failure_cleans_temp(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"fail.ifc"
            def writer(p):
                p.write_bytes(SOURCE.read_bytes())
            def fail_validator(_):
                raise ValueError("Simulated independent validator failure")
            with self.assertRaisesRegex(ValueError,"Simulated"):
                stage_and_commit(dest,writer,fail_validator)
            self.assertFalse(dest.exists())
            self.assertEqual(list(Path(tmp).iterdir()),[])

    def test_no_original_source_key_or_answer_access(self):
        data=source_xml()
        for forbidden in (b"ground_truth_ifc",b"OPENAI_API_KEY",b"evaluation"):
            self.assertNotIn(forbidden,data)

if __name__=="__main__":unittest.main()

class CompileReportAndCliTests(unittest.TestCase):
    def test_live_ifc_height_output_matches_public_report_schema(self):
        import json
        import jsonschema
        with tempfile.TemporaryDirectory() as tmp:
            result=compile_declarative_xml(
                SOURCE, source_xml().replace(
                    b'height="3" thickness="0.2"',
                    b'height="3.3" thickness="0.2"'),
                Path(tmp)/"updated.ifc")
            schema=json.loads((ROOT/"schemas/compile_report.schema.json").read_text())
            jsonschema.validate(result.as_dict(),schema)

    def test_compiler_cli_succeeds_offline(self):
        import json, subprocess, sys
        with tempfile.TemporaryDirectory() as tmp:
            updated=Path(tmp)/"edited.xml"
            updated.write_bytes(source_xml().replace(
                b'height="3" thickness="0.2"',
                b'height="3.3" thickness="0.2"'))
            result=Path(tmp)/"created.ifc"
            run=subprocess.run([sys.executable,"-m","tools.compile_markup",
                "--source-ifc",str(SOURCE),"--edited-xml",str(updated),
                "--result-ifc",str(result)],cwd=ROOT,capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stderr+run.stdout)
            content=json.loads(run.stdout)
            self.assertEqual(content["status"],"COMMITTED_SCOPED_IFC4X3_WALL_EDIT")
            self.assertTrue(result.is_file())
            self.assertTrue(content["write_committed"])

    def test_compiler_cli_invalid_does_not_emit_ifc(self):
        import json, subprocess, sys
        with tempfile.TemporaryDirectory() as tmp:
            invalid=Path(tmp)/"invalid.xml"
            invalid.write_bytes(b"<Building>")
            result=Path(tmp)/"never.ifc"
            run=subprocess.run([sys.executable,"-m","tools.compile_markup",
                "--source-ifc",str(SOURCE),"--edited-xml",str(invalid),
                "--result-ifc",str(result)],cwd=ROOT,capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,2)
            self.assertFalse(result.exists())
            self.assertEqual(json.loads(run.stdout)["status"],"BLOCKED_NO_RESULT_COMMITTED")

class RealPublishedIFCWallHeightTests(unittest.TestCase):
    def test_pinned_bim_edit_small_ifc_wall_edit_preserves_presentation_layers(self):
        source=ROOT/"data/ifc/simple/17_input.ifc"
        if not source.exists():
            self.skipTest("15KB pinned BIM-Edit input absent from ignored local test data")
        before_bytes=source.read_bytes()
        before=ifcopenshell.open(str(source))
        n_layers=len(before.by_type("IfcPresentationLayerAssignment"))
        input_xml=project_ifc(source).xml
        doc=parse_xml(input_xml)
        wall=next(w for w in doc.elements if w.kind=="Wall")
        old=('height="'+str(wall.attrs()["height"])+'"').encode()
        edit=input_xml.replace(old,b'height="3.1"',1)
        with tempfile.TemporaryDirectory() as tmp:
            result=Path(tmp)/"real_ifc_wall.ifc"
            report=compile_declarative_xml(source,edit,result)
            produced=ifcopenshell.open(str(result))
            changed=produced.by_guid(wall.ifc_guid)
            item=next(x for rep in changed.Representation.Representations
                      for x in rep.Items if x.is_a("IfcExtrudedAreaSolid"))
            self.assertAlmostEqual(item.Depth,3.1)
            self.assertEqual(len(produced.by_type("IfcPresentationLayerAssignment")),n_layers)
            self.assertEqual(report.unexpected_root_changes,())
            self.assertGreater(report.untouched_root_objects_verified,0)
            self.assertNotEqual(hashlib.sha256(result.read_bytes()).hexdigest(),
                                hashlib.sha256(before_bytes).hexdigest())
        self.assertEqual(source.read_bytes(),before_bytes)
