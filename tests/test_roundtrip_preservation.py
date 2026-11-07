"""Explicit source-GUID, property/material, relation and fail-closed G1 gates."""
from __future__ import annotations

from pathlib import Path
import hashlib
import tempfile
import unittest

import ifcopenshell
import ifcopenshell.api.pset
import ifcopenshell.api.material
from lxml import etree as ET

from src.runtime.compiler import compile_declarative_xml,CompilerError
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.ifc_projection import project_ifc
from tests.oracles.python.independent_ifc_checker import parity_report, inspect_ifc
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"tests/fixtures/synthetic/input.ifc"
NS="urn:bim-markup-bench:toy:v0"


def _material_source(tmp:Path)->tuple[Path,str]:
    output=tmp/"pset_material_source.ifc"
    model=ifcopenshell.open(str(SOURCE))
    wall=model.by_type("IfcWall")[0]
    guid=wall.GlobalId
    properties=ifcopenshell.api.pset.add_pset(
        model,product=wall,name="Pset_WallCommon")
    ifcopenshell.api.pset.edit_pset(model,pset=properties,
        properties={"Reference":"Research-G1-16","FireRating":"REI 90"})
    material=ifcopenshell.api.material.add_material(model,
        name="Test Lightweight Concrete",category="concrete")
    ifcopenshell.api.material.assign_material(model,products=[wall],material=material)
    model.write(str(output))
    return output,guid


def _wall_height_xml(model_path:Path,wall_guid:str,height:str)->bytes:
    root=ET.fromstring(project_ifc(model_path).xml)
    walls=[x for x in root.iter() if isinstance(x.tag,str) and
           ET.QName(x).localname=="Wall" and x.get("ifcGuid")==wall_guid]
    assert len(walls)==1
    walls[0].set("height",height)
    return ET.tostring(root,encoding="utf-8",xml_declaration=True)


class NoopPreservationTests(unittest.TestCase):
    def test_noop_strict_preservation_with_actual_material_psets_and_relations(self):
        with tempfile.TemporaryDirectory() as t:
            temp=Path(t)
            source,guid=_material_source(temp)
            before_bytes=source.read_bytes()
            before=snapshot_source(source)
            p=project_ifc(source)
            out=temp/"noop.ifc"
            report=compile_declarative_xml(source,p.xml,out)
            after=snapshot_source(out)
            self.assertEqual(report.operations,())
            self.assertEqual(before_bytes,out.read_bytes())
            self.assertEqual(before.graph_fingerprint,after.graph_fingerprint)
            self.assertEqual(before.global_ids,after.global_ids)
            self.assertEqual(before.entity_class_counts,after.entity_class_counts)
            self.assertEqual(before.named_relation_memberships,after.named_relation_memberships)
            state=inspect_ifc(out)
            self.assertGreaterEqual(len(state["materials"]),1)
            self.assertGreaterEqual(len(state["property_sets"]),1)
            self.assertTrue(any("FireRating" in str(ps) for ps in state["property_sets"].values()))
            self.assertTrue(any("Lightweight Concrete" in str(m) for m in state["materials"]))
            self.assertEqual(source.read_bytes(),before_bytes)

    def test_height_edit_preserves_property_sets_and_materials_between_arms(self):
        with tempfile.TemporaryDirectory() as t:
            temp=Path(t)
            source,guid=_material_source(temp)
            original=source.read_bytes()
            xml=_wall_height_xml(source,guid,"3.4")
            d0=temp/"D0.ifc"
            i0=temp/"I0.ifc"
            actual=compile_declarative_xml(source,xml,d0)
            manual_ifc_reference(source,i0,"UPDATE_WALL_HEIGHT",
                                 target_guid=guid,height=3.4)
            report=parity_report(d0,i0)
            self.assertTrue(report["parity"],str(report))
            self.assertEqual(actual.unexpected_root_changes,())
            self.assertEqual(inspect_ifc(source)["materials"],inspect_ifc(d0)["materials"])
            self.assertEqual(inspect_ifc(source)["property_sets"],inspect_ifc(d0)["property_sets"])
            self.assertEqual(source.read_bytes(),original)


class FailClosedGateTests(unittest.TestCase):
    def test_malformed_xml_cannot_overwrite_committed_ifc(self):
        with tempfile.TemporaryDirectory() as t:
            temp=Path(t)
            prior=temp/"result.ifc"
            prior.write_bytes(b"PRIOR_COMMITTED_OUTPUT")
            before=prior.read_bytes()
            with self.assertRaises(CompilerError):
                compile_declarative_xml(SOURCE,b"<Building>",prior)
            self.assertEqual(prior.read_bytes(),before)
            self.assertEqual(list(temp.iterdir()),[prior])

    def test_missing_host_and_wrong_native_guid_leave_no_partial_files(self):
        for condition in ("missing_host","changed_guid","invalid_space"):
            with self.subTest(case=condition),tempfile.TemporaryDirectory() as t:
                temp=Path(t)
                source=project_ifc(SOURCE).xml
                if condition=="missing_host":
                    corrupt=source.replace(b'host="wall_',b'host="invalid_host_wall_',1)
                elif condition=="changed_guid":
                    corrupt=source.replace(b'ifcGuid="2L_lrSH5fHAgIRV7tit5Pp"',
                                           b'ifcGuid="1111111111111111111111"')
                else:
                    # Existing synthetic IfcSpace has no geometric representation:
                    # inserting a fake physical bound would be a modeling lie.
                    root=ET.fromstring(source)
                    rels=root.find(".//{"+NS+"}Relations")
                    ET.SubElement(rels,"{"+NS+"}SpaceBoundary",
                                  {"space":"fake_room","element":
                                   next(x.get("id") for x in root.iter()
                                        if isinstance(x.tag,str) and ET.QName(x).localname=="Wall"),
                                   "kind":"PHYSICAL"})
                    corrupt=ET.tostring(root,encoding="utf-8",xml_declaration=True)
                out=temp/"never.ifc"
                with self.assertRaises(CompilerError):
                    compile_declarative_xml(SOURCE,corrupt,out)
                self.assertFalse(out.exists())
                self.assertEqual(list(temp.iterdir()),[])

    def test_failed_stage_leaves_last_valid_file_untouched(self):
        with tempfile.TemporaryDirectory() as t:
            temp=Path(t)
            valid=temp/"good.ifc"
            p=project_ifc(SOURCE)
            xml=p.xml.replace(b'height="3" thickness="0.2"',
                              b'height="3.3" thickness="0.2"')
            compile_declarative_xml(SOURCE,xml,valid)
            digest=hashlib.sha256(valid.read_bytes()).hexdigest()
            corrupted=p.xml.replace(b'host="wall_',b'host="stale_wrong_wall_',1)
            with self.assertRaises(CompilerError):
                compile_declarative_xml(SOURCE,corrupted,valid)
            self.assertEqual(hashlib.sha256(valid.read_bytes()).hexdigest(),digest)
            self.assertEqual(len(list(temp.glob("*.ifc"))),1)

if __name__=="__main__":unittest.main()
