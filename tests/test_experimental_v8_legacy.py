"""Original BIBIMBAP IFC2X3/IFC4 prospective v0.8 native source tests.

Tests use real *public source IFC*, never hidden benchmark GT, scorer
feedback, API provider, or BIXML/Xim product. Fixed developer XML tasks
are not model success. Independent oracle is separate from compiler.
"""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import time
import unittest

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v8_legacy_projection import (
    project_legacy_v8,parse_v8,LegacyV8Error,Q,
)
from src.runtime.experimental_v8_legacy_compiler import (
    compile_declarative_xml_v8,LegacyV8CompileError,_det_guid,
)
from tools.oracle_bibimbap_v08_native import (
    verify_ifc4_wall,verify_ifc2x3_space,verify_ifc2x3_hosted_door,
    IndependentLegacyV8Error,
)
from tools.bibimbap_matched25_tools import file_hash

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",r"D:\문서\D__1_Projects\202611"))
DATA=BASE/"bibimbap-author-data"/"ifc"
SRC={
    "wall":"empty.ifc",
    "space":"01/01/01_01_004.ifc",
    "door":"01/01/01_01_003.ifc",
}
SOURCE_SOUTH="3YQ$1CPXD2Mh2vQ18vV$hw"
SOURCE_NORTH="3YQ$1CPXD2Mh2vQ18vV$ig"


class PublicNativeLegacy(unittest.TestCase):
    def original(self,kind):
        original=DATA/SRC[kind]
        if not original.exists():
            self.skipTest("Original pinned public BIBIMBAP IFC dataset not mounted")
        td=tempfile.TemporaryDirectory(prefix="bibi130-original-native-")
        self.addCleanup(td.cleanup)
        folder=Path(td.name)
        before=file_hash(original)
        self.addCleanup(lambda:self.assertEqual(file_hash(original),before))
        f=ifcopenshell.open(str(original))
        native=folder/"native_source_metres.ifc"
        ifcopenshell.util.unit.convert_file_length_units(f,"METER").write(str(native))
        normalized_sha=file_hash(native)
        self.addCleanup(lambda:self.assertEqual(file_hash(native),normalized_sha))
        view=project_legacy_v8(native)
        self.assertEqual(view.native_schema,f.schema)
        self.assertEqual(view.source_sha256,normalized_sha)
        tree=parse_v8(view.xml,source_sha256=normalized_sha,native_schema=f.schema)
        return original,native,folder,view,tree

    def fixture(self,kind):
        original,native,folder,view,root=self.original(kind)
        ground=next(x for x in root.findall("./"+Q+"Levels/"+Q+"Level")
                    if abs(float(x.get("placementZ")))<1e-8)
        elements=root.find(Q+"Elements")
        if kind=="wall":
            target=etree.SubElement(elements,Q+"Wall",{
                "id":"original_geometry05_wall",
                "level":ground.get("id"),
                "x1":"10","y1":"5","z1":"0",
                "x2":"15","y2":"5","z2":"0",
                "height":"3","thickness":".2",
            })
            ids=(target.get("id"),)
        elif kind=="space":
            target=etree.SubElement(elements,Q+"Space",{
                "id":"original_geometry04_space",
                "level":ground.get("id"),
                "x":".2","y":".2","z":"0",
                "width":"6.1","depth":"6.5","height":"2.8",
            })
            ids=(target.get("id"),)
        elif kind=="door":
            host=next(x for x in root.findall(".//"+Q+"Wall")
                      if x.get("ifcGuid")==SOURCE_NORTH)
            opening=etree.SubElement(elements,Q+"Opening",{
                "id":"original_geometry03_opening",
                "host":host.get("id"),
                "offset":"2.75","sill":"0","width":"1","height":"2.1",
            })
            door=etree.SubElement(elements,Q+"Door",{
                "id":"original_geometry03_door",
                "opening":opening.get("id"),
                "width":"1","height":"2.1",
            })
            ids=(opening.get("id"),door.get("id"))
        else:
            raise AssertionError("Unexpected original native task")
        return original,native,folder,view,root,ids

    def completed(self,kind):
        original,native,folder,view,root,ids=self.fixture(kind)
        out=folder/"candidate_native_schema.ifc"
        report=compile_declarative_xml_v8(
            native,etree.tostring(root,encoding="utf8"),out)
        guids=[_det_guid(view.source_sha256,i) for i in ids]
        return original,native,folder,view,root,ids,out,report,guids


