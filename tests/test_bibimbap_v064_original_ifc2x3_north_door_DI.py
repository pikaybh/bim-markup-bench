"""v0.64 true original IFC2X3 nearest+north native D/M/Docker I test suite.

Actual source physically supported three-Wall IFC2X3, mandatory
OwnerHistory, host Wall CSG through-opening and genuine 3D meshes.
Evaluates original public question separately from author repository
heterogeneous float/bool scorer, which only audit may import.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,main
from unittest.mock import patch
import json

import ifcopenshell
import ifcopenshell.api.root
from lxml import etree

from tools.bibimbap_matched25_tools import DockerIFCExecutor,file_hash
from tools import audit_bibimbap_v064_ifc2x3_north_door_DI as audit
from tools.bibimbap_v064_ifc2x3_north_door_native import (
    TASK,SOURCE_SHA,STATUS,MAX_CALLS,
    OriginalDoorIFC2X3Native064Error,
    source_original_ifc2x3,full_original_state_v064,
    managed_original_state_v064,parse_full_final_v064,
    restore_managed_final_v064,compile_native_ifc2x3_door_v064,
    source_native_ifc2x3_scope_v064,canonical_semantic_digest_v064,
)
from tools.bibimbap_v064_ifc2x3_north_door_sessions import (
    DirectFullState064,DirectManagedState064,LiveDockerPython064,
)
from tools.bibimbap_v057_provenance import (
    ProviderTrialBlocked057,refuse_all_model_trials_v057,
)


FROZEN_REPORT_SHA="0499d218d2da2dcb5277c36ce33ae2fcb93ca40ef41fa0c9b079270e5ad7669d"


class OriginalSourceIFC2X3NorthDoorNative064(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(audit.REPORT.read_text("utf8"))
        cls.task=next(x for x in audit.public_45(audit.AUTHOR,audit.DATA)
                      if x["test_id"]==TASK)
        cls.source=audit.DATA/"ifc"/cls.task["original_source_ifc_relpath"]
        cls.model=source_original_ifc2x3(cls.source,source_sha=SOURCE_SHA)
        cls.nearest,cls.far,cls.reference=audit.source_public_north_wall_v064(
            cls.model,cls.task["public_question"])
        cls.initial=full_original_state_v064(
            cls.source,source_sha=SOURCE_SHA)
        cls.compact=managed_original_state_v064(
            cls.source,source_sha=SOURCE_SHA)
        cls.correct=audit.native_source_developer_fixture_v064(
            "TEST64_GOOD",cls.nearest,.9,2.1)
        cls.far_wrong=audit.native_source_developer_fixture_v064(
            "TEST64_FAR",cls.far,.9,2.1)
        cls.small_wrong=audit.native_source_developer_fixture_v064(
            "TEST64_SMALL",cls.nearest,.4,1.2)

    def setUp(self):
        self.temp=TemporaryDirectory(prefix="v064-original-source-ifc2x3-")
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)

    def d(self):
        return DirectFullState064(self.source,self.path/"D")

    def m(self):
        return DirectManagedState064(self.source,self.path/"M")

    def i(self):
        return LiveDockerPython064(self.source,self.path/"I")

    def full(self,state=None):
        return audit._populate(
            self.initial,state or self.correct,managed=False)

    def managed(self,state=None):
        return audit._populate(
            self.compact,state or self.correct,managed=True)

    def bad_full(self,raw):
        with self.assertRaises(Exception):
            parse_full_final_v064(
                self.source,raw.encode("utf8"),source_sha=SOURCE_SHA)

    def bad_managed(self,raw):
        with self.assertRaises(Exception):
            restore_managed_final_v064(
                self.source,raw.encode("utf8"),source_sha=SOURCE_SHA)

    def candidate(self,state=None,name="original.ifc"):
        spec=parse_full_final_v064(
            self.source,self.full(state).encode("utf8"),source_sha=SOURCE_SHA)
        out=self.path/name
        compile_native_ifc2x3_door_v064(
            self.source,out,source_sha=SOURCE_SHA,state=spec)
        return out

    def test_01_actual_frozen_report_SHA(self):
        self.assertEqual(file_hash(audit.REPORT),FROZEN_REPORT_SHA)

    def test_02_report_canonical_bytes_equal(self):
        self.assertEqual(audit.REPORT.read_bytes(),
                         audit.canonical(self.report))

    def test_03_parent_v063_frozen_report_preserved(self):
        self.assertEqual(file_hash(audit.PARENT),audit.PARENT_SHA)

    def test_04_v058_fixed_source_selection_preserved(self):
        self.assertEqual(file_hash(audit.FROZEN),audit.FROZEN_SHA)

    def test_05_exact_frozen_six_all_source_native_supported(self):
        self.assertEqual(self.report[
            "prespecified_six_original_public_task_ids_unchanged"],audit.FIXED_SIX)
        self.assertEqual(self.report[
            "fixed_six_original_source_native_developer_supported"],audit.FIXED_SIX)
        self.assertEqual(self.report[
            "original_fixed_six_now_developer_technically_supported_count"],6)

    def test_06_original_10_of_45_developer_only(self):
        self.assertEqual(self.report[
            "original_total_45_task_specific_developer_supported_count"],10)
        self.assertEqual(self.report[
            "original_total_45_tasks_not_developer_native_implemented"],35)

    def test_07_original_45_tasks_31_distinct_source_hashes(self):
        self.assertEqual(self.report["original_total_public_task_count"],45)
        self.assertEqual(self.report["original_total_distinct_IFC_source_files"],31)

    def test_08_original_source_SHA_unchanged(self):
        self.assertEqual(file_hash(self.source),SOURCE_SHA)
        self.assertEqual(self.task["original_ifc_sha256"],SOURCE_SHA)

    def test_09_exact_native_IFC2X3_schema_not_IFC4X3(self):
        self.assertEqual(self.model.schema,"IFC2X3")
        self.assertEqual(self.report["original_source_IFC_schema"],"IFC2X3")

    def test_10_original_native_mm_world_mesh_metres(self):
        self.assertEqual(self.report[
            "original_original_IFC2X3_native_length_unit"],"MILLIMETER")
        self.assertEqual(self.report["world_mesh_SI_unit"],"METRE")

    def test_11_source_164_STEP_52_Roots(self):
        self.assertEqual(len(list(self.model)),164)
        self.assertEqual(len(self.model.by_type("IfcRoot")),52)

    def test_12_source_exact_three_Walls_no_Doors(self):
        self.assertEqual(len(self.model.by_type("IfcWall")),3)
        self.assertEqual(len(self.model.by_type("IfcDoor")),0)
        self.assertEqual(len(self.model.by_type("IfcOpeningElement")),0)

    def test_13_source_no_fill_void_or_spaces(self):
        for kind in ("IfcRelFillsElement","IfcRelVoidsElement","IfcSpace"):
            self.assertEqual(len(self.model.by_type(kind)),0)

    def test_14_source_reference_is_south_wall(self):
        self.assertAlmostEqual(
            self.reference.ObjectPlacement.RelativePlacement.Location.Coordinates[1],
            -900.,places=5)

    def test_15_source_nearest_north_wall_y_1600mm(self):
        self.assertAlmostEqual(
            self.nearest.ObjectPlacement.RelativePlacement.Location.Coordinates[1],
            1600.,places=5)

    def test_16_source_farther_north_wall_y_5100mm(self):
        self.assertAlmostEqual(
            self.far.ObjectPlacement.RelativePlacement.Location.Coordinates[1],
            5100.,places=5)

    def test_17_positive_Y_source_reference_wall_has_two_north_candidates(self):
        n,f,ref=audit.source_public_north_wall_v064(
            self.model,self.task["public_question"])
        self.assertEqual(n.GlobalId,self.nearest.GlobalId)
        self.assertEqual(f.GlobalId,self.far.GlobalId)
        self.assertNotEqual(ref.GlobalId,n.GlobalId)

    def test_18_original_public_question_SHA_matches(self):
        self.assertEqual(self.report[
            "original_public_question_SHA256"],self.task["public_question_sha256"])

    def test_19_original_source_full_initial_XML_byte_size(self):
        self.assertEqual(len(self.initial),2185)
        self.assertEqual(self.report[
            "original_source_exact_three_Wall_initial_full_XML_utf8_bytes"],2185)

    def test_20_original_compact_complete_XML_byte_size(self):
        self.assertEqual(len(self.compact),761)
        self.assertEqual(self.report[
            "original_source_compact_three_Wall_XML_utf8_bytes"],761)

    def test_21_three_exact_original_wall_complete_roster(self):
        root=etree.fromstring(self.initial)
        self.assertEqual(len(root[1]),3)
        self.assertEqual(
            [x.get("ifcGuid") for x in root[1]],
            sorted(w.GlobalId for w in self.model.by_type("IfcWall")))
        self.assertEqual(len(root[2]),0)

    def test_22_compact_exact_three_original_wall_complete_roster(self):
        doc=etree.fromstring(self.compact)
        self.assertEqual(len(doc[0]),3)
        self.assertEqual(len(doc[1]),0)

    def test_23_true_D_full_managed_Docker_same_initial_read_bytes(self):
        D,M,I=self.d(),self.m(),self.i()
        reads=[x.call("read_building_xml",{"query":"source"}) for x in (D,M,I)]
        self.assertEqual([r["status"] for r in reads],["ok"]*3)
        self.assertEqual(reads[0]["xml"],reads[1]["xml"])
        self.assertEqual(reads[1]["xml"],reads[2]["xml"])
        self.assertEqual(reads[0]["xml"].encode("utf8"),self.initial)

    def test_24_tool_read_schema_identical_D_full_managed_I(self):
        D,M,I=self.d(),self.m(),self.i()
        self.assertEqual(D.tools[0],M.tools[0])
        self.assertEqual(M.tools[0],I.tools[0])

    def test_25_different_edit_schema_and_no_fake_tokens(self):
        D,M,I=self.d(),self.m(),self.i()
        self.assertEqual(
            [D.tools[1]["name"],M.tools[1]["name"],I.tools[1]["name"]],
            ["submit_building_xml","submit_managed_final_state","execute_ifc_code"])
        self.assertIsNone(self.report[
            "approved_paid_provider_model_snapshot_tokens_budget"])

    def test_26_real_pinned_executor_is_unmodified_DockerIFCExecutor(self):
        self.assertIs(type(self.i().executor),DockerIFCExecutor)

    def test_27_complete_original_D_FULL_native_CSG_edit(self):
        D=self.d()
        result=D.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(result["status"],"ok")
        self.assertTrue(result["native_ifc_committed"])
        self.assertEqual(result[
            "native_original_Wall_full_thickness_CSG_cut_m3"],.418)

    def test_28_complete_original_D_MANAGED_native_CSG_edit(self):
        M=self.m()
        result=M.call("submit_managed_final_state",{"xml_text":self.managed()})
        self.assertEqual(result["status"],"ok")
        self.assertTrue(result["native_ifc_committed"])
        self.assertEqual(result["original_source_IFC2X3_new_schema_errors"],0)

    def test_29_full_and_managed_reconstructed_XML_identical(self):
        full,parsed=restore_managed_final_v064(
            self.source,self.managed().encode("utf8"),source_sha=SOURCE_SHA)
        self.assertEqual(full,self.full().encode("utf8"))
        self.assertEqual(parsed["host_guid"],self.nearest.GlobalId)

    def test_30_D_FULL_D_MANAGED_identical_native_semantics(self):
        D,M=self.d(),self.m()
        self.assertEqual(D.call("submit_building_xml",
                         {"xml_text":self.full()})["status"],"ok")
        self.assertEqual(M.call("submit_managed_final_state",
                         {"xml_text":self.managed()})["status"],"ok")
        r1=source_native_ifc2x3_scope_v064(
            self.source,D.output_ifc,source_sha=SOURCE_SHA)
        r2=source_native_ifc2x3_scope_v064(
            self.source,M.output_ifc,source_sha=SOURCE_SHA)
        self.assertEqual(canonical_semantic_digest_v064(r1),
                         canonical_semantic_digest_v064(r2))

    def test_31_D_FULL_D_MANAGED_accepted_whole_final_XML_identical(self):
        D,M=self.d(),self.m()
        self.assertEqual(D.call("submit_building_xml",
                         {"xml_text":self.full()})["status"],"ok")
        self.assertEqual(M.call("submit_managed_final_state",
                         {"xml_text":self.managed()})["status"],"ok")
        self.assertEqual(D.current_xml,M.current_xml)

    def test_32_actual_new_Door_Opening_source_Wall_scope_reopened(self):
        f=ifcopenshell.open(str(self.candidate()))
        self.assertEqual(len(f.by_type("IfcDoor")),1)
        self.assertEqual(len(f.by_type("IfcOpeningElement")),1)
        self.assertEqual(len(f.by_type("IfcRelFillsElement")),1)
        self.assertEqual(len(f.by_type("IfcRelVoidsElement")),1)

    def test_33_all_original_164_STEP_entities_preserved(self):
        r=source_native_ifc2x3_scope_v064(
            self.source,self.candidate(),source_sha=SOURCE_SHA)
        self.assertEqual(r[
            "original_IFC2X3_source_native_STEP_entities_unchanged"],164)

    def test_34_actual_native_source_Wall_CSG_cut_0_418_m3(self):
        r=source_native_ifc2x3_scope_v064(
            self.source,self.candidate(),source_sha=SOURCE_SHA)
        self.assertEqual(r[
            "native_original_IFC2X3_wall_full_thickness_volume_lost_m3"],.418)
        self.assertEqual(r["native_expected_original_wall_cut_volume_m3"],.418)

    def test_35_all_new_IFC2X3_relation_OwnerHistory_nonoptional(self):
        out=self.candidate()
        f=ifcopenshell.open(str(out))
        self.assertTrue(all(x.OwnerHistory is not None
                            for x in f.by_type("IfcRoot")))
        v=source_native_ifc2x3_scope_v064(
            self.source,out,source_sha=SOURCE_SHA)
        self.assertTrue(v["new_mandatory_IFC2X3_OwnerHistory_valid"])

    def test_36_new_IFC2X3_schema_findings_zero(self):
        verdict=source_native_ifc2x3_scope_v064(
            self.source,self.candidate(),source_sha=SOURCE_SHA)
        self.assertEqual(verdict["native_original_IFC2X3_new_schema_errors"],0)

    def test_37_native_Door_panel_dimensions_encode_native_mm(self):
        f=ifcopenshell.open(str(self.candidate()))
        door=f.by_type("IfcDoor")[0]
        self.assertAlmostEqual(door.OverallWidth,900.)
        self.assertAlmostEqual(door.OverallHeight,2100.)

    def test_38_correct_source_nearest_positive_Y_public_predicate(self):
        r=audit.public_nearest_north_physical_v064(
            self.source,self.candidate(),self.task["public_question"])
        self.assertTrue(r["candidate_host_is_nearest_positive_Y_wall"])
        self.assertTrue(r["public_original_question_physical_correct"])

    def test_39_structurally_valid_farther_north_door_public_wrong(self):
        out=self.candidate(self.far_wrong,"wrong_far.ifc")
        verdict=source_native_ifc2x3_scope_v064(
            self.source,out,source_sha=SOURCE_SHA)
        pub=audit.public_nearest_north_physical_v064(
            self.source,out,self.task["public_question"])
        self.assertEqual(verdict["status"],STATUS)
        self.assertTrue(pub["candidate_host_is_farther_positive_Y_wall"])
        self.assertFalse(pub["public_original_question_physical_correct"])

    def test_40_structurally_valid_too_small_door_public_wrong(self):
        out=self.candidate(self.small_wrong,"wrong_small.ifc")
        verdict=source_native_ifc2x3_scope_v064(
            self.source,out,source_sha=SOURCE_SHA)
        pub=audit.public_nearest_north_physical_v064(
            self.source,out,self.task["public_question"])
        self.assertEqual(verdict["status"],STATUS)
        self.assertTrue(pub["candidate_host_is_nearest_positive_Y_wall"])
        self.assertFalse(pub["candidate_Door_reasonable_dims"])
        self.assertFalse(pub["public_original_question_physical_correct"])

    def test_41_actual_three_OS_isolated_Python_Docker_executions_attested(self):
        self.assertEqual(self.report[
            "genuine_pinned_OS_isolated_python_scripts_executed"],3)
        self.assertTrue(all(x["actual_genuine_pinned_linux_docker_python"]
            for x in self.report["source_only_original_IFC2X3_developer_controls"]))

    def test_42_nine_native_D_FULL_D_MANAGED_I_candidates(self):
        self.assertEqual(self.report[
            "actual_original_native_IFC2X3_developer_candidates_admitted"],9)
        self.assertEqual(self.report["native_real_D_full_original_IFC2X3_edits"],3)
        self.assertEqual(self.report["native_real_D_managed_original_IFC2X3_edits"],3)
        self.assertEqual(self.report[
            "native_real_pinned_Linux_Docker_I_IFC2X3_edits"],3)

    def test_43_three_equal_per_case_D_I_semantic_DIGESTS(self):
        rows=self.report["source_only_original_IFC2X3_developer_controls"]
        self.assertEqual(len(rows),3)
        self.assertEqual(len({x["all_three_genuine_D_I_canonical_IFC_semantic_SHA256"]
                              for x in rows}),3)

    def test_44_author_repo_correct_score_one(self):
        rows=self.report["source_only_original_IFC2X3_developer_controls"]
        self.assertEqual(rows[0]["original_author_repo_grader_evaluator_only"][
            "author_repo_mean"],1.)
        self.assertTrue(rows[0]["original_author_repo_grader_evaluator_only"][
            "author_repo_numeric_boolean_and_float_metrics"]["right_location"])

    def test_45_author_repo_farther_north_fails_location(self):
        r=self.report["source_only_original_IFC2X3_developer_controls"][1]
        grading=r["original_author_repo_grader_evaluator_only"]
        self.assertFalse(grading[
            "author_repo_numeric_boolean_and_float_metrics"]["right_location"])
        self.assertLess(grading["author_repo_mean"],1.)

    def test_46_original_author_repo_too_small_fails_dimensions(self):
        r=self.report["source_only_original_IFC2X3_developer_controls"][2]
        grading=r["original_author_repo_grader_evaluator_only"]
        self.assertEqual(grading["author_repo_mean"],.75)
        self.assertFalse(grading[
            "author_repo_numeric_boolean_and_float_metrics"]["right_dimensions"])

    def test_47_original_repo_integrity_is_float_not_forced_boolean(self):
        rows=self.report["source_only_original_IFC2X3_developer_controls"]
        self.assertIs(type(rows[1]["original_author_repo_grader_evaluator_only"][
            "author_repo_numeric_boolean_and_float_metrics"]["integrity_constraint"]),
            float)

    def test_48_no_original_correct_target_GUID_in_frozen_report(self):
        raw=audit.REPORT.read_text("utf8")
        self.assertNotIn(self.nearest.GlobalId,raw)
        self.assertNotIn(self.reference.GlobalId,raw)
        self.assertTrue(all(x["original_source_correct_target_GUID_redacted"]
             for x in self.report["source_only_original_IFC2X3_developer_controls"]))

    def test_49_published_paper_official_scorer_not_verified(self):
        self.assertFalse(self.report[
            "published_paper_official_scorer_revision_equivalence_verified"])

    def test_50_source_initial_full_no_new_2_products_refused(self):
        self.bad_full(self.initial.decode("utf8"))

    def test_51_source_initial_compact_no_new_2_products_refused(self):
        self.bad_managed(self.compact.decode("utf8"))

    def test_52_full_missing_one_IfcDoor_refused(self):
        doc=etree.fromstring(self.full().encode("utf8"))
        doc[2].remove(doc[2][1])
        self.bad_full(etree.tostring(doc).decode("utf8"))

    def test_53_full_missing_original_source_Wall_row_refused(self):
        doc=etree.fromstring(self.full().encode("utf8"))
        doc[1].remove(doc[1][0])
        self.bad_full(etree.tostring(doc).decode("utf8"))

    def test_54_compact_reordered_original_Wall_rows_refused(self):
        doc=etree.fromstring(self.managed().encode("utf8"))
        doc[0].insert(0,doc[0][-1])
        self.bad_managed(etree.tostring(doc).decode("utf8"))

    def test_55_compact_original_full_XML_SHA_tamper_refused(self):
        doc=etree.fromstring(self.managed().encode("utf8"))
        doc.set("sourceFullBuildingStateSha256","f"*64)
        self.bad_managed(etree.tostring(doc).decode("utf8"))

    def test_56_original_source_IFC_SHA_tamper_refused(self):
        doc=etree.fromstring(self.full().encode("utf8"))
        doc.set("sourceOriginalIFCSha256","f"*64)
        self.bad_full(etree.tostring(doc).decode("utf8"))

    def test_57_modified_original_product_world_bbox_tamper_refused(self):
        doc=etree.fromstring(self.full().encode("utf8"))
        x=next(node for node in doc[0][0] if node.get("minYM") is not None)
        x.set("minYM","55.000000")
        self.bad_full(etree.tostring(doc).decode("utf8"))

    def test_58_duplicate_new_IFC2X3_product_GUID_rejected(self):
        doc=etree.fromstring(self.full().encode("utf8"))
        doc[2][1].set("ifcGuid",doc[2][0].get("ifcGuid"))
        self.bad_full(etree.tostring(doc).decode("utf8"))

    def test_59_original_existing_source_wall_GUID_reuse_rejected(self):
        doc=etree.fromstring(self.full().encode("utf8"))
        doc[2][1].set("ifcGuid",self.reference.GlobalId)
        self.bad_full(etree.tostring(doc).decode("utf8"))

    def test_60_wrong_new_door_fills_opening_id_rejected(self):
        doc=etree.fromstring(self.full().encode("utf8"))
        doc[2][1].set("fillsOpeningGuid","0"*22)
        self.bad_full(etree.tostring(doc).decode("utf8"))

    def test_61_new_door_not_contained_in_opening_bbox_rejected(self):
        doc=etree.fromstring(self.full().encode("utf8"))
        doc[2][1].set("minYM","3.000000")
        self.bad_full(etree.tostring(doc).decode("utf8"))

    def test_62_opening_shallow_not_through_wall_refused(self):
        doc=etree.fromstring(self.full().encode("utf8"))
        doc[2][0].set("minYM","1.550000")
        doc[2][0].set("maxYM","1.630000")
        doc[2][1].set("minYM","1.565000")
        doc[2][1].set("maxYM","1.610000")
        self.bad_full(etree.tostring(doc).decode("utf8"))

    def test_63_wrong_native_unit_scaling_wrong_1000x_world_refused(self):
        doc=etree.fromstring(self.full().encode("utf8"))
        doc[2][0].set("maxXM","950.000000")
        self.bad_full(etree.tostring(doc).decode("utf8"))

    def test_64_nonfinite_coordinate_nan_refused(self):
        doc=etree.fromstring(self.full().encode("utf8"))
        doc[2][0].set("minXM","NaN")
        self.bad_full(etree.tostring(doc).decode("utf8"))

    def test_65_noncanonical_7_decimal_coordinate_refused(self):
        doc=etree.fromstring(self.full().encode("utf8"))
        doc[2][0].set("maxXM","0.4750000")
        self.bad_full(etree.tostring(doc).decode("utf8"))

    def test_66_typed_operation_command_inside_final_roster_refused(self):
        doc=etree.fromstring(self.full().encode("utf8"))
        doc[2][1].set("operation","create")
        self.bad_full(etree.tostring(doc).decode("utf8"))

    def test_67_entity_expansion_XXE_DTD_refused(self):
        body=self.full().encode("utf8")
        dtd=b"<!DOCTYPE BuildingState [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>"
        self.bad_full(body.replace(b"?>",b"?>"+dtd,1).decode("utf8"))

    def test_68_native_wrong_IfcDoor_OverallWidth_mm_rejected(self):
        out=self.candidate()
        f=ifcopenshell.open(str(out))
        f.by_type("IfcDoor")[0].OverallWidth=900000.
        f.write(str(out))
        with self.assertRaises(OriginalDoorIFC2X3Native064Error):
            source_native_ifc2x3_scope_v064(
                self.source,out,source_sha=SOURCE_SHA)

    def test_69_native_IFC2X3_missing_RelFills_rejected(self):
        out=self.candidate()
        f=ifcopenshell.open(str(out))
        f.remove(f.by_type("IfcRelFillsElement")[0])
        f.write(str(out))
        with self.assertRaises(OriginalDoorIFC2X3Native064Error):
            source_native_ifc2x3_scope_v064(
                self.source,out,source_sha=SOURCE_SHA)

    def test_70_native_IFC2X3_missing_mandatory_OwnerHistory_rejected(self):
        out=self.candidate()
        f=ifcopenshell.open(str(out))
        # IFC2X3 correctly marks OwnerHistory NON-OPTIONAL. The actual
        # IfcOpenShell runtime itself must refuse removal before a
        # malformed candidate can be serialized or accepted.
        with self.assertRaises(TypeError):
            f.by_type("IfcRelFillsElement")[0].OwnerHistory=None
        f.write(str(out))
        verdict=source_native_ifc2x3_scope_v064(
            self.source,out,source_sha=SOURCE_SHA)
        self.assertTrue(verdict["new_mandatory_IFC2X3_OwnerHistory_valid"])

    def test_71_native_IFC2X3_original_Wall_attr_tamper_rejected(self):
        out=self.candidate()
        f=ifcopenshell.open(str(out))
        f.by_guid(self.reference.GlobalId).Name="UNRELATED_WALL_EDIT"
        f.write(str(out))
        with self.assertRaises(OriginalDoorIFC2X3Native064Error):
            source_native_ifc2x3_scope_v064(
                self.source,out,source_sha=SOURCE_SHA)

    def test_72_native_IFC2X3_extra_new_Root_rejected(self):
        out=self.candidate()
        f=ifcopenshell.open(str(out))
        ifcopenshell.api.root.create_entity(f,ifc_class="IfcBuildingElementProxy")
        f.write(str(out))
        with self.assertRaises(OriginalDoorIFC2X3Native064Error):
            source_native_ifc2x3_scope_v064(
                self.source,out,source_sha=SOURCE_SHA)

    def test_73_native_IFC2X3_orphan_point_rejected(self):
        out=self.candidate()
        f=ifcopenshell.open(str(out))
        f.create_entity("IfcCartesianPoint",Coordinates=(250.,250.,0.))
        f.write(str(out))
        with self.assertRaises(OriginalDoorIFC2X3Native064Error):
            source_native_ifc2x3_scope_v064(
                self.source,out,source_sha=SOURCE_SHA)

    def test_74_native_source_original_file_alias_rejected(self):
        with self.assertRaises(OriginalDoorIFC2X3Native064Error):
            source_native_ifc2x3_scope_v064(
                self.source,self.source,source_sha=SOURCE_SHA)

    def test_75_actually_executed_Docker_shallow_opening_refused(self):
        self.assertTrue(self.report[
            "actual_native_Docker_shallow_ifc2x3_opening_rejected"])

    def test_76_actually_executed_Docker_Door_no_fill_refused(self):
        self.assertTrue(self.report[
            "actual_native_Docker_door_without_fill_rejected"])

    def test_77_actual_Docker_first_good_second_bad_ifc_SHA_preserved(self):
        self.assertTrue(self.report[
            "actual_native_Docker_good_then_second_door_rejected_rollback_sha_preserved"])

    def test_78_D_full_good_then_bad_whole_final_XML_keeps_previous(self):
        D=self.d()
        self.assertEqual(D.call("submit_building_xml",{
            "xml_text":self.full()})["status"],"ok")
        prior=file_hash(D.output_ifc)
        old_xml=D.current_xml
        bad=D.call("submit_building_xml",{"xml_text":"<Invalid/>"})
        self.assertEqual(bad["status"],"error")
        self.assertEqual(file_hash(D.output_ifc),prior)
        self.assertEqual(D.current_xml,old_xml)

    def test_79_D_managed_good_then_bad_xml_keeps_previous(self):
        M=self.m()
        self.assertEqual(M.call("submit_managed_final_state",{
            "xml_text":self.managed()})["status"],"ok")
        prior=file_hash(M.output_ifc)
        old_xml=M.current_xml
        bad=M.call("submit_managed_final_state",{"xml_text":"<Invalid/>"})
        self.assertEqual(bad["status"],"error")
        self.assertEqual(file_hash(M.output_ifc),prior)
        self.assertEqual(M.current_xml,old_xml)

    def test_80_25_total_tool_calls_cap_D_and_I(self):
        for session in (self.d(),self.m(),self.i()):
            for _ in range(MAX_CALLS):
                self.assertEqual(session.call("read_building_xml",{
                    "query":"source"})["status"],"ok")
            self.assertEqual(session.call("read_building_xml",{
                "query":"source"})["error_type"],"ToolBudgetExhausted")

    def test_81_I_fake_Docker_runtime_blocks_before_python(self):
        I=self.i()
        with patch(
            "tools.bibimbap_v064_ifc2x3_north_door_sessions.live_pinned_local_runtime_admission_v052",
            return_value={"status":"BLOCKED_RUNTIME","reason":"NO_DOCKER"},
        ),patch.object(I.executor,"run") as fake:
            result=I.call("execute_ifc_code",{"code":"commit()"})
        self.assertEqual(result["error_type"],"BLOCKED_RUNTIME")
        fake.assert_not_called()

    def test_82_I_fake_Docker_attestation_no_native_edit_refused(self):
        I=self.i()
        with patch(
            "tools.bibimbap_v064_ifc2x3_north_door_sessions.live_pinned_local_runtime_admission_v052",
            return_value={"status":"RUNTIME_ADMITTED"},
        ),patch.object(I.executor,"run",return_value={
            "status":"ok","committed":True,"backend":"linux_docker_sandbox",
        }):
            result=I.call("execute_ifc_code",{"code":"commit()"})
        self.assertEqual(
            result["error_type"],"NativeDockerWorkerOrOriginalIFC2X3ScopeRejected")
        self.assertIsNone(I.output_ifc)

    def test_83_original_author_private_grader_never_in_native_model_host(self):
        for name in (
            "bibimbap_v064_ifc2x3_north_door_native.py",
            "bibimbap_v064_ifc2x3_north_door_sessions.py",
        ):
            body=(audit.ROOT/"tools"/name).read_text("utf8")
            for forbidden in ("from data.tests",
                              "import data.tests",
                              "original_author_repo_evaluator_only_v064",
                              "source_public_north_wall_v064",
                              "public_nearest_north_physical_v064",
                              "import openai","import anthropic"):
                self.assertNotIn(forbidden,body)

    def test_84_original_IFC2X3_trial_rights_gate_never_launch(self):
        with self.assertRaises(ProviderTrialBlocked057):
            refuse_all_model_trials_v057({
                "rights":True,"model":True,
                "budget":True,"user_approved":True})
        self.assertEqual(self.report["actual_paid_provider_calls"],0)

    def test_85_source_original_model_provider_IFC_uploads_zero(self):
        self.assertEqual(self.report["original_IFC_provider_uploads"],0)
        self.assertEqual(self.report["actual_LLM_generated_model_trials"],0)

    def test_86_frozen_report_xb_write_refuses_overwrite(self):
        with self.assertRaises(FileExistsError):
            with audit.REPORT.open("xb"):
                pass


if __name__=="__main__":
    main()
