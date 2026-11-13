"""Original public BIBIMBAP IFC4X3 v0.9 complex native positive/negative tests.

Never invokes an LLM, hidden target IFC or original author scorer.
Independent oracle imports NO compiler/binder/projection/GT.
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

from src.runtime.experimental_v9_projection import (
    project_ifc_v9,ComplexV9ProjectionError,
)
from src.runtime.experimental_v7_projection import project_ifc_v7
from src.runtime.experimental_v9_complex_compiler import (
    compile_declarative_xml_v9,ComplexV9Error,
)
from src.runtime.markup_normal_form import NS
from src.runtime.semantic_graph import BindingError
from tools.oracle_bibimbap_v09_native import (
    verify_v09_rotated_slab_square,
    verify_v09_shared_columns_touch_slab,
    verify_v09_boolean_host_door,
    IndependentComplexV9Error,
)
from tools.bibimbap_matched25_tools import file_hash

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",r"D:\문서\D__1_Projects\202611"))
DATA=BASE/"bibimbap-author-data"/"ifc"
Q="{"+NS+"}"
CASES={
    "slab":"01/01/01_01_014.ifc",
    "columns":"01/02/01_02_011.ifc",
    "door":"01/02/01_02_005.ifc",
}
SOURCE_BOOLEAN_SOUTH="3Vyqk8cSj8TOuAk6zHUwAc"
SOURCE_SECOND_WALL="3Vyqk8cSj8TOuAk6zHUwNQ"
PUBLIC_UPPER_SLAB="0dxtXCDSn2mfP92h$AiPMM"
SLAB_ORIGINAL_GUID="11kJIqz$n2Jf_DfJV1SCVP"
SHARED_COLUMN_GUIDS={
    "0n4qMSuxfEFA0BeEfapSQB","0n4qMSuxfEFA0BeEfapSHZ",
}


class OriginalV9Native(unittest.TestCase):
    def source(self,kind):
        original=DATA/CASES[kind]
        if not original.exists():
            self.skipTest("Original pinned public IFC not mounted")
        temp=tempfile.TemporaryDirectory(prefix="bibi132-v09-native-")
        self.addCleanup(temp.cleanup)
        folder=Path(temp.name)
        original_hash=file_hash(original)
        self.addCleanup(lambda:self.assertEqual(file_hash(original),original_hash))
        f=ifcopenshell.open(str(original))
        normalized=folder/"original_source_metres.ifc"
        if abs(ifcopenshell.util.unit.calculate_unit_scale(f)-.001)>1e-12:
            self.skipTest("Source unit not the original millimetre model")
        ifcopenshell.util.unit.convert_file_length_units(
            f,"METER").write(str(normalized))
        source_hash=file_hash(normalized)
        self.addCleanup(lambda:self.assertEqual(file_hash(normalized),source_hash))
        view=project_ifc_v9(normalized)
        root=etree.fromstring(view.xml)
        return original,normalized,folder,view,root

    def fixture(self,kind):
        original,normalized,d,view,root=self.source(kind)
        elements=root.find(Q+"Elements")
        if kind=="slab":
            sls=root.findall("./"+Q+"Elements/"+Q+"Slab")
            self.assertEqual(len(sls),1)
            sls[0].set("depth",sls[0].get("width"))
        elif kind=="columns":
            columns=root.findall("./"+Q+"Elements/"+Q+"Column")
            self.assertEqual({x.get("ifcGuid") for x in columns},
                             SHARED_COLUMN_GUIDS)
            for column in columns:column.set("height","2.7")
        elif kind=="door":
            host=next(x for x in root.findall("./"+Q+"Elements/"+Q+"Wall")
                      if x.get("ifcGuid")==SOURCE_BOOLEAN_SOUTH)
            opening=etree.SubElement(elements,Q+"Opening",{
                "id":"original_source_topo05_south_opening",
                "host":host.get("id"),"offset":"2.8","sill":"0",
                "width":"1","height":"2.1",
            })
            etree.SubElement(elements,Q+"Door",{
                "id":"original_source_topo05_south_door",
                "opening":opening.get("id"),"width":"1","height":"2.1",
            })
        return original,normalized,d,view,root

    def completed(self,kind):
        original,normalized,d,view,root=self.fixture(kind)
        output=d/"native_result.ifc"
        report=compile_declarative_xml_v9(
            normalized,etree.tostring(root,encoding="utf8"),output)
        return original,normalized,d,view,root,report,output


class NativePositiveV9(OriginalV9Native):
    def test_previous_v07_source_projection_is_byte_identical_when_no_clipping_walls(self):
        for kind in ("slab","columns"):
            with self.subTest(case=kind):
                orig,src,d,view,root=self.source(kind)
                original_projection=project_ifc_v7(src)
                if kind=="slab":
                    self.assertEqual(view.xml,original_projection.xml)
                else:
                    self.assertEqual(len(root.findall(".//"+Q+"Wall")),7)
                    self.assertEqual(len(original_projection.xml)!=len(view.xml),True)

    def test_boolean_native_seven_walls_projected_without_rebuilding_original_step(self):
        orig,src,d,view,root=self.source("door")
        self.assertEqual(len(root.findall(".//"+Q+"Wall")),7)
        self.assertEqual(len(root.findall(".//"+Q+"Slab")),2)
        self.assertEqual(len(root.findall(".//"+Q+"Door")),0)
        self.assertEqual(dict(view.unsupported_class_counts),{})
        f=ifcopenshell.open(str(src))
        for x in root.findall(".//"+Q+"Wall"):
            wall=f.by_guid(x.get("ifcGuid"))
            bodies=[rep for rep in wall.Representation.Representations
                    if rep.RepresentationType=="Clipping"]
            self.assertEqual(len(bodies),1)
            self.assertTrue(bodies[0].Items[0].is_a("IfcBooleanClippingResult"))

    def test_original_slabs_local_profile_square_preserves_original_anchored_world_corner(self):
        orig,src,d,view,root,report,out=self.completed("slab")
        self.assertEqual(report.operations[0].operation,
                         "RESHAPE_LOCAL_ROTATED_SLAB_SQUARE")
        native=verify_v09_rotated_slab_square(
            src,out,SLAB_ORIGINAL_GUID)
        self.assertAlmostEqual(native["result_native_slab_volume_cubic_m"],30,places=3)
        self.assertFalse(report.as_dict()["backend_original_45_task_full_parity"])

    def test_two_original_columns_same_source_type_extend_to_original_named_slab(self):
        orig,src,d,view,root,report,out=self.completed("columns")
        self.assertEqual(report.operations[0].operation,
                         "UPDATE_SHARED_NATIVE_MAPPED_COLUMNS_HEIGHT")
        native=verify_v09_shared_columns_touch_slab(
            src,out,SHARED_COLUMN_GUIDS,PUBLIC_UPPER_SLAB)
        self.assertEqual(set(native["source_column_guids"]),SHARED_COLUMN_GUIDS)
        self.assertGreater(native["original_native_slab_underside_m"],2.69)

    def test_native_boolean_wall_hosted_opening_door_physical_voxel_and_connected_rels(self):
        orig,src,d,view,root,report,out=self.completed("door")
        candidate=ifcopenshell.open(str(out))
        op=candidate.by_type("IfcOpeningElement")
        door=candidate.by_type("IfcDoor")
        self.assertEqual((len(op),len(door)),(1,1))
        self.assertEqual(report.operations[0].operation,
                         "CREATE_BOOLEAN_CLIPPING_HOSTED_DOOR")
        native=verify_v09_boolean_host_door(
            src,out,SOURCE_BOOLEAN_SOUTH,op[0].GlobalId,door[0].GlobalId)
        self.assertAlmostEqual(native["actual_Wall_volume_removed_cubic_m"],.42,places=3)
        self.assertGreater(native["original_source_wall_connections_preserved"],0)

    def test_repeated_complete_xml_same_native_result_sha_after_clock_interval(self):
        for kind in CASES:
            with self.subTest(case=kind):
                orig,src,d,view,root=self.fixture(kind)
                xml=etree.tostring(root)
                first=d/"first.ifc"
                second=d/"second.ifc"
                compile_declarative_xml_v9(src,xml,first)
                time.sleep(1.10)
                compile_declarative_xml_v9(src,xml,second)
                self.assertEqual(file_hash(first),file_hash(second))
                self.assertEqual(first.read_bytes(),second.read_bytes())


class NativeNegativeV9(OriginalV9Native):
    def test_original_source_millimetres_must_not_be_relabelled_metres(self):
        for kind in CASES:
            with self.subTest(case=kind):
                raw=DATA/CASES[kind]
                with self.assertRaises(Exception):
                    project_ifc_v9(raw)

    def test_unchanged_source_full_declarative_xml_refuses_noop(self):
        orig,src,d,view,root=self.source("columns")
        output=d/"noop.ifc"
        with self.assertRaisesRegex(ComplexV9Error,"Exactly one"):
            compile_declarative_xml_v9(src,etree.tostring(root),output)
        self.assertFalse(output.exists())

    def test_edited_declarative_document_wrong_original_hash_refused(self):
        orig,src,d,view,root=self.fixture("door")
        root.set("sourceModelSha256","0"*64)
        output=d/"wrong_hash.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v9(src,etree.tostring(root),output)
        self.assertFalse(output.exists())

    def test_existing_research_evidence_output_cannot_be_overwritten(self):
        orig,src,d,view,root=self.fixture("slab")
        output=d/"existing.ifc"
        output.write_bytes(b"Immutable research result")
        with self.assertRaisesRegex(ComplexV9Error,"unused"):
            compile_declarative_xml_v9(src,etree.tostring(root),output)
        self.assertEqual(output.read_bytes(),b"Immutable research result")

    def test_original_slab_cannot_edit_thickness_or_move_with_square(self):
        orig,src,d,view,root=self.fixture("slab")
        slab=next(iter(root.findall(".//"+Q+"Slab")))
        slab.set("thickness","0.4")
        output=d/"unsupported.ifc"
        with self.assertRaisesRegex(ComplexV9Error,"only changes world depth"):
            compile_declarative_xml_v9(src,etree.tostring(root),output)
        self.assertFalse(output.exists())

    def test_original_slab_width_cannot_shrink_to_fabricate_square(self):
        orig,src,d,view,root=self.source("slab")
        slab=next(iter(root.findall(".//"+Q+"Slab")))
        slab.set("width","8.5")
        output=d/"bad_square.ifc"
        with self.assertRaises(ComplexV9Error):
            compile_declarative_xml_v9(src,etree.tostring(root),output)
        self.assertFalse(output.exists())

    def test_slab_world_y_shrink_or_wrong_square_target_rejected(self):
        orig,src,d,view,root=self.source("slab")
        slab=next(iter(root.findall(".//"+Q+"Slab")))
        slab.set("depth","9.5")
        output=d/"not_square.ifc"
        with self.assertRaisesRegex(ComplexV9Error,"exact square"):
            compile_declarative_xml_v9(src,etree.tostring(root),output)
        self.assertFalse(output.exists())

    def test_only_one_of_shared_columns_cannot_change_height(self):
        orig,src,d,view,root=self.source("columns")
        col=next(iter(root.findall(".//"+Q+"Column")))
        col.set("height","2.7")
        output=d/"half_shared.ifc"
        with self.assertRaises(ComplexV9Error):
            compile_declarative_xml_v9(src,etree.tostring(root),output)
        self.assertFalse(output.exists())

    def test_mapped_columns_both_wrong_slab_contact_height_rejected(self):
        orig,src,d,view,root=self.source("columns")
        for col in root.findall(".//"+Q+"Column"):
            col.set("height","2.6")
        output=d/"no_slab_contact.ifc"
        with self.assertRaises(ComplexV9Error):
            compile_declarative_xml_v9(src,etree.tostring(root),output)
        self.assertFalse(output.exists())

    def test_mapped_columns_cannot_be_moved_while_height_changed(self):
        orig,src,d,view,root=self.fixture("columns")
        col=next(iter(root.findall(".//"+Q+"Column")))
        col.set("x",str(float(col.get("x"))+.1))
        output=d/"height_move_combo.ifc"
        with self.assertRaisesRegex(ComplexV9Error,"Only both"):
            compile_declarative_xml_v9(src,etree.tostring(root),output)
        self.assertFalse(output.exists())

    def test_hosted_new_Opening_without_new_Door_refused(self):
        orig,src,d,view,root=self.fixture("door")
        door=next(iter(root.findall(".//"+Q+"Door")))
        root.find(Q+"Elements").remove(door)
        output=d/"opening_without_filling.ifc"
        with self.assertRaisesRegex(ComplexV9Error,r"Door\+Opening"):
            compile_declarative_xml_v9(src,etree.tostring(root),output)
        self.assertFalse(output.exists())

    def test_new_door_unknown_opening_wrong_reference_rejected(self):
        orig,src,d,view,root=self.fixture("door")
        door=next(iter(root.findall(".//"+Q+"Door")))
        door.set("opening","not_an_original_opening")
        output=d/"bad_ref.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v9(src,etree.tostring(root),output)
        self.assertFalse(output.exists())

    def test_original_boolean_host_new_door_overlaps_wall_junction_rejected(self):
        orig,src,d,view,root=self.fixture("door")
        op=next(iter(root.findall(".//"+Q+"Opening")))
        op.set("offset",".01")
        output=d/"door_touches_corner.ifc"
        with self.assertRaisesRegex(ComplexV9Error,"safe interior"):
            compile_declarative_xml_v9(src,etree.tostring(root),output)
        self.assertFalse(output.exists())

    def test_original_boolean_host_op_overshoots_wall_rejected(self):
        orig,src,d,view,root=self.fixture("door")
        op=next(iter(root.findall(".//"+Q+"Opening")))
        op.set("offset","100")
        output=d/"door_beyond_wall.ifc"
        with self.assertRaises((ComplexV9Error,BindingError)):
            compile_declarative_xml_v9(src,etree.tostring(root),output)
        self.assertFalse(output.exists())

    def test_native_opening_and_filling_wrong_dimensions_rejected(self):
        orig,src,d,view,root=self.fixture("door")
        door=next(iter(root.findall(".//"+Q+"Door")))
        door.set("width",".9")
        output=d/"door_wrong_width.ifc"
        with self.assertRaisesRegex(ComplexV9Error,"disagree"):
            compile_declarative_xml_v9(src,etree.tostring(root),output)
        self.assertFalse(output.exists())

    def test_cannot_mutate_original_Boolean_Wall_while_hosting_Door(self):
        orig,src,d,view,root=self.fixture("door")
        host=next(x for x in root.findall(".//"+Q+"Wall")
                  if x.get("ifcGuid")==SOURCE_BOOLEAN_SOUTH)
        host.set("height","2.8")
        output=d/"wall_mutation_hosted.ifc"
        with self.assertRaises(ComplexV9Error):
            compile_declarative_xml_v9(src,etree.tostring(root),output)
        self.assertFalse(output.exists())

    def test_cannot_create_Door_while_resizing_Slab(self):
        orig,src,d,view,root=self.fixture("door")
        slab=next(iter(root.findall(".//"+Q+"Slab")))
        slab.set("thickness","0.4")
        output=d/"multi_change.ifc"
        with self.assertRaisesRegex(ComplexV9Error,"combined"):
            compile_declarative_xml_v9(src,etree.tostring(root),output)
        self.assertFalse(output.exists())

    def test_independent_oracle_detects_original_unrelated_wall_tampering(self):
        orig,src,d,view,root,report,out=self.completed("door")
        candidate=ifcopenshell.open(str(out))
        new_opening=candidate.by_type("IfcOpeningElement")[0]
        new_door=candidate.by_type("IfcDoor")[0]
        survivor=next(w for w in candidate.by_type("IfcWall")
                      if w.GlobalId!=SOURCE_BOOLEAN_SOUTH)
        survivor.Name="CORRUPTED ORIGINAL WALL NAME"
        corrupted=d/"tampered.ifc"
        candidate.write(str(corrupted))
        with self.assertRaises(IndependentComplexV9Error):
            verify_v09_boolean_host_door(
                src,corrupted,SOURCE_BOOLEAN_SOUTH,
                new_opening.GlobalId,new_door.GlobalId)

    def test_independent_oracle_wrong_slab_guid_and_square_geometry_refused(self):
        orig,src,d,view,root,report,out=self.completed("slab")
        with self.assertRaises(IndependentComplexV9Error):
            verify_v09_rotated_slab_square(
                src,out,"0dxtXCDSn2mfP92h$AiPMM")

    def test_independent_oracle_wrong_mapped_slab_relation_refused(self):
        orig,src,d,view,root,report,out=self.completed("columns")
        other=next(x for x in ifcopenshell.open(str(src)).by_type("IfcSlab")
                   if x.GlobalId!=PUBLIC_UPPER_SLAB)
        with self.assertRaises(IndependentComplexV9Error):
            verify_v09_shared_columns_touch_slab(
                src,out,SHARED_COLUMN_GUIDS,other.GlobalId)

    def test_independent_oracle_wrong_original_boolean_host_refused(self):
        orig,src,d,view,root,report,out=self.completed("door")
        candidate=ifcopenshell.open(str(out))
        new_op=candidate.by_type("IfcOpeningElement")[0]
        new_door=candidate.by_type("IfcDoor")[0]
        with self.assertRaises(IndependentComplexV9Error):
            verify_v09_boolean_host_door(
                src,out,SOURCE_SECOND_WALL,new_op.GlobalId,new_door.GlobalId)


if __name__=="__main__":
    unittest.main()