class NativePositiveLegacy(PublicNativeLegacy):
    def test_all_three_native_original_sources_project_to_valid_schema_pinned_xml(self):
        for kind,expected_cls in (("wall",0),("space",7),("door",3)):
            with self.subTest(case=kind):
                original,native,folder,view,tree=self.original(kind)
                self.assertEqual(len(view.projected_guids),expected_cls)
                self.assertEqual(tree.get("sourceIfcSchema"),
                                 ifcopenshell.open(str(original)).schema)
                self.assertNotIn("IFC4X3",view.xml.decode())
                self.assertEqual(len(tree.findall("./"+Q+"Levels/"+Q+"Level")),
                                 len(ifcopenshell.open(str(native)).by_type("IfcBuildingStorey")))

    def test_ifc4_source_null_elevation_is_explicitly_missing_not_fake_zero(self):
        original,native,folder,view,tree=self.original("wall")
        self.assertEqual(len(tree.find(Q+"Elements")),0)
        level=tree.find("./"+Q+"Levels/"+Q+"Level")
        self.assertEqual(level.get("elevationState"),"MISSING")
        self.assertNotIn("elevation",level.attrib)
        self.assertEqual(level.get("placementZ"),"0")
        self.assertIsNone(ifcopenshell.open(str(native)).by_type("IfcBuildingStorey")[0].Elevation)

    def test_original_ifc4_wall_native_schema_placement_and_original_aggregation(self):
        _,native,folder,view,root,ids,out,report,guids=self.completed("wall")
        self.assertEqual(report.operations[0].operation,"CREATE_ORIGINAL_IFC4_WALL")
        self.assertFalse(report.as_dict()["original_45_task_native_equivalence"])
        proof=verify_ifc4_wall(native,out,guids[0])
        self.assertTrue(proof["original_storey_elevation_remains_missing"])
        self.assertEqual(ifcopenshell.open(str(out)).schema,"IFC4")

    def test_original_ifc2x3_space_native_schema_exact_geometry_and_aggregation(self):
        _,native,folder,view,root,ids,out,report,guids=self.completed("space")
        self.assertEqual(report.operations[0].operation,"CREATE_ORIGINAL_IFC2X3_SPACE")
        proof=verify_ifc2x3_space(native,out,guids[0])
        self.assertEqual(proof["all_original_products_world_mesh_preserved"],7)
        self.assertEqual(ifcopenshell.open(str(out)).schema,"IFC2X3")

    def test_original_ifc2x3_door_and_real_wall_boolean_void_native_relations(self):
        _,native,folder,view,root,ids,out,report,guids=self.completed("door")
        self.assertEqual(report.operations[0].operation,
                         "CREATE_ORIGINAL_IFC2X3_HOSTED_DOOR")
        proof=verify_ifc2x3_hosted_door(native,out,guids[0],guids[1])
        self.assertAlmostEqual(proof["host_wall_physical_void_volume_cubic_m"],.42,places=3)
        self.assertEqual(ifcopenshell.open(str(out)).schema,"IFC2X3")

    def test_fixed_original_source_native_schema_edits_are_byte_stable_across_clock_seconds(self):
        for kind in SRC:
            with self.subTest(case=kind):
                original,native,folder,view,root,ids=self.fixture(kind)
                edited=etree.tostring(root,encoding="utf8")
                p=folder/"candidate1.ifc"
                q=folder/"candidate2.ifc"
                compile_declarative_xml_v8(native,edited,p)
                # A timestamp injected by IfcOpenShell after this interval
                # would break byte-stability without source-anchored ownership.
                time.sleep(1.1)
                compile_declarative_xml_v8(native,edited,q)
                self.assertEqual(file_hash(p),file_hash(q))
                self.assertEqual(p.read_bytes(),q.read_bytes())


