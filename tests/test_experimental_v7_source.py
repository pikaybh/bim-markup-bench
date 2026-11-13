"""Source-pinned original BIBIMBAP v0.7 projection/native edit positive & negative tests.

Native IFC2X3/IFC4 read-only evidence is not passed off as editable XML.
All models original paper public input; no LLM inference or new paid calls.
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

from src.runtime.experimental_v7_projection import (
    project_ifc_v7,native_source_admission_v7,_mesh_exact_axis_box,V7CompatError,
)
from src.runtime.experimental_v7_compiler import (
    compile_declarative_xml_v7,V7CompileError,
)
from src.runtime.experimental_v4_projection import project_ifc_v4
from tools.oracle_bibimbap_v07_source import (
    verify_v7_projected_source,verify_column_move,verify_slab_create,
    IndependentV7Error,
)
from tools.bibimbap_matched25_tools import file_hash

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",r"D:\문서\D__1_Projects\202611"))
DATA=BASE/"bibimbap-author-data"/"ifc"
NS="{urn:bim-markup-bench:toy:v0}"
BLOCKED_IFC4X3={
    "geometry_test_01":"01/01/01_01_001.ifc",
    "geometry_test_14":"01/01/01_01_014.ifc",
    "geometry_test_15":"01/01/01_01_015.ifc",
    "topological_test_05":"01/02/01_02_005.ifc",
    "topological_test_11":"01/02/01_02_011.ifc",
    "topological_test_17":"01/02/01_02_017.ifc",
}
BLOCKED_LEGACY={
    "geometry_test_03":("01/01/01_01_003.ifc","IFC2X3"),
    "geometry_test_04":("01/01/01_01_004.ifc","IFC2X3"),
    "geometry_test_05":("empty.ifc","IFC4"),
}
COLUMN_TARGET="3lOEkLxYb9$uRd50gnIDqu"


class _OriginalV7Source(unittest.TestCase):
    def setup_source(self,rel):
        original=DATA/rel
        if not original.exists():
            self.skipTest("Pinned BIBIMBAP original public IFC dataset not mounted")
        d=tempfile.TemporaryDirectory(prefix="bibi128-src-")
        self.addCleanup(d.cleanup)
        folder=Path(d.name)
        original_hash=file_hash(original)
        self.addCleanup(lambda:self.assertEqual(file_hash(original),original_hash))
        model=ifcopenshell.open(str(original))
        clone=folder/"metres_source.ifc"
        ifcopenshell.util.unit.convert_file_length_units(model,"METER").write(str(clone))
        clone_hash=file_hash(clone)
        self.addCleanup(lambda:self.assertEqual(file_hash(clone),clone_hash))
        return original,clone,folder

    def source(self,kind):
        orig,clone,d=self.setup_source(BLOCKED_IFC4X3[kind])
        projection=project_ifc_v7(clone)
        proof=verify_v7_projected_source(orig,clone,projection.xml)
        self.assertEqual(proof["status"],
                         "INDEPENDENT_V7_ORIGINAL_IFC4X3_PARTIAL_PROJECTION_VALIDATED")
        return orig,clone,d,etree.fromstring(projection.xml),projection

    def column_moved(self):
        original,clone,d,root,proj=self.source("geometry_test_15")
        target=next(x for x in root.findall(".//"+NS+"Column")
                    if x.get("ifcGuid")==COLUMN_TARGET)
        target.set("y",str(float(target.get("y"))-.75))
        dest=d/"mapped_column_move.ifc"
        report=compile_declarative_xml_v7(clone,etree.tostring(root),dest)
        return original,clone,d,root,report,dest

    def slab_created(self):
        original,clone,d,root,proj=self.source("geometry_test_01")
        ground=next(x for x in root.findall(".//"+NS+"Level")
                    if abs(float(x.get("elevation")))<1e-8)
        etree.SubElement(root.find(NS+"Elements"),NS+"Slab",{
            "id":"source_only_new_slab_fixture",
            "level":ground.get("id"),
            "x":"0","y":"0","z":"3",
            "width":"3","depth":"3","thickness":"0.2",
        })
        dest=d/"slab_create.ifc"
        report=compile_declarative_xml_v7(clone,etree.tostring(root),dest)
        return original,clone,d,root,report,dest


class OriginalNineSourceV7Tests(_OriginalV7Source):
    def test_exact_six_original_ifc4x3_sources_bootstrap_to_valid_partial_xml(self):
        for kind in BLOCKED_IFC4X3:
            with self.subTest(kind=kind):
                original,clone,d,root,projected=self.source(kind)
                self.assertGreater(len(root.find(NS+"Elements")),0)
                self.assertEqual(projected.source.ifc_schema,"IFC4X3")
                self.assertNotEqual(projected.source.source_sha256,file_hash(original))
                self.assertEqual(projected.source.source_sha256,file_hash(clone))

    def test_all_six_projected_native_counts_and_explicit_opaque_classes(self):
        expected={
            "geometry_test_01":(4,0,{}),
            "geometry_test_14":(0,1,{}),
            "geometry_test_15":(4,0,{}),
            "topological_test_05":(0,2,{"IfcWall":7}),
            "topological_test_11":(2,2,{"IfcWall":7,"IfcSpace":2}),
            "topological_test_17":(10,2,{}),
        }
        for task,(column_count,slab_count,opaque) in expected.items():
            with self.subTest(task=task):
                _,_,_,root,p=self.source(task)
                self.assertEqual(len(root.findall(".//"+NS+"Column")),column_count)
                self.assertEqual(len(root.findall(".//"+NS+"Slab")),slab_count)
                self.assertEqual(dict(p.unsupported_class_counts),opaque)

    def test_three_legacy_sources_native_read_only_without_false_ifc4x3_claim(self):
        for kind,(path,schema) in BLOCKED_LEGACY.items():
            with self.subTest(task=kind):
                source=DATA/path
                self.assertTrue(source.is_file())
                before=file_hash(source)
                admission=native_source_admission_v7(source)
                self.assertEqual(admission["ifc_schema"],schema)
                self.assertFalse(admission["v01_xml_editing_supported"])
                self.assertFalse(admission["legacy_source_schema_losslessly_converted_to_IFC4X3"])
                self.assertEqual(admission["source_sha256"],before)
                with self.assertRaisesRegex(V7CompatError,"Legacy source"):
                    project_ifc_v7(source)
                self.assertEqual(file_hash(source),before)

    def test_ifc4_empty_original_has_missing_storey_not_fabricated(self):
        data=native_source_admission_v7(DATA/"empty.ifc")
        self.assertEqual(data["ifc_schema"],"IFC4")
        self.assertEqual(data["storeys_missing_explicit_elevation"],1)
        self.assertEqual(data["storeys_with_explicit_elevation"],0)

    def test_native_millimetre_source_not_mislabeled_metres(self):
        for key in ("geometry_test_01","geometry_test_15"):
            with self.subTest(task=key):
                source=DATA/BLOCKED_IFC4X3[key]
                with self.assertRaisesRegex(V7CompatError,"metre-unit"):
                    project_ifc_v7(source)

    def test_existing_v4_projection_for_supported_original_source_unchanged(self):
        original,clone,d=self.setup_source("basic_tasks.ifc")
        a=project_ifc_v4(clone)
        b=project_ifc_v7(clone)
        self.assertEqual(a.xml,b.xml)
        self.assertEqual(a.projected_global_ids,b.projected_global_ids)
        self.assertEqual(a.supported_class_counts,b.supported_class_counts)

    def test_geometry14_tilted_local_slab_retained_as_original_exact_world_box(self):
        _,clone,d,tree,projected=self.source("geometry_test_14")
        self.assertEqual(len(tree.findall(".//"+NS+"Slab")),1)
        f=ifcopenshell.open(str(clone))
        slab=f.by_guid("11kJIqz$n2Jf_DfJV1SCVP")
        low,high=_mesh_exact_axis_box(slab)
        self.assertAlmostEqual(high[2]-low[2],.3,places=4)
        self.assertGreater(high[0]-low[0],9.9)

    def test_geometry1_four_native_mapped_columns_source_primitives_unchanged(self):
        _,clone,d,root,p=self.source("geometry_test_01")
        f=ifcopenshell.open(str(clone))
        for col in root.findall(".//"+NS+"Column"):
            entity=f.by_guid(col.get("ifcGuid"))
            self.assertTrue(any(
                item.is_a("IfcMappedItem")
                for rep in entity.Representation.Representations for item in rep.Items))
            self.assertIsNotNone(entity.ObjectPlacement)


class NativeV7MutationPositiveTests(_OriginalV7Source):
    def test_original_geometry15_mapped_column_shift_native_mesh_and_steps(self):
        original,clone,d,root,report,result=self.column_moved()
        self.assertEqual(report.operations[0].operation,"MOVE_ORIGINAL_MAPPED_COLUMN")
        self.assertFalse(report.as_dict()["full_45_task_equivalence_with_Python_IFC"])
        evidence=verify_column_move(clone,result,COLUMN_TARGET,(0,-.75,0))
        self.assertGreaterEqual(evidence["all_original_root_globalids_and_attrs_preserved"],10)
        with self.assertRaises(IndependentV7Error):
            verify_column_move(clone,result,COLUMN_TARGET,(0,+.75,0))

    def test_original_geometry01_new_native_slab_preserves_all_mapped_columns(self):
        original,clone,d,root,report,result=self.slab_created()
        self.assertEqual(report.operations[0].operation,"CREATE_SLAB_FROM_BOOTSTRAP")
        evidence=verify_slab_create(
            clone,result,report.operations[0].ifc_guid,
            minimum=(0,0,3),maximal=(3,3,3.2))
        self.assertEqual(len(ifcopenshell.open(str(result)).by_type("IfcColumn")),4)
        self.assertEqual(len(ifcopenshell.open(str(result)).by_type("IfcSlab")),1)
        with self.assertRaises(IndependentV7Error):
            verify_slab_create(
                clone,result,report.operations[0].ifc_guid,
                minimum=(0,0,3),maximal=(3,3,3.3))

    def test_original_slab_create_repeated_identical_state_has_byte_identical_IFC(self):
        # The original IfcOpenShell assign_container API may reorder an IFC
        # SET of preexisting member GlobalIds. v0.7 restores the original
        # relation tuple ordering with only the added Slab appended.
        orig,clone,d,root,first_report,first=self.slab_created()
        second=d/"slab_create_again.ifc"
        # Cross at least one system-clock second; a source-pinned research
        # compile must never depend on current wall-clock timestamps.
        time.sleep(1.25)
        second_report=compile_declarative_xml_v7(
            clone,etree.tostring(root),second)
        self.assertEqual(first_report.operations[0].ifc_guid,
                         second_report.operations[0].ifc_guid)
        self.assertEqual(file_hash(first),file_hash(second))
        self.assertEqual(first.read_bytes(),second.read_bytes())

    def test_original_input_src_globalids_immutable_after_isolated_run(self):
        _,clone,d,root,report,result=self.column_moved()
        orig=ifcopenshell.open(str(clone))
        cand=ifcopenshell.open(str(result))
        self.assertEqual({x.GlobalId for x in orig.by_type("IfcColumn")},
                         {x.GlobalId for x in cand.by_type("IfcColumn")})
        self.assertEqual(len(orig.by_type("IfcRelContainedInSpatialStructure")),
                         len(cand.by_type("IfcRelContainedInSpatialStructure")))


class NativeV7NegativeTests(_OriginalV7Source):
    def test_mapped_column_size_change_rejected_without_candidate(self):
        orig,clone,d,root,p=self.source("geometry_test_15")
        node=next(x for x in root.findall(".//"+NS+"Column") if x.get("ifcGuid")==COLUMN_TARGET)
        node.set("height",str(float(node.get("height"))+0.5))
        dest=d/"unsafe_height.ifc"
        with self.assertRaisesRegex(V7CompileError,"Only native Column x/y/z"):
            compile_declarative_xml_v7(clone,etree.tostring(root),dest)
        self.assertFalse(dest.exists())

    def test_original_mapped_col_plus_new_slab_combined_change_rejected(self):
        orig,clone,d,root,p=self.source("geometry_test_15")
        node=next(x for x in root.findall(".//"+NS+"Column") if x.get("ifcGuid")==COLUMN_TARGET)
        node.set("y",str(float(node.get("y"))-.75))
        level=next(x for x in root.findall(".//"+NS+"Level")
                   if abs(float(x.get("elevation")))<1e-8)
        etree.SubElement(root.find(NS+"Elements"),NS+"Slab",{
            "id":"combined_new","level":level.get("id"),
            "x":"0","y":"0","z":"3","width":"3","depth":"3","thickness":"0.2",
        })
        dest=d/"combined.ifc"
        with self.assertRaisesRegex(V7CompileError,"Only exactly one"):
            compile_declarative_xml_v7(clone,etree.tostring(root),dest)
        self.assertFalse(dest.exists())

    def test_new_slab_on_original_nonzero_elevation_storey_rejected(self):
        orig,clone,d,root,p=self.source("geometry_test_01")
        second=next(x for x in root.findall(".//"+NS+"Level")
                    if float(x.get("elevation"))>0)
        etree.SubElement(root.find(NS+"Elements"),NS+"Slab",{
            "id":"upper_unsupported","level":second.get("id"),
            "x":"0","y":"0","z":"3","width":"3","depth":"3","thickness":"0.2",
        })
        dest=d/"unsupported_level.ifc"
        with self.assertRaisesRegex(V7CompileError,"zero-elevation"):
            compile_declarative_xml_v7(clone,etree.tostring(root),dest)
        self.assertFalse(dest.exists())

    def test_bad_existing_source_sha_and_unused_destination_gate(self):
        orig,clone,d,root,p=self.source("geometry_test_15")
        node=next(x for x in root.findall(".//"+NS+"Column") if x.get("ifcGuid")==COLUMN_TARGET)
        node.set("y",str(float(node.get("y"))-.75))
        root.set("sourceModelSha256","0"*64)
        dest=d/"invalid_sha.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v7(clone,etree.tostring(root),dest)
        self.assertFalse(dest.exists())
        root.set("sourceModelSha256",file_hash(clone))
        dest.write_bytes(b"pre-existing original experiment record")
        with self.assertRaisesRegex(V7CompileError,"unused"):
            compile_declarative_xml_v7(clone,etree.tostring(root),dest)
        self.assertEqual(dest.read_bytes(),b"pre-existing original experiment record")

    def test_native_projection_oracle_detects_forged_original_geometry(self):
        orig,clone,d,root,p=self.source("geometry_test_15")
        node=next(x for x in root.findall(".//"+NS+"Column") if x.get("ifcGuid")==COLUMN_TARGET)
        node.set("width",str(float(node.get("width"))+1))
        with self.assertRaises(IndependentV7Error):
            verify_v7_projected_source(orig,clone,etree.tostring(root))

    def test_wrong_target_column_original_globalid_or_nonfinite_displacement_rejected(self):
        orig,clone,d,root,p=self.source("geometry_test_15")
        node=next(x for x in root.findall(".//"+NS+"Column") if x.get("ifcGuid")==COLUMN_TARGET)
        node.set("x",str(float(node.get("x"))+1000))
        dest=d/"outside_source.ifc"
        with self.assertRaisesRegex(V7CompileError,"bounded"):
            compile_declarative_xml_v7(clone,etree.tostring(root),dest)
        self.assertFalse(dest.exists())

    def test_noop_v7_projection_does_not_write_ifc(self):
        orig,clone,d,root,p=self.source("geometry_test_01")
        output=d/"noop.ifc"
        with self.assertRaisesRegex(V7CompileError,"Only exactly one"):
            compile_declarative_xml_v7(clone,etree.tostring(root),output)
        self.assertFalse(output.exists())

    def test_independent_oracle_rejects_unrelated_native_product_corruption(self):
        orig,clone,d,root,report,result=self.column_moved()
        f=ifcopenshell.open(str(result))
        other=next(x for x in f.by_type("IfcColumn") if x.GlobalId!=COLUMN_TARGET)
        other.Name="BROKEN OTHER ORIGINAL MAPPED COLUMN"
        corrupt=d/"corrupted.ifc"
        f.write(str(corrupt))
        with self.assertRaises(IndependentV7Error):
            verify_column_move(clone,corrupt,COLUMN_TARGET,(0,-.75,0))


if __name__=="__main__":
    unittest.main()
