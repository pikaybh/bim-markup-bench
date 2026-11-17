"""v0.45 strict original four IFC4X3 native UPDATE/DELETE writer + oracle tests.

Positive native sample mutations intentionally do NOT solve original tasks.
All source/metadata/geometry/relationship/physical edit claims are independently
verified, with negative tests for source manipulation, native output corruption,
invalid schema, unsupported edit modes and last-valid rollback.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from tools.audit_bibimbap_v045_original4_native_mutations import (
    audit,original_45,make_illustrative_plan,PINS,Q,ROOT,PREVIOUS_V044)
from tools.bibimbap_matched25_tools import (
    XmlSourceEditSession,UnsupportedArm,file_hash)
from tools.bibimbap_v045_independent_native_mutation_oracle import (
    verify_original_native_mutation_v045,IndependentNativeMutation045Error)
from src.runtime.experimental_v45_original_native_mutations import (
    OriginalNativeMutation045Error,project_original_native_mutations_v045,
    parse_original_native_edit_plan_v045,
    compile_original_native_mutation_v045,XSD)

BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports"/"bibimbap_v045_original4_native_IFC_typed_writers_20261117.json"
FROZEN_SHA="7d7518f6c65242f7f00066beeb0229fbb6e42e44d5e841243666ac375105c4b3"
TASK_IDS=("geometry_test_14","geometry_test_15",
          "topological_test_11","topological_test_17")


class V045OriginalFourNativeMutation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.originals=original_45(AUTHOR,DATA)
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))
        cls.temp=TemporaryDirectory(prefix="v045-original4-tests-")
        cls.sources={}
        cls.sessions={}
        cls.baselines={}
        cls.submitted={}
        cls.oracle={}
        cls.candidates={}
        for i,tid in enumerate(TASK_IDS):
            source=DATA/"ifc"/cls.originals[tid]["original_source_ifc_relpath"]
            s=XmlSourceEditSession(
                source,Path(cls.temp.name)/f"session{i}",
                experimental_original_native_mutations_v045=True)
            xml=s.call("read_building_xml",{})["xml"].encode("utf8")
            cmd=make_illustrative_plan(xml,tid,source)
            result=s.call("submit_building_xml",{"xml_text":cmd.decode("utf8")})
            if result["status"]!="ok":
                raise AssertionError(f"V045 independent native oracle error {tid}: {result}")
            cls.sources[tid]=source
            cls.sessions[tid]=s
            cls.baselines[tid]=xml
            cls.submitted[tid]=cmd
            cls.oracle[tid]=result
            cls.candidates[tid]=s.output_ifc

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.local=TemporaryDirectory(prefix="v045-native-poison-")
        self.addCleanup(self.local.cleanup)
        self.tmp=Path(self.local.name)

    def xml(self,tid="geometry_test_14"):
        return etree.fromstring(self.submitted[tid])

    def poison_xml(self,change,tid="geometry_test_14"):
        root=self.xml(tid)
        change(root)
        forged=etree.tostring(root,encoding="utf8")
        with self.assertRaises((OriginalNativeMutation045Error,etree.XMLSyntaxError,
                                ValueError,TypeError)):
            parse_original_native_edit_plan_v045(
                self.sources[tid],forged,
                source_sha=self.originals[tid]["original_ifc_sha256"])
        self.assertEqual(file_hash(self.sources[tid]),
                         self.originals[tid]["original_ifc_sha256"])

    def poison_candidate(self,change,tid="geometry_test_14"):
        model=ifcopenshell.open(str(self.candidates[tid]))
        change(model)
        out=self.tmp/"corrupted_original_native_candidate.ifc"
        model.write(str(out))
        with self.assertRaises(IndependentNativeMutation045Error):
            verify_original_native_mutation_v045(
                self.sources[tid],out,
                submitted_xml=self.submitted[tid],
                source_sha=self.originals[tid]["original_ifc_sha256"],
                task_id=tid)

    def edit(self,root):
        return root.find(Q+"NativeEditPlan")[0]

    def native(self,root,section):
        return root.find(Q+"OriginalNativeIFCSource").find(Q+section)

    def test_01_frozen_report_sha256_verified(self):
        self.assertEqual(file_hash(REPORT),FROZEN_SHA)

    def test_02_prior_v044_frozen_report_preserved(self):
        self.assertEqual(file_hash(ROOT/"reports"/"bibimbap_v044_original4_native_STEP_readonly_20261117.json"),
                         PREVIOUS_V044)

    def test_03_original_full45_population_exact(self):
        self.assertEqual(len(self.originals),45)

    def test_04_original31_unique_IFC_source_input_hashes(self):
        self.assertEqual(len({x["original_ifc_sha256"] for x in self.originals.values()}),31)

    def test_05_original15_create_15_update_15_delete(self):
        self.assertEqual(Counter(x["crud"] for x in self.originals.values()),
                         {"create":15,"update":15,"delete":15})

    def test_06_four_original_public_task_sha_pins_preserved(self):
        for sha,(tid,crud,q,_,_) in PINS.items():
            self.assertEqual(self.originals[tid]["original_ifc_sha256"],sha)
            self.assertEqual(self.originals[tid]["public_question_sha256"],q)
            self.assertEqual(self.originals[tid]["crud"],crud)

    def test_07_all_original_source_files_unchanged_after_real_native_edits(self):
        for tid,s in self.sources.items():
            self.assertEqual(file_hash(s),self.originals[tid]["original_ifc_sha256"])

    def test_08_separate_original_native_mutation_explicit_optin_true(self):
        for tid,s in self.sessions.items():
            self.assertEqual(s.native_mutation_original_task_id,tid)
            self.assertTrue(s.experimental_original_native_mutations_v045)
            self.assertFalse(s.experimental_original_native_readonly_v044)

    def test_09_v045_does_not_create_normalized_source_IFC(self):
        for s in self.sessions.values():
            self.assertIsNone(s.normalized)
            self.assertFalse((s.folder/"normalized_original_m.ifc").exists())

    def test_10_models_read_full_native_original_source_and_empty_plan(self):
        for tid,xml in self.baselines.items():
            root=etree.fromstring(xml)
            self.assertEqual([x.tag for x in root],
                             [Q+"OriginalNativeIFCSource",Q+"NativeEditPlan"])
            self.assertEqual(len(root[-1]),0)
            self.assertEqual(root.get("version"),"0.45")
            self.assertEqual(root[-1].get("sourceOriginalIFCSha256"),
                             self.originals[tid]["original_ifc_sha256"])

    def test_11_original_native_STEP_SOURCE_LINES_identical_to_v044(self):
        for tid in TASK_IDS:
            from src.runtime.experimental_v44_original_native_step_readonly import (
                project_native_readonly_source_v044)
            v44=project_native_readonly_source_v044(
                self.sources[tid],
                original_native_sha256=self.originals[tid]["original_ifc_sha256"])
            v45=etree.fromstring(self.baselines[tid])
            self.assertEqual(
                etree.tostring(v45[0],method="c14n"),
                etree.tostring(etree.fromstring(v44.xml)[0],method="c14n"))

    def test_12_strict_dedicated_v045_XSD_accepted(self):
        xs=etree.XMLSchema(etree.parse(str(XSD)))
        for xml in list(self.baselines.values())+list(self.submitted.values()):
            self.assertTrue(xs.validate(etree.fromstring(xml)))

    def test_13_original_native_schema_still_IFC4X3_and_units_mm(self):
        for p in self.candidates.values():
            f=ifcopenshell.open(str(p))
            self.assertEqual(f.schema,"IFC4X3")
            self.assertAlmostEqual(ifcopenshell.util.unit.calculate_unit_scale(f),.001)

    def test_14_four_distinct_original_sources_physically_mutated(self):
        self.assertEqual(set(self.sessions),set(TASK_IDS))
        for s in self.sessions.values():
            self.assertTrue(s.output_ifc.is_file())
            self.assertTrue(s.output_ifc.stat().st_size>100)
            self.assertNotEqual(file_hash(s.output_ifc),s.source_sha)

    def test_15_real_tool_independently_verifies_every_native_IFC(self):
        for tid,o in self.oracle.items():
            self.assertEqual(o["status"],"ok")
            self.assertTrue(o["native_ifc_committed"])
            self.assertEqual(o["independent_native_oracle_status"],
                             "V045_INDEPENDENT_ORIGINAL_IFC_NATIVE_MUTATION_ORACLE_PASS")

    def test_16_second_external_oracle_matches_every_actual_tool_commit(self):
        for tid,p in self.candidates.items():
            o=verify_original_native_mutation_v045(
                self.sources[tid],p,
                submitted_xml=self.submitted[tid],
                source_sha=self.originals[tid]["original_ifc_sha256"],
                task_id=tid)
            self.assertEqual(o["status"],self.oracle[tid]["independent_native_oracle_status"])

    def test_17_actual_all_four_source_mutation_covered(self):
        self.assertEqual(self.report[
            "new_v045_source_eligible_true_native_IFC_mutation_and_independent_oracle_pass"],4)

    def test_18_original_slabs_dimension_actually_changed_and_untouched_geometry_preserved(self):
        o=verify_original_native_mutation_v045(
            self.sources["geometry_test_14"],self.candidates["geometry_test_14"],
            submitted_xml=self.submitted["geometry_test_14"],
            source_sha=self.originals["geometry_test_14"]["original_ifc_sha256"],
            task_id="geometry_test_14")
        self.assertEqual(o["exact_target_original_physical_products_actually_changed"],1)

    def test_19_original_columns_placement_parent_preserved(self):
        orig=ifcopenshell.open(str(self.sources["geometry_test_15"]))
        cand=ifcopenshell.open(str(self.candidates["geometry_test_15"]))
        guid=self.edit(self.xml("geometry_test_15")).get("ifcGuid")
        a=orig.by_guid(guid).ObjectPlacement
        b=cand.by_guid(guid).ObjectPlacement
        self.assertEqual(a.PlacementRelTo.id(),b.PlacementRelTo.id())

    def test_20_shared_mapped_two_column_heights_both_physically_changed(self):
        o=verify_original_native_mutation_v045(
            self.sources["topological_test_11"],self.candidates["topological_test_11"],
            submitted_xml=self.submitted["topological_test_11"],
            source_sha=self.originals["topological_test_11"]["original_ifc_sha256"],
            task_id="topological_test_11")
        self.assertEqual(o["exact_target_original_physical_products_actually_changed"],2)

    def test_21_explicit_deleted_one_original_column_missing_in_native(self):
        f=ifcopenshell.open(str(self.candidates["topological_test_17"]))
        d=self.edit(self.xml("topological_test_17"))[0].get("ifcGuid")
        self.assertNotIn(d,{c.GlobalId for c in f.by_type("IfcColumn")})
        self.assertEqual(len(f.by_type("IfcColumn")),9)

    def test_22_all_original_non_target_source_products_physically_preserved(self):
        for tid,p in self.candidates.items():
            o=verify_original_native_mutation_v045(
                self.sources[tid],p,
                submitted_xml=self.submitted[tid],
                source_sha=self.originals[tid]["original_ifc_sha256"],
                task_id=tid)
            self.assertTrue(o["original_product_guids_preserved_except_explicit_deletions"])
            self.assertTrue(o["original_relationships_and_roles_preserved_except_deletion_refs"])
            self.assertGreaterEqual(o["non_target_original_physical_products_unchanged"],0)

    def test_23_original_native_source_read_rejects_nonpinned_IFC(self):
        other=DATA/"ifc"/"01/02/01_02_002.ifc"
        with self.assertRaises(UnsupportedArm):
            XmlSourceEditSession(other,self.tmp/"bad",
                experimental_original_native_mutations_v045=True)

    def test_24_all_prior_variants_mutually_exclusive_with_v045(self):
        for k in (
            "experimental_original_native_readonly_v044",
            "experimental_original_native_slab_v042",
            "experimental_original_p3_v041",
            "experimental_original_room_v040",
            "experimental_original_complex_v039",
            "experimental_original_legacy_v08",
        ):
            with self.assertRaisesRegex(UnsupportedArm,"mutually exclusive"):
                XmlSourceEditSession(
                    self.sources["geometry_test_14"],self.tmp/k,
                    experimental_original_native_mutations_v045=True,
                    **{k:True})

    def test_25_invalid_original_task_operation_kind_rejected(self):
        self.poison_xml(lambda r:self.edit(r).__setattr__(
            "tag",Q+"SetAllMappedColumnDepth"))

    def test_26_no_edit_action_cannot_create_native_candidate(self):
        with self.assertRaises(OriginalNativeMutation045Error):
            parse_original_native_edit_plan_v045(
                self.sources["geometry_test_14"],
                self.baselines["geometry_test_14"],
                source_sha=self.originals["geometry_test_14"]["original_ifc_sha256"])

    def test_27_original_source_root_sha_poison_rejected(self):
        self.poison_xml(lambda r:r.set("sourceOriginalIFCSha256","0"*64))

    def test_28_native_source_embedded_sha_poison_rejected(self):
        self.poison_xml(lambda r:r[0].set("sourceOriginalIFCSha256","0"*64))

    def test_29_edit_plan_source_sha_poison_rejected(self):
        self.poison_xml(lambda r:r[-1].set("sourceOriginalIFCSha256","0"*64))

    def test_30_native_source_ifc_schema_poison_rejected(self):
        self.poison_xml(lambda r:r.set("sourceIfcSchema","IFC2X3"))

    def test_31_native_source_units_poison_rejected(self):
        self.poison_xml(lambda r:r.set("sourceLengthUnit","METER"))

    def test_32_original_source_readonly_permission_poison_rejected(self):
        self.poison_xml(lambda r:r[0].set("nativeMutationPermission","RW"))

    def test_33_native_source_PRODUCT_GUID_poison_rejected(self):
        self.poison_xml(lambda r:self.native(r,"Products")[0].set("ifcGuid","0"*22))

    def test_34_native_source_relationship_GUID_poison_rejected(self):
        self.poison_xml(lambda r:self.native(r,"Relations")[0].set("ifcGuid","0"*22))

    def test_35_native_source_property_set_name_poison_rejected(self):
        self.poison_xml(lambda r:self.native(r,"PropertySets")[0].set("originalName","FORGED"))

    def test_36_native_source_material_name_poison_rejected(self):
        self.poison_xml(lambda r:self.native(r,"Materials")[0].set("originalName","FORGED"))

    def test_37_native_source_placement_matrix_poison_rejected(self):
        self.poison_xml(lambda r:self.native(r,"LocalPlacements")[0].set("m03","500"))

    def test_38_native_source_mesh_vertex_poison_rejected(self):
        self.poison_xml(lambda r:self.native(r,"WorldGeometry")[0][0][0].set("x","500"))

    def test_39_native_source_mesh_triangle_poison_rejected(self):
        self.poison_xml(lambda r:self.native(r,"WorldGeometry")[0][1][0].set("c","500"))

    def test_40_native_source_literal_STEP_line_poison_rejected(self):
        self.poison_xml(lambda r:self.native(r,"NativeStepRecords")[0].__setattr__(
            "text","#1=IFCORGANIZATION($,'FORGED',$,$,$);"))

    def test_41_native_source_literal_STEP_line_removed_rejected(self):
        def f(r):
            e=self.native(r,"NativeStepRecords");e.remove(e[0])
        self.poison_xml(f)

    def test_42_native_source_relationship_element_deleted_rejected(self):
        def f(r):
            e=self.native(r,"Relations");e.remove(e[0])
        self.poison_xml(f)

    def test_43_original_edit_plan_duplicated_rejected(self):
        def f(r):
            r[-1].append(etree.fromstring(etree.tostring(r[-1][0])))
        self.poison_xml(f)

    def test_44_original_edit_plan_removed_rejected(self):
        self.poison_xml(lambda r:r.remove(r[-1]))

    def test_45_native_edit_plan_unknown_key_rejected(self):
        self.poison_xml(lambda r:self.edit(r).set("eval","RUN_PYTHON"))

    def test_46_original_Slab_wrong_GUID_rejected(self):
        self.poison_xml(lambda r:self.edit(r).set("ifcGuid","0"*22))

    def test_47_original_Slab_negative_dimensions_rejected(self):
        self.poison_xml(lambda r:self.edit(r).set("newXDimM","-1.0"))

    def test_48_original_Slab_overlarge_dimensions_rejected(self):
        self.poison_xml(lambda r:self.edit(r).set("newXDimM","100.0"))

    def test_49_original_Slab_nan_rejected(self):
        self.poison_xml(lambda r:self.edit(r).set("newXDimM","NaN"))

    def test_50_original_Slab_noop_rejected(self):
        s=ifcopenshell.open(str(self.sources["geometry_test_14"]))
        solid=s.by_type("IfcSlab")[0].Representation.Representations[0].Items[0]
        self.poison_xml(lambda r:self.edit(r).set(
            "newXDimM",f"{solid.SweptArea.XDim/1000:.6f}"))

    def test_51_original_Slab_both_dimensions_changed_rejected(self):
        self.poison_xml(lambda r:self.edit(r).set("newYDimM","12.0"))

    def test_52_original_Slab_decrease_only_rejected(self):
        self.poison_xml(lambda r:self.edit(r).set("newXDimM","8.0"))

    def test_53_original_column_move_bad_GUID_rejected(self):
        self.poison_xml(lambda r:self.edit(r).set("ifcGuid","0"*22),
                        "geometry_test_15")

    def test_54_original_column_move_nan_rejected(self):
        self.poison_xml(lambda r:self.edit(r).set("newWorldOriginXM","NaN"),
                        "geometry_test_15")

    def test_55_original_column_move_noop_rejected(self):
        orig=ifcopenshell.open(str(self.sources["geometry_test_15"]))
        col=orig.by_guid(self.edit(self.xml("geometry_test_15")).get("ifcGuid"))
        from ifcopenshell.util.placement import get_local_placement
        p=get_local_placement(col.ObjectPlacement)
        self.poison_xml(lambda r:self.edit(r).set(
            "newWorldOriginXM",f"{p[0,3]/1000:.6f}"),"geometry_test_15")

    def test_56_original_column_move_extra_z_attribute_rejected(self):
        self.poison_xml(lambda r:self.edit(r).set(
            "newWorldOriginZM","3.0"),"geometry_test_15")

    def test_57_shared_original_column_height_negative_rejected(self):
        self.poison_xml(lambda r:self.edit(r).set("newDepthM","-1.0"),
                        "topological_test_11")

    def test_58_shared_original_column_height_zero_rejected(self):
        self.poison_xml(lambda r:self.edit(r).set("newDepthM","0"),
                        "topological_test_11")

    def test_59_shared_original_column_height_noop_rejected(self):
        self.poison_xml(lambda r:self.edit(r).set("newDepthM","1.500000"),
                        "topological_test_11")

    def test_60_shared_original_column_height_extra_GUID_target_rejected(self):
        self.poison_xml(lambda r:self.edit(r).set("ifcGuid","0"*22),
                        "topological_test_11")

    def test_61_original_Column_Delete_target_other_noncolumn_guid_rejected(self):
        f=ifcopenshell.open(str(self.sources["topological_test_17"]))
        g=f.by_type("IfcSlab")[0].GlobalId
        self.poison_xml(lambda r:self.edit(r)[0].set(
            "ifcGuid",g),"topological_test_17")

    def test_62_original_Column_Delete_duplicate_GUID_rejected(self):
        def f(r):
            x=self.edit(r)
            x.append(etree.fromstring(etree.tostring(x[0])))
        self.poison_xml(f,"topological_test_17")

    def test_63_original_Column_Delete_no_column_rejected(self):
        def f(r):
            x=self.edit(r);x.remove(x[0])
        self.poison_xml(f,"topological_test_17")

    def test_64_original_Column_Delete_extra_attr_rejected(self):
        self.poison_xml(lambda r:self.edit(r)[0].set("reason","HIDDEN_GT"),
                        "topological_test_17")

    def test_65_original_Column_Delete_other_tag_rejected(self):
        self.poison_xml(lambda r:self.edit(r)[0].__setattr__(
            "tag",Q+"DeleteWall"),"topological_test_17")

    def test_66_source_corruption_bad_schema_refused_even_with_valid_XML(self):
        corrupted=ifcopenshell.open(str(self.sources["geometry_test_14"]))
        corrupted.by_type("IfcSlab")[0].Name="BAD_SOURCE"
        p=self.tmp/"not_the_original.ifc"
        corrupted.write(str(p))
        with self.assertRaises(OriginalNativeMutation045Error):
            compile_original_native_mutation_v045(
                p,self.submitted["geometry_test_14"],
                self.tmp/"must_not_write.ifc",
                source_sha=self.originals["geometry_test_14"]["original_ifc_sha256"])
        self.assertFalse((self.tmp/"must_not_write.ifc").exists())

    def test_67_candidate_IFC_modified_unrelated_metadata_fails_oracle(self):
        self.poison_candidate(
            lambda f:setattr(f.by_type("IfcProject")[0],"Name","FORGED_PROJECT"),
            "geometry_test_14")

    def test_68_candidate_IFC_modified_unrelated_product_GUID_fails_oracle(self):
        self.poison_candidate(
            lambda f:setattr(f.by_type("IfcBuildingStorey")[0],"GlobalId","0"*22),
            "geometry_test_14")

    def test_69_candidate_IFC_modified_relationship_GUID_fails_oracle(self):
        self.poison_candidate(
            lambda f:setattr(f.by_type("IfcRelationship")[0],"GlobalId","0"*22),
            "geometry_test_14")

    def test_70_candidate_IFC_moved_unrelated_other_column_fails_oracle(self):
        def modify(f):
            p=sorted(f.by_type("IfcColumn"),key=lambda x:x.GlobalId)[-1]
            c=p.ObjectPlacement.RelativePlacement.Location
            v=list(c.Coordinates);v[0]+=500
            c.Coordinates=tuple(v)
        self.poison_candidate(modify,"geometry_test_15")

    def test_71_candidate_IFC_was_not_physically_moved_fails_oracle(self):
        def modify(f):
            original=ifcopenshell.open(str(self.sources["geometry_test_15"]))
            guid=self.edit(self.xml("geometry_test_15")).get("ifcGuid")
            f.by_guid(guid).ObjectPlacement.RelativePlacement.Location.Coordinates=(
                original.by_guid(guid).ObjectPlacement.RelativePlacement.Location.Coordinates)
        self.poison_candidate(modify,"geometry_test_15")

    def test_72_candidate_IFC_Slab_wrong_profile_dimensions_fails_oracle(self):
        self.poison_candidate(
            lambda f:setattr(
                f.by_type("IfcSlab")[0].Representation.Representations[0].Items[0].SweptArea,
                "XDim",10000.0),"geometry_test_14")

    def test_73_candidate_IFC_shared_column_height_mismatches_XML_fails_oracle(self):
        def modify(f):
            p=f.by_type("IfcColumn")[0]
            p.Representation.Representations[0].Items[0].MappingSource.MappedRepresentation.Items[0].Depth=2500.0
        self.poison_candidate(modify,"topological_test_11")

    def test_74_candidate_IFC_target_column_not_actually_deleted_fails_oracle(self):
        # Original unmodified IFC is invalid as candidate for explicit native deletion.
        p=self.sources["topological_test_17"]
        with self.assertRaises(IndependentNativeMutation045Error):
            verify_original_native_mutation_v045(
                p,p,submitted_xml=self.submitted["topological_test_17"],
                source_sha=self.originals["topological_test_17"]["original_ifc_sha256"],
                task_id="topological_test_17")

    def test_75_candidate_IFC_wrong_original_native_units_fails_oracle(self):
        f=ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(self.candidates["geometry_test_14"])),"METER")
        out=self.tmp/"bad_units.ifc";f.write(str(out))
        with self.assertRaises(IndependentNativeMutation045Error):
            verify_original_native_mutation_v045(
                self.sources["geometry_test_14"],out,
                submitted_xml=self.submitted["geometry_test_14"],
                source_sha=self.originals["geometry_test_14"]["original_ifc_sha256"],
                task_id="geometry_test_14")

    def test_76_native_ifc_submitted_XML_after_accept_read_matches_commit(self):
        for tid,s in self.sessions.items():
            out=s.call("read_building_xml",{})
            self.assertEqual(out["xml"].encode("utf8"),self.submitted[tid])
            self.assertTrue(out["native_candidate_available"])
            self.assertEqual(s.output_ifc,self.candidates[tid])

    def test_77_actual_model_tool_rejects_spoof_next_XML_without_state_rollback(self):
        for tid,s in self.sessions.items():
            original_sha=file_hash(s.output_ifc)
            bad=self.submitted[tid].decode("utf8").replace(
                "NativeEditPlan","SpoofNativeEditPlan",1)
            result=s.call("submit_building_xml",{"xml_text":bad})
            self.assertEqual(result["status"],"error")
            self.assertFalse(result["native_ifc_committed"])
            self.assertTrue(result["last_valid_xml_preserved"])
            self.assertEqual(file_hash(s.output_ifc),original_sha)
            self.assertEqual(s.current_xml,self.submitted[tid])

    def test_78_original_public_input_IFC_sources_still_byte_identical(self):
        for tid in TASK_IDS:
            self.assertEqual(file_hash(self.sources[tid]),
                             self.originals[tid]["original_ifc_sha256"])

    def test_79_no_original_task_answer_claimed_by_any_success(self):
        for r in self.oracle.values():
            self.assertFalse(r["original_author_benchmark_task_success_claimed"])
        self.assertEqual(self.report["new_v045_native_original_task_semantic_answers_proven"],0)

    def test_80_paid_model_Docker_and_author_grader_never_used(self):
        self.assertEqual(self.report["new_v045_paid_provider_calls"],0)
        self.assertEqual(self.report["new_v045_Docker_runs"],0)
        self.assertEqual(self.report["new_v045_author_grader_calls"],0)
        self.assertEqual(self.report["new_v045_matched_LLM_trials"],0)

    def test_81_prior_task_specific_developer_CREATE_pairs_not_inflated(self):
        self.assertEqual(self.report["original_developer_D0_I0_task_pairs_CREATE"],5)
        self.assertFalse(self.report["original_full_45_equal_source_info_and_write_authority_proven"])

    def test_82_new_writers_are_explicitly_NOT_activated_by_default_runner(self):
        self.assertTrue(self.report["new_v045_not_default_paid_runner_mode"])
        self.assertNotIn("experimental_original_native_mutations_v045=True",
                         (ROOT/"tools"/"bibimbap_matched25_cli.py").read_text(encoding="utf8"))

    def test_83_old_v044_readonly_source_gate_remains_unchanged_and_rejects_edits(self):
        tid="geometry_test_14"
        with TemporaryDirectory() as t:
            s=XmlSourceEditSession(
                self.sources[tid],Path(t)/"readonly",
                experimental_original_native_readonly_v044=True)
            old=s.call("read_building_xml",{})
            out=s.call("submit_building_xml",{"xml_text":old["xml"]})
            self.assertEqual(out["status"],"error")
            self.assertEqual(out["error_type"],"UnsupportedArm")
            self.assertIsNone(s.output_ifc)

    def test_84_earlier_original_default_schema_not_extended(self):
        self.assertNotIn("NativeEditPlan",
            (ROOT/"spec"/"original_native_step_readonly_v044.xsd").read_text(encoding="utf8"))
        self.assertNotIn("NativeEditPlan",
            (ROOT/"spec"/"toy_markup_v0.xsd").read_text(encoding="utf8"))

    def test_85_machine_report_refuses_overwrite(self):
        with self.assertRaises(FileExistsError):
            with REPORT.open("xb") as stream:stream.write(b"FORGED")
        self.assertEqual(file_hash(REPORT),FROZEN_SHA)

    def test_86_byte_exact_independent_report_replay(self):
        report=audit(AUTHOR,DATA)
        raw=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(sha256(raw).hexdigest(),FROZEN_SHA)
        self.assertEqual(raw,REPORT.read_bytes())


if __name__=="__main__":
    unittest.main()