class NativeNegativeLegacy(PublicNativeLegacy):
    def test_ifc4_storey_missing_elevation_cannot_be_fabricated(self):
        _,native,folder,view,root,ids=self.fixture("wall")
        level=root.find("./"+Q+"Levels/"+Q+"Level")
        level.set("elevationState","EXPLICIT")
        level.set("elevation","0")
        out=folder/"fabricated_elevation.ifc"
        with self.assertRaisesRegex(LegacyV8CompileError,"Storey"):
            compile_declarative_xml_v8(native,etree.tostring(root),out)
        self.assertFalse(out.exists())

    def test_ifc4_storey_placement_must_remain_original(self):
        _,native,folder,view,root,ids=self.fixture("wall")
        level=root.find("./"+Q+"Levels/"+Q+"Level")
        level.set("placementZ","10")
        out=folder/"altered_placement.ifc"
        with self.assertRaisesRegex(LegacyV8CompileError,"Storey"):
            compile_declarative_xml_v8(native,etree.tostring(root),out)
        self.assertFalse(out.exists())

    def test_ifc4_source_schema_mislabelled_ifc2x3_refused(self):
        _,native,folder,view,root,ids=self.fixture("wall")
        root.set("sourceIfcSchema","IFC2X3")
        out=folder/"wrong_schema.ifc"
        with self.assertRaises(LegacyV8Error):
            compile_declarative_xml_v8(native,etree.tostring(root),out)
        self.assertFalse(out.exists())

    def test_wrong_original_source_digest_rejected_and_existing_output_preserved(self):
        _,native,folder,view,root,ids=self.fixture("wall")
        root.set("sourceModelSha256","0"*64)
        out=folder/"wrong_hash.ifc"
        with self.assertRaises(LegacyV8Error):
            compile_declarative_xml_v8(native,etree.tostring(root),out)
        self.assertFalse(out.exists())
        root.set("sourceModelSha256",view.source_sha256)
        out.write_bytes(b"Pre-existing research evidence")
        with self.assertRaisesRegex(LegacyV8CompileError,"unused"):
            compile_declarative_xml_v8(native,etree.tostring(root),out)
        self.assertEqual(out.read_bytes(),b"Pre-existing research evidence")

    def test_unsafe_DTD_and_XXE_xml_rejected(self):
        _,native,folder,view,root,ids=self.fixture("wall")
        xml=etree.tostring(root,encoding="utf8")
        tampered=(b'<!DOCTYPE Building [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
                  +xml)
        out=folder/"doctype.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v8(native,tampered,out)
        self.assertFalse(out.exists())

    def test_invalid_xml_extra_model_mutation_command_rejected(self):
        _,native,folder,view,root,ids=self.fixture("wall")
        etree.SubElement(root.find(Q+"Elements"),Q+"Create",{"type":"IfcColumn"})
        out=folder/"fake_commands.ifc"
        with self.assertRaises(LegacyV8Error):
            compile_declarative_xml_v8(native,etree.tostring(root),out)
        self.assertFalse(out.exists())

    def test_existing_native_ifc2x3_wall_change_rejected(self):
        _,native,folder,view,root,ids=self.fixture("door")
        wall=next(x for x in root.findall(".//"+Q+"Wall")
                  if x.get("ifcGuid")==SOURCE_SOUTH)
        wall.set("height",str(float(wall.get("height"))+1.))
        out=folder/"edit_existing_wall.ifc"
        with self.assertRaisesRegex(LegacyV8CompileError,"remain unchanged"):
            compile_declarative_xml_v8(native,etree.tostring(root),out)
        self.assertFalse(out.exists())

    def test_original_native_ifc2x3_column_change_rejected(self):
        _,native,folder,view,root,ids=self.fixture("space")
        col=next(iter(root.findall(".//"+Q+"Column")))
        col.set("x",str(float(col.get("x"))+1.))
        out=folder/"edit_existing_column.ifc"
        with self.assertRaisesRegex(LegacyV8CompileError,"remain unchanged"):
            compile_declarative_xml_v8(native,etree.tostring(root),out)
        self.assertFalse(out.exists())

    def test_ifc2x3_cannot_create_space_and_wall_together(self):
        _,native,folder,view,root,ids=self.fixture("space")
        level=next(x for x in root.findall(".//"+Q+"Level")
                   if x.get("placementZ")=="0")
        etree.SubElement(root.find(Q+"Elements"),Q+"Wall",{
            "id":"extra_mixed_wall","level":level.get("id"),
            "x1":"0","y1":"0","z1":"0","x2":"2","y2":"0","z2":"0",
            "height":"3","thickness":".2",
        })
        out=folder/"multiple.ifc"
        with self.assertRaisesRegex(LegacyV8CompileError,"Only one"):
            compile_declarative_xml_v8(native,etree.tostring(root),out)
        self.assertFalse(out.exists())

    def test_ifc4_cannot_create_two_walls_in_one_transaction(self):
        _,native,folder,view,root,ids=self.fixture("wall")
        level=next(iter(root.findall(".//"+Q+"Level")))
        etree.SubElement(root.find(Q+"Elements"),Q+"Wall",{
            "id":"second_new_wall","level":level.get("id"),
            "x1":"0","y1":"0","z1":"0","x2":"2","y2":"0","z2":"0",
            "height":"3","thickness":".2",
        })
        out=folder/"two_walls.ifc"
        with self.assertRaisesRegex(LegacyV8CompileError,"Only one"):
            compile_declarative_xml_v8(native,etree.tostring(root),out)
        self.assertFalse(out.exists())

    def test_ifc2x3_opening_without_Door_must_refuse(self):
        _,native,folder,view,root,ids=self.fixture("door")
        door=next(iter(root.findall(".//"+Q+"Door")))
        root.find(Q+"Elements").remove(door)
        out=folder/"orphan_opening.ifc"
        with self.assertRaisesRegex(LegacyV8CompileError,"Only one"):
            compile_declarative_xml_v8(native,etree.tostring(root),out)
        self.assertFalse(out.exists())

    def test_ifc2x3_Door_filling_missing_opening_rejected(self):
        _,native,folder,view,root,ids=self.fixture("door")
        door=next(iter(root.findall(".//"+Q+"Door")))
        door.set("opening","unknown_original_opening")
        out=folder/"dangling_door.ifc"
        with self.assertRaises(LegacyV8Error):
            compile_declarative_xml_v8(native,etree.tostring(root),out)
        self.assertFalse(out.exists())

    def test_ifc2x3_Door_wrong_original_host_wall_rejected(self):
        _,native,folder,view,root,ids=self.fixture("door")
        wrong=next(x for x in root.findall(".//"+Q+"Wall")
                   if x.get("ifcGuid")==SOURCE_SOUTH)
        opener=next(iter(root.findall(".//"+Q+"Opening")))
        opener.set("host",wrong.get("id"))
        # The source-only independent oracle must reject the wrong host
        # even if this *different* valid physical edit compiles.
        out=folder/"wrong_original_wall.ifc"
        report=compile_declarative_xml_v8(native,etree.tostring(root),out)
        with self.assertRaises(IndependentLegacyV8Error):
            verify_ifc2x3_hosted_door(native,out,
                _det_guid(view.source_sha256,ids[0]),
                _det_guid(view.source_sha256,ids[1]))

    def test_ifc2x3_Door_outside_original_wall_rejected(self):
        _,native,folder,view,root,ids=self.fixture("door")
        opener=next(iter(root.findall(".//"+Q+"Opening")))
        opener.set("offset","6")
        out=folder/"opening_too_far.ifc"
        with self.assertRaisesRegex(LegacyV8CompileError,"outside"):
            compile_declarative_xml_v8(native,etree.tostring(root),out)
        self.assertFalse(out.exists())

    def test_ifc2x3_Door_dims_mismatch_Opening_rejected(self):
        _,native,folder,view,root,ids=self.fixture("door")
        door=next(iter(root.findall(".//"+Q+"Door")))
        door.set("height","3")
        out=folder/"unmatched_dimensions.ifc"
        with self.assertRaisesRegex(LegacyV8CompileError,"dimensions disagree"):
            compile_declarative_xml_v8(native,etree.tostring(root),out)
        self.assertFalse(out.exists())

    def test_independent_native_oracle_rejects_other_original_product_tampering(self):
        for kind in SRC:
            with self.subTest(task=kind):
                _,native,folder,view,root,ids,out,report,guids=self.completed(kind)
                altered=ifcopenshell.open(str(out))
                existing=ifcopenshell.open(str(native)).by_type("IfcBuildingStorey")[0]
                altered.by_guid(existing.GlobalId).Name="CORRUPTED ORIGINAL STOREY NAME"
                broken=folder/"native_tampered.ifc"
                altered.write(str(broken))
                with self.assertRaises(IndependentLegacyV8Error):
                    if kind=="wall":
                        verify_ifc4_wall(native,broken,guids[0])
                    elif kind=="space":
                        verify_ifc2x3_space(native,broken,guids[0])
                    else:
                        verify_ifc2x3_hosted_door(native,broken,guids[0],guids[1])

    def test_original_source_schema_cannot_be_relabelled_by_previous_v07(self):
        from src.runtime.experimental_v7_projection import project_ifc_v7,V7CompatError
        for kind in SRC:
            with self.subTest(case=kind):
                _,native,folder,view,root=self.original(kind)
                with self.assertRaises(V7CompatError):
                    project_ifc_v7(native)


if __name__=="__main__":
    unittest.main()
